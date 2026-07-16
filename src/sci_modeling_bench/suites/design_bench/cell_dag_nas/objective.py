"""Canonical exact-table Objective for CellDAG-NAS."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.cell_dag_nas._graph import (
    decode_architecture,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas.dataset import (
    CELL_DAG_NAS_DEFAULT_SPLIT,
    CellDAGNASDataset,
)

_DATASET_ID = "design-bench/cell-dag-nas"
_OUTPUT_FIELDS = ("test_accuracies", "mean_test_accuracy")


class CellDAGNASExactObjective(Objective):
    """Evaluate every graph alias through one canonical NASBench lookup."""

    objective_id = "design-bench/cell-dag-nas-exact-v1"

    def __init__(
        self,
        dataset: CellDAGNASDataset,
        *,
        split: str = CELL_DAG_NAS_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"CellDAGNASExactObjective requires dataset_id {_DATASET_ID!r}, "
                f"got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._lookup: dict[str, tuple[tuple[float, ...], float]] | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return _OUTPUT_FIELDS

    @property
    def split(self) -> str:
        return self._split

    def canonical_hash(self, candidate: Candidate) -> str:
        """Return the canonical graph identity for a validated candidate."""

        return decode_architecture(candidate["architecture"]).canonical_hash

    def contains_hash(self, canonical_hash: str) -> bool:
        return canonical_hash in self._get_lookup()

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            canonical_hash = self.canonical_hash(candidate)
            try:
                repeats, mean = lookup[canonical_hash]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"valid graph {canonical_hash!r} is absent from the frozen table"
                ) from exc
            yield {
                "test_accuracies": list(repeats),
                "mean_test_accuracy": mean,
            }

    def _get_lookup(self) -> dict[str, tuple[tuple[float, ...], float]]:
        if self._lookup is not None:
            return self._lookup
        observations = self.dataset.load(self.split)
        required = {"canonical_hash", *_OUTPUT_FIELDS}
        missing = sorted(required - set(observations.column_names))
        if missing:
            raise ObjectiveError(f"CellDAG-NAS split is missing columns: {missing}")
        lookup: dict[str, tuple[tuple[float, ...], float]] = {}
        for canonical_hash, repeats, mean in zip(
            observations["canonical_hash"],
            observations["test_accuracies"],
            observations["mean_test_accuracy"],
        ):
            if canonical_hash in lookup:
                raise ObjectiveError(f"duplicate canonical hash {canonical_hash!r}")
            lookup[canonical_hash] = (
                tuple(float(value) for value in repeats),
                float(mean),
            )
        self._lookup = lookup
        return lookup
