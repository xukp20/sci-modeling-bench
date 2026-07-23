from __future__ import annotations

import os
from pathlib import Path

import pytest

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.gfp.build import (
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
    build_gfp_release,
)


def test_gfp_knowledge_resources_are_packaged(tmp_path: Path) -> None:
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


def test_gfp_manifest_references_packaged_knowledge(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "statistics": {
                "clean_nucleotide_observations": 56_086,
                "clean_barcode_observations": 65_678,
            },
            "artifact": {
                "path": "data/gfp/proteins.parquet",
                "sha256": "test-artifact-sha256",
            },
            "knowledge": artifacts,
        },
    )

    manifest = DatasetManifest.from_json(
        (tmp_path / "manifests" / "gfp.json").read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


@pytest.mark.integration
def test_formal_source_build(tmp_path: Path) -> None:
    source_dir_value = os.environ.get("SMB_GFP_SOURCE_DIR")
    if source_dir_value is None:
        pytest.skip("SMB_GFP_SOURCE_DIR is not configured")
    source_dir = Path(source_dir_value)

    provenance = build_gfp_release(
        source_dir / "amino_acid_genotypes_to_brightness.tsv",
        source_dir / "nucleotide_genotypes_to_brightness.tsv",
        source_dir / "barcodes_to_brightness.tsv",
        source_dir / "genotypes.tsv",
        source_dir / "avGFP_reference_sequence.fa",
        tmp_path,
    )

    assert provenance["statistics"]["canonical_proteins"] == 51_715
    assert provenance["statistics"]["clean_nucleotide_observations"] == 56_086
    assert provenance["statistics"]["clean_barcode_observations"] == 65_678
    assert provenance["statistics"]["default_protocol"] == {
        "visible_max_percentile": 80.0,
        "cutoff": 3.6496037176800002,
        "visible_proteins": 41_372,
        "candidate_pool": 10_343,
    }
    assert provenance["artifact"]["sha256"] == (
        "5340280e9e01b9ed2c32cbb429d2d4bb28513f44daa764511be4db8b6fb66d98"
    )
    assert len(provenance["knowledge"]) == 8
