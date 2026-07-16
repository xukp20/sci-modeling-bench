"""Measured-pool Protocol for UCI Superconductor composition groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    DESCRIPTOR_NAMES,
    ELEMENT_SYMBOLS,
    SUPERCONDUCTOR_DEFAULT_SPLIT,
)

_DATASET_ID = "design-bench/superconductor"


@dataclass(frozen=True)
class SuperconductorAgentInput:
    """Offline observations and label-hidden candidates exposed to an Agent."""

    observations: HFDataset
    candidates: HFDataset
    element_symbols: tuple[str, ...] = ELEMENT_SYMBOLS
    descriptor_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class SuperconductorMeasuredPoolProtocol(Protocol[SuperconductorAgentInput]):
    """Expose lower-temperature observations and an upper-tail candidate pool."""

    protocol_id: ClassVar[str] = "design-bench/superconductor-measured-pool-v1"

    visible_max_percentile: float = 80.0
    include_descriptors: bool = False

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_max_percentile < 100.0:
            raise ProtocolError("visible_max_percentile must be between 0 and 100")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> SuperconductorAgentInput:
        groups = self._load_groups(dataset, split)
        visible_indices, candidate_indices, _ = self.partition(groups)
        observations = self._visible_observations(groups, visible_indices)
        candidate_columns = [
            "composition_id",
            "composition",
            "representative_formula",
        ]
        if self.include_descriptors:
            candidate_columns.append("descriptor_features")
        candidates = groups.select(candidate_indices).select_columns(candidate_columns)
        return SuperconductorAgentInput(
            observations=observations,
            candidates=candidates,
            descriptor_names=DESCRIPTOR_NAMES if self.include_descriptors else (),
        )

    def candidate_pool(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        """Return the trusted labeled evaluation pool for Task construction."""

        groups = self._load_groups(dataset, split)
        _, candidate_indices, _ = self.partition(groups)
        return groups.select(candidate_indices)

    def partition(
        self,
        groups: HFDataset,
    ) -> tuple[list[int], list[int], float]:
        values = np.asarray(groups["critical_temp_k"], dtype=np.float64)
        if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
            raise ProtocolError("critical_temp_k must be a non-empty finite scalar column")
        cutoff = float(
            np.percentile(values, self.visible_max_percentile, method="linear")
        )
        visible = np.flatnonzero(values <= cutoff).tolist()
        candidates = np.flatnonzero(values > cutoff).tolist()
        if not visible or not candidates:
            raise ProtocolError("percentile partition produced an empty side")
        return visible, candidates, cutoff

    def _load_groups(self, dataset: Dataset, split: str | None) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"SuperconductorMeasuredPoolProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or SUPERCONDUCTOR_DEFAULT_SPLIT
        try:
            groups = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        required = {
            "composition_id",
            "composition",
            "representative_formula",
            "source_record_ids",
            "material_formulas",
            "critical_temperatures_k",
            "critical_temp_k",
            "descriptor_features_by_observation",
            "descriptor_features",
        }
        missing = sorted(required - set(groups.column_names))
        if missing:
            raise ProtocolError(f"Superconductor split is missing columns: {missing}")
        return groups

    def _visible_observations(
        self,
        groups: HFDataset,
        visible_indices: list[int],
    ) -> HFDataset:
        columns: dict[str, list[object]] = {
            "source_record_id": [],
            "composition_id": [],
            "composition": [],
            "material_formula": [],
            "critical_temp_k": [],
        }
        if self.include_descriptors:
            columns["descriptor_features"] = []
        for index in visible_indices:
            row = groups[index]
            for source_id, formula, temperature, descriptors in zip(
                row["source_record_ids"],
                row["material_formulas"],
                row["critical_temperatures_k"],
                row["descriptor_features_by_observation"],
                strict=True,
            ):
                columns["source_record_id"].append(source_id)
                columns["composition_id"].append(row["composition_id"])
                columns["composition"].append(row["composition"])
                columns["material_formula"].append(formula)
                columns["critical_temp_k"].append(temperature)
                if self.include_descriptors:
                    columns["descriptor_features"].append(descriptors)

        features: dict[str, object] = {
            "source_record_id": Value("int32"),
            "composition_id": Value("string"),
            "composition": Sequence(Value("float64"), length=len(ELEMENT_SYMBOLS)),
            "material_formula": Value("string"),
            "critical_temp_k": Value("float64"),
        }
        if self.include_descriptors:
            features["descriptor_features"] = Sequence(
                Value("float64"), length=len(DESCRIPTOR_NAMES)
            )
        return HFDataset.from_dict(columns, features=Features(features))
