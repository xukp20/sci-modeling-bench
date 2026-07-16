"""Lower-affinity observation Protocol for Pho4 BET-seq."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    SEQUENCE_COUNT,
    sequence_indices,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    TFBIND10_PHO4_DEFAULT_SPLIT,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.objective import (
    build_affinity_landscape,
)

_DATASET_ID = "design-bench/tfbind10-pho4"
_AGENT_OBSERVATION_COLUMNS = (
    "sequence",
    "replicate_id",
    "bound_count",
    "input_count",
    "bound_fraction",
    "input_fraction",
    "observed_ddg",
)


@dataclass(frozen=True)
class TFBind10Pho4AgentInput:
    """Raw visible replicates and a label-hidden candidate sequence pool."""

    observations: HFDataset
    candidates: HFDataset


@dataclass(frozen=True)
class TFBind10Pho4LowerHalfProtocol(Protocol[TFBind10Pho4AgentInput]):
    """Expose raw observations for the lower half of the measured landscape."""

    protocol_id: ClassVar[str] = "design-bench/tfbind10-pho4-lower-half-v1"

    visible_max_percentile: float = 50.0
    _score_tables: dict[Dataset, HFDataset] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_max_percentile < 100.0:
            raise ProtocolError("visible_max_percentile must be between 0 and 100")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> TFBind10Pho4AgentInput:
        observations = self._load_observations(dataset, split)
        scores = self._score_table(dataset, observations)
        visible_sequences, candidate_scores, _ = self.partition(scores)

        visible_by_sequence = np.zeros(SEQUENCE_COUNT, dtype=np.bool_)
        visible_by_sequence[sequence_indices(list(visible_sequences["sequence"]))] = (
            True
        )
        observation_indices = sequence_indices(list(observations["sequence"]))
        visible_rows = np.flatnonzero(visible_by_sequence[observation_indices]).tolist()
        agent_observations = observations.select(visible_rows).select_columns(
            list(_AGENT_OBSERVATION_COLUMNS)
        )
        candidates = candidate_scores.select_columns(["sequence"])
        return TFBind10Pho4AgentInput(
            observations=agent_observations,
            candidates=candidates,
        )

    def candidate_pool(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
        score_table: HFDataset | None = None,
    ) -> HFDataset:
        """Return the trusted, labeled upper-half pool used by the Task."""

        observations = self._load_observations(dataset, split)
        scores = (
            score_table
            if score_table is not None
            else self._score_table(dataset, observations)
        )
        self._validate_score_table(scores)
        self._score_tables[dataset] = scores
        _, candidates, _ = self.partition(scores)
        return candidates

    def partition(
        self,
        scores: HFDataset,
    ) -> tuple[HFDataset, HFDataset, float]:
        self._validate_score_table(scores)
        values = np.asarray(scores["affinity_score"], dtype=np.float64)
        cutoff = float(
            np.percentile(values, self.visible_max_percentile, method="linear")
        )
        visible_indices = np.flatnonzero(values <= cutoff).tolist()
        candidate_indices = np.flatnonzero(values > cutoff).tolist()
        if not visible_indices or not candidate_indices:
            raise ProtocolError("affinity percentile partition produced an empty side")
        return (
            scores.select(visible_indices),
            scores.select(candidate_indices),
            cutoff,
        )

    def _score_table(
        self,
        dataset: Dataset,
        observations: HFDataset,
    ) -> HFDataset:
        cached = self._score_tables.get(dataset)
        if cached is not None:
            return cached
        scores = build_affinity_landscape(observations).to_dataset()
        self._score_tables[dataset] = scores
        return scores

    def _load_observations(
        self,
        dataset: Dataset,
        split: str | None,
    ) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"TFBind10Pho4LowerHalfProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or TFBIND10_PHO4_DEFAULT_SPLIT
        try:
            observations = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        missing = sorted(
            set(_AGENT_OBSERVATION_COLUMNS) - set(observations.column_names)
        )
        if missing:
            raise ProtocolError(f"Pho4 observation split is missing columns: {missing}")
        return observations

    @staticmethod
    def _validate_score_table(scores: HFDataset) -> None:
        missing = sorted({"sequence", "affinity_score"} - set(scores.column_names))
        if missing:
            raise ProtocolError(f"Pho4 score table is missing columns: {missing}")
        values = np.asarray(scores["affinity_score"], dtype=np.float64)
        if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
            raise ProtocolError(
                "affinity_score must be a non-empty finite scalar column"
            )
