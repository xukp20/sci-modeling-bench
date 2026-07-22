"""Measured composition-group Objective for Superconductor."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    SUPERCONDUCTOR_DEFAULT_SPLIT,
    SuperconductorDataset,
)

_DATASET_ID = "design-bench/superconductor"


class SuperconductorMeasuredObjective(Objective):
    """Return the median measured Tc for a canonical composition group."""

    objective_id = "design-bench/superconductor-measured-group-median-v1"

    def __init__(
        self,
        dataset: SuperconductorDataset,
        *,
        split: str = SUPERCONDUCTOR_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"SuperconductorMeasuredObjective requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._lookup: dict[str, float] | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("critical_temp_k",)

    @property
    def split(self) -> str:
        return self._split

    def contains(self, composition_id: str) -> bool:
        return composition_id in self._get_lookup()

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            candidate_id = candidate["composition_id"]
            try:
                value = lookup[candidate_id]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"composition group {candidate_id!r} is absent from split "
                    f"{self.split!r}"
                ) from exc
            yield {"critical_temp_k": value}

    def _get_lookup(self) -> dict[str, float]:
        if self._lookup is not None:
            return self._lookup
        observations = self.dataset.load(self.split)
        lookup = {
            str(candidate_id): float(value)
            for candidate_id, value in zip(
                observations["composition_id"],
                observations["critical_temp_k"],
                strict=True,
            )
        }
        if len(lookup) != len(observations):
            raise ObjectiveError("Superconductor composition IDs must be unique")
        self._lookup = lookup
        return lookup

    def prepare(self) -> tuple[()]:
        _ = self._get_lookup()
        return ()
