"""Superconductor test fixtures."""

from __future__ import annotations

import json
import os
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.superconductor import (
    DESCRIPTOR_NAMES,
    ELEMENT_SYMBOLS,
    SuperconductorDataset,
)
from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    composition_id,
)

PUBLISHED_REVISION = "b9ec928a5b54e105926e86a2d89be80a07aa0763"


class TinySuperconductorRepository:
    repo_id = "local/superconductor"
    resolved_revision = "tiny-superconductor-fixture"

    def __init__(self) -> None:
        compositions = []
        for index in range(10):
            composition = [0.0] * len(ELEMENT_SYMBOLS)
            composition[index] = 1.0
            compositions.append(composition)
        self.data = HFDataset.from_dict(
            {
                "composition_id": [composition_id(row) for row in compositions],
                "composition": compositions,
                "representative_formula": [f"X{index}" for index in range(10)],
                "source_record_ids": [[index] for index in range(10)],
                "material_formulas": [[f"X{index}"] for index in range(10)],
                "critical_temperatures_k": [[float(index + 1)] for index in range(10)],
                "critical_temp_k": [float(index + 1) for index in range(10)],
                "critical_temp_min_k": [float(index + 1) for index in range(10)],
                "critical_temp_max_k": [float(index + 1) for index in range(10)],
                "critical_temp_std_k": [0.0] * 10,
                "observation_count": [1] * 10,
                "descriptor_features_by_observation": [
                    [[float(index)] * len(DESCRIPTOR_NAMES)]
                    for index in range(10)
                ],
                "descriptor_features": [
                    [float(index)] * len(DESCRIPTOR_NAMES)
                    for index in range(10)
                ],
            },
            features=Features(
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
                    "descriptor_features": Sequence(Value("float64"), length=len(DESCRIPTOR_NAMES)),
                }
            ),
        )

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


@pytest.fixture
def tiny_superconductor_dataset() -> SuperconductorDataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/superconductor",
                "version": "test",
                "default_split": "composition_groups",
                "description": "Tiny Superconductor fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "composition_id",
                        "description": "Composition group ID.",
                        "constraints": [{"kind": "length", "minimum": 27, "maximum": 27}],
                    }
                ],
                "targets": [
                    {
                        "name": "critical_temp_k",
                        "description": "Group median critical temperature.",
                        "unit": "K",
                        "constraints": [{"kind": "finite"}],
                    }
                ],
                "context": [],
                "splits": [
                    {
                        "name": "composition_groups",
                        "description": "Tiny composition groups.",
                        "num_rows": 10,
                    }
                ],
            }
        )
    )
    return SuperconductorDataset(
        manifest,
        TinySuperconductorRepository(),
        config_name="superconductor",
    )


@pytest.fixture(scope="session")
def published_superconductor_dataset() -> SuperconductorDataset:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")
    return SuperconductorDataset.from_hub(revision=PUBLISHED_REVISION)
