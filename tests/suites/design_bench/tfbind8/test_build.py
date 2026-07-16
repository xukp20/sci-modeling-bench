from __future__ import annotations

import os
from pathlib import Path

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench import TFBind8Validator
from sci_modeling_bench.suites.design_bench.tfbind8.build import (
    CANONICAL_ROW_COUNT,
    CONFIG_NAME,
    SPLIT_NAME,
    build_tfbind8_release,
)


@pytest.mark.integration
def test_build_tfbind8_from_pinned_source(tmp_path: Path) -> None:
    archive = os.environ.get("SMB_TFBIND8_ARCHIVE")
    if archive is None:
        pytest.skip("SMB_TFBIND8_ARCHIVE is not configured")
    legacy_data_dir = os.environ.get("SMB_TFBIND8_LEGACY_DATA_DIR")

    provenance = build_tfbind8_release(
        archive,
        tmp_path,
        legacy_data_dir=legacy_data_dir,
    )
    data = HFDataset.from_parquet(
        str(tmp_path / "data" / CONFIG_NAME / f"{SPLIT_NAME}.parquet")
    )
    manifest = DatasetManifest.from_json(
        (tmp_path / "manifests" / f"{CONFIG_NAME}.json").read_text()
    )

    assert len(data) == CANONICAL_ROW_COUNT
    assert data.column_names == ["sequence", "e_score", "normalized_e_score"]
    assert data[0]["sequence"] == "AAAAAAAA"
    assert data[-1]["sequence"] == "TTTTTTTT"
    assert min(data["e_score"]) == pytest.approx(-0.47907)
    assert max(data["e_score"]) == pytest.approx(0.49105)
    assert min(data["normalized_e_score"]) == 0.0
    assert max(data["normalized_e_score"]) == 1.0
    assert manifest.default_split == SPLIT_NAME
    assert manifest.knowledge == {}
    assert provenance["canonicalization"]["duplicate_rows_removed"] == 256
    assert TFBind8Validator().validate_dataset(data).valid
    if legacy_data_dir is not None:
        assert provenance["legacy_parity"]["status"] == "verified"
