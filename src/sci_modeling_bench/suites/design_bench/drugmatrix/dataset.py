"""Canonical individual-animal DrugMatrix clinical-pathology Dataset."""

from __future__ import annotations

import math
from collections import Counter
from numbers import Real
from typing import Any

from sci_modeling_bench.dataset import (
    Dataset,
    DatasetValidator,
    HubDatasetSource,
    ValidationReport,
    Violation,
)
from sci_modeling_bench.suites.design_bench.drugmatrix._conditions import ENDPOINTS

DEFAULT_DRUGMATRIX_REPO_ID = "sci-modeling-bench/design-bench"
DEFAULT_DRUGMATRIX_REVISION = "013a4d698f61db49a6c26f986e5f3bab143aa4fe"
DRUGMATRIX_CONFIG_NAME = "drugmatrix_clinical_pathology"
DRUGMATRIX_DEFAULT_SPLIT = "observations"
DEFAULT_DRUGMATRIX_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_DRUGMATRIX_REPO_ID,
    config_name=DRUGMATRIX_CONFIG_NAME,
    revision=DEFAULT_DRUGMATRIX_REVISION,
)
DRUGMATRIX_ENDPOINTS = ENDPOINTS

EXPECTED_ROWS = 10_605
EXPECTED_TREATMENTS = {
    "Chemical": 8_940,
    "Vehicle Control": 1_650,
    "Untreated Control": 15,
}
EXPECTED_STUDIES = 101
EXPECTED_CHEMICAL_CASRN = 653
EXPECTED_MAPPED_CHEMICAL_ROWS = 8_779
EXPECTED_NONNULL_ENDPOINTS = {
    "mchc": 10_552,
    "mch": 10_552,
    "creatinine": 10_582,
    "sodium": 10_420,
    "chloride": 10_420,
    "phosphorus": 10_595,
}
EXPECTED_ENDPOINT_RANGES = {
    "mchc": (16.6, 51.2),
    "mch": (9.7, 38.5),
    "creatinine": (0.1, 6.56),
    "sodium": (47.9, 1_555.0),
    "chloride": (43.0, 137.0),
    "phosphorus": (3.7, 37.9),
}
_EXPECTED_COLUMNS = (
    "animal_id",
    "study_id",
    "casrn",
    "canonical_smiles",
    "dose",
    "duration_days",
    "vehicle",
    "treatment",
    "sex",
    "route",
    *ENDPOINTS,
)


