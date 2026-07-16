from __future__ import annotations

import os

import pytest

from sci_modeling_bench.suites.design_bench.tfbind10_pho4 import (
    TFBind10Pho4Dataset,
)

PUBLISHED_REVISION = "51155f061b77c9f56a0ad8cf3b04c4ae481a7274"


def test_dataset_validates_dna_10_mer_candidates(
    tiny_tfbind10_pho4_dataset,
) -> None:
    assert tiny_tfbind10_pho4_dataset.validate_inputs({"sequence": "AACCGGTTAA"}).valid
    invalid = tiny_tfbind10_pho4_dataset.validate_inputs({"sequence": "AACCGGTTAN"})
    assert not invalid.valid
    assert invalid.violations[0].code == "invalid_alphabet_symbol"


@pytest.mark.integration
def test_published_dataset_loads_at_pinned_revision() -> None:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")

    dataset = TFBind10Pho4Dataset.from_hub(revision=PUBLISHED_REVISION)
    observations = dataset.load()

    assert dataset.resolved_revision == PUBLISHED_REVISION
    assert len(observations) == 4_160_533
    assert observations.column_names == [
        "sequence",
        "replicate_id",
        "bound_count",
        "input_count",
        "bound_fraction",
        "input_fraction",
        "observed_ddg",
    ]
