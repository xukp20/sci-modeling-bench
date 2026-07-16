from __future__ import annotations

import json
import os
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.cell_dag_nas import (
    CellDAGNASDataset,
    CellDAGNASValidator,
)

A = [0, 4, 5, 3, 10, 1] + [2] * 25
B = [0, 4, 6, 5, 3, 10, 9, 10, 1] + [2] * 22
C = [0, 4, 7, 5, 3, 10, 10, 10, 1] + [2] * 22
D = [0, 4, 8, 5, 3, 10, 9, 10, 1] + [2] * 22
PUBLISHED_REVISION = "1c223e204fa5f88c8a0c55bd9a66865fdb8bcafa"


class TinyRepository:
    repo_id = "local/cell-dag-nas"
    resolved_revision = "tiny-cell-dag-nas"

    def __init__(self) -> None:
        self.data = HFDataset.from_dict(
            {
                "architecture": [A, B, C],
                "test_accuracies": [[0.1] * 3, [0.9] * 3, [0.5] * 3],
                "mean_test_accuracy": [0.1, 0.9, 0.5],
                "canonical_hash": [
                    "043721b9c7fe8c5fad811d47d83132ec",
                    "d1269d9156ddc027c40473008192958a",
                    "d32d0b26d534203b48d866facd98cc3e",
                ],
                "aliases": [[A], [B], [C]],
                "train_accuracies": [[0.2] * 3, [1.0] * 3, [0.7] * 3],
                "validation_accuracies": [[0.1] * 3, [0.91] * 3, [0.51] * 3],
                "training_times": [[1.0] * 3, [2.0] * 3, [3.0] * 3],
            },
            features=Features(
                {
                    "architecture": Sequence(Value("int8"), length=31),
                    "test_accuracies": Sequence(Value("float32"), length=3),
                    "mean_test_accuracy": Value("float64"),
                    "canonical_hash": Value("string"),
                    "aliases": Sequence(Sequence(Value("int8"), length=31)),
                    "train_accuracies": Sequence(Value("float32"), length=3),
                    "validation_accuracies": Sequence(Value("float32"), length=3),
                    "training_times": Sequence(Value("float32"), length=3),
                }
            ),
        )

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


@pytest.fixture
def tiny_cell_dag_nas_dataset() -> CellDAGNASDataset:
    fields = [
        {"name": "architecture", "description": "Architecture."},
    ]
    targets = [
        {"name": "test_accuracies", "description": "Test repeats."},
        {"name": "mean_test_accuracy", "description": "Mean test."},
    ]
    context = [
        {"name": name, "description": name, "required": False}
        for name in (
            "canonical_hash",
            "aliases",
            "train_accuracies",
            "validation_accuracies",
            "training_times",
        )
    ]
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/cell-dag-nas",
                "version": "test",
                "default_split": "architectures",
                "description": "Tiny CellDAG-NAS fixture.",
                "license": "test-only",
                "inputs": fields,
                "targets": targets,
                "context": context,
                "splits": [
                    {
                        "name": "architectures",
                        "description": "Tiny graph table.",
                        "num_rows": 3,
                    }
                ],
            }
        )
    )
    return CellDAGNASDataset(
        manifest,
        TinyRepository(),
        config_name="cell_dag_nas",
        validator=CellDAGNASValidator(),
    )


@pytest.fixture(scope="session")
def published_cell_dag_nas_dataset() -> CellDAGNASDataset:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")
    return CellDAGNASDataset.from_hub(revision=PUBLISHED_REVISION)
