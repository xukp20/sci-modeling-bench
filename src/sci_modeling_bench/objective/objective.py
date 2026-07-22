"""Minimal strongly typed Objective contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, TypeAlias

from sci_modeling_bench.cache import PreparationReport
from sci_modeling_bench.dataset.dataset import Dataset
from sci_modeling_bench.exceptions import (
    ObjectiveError,
    ObjectiveInputError,
    ObjectiveOutputError,
)

Candidate: TypeAlias = Mapping[str, Any]
ObjectiveOutput: TypeAlias = Mapping[str, Any]


class Objective(ABC):
    """A Dataset-bound, ordered batch mapping from candidates to outputs."""

    objective_id: str

    def __init__(self, dataset: Dataset) -> None:
        if not getattr(self, "objective_id", "").strip():
            raise ObjectiveError("objective_id must be a non-empty string")
        self._dataset = dataset

        output_fields = self.output_fields
        if not output_fields or len(set(output_fields)) != len(output_fields):
            raise ObjectiveOutputError(
                "output_fields must contain unique semantic field names"
            )

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @property
    @abstractmethod
    def output_fields(self) -> tuple[str, ...]:
        """Semantic fields returned for every candidate."""

    def evaluate(self, candidate: Candidate) -> dict[str, Any]:
        """Evaluate one candidate using the batch contract."""

        return self.evaluate_batch((candidate,))[0]

    def prepare(self) -> tuple[PreparationReport, ...]:
        """Prepare deterministic evaluator resources without scoring candidates."""

        return ()

    def evaluate_batch(
        self,
        candidates: Iterable[Candidate],
    ) -> tuple[dict[str, Any], ...]:
        """Validate and evaluate candidates while preserving order and repeats."""

        candidate_batch = tuple(candidates)
        for candidate_index, candidate in enumerate(candidate_batch):
            report = self.dataset.validate_inputs(
                self._candidate_for_dataset_validation(candidate)
            )
            if not report.valid:
                raise ObjectiveInputError(candidate_index, report)

        raw_outputs = tuple(self._evaluate_batch(candidate_batch))
        if len(raw_outputs) != len(candidate_batch):
            raise ObjectiveOutputError(
                f"Objective returned {len(raw_outputs)} outputs for "
                f"{len(candidate_batch)} candidates"
            )

        expected_fields = set(self.output_fields)
        outputs: list[dict[str, Any]] = []
        for output_index, output in enumerate(raw_outputs):
            if not isinstance(output, Mapping):
                raise ObjectiveOutputError(
                    f"output at batch index {output_index} is not a mapping"
                )
            actual_fields = set(output)
            if actual_fields != expected_fields:
                raise ObjectiveOutputError(
                    f"output at batch index {output_index} has fields "
                    f"{sorted(actual_fields)}, expected {sorted(expected_fields)}"
                )
            outputs.append({field: output[field] for field in self.output_fields})
        return tuple(outputs)

    def _candidate_for_dataset_validation(self, candidate: Candidate) -> Candidate:
        """Return the Dataset-schema view used to validate one candidate."""

        return candidate

    @abstractmethod
    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        """Implement evaluation for a validated, materialized batch."""
