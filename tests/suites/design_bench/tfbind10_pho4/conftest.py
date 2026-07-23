"""TFBind10 Pho4 test fixtures."""

from __future__ import annotations

import json
import math

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.tfbind10_pho4 import (
    TFBind10Pho4Dataset,
)

SEQUENCES = (
    "AAAAAAAAAA",
    "AAAAAAAAAC",
    "AAAAAAAAAG",
    "AAAAAAAAAT",
    "AAAAAAAACA",
    "AAAAAAAACC",
    "AAAAAAAACG",
    "AAAAAAAACT",
)


class TinyTFBind10Pho4Repository:
    repo_id = "local/tfbind10-pho4"
    resolved_revision = "tiny-tfbind10-pho4-fixture"

    def __init__(self) -> None:
        rows = {
            "sequence": [],
            "replicate_id": [],
            "bound_count": [],
            "input_count": [],
            "bound_fraction": [],
            "input_fraction": [],
            "observed_ddg": [],
        }
        bound_depth = sum(range(1, len(SEQUENCES) + 1))
        input_depth = 10 * len(SEQUENCES)
        for replicate in range(1, 5):
            for bound_count, sequence in enumerate(SEQUENCES, start=1):
                bound_fraction = bound_count / bound_depth
                input_fraction = 10 / input_depth
                rows["sequence"].append(sequence)
                rows["replicate_id"].append(replicate)
                rows["bound_count"].append(bound_count)
                rows["input_count"].append(10)
                rows["bound_fraction"].append(bound_fraction)
                rows["input_fraction"].append(input_fraction)
                rows["observed_ddg"].append(
                    -0.593 * math.log(bound_fraction / input_fraction)
                )
        self.data = HFDataset.from_dict(
            rows,
            features=Features(
                {
                    "sequence": Value("string"),
                    "replicate_id": Value("int8"),
                    "bound_count": Value("int32"),
                    "input_count": Value("int32"),
                    "bound_fraction": Value("float64"),
                    "input_fraction": Value("float64"),
                    "observed_ddg": Value("float64"),
                }
            ),
        )

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool):
        return self.data


@pytest.fixture
def tiny_tfbind10_pho4_dataset() -> TFBind10Pho4Dataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/tfbind10-pho4",
                "version": "test",
                "default_split": "observations",
                "description": "Tiny Pho4 raw-replicate fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "sequence",
                        "description": (
                            "Ten variable DNA nucleotides serialized as five "
                            "upstream and five downstream bases around a fixed "
                            "CACGTG core, which is excluded from this field."
                        ),
                        "constraints": [
                            {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                            {"kind": "length", "minimum": 10, "maximum": 10},
                        ],
                    }
                ],
                "targets": [
                    {
                        "name": "observed_ddg",
                        "description": "Per-replicate observed ddG.",
                        "unit": "kcal/mol",
                    }
                ],
                "context": [
                    {
                        "name": "replicate_id",
                        "description": "Replicate.",
                        "required": False,
                    },
                    {
                        "name": "bound_count",
                        "description": "Bound count.",
                        "required": False,
                    },
                    {
                        "name": "input_count",
                        "description": "Input count.",
                        "required": False,
                    },
                    {
                        "name": "bound_fraction",
                        "description": "Bound fraction.",
                        "required": False,
                    },
                    {
                        "name": "input_fraction",
                        "description": "Input fraction.",
                        "required": False,
                    },
                ],
                "splits": [
                    {
                        "name": "observations",
                        "description": "Tiny observations.",
                        "num_rows": 32,
                    }
                ],
            }
        )
    )
    return TFBind10Pho4Dataset(
        manifest,
        TinyTFBind10Pho4Repository(),
        config_name="tfbind10_pho4",
    )
