"""Strict parser for the SciModelingBench dataset manifest."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from sci_modeling_bench.dataset.metadata import (
    Citation,
    DatasetMetadata,
    SourceReference,
)
from sci_modeling_bench.dataset.schema import DatasetSchema, FieldSpec, JsonScalar
from sci_modeling_bench.exceptions import ManifestError

_KNOWLEDGE_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_HUB_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _validate_repository_path(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a safe repository-relative path")
    if value.endswith("/"):
        raise ValueError(f"{label} must identify a file")
    return value


class KnowledgeResourceSpec(BaseModel):
    """Manifest entry for a repository-relative text resource."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    title: str = Field(min_length=1)
    description: str | None = None
    path: str = Field(min_length=1)
    media_type: Literal["text/markdown", "text/plain"] = "text/markdown"

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_repository_path(value, "knowledge path")


class DatasetConfigSpec(BaseModel):
    """Index entry for one Hugging Face dataset config."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    manifest: str = Field(min_length=1)

    @field_validator("manifest")
    @classmethod
    def validate_manifest_path(cls, value: str) -> str:
        return _validate_repository_path(value, "config manifest path")


class DatasetCollectionManifest(BaseModel):
    """Repository-level index mapping HF configs to dataset manifests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal[1]
    default_config: str = Field(min_length=1)
    configs: dict[str, DatasetConfigSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_collection(self) -> DatasetCollectionManifest:
        invalid_names = sorted(
            name for name in self.configs if _HUB_NAME.fullmatch(name) is None
        )
        if invalid_names:
            raise ValueError(
                "config names must use letters, numbers, '.', '_' or '-': "
                f"{invalid_names}"
            )
        if self.default_config not in self.configs:
            raise ValueError("default_config must identify a declared config")

        paths = [config.manifest for config in self.configs.values()]
        duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
        if duplicate_paths:
            raise ValueError(f"config manifest paths must be unique: {duplicate_paths}")
        return self

    @classmethod
    def from_json(cls, content: str | bytes) -> DatasetCollectionManifest:
        try:
            return cls.model_validate_json(content)
        except ValidationError as exc:
            raise ManifestError(f"invalid dataset collection manifest: {exc}") from exc

    def select(self, config_name: str | None) -> tuple[str, DatasetConfigSpec]:
        selected = config_name or self.default_config
        try:
            return selected, self.configs[selected]
        except KeyError as exc:
            available = ", ".join(sorted(self.configs))
            raise ManifestError(
                f"dataset config {selected!r} is not declared; available: {available}"
            ) from exc


class DatasetSplit(BaseModel):
    """Published split metadata shared by every observation in the split."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    num_rows: int | None = Field(default=None, ge=0)
    source: tuple[SourceReference, ...] = ()
    attributes: dict[str, JsonScalar] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if _HUB_NAME.fullmatch(value) is None:
            raise ValueError(
                "split name must use letters, numbers, '.', '_' or '-'"
            )
        return value


class DatasetManifest(BaseModel):
    """Versioned machine-readable description stored with a HF dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal[1]
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    default_split: str = Field(min_length=1)
    description: str = Field(min_length=1)
    license: str = Field(min_length=1)
    source: tuple[SourceReference, ...] = ()
    citation: tuple[Citation, ...] = ()
    inputs: tuple[FieldSpec, ...] = Field(min_length=1)
    targets: tuple[FieldSpec, ...] = Field(min_length=1)
    context: tuple[FieldSpec, ...] = ()
    splits: tuple[DatasetSplit, ...] = Field(min_length=1)
    knowledge: dict[str, KnowledgeResourceSpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_manifest(self) -> DatasetManifest:
        DatasetSchema(inputs=self.inputs, targets=self.targets, context=self.context)

        split_names = [split.name for split in self.splits]
        duplicate_splits = sorted(
            {name for name in split_names if split_names.count(name) > 1}
        )
        if duplicate_splits:
            raise ValueError(f"split names must be unique: {duplicate_splits}")
        if self.default_split not in split_names:
            raise ValueError("default_split must identify a declared split")

        invalid_keys = sorted(
            key for key in self.knowledge if _KNOWLEDGE_KEY.fullmatch(key) is None
        )
        if invalid_keys:
            raise ValueError(
                f"knowledge keys must use stable snake_case names: {invalid_keys}"
            )

        paths = [resource.path for resource in self.knowledge.values()]
        duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
        if duplicate_paths:
            raise ValueError(
                f"knowledge resource paths must be unique: {duplicate_paths}"
            )
        return self

    @classmethod
    def from_json(cls, content: str | bytes) -> DatasetManifest:
        """Parse a manifest and expose validation failures as package errors."""

        try:
            return cls.model_validate_json(content)
        except ValidationError as exc:
            raise ManifestError(f"invalid dataset manifest: {exc}") from exc

    @property
    def metadata(self) -> DatasetMetadata:
        """Build immutable public metadata from the manifest."""

        return DatasetMetadata(
            dataset_id=self.dataset_id,
            version=self.version,
            description=self.description,
            license=self.license,
            source=self.source,
            citation=self.citation,
        )

    @property
    def dataset_schema(self) -> DatasetSchema:
        """Build the public semantic schema."""

        return DatasetSchema(
            inputs=self.inputs,
            targets=self.targets,
            context=self.context,
        )

    @property
    def split_names(self) -> tuple[str, ...]:
        return tuple(split.name for split in self.splits)