class DrugMatrixDataset(Dataset):
    """Official DrugMatrix individual-animal observations with an overridable source."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_DRUGMATRIX_REPO_ID,
        config_name: str | None = DRUGMATRIX_CONFIG_NAME,
        revision: str | None = DEFAULT_DRUGMATRIX_REVISION,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> DrugMatrixDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or DrugMatrixValidator(),
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_DRUGMATRIX_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> DrugMatrixDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or DrugMatrixValidator(),
        )


class DrugMatrixValidator(DatasetValidator):
    """Check frozen source preservation and clinical-pathology invariants."""

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="drugmatrix_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        try:
            rows = list(data)
        except Exception as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="drugmatrix_unreadable_dataset",
                        message=f"failed to read DrugMatrix observations: {exc}",
                    ),
                )
            )
        if len(rows) != EXPECTED_ROWS:
            violations.append(
                Violation(
                    code="drugmatrix_row_count",
                    message=f"expected {EXPECTED_ROWS} observations, got {len(rows)}",
                )
            )

        animal_ids = [row.get("animal_id") for row in rows]
        if any(not isinstance(value, str) or not value for value in animal_ids):
            violations.append(
                Violation(
                    code="drugmatrix_animal_id",
                    field="animal_id",
                    message="every animal_id must be a non-empty string",
                )
            )
        if len(set(animal_ids)) != len(animal_ids):
            violations.append(
                Violation(
                    code="drugmatrix_duplicate_animal_id",
                    field="animal_id",
                    message="animal_id values must be unique",
                )
            )

        treatment_counts = Counter(row.get("treatment") for row in rows)
        if dict(treatment_counts) != EXPECTED_TREATMENTS:
            violations.append(
                Violation(
                    code="drugmatrix_treatment_counts",
                    field="treatment",
                    message=(
                        f"expected treatment counts {EXPECTED_TREATMENTS}, "
                        f"got {dict(treatment_counts)}"
                    ),
                )
            )

        study_ids = {row.get("study_id") for row in rows}
        if None in study_ids or len(study_ids) != EXPECTED_STUDIES:
            violations.append(
                Violation(
                    code="drugmatrix_study_ids",
                    field="study_id",
                    message=(
                        f"expected {EXPECTED_STUDIES} non-null study IDs, "
                        f"got {len(study_ids - {None})}"
                    ),
                )
            )
        chemical_rows = [
            row for row in rows if row.get("treatment") == "Chemical"
        ]
        chemical_casrn = {row.get("casrn") for row in chemical_rows}
        if None in chemical_casrn or len(chemical_casrn) != EXPECTED_CHEMICAL_CASRN:
            violations.append(
                Violation(
                    code="drugmatrix_chemical_casrn",
                    field="casrn",
                    message=(
                        f"expected {EXPECTED_CHEMICAL_CASRN} non-null chemical CASRN "
                        f"values, got {len(chemical_casrn - {None})}"
                    ),
                )
            )
        mapped_rows = sum(
            row.get("canonical_smiles") is not None for row in chemical_rows
        )
        if mapped_rows != EXPECTED_MAPPED_CHEMICAL_ROWS:
            violations.append(
                Violation(
                    code="drugmatrix_mapped_chemical_rows",
                    field="canonical_smiles",
                    message=(
                        f"expected {EXPECTED_MAPPED_CHEMICAL_ROWS} mapped chemical "
                        f"rows, got {mapped_rows}"
                    ),
                )
            )

        for index, row in enumerate(rows):
            duration = row.get("duration_days")
            dose = row.get("dose")
            if not _finite_nonnegative(duration):
                violations.append(
                    Violation(
                        code="drugmatrix_duration",
                        field="duration_days",
                        row_index=index,
                        message="duration_days must be finite and non-negative",
                    )
                )
            if dose is not None and not _finite_nonnegative(dose):
                violations.append(
                    Violation(
                        code="drugmatrix_dose",
                        field="dose",
                        row_index=index,
                        message="non-null dose must be finite and non-negative",
                    )
                )
            treatment = row.get("treatment")
            if treatment == "Chemical" and dose is None:
                violations.append(
                    Violation(
                        code="drugmatrix_chemical_dose",
                        field="dose",
                        row_index=index,
                        message="chemical observations require a source dose",
                    )
                )
            if treatment != "Chemical" and (
                row.get("casrn") is not None or dose is not None
            ):
                violations.append(
                    Violation(
                        code="drugmatrix_control_identity",
                        row_index=index,
                        message="control observations cannot have CASRN or dose values",
                    )
                )
            smiles = row.get("canonical_smiles")
            if smiles is not None and (
                not isinstance(smiles, str) or not smiles or smiles != smiles.strip()
            ):
                violations.append(
                    Violation(
                        code="drugmatrix_smiles",
                        field="canonical_smiles",
                        row_index=index,
                        message="canonical_smiles must be null or a trimmed non-empty string",
                    )
                )
            if row.get("treatment") != "Chemical" and smiles is not None:
                violations.append(
                    Violation(
                        code="drugmatrix_control_smiles",
                        field="canonical_smiles",
                        row_index=index,
                        message="control observations cannot be assigned a molecule SMILES",
                    )
                )

        for endpoint in ENDPOINTS:
            values = [row.get(endpoint) for row in rows if row.get(endpoint) is not None]
            if len(values) != EXPECTED_NONNULL_ENDPOINTS[endpoint]:
                violations.append(
                    Violation(
                        code="drugmatrix_endpoint_count",
                        field=endpoint,
                        message=(
                            f"expected {EXPECTED_NONNULL_ENDPOINTS[endpoint]} non-null "
                            f"values, got {len(values)}"
                        ),
                    )
                )
                continue
            if any(not _finite(value) for value in values):
                violations.append(
                    Violation(
                        code="drugmatrix_endpoint_finite",
                        field=endpoint,
                        message="non-null endpoint values must be finite",
                    )
                )
                continue
            actual_range = (min(values), max(values))
            if actual_range != EXPECTED_ENDPOINT_RANGES[endpoint]:
                violations.append(
                    Violation(
                        code="drugmatrix_endpoint_range",
                        field=endpoint,
                        message=(
                            f"expected range {EXPECTED_ENDPOINT_RANGES[endpoint]}, "
                            f"got {actual_range}"
                        ),
                    )
                )
        return ValidationReport(violations=tuple(violations))


def _finite(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and math.isfinite(float(value))
    )


def _finite_nonnegative(value: Any) -> bool:
    return _finite(value) and float(value) >= 0.0
