"""Semantic field schema and common machine-readable constraints."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

JsonScalar = str | int | float | bool | None


class NumericRangeConstraint(BaseModel):
    """Inclusive or exclusive numeric bounds applied to scalar leaves."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["range"] = "range"
    minimum: float | None = None
    maximum: float | None = None
    inclusive_minimum: bool = True
    inclusive_maximum: bool = True

    @model_validator(mode="after")
    def validate_bounds(self) -> NumericRangeConstraint:
        if self.minimum is None and self.maximum is None:
            raise ValueError("range constraint requires minimum or maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("range minimum cannot exceed maximum")
        return self


class AllowedValuesConstraint(BaseModel):
    """Finite set of values allowed for a scalar or sequence leaves."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["allowed_values"] = "allowed_values"
    values: tuple[JsonScalar, ...] = Field(min_length=1)


class AlphabetConstraint(BaseModel):
    """Character alphabet for a string-valued field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["alphabet"] = "alphabet"
    symbols: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_symbols(self) -> AlphabetConstraint:
        if any(len(symbol) != 1 for symbol in self.symbols):
            raise ValueError("alphabet symbols must be single characters")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("alphabet symbols must be unique")
        return self


class LengthConstraint(BaseModel):
    """Length bounds for a string or sized sequence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["length"] = "length"
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> LengthConstraint:
        if self.minimum is None and self.maximum is None:
            raise ValueError("length constraint requires minimum or maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("length minimum cannot exceed maximum")
        return self


class FiniteConstraint(BaseModel):
    """Require every numeric scalar leaf to be finite."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["finite"] = "finite"


ConstraintSpec = Annotated[
    NumericRangeConstraint
    | AllowedValuesConstraint
    | AlphabetConstraint
    | LengthConstraint
    | FiniteConstraint,
    Field(discriminator="kind"),
]


class FieldSpec(BaseModel):
    """Scientific semantics and constraints for one published column."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    unit: str | None = None
    required: bool = True
    constraints: tuple[ConstraintSpec, ...] = ()

    @model_validator(mode="after")
    def validate_constraint_kinds(self) -> FieldSpec:
        kinds = [constraint.kind for constraint in self.constraints]
        if len(kinds) != len(set(kinds)):
            raise ValueError(f"field {self.name!r} has duplicate constraint kinds")
        return self


class DatasetSchema(BaseModel):
    """Role assignment for input, target, and context columns."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: tuple[FieldSpec, ...] = Field(min_length=1)
    targets: tuple[FieldSpec, ...] = Field(min_length=1)
    context: tuple[FieldSpec, ...] = ()

    @model_validator(mode="after")
    def validate_unique_names(self) -> DatasetSchema:
        names = [field.name for field in self.fields]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"field names must be unique across roles: {duplicates}")
        return self

    @property
    def fields(self) -> tuple[FieldSpec, ...]:
        """Return every declared field in stable role order."""

        return self.inputs + self.targets + self.context

    @property
    def field_names(self) -> tuple[str, ...]:
        """Return every declared field name in stable role order."""

        return tuple(field.name for field in self.fields)
