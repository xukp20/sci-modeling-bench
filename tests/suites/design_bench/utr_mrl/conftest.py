"""UTR MRL test fixtures."""

from __future__ import annotations

import json
import os
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.utr_mrl import UTRMRLDataset
from sci_modeling_bench.suites.design_bench.utr_mrl._sequence import (
    sequence_annotations,
)

PUBLISHED_REVISION = "2dd09bd522d8fd883e900321fdbd819b747521ea"


def _sequence(prefix: str, suffix: str, fill: str = "C") -> str:
    return prefix + fill * (50 - len(prefix) - len(suffix)) + suffix


NO_UAUG_STRONG = _sequence("", "ACA")
NO_UAUG_WEAK = _sequence("", "TGT")
UAUG_STRONG = _sequence("ATG", "ACA")
MIXED = "C" * 50
UAUG_WEAK = tuple(_sequence("ATG", f"{base}TGT") for base in "ACGT")


class TinyUTRMRLRepository:
    repo_id = "local/utr-mrl"
    resolved_revision = "tiny-utr-mrl-fixture"

    def __init__(self) -> None:
        scores = {
            NO_UAUG_STRONG: 6.0,
            NO_UAUG_WEAK: 5.0,
            UAUG_STRONG: 4.0,
            MIXED: 3.0,
            UAUG_WEAK[0]: 1.0,
            UAUG_WEAK[1]: 2.0,
            UAUG_WEAK[2]: 7.0,
            UAUG_WEAK[3]: 8.0,
        }
        sequences = sorted(scores)
        annotations = [sequence_annotations(sequence) for sequence in sequences]
        self.data = HFDataset.from_dict(
            {
                "sequence": sequences,
                "mean_ribosome_load": [scores[sequence] for sequence in sequences],
                "has_uaug": [row[0] for row in annotations],
                "has_out_of_frame_uaug": [row[1] for row in annotations],
                "kozak_quality": [row[2] for row in annotations],
            },
            features=Features(
                {
                    "sequence": Value("string"),
                    "mean_ribosome_load": Value("float64"),
                    "has_uaug": Value("bool"),
                    "has_out_of_frame_uaug": Value("bool"),
                    "kozak_quality": Value("string"),
                }
            ),
        )

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


@pytest.fixture
def tiny_utr_mrl_dataset() -> UTRMRLDataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/utr-mrl-egfp-unmodified",
                "version": "test",
                "default_split": "measurements",
                "description": "Tiny measured UTR fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "sequence",
                        "description": "DNA-form 50-nt UTR.",
                        "constraints": [
                            {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                            {"kind": "length", "minimum": 50, "maximum": 50},
                        ],
                    }
                ],
                "targets": [
                    {
                        "name": "mean_ribosome_load",
                        "description": "Measured replicate-mean MRL.",
                        "constraints": [{"kind": "finite"}],
                    }
                ],
                "context": [],
                "splits": [
                    {
                        "name": "measurements",
                        "description": "Tiny measurements.",
                        "num_rows": 8,
                    }
                ],
            }
        )
    )
    return UTRMRLDataset(
        manifest,
        TinyUTRMRLRepository(),
        config_name="utr_mrl_egfp_unmodified",
    )


@pytest.fixture(scope="session")
def published_utr_mrl_dataset() -> UTRMRLDataset:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")
    return UTRMRLDataset.from_hub(revision=PUBLISHED_REVISION)
