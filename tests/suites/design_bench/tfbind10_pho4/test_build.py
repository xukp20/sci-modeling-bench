from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.build import (
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
    build_tfbind10_pho4_release,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    EXPECTED_OBSERVATION_ROWS,
)


def test_tfbind10_pho4_knowledge_resources_are_packaged(
    tmp_path: Path,
) -> None:
    artifacts = _write_knowledge_resources(tmp_path)

    assert {artifact["key"] for artifact in artifacts} == set(KNOWLEDGE_RESOURCES)
    assert len(artifacts) == 7
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


def test_tfbind10_pho4_manifest_references_packaged_knowledge(
    tmp_path: Path,
) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "artifact": {
                "path": "data/tfbind10_pho4/observations.parquet",
                "sha256": "test-artifact-sha256",
            },
            "knowledge": artifacts,
        },
    )

    manifest = DatasetManifest.from_json(
        (tmp_path / "manifests" / "tfbind10_pho4.json").read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


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
    assert set(manifest["knowledge"]) == set(KNOWLEDGE_RESOURCES)
    assert len(provenance["knowledge"]) == 7
