"""Raw-replicate Pho4 BET-seq Dataset derived from TFBind10."""

from __future__ import annotations

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
from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    SEQUENCE_COUNT,
    dataset_numpy_column,
    dataset_sequence_indices,
)

DEFAULT_TFBIND10_PHO4_REPO_ID = "sci-modeling-bench/design-bench"
TFBIND10_PHO4_CONFIG_NAME = "tfbind10_pho4"
TFBIND10_PHO4_DEFAULT_SPLIT = "observations"
DEFAULT_TFBIND10_PHO4_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_TFBIND10_PHO4_REPO_ID,
    config_name=TFBIND10_PHO4_CONFIG_NAME,
)

THERMAL_ENERGY_KCAL_PER_MOL = 0.593
EXPECTED_OBSERVATION_ROWS = 4_160_533
EXPECTED_ROWS_BY_REPLICATE = (1_027_148, 1_036_250, 1_048_561, 1_048_574)
EXPECTED_BOUND_DEPTHS = (6_203_398, 8_704_634, 54_959_850, 50_430_034)
EXPECTED_INPUT_DEPTHS = (7_190_687, 8_330_396, 24_275_485, 24_275_485)
EXPECTED_FINITE_DDG = (918_575, 956_323, 1_047_424, 1_047_423)
EXPECTED_POSITIVE_INFINITY_DDG = (62_683, 39_166, 18, 19)
EXPECTED_NEGATIVE_INFINITY_DDG = (45_890, 40_761, 1_119, 1_132)

_DATASET_ID = "design-bench/tfbind10-pho4"
_EXPECTED_COLUMNS = (
    "sequence",
    "replicate_id",
    "bound_count",
    "input_count",
    "bound_fraction",
    "input_fraction",
    "observed_ddg",
)


