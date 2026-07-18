"""Measured-pool Protocol for UCI Superconductor composition groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    AgentInputContext,
    AgentInputField,
    Protocol,
    agent_input_field,
    agent_input_manifest,
    agent_table_view,
)
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
    ) -> AgentInputBundle[SuperconductorAgentInput]:
        groups = self._load_groups(dataset, split)
        visible_indices, candidate_indices, _ = self.partition(groups)
        observations = self._visible_observations(groups, visible_indices)
        candidate_columns = [
            "composition",
            "representative_formula",
        ]
        if self.include_descriptors:
            candidate_columns.append("descriptor_features")
        candidates = groups.select(candidate_indices).select_columns(candidate_columns)
        data = SuperconductorAgentInput(
            observations=observations,
            candidates=candidates,
            descriptor_names=DESCRIPTOR_NAMES if self.include_descriptors else (),
        )
        selected_split = split or SUPERCONDUCTOR_DEFAULT_SPLIT
        context = [
            AgentInputContext(
                name="element_symbols",
                description=(
                    "Element order used by every fixed-length composition vector."
                ),
                value=list(data.element_symbols),
            )
        ]
        if data.descriptor_names:
            context.append(
                AgentInputContext(
                    name="descriptor_names",
                    description=(
                        "Published descriptor order used by every descriptor_features vector."
                    ),
                    value=list(data.descriptor_names),
                )
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
                            "Source-level critical-temperature measurements for "
                            "visible lower-temperature composition groups."
                        ),
                        overrides=_observation_view_fields(data.observations),
                    ),
                    agent_table_view(
                        dataset,
                        data.candidates,
                        name="candidates",
                        role="candidates",
                        description=(
                            "Label-hidden measured composition groups available for ranking."
                        ),
                        overrides=_candidate_view_fields(data.candidates),
                    ),
                ),
                context=tuple(context),
            ),
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


def _observation_view_fields(data: HFDataset) -> dict[str, AgentInputField]:
    fields = {
        "source_record_id": agent_input_field(
            data,
            "source_record_id",
            role="context",
            description="Stable source-row identifier for one measured material record.",
            source_field="source_record_ids",
        ),
        "composition_id": agent_input_field(
            data,
            "composition_id",
            role="context",
            description="Stable identity of the normalized composition group.",
            source_field="composition_id",
        ),
        "composition": agent_input_field(
            data,
            "composition",
            role="input",
            description=(
                "Normalized elemental composition vector in element_symbols order."
            ),
            source_field="composition",
        ),
        "material_formula": agent_input_field(
            data,
            "material_formula",
            role="context",
            description="Source material formula associated with this observation.",
            source_field="material_formulas",
        ),
    }
    if "descriptor_features" in data.column_names:
        fields["descriptor_features"] = agent_input_field(
            data,
            "descriptor_features",
            role="context",
            description=(
                "Published descriptor vector in descriptor_names order for this observation."
            ),
            source_field="descriptor_features_by_observation",
        )
    return fields


def _candidate_view_fields(data: HFDataset) -> dict[str, AgentInputField]:
    fields = {
        "composition": agent_input_field(
            data,
            "composition",
            role="input",
            description=(
                "Normalized elemental composition vector in element_symbols order."
            ),
            source_field="composition",
        ),
        "representative_formula": agent_input_field(
            data,
            "representative_formula",
            role="context",
            description="Representative source formula for the composition group.",
            source_field="representative_formula",
        ),
    }
    if "descriptor_features" in data.column_names:
        fields["descriptor_features"] = agent_input_field(
            data,
            "descriptor_features",
            role="context",
            description=(
                "Published group descriptor vector in descriptor_names order."
            ),
            source_field="descriptor_features",
        )
    return fields
