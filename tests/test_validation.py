from __future__ import annotations

from datasets import Dataset as HFDataset
from datasets import Features

from sci_modeling_bench.dataset.schema import FieldSpec
from sci_modeling_bench.dataset.validation import (
    ValidationReport,
    Violation,
    validate_fields,
)


def test_common_constraints_report_machine_readable_codes() -> None:
    field = FieldSpec.model_validate(
        {
            "name": "x",
            "description": "Bounded vector.",
            "constraints": [
                {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                {"kind": "finite"},
                {"kind": "length", "minimum": 2, "maximum": 2},
            ],
        }
    )

    report = validate_fields({"x": [-0.5, float("inf")]}, (field,))

    assert not report.valid
    assert {item.code for item in report.violations} == {
        "below_minimum",
        "above_maximum",
        "non_finite_value",
    }


def test_validation_report_combines_and_attaches_row() -> None:
    first = ValidationReport(
        violations=(Violation(code="first", message="first"),)
    )
    warning = ValidationReport(
        violations=(
            Violation(code="warning", message="warning", severity="warning"),
        )
    )

    combined = ValidationReport.combine(first, warning).at_row(4)

    assert not combined.valid
    assert [item.row_index for item in combined.violations] == [4, 4]


def test_hugging_face_sequence_features_are_validated_without_crashing() -> None:
    features = HFDataset.from_dict({"x": [[1, 2]]}).features
    field = FieldSpec(name="x", description="Integer vector.")

    valid = validate_fields({"x": [1, 2]}, (field,), features=features)
    invalid = validate_fields({"x": "not-a-list"}, (field,), features=features)

    assert valid.valid
    assert not invalid.valid
    assert invalid.violations[0].code == "feature_mismatch"


def test_optional_null_skips_value_constraints() -> None:
    field = FieldSpec.model_validate(
        {
            "name": "x",
            "description": "Optional bounded measurement.",
            "required": False,
            "constraints": [
                {"kind": "range", "minimum": 0.0},
                {"kind": "finite"},
            ],
        }
    )

    report = validate_fields({"x": None}, (field,))

    assert report.valid


def test_arrow_schema_rejects_values_accepted_by_permissive_hf_encoding(
    monkeypatch,
) -> None:
    features = HFDataset.from_dict({"x": [[1, 2]]}).features
    field = FieldSpec(name="x", description="Integer vector.")

    def permissive_encode(self, example):
        return {"x": list(example["x"])}

    monkeypatch.setattr(Features, "encode_example", permissive_encode)

    report = validate_fields(
        {"x": "not-a-list"},
        (field,),
        features=features,
    )

    assert not report.valid
    assert report.violations[0].code == "feature_mismatch"
