from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.superconductor import (
    SuperconductorBlackBoxOptimizationTask,
    SuperconductorMeasuredPoolProtocol,
)


def _task(dataset, **kwargs):
    return SuperconductorBlackBoxOptimizationTask(
        dataset,
        protocol=SuperconductorMeasuredPoolProtocol(
            visible_max_percentile=50.0
        ),
        submission_size=3,
        **kwargs,
    )


def test_task_scores_selection_and_submitted_order(
    tiny_superconductor_dataset,
) -> None:
    task = _task(tiny_superconductor_dataset)
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)
    by_score = {row["critical_temp_k"]: row["composition_id"] for row in pool}

    evaluation = task.evaluate(
        [
            {"composition_id": by_score[8.0]},
            {"composition_id": by_score[10.0]},
            {"composition_id": by_score[9.0]},
        ]
    )

    assert evaluation.primary_metric == "global_ndcg"
    assert evaluation.metrics["best_score"] == 10.0
    assert evaluation.metrics["rank_1_score"] == 8.0
    assert evaluation.metrics["best_k_mean"] == 9.0
    assert evaluation.metrics["batch_mean"] == 9.0
    assert evaluation.metrics["normalized_enrichment"] == 1.0
    assert 0.0 < evaluation.score < 1.0
    assert evaluation.score == evaluation.metrics["reranking_ndcg"]
    assert evaluation.reference_scope == "evaluation_pool"


def test_task_can_select_an_alternate_primary_metric(
    tiny_superconductor_dataset,
) -> None:
    task = _task(tiny_superconductor_dataset, primary_metric="batch_mean")
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)
    candidates = [
        {"composition_id": pool[index]["composition_id"]}
        for index in (2, 3, 4)
    ]

    evaluation = task.evaluate(candidates)

    assert evaluation.primary_metric == "batch_mean"
    assert evaluation.score == 9.0


def test_candidate_outside_hidden_pool_is_rejected(
    tiny_superconductor_dataset,
) -> None:
    task = _task(tiny_superconductor_dataset)
    data = tiny_superconductor_dataset.load()
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)

    evaluation = task.evaluate(
        [
            {"composition_id": data[0]["composition_id"]},
            {"composition_id": pool[0]["composition_id"]},
            {"composition_id": pool[1]["composition_id"]},
        ]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )


def test_repeated_composition_id_is_rejected(
    tiny_superconductor_dataset,
) -> None:
    task = _task(tiny_superconductor_dataset)
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)
    candidate = {"composition_id": pool[0]["composition_id"]}

    evaluation = task.evaluate(
        [candidate, candidate, {"composition_id": pool[1]["composition_id"]}]
    )

    assert evaluation.metrics == {}
    assert evaluation.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )
