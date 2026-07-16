"""Build the canonical UCI Superconductor composition-group release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    COMPOSITION_DECIMALS,
    DESCRIPTOR_NAMES,
    ELEMENT_SYMBOLS,
    EXPECTED_GROUPS,
    EXPECTED_SOURCE_ROWS,
    SUPERCONDUCTOR_CONFIG_NAME,
    SUPERCONDUCTOR_DEFAULT_SPLIT,
    composition_id,
)

SOURCE_ARCHIVE_NAME = "superconductivty+data.zip"
SOURCE_ARCHIVE_URL = (
    "https://archive.ics.uci.edu/static/public/464/"
    "superconductivty%2Bdata.zip"
)
SOURCE_ARCHIVE_SIZE = 8_300_005
SOURCE_ARCHIVE_SHA256 = (
    "87f4490d73390ff94ee01dbf0d7d32abc80b22f2c803d471765cfc46a9f6371e"
)
UNIQUE_MEMBER = "unique_m.csv"
UNIQUE_MEMBER_SIZE = 4_291_603
UNIQUE_MEMBER_CRC32 = 0xBE0F9212
TRAIN_MEMBER = "train.csv"
TRAIN_MEMBER_SIZE = 23_859_780
TRAIN_MEMBER_CRC32 = 0x94C2BC69
UNIQUE_MEMBER_SHA256 = (
    "b68ae6b55ea8581eff8b1ffba073a899db7e2d2f7f3b781bb0802f643f51e5f7"
)
TRAIN_MEMBER_SHA256 = (
    "4dfb6e3a1f6ffd969e5a5e42f093c4800d1e2a6c8b1e309f8fcd9f23d86952f3"
)
DESIGN_BENCH_COMMIT = "e52939588421b5433f6f2e9b359cf013c542bd89"
DESIGN_BENCH_PROCESSOR = (
    "https://github.com/brandontrabucco/design-bench/blob/"
    f"{DESIGN_BENCH_COMMIT}/process/process_raw_superconductor.py"
)
DATASET_REPO_ID = "sci-modeling-bench/design-bench"
DATASET_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class SourceObservation:
    source_record_id: int
    composition: tuple[float, ...]
    material_formula: str
    critical_temp_k: float
    descriptors: tuple[float, ...]


def build_superconductor_release(
    archive_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Build an upload-ready HF config and return its provenance report."""

    archive = Path(archive_path)
    destination = Path(output_dir)
    _verify_archive(archive)
    observations = read_source_observations(archive)
    rows, statistics = canonicalize_observations(observations)

    data_path = (
        destination
        / "data"
        / SUPERCONDUCTOR_CONFIG_NAME
        / f"{SUPERCONDUCTOR_DEFAULT_SPLIT}.parquet"
    )
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data = HFDataset.from_dict(
        {name: [row[name] for row in rows] for name in rows[0]},
        features=_features(),
    )
    data.to_parquet(data_path)

    provenance = _provenance(archive, data_path, statistics)
    _write_release_metadata(destination, provenance)
    return provenance


def read_source_observations(
    archive_path: str | Path,
) -> tuple[SourceObservation, ...]:
    """Read and align UCI composition and descriptor tables row by row."""

    with zipfile.ZipFile(archive_path) as archive:
        _verify_member(archive, UNIQUE_MEMBER, UNIQUE_MEMBER_SIZE, UNIQUE_MEMBER_CRC32)
        _verify_member(archive, TRAIN_MEMBER, TRAIN_MEMBER_SIZE, TRAIN_MEMBER_CRC32)
        with archive.open(UNIQUE_MEMBER) as unique_raw, archive.open(TRAIN_MEMBER) as train_raw:
            unique_reader = csv.reader(io.TextIOWrapper(unique_raw, encoding="utf-8", newline=""))
            train_reader = csv.reader(io.TextIOWrapper(train_raw, encoding="utf-8", newline=""))
            unique_header = tuple(next(unique_reader))
            train_header = tuple(next(train_reader))
            expected_unique = (*ELEMENT_SYMBOLS, "critical_temp", "material")
            expected_train = (*DESCRIPTOR_NAMES, "critical_temp")
            if unique_header != expected_unique:
                raise ValueError("unexpected unique_m.csv columns")
            if train_header != expected_train:
                raise ValueError("unexpected train.csv columns")

            observations: list[SourceObservation] = []
            for index, (unique_values, train_values) in enumerate(
                zip(unique_reader, train_reader, strict=True)
            ):
                if len(unique_values) != len(expected_unique):
                    raise ValueError(f"unique_m.csv row {index + 2} has wrong width")
                if len(train_values) != len(expected_train):
                    raise ValueError(f"train.csv row {index + 2} has wrong width")
                composition = tuple(float(value) for value in unique_values[: len(ELEMENT_SYMBOLS)])
                critical_temp = float(unique_values[-2])
                train_critical_temp = float(train_values[-1])
                descriptors = tuple(float(value) for value in train_values[:-1])
                if critical_temp != train_critical_temp:
                    raise ValueError(f"critical_temp mismatch at source row {index}")
                if (
                    any(not math.isfinite(value) or value < 0 for value in composition)
                    or sum(composition) <= 0
                ):
                    raise ValueError(f"invalid composition at source row {index}")
                if not math.isfinite(critical_temp) or critical_temp < 0:
                    raise ValueError(f"invalid critical_temp at source row {index}")
                if any(not math.isfinite(value) for value in descriptors):
                    raise ValueError(f"invalid descriptor at source row {index}")
                observations.append(
                    SourceObservation(
                        source_record_id=index,
                        composition=composition,
                        material_formula=unique_values[-1],
                        critical_temp_k=critical_temp,
                        descriptors=descriptors,
                    )
                )

    if len(observations) != EXPECTED_SOURCE_ROWS:
        raise ValueError(
            f"expected {EXPECTED_SOURCE_ROWS} source rows, got {len(observations)}"
        )
    return tuple(observations)


