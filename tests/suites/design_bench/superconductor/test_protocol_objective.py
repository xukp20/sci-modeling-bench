from __future__ import annotations

from sci_modeling_bench.suites.design_bench.superconductor import (
    SuperconductorMeasuredObjective,
    SuperconductorMeasuredPoolProtocol,
)


def test_protocol_exposes_raw_visible_observations_and_hidden_candidates(
    tiny_superconductor_dataset,
) -> None:
    protocol = SuperconductorMeasuredPoolProtocol(visible_max_percentile=50.0)

    agent_input = protocol.build_input(tiny_superconductor_dataset)
    pool = protocol.candidate_pool(tiny_superconductor_dataset)

    assert len(agent_input.observations) == 5
    assert agent_input.observations["critical_temp_k"] == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert len(agent_input.candidates) == 5
    assert "composition_id" not in agent_input.candidates.column_names
    assert "critical_temp_k" not in agent_input.candidates.column_names
    assert pool["critical_temp_k"] == [6.0, 7.0, 8.0, 9.0, 10.0]


def test_protocol_can_expose_published_descriptor_features(
    tiny_superconductor_dataset,
) -> None:
    agent_input = SuperconductorMeasuredPoolProtocol(
        visible_max_percentile=50.0,
        include_descriptors=True,
    ).build_input(tiny_superconductor_dataset)

    assert "descriptor_features" in agent_input.observations.column_names
    assert "descriptor_features" in agent_input.candidates.column_names
    assert len(agent_input.descriptor_names) == 81


def test_objective_returns_the_group_median_measurement(
    tiny_superconductor_dataset,
) -> None:
    row = tiny_superconductor_dataset.load()[7]
    objective = SuperconductorMeasuredObjective(tiny_superconductor_dataset)

    assert objective.evaluate({"composition_id": row["composition_id"]}) == {
        "critical_temp_k": 8.0
    }
