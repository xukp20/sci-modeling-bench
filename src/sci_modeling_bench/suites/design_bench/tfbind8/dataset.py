"""TFBind8 Dataset defaults and scientific integrity checks."""

from __future__ import annotations

import math
import struct
from numbers import Real
from pathlib import Path
from typing import Any

from sci_modeling_bench.dataset.dataset import Dataset
from sci_modeling_bench.dataset.source import HubDatasetSource
from sci_modeling_bench.dataset.validation import (
    DatasetValidator,
    ValidationReport,
    Violation,
)

DEFAULT_TFBIND8_REPO_ID = "sci-modeling-bench/design-bench"
TFBIND8_CONFIG_NAME = "tfbind8"
TFBIND8_DEFAULT_SPLIT = "six6_ref_r1"
DEFAULT_TFBIND8_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_TFBIND8_REPO_ID,
    config_name=TFBIND8_CONFIG_NAME,
)

_ALPHABET = "ACGT"
_COMPLEMENT = str.maketrans("ACGT", "TGCA")
_EXPECTED_SEQUENCE_COUNT = 4**8
_EXPECTED_COLUMNS = ("sequence", "e_score", "normalized_e_score")


class TFBind8Dataset(Dataset):
    """Canonical TFBind8 observations with an overridable Hub source."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_TFBIND8_REPO_ID,
        config_name: str | None = TFBIND8_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> TFBind8Dataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or TFBind8Validator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_TFBIND8_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> TFBind8Dataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or TFBind8Validator(),
            cache=cache,
            cache_dir=cache_dir,
        )


class TFBind8Validator(DatasetValidator):
    """Checks invariants of a complete, canonical TFBind8 condition."""

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        column_names = tuple(getattr(data, "column_names", ()))
        if column_names and column_names != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="tfbind8_columns",
                    message=(
                        f"canonical TFBind8 columns must be {_EXPECTED_COLUMNS}, "
                        f"got {column_names}"
                    ),
                )
            )

        try:
            row_count = len(data)
            sequences = list(data["sequence"])
            e_scores = list(data["e_score"])
            normalized_scores = list(data["normalized_e_score"])
        except Exception as exc:
            violations.append(
                Violation(
                    code="tfbind8_unreadable_dataset",
                    message=f"failed to read canonical TFBind8 columns: {exc}",
                )
            )
            return ValidationReport(violations=tuple(violations))

        if row_count != _EXPECTED_SEQUENCE_COUNT:
            violations.append(
                Violation(
                    code="tfbind8_incomplete_space",
                    message=(
                        f"canonical TFBind8 must contain {_EXPECTED_SEQUENCE_COUNT} "
                        f"rows, got {row_count}"
                    ),
                )
            )

        if len(set(sequences)) != len(sequences):
            violations.append(
                Violation(
                    code="tfbind8_duplicate_sequence",
                    message="canonical TFBind8 sequences must be unique",
                )
            )

        if any(
            not isinstance(sequence, str)
            or len(sequence) != 8
            or set(sequence) - set(_ALPHABET)
            for sequence in sequences
        ):
            violations.append(
                Violation(
                    code="tfbind8_invalid_sequence",
                    field="sequence",
                    message="every sequence must be an eight-base uppercase DNA string",
                )
            )

        expected_order = (
            _sequence_from_index(index) for index in range(len(sequences))
        )
        if any(actual != expected for actual, expected in zip(sequences, expected_order)):
            violations.append(
                Violation(
                    code="tfbind8_noncanonical_order",
                    field="sequence",
                    message="sequences must use deterministic A<C<G<T lexicographic order",
                )
            )

        numeric_scores = all(
            isinstance(value, Real) and math.isfinite(value) for value in e_scores
        ) and all(
            isinstance(value, Real) and math.isfinite(value)
            for value in normalized_scores
        )
        if not numeric_scores:
            return ValidationReport(violations=tuple(violations))

        score_by_sequence = {
            sequence: (e_score, normalized_score)
            for sequence, e_score, normalized_score in zip(
                sequences, e_scores, normalized_scores
            )
        }
        if len(score_by_sequence) == len(sequences) and any(
            score_by_sequence.get(_reverse_complement(sequence)) != scores
            for sequence, scores in score_by_sequence.items()
        ):
            violations.append(
                Violation(
                    code="tfbind8_reverse_complement_mismatch",
                    message="reverse-complement pairs must retain identical PBM scores",
                )
            )

        if e_scores:
            minimum = min(e_scores)
            maximum = max(e_scores)
            if minimum == maximum:
                violations.append(
                    Violation(
                        code="tfbind8_constant_e_score",
                        field="e_score",
                        message="E-score range must be non-zero",
                    )
                )
            elif any(
                normalized != _float32((e_score - minimum) / (maximum - minimum))
                for e_score, normalized in zip(e_scores, normalized_scores)
            ):
                violations.append(
                    Violation(
                        code="tfbind8_normalization_mismatch",
                        field="normalized_e_score",
                        message=(
                            "normalized_e_score must equal the float32 min-max "
                            "normalization of e_score"
                        ),
                    )
                )

        return ValidationReport(violations=tuple(violations))


def _sequence_from_index(index: int) -> str:
    symbols = ["A"] * 8
    for position in range(7, -1, -1):
        index, digit = divmod(index, 4)
        symbols[position] = _ALPHABET[digit]
    return "".join(symbols)


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def _float32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]
