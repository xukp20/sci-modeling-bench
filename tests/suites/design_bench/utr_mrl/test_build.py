from __future__ import annotations

import json
import os

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.suites.design_bench.utr_mrl.build import (
    build_utr_mrl_release,
)


@pytest.mark.integration
def test_builder_replays_pinned_mrnabench_parquet(tmp_path) -> None:
    source = os.environ.get("SMB_UTR_MRL_SOURCE_PARQUET")
    if not source:
        pytest.skip("SMB_UTR_MRL_SOURCE_PARQUET is not configured")

    provenance = build_utr_mrl_release(source, tmp_path)
    data = HFDataset.from_parquet(
        str(tmp_path / "data" / "utr_mrl_egfp_unmodified" / "measurements.parquet")
    )
    manifest = json.loads(
        (tmp_path / "manifests" / "utr_mrl_egfp_unmodified.json").read_text()
    )

    assert len(data) == 318_468
    assert provenance["statistics"]["compositional_partition"] == {
        "candidate_pool": 5_043,
        "combination_counts": {
            "mixed": 236_548,
            "no_uaug_strong": 35_534,
            "no_uaug_weak": 2_533,
            "uaug_strong": 38_810,
            "uaug_weak": 5_043,
        },
        "visible_observations": 76_877,
    }
    assert manifest["splits"][0]["attributes"]["reporter"] == "eGFP"
    assert manifest["knowledge"] == {}
