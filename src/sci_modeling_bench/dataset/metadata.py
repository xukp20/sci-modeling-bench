"""Typed dataset identity and provenance metadata."""

from pydantic import BaseModel, ConfigDict, Field


class SourceReference(BaseModel):
    """Reference to an upstream data source."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    url: str | None = None
    version: str | None = None
    revision: str | None = None
    checksum: str | None = None
    notes: str | None = None


class Citation(BaseModel):
    """Human-readable citation for a dataset or upstream artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    text: str = Field(min_length=1)
    url: str | None = None


class DatasetMetadata(BaseModel):
    """Stable semantic metadata for a published dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    license: str = Field(min_length=1)
    source: tuple[SourceReference, ...] = ()
    citation: tuple[Citation, ...] = ()
