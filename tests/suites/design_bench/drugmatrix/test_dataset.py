from __future__ import annotations

from sci_modeling_bench.suites.design_bench.drugmatrix import (
    DRUGMATRIX_ENDPOINTS,
    DrugMatrixCandidatePoolRankingTask,
    DrugMatrixValidator,
)


def test_validator_reports_noncanonical_tiny_fixture(
    tiny_drugmatrix_dataset,
) -> None:
    report = DrugMatrixValidator().validate_dataset(tiny_drugmatrix_dataset.load())

    codes = {item.code for item in report.violations}
    assert "drugmatrix_row_count" in codes
    assert "drugmatrix_treatment_counts" in codes


def test_published_dataset_and_all_endpoint_tasks(
    published_drugmatrix_dataset,
) -> None:
    data = published_drugmatrix_dataset.load()
    report = published_drugmatrix_dataset.validate_dataset(data)

    assert len(data) == 10_605
    assert report.valid
    assert published_drugmatrix_dataset.resolved_revision == (
        "d8b9ea3c78ed33edf0869a427940a0651eb49f52"
    )
    for endpoint in DRUGMATRIX_ENDPOINTS:
        task = DrugMatrixCandidatePoolRankingTask(
            published_drugmatrix_dataset,
            endpoint=endpoint,
            submission_size=64,
        )
        candidates = task.build_input().data.candidates
        evaluation = task.evaluate(
            [
                {"condition_id": identity}
                for identity in candidates["condition_id"][:64]
            ]
        )
        assert evaluation.evaluation_eligible
        assert evaluation.candidate_pool_size == 390
