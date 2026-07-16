"""Validation reports, common constraints, and dataset-specific hooks."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from numbers import Real
from typing import Any, Literal

from datasets import Features
from pyarrow import Table
from pydantic import BaseModel, ConfigDict, computed_field

from sci_modeling_bench.dataset.schema import (
    AllowedValuesConstraint,
    AlphabetConstraint,
    FieldSpec,
    FiniteConstraint,
    LengthConstraint,
    NumericRangeConstraint,
)


class Violation(BaseModel):
    """One machine-readable validation finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    field: str | None = None
    row_index: int | None = None
    severity: Literal["error", "warning"] = "error"


class ValidationReport(BaseModel):
    """Immutable collection of validation findings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    violations: tuple[Violation, ...] = ()

    @computed_field
    @property
    def valid(self) -> bool:
        """Whether the report contains no error-severity violations."""

        return not any(item.severity == "error" for item in self.violations)

    @classmethod
    def combine(cls, *reports: ValidationReport) -> ValidationReport:
        """Combine reports without mutating any source report."""

        return cls(
            violations=tuple(
                violation
                for report in reports
                for violation in report.violations
            )
        )

    def at_row(self, row_index: int) -> ValidationReport:
        """Attach a row index to findings that do not already have one."""

        return ValidationReport(
            violations=tuple(
                violation
                if violation.row_index is not None
                else violation.model_copy(update={"row_index": row_index})
                for violation in self.violations
            )
        )


class DatasetValidator:
    """Optional base class for scientific checks not expressible in a manifest."""

    def validate_inputs(
        self,
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        return ValidationReport()

    def validate_targets(
        self,
        targets: Mapping[str, Any],
        inputs: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        return ValidationReport()

    def validate_observation(
        self,
        observation: Mapping[str, Any],
    ) -> ValidationReport:
        return ValidationReport()

    def validate_dataset(self, data: Any) -> ValidationReport:
        return ValidationReport()


def validate_fields(
    values: Mapping[str, Any],
    fields: tuple[FieldSpec, ...],
    *,
    features: Mapping[str, Any] | None = None,
    reject_unknown: bool = True,
) -> ValidationReport:
    """Validate one role-specific mapping against field declarations."""

    violations: list[Violation] = []
    expected = {field.name for field in fields}

    if reject_unknown:
        for name in sorted(set(values) - expected):
            violations.append(
                Violation(
                    code="unknown_field",
                    field=name,
                    message=f"field {name!r} is not declared for this role",
                )
            )

    for field in fields:
        if field.name not in values:
            if field.required:
                violations.append(
                    Violation(
                        code="missing_field",
                        field=field.name,
                        message=f"required field {field.name!r} is missing",
                    )
                )
            continue

        value = values[field.name]
        if value is None and field.required:
            violations.append(
                Violation(
                    code="null_value",
                    field=field.name,
                    message=f"required field {field.name!r} cannot be null",
                )
            )
            continue
        if features is not None and field.name in features:
            try:
                field_features = Features({field.name: features[field.name]})
                encoded = field_features.encode_example({field.name: value})
                Table.from_pylist([encoded], schema=field_features.arrow_schema)
            except Exception as exc:
                violations.append(
                    Violation(
                        code="feature_mismatch",
                        field=field.name,
                        message=f"value does not match the published feature: {exc}",
                    )
                )

        violations.extend(_validate_constraints(field, value))

    return ValidationReport(violations=tuple(violations))


def _validate_constraints(field: FieldSpec, value: Any) -> Iterable[Violation]:
    for constraint in field.constraints:
        if isinstance(constraint, NumericRangeConstraint):
            yield from _validate_range(field.name, value, constraint)
        elif isinstance(constraint, AllowedValuesConstraint):
            yield from _validate_allowed_values(field.name, value, constraint)
        elif isinstance(constraint, AlphabetConstraint):
            yield from _validate_alphabet(field.name, value, constraint)
        elif isinstance(constraint, LengthConstraint):
            yield from _validate_length(field.name, value, constraint)
        elif isinstance(constraint, FiniteConstraint):
            yield from _validate_finite(field.name, value)


def _validate_range(
    field_name: str,
    value: Any,
    constraint: NumericRangeConstraint,
) -> Iterable[Violation]:
    for leaf in _scalar_leaves(value):
        if not isinstance(leaf, Real):
            yield Violation(
                code="non_numeric_value",
                field=field_name,
                message=f"range constraint requires numeric values, got {type(leaf).__name__}",
            )
            continue
        if constraint.minimum is not None:
            below = leaf < constraint.minimum
            equal_but_excluded = (
                not constraint.inclusive_minimum and leaf == constraint.minimum
            )
            if below or equal_but_excluded:
                operator = ">=" if constraint.inclusive_minimum else ">"
                yield Violation(
                    code="below_minimum",
                    field=field_name,
                    message=f"value {leaf!r} must be {operator} {constraint.minimum}",
                )
        if constraint.maximum is not None:
            above = leaf > constraint.maximum
            equal_but_excluded = (
                not constraint.inclusive_maximum and leaf == constraint.maximum
            )
            if above or equal_but_excluded:
                operator = "<=" if constraint.inclusive_maximum else "<"
                yield Violation(
                    code="above_maximum",
                    field=field_name,
                    message=f"value {leaf!r} must be {operator} {constraint.maximum}",
                )


def _validate_allowed_values(
    field_name: str,
    value: Any,
    constraint: AllowedValuesConstraint,
) -> Iterable[Violation]:
    for leaf in _scalar_leaves(value):
        if leaf not in constraint.values:
            yield Violation(
                code="value_not_allowed",
                field=field_name,
                message=f"value {leaf!r} is not in the allowed set",
            )


def _validate_alphabet(
    field_name: str,
    value: Any,
    constraint: AlphabetConstraint,
) -> Iterable[Violation]:
    if not isinstance(value, str):
        yield Violation(
            code="non_string_value",
            field=field_name,
            message="alphabet constraint requires a string value",
        )
        return
    invalid_symbols = sorted(set(value) - set(constraint.symbols))
    if invalid_symbols:
        yield Violation(
            code="invalid_alphabet_symbol",
            field=field_name,
            message=f"value contains symbols outside the alphabet: {invalid_symbols}",
        )


def _validate_length(
    field_name: str,
    value: Any,
    constraint: LengthConstraint,
) -> Iterable[Violation]:
    try:
        length = len(value)
    except TypeError:
        yield Violation(
            code="unsized_value",
            field=field_name,
            message="length constraint requires a sized value",
        )
        return
    if constraint.minimum is not None and length < constraint.minimum:
        yield Violation(
            code="below_minimum_length",
            field=field_name,
            message=f"length {length} must be >= {constraint.minimum}",
        )
    if constraint.maximum is not None and length > constraint.maximum:
        yield Violation(
            code="above_maximum_length",
            field=field_name,
            message=f"length {length} must be <= {constraint.maximum}",
        )


def _validate_finite(field_name: str, value: Any) -> Iterable[Violation]:
    for leaf in _scalar_leaves(value):
        if isinstance(leaf, Real) and not math.isfinite(leaf):
            yield Violation(
                code="non_finite_value",
                field=field_name,
                message=f"value {leaf!r} must be finite",
            )


def _scalar_leaves(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _scalar_leaves(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _scalar_leaves(item)
        return
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes, bytearray)):
        converted = value.tolist()
        if converted is not value:
            yield from _scalar_leaves(converted)
            return
    yield value
