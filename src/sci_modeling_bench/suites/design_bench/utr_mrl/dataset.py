"""Replicate-mean eGFP UTR MRL Dataset."""

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
from sci_modeling_bench.suites.design_bench.utr_mrl._sequence import (
    sequence_annotations,
)

DEFAULT_UTR_MRL_REPO_ID = "sci-modeling-bench/design-bench"
UTR_MRL_CONFIG_NAME = "utr_mrl_egfp_unmodified"
UTR_MRL_DEFAULT_SPLIT = "measurements"
DEFAULT_UTR_MRL_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_UTR_MRL_REPO_ID,
    config_name=UTR_MRL_CONFIG_NAME,
)

EXPECTED_UTR_MRL_ROWS = 318_468
_EXPECTED_COLUMNS = (
    "sequence",
    "mean_ribosome_load",
    "has_uaug",
    "has_out_of_frame_uaug",
    "kozak_quality",
)


class UTRMRLDataset(Dataset):
    """Measured 50-nt UTRs in one fixed eGFP/unmodified-RNA context."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_UTR_MRL_REPO_ID,
        config_name: str | None = UTR_MRL_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> UTRMRLDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or UTRMRLValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_UTR_MRL_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> UTRMRLDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or UTRMRLValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    def validate_dataset(self, data: Any | None = None) -> ValidationReport:
        """Run the vectorized canonical-table audit without per-row dispatch."""

        selected_data = data if data is not None else self.load()
        self._ensure_declared_features(selected_data)
        return self._validator.validate_dataset(selected_data)


class UTRMRLValidator(DatasetValidator):
    """Check canonical identity, targets, ordering, and derived annotations."""

    def __init__(self, *, expected_rows: int | None = EXPECTED_UTR_MRL_ROWS) -> None:
        self.expected_rows = expected_rows

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="utr_mrl_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        try:
            sequences = list(data["sequence"])
            targets = np.asarray(data["mean_ribosome_load"], dtype=np.float64)
            stored_uaug = np.asarray(data["has_uaug"], dtype=np.bool_)
            stored_oof = np.asarray(data["has_out_of_frame_uaug"], dtype=np.bool_)
            stored_kozak = list(data["kozak_quality"])
        except Exception as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="utr_mrl_unreadable_dataset",
                        message=f"failed to read canonical columns: {exc}",
                    ),
                )
            )

        if self.expected_rows is not None and len(sequences) != self.expected_rows:
            violations.append(
                Violation(
                    code="utr_mrl_row_count",
                    message=f"expected {self.expected_rows} rows, got {len(sequences)}",
                )
            )
        sequence_types_valid = all(isinstance(sequence, str) for sequence in sequences)
        if not sequence_types_valid:
            violations.append(
                Violation(
                    code="utr_mrl_sequence_type",
                    field="sequence",
                    message="canonical UTR sequences must be strings",
                )
            )
        elif len(set(sequences)) != len(sequences):
            violations.append(
                Violation(
                    code="utr_mrl_duplicate_sequence",
                    field="sequence",
                    message="canonical UTR sequences must be unique",
                )
            )
        if sequence_types_valid and sequences != sorted(sequences):
            violations.append(
                Violation(
                    code="utr_mrl_sequence_order",
                    field="sequence",
                    message="canonical rows must use lexicographic sequence order",
                )
            )
        if targets.shape != (len(sequences),) or not np.all(np.isfinite(targets)):
            violations.append(
                Violation(
                    code="utr_mrl_invalid_targets",
                    field="mean_ribosome_load",
                    message="MRL targets must be aligned finite scalars",
                )
            )
        elif np.any(targets < 0.0) or np.any(targets > 13.0):
            violations.append(
                Violation(
                    code="utr_mrl_target_range",
                    field="mean_ribosome_load",
                    message="MRL targets must be in the measured range [0, 13]",
                )
            )

        if not (
            len(stored_uaug)
            == len(stored_oof)
            == len(stored_kozak)
            == len(sequences)
        ):
            violations.append(
                Violation(
                    code="utr_mrl_annotation_alignment",
                    message="sequence and annotation columns must be row-aligned",
                )
            )
            return ValidationReport(violations=tuple(violations))

        expected: list[tuple[bool, bool, str]] = []
        for row_index, sequence in enumerate(sequences):
            try:
                expected.append(sequence_annotations(sequence))
            except (TypeError, ValueError) as exc:
                violations.append(
                    Violation(
                        code="utr_mrl_invalid_sequence",
                        field="sequence",
                        row_index=row_index,
                        message=str(exc),
                    )
                )
                expected.append((False, False, "mixed"))
        expected_uaug = np.asarray([row[0] for row in expected], dtype=np.bool_)
        expected_oof = np.asarray([row[1] for row in expected], dtype=np.bool_)
        expected_kozak = [row[2] for row in expected]
        _append_mismatch(
            violations,
            "has_uaug",
            stored_uaug,
            expected_uaug,
        )
        _append_mismatch(
            violations,
            "has_out_of_frame_uaug",
            stored_oof,
            expected_oof,
        )
        kozak_mismatch = next(
            (
                index
                for index, (stored, wanted) in enumerate(
                    zip(stored_kozak, expected_kozak, strict=True)
                )
                if stored != wanted
            ),
            None,
        )
        if kozak_mismatch is not None:
            violations.append(
                Violation(
                    code="utr_mrl_kozak_mismatch",
                    field="kozak_quality",
                    row_index=kozak_mismatch,
                    message="kozak_quality must be derived from the final three UTR bases",
                )
            )
        return ValidationReport(violations=tuple(violations))


def _append_mismatch(
    violations: list[Violation],
    field: str,
    actual: np.ndarray,
    expected: np.ndarray,
) -> None:
    mismatch = np.flatnonzero(actual != expected)
    if mismatch.size:
        violations.append(
            Violation(
                code=f"utr_mrl_{field}_mismatch",
                field=field,
                row_index=int(mismatch[0]),
                message=f"{field} must be deterministically derived from sequence",
            )
        )
