from __future__ import annotations

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
    assert evaluation.primary_metric == "normalized_enrichment"
    assert evaluation.score == 1.0
    assert evaluation.reference_scope == "evaluation_pool"
    assert evaluation.metrics.keys() == task.metric_directions.keys()


def test_task_rejects_visible_sequence_without_fabricating_metrics(
    tiny_tfbind10_pho4_dataset,
) -> None:
    task = TFBind10Pho4BlackBoxOptimizationTask(
        tiny_tfbind10_pho4_dataset,
        submission_size=2,
    )

    evaluation = task.evaluate(
        [{"sequence": SEQUENCES[0]}, {"sequence": SEQUENCES[-1]}]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )
