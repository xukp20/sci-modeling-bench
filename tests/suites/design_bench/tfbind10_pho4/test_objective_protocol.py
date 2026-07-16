from __future__ import annotations

from sci_modeling_bench.suites.design_bench.tfbind10_pho4 import (
    TFBind10Pho4LowerHalfProtocol,
    TFBind10Pho4PosteriorObjective,
)

from .conftest import SEQUENCES


def test_posterior_objective_returns_derived_affinity_in_order(
    tiny_tfbind10_pho4_dataset,
) -> None:
    objective = TFBind10Pho4PosteriorObjective(tiny_tfbind10_pho4_dataset)

    outputs = objective.evaluate_batch(
        [{"sequence": SEQUENCES[-1]}, {"sequence": SEQUENCES[0]}]
    )

    assert outputs[0]["affinity_score"] > outputs[1]["affinity_score"]
    assert objective.output_fields == ("affinity_score",)
    assert "affinity_score" not in {
        field.name for field in tiny_tfbind10_pho4_dataset.schema.targets
    }


def test_protocol_exposes_raw_lower_half_and_hides_candidate_labels(
    tiny_tfbind10_pho4_dataset,
) -> None:
    agent_input = TFBind10Pho4LowerHalfProtocol().build_input(
        tiny_tfbind10_pho4_dataset
    )

    assert len(agent_input.observations) == 16
    assert set(agent_input.observations["sequence"]) == set(SEQUENCES[:4])
    assert agent_input.observations.column_names == [
        "sequence",
        "replicate_id",
        "bound_count",
        "input_count",
        "bound_fraction",
        "input_fraction",
        "observed_ddg",
    ]
    assert agent_input.candidates.column_names == ["sequence"]
    assert set(agent_input.candidates["sequence"]) == set(SEQUENCES[4:])
