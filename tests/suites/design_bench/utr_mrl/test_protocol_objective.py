from __future__ import annotations

import pytest

from sci_modeling_bench.exceptions import ObjectiveLookupError
from sci_modeling_bench.suites.design_bench.utr_mrl import (
    UTRMRLCompositionalProtocol,
    UTRMRLMeasuredObjective,
)

from .conftest import UAUG_WEAK


def test_protocol_exposes_labels_only_for_observations(tiny_utr_mrl_dataset) -> None:
    agent_input = UTRMRLCompositionalProtocol().build_input(tiny_utr_mrl_dataset)

    assert len(agent_input.observations) == 3
    assert len(agent_input.candidates) == 4
    assert agent_input.observations.column_names == [
        "sequence",
        "mean_ribosome_load",
    ]
    assert agent_input.candidates.column_names == ["sequence"]
    assert set(agent_input.candidates["sequence"]) == set(UAUG_WEAK)


def test_measured_objective_preserves_order_and_duplicates(
    tiny_utr_mrl_dataset,
) -> None:
    objective = UTRMRLMeasuredObjective(tiny_utr_mrl_dataset)

    outputs = objective.evaluate_batch(
        [
            {"sequence": UAUG_WEAK[3]},
            {"sequence": UAUG_WEAK[0]},
            {"sequence": UAUG_WEAK[3]},
        ]
    )

    assert [row["mean_ribosome_load"] for row in outputs] == [8.0, 1.0, 8.0]
    assert objective.output_fields == ("mean_ribosome_load",)


def test_measured_objective_rejects_unmeasured_sequence(
    tiny_utr_mrl_dataset,
) -> None:
    objective = UTRMRLMeasuredObjective(tiny_utr_mrl_dataset)

    with pytest.raises(ObjectiveLookupError):
        objective.evaluate({"sequence": "A" * 50})
