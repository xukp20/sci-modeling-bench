from __future__ import annotations

import json
import os

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.suites.design_bench.drugmatrix.build import (
    build_drugmatrix_release,
    normalize_name,
)


def test_name_normalization_is_exact_and_punctuation_insensitive() -> None:
    assert normalize_name("  Alpha-Beta (HCl) ") == "alphabetahcl"


@pytest.mark.integration
def test_builder_replays_pinned_drugmatrix_sources(tmp_path) -> None:
    clinical = os.environ.get("SMB_DRUGMATRIX_CLINICAL_PATHOLOGY")
    curated = os.environ.get("SMB_DRUGMATRIX_CURATED_CHEMICALS")
    chembl = os.environ.get("SMB_DRUGMATRIX_CHEMBL_ACTIVITY")
    if not all((clinical, curated, chembl)):
        pytest.skip("DrugMatrix source paths are not configured")

    provenance = build_drugmatrix_release(clinical, curated, chembl, tmp_path)
    data = HFDataset.from_parquet(
        str(
            tmp_path
            / "data"
            / "drugmatrix_clinical_pathology"
            / "observations.parquet"
        )
    )
    manifest = json.loads(
        (tmp_path / "manifests" / "drugmatrix_clinical_pathology.json").read_text()
    )

    assert len(data) == 10_605
    assert provenance["statistics"] == {
        "chemical_test_articles": 656,
        "mapped_test_articles": 640,
        "rows": 10_605,
        "rows_with_all_six_endpoints": 10_359,
        "unique_animal_ids": 10_605,
        "unmapped_test_articles": 16,
    }
    assert provenance["measured_pool"]["conditions"] == 390
    assert provenance["measured_pool"]["unique_canonical_smiles"] == 385
    assert provenance["artifact"]["sha256"] == (
        "d597095922573c5b459ec2ce9e693b03a26b6098846dbc90f0bbb78a567099f4"
    )
    assert manifest["knowledge"] == {}
