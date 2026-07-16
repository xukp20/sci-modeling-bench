"""Default Agent-visible offline Protocol for CellDAG-NAS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pyarrow as pa
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.cell_dag_nas.dataset import (
    CELL_DAG_NAS_DEFAULT_SPLIT,
)

_DATASET_ID = "design-bench/cell-dag-nas"


@dataclass(frozen=True)
class CellDAGNASDesignBenchProtocol(Protocol[HFDataset]):
    """Expose aliases and raw test repeats for the lowest-scoring graphs."""

    protocol_id: ClassVar[str] = "design-bench/cell-dag-nas-low-canonical-v1"
    visible_fraction: float = 0.40

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_fraction <= 1.0:
            raise ProtocolError("visible_fraction must be in the interval (0, 1]")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"CellDAGNASDesignBenchProtocol requires dataset_id {_DATASET_ID!r}, "
                f"got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or CELL_DAG_NAS_DEFAULT_SPLIT
        try:
            observations = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        required = {"canonical_hash", "aliases", "test_accuracies", "mean_test_accuracy"}
        missing = sorted(required - set(observations.column_names))
        if missing:
            raise ProtocolError(f"CellDAG-NAS split is missing columns: {missing}")

        count = int(np.floor(len(observations) * self.visible_fraction))
        if count == 0:
            raise ProtocolError("visible_fraction selects no canonical graphs")
        table = observations.data.table.combine_chunks()
        means = table["mean_test_accuracy"].to_numpy()
        hashes = table["canonical_hash"].to_pylist()
        order = sorted(
            range(len(observations)),
            key=lambda index: (
                float(means[index]),
                hashes[index],
            ),
        )[:count]

        selected = table.take(pa.array(order, type=pa.int64()))
        aliases = selected["aliases"].chunk(0)
        offsets = aliases.offsets.to_numpy()
        multiplicities = offsets[1:] - offsets[:-1]
        repeat_indices = np.repeat(np.arange(count, dtype=np.int64), multiplicities)
        agent_table = pa.Table.from_arrays(
            [
                aliases.values,
                selected["test_accuracies"].chunk(0).take(
                    pa.array(repeat_indices, type=pa.int64())
                ),
            ],
            names=["architecture", "test_accuracies"],
        )
        return HFDataset(agent_table)
