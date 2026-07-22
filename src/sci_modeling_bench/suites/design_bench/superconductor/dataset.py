"""Canonical UCI Superconductor composition-group Dataset."""

from __future__ import annotations

import hashlib
import math
from numbers import Real
from pathlib import Path
from typing import Any

import numpy as np

from sci_modeling_bench.dataset import (
    Dataset,
    DatasetValidator,
    HubDatasetSource,
    ValidationReport,
    Violation,
)

DEFAULT_SUPERCONDUCTOR_REPO_ID = "sci-modeling-bench/design-bench"
SUPERCONDUCTOR_CONFIG_NAME = "superconductor"
SUPERCONDUCTOR_DEFAULT_SPLIT = "composition_groups"
DEFAULT_SUPERCONDUCTOR_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_SUPERCONDUCTOR_REPO_ID,
    config_name=SUPERCONDUCTOR_CONFIG_NAME,
)

ELEMENT_SYMBOLS = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg",
    "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr",
    "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf",
    "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po",
    "At", "Rn",
)

DESCRIPTOR_NAMES = (
    "number_of_elements",
    "mean_atomic_mass", "wtd_mean_atomic_mass", "gmean_atomic_mass",
    "wtd_gmean_atomic_mass", "entropy_atomic_mass", "wtd_entropy_atomic_mass",
    "range_atomic_mass", "wtd_range_atomic_mass", "std_atomic_mass",
    "wtd_std_atomic_mass", "mean_fie", "wtd_mean_fie", "gmean_fie",
    "wtd_gmean_fie", "entropy_fie", "wtd_entropy_fie", "range_fie",
    "wtd_range_fie", "std_fie", "wtd_std_fie", "mean_atomic_radius",
    "wtd_mean_atomic_radius", "gmean_atomic_radius", "wtd_gmean_atomic_radius",
    "entropy_atomic_radius", "wtd_entropy_atomic_radius", "range_atomic_radius",
    "wtd_range_atomic_radius", "std_atomic_radius", "wtd_std_atomic_radius",
    "mean_Density", "wtd_mean_Density", "gmean_Density", "wtd_gmean_Density",
    "entropy_Density", "wtd_entropy_Density", "range_Density",
    "wtd_range_Density", "std_Density", "wtd_std_Density",
    "mean_ElectronAffinity", "wtd_mean_ElectronAffinity",
    "gmean_ElectronAffinity", "wtd_gmean_ElectronAffinity",
    "entropy_ElectronAffinity", "wtd_entropy_ElectronAffinity",
    "range_ElectronAffinity", "wtd_range_ElectronAffinity",
    "std_ElectronAffinity", "wtd_std_ElectronAffinity", "mean_FusionHeat",
    "wtd_mean_FusionHeat", "gmean_FusionHeat", "wtd_gmean_FusionHeat",
    "entropy_FusionHeat", "wtd_entropy_FusionHeat", "range_FusionHeat",
    "wtd_range_FusionHeat", "std_FusionHeat", "wtd_std_FusionHeat",
    "mean_ThermalConductivity", "wtd_mean_ThermalConductivity",
    "gmean_ThermalConductivity", "wtd_gmean_ThermalConductivity",
    "entropy_ThermalConductivity", "wtd_entropy_ThermalConductivity",
    "range_ThermalConductivity", "wtd_range_ThermalConductivity",
    "std_ThermalConductivity", "wtd_std_ThermalConductivity", "mean_Valence",
    "wtd_mean_Valence", "gmean_Valence", "wtd_gmean_Valence",
    "entropy_Valence", "wtd_entropy_Valence", "range_Valence",
    "wtd_range_Valence", "std_Valence", "wtd_std_Valence",
)

EXPECTED_SOURCE_ROWS = 21_263
EXPECTED_GROUPS = 15_164
COMPOSITION_DECIMALS = 8
_EXPECTED_COLUMNS = (
    "composition_id",
    "composition",
    "representative_formula",
    "source_record_ids",
    "material_formulas",
    "critical_temperatures_k",
    "critical_temp_k",
    "critical_temp_min_k",
    "critical_temp_max_k",
    "critical_temp_std_k",
    "observation_count",
    "descriptor_features_by_observation",
    "descriptor_features",
)


