"""Build the canonical CellDAG-NAS release from pinned upstream artifacts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
from collections.abc import Iterable, Iterator
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.suites.design_bench.cell_dag_nas._graph import (
    ARCHITECTURE_LENGTH,
    decode_architecture,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas.dataset import (
    CELL_DAG_NAS_CONFIG_NAME,
    CELL_DAG_NAS_DEFAULT_SPLIT,
    EXPECTED_ALIAS_ROWS,
    EXPECTED_CANONICAL_GRAPHS,
    EXPECTED_REPEAT_COUNT,
)

DATASET_REPO_ID = "sci-modeling-bench/design-bench"
DATASET_VERSION = "1.0.0"
NASBENCH_COMMIT = "b94247037ee470418a3e56dcb83814e9be83f3a8"
DESIGN_BENCH_COMMIT = "e52939588421b5433f6f2e9b359cf013c542bd89"
TFRECORD_NAME = "nasbench_only108.tfrecord"
TFRECORD_URL = "https://storage.googleapis.com/nasbench/nasbench_only108.tfrecord"
TFRECORD_SIZE = 522_767_376
TFRECORD_SHA256 = "4c39c3936e36a85269881d659e44e61a245babcb72cb374eacacf75d0e5f4fd1"

ARCHITECTURE_ENCODING_DESCRIPTION = (
    "One valid 31-token NASBench-101 cell encoding. The grammar is "
    "[start, node operations..., separator, strict-upper-triangle adjacency..., "
    "stop, padding...]. Tokens are 0=start, 1=stop, 2=padding, 3=separator, "
    "4=input, 5=output, 6=1x1 convolution, 7=3x3 convolution, "
    "8=3x3 max-pooling, 9=no edge, and 10=edge. For n vertices, the "
    "n(n-1)/2 adjacency entries are flattened from the strict upper triangle "
    "in row-major order: (0,1), (0,2), ..., (0,n-1), (1,2), ..., "
    "(n-2,n-1). A valid cell has 2 to 7 vertices, at most 9 edges, and every "
    "vertex lies on a path from input to output."
)

KNOWLEDGE_RESOURCES = {
    "directed_acyclic_computation_graphs_and_graph_isomorphism": {
        "title": "Directed Acyclic Computation Graphs and Graph Isomorphism",
        "description": (
            "DAGs, topological order, computation paths, labeled graph "
            "isomorphism, automorphisms, and adjacency representations."
        ),
        "source_path": (
            "shared/"
            "directed-acyclic-computation-graphs-and-graph-isomorphism.md"
        ),
        "path": (
            "knowledge/shared/"
            "directed-acyclic-computation-graphs-and-graph-isomorphism.md"
        ),
        "media_type": "text/markdown",
    },
    "convolutional_feature_maps_kernels_and_receptive_fields": {
        "title": "Convolutional Feature Maps, Kernels, and Receptive Fields",
        "description": (
            "Two-dimensional convolution, channels, kernel size, parameter count, "
            "spatial dimensions, and receptive fields."
        ),
        "source_path": (
            "shared/convolutional-feature-maps-kernels-and-receptive-fields.md"
        ),
        "path": (
            "knowledge/shared/"
            "convolutional-feature-maps-kernels-and-receptive-fields.md"
        ),
        "media_type": "text/markdown",
    },
    "pooling_branching_and_feature_aggregation": {
        "title": "Pooling, Branching, and Feature Aggregation",
        "description": (
            "Max pooling, parallel computation paths, elementwise summation, "
            "concatenation, residual connections, and tensor compatibility."
        ),
        "source_path": "shared/pooling-branching-and-feature-aggregation.md",
        "path": "knowledge/shared/pooling-branching-and-feature-aggregation.md",
        "media_type": "text/markdown",
    },
    "cell_based_convolutional_neural_networks": {
        "title": "Cell-Based Convolutional Neural Networks",
        "description": (
            "Reusable neural-network cells, micro- and macro-architecture, "
            "operation graphs, repeated modules, and shape transitions."
        ),
        "source_path": "shared/cell-based-convolutional-neural-networks.md",
        "path": "knowledge/shared/cell-based-convolutional-neural-networks.md",
        "media_type": "text/markdown",
    },
    "neural_architecture_search_spaces_and_performance_evaluation": {
        "title": "Neural Architecture Search Spaces and Performance Evaluation",
        "description": (
            "NAS search spaces, search strategies, performance estimation, "
            "tabular benchmarks, proxy evaluation, and protocol dependence."
        ),
        "source_path": (
            "shared/"
            "neural-architecture-search-spaces-and-performance-evaluation.md"
        ),
        "path": (
            "knowledge/shared/"
            "neural-architecture-search-spaces-and-performance-evaluation.md"
        ),
        "media_type": "text/markdown",
    },
    "stochastic_neural_network_training_and_repeated_evaluation": {
        "title": "Stochastic Neural-Network Training and Repeated Evaluation",
        "description": (
            "Random initialization, data ordering, augmentation, implementation "
            "noise, repeated runs, uncertainty, and train-validation-test roles."
        ),
        "source_path": (
            "shared/"
            "stochastic-neural-network-training-and-repeated-evaluation.md"
        ),
        "path": (
            "knowledge/shared/"
            "stochastic-neural-network-training-and-repeated-evaluation.md"
        ),
        "media_type": "text/markdown",
    },
    "cifar10_image_classification": {
        "title": "CIFAR-10 Image Classification",
        "description": (
            "CIFAR-10 image dimensions, classes, dataset partitions, image "
            "classification objective, and interpretation limitations."
        ),
        "source_path": "shared/cifar10-image-classification.md",
        "path": "knowledge/shared/cifar10-image-classification.md",
        "media_type": "text/markdown",
    },
}


def build_cell_dag_nas_release(
    tfrecord_path: str | Path,
    processed_data_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Build an upload-ready shared HF repository and return provenance."""

    tfrecord = Path(tfrecord_path)
    processed = Path(processed_data_dir)
    destination = Path(output_dir)
    _verify_tfrecord(tfrecord)

    official = _read_official_records(tfrecord)
    aliases, shard_checksums, parity = _read_aliases(processed, official)
    if set(aliases) != set(official):
        missing = len(set(official) - set(aliases))
        extra = len(set(aliases) - set(official))
        raise ValueError(f"official/alias hash mismatch: missing={missing}, extra={extra}")

    data_path = (
        destination
        / "data"
        / CELL_DAG_NAS_CONFIG_NAME
        / f"{CELL_DAG_NAS_DEFAULT_SPLIT}.parquet"
    )
    data_path.parent.mkdir(parents=True, exist_ok=True)
    features = Features(
        {
            "architecture": Sequence(Value("int8"), length=ARCHITECTURE_LENGTH),
            "test_accuracies": Sequence(Value("float32"), length=3),
            "mean_test_accuracy": Value("float64"),
            "canonical_hash": Value("string"),
            "aliases": Sequence(
                Sequence(Value("int8"), length=ARCHITECTURE_LENGTH)
            ),
            "train_accuracies": Sequence(Value("float32"), length=3),
            "validation_accuracies": Sequence(Value("float32"), length=3),
            "training_times": Sequence(Value("float32"), length=3),
        }
    )
    dataset = HFDataset.from_generator(
        _iter_release_rows,
        gen_kwargs={"official": official, "aliases": aliases},
        features=features,
    )
    dataset.to_parquet(data_path)

    visible_stats = _visible_stats(dataset)
    provenance = _build_provenance(
        tfrecord,
        data_path,
        shard_checksums=shard_checksums,
        parity=parity,
        visible_stats=visible_stats,
    )
    provenance["knowledge"] = _write_knowledge_resources(destination)
    _write_release_metadata(destination, provenance)
    return provenance


