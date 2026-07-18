from __future__ import annotations

import math

import pytest

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.suites.design_bench.drugmatrix import (
    DRUGMATRIX_ENDPOINTS,
    DrugMatrixEndpointObjective,
    DrugMatrixMeasuredPoolProtocol,
)


def test_protocol_hides_candidate_treatment_rows(tiny_drugmatrix_dataset) -> None:
    protocol = DrugMatrixMeasuredPoolProtocol()

    agent_input = protocol.build_input(tiny_drugmatrix_dataset)
    pool = protocol.candidate_pool(tiny_drugmatrix_dataset)

    assert len(pool) == 4
    assert len(agent_input.observations) == 8
    assert set(agent_input.candidates.column_names) == {
        "condition_id",
        "casrn",
        "canonical_smiles",
        "dose",
        "duration_days",
        "vehicle",
        "sex",
        "route",
        "study_id",
    }
    assert not any(
        row["animal_id"].startswith("candidate-")
        for row in agent_input.observations
    )


@pytest.mark.parametrize("endpoint", DRUGMATRIX_ENDPOINTS)
def test_objective_supports_every_endpoint(
    tiny_drugmatrix_dataset,
    endpoint: str,
) -> None:
    protocol = DrugMatrixMeasuredPoolProtocol()
    pool = protocol.candidate_pool(tiny_drugmatrix_dataset)
    objective = DrugMatrixEndpointObjective(
        tiny_drugmatrix_dataset,
        endpoint=endpoint,
    )

    output = objective.evaluate({"condition_id": pool[0]["condition_id"]})

    assert set(output) == {"raw_response", "control_deviation"}
    assert output["control_deviation"] == pytest.approx(
        abs(math.log(output["raw_response"] / (10.0 + DRUGMATRIX_ENDPOINTS.index(endpoint))))
    )


def test_objective_rejects_unknown_endpoint_and_condition(
    tiny_drugmatrix_dataset,
) -> None:
    with pytest.raises(ObjectiveError, match="endpoint must be one of"):
        DrugMatrixEndpointObjective(tiny_drugmatrix_dataset, endpoint="unknown")

    objective = DrugMatrixEndpointObjective(tiny_drugmatrix_dataset, endpoint="mchc")
    with pytest.raises(ObjectiveLookupError, match="absent from the measured pool"):
        objective.evaluate({"condition_id": "missing"})
