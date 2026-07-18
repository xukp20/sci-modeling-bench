from __future__ import annotations

from sci_modeling_bench.suites.design_bench.superconductor import (
    SuperconductorCandidatePoolRankingTask,
    SuperconductorMeasuredPoolProtocol,
)
from sci_modeling_bench.task import CandidatePoolRankingTask


def _task(dataset, **kwargs):
    return SuperconductorCandidatePoolRankingTask(
        dataset,
        protocol=SuperconductorMeasuredPoolProtocol(visible_max_percentile=50.0),
        submission_size=3,
        **kwargs,
    )


def test_task_scores_selection_and_submitted_order(
    tiny_superconductor_dataset,
) -> None:
    task = _task(tiny_superconductor_dataset)
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)
    by_score = {row["critical_temp_k"]: row["composition"] for row in pool}

    candidates = {
        tuple(row["composition"]): row for row in task.build_input().candidates
    }
    evaluation = task.evaluate(
        [
            candidates[tuple(by_score[8.0])],
            candidates[tuple(by_score[10.0])],
            candidates[tuple(by_score[9.0])],
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
    visible_candidates = {
        tuple(row["composition"]): row for row in task.build_input().candidates
    }
    candidates = [
        visible_candidates[tuple(pool[index]["composition"])] for index in (2, 3, 4)
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
            {
                "composition": data[0]["composition"],
            },
            pool[0],
            pool[1],
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
    candidate = task.build_input().candidates[0]

    evaluation = task.evaluate([candidate, candidate, task.build_input().candidates[1]])

    assert evaluation.metrics == {}
    assert evaluation.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )


def test_canonical_task_accepts_candidate_content_and_ignores_a_suffix(
    tiny_superconductor_dataset,
) -> None:
    task = SuperconductorCandidatePoolRankingTask(
        tiny_superconductor_dataset,
        protocol=SuperconductorMeasuredPoolProtocol(visible_max_percentile=50.0),
        submission_size=3,
    )
    candidates = list(task.build_input().candidates)

    evaluation = task.evaluate(candidates[:4])

    assert isinstance(task, CandidatePoolRankingTask)
    assert evaluation.submission_valid
    assert evaluation.evaluation_eligible
    assert evaluation.candidate_pool_size == 5
    assert evaluation.evaluated_candidates == 3
    assert evaluation.ignored_candidates == 1


def test_canonical_task_rejects_id_only_submission(
    tiny_superconductor_dataset,
) -> None:
    task = SuperconductorCandidatePoolRankingTask(
        tiny_superconductor_dataset,
        protocol=SuperconductorMeasuredPoolProtocol(visible_max_percentile=50.0),
        submission_size=3,
    )
    pool = task.protocol.candidate_pool(tiny_superconductor_dataset)

    evaluation = task.evaluate(
        [{"composition_id": value} for value in pool["composition_id"][:3]]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.candidates[0].validation.violations[0].field == "composition_id"