def _read_official_records(
    path: Path,
) -> dict[str, tuple[tuple[float, float, float, float], ...]]:
    try:
        model_metrics_class = _model_metrics_message_class()
    except ImportError as exc:
        raise RuntimeError(
            "building CellDAG-NAS requires protobuf; install the data-build extra"
        ) from exc

    records: dict[str, list[tuple[float, float, float, float]]] = {}
    graph_identity: dict[str, tuple[str, str]] = {}
    for payload in _iter_tfrecord(path):
        module_hash, epochs, adjacency, operations, raw_metrics = json.loads(
            payload.decode("utf-8")
        )
        if int(epochs) != 108:
            raise ValueError(f"only-108 TFRecord contains epoch budget {epochs}")
        identity = (adjacency, operations)
        previous = graph_identity.setdefault(module_hash, identity)
        if previous != identity:
            raise ValueError(f"graph identity changed across repeats for {module_hash}")
        metrics = model_metrics_class.FromString(base64.b64decode(raw_metrics))
        final = metrics.evaluation_data[2]
        records.setdefault(module_hash, []).append(
            (
                float(final.train_accuracy),
                float(final.validation_accuracy),
                float(final.test_accuracy),
                float(final.training_time),
            )
        )
    if len(records) != EXPECTED_CANONICAL_GRAPHS:
        raise ValueError(
            f"expected {EXPECTED_CANONICAL_GRAPHS} official graphs, got {len(records)}"
        )
    invalid = [key for key, values in records.items() if len(values) != EXPECTED_REPEAT_COUNT]
    if invalid:
        raise ValueError(f"graphs without exactly three repeats: {len(invalid)}")
    return {key: tuple(values) for key, values in records.items()}


