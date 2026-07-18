from __future__ import annotations

import sci_modeling_bench.suites.design_bench.tfbind10_pho4.protocol as protocol_module
from sci_modeling_bench.suites.design_bench.tfbind10_pho4 import (
    TFBind10Pho4BlackBoxOptimizationTask,
)

from .conftest import SEQUENCES


def test_task_uses_enrichment_and_common_metrics(tiny_tfbind10_pho4_dataset) -> None:
    task = TFBind10Pho4BlackBoxOptimizationTask(
        tiny_tfbind10_pho4_dataset,
        submission_size=2,
    )

    evaluation = task.evaluate(
        [{"sequence": SEQUENCES[-1]}, {"sequence": SEQUENCES[-2]}]
    )

    assert evaluation.evaluation_eligible
    assert task.task_id == "design-bench/tfbind10-pho4-black-box-optimization-v2"
    assert evaluation.primary_metric == "normalized_enrichment"
    assert evaluation.score == 1.0
    assert evaluation.reference_scope == "full_domain"
    assert evaluation.reference_size == len(SEQUENCES)
    assert evaluation.metrics.keys() == task.metric_directions.keys()


def test_task_accepts_visible_sequences_as_legal_domain_candidates(
    tiny_tfbind10_pho4_dataset,
) -> None:
    task = TFBind10Pho4BlackBoxOptimizationTask(
        tiny_tfbind10_pho4_dataset,
        submission_size=2,
    )

    evaluation = task.evaluate(
        [{"sequence": SEQUENCES[0]}, {"sequence": SEQUENCES[-1]}]
    )

    assert evaluation.evaluation_eligible
    assert evaluation.valid_candidates == 2
    assert evaluation.invalid_candidates == 0
    assert evaluation.candidates[0].validation.valid
    assert evaluation.metrics


def test_task_reuses_objective_scores_when_building_input(
    tiny_tfbind10_pho4_dataset,
    monkeypatch,
) -> None:
    task = TFBind10Pho4BlackBoxOptimizationTask(
        tiny_tfbind10_pho4_dataset,
        submission_size=2,
    )

    def fail_if_recomputed(*_args, **_kwargs):
        raise AssertionError("Task.build_input() recomputed the affinity landscape")

    monkeypatch.setattr(
        protocol_module,
        "build_affinity_landscape",
        fail_if_recomputed,
    )

    agent_input = task.build_input().data

    assert len(agent_input) == 16
    assert set(agent_input["sequence"]) == set(SEQUENCES[:4])
