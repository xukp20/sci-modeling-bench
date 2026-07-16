from __future__ import annotations

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.suites.design_bench import (
    DEFAULT_TFBIND8_SOURCE,
    TFBIND8_CONFIG_NAME,
    TFBind8Validator,
)


def _sequence_from_index(index: int) -> str:
    symbols = ["A"] * 8
    for position in range(7, -1, -1):
        index, digit = divmod(index, 4)
        symbols[position] = "ACGT"[digit]
    return "".join(symbols)


@pytest.fixture(scope="module")
def complete_symmetric_landscape() -> HFDataset:
    sequences = [_sequence_from_index(index) for index in range(4**8)]
    e_scores = [sequence.count("G") + sequence.count("C") for sequence in sequences]
    normalized = [score / 8.0 for score in e_scores]
    return HFDataset.from_dict(
        {
            "sequence": sequences,
            "e_score": e_scores,
            "normalized_e_score": normalized,
        },
        features=Features(
            {
                "sequence": Value("string"),
                "e_score": Value("float64"),
                "normalized_e_score": Value("float32"),
            }
        ),
    )


def test_tfbind8_default_source_is_overridable_hub_reference() -> None:
    assert DEFAULT_TFBIND8_SOURCE.repo_id == "sci-modeling-bench/design-bench"
    assert DEFAULT_TFBIND8_SOURCE.config_name == TFBIND8_CONFIG_NAME
    assert DEFAULT_TFBIND8_SOURCE.revision is None


def test_tfbind8_validator_accepts_complete_canonical_landscape(
    complete_symmetric_landscape: HFDataset,
) -> None:
    report = TFBind8Validator().validate_dataset(complete_symmetric_landscape)

    assert report.valid, report.violations


def test_tfbind8_validator_detects_normalization_drift(
    complete_symmetric_landscape: HFDataset,
) -> None:
    columns = complete_symmetric_landscape.to_dict()
    columns["normalized_e_score"][0] = 0.5
    drifted = HFDataset.from_dict(
        columns,
        features=complete_symmetric_landscape.features,
    )

    report = TFBind8Validator().validate_dataset(drifted)

    assert "tfbind8_normalization_mismatch" in {
        violation.code for violation in report.violations
    }
