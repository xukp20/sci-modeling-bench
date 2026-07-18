from __future__ import annotations

from sci_modeling_bench.suites.design_bench.utr_mrl import (
    UTRMRLCompositionalRankingTask,
)
from sci_modeling_bench.task import CandidatePoolRankingTask

from .conftest import NO_UAUG_STRONG


def test_task_scores_ordered_candidate_selection(tiny_utr_mrl_dataset) -> None:
    task = UTRMRLCompositionalRankingTask(
        tiny_utr_mrl_dataset,
        submission_size=3,
    )
    by_sequence = {
        row["sequence"]: row for row in task.build_input().candidates
    }
    pool = task.protocol.candidate_pool(tiny_utr_mrl_dataset)
    ranked = sorted(pool, key=lambda row: row["mean_ribosome_load"], reverse=True)

    evaluation = task.evaluate(
        [by_sequence[row["sequence"]] for row in ranked[:3]]
    )

    assert isinstance(task, CandidatePoolRankingTask)
    assert evaluation.evaluation_eligible
    assert evaluation.primary_metric == "global_ndcg"
    assert evaluation.score == 1.0
    assert evaluation.metrics["best_score"] == 8.0
    assert evaluation.metrics["rank_1_score"] == 8.0
    assert evaluation.metrics["best_k_mean"] == 17.0 / 3.0
    assert evaluation.reference_scope == "evaluation_pool"


def test_task_rejects_visible_or_duplicate_candidates(tiny_utr_mrl_dataset) -> None:
    task = UTRMRLCompositionalRankingTask(
        tiny_utr_mrl_dataset,
        submission_size=3,
    )
    candidate = task.build_input().candidates[0]

    outside = task.evaluate(
        [
            {"sequence": NO_UAUG_STRONG},
            candidate,
            task.build_input().candidates[1],
        ]
    )
    duplicate = task.evaluate(
        [candidate, candidate, task.build_input().candidates[1]]
    )

    assert not outside.evaluation_eligible
    assert outside.metrics == {}
    assert outside.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )
    assert not duplicate.evaluation_eligible
    assert duplicate.metrics == {}
    assert duplicate.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )
