"""Uniform, disclosure-scoped metadata for Agent-visible Protocol outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, Mapping, TypeVar

from datasets import Dataset as HFDataset
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from sci_modeling_bench.dataset import Citation, Dataset, SourceReference
from sci_modeling_bench.dataset.schema import ConstraintSpec


AgentInputDataT = TypeVar("AgentInputDataT")
AgentFieldRole = Literal["input", "target", "context"]
AgentViewRole = Literal["observations", "candidates", "auxiliary"]


class AgentInputField(BaseModel):
    """Scientific and physical description of one visible table column."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    role: AgentFieldRole
    description: str = Field(min_length=1)
    physical_type: str = Field(min_length=1)
    unit: str | None = None
    required: bool = True
    constraints: tuple[ConstraintSpec, ...] = ()
    source_field: str | None = None


class AgentInputView(BaseModel):
    """One named Agent-visible table and its complete visible schema."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    role: AgentViewRole
    description: str = Field(min_length=1)
    kind: Literal["table"] = "table"
    num_rows: int = Field(ge=0)
    fields: tuple[AgentInputField, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_fields(self) -> AgentInputView:
        names = [field.name for field in self.fields]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Agent input view fields must be unique: {duplicates}")
        return self


class AgentInputContext(BaseModel):
    """One scalar or structured scientific constant visible to the Agent."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    value: JsonValue
    unit: str | None = None


class AgentInputManifest(BaseModel):
    """Machine-readable description of exactly what one Protocol disclosed."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal[1] = 1
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_description: str = Field(min_length=1)
    dataset_license: str = Field(min_length=1)
    source: tuple[SourceReference, ...] = ()
    citation: tuple[Citation, ...] = ()
    repo_id: str = Field(min_length=1)
    resolved_revision: str = Field(min_length=1)
    config_name: str = Field(min_length=1)
    split: str = Field(min_length=1)
    split_description: str = Field(min_length=1)
    split_attributes: dict[str, JsonValue] = Field(default_factory=dict)
    protocol_id: str = Field(min_length=1)
    task_id: str | None = None
    views: tuple[AgentInputView, ...] = Field(min_length=1)
    context: tuple[AgentInputContext, ...] = ()

    @model_validator(mode="after")
    def validate_unique_names(self) -> AgentInputManifest:
        view_names = [view.name for view in self.views]
        duplicate_views = sorted(
            {name for name in view_names if view_names.count(name) > 1}
        )
        if duplicate_views:
            raise ValueError(f"Agent input view names must be unique: {duplicate_views}")
        context_names = [item.name for item in self.context]
        duplicate_context = sorted(
            {name for name in context_names if context_names.count(name) > 1}
        )
        if duplicate_context:
            raise ValueError(
                f"Agent input context names must be unique: {duplicate_context}"
            )
        return self

    def for_task(self, task_id: str) -> AgentInputManifest:
        """Return the same disclosure manifest bound to one Task identity."""

        return self.model_copy(update={"task_id": task_id})


@dataclass(frozen=True)
class AgentInputBundle(Generic[AgentInputDataT]):
    """Agent-visible data paired with its disclosure-scoped manifest."""

    data: AgentInputDataT
    manifest: AgentInputManifest


def agent_input_manifest(
    dataset: Dataset,
    *,
    protocol_id: str,
    split: str,
    views: tuple[AgentInputView, ...],
    context: tuple[AgentInputContext, ...] = (),
) -> AgentInputManifest:
    """Build public identity metadata without exposing the canonical manifest."""

    split_spec = dataset.split(split)
    return AgentInputManifest(
        dataset_id=dataset.metadata.dataset_id,
        dataset_version=dataset.metadata.version,
        dataset_description=dataset.metadata.description,
        dataset_license=dataset.metadata.license,
        source=dataset.metadata.source,
        citation=dataset.metadata.citation,
        repo_id=dataset.repo_id,
        resolved_revision=dataset.resolved_revision,
        config_name=dataset.config_name,
        split=split_spec.name,
        split_description=split_spec.description,
        split_attributes=dict(split_spec.attributes),
        protocol_id=protocol_id,
        views=views,
        context=context,
    )


def agent_table_view(
    dataset: Dataset,
    data: HFDataset,
    *,
    name: str,
    role: AgentViewRole,
    description: str,
    overrides: Mapping[str, AgentInputField] | None = None,
) -> AgentInputView:
    """Describe a visible table, requiring semantics for every physical column."""

    selected_overrides = dict(overrides or {})
    schema_fields = {
        field.name: (role, field)
        for role, fields in (
            ("input", dataset.schema.inputs),
            ("target", dataset.schema.targets),
            ("context", dataset.schema.context),
        )
        for field in fields
    }
    fields: list[AgentInputField] = []
    for column in data.column_names:
        override = selected_overrides.pop(column, None)
        if override is not None:
            if override.name != column:
                raise ValueError(
                    f"Agent input field override {override.name!r} does not match "
                    f"column {column!r}"
                )
            fields.append(override)
            continue
        declared = schema_fields.get(column)
        if declared is None:
            raise ValueError(
                f"Agent-visible column {column!r} has no Dataset FieldSpec or "
                "explicit AgentInputField override"
            )
        field_role, field = declared
        fields.append(
            AgentInputField(
                name=column,
                role=field_role,
                description=field.description,
                physical_type=_physical_type(data, column),
                unit=field.unit,
                required=field.required,
                constraints=field.constraints,
                source_field=column,
            )
        )
    if selected_overrides:
        raise ValueError(
            f"Agent input field overrides do not match visible columns: "
            f"{sorted(selected_overrides)}"
        )
    return AgentInputView(
        name=name,
        role=role,
        description=description,
        num_rows=len(data),
        fields=tuple(fields),
    )


def agent_input_field(
    data: HFDataset,
    name: str,
    *,
    role: AgentFieldRole,
    description: str,
    unit: str | None = None,
    required: bool = True,
    constraints: tuple[ConstraintSpec, ...] = (),
    source_field: str | None = None,
) -> AgentInputField:
    """Declare semantics for a visible field derived by a Protocol."""

    return AgentInputField(
        name=name,
        role=role,
        description=description,
        physical_type=_physical_type(data, name),
        unit=unit,
        required=required,
        constraints=constraints,
        source_field=source_field,
    )


def _physical_type(data: HFDataset, column: str) -> str:
    try:
        return str(data.features[column])
    except KeyError as exc:
        raise ValueError(f"Agent input table has no physical feature for {column!r}") from exc
