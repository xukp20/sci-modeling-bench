"""Exact lookup Objective for canonical TFBind8 observations."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.tfbind8.dataset import (
    TFBIND8_DEFAULT_SPLIT,
    TFBind8Dataset,
)

_TFBIND8_DATASET_ID = "design-bench/tfbind8"
_OUTPUT_FIELDS = ("e_score", "normalized_e_score")


class TFBind8ExactObjective(Objective):
    """Return both published scores for every legal TFBind8 sequence."""

    objective_id = "design-bench/tfbind8-exact-v1"

    def __init__(
        self,
        dataset: TFBind8Dataset,
        *,
        split: str = TFBIND8_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _TFBIND8_DATASET_ID:
            raise ObjectiveError(
                f"TFBind8ExactObjective requires dataset_id "
                f"{_TFBIND8_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        try:
            dataset.split(split)
        except ValueError as exc:
            raise ObjectiveError(str(exc)) from exc

        self._split = split
        self._lookup: dict[str, tuple[float, float]] | None = None
        super().__init__(dataset)

    @property
    def split(self) -> str:
        return self._split

    @property
    def output_fields(self) -> tuple[str, ...]:
        return _OUTPUT_FIELDS

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            sequence = candidate["sequence"]
            try:
                e_score, normalized_e_score = lookup[sequence]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"valid TFBind8 sequence {sequence!r} is absent from exact "
                    f"split {self.split!r}"
                ) from exc
            yield {
                "e_score": e_score,
                "normalized_e_score": normalized_e_score,
            }

    def _get_lookup(self) -> dict[str, tuple[float, float]]:
        if self._lookup is not None:
            return self._lookup

        observations = self.dataset.load(self.split)
        required = {"sequence", *_OUTPUT_FIELDS}
        missing = sorted(required - set(observations.column_names))
        if missing:
            raise ObjectiveError(
                f"exact TFBind8 split {self.split!r} is missing columns: {missing}"
            )

        lookup: dict[str, tuple[float, float]] = {}
        for sequence, e_score, normalized_e_score in zip(
            observations["sequence"],
            observations["e_score"],
            observations["normalized_e_score"],
        ):
            scores = (float(e_score), float(normalized_e_score))
            if sequence in lookup:
                raise ObjectiveError(
                    f"exact TFBind8 split {self.split!r} contains duplicate "
                    f"sequence {sequence!r}"
                )
            lookup[sequence] = scores

        if len(lookup) != len(observations):
            raise ObjectiveError(
                f"failed to build a one-to-one exact lookup for split {self.split!r}"
            )
        self._lookup = lookup
        return lookup

    def prepare(self) -> tuple[()]:
        _ = self._get_lookup()
        return ()
