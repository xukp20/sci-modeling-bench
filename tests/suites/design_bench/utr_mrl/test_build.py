from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.utr_mrl.build import (
    KNOWLEDGE_RESOURCES,
    _write_knowledge_resources,
    _write_release_metadata,
    build_utr_mrl_release,
)


def test_utr_mrl_knowledge_resources_are_packaged(tmp_path: Path) -> None:
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


def test_utr_mrl_manifest_references_packaged_knowledge(tmp_path: Path) -> None:
    artifacts = _write_knowledge_resources(tmp_path)
    _write_release_metadata(
        tmp_path,
        {
            "artifact": {
                "path": (
                    "data/utr_mrl_egfp_unmodified/measurements.parquet"
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
            / "utr_mrl_egfp_unmodified.json"
        ).read_text()
    )
    assert set(manifest.knowledge) == set(KNOWLEDGE_RESOURCES)
    for key, resource in manifest.knowledge.items():
        assert resource.media_type == "text/markdown"
        assert (tmp_path / resource.path).is_file(), key


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
    assert manifest["splits"][0]["attributes"]["main_start_junction"] == (
        "<50-nt variable sequence>ATG"
    )
    sequence_input = manifest["inputs"][0]
    assert "fixed 25-nucleotide leader segment" in sequence_input["description"]
    assert "fixed eGFP main start codon ATG" in sequence_input["description"]
    assert "T represents U" in sequence_input["description"]
    assert set(manifest["knowledge"]) == set(KNOWLEDGE_RESOURCES)
    assert len(provenance["knowledge"]) == 7
