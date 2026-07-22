"""Count-grounded posterior affinity Objective for Pho4 BET-seq."""

from __future__ import annotations

from collections.abc import Iterable
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.cache import PreparationReport, artifact_identity
from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    SEQUENCE_COUNT,
    all_sequences,
    dataset_numpy_column,
    dataset_sequence_indices,
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
_ARTIFACT_ID = "tfbind10-pho4-posterior-affinity"
_ARTIFACT_PRODUCER_VERSION = 1


@dataclass(frozen=True)
class Pho4AffinityLandscape:
    """One deterministic score for every observed DNA 10-mer."""

    scores: np.ndarray
    observed: np.ndarray
    row_sequence_indices: np.ndarray
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
        self._preparation_report: PreparationReport | None = None
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
            identity = artifact_identity(
                self.dataset,
                artifact_id=_ARTIFACT_ID,
                producer_version=_ARTIFACT_PRODUCER_VERSION,
                split=self.split,
                parameters={"pseudocount": self.pseudocount},
            )
            prepared = self.dataset.artifact_cache.get_or_build(
                identity,
                load=_load_affinity_landscape,
                build=lambda: build_affinity_landscape(
                    self.dataset.load(self.split)
                ),
                write=_write_affinity_landscape,
            )
            self._landscape = prepared.value
            self._preparation_report = prepared.report
        return self._landscape

    def prepare(self) -> tuple[PreparationReport, ...]:
        _ = self.landscape
        return () if self._preparation_report is None else (self._preparation_report,)

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
    sequence_ids = dataset_sequence_indices(observations)
    replicate_ids = dataset_numpy_column(observations, "replicate_id", np.int8)
    bound_counts = dataset_numpy_column(observations, "bound_count", np.int64)
    input_counts = dataset_numpy_column(observations, "input_count", np.int64)
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
    row_sequence_indices = sequence_ids.astype(np.int32, copy=True)
    score.setflags(write=False)
    observed.setflags(write=False)
    row_sequence_indices.setflags(write=False)
    return Pho4AffinityLandscape(
        scores=score,
        observed=observed,
        row_sequence_indices=row_sequence_indices,
        bound_depth=bound_depth,
        input_depth=input_depth,
    )


def _write_affinity_landscape(
    directory: Path, landscape: Pho4AffinityLandscape
) -> None:
    np.save(directory / "scores.npy", landscape.scores, allow_pickle=False)
    np.save(directory / "observed.npy", landscape.observed, allow_pickle=False)
    np.save(
        directory / "row_sequence_indices.npy",
        landscape.row_sequence_indices,
        allow_pickle=False,
    )
    (directory / "landscape.json").write_text(
        json.dumps(
            {
                "bound_depth": landscape.bound_depth,
                "input_depth": landscape.input_depth,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _load_affinity_landscape(directory: Path) -> Pho4AffinityLandscape:
    scores = np.load(directory / "scores.npy", allow_pickle=False, mmap_mode="r")
    observed = np.load(
        directory / "observed.npy", allow_pickle=False, mmap_mode="r"
    )
    row_indices = np.load(
        directory / "row_sequence_indices.npy",
        allow_pickle=False,
        mmap_mode="r",
    )
    metadata = json.loads((directory / "landscape.json").read_text(encoding="utf-8"))
    if scores.shape != (SEQUENCE_COUNT,) or scores.dtype != np.float64:
        raise ValueError("cached Pho4 scores have an invalid shape or dtype")
    if observed.shape != (SEQUENCE_COUNT,) or observed.dtype != np.bool_:
        raise ValueError("cached Pho4 observed mask has an invalid shape or dtype")
    if row_indices.ndim != 1 or row_indices.dtype != np.int32:
        raise ValueError("cached Pho4 row indices have an invalid shape or dtype")
    if not np.all(np.isfinite(scores[observed])):
        raise ValueError("cached Pho4 observed scores must be finite")
    return Pho4AffinityLandscape(
        scores=scores,
        observed=observed,
        row_sequence_indices=row_indices,
        bound_depth=int(metadata["bound_depth"]),
        input_depth=int(metadata["input_depth"]),
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
