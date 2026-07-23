from __future__ import annotations

import json
from pathlib import Path

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.cell_dag_nas.build import (
    ARCHITECTURE_ENCODING_DESCRIPTION,
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
)


def test_manifest_discloses_architecture_token_encoding(tmp_path: Path) -> None:
    _write_release_metadata(
        tmp_path,
        {
            "default_protocol": {
                "visible_canonical_graphs": 1,
                "visible_alias_rows": 1,
            }
        },
    )

    manifest = json.loads(
        (
            tmp_path / "manifests" / "cell_dag_nas.json"
        ).read_text(encoding="utf-8")
    )
    description = manifest["inputs"][0]["description"]

    assert description == ARCHITECTURE_ENCODING_DESCRIPTION
    assert "0=start" in description
    assert "6=1x1 convolution" in description
    assert "7=3x3 convolution" in description
    assert "8=3x3 max-pooling" in description
    assert "9=no edge" in description
    assert "10=edge" in description
    assert "strict upper triangle" in description
    assert "(0,1), (0,2)" in description
    assert "at most 9 edges" in description
    assert "path from input to output" in description


def test_cell_dag_nas_knowledge_resources_are_packaged(tmp_path: Path) -> None:
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


def test_cell_dag_nas_manifest_references_knowledge(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "default_protocol": {
                "visible_canonical_graphs": 1,
                "visible_alias_rows": 1,
            },
            "knowledge": artifacts,
        },
    )

    manifest = DatasetManifest.from_json(
        (
            tmp_path / "manifests" / "cell_dag_nas.json"
        ).read_text(encoding="utf-8")
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key
