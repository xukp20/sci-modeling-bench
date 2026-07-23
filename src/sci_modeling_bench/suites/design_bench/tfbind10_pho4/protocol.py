"""Lower-affinity observation Protocol for Pho4 BET-seq."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    AgentInputContext,
    Protocol,
    agent_input_manifest,
    agent_table_view,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    FIXED_EBOX_CORE,
    FLANK_LENGTH_PER_SIDE,
    FULL_SITE_TEMPLATE,
    SEQUENCE_COUNT,
    SEQUENCE_LENGTH,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    TFBIND10_PHO4_DEFAULT_SPLIT,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.objective import (
    Pho4AffinityLandscape,
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
class TFBind10Pho4LowerHalfProtocol(Protocol[HFDataset]):
    """Expose raw observations for the lower half of the measured landscape."""

    protocol_id: ClassVar[str] = "design-bench/tfbind10-pho4-lower-half-v2"

    visible_max_percentile: float = 50.0

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_max_percentile < 100.0:
            raise ProtocolError("visible_max_percentile must be between 0 and 100")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
        landscape: Pho4AffinityLandscape | None = None,
    ) -> AgentInputBundle[HFDataset]:
        observations = self._load_observations(dataset, split)
        selected_landscape = (
            landscape
            if landscape is not None
            else build_affinity_landscape(observations)
        )
        self._validate_landscape(selected_landscape, len(observations))
        values = selected_landscape.scores[selected_landscape.observed]
        cutoff = float(
            np.percentile(values, self.visible_max_percentile, method="linear")
        )
        visible_by_sequence = selected_landscape.observed & (
            selected_landscape.scores <= cutoff
        )
        visible_rows = np.flatnonzero(
            visible_by_sequence[selected_landscape.row_sequence_indices]
        ).tolist()
        if not visible_rows or len(visible_rows) == len(observations):
            raise ProtocolError("affinity percentile selection produced an empty side")
        visible = observations.select(visible_rows).select_columns(
            list(_AGENT_OBSERVATION_COLUMNS)
        )
        selected_split = split or TFBIND10_PHO4_DEFAULT_SPLIT
        view = agent_table_view(
            dataset,
            visible,
            name="observations",
            role="observations",
            description=(
                "Raw Pho4 sequence-replicate observations for the lower half of "
                "the trusted posterior-affinity landscape."
            ),
        )
        return AgentInputBundle(
            data=visible,
            manifest=agent_input_manifest(
                dataset,
                protocol_id=self.protocol_id,
                split=selected_split,
                views=(view,),
                context=(
                    AgentInputContext(
                        name="sequence_layout",
                        description=(
                            "Physical site layout encoded by every ten-character "
                            "sequence field and candidate."
                        ),
                        value={
                            "candidate_length": SEQUENCE_LENGTH,
                            "serialization": "upstream_then_downstream",
                            "upstream_length": FLANK_LENGTH_PER_SIDE,
                            "fixed_core": FIXED_EBOX_CORE,
                            "downstream_length": FLANK_LENGTH_PER_SIDE,
                            "full_site_template": FULL_SITE_TEMPLATE,
                            "candidate_includes_fixed_core": False,
                            "orientation": "5prime_to_3prime",
                        },
                    ),
                ),
            ),
        )

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
    def _validate_landscape(
        landscape: Pho4AffinityLandscape,
        observation_count: int,
    ) -> None:
        if landscape.scores.shape != (SEQUENCE_COUNT,):
            raise ProtocolError("Pho4 landscape scores have an invalid shape")
        if landscape.observed.shape != (SEQUENCE_COUNT,):
            raise ProtocolError("Pho4 landscape observed mask has an invalid shape")
        if landscape.row_sequence_indices.shape != (observation_count,):
            raise ProtocolError(
                "Pho4 landscape row indices do not match the observation split"
            )
        if not np.any(landscape.observed):
            raise ProtocolError("Pho4 landscape contains no observed sequences")
        if not np.all(np.isfinite(landscape.scores[landscape.observed])):
            raise ProtocolError("Pho4 observed affinity scores must be finite")
        row_indices = landscape.row_sequence_indices
        if np.any(row_indices < 0) or np.any(row_indices >= SEQUENCE_COUNT):
            raise ProtocolError("Pho4 landscape row indices are outside the domain")
        if not np.all(landscape.observed[row_indices]):
            raise ProtocolError("Pho4 landscape row indices include unseen sequences")
