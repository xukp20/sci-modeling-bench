from __future__ import annotations

from sci_modeling_bench.suites.design_bench.gfp import (
    GFPCandidatePoolRankingTask,
    GFPLowerToHigherMeasuredPoolProtocol,
)


def _task(dataset, **kwargs):
    return GFPCandidatePoolRankingTask(
        dataset,
        protocol=GFPLowerToHigherMeasuredPoolProtocol(visible_max_percentile=50.0),
        submission_size=3,
        **kwargs,
    )


def test_task_scores_selection_and_order(tiny_gfp_dataset) -> None:
    task = _task(tiny_gfp_dataset)
    pool = task.protocol.candidate_pool(tiny_gfp_dataset)
    by_score = {
        row["median_log10_brightness"]: row["sequence"] for row in pool
    }

    evaluation = task.evaluate(
        [
            {"sequence": by_score[8.0]},
            {"sequence": by_score[10.0]},
            {"sequence": by_score[9.0]},
        ]
    )

    assert evaluation.evaluation_eligible
    assert evaluation.primary_metric == "global_ndcg"
    assert evaluation.metrics["best_score"] == 10.0
    assert evaluation.metrics["rank_1_score"] == 8.0
    assert evaluation.metrics["batch_mean"] == 9.0
    assert evaluation.metrics["normalized_enrichment"] == 1.0
    assert 0.0 < evaluation.score < 1.0


def test_task_accepts_agent_candidate_rows_and_ignores_suffix(
    tiny_gfp_dataset,
) -> None:
    task = _task(tiny_gfp_dataset)
    candidates = list(task.build_input().candidates)

    evaluation = task.evaluate(candidates[:4])

    assert evaluation.evaluation_eligible
    assert evaluation.evaluated_candidates == 3
    assert evaluation.ignored_candidates == 1


def test_task_rejects_visible_or_repeated_sequence(tiny_gfp_dataset) -> None:
    task = _task(tiny_gfp_dataset)
    visible = task.build_input().protein_observations[0]["sequence"]
    candidates = list(task.build_input().candidates)

    outside = task.evaluate(
        [{"sequence": visible}, candidates[0], candidates[1]]
    )
    repeated = task.evaluate([candidates[0], candidates[0], candidates[1]])

    assert not outside.evaluation_eligible
    assert outside.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )
    assert not repeated.evaluation_eligible
    assert repeated.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )
