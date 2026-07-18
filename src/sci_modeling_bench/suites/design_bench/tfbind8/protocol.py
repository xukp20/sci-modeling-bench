"""Agent-visible offline-data Protocol for TFBind8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    Protocol,
    agent_input_manifest,
    agent_table_view,
)
from sci_modeling_bench.suites.design_bench.tfbind8.dataset import (
    TFBIND8_DEFAULT_SPLIT,
)

_TFBIND8_DATASET_ID = "design-bench/tfbind8"


@dataclass(frozen=True)
class TFBind8DesignBenchProtocol(Protocol[HFDataset]):
    """Expose a deterministic target-percentile slice of TFBind8 observations."""

    protocol_id: ClassVar[str] = "design-bench/tfbind8-bottom-percentile-v1"

    min_percentile: float = 0.0
    max_percentile: float = 50.0
    target_field: str = "normalized_e_score"

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_percentile <= 100.0:
            raise ProtocolError("min_percentile must be between 0 and 100")
        if not 0.0 <= self.max_percentile <= 100.0:
            raise ProtocolError("max_percentile must be between 0 and 100")
        if self.min_percentile > self.max_percentile:
            raise ProtocolError("min_percentile cannot exceed max_percentile")
        if not self.target_field.strip():
            raise ProtocolError("target_field must be a non-empty string")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> AgentInputBundle[HFDataset]:
        if dataset.metadata.dataset_id != _TFBIND8_DATASET_ID:
            raise ProtocolError(
                f"TFBind8DesignBenchProtocol requires dataset_id "
                f"{_TFBIND8_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )

        target_fields = {field.name for field in dataset.schema.targets}
        if self.target_field not in target_fields:
            raise ProtocolError(
                f"target field {self.target_field!r} is not declared by the Dataset"
            )

        selected_split = split or TFBIND8_DEFAULT_SPLIT
        try:
            observations = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc

        required_columns = {"sequence", self.target_field}
        missing = sorted(required_columns - set(observations.column_names))
        if missing:
            raise ProtocolError(
                f"TFBind8 split {selected_split!r} is missing columns: {missing}"
            )

        values = np.asarray(observations[self.target_field])
        if values.ndim != 1 or not np.issubdtype(values.dtype, np.number):
            raise ProtocolError(
                f"target field {self.target_field!r} must be a numeric scalar column"
            )
        if values.size == 0:
            raise ProtocolError(f"TFBind8 split {selected_split!r} is empty")
        if not np.all(np.isfinite(values)):
            raise ProtocolError(
                f"target field {self.target_field!r} contains non-finite values"
            )

        minimum = (
            -np.inf
            if self.min_percentile == 0.0
            else np.percentile(values, self.min_percentile, method="linear")
        )
        maximum = (
            np.inf
            if self.max_percentile == 100.0
            else np.percentile(values, self.max_percentile, method="linear")
        )
        selected_indices = np.flatnonzero(
            np.logical_and(values >= minimum, values <= maximum)
        ).tolist()

        visible = observations.select(selected_indices).select_columns(
            ["sequence", self.target_field]
        )
        view = agent_table_view(
            dataset,
            visible,
            name="observations",
            role="observations",
            description=(
                "Agent-visible TFBind8 sequences and measured scores selected by "
                "the configured target-percentile interval."
            ),
        )
        return AgentInputBundle(
            data=visible,
            manifest=agent_input_manifest(
                dataset,
                protocol_id=self.protocol_id,
                split=selected_split,
                views=(view,),
            ),
        )
