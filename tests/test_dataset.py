from __future__ import annotations

import copy
from typing import Any

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import dataset as dataset_module
from sci_modeling_bench.dataset.dataset import Dataset
from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.dataset.source import HubDatasetSource
from sci_modeling_bench.dataset.validation import (
    DatasetValidator,
    ValidationReport,
    Violation,
)
from sci_modeling_bench.exceptions import SchemaMismatchError


def make_dataset(fake_repository: Any) -> Dataset:
    manifest = DatasetManifest.from_json(
        fake_repository.read_text("manifests/tfbind8.json")
    )
    return Dataset(manifest, fake_repository, config_name="tfbind8")


def test_dataset_loads_and_caches_default_split(fake_repository: Any) -> None:
    dataset = make_dataset(fake_repository)

    first = dataset.load()
    second = dataset.load()

    assert first is second
    assert fake_repository.load_calls == [("tfbind8", "six6_ref_r1", False)]
    assert dataset.repo_id == "local/example"
    assert dataset.config_name == "tfbind8"
    assert dataset.default_split == "six6_ref_r1"
    assert dataset.available_splits == ("six6_ref_r1",)
    assert dataset.split().attributes["transcription_factor"] == "SIX6"
    assert dataset.resolved_revision == "0123456789abcdef"


def test_dataset_reads_knowledge_lazily(fake_repository: Any) -> None:
    dataset = make_dataset(fake_repository)
    fake_repository.read_calls.clear()

    assert dataset.knowledge
    assert fake_repository.read_calls == []
    assert dataset.knowledge.read_text("domain_overview").startswith("# Domain")
    assert fake_repository.read_calls == ["knowledge/domain-overview.md"]


def test_dataset_validates_inputs_and_full_data(fake_repository: Any) -> None:
    dataset = make_dataset(fake_repository)

    valid = dataset.validate_inputs({"sequence": "AACCGGTT"})
    invalid = dataset.validate_inputs({"sequence": "AACCGGTX"})
    full = dataset.validate_dataset()

    assert valid.valid
    assert not invalid.valid
    assert {item.code for item in invalid.violations} == {
        "invalid_alphabet_symbol"
    }
    assert full.valid


def test_dataset_custom_validator_is_composed(fake_repository: Any) -> None:
    class RejectHomopolymers(DatasetValidator):
        def validate_inputs(self, inputs, context=None) -> ValidationReport:
            if len(set(inputs["sequence"])) == 1:
                return ValidationReport(
                    violations=(
                        Violation(
                            code="homopolymer",
                            field="sequence",
                            message="homopolymers are not accepted",
                        ),
                    )
                )
            return ValidationReport()

    manifest = DatasetManifest.from_json(
        fake_repository.read_text("manifests/tfbind8.json")
    )
    dataset = Dataset(
        manifest,
        fake_repository,
        config_name="tfbind8",
        validator=RejectHomopolymers(),
    )

    assert not dataset.validate_inputs({"sequence": "AAAAAAAA"}).valid


def test_dataset_rejects_missing_declared_columns(
    fake_repository: Any,
    manifest_data: dict,
) -> None:
    class MissingTargetRepository(type(fake_repository)):
        def load(
            self,
            config_name: str,
            split: str,
            *,
            streaming: bool,
        ) -> Any:
            return HFDataset.from_dict({"sequence": ["AACCGGTT"]})

    repository = MissingTargetRepository(copy.deepcopy(manifest_data))
    dataset = make_dataset(repository)

    with pytest.raises(SchemaMismatchError, match="score"):
        dataset.load()


def test_dataset_rejects_undeclared_split(fake_repository: Any) -> None:
    dataset = make_dataset(fake_repository)

    with pytest.raises(ValueError, match="not declared"):
        dataset.load("unknown")


def test_dataset_from_source_selects_config_manifest(
    monkeypatch,
    fake_repository: Any,
) -> None:
    def fake_resolve(repo_id, revision=None, *, token=None):
        assert repo_id == "mirror/design-bench"
        assert revision == "v1"
        assert token is None
        return fake_repository

    monkeypatch.setattr(
        dataset_module.HubDatasetRepository,
        "resolve",
        fake_resolve,
    )

    dataset = Dataset.from_source(
        HubDatasetSource(
            repo_id="mirror/design-bench",
            config_name="tfbind8",
            revision="v1",
        )
    )

    assert dataset.config_name == "tfbind8"
    assert fake_repository.read_calls == [
        "scimodelingbench.json",
        "manifests/tfbind8.json",
    ]


def test_dataset_rejects_declared_row_count_mismatch(
    fake_repository: Any,
    manifest_data: dict,
) -> None:
    manifest_data["splits"][0]["num_rows"] = 3
    dataset = make_dataset(type(fake_repository)(manifest_data))

    with pytest.raises(SchemaMismatchError, match="declares 3 rows"):
        dataset.load()
