"""Generate and audit the frozen Hopper Controller rollout artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.suites.design_bench.hopper_controller.dataset import (
    EXPECTED_POLICY_COUNT,
    EXPECTED_ROLLOUT_COUNT,
    HOPPER_CONTROLLER_CONFIG_NAME,
    HOPPER_CONTROLLER_DEFAULT_SPLIT,
)

from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    POLICY_SIZE,
    derived_seed,
    initialize_rollout_worker,
    policy_identity,
    rollout_source_policy,
    simulator_metadata,
)

SOURCE_X_URL = (
    "https://storage.googleapis.com/design-bench/"
    "hopper_controller/hopper_controller-x-0.npy"
)
SOURCE_Y_URL = (
    "https://storage.googleapis.com/design-bench/"
    "hopper_controller/hopper_controller-y-0.npy"
)
SOURCE_X_SHA256 = "da93f2033436ae5c2f31e584ae42b4b4d043bea29448d78eec6470e4d8ee71d7"
SOURCE_Y_SHA256 = "8f04be4b81627e59bd83faf42e7aeaed3134dafc8f97d35c3fc887a649d93efd"
SOURCE_ROWS = 3_200
ROLLOUT_REPEATS = 500
ROLLOUT_BASE_SEED = 20_260_717
DESIGN_BENCH_COMMIT = "e52939588421b5433f6f2e9b359cf013c542bd89"
DATASET_VERSION = "1.0.0"


def generate_rollout_artifact(
    source_x_path: str | Path,
    source_y_path: str | Path,
    output_path: str | Path,
    *,
    repeats: int = ROLLOUT_REPEATS,
    workers: int = 32,
    base_seed: int = ROLLOUT_BASE_SEED,
    verify_source: bool = True,
) -> dict[str, Any]:
    """Evaluate every policy and write an atomic compressed measurement file."""

    if repeats < 2:
        raise ValueError("repeats must be at least 2")
    if workers < 1:
        raise ValueError("workers must be positive")
    source_x = Path(source_x_path)
    source_y = Path(source_y_path)
    if verify_source:
        _verify_file(source_x, SOURCE_X_SHA256)
        _verify_file(source_y, SOURCE_Y_SHA256)
    policies = np.load(source_x, mmap_mode="r", allow_pickle=False)
    old_targets = np.load(source_y, allow_pickle=False)
    expected_rows = SOURCE_ROWS if verify_source else len(policies)
    if policies.shape != (expected_rows, POLICY_SIZE) or policies.dtype != np.float32:
        raise ValueError("source policies have an unexpected shape or dtype")
    if old_targets.size != expected_rows or not np.all(np.isfinite(old_targets)):
        raise ValueError("source targets have an unexpected shape or values")
    if not np.all(np.isfinite(policies)):
        raise ValueError("source policies contain non-finite values")
    identities = tuple(policy_identity(policy) for policy in policies)
    if len(set(identities)) != expected_rows:
        raise ValueError("source policies must be canonical-unique")

    returns = np.empty((expected_rows, repeats), dtype=np.float32)
    lengths = np.empty((expected_rows, repeats), dtype=np.int32)
    terminated = np.empty((expected_rows, repeats), dtype=np.bool_)
    truncated = np.empty((expected_rows, repeats), dtype=np.bool_)
    observed_identities = [""] * expected_rows
    started = time.perf_counter()
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=initialize_rollout_worker,
        initargs=(str(source_x), repeats, base_seed),
    ) as pool:
        for index, identity, ret, length, term, trunc in pool.map(
            rollout_source_policy,
            range(expected_rows),
            chunksize=1,
        ):
            observed_identities[index] = identity
            returns[index] = ret
            lengths[index] = length
            terminated[index] = term
            truncated[index] = trunc
    elapsed = time.perf_counter() - started
    if tuple(observed_identities) != identities:
        raise RuntimeError("parallel rollout results do not align with source policies")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp.npz")
    metadata = {
        "schema_version": 1,
        "source_x_url": SOURCE_X_URL,
        "source_y_url": SOURCE_Y_URL,
        "source_x_sha256": _sha256(source_x),
        "source_y_sha256": _sha256(source_y),
        "design_bench_commit": DESIGN_BENCH_COMMIT,
        "rollout_repeats": repeats,
        "rollout_base_seed": base_seed,
        "workers": workers,
        "wall_time_seconds": elapsed,
        "target": "mean stochastic return in Hopper-v5",
        "simulator": simulator_metadata(),
        "reset_seeds": [
            derived_seed(base_seed, "reset", repeat) for repeat in range(repeats)
        ],
        "action_seed_derivation": "sha256(base_seed, action, policy_identity, repeat)",
        "builder_revision": os.environ.get("SMB_BUILDER_REVISION", "working-tree"),
        "host": {
            "platform": platform.platform(),
            "logical_cpus": os.cpu_count(),
        },
    }
    np.savez_compressed(
        temporary,
        policy_weights=np.asarray(policies),
        source_return=np.asarray(old_targets, dtype=np.float32).reshape(-1),
        policy_identity=np.asarray(identities),
        raw_returns=returns,
        episode_lengths=lengths,
        terminated=terminated,
        truncated=truncated,
        metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    os.replace(temporary, destination)
    report = audit_rollout_artifact(destination)
    report["artifact_sha256"] = _sha256(destination)
    return report


def audit_rollout_artifact(path: str | Path) -> dict[str, Any]:
    """Recompute summaries and the predeclared signal/repeat-stability gates."""

    with np.load(path, allow_pickle=False) as artifact:
        weights = artifact["policy_weights"]
        identities = artifact["policy_identity"]
        returns = artifact["raw_returns"].astype(np.float64)
        lengths = artifact["episode_lengths"]
        terminated = artifact["terminated"]
        truncated = artifact["truncated"]
        source_return = artifact["source_return"].astype(np.float64)
    rows, repeats = returns.shape
    if weights.shape != (rows, POLICY_SIZE):
        raise ValueError("artifact policy shape mismatch")
    if source_return.shape != (rows,):
        raise ValueError("artifact source target shape mismatch")
    if len(set(identities.tolist())) != rows:
        raise ValueError("artifact policy identities are not unique")
    expected_identities = [policy_identity(policy) for policy in weights]
    if identities.tolist() != expected_identities:
        raise ValueError("artifact policy identities do not match policy weights")
    if not np.all(np.isfinite(weights)) or not np.all(np.isfinite(returns)):
        raise ValueError("artifact contains non-finite policy or return values")
    if lengths.shape != returns.shape or np.any(lengths < 1) or np.any(lengths > 1_000):
        raise ValueError("artifact episode lengths are invalid")
    if terminated.shape != returns.shape or truncated.shape != returns.shape:
        raise ValueError("artifact termination arrays are misaligned")
    if np.any(~(terminated | truncated)):
        raise ValueError("every rollout must terminate or truncate")

    means = returns.mean(axis=1)
    medians = np.median(returns, axis=1)
    standard_errors = returns.std(axis=1, ddof=1) / np.sqrt(repeats)
    signal_span = float(np.percentile(means, 95) - np.percentile(means, 5))
    median_se = float(np.median(standard_errors))
    fold_indices = tuple(np.arange(offset, repeats, 5) for offset in range(5))
    fold_means = tuple(returns[:, indices].mean(axis=1) for indices in fold_indices)
    spearman: list[float] = []
    top32: list[float] = []
    top128: list[float] = []
    for left in range(len(fold_means)):
        for right in range(left + 1, len(fold_means)):
            spearman.append(_spearman(fold_means[left], fold_means[right]))
            top32.append(_top_k_jaccard(fold_means[left], fold_means[right], 32))
            top128.append(_top_k_jaccard(fold_means[left], fold_means[right], 128))
    report = {
        "rows": rows,
        "repeats": repeats,
        "episodes": rows * repeats,
        "environment_steps": int(lengths.sum()),
        "mean_episode_length": float(lengths.mean()),
        "full_horizon_fraction": float(np.mean(lengths == 1_000)),
        "mean_return_minimum": float(means.min()),
        "mean_return_maximum": float(means.max()),
        "mean_return_p05": float(np.percentile(means, 5)),
        "mean_return_p95": float(np.percentile(means, 95)),
        "median_standard_error": median_se,
        "signal_to_median_se": signal_span / median_se,
        "mean_median_top32_jaccard": _top_k_jaccard(means, medians, 32),
        "old_new_pearson": float(np.corrcoef(source_return, means)[0, 1]),
        "old_new_spearman": _spearman(source_return, means),
        "fold_spearman_median": float(np.median(spearman)),
        "fold_spearman_minimum": float(np.min(spearman)),
        "fold_top32_jaccard_median": float(np.median(top32)),
        "fold_top128_jaccard_median": float(np.median(top128)),
    }
    report["gate"] = {
        "signal": report["signal_to_median_se"] >= 10.0,
        "fold_spearman": report["fold_spearman_median"] >= 0.95,
        "fold_top32": report["fold_top32_jaccard_median"] >= 0.70,
        "fold_top128": report["fold_top128_jaccard_median"] >= 0.80,
    }
    report["gate_passed"] = all(report["gate"].values())
    return report


def build_hopper_controller_release(
    artifact_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Convert the audited 500-repeat artifact into an upload-ready HF config."""

    artifact_file = Path(artifact_path)
    destination = Path(output_dir)
    report = audit_rollout_artifact(artifact_file)
    if report["rows"] != EXPECTED_POLICY_COUNT:
        raise ValueError(
            f"release requires {EXPECTED_POLICY_COUNT} policies, got {report['rows']}"
        )
    if report["repeats"] != EXPECTED_ROLLOUT_COUNT:
        raise ValueError(
            f"release requires {EXPECTED_ROLLOUT_COUNT} rollouts per policy, "
            f"got {report['repeats']}"
        )

    with np.load(artifact_file, allow_pickle=False) as artifact:
        weights = artifact["policy_weights"]
        source_return = artifact["source_return"]
        identities = artifact["policy_identity"]
        returns = artifact["raw_returns"]
        lengths = artifact["episode_lengths"]
        terminated = artifact["terminated"]
        truncated = artifact["truncated"]
        metadata = json.loads(str(artifact["metadata"]))
        means = returns.mean(axis=1, dtype=np.float64)
        medians = np.median(returns.astype(np.float64), axis=1)
        standard_deviations = returns.std(axis=1, ddof=1, dtype=np.float64)
        standard_errors = standard_deviations / np.sqrt(EXPECTED_ROLLOUT_COUNT)
        data = HFDataset.from_dict(
            {
                "source_index": np.arange(EXPECTED_POLICY_COUNT, dtype=np.int32),
                "policy_identity": identities,
                "policy_weights": weights,
                "source_return": source_return,
                "raw_returns": returns,
                "episode_lengths": lengths,
                "terminated": terminated,
                "truncated": truncated,
                "rollout_count": np.full(
                    EXPECTED_POLICY_COUNT, EXPECTED_ROLLOUT_COUNT, dtype=np.int32
                ),
                "mean_return": means,
                "median_return": medians,
                "return_std": standard_deviations,
                "return_standard_error": standard_errors,
            },
            features=_release_features(),
        )

    data_path = (
        destination
        / "data"
        / HOPPER_CONTROLLER_CONFIG_NAME
        / f"{HOPPER_CONTROLLER_DEFAULT_SPLIT}.parquet"
    )
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(data_path)
    provenance = {
        "schema_version": 1,
        "dataset_id": "design-bench/hopper-controller",
        "dataset_version": DATASET_VERSION,
        "release_builder_revision": os.environ.get(
            "SMB_BUILDER_REVISION", "working-tree"
        ),
        "config": HOPPER_CONTROLLER_CONFIG_NAME,
        "split": HOPPER_CONTROLLER_DEFAULT_SPLIT,
        "source_artifact": {
            "path": str(artifact_file),
            "size_bytes": artifact_file.stat().st_size,
            "sha256": _sha256(artifact_file),
        },
        "rollout_metadata": metadata,
        "audit": report,
        "transformation": {
            "steps": [
                "preserve all Design-Bench policy weights and source targets",
                "preserve every frozen Hopper-v5 return, episode length, and outcome flag",
                "compute float64 mean, median, sample standard deviation, and standard error",
                "preserve Design-Bench source row order only as maintainer provenance",
            ],
            "target": "arithmetic mean of 500 stochastic episodic returns",
            "policy_feature_engineering": "none",
            "trajectory_annotation": "none",
        },
        "artifact": {
            "path": (
                f"data/{HOPPER_CONTROLLER_CONFIG_NAME}/"
                f"{HOPPER_CONTROLLER_DEFAULT_SPLIT}.parquet"
            ),
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
        },
    }
    _write_release_metadata(destination, provenance)
    return provenance


