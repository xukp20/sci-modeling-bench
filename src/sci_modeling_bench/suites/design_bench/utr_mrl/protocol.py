"""Biological compositional split for measured UTR MRL ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    Protocol,
    agent_input_manifest,
    agent_table_view,
)
from sci_modeling_bench.suites.design_bench.utr_mrl.dataset import (
    UTR_MRL_DEFAULT_SPLIT,
)

_DATASET_ID = "design-bench/utr-mrl-egfp-unmodified"


@dataclass(frozen=True)
class UTRMRLAgentInput:
    """Raw labeled observations and label-hidden measured UTR candidates."""

    observations: HFDataset
    candidates: HFDataset


@dataclass(frozen=True)
class UTRMRLCompositionalProtocol(Protocol[UTRMRLAgentInput]):
    """Withhold the joint uAUG-present and weak-Kozak combination."""

    protocol_id: ClassVar[str] = "design-bench/utr-mrl-compositional-v1"

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> AgentInputBundle[UTRMRLAgentInput]:
        measurements = self._load_measurements(dataset, split)
        visible, candidates = self.partition(measurements)
        data = UTRMRLAgentInput(
            observations=measurements.select(visible).select_columns(
                ["sequence", "mean_ribosome_load"]
            ),
            candidates=measurements.select(candidates).select_columns(["sequence"]),
        )
        selected_split = split or UTR_MRL_DEFAULT_SPLIT
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
                            "Measured 50-nucleotide UTR observations from the three "
                            "Agent-visible uAUG and Kozak combinations."
                        ),
                    ),
                    agent_table_view(
                        dataset,
                        data.candidates,
                        name="candidates",
                        role="candidates",
                        description=(
                            "Label-hidden measured 50-nucleotide UTR candidates from "
                            "the held-out biological combination."
                        ),
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
        """Return the trusted labeled pool used to construct the Task."""

        measurements = self._load_measurements(dataset, split)
        _, candidates = self.partition(measurements)
        return measurements.select(candidates).select_columns(
            ["sequence", "mean_ribosome_load"]
        )

    def partition(self, measurements: HFDataset) -> tuple[list[int], list[int]]:
        required = {"sequence", "has_uaug", "kozak_quality"}
        missing = sorted(required - set(measurements.column_names))
        if missing:
            raise ProtocolError(f"UTR MRL split is missing columns: {missing}")
        sequences = list(measurements["sequence"])
        uaug = list(measurements["has_uaug"])
        kozak = list(measurements["kozak_quality"])
        if not (len(sequences) == len(uaug) == len(kozak)):
            raise ProtocolError("UTR MRL partition columns are not aligned")

        visible: list[int] = []
        candidates: list[int] = []
        for index, (has_start, quality) in enumerate(
            zip(uaug, kozak, strict=True)
        ):
            if quality == "mixed":
                continue
            if bool(has_start) and quality == "weak":
                candidates.append(index)
            elif quality in {"strong", "weak"}:
                visible.append(index)
            else:
                raise ProtocolError(f"unknown kozak_quality value: {quality!r}")
        if not visible or not candidates:
            raise ProtocolError("compositional partition produced an empty side")
        visible.sort(key=sequences.__getitem__)
        candidates.sort(key=sequences.__getitem__)
        return visible, candidates

    def _load_measurements(
        self,
        dataset: Dataset,
        split: str | None,
    ) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"UTRMRLCompositionalProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or UTR_MRL_DEFAULT_SPLIT
        try:
            measurements = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        required = {
            "sequence",
            "mean_ribosome_load",
            "has_uaug",
            "kozak_quality",
        }
        missing = sorted(required - set(measurements.column_names))
        if missing:
            raise ProtocolError(f"UTR MRL split is missing columns: {missing}")
        return measurements