def _read_aliases(
    folder: Path,
    official: dict[str, tuple[tuple[float, float, float, float], ...]],
) -> tuple[dict[str, bytearray], dict[str, str], dict[str, Any]]:
    x_paths = _numeric_shards(folder, "x")
    y_paths = _numeric_shards(folder, "y")
    if len(x_paths) != 26 or len(y_paths) != 26:
        raise ValueError(f"expected 26 x/y shards, got {len(x_paths)}/{len(y_paths)}")
    aliases: dict[str, bytearray] = {}
    rows = 0
    max_error = 0.0
    mismatches = 0
    checksums: dict[str, str] = {}
    for x_path, y_path in zip(x_paths, y_paths, strict=True):
        checksums[x_path.name] = _sha256(x_path)
        checksums[y_path.name] = _sha256(y_path)
        x = np.load(x_path, allow_pickle=False, mmap_mode="r")
        y = np.load(y_path, allow_pickle=False, mmap_mode="r").reshape(-1)
        if len(x) != len(y):
            raise ValueError(f"row mismatch for {x_path.name} and {y_path.name}")
        for architecture, legacy_score in zip(x, y):
            decoded = decode_architecture(architecture)
            try:
                repeats = official[decoded.canonical_hash]
            except KeyError as exc:
                raise ValueError(
                    f"processed alias maps to unknown hash {decoded.canonical_hash}"
                ) from exc
            expected = np.float32(np.mean([repeat[2] for repeat in repeats]))
            error = abs(float(legacy_score) - float(expected))
            max_error = max(max_error, error)
            mismatches += int(error != 0.0)
            aliases.setdefault(decoded.canonical_hash, bytearray()).extend(
                bytes(decoded.tokens)
            )
            rows += 1
    if rows != EXPECTED_ALIAS_ROWS:
        raise ValueError(f"expected {EXPECTED_ALIAS_ROWS} aliases, got {rows}")
    if mismatches:
        raise ValueError(
            f"Design-Bench score parity failed for {mismatches} rows; max error={max_error}"
        )
    return aliases, checksums, {
        "rows": rows,
        "score_mismatches": mismatches,
        "score_max_absolute_error": max_error,
    }


def _iter_release_rows(
    official: dict[str, tuple[tuple[float, float, float, float], ...]],
    aliases: dict[str, bytearray],
) -> Iterator[dict[str, Any]]:
    for canonical_hash in sorted(official):
        raw_aliases = aliases[canonical_hash]
        if len(raw_aliases) % ARCHITECTURE_LENGTH:
            raise ValueError(f"corrupt alias buffer for {canonical_hash}")
        alias_rows = [
            list(raw_aliases[offset : offset + ARCHITECTURE_LENGTH])
            for offset in range(0, len(raw_aliases), ARCHITECTURE_LENGTH)
        ]
        alias_rows.sort()
        repeats = official[canonical_hash]
        tests = [repeat[2] for repeat in repeats]
        yield {
            "architecture": alias_rows[0],
            "test_accuracies": tests,
            "mean_test_accuracy": sum(tests) / len(tests),
            "canonical_hash": canonical_hash,
            "aliases": alias_rows,
            "train_accuracies": [repeat[0] for repeat in repeats],
            "validation_accuracies": [repeat[1] for repeat in repeats],
            "training_times": [repeat[3] for repeat in repeats],
        }


