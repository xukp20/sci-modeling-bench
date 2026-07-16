"""Main Dataset aggregate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sci_modeling_bench.dataset._hub import DatasetRepository, HubDatasetRepository
from sci_modeling_bench.dataset.knowledge import Knowledge, KnowledgeResource
from sci_modeling_bench.dataset.manifest import (
    DatasetCollectionManifest,
    DatasetManifest,
    DatasetSplit,
)
from sci_modeling_bench.dataset.metadata import DatasetMetadata
from sci_modeling_bench.dataset.schema import DatasetSchema
from sci_modeling_bench.dataset.source import HubDatasetSource
from sci_modeling_bench.dataset.validation import (
    DatasetValidator,
    ValidationReport,
    Violation,
    validate_fields,
)
from sci_modeling_bench.exceptions import SchemaMismatchError

COLLECTION_MANIFEST_FILENAME = "scimodelingbench.json"


class Dataset:
    """Pinned scientific observations with semantics and validation."""

    def __init__(
        self,
        manifest: DatasetManifest,
        repository: DatasetRepository,
        *,
        config_name: str,
        validator: DatasetValidator | None = None,
    ) -> None:
        self._manifest = manifest
        self._repository = repository
        self._config_name = config_name
        self._validator = validator or DatasetValidator()
        self._loaded: dict[str, Any] = {}
        self._knowledge = Knowledge(
            {
                name: KnowledgeResource(
                    title=spec.title,
                    description=spec.description,
                    path=spec.path,
                    media_type=spec.media_type,
                    _reader=repository.read_text,
                )
                for name, spec in manifest.knowledge.items()
            }
        )

    @classmethod
    def from_hub(
        cls,
        repo_id: str,
        config_name: str | None = None,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> Dataset:
        """Load one config from a pinned Hugging Face Dataset repository."""

        return cls.from_source(
            HubDatasetSource(
                repo_id=repo_id,
                config_name=config_name,
                revision=revision,
            ),
            token=token,
            validator=validator,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> Dataset:
        """Load a Dataset from an explicit, reusable Hub source reference."""

        repository = HubDatasetRepository.resolve(
            source.repo_id,
            source.revision,
            token=token,
        )
        collection = DatasetCollectionManifest.from_json(
            repository.read_text(COLLECTION_MANIFEST_FILENAME)
        )
        config_name, config = collection.select(source.config_name)
        manifest = DatasetManifest.from_json(
            repository.read_text(config.manifest)
        )
        return cls(
            manifest,
            repository,
            config_name=config_name,
            validator=validator,
        )

    @property
    def metadata(self) -> DatasetMetadata:
        return self._manifest.metadata

    @property
    def schema(self) -> DatasetSchema:
        return self._manifest.dataset_schema

    @property
    def knowledge(self) -> Knowledge:
        return self._knowledge

    @property
    def config_name(self) -> str:
        return self._config_name

    @property
    def default_split(self) -> str:
        return self._manifest.default_split

    @property
    def splits(self) -> tuple[DatasetSplit, ...]:
        return self._manifest.splits

    @property
    def available_splits(self) -> tuple[str, ...]:
        return self._manifest.split_names

    def split(self, name: str | None = None) -> DatasetSplit:
        """Return metadata for a declared split."""

        selected = name or self.default_split
        for split in self.splits:
            if split.name == selected:
                return split
        available = ", ".join(self.available_splits)
        raise ValueError(
            f"split {selected!r} is not declared for config "
            f"{self.config_name!r}; available: {available}"
        )

    @property
    def repo_id(self) -> str:
        return self._repository.repo_id

    @property
    def resolved_revision(self) -> str:
        return self._repository.resolved_revision

    @property
    def features(self) -> Any:
        """Return physical Hugging Face features for the default split."""

        return self.load().features

    def load(
        self,
        split: str | None = None,
        *,
        streaming: bool = False,
    ) -> Any:
        """Load a standard Hugging Face Dataset or IterableDataset."""

        selected_split = split or self._manifest.default_split
        split_metadata = self.split(selected_split)
        if not streaming and selected_split in self._loaded:
            return self._loaded[selected_split]

        data = self._repository.load(
            self.config_name,
            selected_split,
            streaming=streaming,
        )
        self._ensure_declared_features(data)
        if not streaming and split_metadata.num_rows is not None:
            actual_rows = len(data)
            if actual_rows != split_metadata.num_rows:
                raise SchemaMismatchError(
                    f"config {self.config_name!r}, split {selected_split!r} declares "
                    f"{split_metadata.num_rows} rows but loaded {actual_rows}"
                )
        if not streaming:
            self._loaded[selected_split] = data
        return data

    def validate_inputs(
        self,
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        mapping_report = _require_mapping(inputs, "inputs")
        if not mapping_report.valid:
            return mapping_report
        context_values = {} if context is None else context
        context_report = _require_mapping(context_values, "context")
        if not context_report.valid:
            return context_report

        features = self.features
        return ValidationReport.combine(
            validate_fields(inputs, self.schema.inputs, features=features),
            validate_fields(context_values, self.schema.context, features=features),
            self._validator.validate_inputs(inputs, context),
        )

    def validate_targets(
        self,
        targets: Mapping[str, Any],
        inputs: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        mapping_report = _require_mapping(targets, "targets")
        if not mapping_report.valid:
            return mapping_report
        context_values = {} if context is None else context
        context_report = _require_mapping(context_values, "context")
        if not context_report.valid:
            return context_report

        features = self.features
        return ValidationReport.combine(
            validate_fields(targets, self.schema.targets, features=features),
            validate_fields(context_values, self.schema.context, features=features),
            self._validator.validate_targets(targets, inputs, context),
        )

    def validate_observation(
        self,
        observation: Mapping[str, Any],
    ) -> ValidationReport:
        mapping_report = _require_mapping(observation, "observation")
        if not mapping_report.valid:
            return mapping_report

        features = self.features
        generic = validate_fields(
            observation,
            self.schema.fields,
            features=features,
            reject_unknown=False,
        )
        return ValidationReport.combine(
            generic,
            self._validator.validate_observation(observation),
        )

    def validate_dataset(self, data: Any | None = None) -> ValidationReport:
        """Validate all observations plus optional dataset-level custom checks."""

        selected_data = data if data is not None else self.load()
        self._ensure_declared_features(selected_data)
        violations: list[Violation] = []
        for row_index, observation in enumerate(selected_data):
            report = self.validate_observation(observation)
            if report.violations:
                violations.extend(report.at_row(row_index).violations)
        violations.extend(
            self._validator.validate_dataset(selected_data).violations
        )
        return ValidationReport(violations=tuple(violations))

    def _ensure_declared_features(self, data: Any) -> None:
        features = getattr(data, "features", None)
        if features is None:
            return
        missing = sorted(set(self.schema.field_names) - set(features))
        if missing:
            raise SchemaMismatchError(
                f"dataset {self.metadata.dataset_id!r} is missing declared columns: {missing}"
            )


def _require_mapping(value: Any, label: str) -> ValidationReport:
    if isinstance(value, Mapping):
        return ValidationReport()
    return ValidationReport(
        violations=(
            Violation(
                code="invalid_mapping",
                message=f"{label} must be a mapping keyed by semantic column name",
            ),
        )
    )
