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
    KNOWLEDGE_RESOURCES,
    SPLIT_NAME,
    _write_knowledge_resources,
    _write_release_metadata,
    build_tfbind8_release,
)


def test_tfbind8_knowledge_resources_are_packaged(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)

    assert {artifact["key"] for artifact in artifacts} == set(KNOWLEDGE_RESOURCES)
    assert len(artifacts) == 6
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


def test_tfbind8_manifest_references_packaged_knowledge(tmp_path: Path) -> None:
    _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "artifact": {
                "path": f"data/{CONFIG_NAME}/{SPLIT_NAME}.parquet",
                "sha256": "test-artifact-sha256",
            },
            "legacy_parity": {"status": "not_run"},
        },
    )

    manifest = DatasetManifest.from_json(
        (tmp_path / "manifests" / f"{CONFIG_NAME}.json").read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


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
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert (tmp_path / resource.path).is_file(), key
    assert len(provenance["knowledge"]) == 6
    assert provenance["canonicalization"]["duplicate_rows_removed"] == 256
    assert TFBind8Validator().validate_dataset(data).valid
    if legacy_data_dir is not None:
        assert provenance["legacy_parity"]["status"] == "verified"