def _visible_stats(dataset: HFDataset) -> dict[str, Any]:
    table = dataset.data.table.combine_chunks()
    means = table["mean_test_accuracy"].to_numpy()
    hashes = table["canonical_hash"].to_pylist()
    alias_lists = table["aliases"].chunk(0)
    offsets = alias_lists.offsets.to_numpy()
    alias_lengths = offsets[1:] - offsets[:-1]
    count = int(np.floor(len(means) * 0.40))
    order = sorted(
        range(len(dataset)),
        key=lambda index: (
            float(means[index]),
            hashes[index],
        ),
    )[:count]
    alias_rows = int(alias_lengths[np.asarray(order)].sum())
    best = max(float(value) for value in means)
    return {
        "visible_fraction": 0.40,
        "visible_canonical_graphs": count,
        "hidden_canonical_graphs": len(means) - count,
        "visible_alias_rows": alias_rows,
        "visible_alias_fraction": alias_rows / EXPECTED_ALIAS_ROWS,
        "visible_boundary_mean_test_accuracy": float(
            means[order[-1]]
        ),
        "global_best_mean_test_accuracy": best,
    }


def _build_provenance(
    tfrecord: Path,
    data_path: Path,
    *,
    shard_checksums: dict[str, str],
    parity: dict[str, Any],
    visible_stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": "design-bench/cell-dag-nas",
        "dataset_version": DATASET_VERSION,
        "config": CELL_DAG_NAS_CONFIG_NAME,
        "split": CELL_DAG_NAS_DEFAULT_SPLIT,
        "official_source": {
            "name": TFRECORD_NAME,
            "url": TFRECORD_URL,
            "size_bytes": tfrecord.stat().st_size,
            "sha256": _sha256(tfrecord),
            "nasbench_commit": NASBENCH_COMMIT,
        },
        "design_bench": {
            "revision": DESIGN_BENCH_COMMIT,
            "processed_shard_sha256": shard_checksums,
            "parity": parity,
        },
        "canonicalization": {
            "canonical_graphs": EXPECTED_CANONICAL_GRAPHS,
            "alias_rows": EXPECTED_ALIAS_ROWS,
            "repeats_per_graph": EXPECTED_REPEAT_COUNT,
            "representative": "lexicographically smallest 31-token alias",
            "hash": "NASBench-101 graph_util.hash_module",
        },
        "default_protocol": visible_stats,
        "artifact": {
            "path": (
                f"data/{CELL_DAG_NAS_CONFIG_NAME}/"
                f"{CELL_DAG_NAS_DEFAULT_SPLIT}.parquet"
            ),
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / CELL_DAG_NAS_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": CELL_DAG_NAS_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][CELL_DAG_NAS_CONFIG_NAME] = {
        "manifest": f"manifests/{CELL_DAG_NAS_CONFIG_NAME}.json"
    }
    manifest = {
        "schema_version": 1,
        "dataset_id": "design-bench/cell-dag-nas",
        "version": DATASET_VERSION,
        "default_split": CELL_DAG_NAS_DEFAULT_SPLIT,
        "description": (
            "Canonical NASBench-101 cell DAGs with all Design-Bench aliases "
            "and three official 108-epoch training repeats."
        ),
        "license": "apache-2.0",
        "source": [
            {
                "name": "NASBench-101 only-108 TFRecord",
                "url": TFRECORD_URL,
                "revision": NASBENCH_COMMIT,
                "checksum": f"sha256:{TFRECORD_SHA256}",
            },
            {
                "name": "Design-Bench NASBench preprocessing",
                "url": "https://github.com/brandontrabucco/design-bench",
                "revision": DESIGN_BENCH_COMMIT,
            },
        ],
        "citation": [
            {
                "text": "Ying et al. (2019), NAS-Bench-101.",
                "url": "https://proceedings.mlr.press/v97/ying19a.html",
            },
            {
                "text": "Trabucco et al. (2022), Design-Bench.",
                "url": "https://arxiv.org/abs/2202.08450",
            },
        ],
        "inputs": [
            {
                "name": "architecture",
                "description": ARCHITECTURE_ENCODING_DESCRIPTION,
                "constraints": [
                    {"kind": "length", "minimum": 31, "maximum": 31},
                    {"kind": "allowed_values", "values": list(range(11))},
                ],
            }
        ],
        "targets": [
            {
                "name": "test_accuracies",
                "description": "Final test accuracy for the three 108-epoch runs.",
                "constraints": [
                    {"kind": "length", "minimum": 3, "maximum": 3},
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
            {
                "name": "mean_test_accuracy",
                "description": "Arithmetic mean of the three final test accuracies.",
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
        ],
        "context": [
            {
                "name": "canonical_hash",
                "description": "Official graph-invariant NASBench-101 identity.",
                "required": False,
            },
            {
                "name": "aliases",
                "description": "All enumerated 31-token encodings of this graph.",
                "required": False,
            },
            {
                "name": "train_accuracies",
                "description": "Final train accuracy for the three 108-epoch runs.",
                "required": False,
                "constraints": [{"kind": "finite"}],
            },
            {
                "name": "validation_accuracies",
                "description": "Final validation accuracy for the three runs.",
                "required": False,
                "constraints": [{"kind": "finite"}],
            },
            {
                "name": "training_times",
                "description": "Training time in seconds for the three runs.",
                "required": False,
                "unit": "s",
                "constraints": [{"kind": "finite"}],
            },
        ],
        "splits": [
            {
                "name": CELL_DAG_NAS_DEFAULT_SPLIT,
                "description": "Complete canonical NASBench-101 only-108 graph space.",
                "num_rows": EXPECTED_CANONICAL_GRAPHS,
                "attributes": {
                    "canonical_graphs": EXPECTED_CANONICAL_GRAPHS,
                    "alias_rows": EXPECTED_ALIAS_ROWS,
                    "repeats_per_graph": EXPECTED_REPEAT_COUNT,
                    "epoch_budget": 108,
                    "dataset": "CIFAR-10",
                },
            }
        ],
        "knowledge": {
            key: {
                field: value
                for field, value in specification.items()
                if field != "source_path"
            }
            for key, specification in KNOWLEDGE_RESOURCES.items()
        },
    }
    _write_json(collection_path, collection)
    _write_json(manifest_dir / f"{CELL_DAG_NAS_CONFIG_NAME}.json", manifest)
    _write_json(
        provenance_dir / f"{CELL_DAG_NAS_DEFAULT_SPLIT}.json",
        provenance,
    )
    (destination / "README.md").write_text(_dataset_card(provenance), encoding="utf-8")


def _dataset_card(provenance: dict[str, Any]) -> str:
    visible = provenance["default_protocol"]
    return f"""---
configs:
- config_name: tfbind8
  data_files:
  - split: six6_ref_r1
    path: data/tfbind8/six6_ref_r1.parquet
- config_name: {CELL_DAG_NAS_CONFIG_NAME}
  data_files:
  - split: {CELL_DAG_NAS_DEFAULT_SPLIT}
    path: data/{CELL_DAG_NAS_CONFIG_NAME}/{CELL_DAG_NAS_DEFAULT_SPLIT}.parquet
license: other
---

# SciModelingBench Design-Bench Data

Canonical scientific observations used by the SciModelingBench Design-Bench
integrations. Each config has its own manifest and provenance report.

## TFBind8

The `tfbind8` config contains the complete canonical `SIX6_REF_R1` DNA 8-mer
landscape. See `provenance/tfbind8/six6_ref_r1.json`.

## CellDAG-NAS

The `{CELL_DAG_NAS_CONFIG_NAME}` config contains {EXPECTED_CANONICAL_GRAPHS:,}
canonical NASBench-101 graphs, {EXPECTED_ALIAS_ROWS:,} Design-Bench token aliases,
and three official 108-epoch train/validation/test/time records per graph.

The default SciModelingBench Protocol exposes the lowest 40% canonical graphs:
{visible['visible_canonical_graphs']:,} graphs and
{visible['visible_alias_rows']:,} alias rows. It exposes the three raw test
accuracies rather than their mean.

```python
from datasets import load_dataset

data = load_dataset(
    "{DATASET_REPO_ID}",
    name="{CELL_DAG_NAS_CONFIG_NAME}",
    split="{CELL_DAG_NAS_DEFAULT_SPLIT}",
)
```

Machine-readable provenance is stored at
`provenance/{CELL_DAG_NAS_CONFIG_NAME}/{CELL_DAG_NAS_DEFAULT_SPLIT}.json`.

## License

The shared repository contains data from multiple upstream sources, so the root
card uses `license: other`. The CellDAG-NAS config is derived from the
Apache-2.0 NASBench-101 release. TFBind8 retains the source terms documented in
its manifest and provenance report.
"""


def _verify_tfrecord(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != TFRECORD_SIZE:
        raise ValueError(f"TFRecord size mismatch: {path.stat().st_size}")
    checksum = _sha256(path)
    if checksum != TFRECORD_SHA256:
        raise ValueError(f"TFRecord checksum mismatch: {checksum}")


def _iter_tfrecord(path: Path) -> Iterator[bytes]:
    with path.open("rb") as stream:
        while True:
            length_bytes = stream.read(8)
            if not length_bytes:
                return
            if len(length_bytes) != 8:
                raise EOFError("truncated TFRecord length")
            length = struct.unpack("<Q", length_bytes)[0]
            if len(stream.read(4)) != 4:
                raise EOFError("truncated TFRecord length CRC")
            payload = stream.read(length)
            if len(payload) != length:
                raise EOFError("truncated TFRecord payload")
            if len(stream.read(4)) != 4:
                raise EOFError("truncated TFRecord payload CRC")
            yield payload


def _model_metrics_message_class():
    """Build a modern protobuf parser for the archived NASBench schema."""

    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

    file_descriptor = descriptor_pb2.FileDescriptorProto(
        name="model_metrics.proto",
        package="nasbench",
        syntax="proto2",
    )
    evaluation = file_descriptor.message_type.add(name="EvaluationData")
    for number, name in enumerate(
        (
            "current_epoch",
            "training_time",
            "train_accuracy",
            "validation_accuracy",
            "test_accuracy",
        ),
        start=1,
    ):
        evaluation.field.add(
            name=name,
            number=number,
            label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
            type=descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE,
        )
    evaluation.field.add(
        name="checkpoint_path",
        number=6,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
        type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
    )

    metrics = file_descriptor.message_type.add(name="ModelMetrics")
    metrics.field.add(
        name="evaluation_data",
        number=1,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
        type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".nasbench.EvaluationData",
    )
    metrics.field.add(
        name="trainable_parameters",
        number=2,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
        type=descriptor_pb2.FieldDescriptorProto.TYPE_INT32,
    )
    metrics.field.add(
        name="total_time",
        number=3,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
        type=descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE,
    )
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_descriptor)
    return message_factory.GetMessageClass(
        pool.FindMessageTypeByName("nasbench.ModelMetrics")
    )


def _numeric_shards(folder: Path, kind: str) -> list[Path]:
    return sorted(
        folder.glob(f"nas_bench-{kind}-*.npy"),
        key=lambda path: int(path.stem.rsplit("-", 1)[1]),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_knowledge_resources(destination: Path) -> list[dict[str, Any]]:
    source_root = resources.files("sci_modeling_bench").joinpath(
        "resources", "knowledge"
    )
    artifacts: list[dict[str, Any]] = []
    for key, specification in KNOWLEDGE_RESOURCES.items():
        content = source_root.joinpath(specification["source_path"]).read_bytes()
        output_path = destination / specification["path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        artifacts.append(
            {
                "key": key,
                "path": specification["path"],
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return artifacts


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build canonical CellDAG-NAS data.")
    parser.add_argument("--tfrecord", type=Path, required=True)
    parser.add_argument("--processed-data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_cell_dag_nas_release(
        args.tfrecord,
        args.processed_data_dir,
        args.output_dir,
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
