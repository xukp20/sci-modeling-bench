from __future__ import annotations

import json
import os

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.suites.design_bench.tfbind10_pho4.build import (
    build_tfbind10_pho4_release,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    EXPECTED_OBSERVATION_ROWS,
)


@pytest.mark.integration
def test_builder_replays_pinned_figshare_archive(tmp_path) -> None:
    archive = os.environ.get("SMB_TFBIND10_PHO4_ARCHIVE")
    if not archive:
        pytest.skip("SMB_TFBIND10_PHO4_ARCHIVE is not configured")

    provenance = build_tfbind10_pho4_release(archive, tmp_path)
    data = HFDataset.from_parquet(
        str(tmp_path / "data" / "tfbind10_pho4" / "observations.parquet")
    )
    manifest = json.loads((tmp_path / "manifests" / "tfbind10_pho4.json").read_text())

    assert len(data) == EXPECTED_OBSERVATION_ROWS
    assert provenance["statistics"]["unique_sequences"] == 4**10
    assert "fixed CACGTG E-box core" in manifest["inputs"][0]["description"]
    assert "NNNNNCACGTGNNNNN" in manifest["inputs"][0]["description"]
    assert manifest["targets"][0]["name"] == "observed_ddg"
    assert "affinity_score" not in data.column_names
