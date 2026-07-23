from __future__ import annotations

import os
from pathlib import Path

import pytest

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.superconductor.build import (
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
    build_superconductor_release,
)


def test_superconductor_knowledge_resources_are_packaged(tmp_path: Path) -> None:
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


def test_superconductor_manifest_references_packaged_knowledge(
    tmp_path: Path,
) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "artifact": {
                "path": "data/superconductor/composition_groups.parquet",
                "sha256": "test-artifact-sha256",
            },
            "knowledge": artifacts,
        },
    )

    manifest = DatasetManifest.from_json(
        (tmp_path / "manifests" / "superconductor.json").read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


@pytest.mark.integration
def test_builder_replays_the_pinned_uci_archive(tmp_path: Path) -> None:
    archive = os.environ.get("SMB_SUPERCONDUCTOR_ARCHIVE")
    if archive is None:
        pytest.skip("SMB_SUPERCONDUCTOR_ARCHIVE is not configured")

    provenance = build_superconductor_release(archive, tmp_path)

    assert provenance["statistics"]["source_rows"] == 21_263
    assert provenance["statistics"]["composition_groups"] == 15_164
    assert provenance["statistics"]["conflict_groups_removed"] == 0
    assert len(provenance["knowledge"]) == 7
    assert (tmp_path / "data/superconductor/composition_groups.parquet").is_file()