def canonicalize_observations(
    observations: tuple[SourceObservation, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Group proportional formulas while preserving every source measurement."""

    groups: dict[tuple[float, ...], list[SourceObservation]] = defaultdict(list)
    for observation in observations:
        total = math.fsum(observation.composition)
        normalized = tuple(
            round(value / total, COMPOSITION_DECIMALS)
            for value in observation.composition
        )
        groups[normalized].append(observation)
    if len(groups) != EXPECTED_GROUPS:
        raise ValueError(f"expected {EXPECTED_GROUPS} groups, got {len(groups)}")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for composition, members in groups.items():
        group_id = composition_id(composition)
        if group_id in seen_ids:
            raise ValueError(f"composition ID collision: {group_id}")
        seen_ids.add(group_id)
        temperatures = np.asarray(
            [member.critical_temp_k for member in members], dtype=np.float64
        )
        descriptor_matrix = np.asarray(
            [member.descriptors for member in members], dtype=np.float64
        )
        rows.append(
            {
                "composition_id": group_id,
                "composition": list(composition),
                "representative_formula": members[0].material_formula,
                "source_record_ids": [member.source_record_id for member in members],
                "material_formulas": [member.material_formula for member in members],
                "critical_temperatures_k": temperatures.tolist(),
                "critical_temp_k": float(np.median(temperatures)),
                "critical_temp_min_k": float(np.min(temperatures)),
                "critical_temp_max_k": float(np.max(temperatures)),
                "critical_temp_std_k": float(np.std(temperatures)),
                "observation_count": len(members),
                "descriptor_features_by_observation": descriptor_matrix.tolist(),
                "descriptor_features": np.median(descriptor_matrix, axis=0).tolist(),
            }
        )
    rows.sort(key=lambda row: row["composition_id"])

    group_sizes = np.asarray([row["observation_count"] for row in rows])
    group_targets = np.asarray([row["critical_temp_k"] for row in rows])
    repeated = int(np.count_nonzero(group_sizes > 1))
    return rows, {
        "source_rows": len(observations),
        "composition_groups": len(rows),
        "repeated_groups": repeated,
        "rows_in_repeated_groups": int(group_sizes[group_sizes > 1].sum()),
        "maximum_group_size": int(group_sizes.max()),
        "critical_temp_k_minimum": float(group_targets.min()),
        "critical_temp_k_maximum": float(group_targets.max()),
        "critical_temp_k_mean": float(group_targets.mean()),
        "composition_rounding_decimals": COMPOSITION_DECIMALS,
        "target_aggregation": "median",
        "standard_deviation": "population",
        "conflict_groups_removed": 0,
    }


def _features() -> Features:
    return Features(
        {
            "composition_id": Value("string"),
            "composition": Sequence(Value("float64"), length=len(ELEMENT_SYMBOLS)),
            "representative_formula": Value("string"),
            "source_record_ids": Sequence(Value("int32")),
            "material_formulas": Sequence(Value("string")),
            "critical_temperatures_k": Sequence(Value("float64")),
            "critical_temp_k": Value("float64"),
            "critical_temp_min_k": Value("float64"),
            "critical_temp_max_k": Value("float64"),
            "critical_temp_std_k": Value("float64"),
            "observation_count": Value("int32"),
            "descriptor_features_by_observation": Sequence(
                Sequence(Value("float64"), length=len(DESCRIPTOR_NAMES))
            ),
            "descriptor_features": Sequence(
                Value("float64"), length=len(DESCRIPTOR_NAMES)
            ),
        }
    )


def _provenance(
    archive: Path,
    data_path: Path,
    statistics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": "design-bench/superconductor",
        "dataset_version": DATASET_VERSION,
        "config": SUPERCONDUCTOR_CONFIG_NAME,
        "split": SUPERCONDUCTOR_DEFAULT_SPLIT,
        "source_archive": {
            "name": SOURCE_ARCHIVE_NAME,
            "url": SOURCE_ARCHIVE_URL,
            "size_bytes": archive.stat().st_size,
            "sha256": _sha256(archive),
        },
        "source_members": {
            UNIQUE_MEMBER: {
                "size_bytes": UNIQUE_MEMBER_SIZE,
                "crc32": f"{UNIQUE_MEMBER_CRC32:08x}",
                "sha256": UNIQUE_MEMBER_SHA256,
            },
            TRAIN_MEMBER: {
                "size_bytes": TRAIN_MEMBER_SIZE,
                "crc32": f"{TRAIN_MEMBER_CRC32:08x}",
                "sha256": TRAIN_MEMBER_SHA256,
            },
        },
        "transformation": {
            "steps": [
                "align unique_m.csv and train.csv by source row",
                "normalize each 86-element amount vector by its sum",
                f"round fractions to {COMPOSITION_DECIMALS} decimal places",
                "group proportional compositions without deleting any source record",
                "use the group median measured critical temperature as the Task target",
                "retain aligned source IDs, formulas, measurements, and UCI descriptors",
            ],
            "design_bench_processor": DESIGN_BENCH_PROCESSOR,
            "design_bench_commit": DESIGN_BENCH_COMMIT,
        },
        "statistics": statistics,
        "artifact": {
            "path": (
                f"data/{SUPERCONDUCTOR_CONFIG_NAME}/"
                f"{SUPERCONDUCTOR_DEFAULT_SPLIT}.parquet"
            ),
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / SUPERCONDUCTOR_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": SUPERCONDUCTOR_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][SUPERCONDUCTOR_CONFIG_NAME] = {
        "manifest": f"manifests/{SUPERCONDUCTOR_CONFIG_NAME}.json"
    }

    manifest = {
        "schema_version": 1,
        "dataset_id": "design-bench/superconductor",
        "version": DATASET_VERSION,
        "default_split": SUPERCONDUCTOR_DEFAULT_SPLIT,
        "description": (
            "UCI superconductors grouped by normalized elemental composition, "
            "with every source measurement retained."
        ),
        "license": "cc-by-4.0",
        "source": [
            {
                "name": "UCI Superconductivity Data",
                "url": "https://archive.ics.uci.edu/dataset/464/superconductivty+data",
                "version": "dataset 464",
                "checksum": f"sha256:{SOURCE_ARCHIVE_SHA256}",
            },
            {
                "name": "Design-Bench Superconductor preprocessing",
                "url": DESIGN_BENCH_PROCESSOR,
                "revision": DESIGN_BENCH_COMMIT,
            },
        ],
        "citation": [
            {
                "text": (
                    "Hamidieh (2018), A data-driven statistical model for "
                    "predicting the critical temperature of a superconductor."
                ),
                "url": "https://arxiv.org/abs/1803.10260",
            },
            {
                "text": "Trabucco et al. (2022), Design-Bench.",
                "url": "https://arxiv.org/abs/2202.08450",
            },
        ],
        "inputs": [
            {
                "name": "composition_id",
                "description": "Stable identity of one normalized composition group.",
                "constraints": [{"kind": "length", "minimum": 27, "maximum": 27}],
            }
        ],
        "targets": [
            {
                "name": "critical_temp_k",
                "description": "Median measured critical temperature within the composition group.",
                "unit": "K",
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 200.0},
                ],
            }
        ],
        "context": [
            {
                "name": "composition",
                "description": "Normalized H-to-Rn elemental fractions rounded to eight decimals.",
                "required": False,
                "constraints": [
                    {"kind": "length", "minimum": 86, "maximum": 86},
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
            {
                "name": "representative_formula",
                "description": "First UCI material formula in the group.",
                "required": False,
            },
            {
                "name": "source_record_ids",
                "description": "Aligned UCI source row IDs.",
                "required": False,
            },
            {
                "name": "material_formulas",
                "description": "Aligned source material formulas.",
                "required": False,
            },
            {
                "name": "critical_temperatures_k",
                "description": "All aligned measured critical temperatures.",
                "unit": "K",
                "required": False,
            },
            {
                "name": "critical_temp_min_k",
                "description": "Minimum measured group temperature.",
                "unit": "K",
                "required": False,
            },
            {
                "name": "critical_temp_max_k",
                "description": "Maximum measured group temperature.",
                "unit": "K",
                "required": False,
            },
            {
                "name": "critical_temp_std_k",
                "description": "Population standard deviation of group temperatures.",
                "unit": "K",
                "required": False,
            },
            {
                "name": "observation_count",
                "description": "Number of retained source observations.",
                "required": False,
            },
            {
                "name": "descriptor_features_by_observation",
                "description": "All aligned UCI descriptor vectors.",
                "required": False,
            },
            {
                "name": "descriptor_features",
                "description": (
                    "Median of the 81 aligned UCI composition descriptors."
                ),
                "required": False,
                "constraints": [
                    {"kind": "length", "minimum": 81, "maximum": 81},
                    {"kind": "finite"},
                ],
            },
        ],
        "splits": [
            {
                "name": SUPERCONDUCTOR_DEFAULT_SPLIT,
                "description": "All canonical composition groups with source observations retained.",
                "num_rows": EXPECTED_GROUPS,
                "attributes": {
                    "source_rows": EXPECTED_SOURCE_ROWS,
                    "composition_rounding_decimals": COMPOSITION_DECIMALS,
                    "target_aggregation": "median",
                },
            }
        ],
        "knowledge": {},
    }
    _write_json(collection_path, collection)
    _write_json(manifest_dir / f"{SUPERCONDUCTOR_CONFIG_NAME}.json", manifest)
    _write_json(
        provenance_dir / f"{SUPERCONDUCTOR_DEFAULT_SPLIT}.json", provenance
    )
    (destination / "README.md").write_text(_dataset_card(provenance), encoding="utf-8")


def _dataset_card(provenance: dict[str, Any]) -> str:
    artifact = provenance["artifact"]
    return f"""---
configs:
- config_name: tfbind8
  data_files:
  - split: six6_ref_r1
    path: data/tfbind8/six6_ref_r1.parquet
- config_name: cell_dag_nas
  data_files:
  - split: architectures
    path: data/cell_dag_nas/architectures.parquet
- config_name: {SUPERCONDUCTOR_CONFIG_NAME}
  data_files:
  - split: {SUPERCONDUCTOR_DEFAULT_SPLIT}
    path: {artifact['path']}
license: other
---

# SciModelingBench Design-Bench Data

Canonical scientific observations used by the SciModelingBench Design-Bench
suite. Each config has its own manifest and provenance report.

## TFBind8

The `tfbind8` config contains the complete canonical `SIX6_REF_R1` DNA 8-mer
landscape. See `provenance/tfbind8/six6_ref_r1.json`.

## CellDAG-NAS

The `cell_dag_nas` config contains canonical NASBench-101 graphs, all
Design-Bench token aliases, and three official 108-epoch training records per
graph. See `provenance/cell_dag_nas/architectures.json`.

## Superconductor

The split contains {EXPECTED_GROUPS:,} normalized elemental-composition groups
derived from all {EXPECTED_SOURCE_ROWS:,} aligned UCI rows. Every source row,
formula, measured critical temperature, and descriptor vector remains attached
to its group. The benchmark target is the group median measured temperature;
no disagreement group is deleted.

```python
from datasets import load_dataset

groups = load_dataset(
    "{DATASET_REPO_ID}",
    name="{SUPERCONDUCTOR_CONFIG_NAME}",
    split="{SUPERCONDUCTOR_DEFAULT_SPLIT}",
)
```

## Provenance

- UCI archive SHA-256: `{SOURCE_ARCHIVE_SHA256}`.
- Canonical Parquet SHA-256: `{artifact['sha256']}`.
- Grouping: normalize composition, round to {COMPOSITION_DECIMALS} decimals,
  preserve all source observations, and use the group median as the Task target.
- Full report: `provenance/{SUPERCONDUCTOR_CONFIG_NAME}/{SUPERCONDUCTOR_DEFAULT_SPLIT}.json`.

## License

The shared repository contains data from multiple upstream sources, so the root
card uses `license: other`. Superconductor is CC BY 4.0, CellDAG-NAS is derived
from Apache-2.0 NASBench-101, and TFBind8 retains the source-specific terms in
its manifest and provenance.
"""


def _verify_archive(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != SOURCE_ARCHIVE_SIZE:
        raise ValueError("UCI archive size mismatch")
    if _sha256(path) != SOURCE_ARCHIVE_SHA256:
        raise ValueError("UCI archive checksum mismatch")


def _verify_member(
    archive: zipfile.ZipFile,
    name: str,
    size: int,
    crc32: int,
) -> None:
    info = archive.getinfo(name)
    if info.file_size != size or info.CRC != crc32:
        raise ValueError(f"archive member identity mismatch: {name}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the UCI Superconductor composition-group HF config."
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_superconductor_release(args.archive, args.output_dir)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
