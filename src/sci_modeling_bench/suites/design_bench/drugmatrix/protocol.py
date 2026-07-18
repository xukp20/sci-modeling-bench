"""Measured-pool Protocol for DrugMatrix clinical-pathology observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.drugmatrix._conditions import (
    MeasuredPool,
    build_measured_pool,
    candidate_view,
)
from sci_modeling_bench.suites.design_bench.drugmatrix.dataset import (
    DRUGMATRIX_DEFAULT_SPLIT,
)

_DATASET_ID = "design-bench/drugmatrix-clinical-pathology"


@dataclass(frozen=True)
class DrugMatrixAgentInput:
    """Visible individual-animal rows and label-hidden treatment conditions."""

    observations: HFDataset
    candidates: HFDataset


@dataclass(frozen=True)
class DrugMatrixMeasuredPoolProtocol(Protocol[DrugMatrixAgentInput]):
    """Hide measured five-day maximum-dose conditions behind a finite pool."""

    protocol_id: ClassVar[str] = "design-bench/drugmatrix-measured-pool-v1"
    _pools: dict[tuple[Dataset, str], MeasuredPool] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> DrugMatrixAgentInput:
        selected_split = split or DRUGMATRIX_DEFAULT_SPLIT
        observations = self._load_observations(dataset, selected_split)
        pool = self._pool(dataset, selected_split, observations)
        visible_indices = [
            index
            for index in range(len(observations))
            if index not in pool.treatment_row_indices
        ]
        return DrugMatrixAgentInput(
            observations=observations.select(visible_indices),
            candidates=candidate_view(pool),
        )

    def candidate_pool(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        """Return the internal labeled pool used to construct a Task."""

        selected_split = split or DRUGMATRIX_DEFAULT_SPLIT
        observations = self._load_observations(dataset, selected_split)
        return self._pool(dataset, selected_split, observations).table

    def _pool(
        self,
        dataset: Dataset,
        split: str,
        observations: HFDataset,
    ) -> MeasuredPool:
        key = (dataset, split)
        if key not in self._pools:
            self._pools[key] = build_measured_pool(observations)
        return self._pools[key]

    def _load_observations(self, dataset: Dataset, split: str) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"DrugMatrixMeasuredPoolProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        try:
            return dataset.load(split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
