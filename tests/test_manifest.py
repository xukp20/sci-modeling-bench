from __future__ import annotations

import copy
import json

import pytest

from sci_modeling_bench.dataset.manifest import (
    DatasetCollectionManifest,
    DatasetManifest,
)
from sci_modeling_bench.exceptions import ManifestError


def test_manifest_builds_metadata_and_schema(manifest_data: dict) -> None:
    manifest = DatasetManifest.from_json(json.dumps(manifest_data))

    assert manifest.metadata.dataset_id == "example/tfbind8"
    assert manifest.metadata.version == "1.0.0"
    assert manifest.dataset_schema.field_names == ("sequence", "score")
    assert manifest.default_split == "six6_ref_r1"
    assert manifest.split_names == ("six6_ref_r1",)


def test_manifest_rejects_duplicate_field_names(manifest_data: dict) -> None:
    invalid = copy.deepcopy(manifest_data)
    invalid["targets"][0]["name"] = "sequence"

    with pytest.raises(ManifestError, match="field names must be unique"):
        DatasetManifest.from_json(json.dumps(invalid))


@pytest.mark.parametrize(
    "path",
    ["../secret.md", "/absolute/file.md", "knowledge/"],
)
def test_manifest_rejects_unsafe_knowledge_paths(
    manifest_data: dict,
    path: str,
) -> None:
    invalid = copy.deepcopy(manifest_data)
    invalid["knowledge"]["domain_overview"]["path"] = path

    with pytest.raises(ManifestError, match="knowledge path"):
        DatasetManifest.from_json(json.dumps(invalid))


def test_manifest_rejects_unknown_fields(manifest_data: dict) -> None:
    invalid = copy.deepcopy(manifest_data)
    invalid["unexpected"] = True

    with pytest.raises(ManifestError, match="Extra inputs are not permitted"):
        DatasetManifest.from_json(json.dumps(invalid))


def test_manifest_rejects_unknown_default_split(manifest_data: dict) -> None:
    invalid = copy.deepcopy(manifest_data)
    invalid["default_split"] = "missing"

    with pytest.raises(ManifestError, match="default_split"):
        DatasetManifest.from_json(json.dumps(invalid))


def test_collection_selects_default_and_named_configs() -> None:
    collection = DatasetCollectionManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "default_config": "first",
                "configs": {
                    "first": {"manifest": "manifests/first.json"},
                    "second": {"manifest": "manifests/second.json"},
                },
            }
        )
    )

    assert collection.select(None)[0] == "first"
    assert collection.select("second")[1].manifest == "manifests/second.json"


def test_collection_rejects_unsafe_manifest_path() -> None:
    with pytest.raises(ManifestError, match="config manifest path"):
        DatasetCollectionManifest.from_json(
            json.dumps(
                {
                    "schema_version": 1,
                    "default_config": "tfbind8",
                    "configs": {
                        "tfbind8": {"manifest": "../tfbind8.json"}
                    },
                }
            )
        )
