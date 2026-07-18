"""Measured-pool Protocol for DrugMatrix clinical-pathology observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    AgentInputField,
    Protocol,
    agent_input_field,
    agent_input_manifest,
    agent_table_view,
)
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
    ) -> AgentInputBundle[DrugMatrixAgentInput]:
        selected_split = split or DRUGMATRIX_DEFAULT_SPLIT
        observations = self._load_observations(dataset, selected_split)
        pool = self._pool(dataset, selected_split, observations)
        visible_indices = [
            index
            for index in range(len(observations))
            if index not in pool.treatment_row_indices
        ]
        data = DrugMatrixAgentInput(
            observations=observations.select(visible_indices),
            candidates=candidate_view(pool),
        )
        return AgentInputBundle(
            data=data,
            manifest=agent_input_manifest(
                dataset,
                protocol_id=self.protocol_id,
                split=selected_split,
                views=(
                    agent_table_view(
                        dataset,
                        data.observations,
                        name="observations",
                        role="observations",
                        description=(
                            "Agent-visible individual-animal chemical and matched-control "
                            "clinical-pathology observations."
                        ),
                        overrides=_observation_view_fields(data.observations),
                    ),
                    agent_table_view(
                        dataset,
                        data.candidates,
                        name="candidates",
                        role="candidates",
                        description=(
                            "Label-hidden measured five-day maximum-dose treatment conditions."
                        ),
                        overrides=_candidate_view_fields(data.candidates),
                    ),
                ),
            ),
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


def _observation_view_fields(data: HFDataset) -> dict[str, AgentInputField]:
    descriptions = {
        "animal_id": "Unique source identifier for one individual-animal record.",
        "study_id": "Source toxicology study identifier.",
        "casrn": "Chemical Abstracts Service identifier; null for control animals.",
        "dose": "Source-administered chemical dose; null for control animals.",
        "duration_days": "Exposure duration recorded for this animal.",
        "vehicle": "Administration vehicle reported for this animal.",
        "treatment": "Chemical, vehicle-control, or untreated-control class.",
        "sex": "Animal sex when reported.",
        "route": "Administration route when reported.",
    }
    return {
        name: agent_input_field(
            data,
            name,
            role="context",
            description=description,
            unit="days" if name == "duration_days" else None,
            required=name not in {"casrn", "dose", "vehicle", "sex", "route"},
            source_field=name,
        )
        for name, description in descriptions.items()
    }


def _candidate_view_fields(data: HFDataset) -> dict[str, AgentInputField]:
    descriptions = {
        "condition_id": "Stable identity of the complete measured treatment condition.",
        "casrn": "Chemical Abstracts Service identifier for the treatment molecule.",
        "dose": "Source-administered dose for this measured treatment condition.",
        "duration_days": "Exposure duration for this measured treatment condition.",
        "vehicle": "Administration vehicle matched to the condition controls.",
        "sex": "Animal sex defining the measured treatment condition.",
        "route": "Administration route defining the measured treatment condition.",
        "study_id": "Source study defining the measured treatment condition.",
    }
    fields = {
        name: agent_input_field(
            data,
            name,
            role="input" if name == "condition_id" else "context",
            description=description,
            unit="days" if name == "duration_days" else None,
            required=True,
            source_field=name,
        )
        for name, description in descriptions.items()
    }
    return fields
