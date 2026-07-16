from __future__ import annotations

import numpy as np
import pytest

from sci_modeling_bench.suites.design_bench.cell_dag_nas import (
    CellDAGNASBlackBoxOptimizationTask,
)
from tests.suites.design_bench.cell_dag_nas.conftest import A, B, C, D


def test_task_returns_common_metrics_for_unique_in_table_graphs(
    tiny_cell_dag_nas_dataset,
) -> None:
    task = CellDAGNASBlackBoxOptimizationTask(
        tiny_cell_dag_nas_dataset,
        submission_size=2,
    )
    evaluation = task.evaluate(
        [{"architecture": B}, {"architecture": C}]
    )

    assert evaluation.evaluation_eligible
    assert evaluation.primary_metric == "best_k_mean"
    assert evaluation.score == pytest.approx(0.7)
    assert evaluation.metrics["best_score"] == pytest.approx(0.9)
    assert evaluation.metrics["best_k_mean"] == pytest.approx(0.7)
    assert evaluation.metrics["best_regret"] == pytest.approx(0.0)
    assert evaluation.metrics["best_k_mean_regret"] == pytest.approx(0.0)
    assert evaluation.metrics["batch_mean_regret"] == pytest.approx(
        0.0, abs=1e-9
    )
    assert evaluation.metrics["normalized_enrichment"] == pytest.approx(
        1.0, abs=1e-8
    )
    assert evaluation.reference_scope == "full_domain"
    assert evaluation.reference_size == 3


def test_task_uses_canonical_graph_identity_for_duplicates(
    tiny_cell_dag_nas_dataset,
) -> None:
    task = CellDAGNASBlackBoxOptimizationTask(
        tiny_cell_dag_nas_dataset,
        submission_size=2,
    )
    evaluation = task.evaluate(
        [{"architecture": A}, {"architecture": A}]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.score is None
    assert evaluation.valid_candidates == 1
    assert evaluation.invalid_candidates == 1
    assert evaluation.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )


def test_task_marks_legal_graph_absent_from_frozen_table(
    tiny_cell_dag_nas_dataset,
) -> None:
    task = CellDAGNASBlackBoxOptimizationTask(
        tiny_cell_dag_nas_dataset,
        submission_size=2,
    )
    evaluation = task.evaluate(
        [{"architecture": B}, {"architecture": D}]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.candidates[1].validation.violations[0].code == (
        "out_of_table_graph"
    )


def test_task_keeps_dataset_validation_findings(
    tiny_cell_dag_nas_dataset,
) -> None:
    task = CellDAGNASBlackBoxOptimizationTask(
        tiny_cell_dag_nas_dataset,
        submission_size=2,
    )
    invalid = A.copy()
    invalid[4] = 9
    evaluation = task.evaluate(
        [{"architecture": B}, {"architecture": invalid}]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.candidates[1].validation.violations[0].code == "non_full_dag"


def test_task_allows_an_explicit_primary_metric(
    tiny_cell_dag_nas_dataset,
) -> None:
    task = CellDAGNASBlackBoxOptimizationTask(
        tiny_cell_dag_nas_dataset,
        submission_size=2,
        primary_metric="normalized_enrichment",
    )
    evaluation = task.evaluate(
        [{"architecture": B}, {"architecture": C}]
    )

    assert evaluation.primary_metric == "normalized_enrichment"
    assert evaluation.score == pytest.approx(1.0)


@pytest.mark.integration
def test_published_task_scores_the_frozen_top_128(
    published_cell_dag_nas_dataset,
) -> None:
    observations = published_cell_dag_nas_dataset.load().with_format("numpy")
    scores = np.asarray(observations["mean_test_accuracy"], dtype=np.float64)
    top = np.argpartition(scores, -128)[-128:]
    top = top[np.argsort(scores[top])[::-1]]
    architectures = observations.select(top.tolist())["architecture"]
    task = CellDAGNASBlackBoxOptimizationTask(published_cell_dag_nas_dataset)

    evaluation = task.evaluate(
        [{"architecture": architecture} for architecture in architectures]
    )

    assert evaluation.evaluation_eligible
    assert evaluation.reference_scope == "full_domain"
    assert evaluation.reference_size == 423_624
    assert evaluation.metrics["best_regret"] == pytest.approx(0.0)
    assert evaluation.metrics["best_k_mean_regret"] == pytest.approx(0.0)
    assert evaluation.metrics["batch_mean_regret"] == pytest.approx(
        0.0, abs=1e-9
    )
    assert evaluation.metrics["normalized_enrichment"] == pytest.approx(
        1.0, abs=1e-8
    )
