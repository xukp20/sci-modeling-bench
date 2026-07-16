"""TFBind8-specific test fixtures."""

from __future__ import annotations

import json
import os
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.tfbind8 import TFBind8Dataset

PUBLISHED_REVISION = "2ee2856f4255bb6a64c11b6c2660a6f41418e654"


class TinyTFBind8Repository:
    repo_id = "local/tfbind8"
    resolved_revision = "tiny-tfbind8-fixture"

    def __init__(self) -> None:
        self.data = HFDataset.from_dict(
            {
                "sequence": ["AAAAAAAA", "AAAAAAAC", "AACCGGTT", "TTTTTTTT"],
                "e_score": [-0.5, -0.25, 0.25, 0.5],
                "normalized_e_score": [0.0, 0.25, 0.75, 1.0],
            },
            features=Features(
                {
                    "sequence": Value("string"),
                    "e_score": Value("float64"),
                    "normalized_e_score": Value("float32"),
                }
            ),
        )
        self.load_calls: list[tuple[str, str, bool]] = []

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        self.load_calls.append((config_name, split, streaming))
        return self.data


@pytest.fixture
def tiny_tfbind8_repository() -> TinyTFBind8Repository:
    return TinyTFBind8Repository()


@pytest.fixture
def tiny_tfbind8_dataset(
    tiny_tfbind8_repository: TinyTFBind8Repository,
) -> TFBind8Dataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/tfbind8",
                "version": "test",
                "default_split": "six6_ref_r1",
                "description": "Tiny TFBind8 test fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "sequence",
                        "description": "Eight-base uppercase DNA sequence.",
                        "constraints": [
                            {
                                "kind": "alphabet",
                                "symbols": ["A", "C", "G", "T"],
                            },
                            {"kind": "length", "minimum": 8, "maximum": 8},
                        ],
                    }
                ],
                "targets": [
                    {
                        "name": "e_score",
                        "description": "Raw PBM E-score.",
                        "constraints": [{"kind": "finite"}],
                    },
                    {
                        "name": "normalized_e_score",
                        "description": "Normalized PBM E-score.",
                        "constraints": [
                            {"kind": "finite"},
                            {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                        ],
                    },
                ],
                "splits": [
                    {
                        "name": "six6_ref_r1",
                        "description": "Tiny SIX6 split.",
                        "num_rows": 4,
                    }
                ],
            }
        )
    )
    return TFBind8Dataset(
        manifest,
        tiny_tfbind8_repository,
        config_name="tfbind8",
    )


@pytest.fixture(scope="session")
def published_tfbind8_dataset() -> TFBind8Dataset:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")
    return TFBind8Dataset.from_hub(revision=PUBLISHED_REVISION)
