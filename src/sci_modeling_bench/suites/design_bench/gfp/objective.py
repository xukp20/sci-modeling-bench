"""Frozen protein-level measured Objective for Sarkisyan GFP."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.gfp.dataset import (
    GFP_DEFAULT_SPLIT,
    GFPDataset,
)

_DATASET_ID = "design-bench/gfp"


class GFPMeasuredObjective(Objective):
    """Return the frozen author-aggregated brightness for a measured protein."""

    objective_id = "design-bench/gfp-measured-protein-median-v1"

    def __init__(
        self,
        dataset: GFPDataset,
        *,
        split: str = GFP_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"GFPMeasuredObjective requires dataset_id {_DATASET_ID!r}, "
                f"got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._lookup: dict[str, float] | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("median_log10_brightness",)

    @property
    def split(self) -> str:
        return self._split

    def contains(self, sequence: str) -> bool:
        return sequence in self._get_lookup()

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            sequence = candidate["sequence"]
            try:
                value = lookup[sequence]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"protein sequence is absent from split {self.split!r}"
                ) from exc
            yield {"median_log10_brightness": value}

    def _get_lookup(self) -> dict[str, float]:
        if self._lookup is not None:
            return self._lookup
        observations = self.dataset.load(self.split)
        lookup = {
            str(sequence): float(value)
            for sequence, value in zip(
                observations["sequence"],
                observations["median_log10_brightness"],
                strict=True,
            )
        }
        if len(lookup) != len(observations):
            raise ObjectiveError("GFP protein sequences must be unique")
        self._lookup = lookup
        return lookup