class SuperconductorDataset(Dataset):
    """Measured superconductors grouped by normalized elemental composition."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_SUPERCONDUCTOR_REPO_ID,
        config_name: str | None = SUPERCONDUCTOR_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> SuperconductorDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or SuperconductorValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_SUPERCONDUCTOR_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> SuperconductorDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or SuperconductorValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )


class SuperconductorValidator(DatasetValidator):
    """Check composition grouping and preservation of source measurements."""

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="superconductor_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        try:
            rows = list(data)
        except Exception as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="superconductor_unreadable_dataset",
                        message=f"failed to read composition groups: {exc}",
                    ),
                )
            )

        if len(rows) != EXPECTED_GROUPS:
            violations.append(
                Violation(
                    code="superconductor_group_count",
                    message=f"expected {EXPECTED_GROUPS} groups, got {len(rows)}",
                )
            )
        ids = [row.get("composition_id") for row in rows]
        if len(set(ids)) != len(ids):
            violations.append(
                Violation(
                    code="superconductor_duplicate_group_id",
                    field="composition_id",
                    message="composition group IDs must be unique",
                )
            )
        if ids != sorted(ids):
            violations.append(
                Violation(
                    code="superconductor_group_order",
                    field="composition_id",
                    message="composition groups must use deterministic ID order",
                )
            )

        all_source_ids: list[int] = []
        seen_compositions: set[tuple[float, ...]] = set()
        for row_index, row in enumerate(rows):
            composition = tuple(row.get("composition", ()))
            source_ids = tuple(row.get("source_record_ids", ()))
            formulas = tuple(row.get("material_formulas", ()))
            temperatures = tuple(row.get("critical_temperatures_k", ()))
            descriptors = tuple(row.get("descriptor_features", ()))
            descriptor_observations = tuple(
                tuple(values)
                for values in row.get("descriptor_features_by_observation", ())
            )
            if len(composition) != len(ELEMENT_SYMBOLS):
                violations.append(
                    Violation(
                        code="superconductor_composition_length",
                        field="composition",
                        row_index=row_index,
                        message=f"composition must have {len(ELEMENT_SYMBOLS)} values",
                    )
                )
                continue
            if composition in seen_compositions:
                violations.append(
                    Violation(
                        code="superconductor_duplicate_composition",
                        field="composition",
                        row_index=row_index,
                        message="normalized compositions must be unique",
                    )
                )
            seen_compositions.add(composition)
            if (
                any(
                    not isinstance(value, Real)
                    or not math.isfinite(value)
                    or value < 0
                    for value in composition
                )
                or not math.isclose(sum(composition), 1.0, abs_tol=1e-6)
            ):
                violations.append(
                    Violation(
                        code="superconductor_invalid_composition",
                        field="composition",
                        row_index=row_index,
                        message="composition must be finite, non-negative, and sum to one",
                    )
                )
            expected_id = composition_id(composition)
            if row.get("composition_id") != expected_id:
                violations.append(
                    Violation(
                        code="superconductor_group_id_mismatch",
                        field="composition_id",
                        row_index=row_index,
                        message=f"composition_id must equal {expected_id}",
                    )
                )
            if not (
                len(source_ids)
                == len(formulas)
                == len(temperatures)
                == len(descriptor_observations)
                == row.get("observation_count")
            ):
                violations.append(
                    Violation(
                        code="superconductor_observation_alignment",
                        row_index=row_index,
                        message="source IDs, formulas, temperatures, and count must align",
                    )
                )
                continue
            if len(descriptors) != len(DESCRIPTOR_NAMES) or any(
                not isinstance(value, Real) or not math.isfinite(value)
                for value in descriptors
            ):
                violations.append(
                    Violation(
                        code="superconductor_descriptor_shape",
                        field="descriptor_features",
                        row_index=row_index,
                        message=(
                            "descriptor_features must contain "
                            f"{len(DESCRIPTOR_NAMES)} finite values"
                        ),
                    )
                )
            if any(
                len(values) != len(DESCRIPTOR_NAMES)
                or any(
                    not isinstance(value, Real) or not math.isfinite(value)
                    for value in values
                )
                for values in descriptor_observations
            ):
                violations.append(
                    Violation(
                        code="superconductor_observation_descriptor_shape",
                        field="descriptor_features_by_observation",
                        row_index=row_index,
                        message=(
                            "every source observation must retain 81 finite "
                            "descriptor values"
                        ),
                    )
                )
            numeric_temperatures = np.asarray(temperatures, dtype=np.float64)
            if numeric_temperatures.size and not (
                math.isclose(
                    float(row["critical_temp_k"]),
                    float(np.median(numeric_temperatures)),
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(row["critical_temp_min_k"]),
                    float(np.min(numeric_temperatures)),
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(row["critical_temp_max_k"]),
                    float(np.max(numeric_temperatures)),
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(row["critical_temp_std_k"]),
                    float(np.std(numeric_temperatures)),
                    abs_tol=1e-12,
                )
            ):
                violations.append(
                    Violation(
                        code="superconductor_target_summary_mismatch",
                        field="critical_temp_k",
                        row_index=row_index,
                        message="group target summaries must match source measurements",
                    )
                )
            all_source_ids.extend(int(value) for value in source_ids)

        if sorted(all_source_ids) != list(range(EXPECTED_SOURCE_ROWS)):
            violations.append(
                Violation(
                    code="superconductor_source_coverage",
                    field="source_record_ids",
                    message="source record IDs must cover every UCI row exactly once",
                )
            )
        return ValidationReport(violations=tuple(violations))


def composition_id(composition: tuple[float, ...] | list[float]) -> str:
    """Return the stable ID for one rounded normalized composition."""

    payload = ",".join(f"{float(value):.{COMPOSITION_DECIMALS}f}" for value in composition)
    return "sc-" + hashlib.sha256(payload.encode("ascii")).hexdigest()[:24]
