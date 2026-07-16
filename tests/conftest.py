"""Shared test fixtures."""

from __future__ import annotations

import json
from typing import Any

import pytest
from datasets import Dataset as HFDataset


@pytest.fixture
def manifest_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": "example/tfbind8",
        "version": "1.0.0",
        "description": "A small transcription-factor binding fixture.",
        "license": "CC-BY-4.0",
        "source": [
            {
                "name": "Example source",
                "url": "https://example.com/data",
                "version": "1",
            }
        ],
        "citation": [
            {
                "text": "Example et al. (2026)",
                "url": "https://example.com/paper",
            }
        ],
        "inputs": [
            {
                "name": "sequence",
                "description": "Eight-base DNA sequence.",
                "constraints": [
                    {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                    {"kind": "length", "minimum": 8, "maximum": 8},
                ],
            }
        ],
        "targets": [
            {
                "name": "score",
                "description": "Binding score.",
                "constraints": [{"kind": "finite"}],
            }
        ],
        "context": [],
        "splits": [
            {
                "name": "six6_ref_r1",
                "description": "SIX6 reference replicate 1.",
                "num_rows": 2,
                "attributes": {
                    "transcription_factor": "SIX6",
                    "allele": "REF",
                    "replicate": 1,
                },
            }
        ],
        "default_split": "six6_ref_r1",
        "knowledge": {
            "domain_overview": {
                "title": "Domain overview",
                "description": "Background for the fixture.",
                "path": "knowledge/domain-overview.md",
                "media_type": "text/markdown",
            }
        },
    }


class FakeRepository:
    repo_id = "local/example"
    resolved_revision = "0123456789abcdef"

    def __init__(self, manifest_data: dict[str, Any]) -> None:
        self._collection = json.dumps(
            {
                "schema_version": 1,
                "default_config": "tfbind8",
                "configs": {
                    "tfbind8": {"manifest": "manifests/tfbind8.json"}
                },
            }
        )
        self._manifest = json.dumps(manifest_data)
        self._data = HFDataset.from_dict(
            {
                "sequence": ["AACCGGTT", "TTGGCCAA"],
                "score": [0.25, 0.75],
            }
        )
        self.read_calls: list[str] = []
        self.load_calls: list[tuple[str, str, bool]] = []

    def read_text(self, path: str) -> str:
        self.read_calls.append(path)
        if path == "scimodelingbench.json":
            return self._collection
        if path == "manifests/tfbind8.json":
            return self._manifest
        if path == "knowledge/domain-overview.md":
            return "# Domain overview\n"
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        self.load_calls.append((config_name, split, streaming))
        return self._data


@pytest.fixture
def fake_repository(manifest_data: dict[str, Any]) -> FakeRepository:
    return FakeRepository(manifest_data)
