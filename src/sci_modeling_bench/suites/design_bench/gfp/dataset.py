"""Canonical protein-level Sarkisyan GFP Dataset."""

from __future__ import annotations

import hashlib
import math
from numbers import Integral, Real
from typing import Any

import numpy as np

from sci_modeling_bench.dataset import (
    Dataset,
    DatasetValidator,
    HubDatasetSource,
    ValidationReport,
    Violation,
)
from sci_modeling_bench.suites.design_bench.gfp._sequence import (
    AMINO_ACID_SET,
    GFP_PROTEIN_LENGTH,
    apply_amino_acid_mutations,
    mutation_count,
)

DEFAULT_GFP_REPO_ID = "sci-modeling-bench/design-bench"
GFP_CONFIG_NAME = "gfp"
GFP_DEFAULT_SPLIT = "protein_genotypes"
DEFAULT_GFP_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_GFP_REPO_ID,
    config_name=GFP_CONFIG_NAME,
)

EXPECTED_GFP_PROTEINS = 51_715
EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS = 56_086
EXPECTED_GFP_BARCODE_OBSERVATIONS = 65_678
_EXPECTED_COLUMNS = (
    "protein_id",
    "sequence",
    "aa_mutations",
    "mutation_count",
    "unique_barcodes",
    "median_log10_brightness",
    "brightness_std",
    "nucleotide_mutations",
    "nucleotide_mutation_counts",
    "nucleotide_unique_barcodes",
    "nucleotide_median_log10_brightness",
    "nucleotide_brightness_std",
    "source_barcode_ids",
    "barcode_nucleotide_mutations",
    "barcode_nucleotide_mutation_counts",
    "barcode_log10_brightness",
    "barcode_min_coverage",
    "barcode_mean_coverage",
)


def protein_id(sequence: str) -> str:
    """Return the stable identity used to join GFP observation levels."""

    digest = hashlib.sha256(sequence.encode("ascii")).hexdigest()[:24]
    return f"gfp_{digest}"