def _release_features() -> Features:
    return Features(
        {
            "source_index": Value("int32"),
            "policy_identity": Value("string"),
            "policy_weights": Sequence(Value("float32"), length=POLICY_SIZE),
            "source_return": Value("float32"),
            "raw_returns": Sequence(
                Value("float32"), length=EXPECTED_ROLLOUT_COUNT
            ),
            "episode_lengths": Sequence(
                Value("int32"), length=EXPECTED_ROLLOUT_COUNT
            ),
            "terminated": Sequence(Value("bool"), length=EXPECTED_ROLLOUT_COUNT),
            "truncated": Sequence(Value("bool"), length=EXPECTED_ROLLOUT_COUNT),
            "rollout_count": Value("int32"),
            "mean_return": Value("float64"),
            "median_return": Value("float64"),
            "return_std": Value("float64"),
            "return_standard_error": Value("float64"),
        }
    )


def _write_release_metadata(
    destination: Path,
    provenance: dict[str, Any],
) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / HOPPER_CONTROLLER_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)
    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": HOPPER_CONTROLLER_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][HOPPER_CONTROLLER_CONFIG_NAME] = {
        "manifest": f"manifests/{HOPPER_CONTROLLER_CONFIG_NAME}.json"
    }
    manifest = {
        "schema_version": 1,
        "dataset_id": "design-bench/hopper-controller",
        "version": DATASET_VERSION,
        "default_split": HOPPER_CONTROLLER_DEFAULT_SPLIT,
        "description": (
            "Design-Bench structured PPO controller checkpoints evaluated by 500 "
            "frozen stochastic Hopper-v5 rollouts per policy."
        ),
        "license": "MIT",
        "source": [
            {
                "name": "Design-Bench Hopper Controller policies",
                "url": SOURCE_X_URL,
                "revision": DESIGN_BENCH_COMMIT,
                "checksum": f"sha256:{SOURCE_X_SHA256}",
            },
            {
                "name": "Design-Bench Hopper Controller source targets",
                "url": SOURCE_Y_URL,
                "revision": DESIGN_BENCH_COMMIT,
                "checksum": f"sha256:{SOURCE_Y_SHA256}",
            },
        ],
        "citation": [
            {
                "text": "Trabucco et al. (2022), Design-Bench.",
                "url": "https://arxiv.org/abs/2202.08450",
            },
            {
                "text": "Todorov, Erez, and Tassa (2012), MuJoCo.",
                "url": "https://doi.org/10.1109/IROS.2012.6386109",
            },
        ],
        "inputs": [
            {
                "name": "policy_weights",
                "description": (
                    "Float32 parameters of the 11-64-64-3 tanh Gaussian policy."
                ),
                "constraints": [
                    {"kind": "length", "minimum": POLICY_SIZE, "maximum": POLICY_SIZE},
                    {"kind": "finite"},
                ],
            }
        ],
        "targets": [
            {
                "name": "raw_returns",
                "description": "All 500 frozen stochastic episodic returns.",
                "constraints": [
                    {
                        "kind": "length",
                        "minimum": EXPECTED_ROLLOUT_COUNT,
                        "maximum": EXPECTED_ROLLOUT_COUNT,
                    },
                    {"kind": "finite"},
                ],
            },
            {
                "name": "mean_return",
                "description": "Arithmetic mean of the 500 episodic returns.",
                "constraints": [{"kind": "finite"}],
            },
        ],
        "context": [
            {
                "name": "source_index",
                "description": "Maintainer-only row index in the Design-Bench array.",
                "required": False,
                "constraints": [
                    {
                        "kind": "range",
                        "minimum": 0,
                        "maximum": EXPECTED_POLICY_COUNT - 1,
                    }
                ],
            },
            {
                "name": "policy_identity",
                "description": "SHA-256-derived identity of canonical float32 weights.",
                "required": False,
                "constraints": [
                    {"kind": "length", "minimum": 31, "maximum": 31}
                ],
            },
            {
                "name": "source_return",
                "description": "Historical Design-Bench return retained for provenance.",
                "required": False,
                "constraints": [{"kind": "finite"}],
            },
            {
                "name": "episode_lengths",
                "description": "Step count aligned with every raw return.",
                "required": False,
                "constraints": [
                    {
                        "kind": "length",
                        "minimum": EXPECTED_ROLLOUT_COUNT,
                        "maximum": EXPECTED_ROLLOUT_COUNT,
                    },
                    {"kind": "range", "minimum": 1, "maximum": 1000},
                ],
            },
            {
                "name": "terminated",
                "description": "Environment termination flag for every rollout.",
                "required": False,
                "constraints": [
                    {
                        "kind": "length",
                        "minimum": EXPECTED_ROLLOUT_COUNT,
                        "maximum": EXPECTED_ROLLOUT_COUNT,
                    }
                ],
            },
            {
                "name": "truncated",
                "description": "Time-limit truncation flag for every rollout.",
                "required": False,
                "constraints": [
                    {
                        "kind": "length",
                        "minimum": EXPECTED_ROLLOUT_COUNT,
                        "maximum": EXPECTED_ROLLOUT_COUNT,
                    }
                ],
            },
            {
                "name": "rollout_count",
                "description": "Number of frozen rollouts per policy.",
                "required": False,
                "constraints": [
                    {
                        "kind": "range",
                        "minimum": EXPECTED_ROLLOUT_COUNT,
                        "maximum": EXPECTED_ROLLOUT_COUNT,
                    }
                ],
            },
            {
                "name": "median_return",
                "description": "Median of the raw episodic returns.",
                "required": False,
                "constraints": [{"kind": "finite"}],
            },
            {
                "name": "return_std",
                "description": "Sample standard deviation of raw episodic returns.",
                "required": False,
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0},
                ],
            },
            {
                "name": "return_standard_error",
                "description": "Sample standard deviation divided by sqrt(500).",
                "required": False,
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0},
                ],
            },
        ],
        "splits": [
            {
                "name": HOPPER_CONTROLLER_DEFAULT_SPLIT,
                "description": "All 3,200 source policies and frozen measurements.",
                "num_rows": EXPECTED_POLICY_COUNT,
                "attributes": {
                    "environment": "Hopper-v5",
                    "rollouts_per_policy": EXPECTED_ROLLOUT_COUNT,
                    "target_aggregation": "arithmetic_mean",
                },
            }
        ],
    }
    collection_path.write_text(
        json.dumps(collection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (manifest_dir / f"{HOPPER_CONTROLLER_CONFIG_NAME}.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (provenance_dir / "build.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _spearman(left: np.ndarray, right: np.ndarray) -> float:
    left_order = np.argsort(np.argsort(left, kind="stable"), kind="stable")
    right_order = np.argsort(np.argsort(right, kind="stable"), kind="stable")
    return float(np.corrcoef(left_order, right_order)[0, 1])


def _top_k_jaccard(left: np.ndarray, right: np.ndarray, k: int) -> float:
    actual_k = min(k, len(left))
    left_set = set(np.argpartition(left, -actual_k)[-actual_k:].tolist())
    right_set = set(np.argpartition(right, -actual_k)[-actual_k:].tolist())
    return len(left_set & right_set) / len(left_set | right_set)


def _verify_file(path: Path, expected_sha256: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = _sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"checksum mismatch for {path}: {actual}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_x", type=Path)
    parser.add_argument("source_y", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--repeats", type=int, default=ROLLOUT_REPEATS)
    parser.add_argument("--base-seed", type=int, default=ROLLOUT_BASE_SEED)
    parser.add_argument(
        "--release-dir",
        type=Path,
        help="also package the generated artifact as an upload-ready HF config",
    )
    args = parser.parse_args()
    report = generate_rollout_artifact(
        args.source_x,
        args.source_y,
        args.output,
        repeats=args.repeats,
        workers=args.workers,
        base_seed=args.base_seed,
    )
    if args.release_dir is not None:
        report["release"] = build_hopper_controller_release(
            args.output, args.release_dir
        )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
