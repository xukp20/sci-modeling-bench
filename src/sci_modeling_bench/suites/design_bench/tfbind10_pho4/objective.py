"""Count-grounded posterior affinity Objective for Pho4 BET-seq."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    SEQUENCE_COUNT,
    all_sequences,
    sequence_indices,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    TFBIND10_PHO4_DEFAULT_SPLIT,
    THERMAL_ENERGY_KCAL_PER_MOL,
    TFBind10Pho4Dataset,
)

_DATASET_ID = "design-bench/tfbind10-pho4"
_REQUIRED_COLUMNS = {
    "sequence",
    "replicate_id",
    "bound_count",
    "input_count",
}


@dataclass(frozen=True)
class Pho4AffinityLandscape:
    """One deterministic score for every observed DNA 10-mer."""

    scores: np.ndarray
    observed: np.ndarray
    bound_depth: int
    input_depth: int

    def to_dataset(self) -> HFDataset:
        indices = np.flatnonzero(self.observed)
        sequences = all_sequences()
        return HFDataset.from_dict(
            {
                "sequence": [sequences[index] for index in indices],
                "affinity_score": self.scores[indices].tolist(),
            },
            features=Features(
                {
                    "sequence": Value("string"),
                    "affinity_score": Value("float64"),
                }
            ),
        )


class TFBind10Pho4PosteriorObjective(Objective):
    """Pool read counts and return posterior expected log enrichment."""

    objective_id = "design-bench/tfbind10-pho4-posterior-affinity-v1"
    pseudocount = 1.0

    def __init__(
        self,
        dataset: TFBind10Pho4Dataset,
        *,
        split: str = TFBIND10_PHO4_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"TFBind10Pho4PosteriorObjective requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._landscape: Pho4AffinityLandscape | None = None
        self._score_table: HFDataset | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("affinity_score",)

    @property
    def split(self) -> str:
        return self._split

    def contains(self, sequence: str) -> bool:
        try:
            index = int(sequence_indices([sequence])[0])
        except ValueError:
            return False
        return bool(self.landscape.observed[index])

    @property
    def landscape(self) -> Pho4AffinityLandscape:
        if self._landscape is None:
            self._landscape = build_affinity_landscape(self.dataset.load(self.split))
        return self._landscape

    def score_table(self) -> HFDataset:
        """Return the trusted complete score table in canonical sequence order."""

        if self._score_table is None:
            self._score_table = self.landscape.to_dataset()
        return self._score_table

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        indices = sequence_indices(
            [str(candidate["sequence"]) for candidate in candidates]
        )
        landscape = self.landscape
        for sequence, index in zip(candidates, indices, strict=True):
            if not landscape.observed[index]:
                raise ObjectiveLookupError(
                    f"sequence {sequence['sequence']!r} is absent from split "
                    f"{self.split!r}"
                )
            yield {"affinity_score": float(landscape.scores[index])}


def build_affinity_landscape(observations: HFDataset) -> Pho4AffinityLandscape:
    """Aggregate raw replicates into a smoothed, maximize-oriented landscape."""

    missing = sorted(_REQUIRED_COLUMNS - set(observations.column_names))
    if missing:
        raise ObjectiveError(f"Pho4 observation split is missing columns: {missing}")
    sequences = list(observations["sequence"])
    sequence_ids = sequence_indices(sequences)
    replicate_ids = np.asarray(observations["replicate_id"], dtype=np.int8)
    bound_counts = np.asarray(observations["bound_count"], dtype=np.int64)
    input_counts = np.asarray(observations["input_count"], dtype=np.int64)
    if not (
        len(sequence_ids)
        == len(replicate_ids)
        == len(bound_counts)
        == len(input_counts)
    ):
        raise ObjectiveError("Pho4 observation columns are not aligned")
    if np.any(replicate_ids < 1) or np.any(replicate_ids > 4):
        raise ObjectiveError("Pho4 replicate_id must be one of 1, 2, 3, or 4")
    if np.any(bound_counts < 0) or np.any(input_counts < 0):
        raise ObjectiveError("Pho4 read counts must be non-negative")

    flat_ids = (replicate_ids.astype(np.int64) - 1) * SEQUENCE_COUNT + sequence_ids
    if np.any(np.bincount(flat_ids, minlength=4 * SEQUENCE_COUNT) > 1):
        raise ObjectiveError("Pho4 sequence/replicate observations must be unique")

    bound_by_replicate = np.zeros((4, SEQUENCE_COUNT), dtype=np.int64)
    input_by_replicate = np.zeros((4, SEQUENCE_COUNT), dtype=np.int64)
    bound_by_replicate[replicate_ids - 1, sequence_ids] = bound_counts
    input_by_replicate[replicate_ids - 1, sequence_ids] = input_counts
    if not np.array_equal(input_by_replicate[2], input_by_replicate[3]):
        raise ObjectiveError(
            "Pho4 replicates 3 and 4 must share the same input library"
        )

    pooled_bound = bound_by_replicate.sum(axis=0)
    pooled_input = input_by_replicate[:3].sum(axis=0)
    bound_depth = int(pooled_bound.sum())
    input_depth = int(pooled_input.sum())
    if bound_depth <= 0 or input_depth <= 0:
        raise ObjectiveError("Pho4 pooled libraries must have positive depth")

    alpha = TFBind10Pho4PosteriorObjective.pseudocount
    score = THERMAL_ENERGY_KCAL_PER_MOL * (
        _digamma_positive(pooled_bound.astype(np.float64) + alpha)
        - _digamma_scalar(bound_depth + SEQUENCE_COUNT * alpha)
        - _digamma_positive(pooled_input.astype(np.float64) + alpha)
        + _digamma_scalar(input_depth + SEQUENCE_COUNT * alpha)
    )
    observed = np.zeros(SEQUENCE_COUNT, dtype=np.bool_)
    observed[sequence_ids] = True
    score.setflags(write=False)
    observed.setflags(write=False)
    return Pho4AffinityLandscape(
        scores=score,
        observed=observed,
        bound_depth=bound_depth,
        input_depth=input_depth,
    )


def _digamma_positive(values: np.ndarray) -> np.ndarray:
    """Evaluate digamma for positive values using recurrence and asymptotics."""

    x = np.asarray(values, dtype=np.float64).copy()
    if np.any(x <= 0) or np.any(~np.isfinite(x)):
        raise ValueError("digamma inputs must be finite and positive")
    result = np.zeros_like(x)
    while True:
        mask = x < 8.0
        if not np.any(mask):
            break
        result[mask] -= 1.0 / x[mask]
        x[mask] += 1.0
    inverse = 1.0 / x
    inverse_squared = inverse * inverse
    return (
        result
        + np.log(x)
        - 0.5 * inverse
        - inverse_squared
        * (
            1.0 / 12.0
            - inverse_squared
            * (
                1.0 / 120.0
                - inverse_squared
                * (
                    1.0 / 252.0
                    - inverse_squared * (1.0 / 240.0 - inverse_squared / 132.0)
                )
            )
        )
    )


def _digamma_scalar(value: float) -> float:
    return float(_digamma_positive(np.asarray([value], dtype=np.float64))[0])
