from __future__ import annotations

from inspect import signature

import pytest

from sci_modeling_bench.suites.design_bench import (
    CellDAGNASBlackBoxOptimizationTask,
    DrugMatrixCandidatePoolRankingTask,
    GFPCandidatePoolRankingTask,
    HopperControllerCandidatePoolRankingTask,
    SuperconductorCandidatePoolRankingTask,
    TFBind10Pho4BlackBoxOptimizationTask,
    TFBind8BlackBoxOptimizationTask,
    UTRMRLCompositionalRankingTask,
)


@pytest.mark.parametrize(
    ("task_type", "submission_size", "summary_size", "primary_metric"),
    [
        (TFBind8BlackBoxOptimizationTask, 32, 5, "best_k_mean"),
        (CellDAGNASBlackBoxOptimizationTask, 32, 5, "best_k_mean"),
        (TFBind10Pho4BlackBoxOptimizationTask, 128, 16, "normalized_enrichment"),
        (SuperconductorCandidatePoolRankingTask, 32, 5, "global_ndcg"),
        (HopperControllerCandidatePoolRankingTask, 32, 5, "global_ndcg"),
        (UTRMRLCompositionalRankingTask, 128, 16, "normalized_enrichment"),
        (GFPCandidatePoolRankingTask, 128, 16, "normalized_enrichment"),
        (DrugMatrixCandidatePoolRankingTask, 16, 5, "global_ndcg"),
    ],
)
def test_design_bench_task_default_profiles(
    task_type,
    submission_size: int,
    summary_size: int,
    primary_metric: str,
) -> None:
    parameters = signature(task_type.__init__).parameters

    assert parameters["submission_size"].default == submission_size
    assert task_type.default_summary_size == summary_size
    assert task_type.default_primary_metric == primary_metric
