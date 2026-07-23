from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.drugmatrix.build import (
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
    build_drugmatrix_release,
    normalize_name,
)


def test_name_normalization_is_exact_and_punctuation_insensitive() -> None:
    assert normalize_name("  Alpha-Beta (HCl) ") == "alphabetahcl"


def test_drugmatrix_knowledge_resources_are_packaged(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)

    assert {artifact["key"] for artifact in artifacts} == set(KNOWLEDGE_RESOURCES)
    assert len(artifacts) == 8
    for artifact in artifacts:
        path = tmp_path / artifact["path"]
        content = path.read_text(encoding="utf-8")
        assert path.is_file()
        assert artifact["size_bytes"] == path.stat().st_size
        assert len(artifact["sha256"]) == 64
        assert content.startswith("# ")
        assert "\n## Summary\n" in content
        assert "\n## Scope\n" in content
        assert "\n## Core knowledge\n" in content
        assert "\n## Conditions, limitations, and uncertainty\n" in content
        assert "\n## References\n" in content


def test_drugmatrix_manifest_references_packaged_knowledge(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "artifact": {
                "path": (
                    "data/drugmatrix_clinical_pathology/observations.parquet"
                ),
                "sha256": "test-artifact-sha256",
            },
            "knowledge": artifacts,
        },
    )

    manifest = DatasetManifest.from_json(
        (
            tmp_path
            / "manifests"
            / "drugmatrix_clinical_pathology.json"
        ).read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


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
    assert set(manifest["knowledge"]) == set(KNOWLEDGE_RESOURCES)
    assert len(provenance["knowledge"]) == 8