class GFPDataset(Dataset):
    """Measured avGFP protein genotypes with retained source observations."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_GFP_REPO_ID,
        config_name: str | None = GFP_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> GFPDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or GFPValidator(),
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_GFP_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
    ) -> GFPDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or GFPValidator(),
        )

    def validate_dataset(self, data: Any | None = None) -> ValidationReport:
        """Run the canonical-table audit without generic per-row dispatch."""

        selected_data = data if data is not None else self.load()
        self._ensure_declared_features(selected_data)
        return self._validator.validate_dataset(selected_data)


class GFPValidator(DatasetValidator):
    """Check protein identity and aligned source-measurement preservation."""

    def __init__(self, *, expected_rows: int | None = EXPECTED_GFP_PROTEINS) -> None:
        self.expected_rows = expected_rows

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="gfp_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        try:
            rows = list(data)
        except Exception as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="gfp_unreadable_dataset",
                        message=f"failed to read canonical GFP rows: {exc}",
                    ),
                )
            )

        if self.expected_rows is not None and len(rows) != self.expected_rows:
            violations.append(
                Violation(
                    code="gfp_row_count",
                    message=f"expected {self.expected_rows} rows, got {len(rows)}",
                )
            )
        ids = [row.get("protein_id") for row in rows]
        sequences = [row.get("sequence") for row in rows]
        id_types_valid = all(isinstance(value, str) for value in ids)
        if not id_types_valid:
            violations.append(
                Violation(
                    code="gfp_protein_id_type",
                    field="protein_id",
                    message="protein IDs must be strings",
                )
            )
        elif len(set(ids)) != len(ids):
            violations.append(
                Violation(
                    code="gfp_duplicate_protein_id",
                    field="protein_id",
                    message="protein IDs must be unique",
                )
            )
        if id_types_valid and ids != sorted(ids):
            violations.append(
                Violation(
                    code="gfp_protein_order",
                    field="protein_id",
                    message="canonical rows must use protein_id order",
                )
            )
        if len(set(sequences)) != len(sequences):
            violations.append(
                Violation(
                    code="gfp_duplicate_sequence",
                    field="sequence",
                    message="canonical protein sequences must be unique",
                )
            )

        reference_rows = [
            row
            for row in rows
            if row.get("aa_mutations") == "" and row.get("mutation_count") == 0
        ]
        reference = reference_rows[0].get("sequence") if len(reference_rows) == 1 else None
        if not isinstance(reference, str):
            violations.append(
                Violation(
                    code="gfp_reference_row",
                    message="canonical data must contain exactly one wild-type row",
                )
            )

        seen_barcodes: set[str] = set()
        total_nucleotide_rows = 0
        for row_index, row in enumerate(rows):
            self._validate_row(
                row,
                row_index,
                reference,
                seen_barcodes,
                violations,
            )
            total_nucleotide_rows += len(row.get("nucleotide_mutations", ()))
        if self.expected_rows == EXPECTED_GFP_PROTEINS and (
            total_nucleotide_rows != EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS
        ):
            violations.append(
                Violation(
                    code="gfp_nucleotide_observation_count",
                    message=(
                        f"expected {EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS} clean "
                        f"nucleotide observations, got {total_nucleotide_rows}"
                    ),
                )
            )
        if self.expected_rows == EXPECTED_GFP_PROTEINS and (
            len(seen_barcodes) != EXPECTED_GFP_BARCODE_OBSERVATIONS
        ):
            violations.append(
                Violation(
                    code="gfp_barcode_observation_count",
                    message=(
                        f"expected {EXPECTED_GFP_BARCODE_OBSERVATIONS} clean "
                        f"barcode observations, got {len(seen_barcodes)}"
                    ),
                )
            )
        return ValidationReport(violations=tuple(violations))

    def _validate_row(
        self,
        row: dict[str, Any],
        row_index: int,
        reference: str | None,
        seen_barcodes: set[str],
        violations: list[Violation],
    ) -> None:
        sequence = row.get("sequence")
        if not _valid_sequence(sequence):
            violations.append(
                Violation(
                    code="gfp_invalid_sequence",
                    field="sequence",
                    row_index=row_index,
                    message=(
                        f"sequence must contain {GFP_PROTEIN_LENGTH} uppercase "
                        "standard amino acids"
                    ),
                )
            )
            return
        if row.get("protein_id") != protein_id(sequence):
            violations.append(
                Violation(
                    code="gfp_protein_id_mismatch",
                    field="protein_id",
                    row_index=row_index,
                    message="protein_id must be derived from the canonical sequence",
                )
            )

        notation = row.get("aa_mutations")
        try:
            expected_count = mutation_count(notation)
            expected_sequence = (
                apply_amino_acid_mutations(reference, notation)
                if reference is not None
                else sequence
            )
        except (TypeError, ValueError) as exc:
            violations.append(
                Violation(
                    code="gfp_invalid_mutation_notation",
                    field="aa_mutations",
                    row_index=row_index,
                    message=str(exc),
                )
            )
            expected_count = None
            expected_sequence = sequence
        if expected_count is not None and row.get("mutation_count") != expected_count:
            violations.append(
                Violation(
                    code="gfp_mutation_count_mismatch",
                    field="mutation_count",
                    row_index=row_index,
                    message="mutation_count must match aa_mutations",
                )
            )
        if expected_sequence != sequence:
            violations.append(
                Violation(
                    code="gfp_mutation_sequence_mismatch",
                    field="sequence",
                    row_index=row_index,
                    message="aa_mutations must reconstruct the stored sequence",
                )
            )

        count = row.get("unique_barcodes")
        target = row.get("median_log10_brightness")
        std = row.get("brightness_std")
        if not _nonnegative_integer(count) or count < 1:
            violations.append(
                Violation(
                    code="gfp_invalid_unique_barcodes",
                    field="unique_barcodes",
                    row_index=row_index,
                    message="unique_barcodes must be a positive integer",
                )
            )
        if not _finite(target):
            violations.append(
                Violation(
                    code="gfp_invalid_target",
                    field="median_log10_brightness",
                    row_index=row_index,
                    message="median_log10_brightness must be finite",
                )
            )
        if std is not None and (not _finite(std) or std < 0):
            violations.append(
                Violation(
                    code="gfp_invalid_brightness_std",
                    field="brightness_std",
                    row_index=row_index,
                    message="brightness_std must be null or finite and non-negative",
                )
            )

        nucleotide_fields = (
            "nucleotide_mutations",
            "nucleotide_mutation_counts",
            "nucleotide_unique_barcodes",
            "nucleotide_median_log10_brightness",
            "nucleotide_brightness_std",
        )
        nucleotide_values = [row.get(name) or () for name in nucleotide_fields]
        nucleotide_lengths = {len(values) for values in nucleotide_values}
        if len(nucleotide_lengths) != 1 or not nucleotide_lengths or 0 in nucleotide_lengths:
            violations.append(
                Violation(
                    code="gfp_nucleotide_alignment",
                    row_index=row_index,
                    message="nucleotide observation list columns must be non-empty and aligned",
                )
            )
        else:
            if len(set(nucleotide_values[0])) != len(nucleotide_values[0]):
                violations.append(
                    Violation(
                        code="gfp_duplicate_nucleotide_genotype",
                        field="nucleotide_mutations",
                        row_index=row_index,
                        message="nucleotide genotypes must be unique within a protein",
                    )
                )
            if _nonnegative_integer(count) and (
                sum(nucleotide_values[2]) != count
            ):
                violations.append(
                    Violation(
                        code="gfp_nucleotide_barcode_total_mismatch",
                        field="nucleotide_unique_barcodes",
                        row_index=row_index,
                        message=(
                            "nucleotide barcode totals must match the protein aggregate"
                        ),
                    )
                )
            nucleotide_rows = zip(*nucleotide_values, strict=True)
            for child_index, (
                child_notation,
                child_count,
                child_barcodes,
                value,
                child_std,
            ) in enumerate(nucleotide_rows):
                try:
                    wanted_count = mutation_count(child_notation)
                except (TypeError, ValueError):
                    wanted_count = None
                if wanted_count is None or child_count != wanted_count:
                    violations.append(
                        Violation(
                            code="gfp_nucleotide_mutation_count",
                            field="nucleotide_mutation_counts",
                            row_index=row_index,
                            message=f"invalid nucleotide mutation count at child {child_index}",
                        )
                    )
                    break
                if not _nonnegative_integer(child_barcodes) or child_barcodes < 1:
                    violations.append(
                        Violation(
                            code="gfp_nucleotide_barcode_count",
                            row_index=row_index,
                            message=f"invalid nucleotide barcode count at child {child_index}",
                        )
                    )
                    break
                if not _finite(value) or (
                    child_std is not None and (not _finite(child_std) or child_std < 0)
                ):
                    violations.append(
                        Violation(
                            code="gfp_nucleotide_measurement",
                            row_index=row_index,
                            message=f"invalid nucleotide measurement at child {child_index}",
                        )
                    )
                    break

        barcode_fields = (
            "source_barcode_ids",
            "barcode_nucleotide_mutations",
            "barcode_nucleotide_mutation_counts",
            "barcode_log10_brightness",
            "barcode_min_coverage",
            "barcode_mean_coverage",
        )
        barcode_values = [row.get(name) or () for name in barcode_fields]
        barcode_lengths = {len(values) for values in barcode_values}
        if len(barcode_lengths) != 1 or not barcode_lengths or 0 in barcode_lengths:
            violations.append(
                Violation(
                    code="gfp_barcode_alignment",
                    row_index=row_index,
                    message="barcode observation list columns must be non-empty and aligned",
                )
            )
            return
        if _nonnegative_integer(count) and len(barcode_values[0]) != count:
            violations.append(
                Violation(
                    code="gfp_barcode_count_mismatch",
                    field="unique_barcodes",
                    row_index=row_index,
                    message="retained barcode observations must match unique_barcodes",
                )
            )
        barcode_rows = zip(*barcode_values, strict=True)
        for child_index, (
            barcode,
            child_notation,
            child_count,
            value,
            min_coverage,
            mean_coverage,
        ) in enumerate(barcode_rows):
            if (
                not isinstance(barcode, str)
                or not barcode
                or set(barcode) - {"A", "C", "G", "T"}
            ):
                violations.append(
                    Violation(
                        code="gfp_invalid_barcode_id",
                        field="source_barcode_ids",
                        row_index=row_index,
                        message=f"invalid source barcode at child {child_index}",
                    )
                )
                break
            if barcode in seen_barcodes:
                violations.append(
                    Violation(
                        code="gfp_duplicate_barcode_id",
                        field="source_barcode_ids",
                        row_index=row_index,
                        message=f"source barcode {barcode!r} is repeated",
                    )
                )
                break
            seen_barcodes.add(barcode)
            try:
                wanted_count = mutation_count(child_notation)
            except (TypeError, ValueError):
                wanted_count = None
            if wanted_count is None or child_count != wanted_count:
                violations.append(
                    Violation(
                        code="gfp_barcode_mutation_count",
                        row_index=row_index,
                        message=f"invalid barcode mutation count at child {child_index}",
                    )
                )
                break
            if (
                not _finite(value)
                or not _nonnegative_integer(min_coverage)
                or not _finite(mean_coverage)
                or mean_coverage < 0
            ):
                violations.append(
                    Violation(
                        code="gfp_invalid_barcode_measurement",
                        row_index=row_index,
                        message=f"invalid barcode measurement at child {child_index}",
                    )
                )
                break


def _valid_sequence(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == GFP_PROTEIN_LENGTH
        and not (set(value) - AMINO_ACID_SET)
    )


def _finite(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and math.isfinite(value)
    )


def _nonnegative_integer(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Integral)
        and int(value) >= 0
    )