class TFBind10Pho4Dataset(Dataset):
    """Pho4 10-mer BET-seq observations with source replicates preserved."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_TFBIND10_PHO4_REPO_ID,
        config_name: str | None = TFBIND10_PHO4_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> TFBind10Pho4Dataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or TFBind10Pho4Validator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_TFBIND10_PHO4_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> TFBind10Pho4Dataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or TFBind10Pho4Validator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    def validate_dataset(self, data: Any | None = None) -> ValidationReport:
        """Run vectorized full-release checks without per-row Python iteration."""

        selected_data = data if data is not None else self.load()
        self._ensure_declared_features(selected_data)
        return self._validator.validate_dataset(selected_data)


class TFBind10Pho4Validator(DatasetValidator):
    """Check source-observation integrity and replicate count semantics."""

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="tfbind10_pho4_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        try:
            row_count = len(data)
            sequence_ids = dataset_sequence_indices(data)
            raw_replicate_ids = dataset_numpy_column(data, "replicate_id")
            raw_bound_counts = dataset_numpy_column(data, "bound_count")
            raw_input_counts = dataset_numpy_column(data, "input_count")
            bound_fractions = dataset_numpy_column(
                data, "bound_fraction", np.float64
            )
            input_fractions = dataset_numpy_column(
                data, "input_fraction", np.float64
            )
            observed_ddg = dataset_numpy_column(data, "observed_ddg", np.float64)
        except Exception as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="tfbind10_pho4_unreadable_dataset",
                        message=f"failed to read Pho4 observations: {exc}",
                    ),
                )
            )

        if not all(
            np.issubdtype(column.dtype, np.integer)
            for column in (raw_replicate_ids, raw_bound_counts, raw_input_counts)
        ):
            violations.append(
                Violation(
                    code="tfbind10_pho4_integer_storage",
                    message="replicate IDs and read counts must use integer storage",
                )
            )
            return ValidationReport(violations=tuple(violations))
        if np.any(raw_replicate_ids < 1) or np.any(raw_replicate_ids > 4):
            violations.append(
                Violation(
                    code="tfbind10_pho4_replicate_id",
                    field="replicate_id",
                    message="replicate_id must be one of 1, 2, 3, or 4",
                )
            )
            return ValidationReport(violations=tuple(violations))
        replicate_ids = raw_replicate_ids.astype(np.int8, copy=False)
        bound_counts = raw_bound_counts.astype(np.int64, copy=False)
        input_counts = raw_input_counts.astype(np.int64, copy=False)

        if row_count != EXPECTED_OBSERVATION_ROWS:
            violations.append(
                Violation(
                    code="tfbind10_pho4_row_count",
                    message=(
                        f"expected {EXPECTED_OBSERVATION_ROWS} source observations, "
                        f"got {row_count}"
                    ),
                )
            )
        if any(
            len(column) != row_count
            for column in (
                sequence_ids,
                replicate_ids,
                bound_counts,
                input_counts,
                bound_fractions,
                input_fractions,
                observed_ddg,
            )
        ):
            violations.append(
                Violation(
                    code="tfbind10_pho4_column_alignment",
                    message="all canonical columns must have the same row count",
                )
            )
            return ValidationReport(violations=tuple(violations))

        if np.any(bound_counts < 0) or np.any(input_counts < 0):
            violations.append(
                Violation(
                    code="tfbind10_pho4_negative_count",
                    message="bound_count and input_count must be non-negative",
                )
            )
        if (
            np.any(~np.isfinite(bound_fractions))
            or np.any(~np.isfinite(input_fractions))
            or np.any(bound_fractions < 0)
            or np.any(input_fractions < 0)
        ):
            violations.append(
                Violation(
                    code="tfbind10_pho4_invalid_fraction",
                    message="bound_fraction and input_fraction must be finite and non-negative",
                )
            )

        flat_ids = (replicate_ids.astype(np.int64) - 1) * SEQUENCE_COUNT + sequence_ids
        multiplicity = np.bincount(flat_ids, minlength=4 * SEQUENCE_COUNT)
        if np.any(multiplicity > 1):
            violations.append(
                Violation(
                    code="tfbind10_pho4_duplicate_observation",
                    message="each sequence and replicate pair may occur at most once",
                )
            )
        if np.unique(sequence_ids).size != SEQUENCE_COUNT:
            violations.append(
                Violation(
                    code="tfbind10_pho4_sequence_coverage",
                    field="sequence",
                    message=f"observations must cover all {SEQUENCE_COUNT} DNA 10-mers",
                )
            )

        rows_by_replicate = tuple(
            int(np.count_nonzero(replicate_ids == replicate))
            for replicate in range(1, 5)
        )
        bound_depths = tuple(
            int(bound_counts[replicate_ids == replicate].sum())
            for replicate in range(1, 5)
        )
        input_depths = tuple(
            int(input_counts[replicate_ids == replicate].sum())
            for replicate in range(1, 5)
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_replicate_rows",
            "replicate_id",
            rows_by_replicate,
            EXPECTED_ROWS_BY_REPLICATE,
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_bound_depths",
            "bound_count",
            bound_depths,
            EXPECTED_BOUND_DEPTHS,
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_input_depths",
            "input_count",
            input_depths,
            EXPECTED_INPUT_DEPTHS,
        )

        for replicate in range(1, 5):
            mask = replicate_ids == replicate
            if bound_depths[replicate - 1] and not np.allclose(
                bound_fractions[mask],
                bound_counts[mask] / bound_depths[replicate - 1],
                rtol=0.0,
                atol=1e-18,
            ):
                violations.append(
                    Violation(
                        code="tfbind10_pho4_bound_fraction_mismatch",
                        field="bound_fraction",
                        message=f"replicate {replicate} fractions do not match counts/depth",
                    )
                )
            if input_depths[replicate - 1] and not np.allclose(
                input_fractions[mask],
                input_counts[mask] / input_depths[replicate - 1],
                rtol=0.0,
                atol=1e-18,
            ):
                violations.append(
                    Violation(
                        code="tfbind10_pho4_input_fraction_mismatch",
                        field="input_fraction",
                        message=f"replicate {replicate} fractions do not match counts/depth",
                    )
                )

        with np.errstate(divide="ignore", invalid="ignore"):
            expected_ddg = -THERMAL_ENERGY_KCAL_PER_MOL * np.log(
                bound_fractions / input_fractions
            )
        if (
            np.any(np.isnan(observed_ddg))
            or np.any(np.isnan(expected_ddg))
            or not np.array_equal(np.isposinf(observed_ddg), np.isposinf(expected_ddg))
            or not np.array_equal(np.isneginf(observed_ddg), np.isneginf(expected_ddg))
        ):
            violations.append(
                Violation(
                    code="tfbind10_pho4_ddg_nonfinite_mismatch",
                    field="observed_ddg",
                    message="observed_ddg zero-count infinities do not match source fractions",
                )
            )
        finite = np.isfinite(expected_ddg)
        if not np.allclose(
            observed_ddg[finite], expected_ddg[finite], rtol=0.0, atol=1e-12
        ):
            violations.append(
                Violation(
                    code="tfbind10_pho4_ddg_mismatch",
                    field="observed_ddg",
                    message="finite observed_ddg values do not match -RT log(bound/input)",
                )
            )

        finite_counts = tuple(
            int(
                np.count_nonzero(
                    np.logical_and(
                        replicate_ids == replicate, np.isfinite(observed_ddg)
                    )
                )
            )
            for replicate in range(1, 5)
        )
        positive_infinity_counts = tuple(
            int(
                np.count_nonzero(
                    np.logical_and(
                        replicate_ids == replicate, np.isposinf(observed_ddg)
                    )
                )
            )
            for replicate in range(1, 5)
        )
        negative_infinity_counts = tuple(
            int(
                np.count_nonzero(
                    np.logical_and(
                        replicate_ids == replicate, np.isneginf(observed_ddg)
                    )
                )
            )
            for replicate in range(1, 5)
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_finite_ddg",
            "observed_ddg",
            finite_counts,
            EXPECTED_FINITE_DDG,
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_positive_infinity_ddg",
            "observed_ddg",
            positive_infinity_counts,
            EXPECTED_POSITIVE_INFINITY_DDG,
        )
        _expect_tuple(
            violations,
            "tfbind10_pho4_negative_infinity_ddg",
            "observed_ddg",
            negative_infinity_counts,
            EXPECTED_NEGATIVE_INFINITY_DDG,
        )

        input_by_replicate = np.zeros((4, SEQUENCE_COUNT), dtype=np.int32)
        input_by_replicate[replicate_ids - 1, sequence_ids] = input_counts
        if not np.array_equal(input_by_replicate[2], input_by_replicate[3]):
            violations.append(
                Violation(
                    code="tfbind10_pho4_shared_input_library",
                    field="input_count",
                    message="replicates 3 and 4 must preserve their shared input library",
                )
            )
        return ValidationReport(violations=tuple(violations))


def _expect_tuple(
    violations: list[Violation],
    code: str,
    field: str,
    actual: tuple[int, ...],
    expected: tuple[int, ...],
) -> None:
    if actual != expected:
        violations.append(
            Violation(
                code=code,
                field=field,
                message=f"expected {expected} by replicate, got {actual}",
            )
        )
