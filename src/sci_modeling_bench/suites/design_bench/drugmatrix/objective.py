"""Measured control-relative Objective for DrugMatrix endpoints."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.drugmatrix._conditions import (
    ENDPOINTS,
    build_measured_pool,
)
from sci_modeling_bench.suites.design_bench.drugmatrix.dataset import (
    DRUGMATRIX_DEFAULT_SPLIT,
    DrugMatrixDataset,
)

_DATASET_ID = "design-bench/drugmatrix-clinical-pathology"


class DrugMatrixEndpointObjective(Objective):
    """Aggregate one endpoint for measured treatment/control conditions."""

    objective_id = "design-bench/drugmatrix-control-deviation-v1"

    def __init__(
        self,
        dataset: DrugMatrixDataset,
        *,
        endpoint: str,
        split: str = DRUGMATRIX_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"DrugMatrixEndpointObjective requires dataset_id {_DATASET_ID!r}, "
                f"got {dataset.metadata.dataset_id!r}"
            )
        if endpoint not in ENDPOINTS:
            raise ObjectiveError(f"endpoint must be one of {ENDPOINTS}, got {endpoint!r}")
        dataset.split(split)
        self._endpoint = endpoint
        self._split = split
        self._lookup: dict[str, tuple[str, float, float]] | None = None
        super().__init__(dataset)

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def split(self) -> str:
        return self._split

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("raw_response", "control_deviation")

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            identity = candidate.get("condition_id")
            try:
                _, raw_response, control_deviation = lookup[str(identity)]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"condition {identity!r} is absent from the measured pool"
                ) from exc
            yield {
                "raw_response": raw_response,
                "control_deviation": control_deviation,
            }

    def _candidate_for_dataset_validation(self, candidate: Candidate) -> Candidate:
        identity = str(candidate.get("condition_id"))
        entry = self._get_lookup().get(identity)
        return {"canonical_smiles": entry[0] if entry is not None else None}

    def _get_lookup(self) -> dict[str, tuple[str, float, float]]:
        if self._lookup is not None:
            return self._lookup
        table = build_measured_pool(self.dataset.load(self.split)).table
        raw_field = f"{self.endpoint}_raw_response"
        deviation_field = f"{self.endpoint}_control_deviation"
        lookup = {
            str(identity): (str(smiles), float(raw), float(deviation))
            for identity, smiles, raw, deviation in zip(
                table["condition_id"],
                table["canonical_smiles"],
                table[raw_field],
                table[deviation_field],
                strict=True,
            )
        }
        if len(lookup) != len(table):
            raise ObjectiveError("DrugMatrix measured-pool condition IDs must be unique")
        self._lookup = lookup
        return lookup
