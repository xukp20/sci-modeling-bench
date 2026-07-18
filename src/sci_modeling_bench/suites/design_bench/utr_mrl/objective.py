"""Frozen measured-mean Objective for UTR MRL sequences."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.utr_mrl.dataset import (
    UTR_MRL_DEFAULT_SPLIT,
    UTRMRLDataset,
)

_DATASET_ID = "design-bench/utr-mrl-egfp-unmodified"


class UTRMRLMeasuredObjective(Objective):
    """Return the frozen replicate-mean MRL for a measured 50-mer."""

    objective_id = "design-bench/utr-mrl-measured-mean-v1"

    def __init__(
        self,
        dataset: UTRMRLDataset,
        *,
        split: str = UTR_MRL_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"UTRMRLMeasuredObjective requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._lookup: dict[str, float] | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("mean_ribosome_load",)

    @property
    def split(self) -> str:
        return self._split

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            sequence = str(candidate["sequence"])
            try:
                value = lookup[sequence]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"sequence {sequence!r} is absent from split {self.split!r}"
                ) from exc
            yield {"mean_ribosome_load": value}

    def _get_lookup(self) -> dict[str, float]:
        if self._lookup is not None:
            return self._lookup
        measurements = self.dataset.load(self.split)
        lookup = {
            str(sequence): float(value)
            for sequence, value in zip(
                measurements["sequence"],
                measurements["mean_ribosome_load"],
                strict=True,
            )
        }
        if len(lookup) != len(measurements):
            raise ObjectiveError("UTR MRL sequences must be unique")
        self._lookup = lookup
        return lookup
