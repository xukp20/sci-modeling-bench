"""Default CellDAG-NAS black-box optimization Task."""

from __future__ import annotations

from datasets import Dataset as HFDataset

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import (
    BlackBoxOptimizationTask,
    CandidateValidationReport,
    CandidateViolation,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas.dataset import (
    CELL_DAG_NAS_CONFIG_NAME,
    DEFAULT_CELL_DAG_NAS_REPO_ID,
    CellDAGNASDataset,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas.objective import (
    CellDAGNASExactObjective,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas.protocol import (
    CellDAGNASDesignBenchProtocol,
)


class CellDAGNASBlackBoxOptimizationTask(
    BlackBoxOptimizationTask[HFDataset]
):
    """Select an ordered batch of canonical-unique NASBench-101 cells."""

    task_id = "design-bench/cell-dag-nas-black-box-optimization-v1"
    default_primary_metric = "best_k_mean"

    def __init__(
        self,
        dataset: CellDAGNASDataset,
        *,
        protocol: CellDAGNASDesignBenchProtocol | None = None,
        objective: CellDAGNASExactObjective | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> None:
        selected_objective = objective or CellDAGNASExactObjective(dataset)
        observations = dataset.load(selected_objective.split)
        super().__init__(
            dataset,
            protocol or CellDAGNASDesignBenchProtocol(),
            selected_objective,
            score_field="mean_test_accuracy",
            reference_scores=observations["mean_test_accuracy"],
            reference_scope="full_domain",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    @property
    def objective(self) -> CellDAGNASExactObjective:
        return super().objective  # type: ignore[return-value]

    def _validate_candidate(
        self,
        candidate: Candidate,
        report: CandidateValidationReport,
    ) -> CandidateValidationReport:
        if not report.valid:
            return report
        canonical_hash = self.objective.canonical_hash(candidate)
        if self.objective.contains_hash(canonical_hash):
            return report
        return report.with_violation(
            CandidateViolation(
                code="out_of_table_graph",
                field="architecture",
                message="legal graph is absent from the frozen NASBench-101 table",
            )
        )

    def _candidate_identity(self, candidate: Candidate) -> str:
        return self.objective.canonical_hash(candidate)

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_CELL_DAG_NAS_REPO_ID,
        config_name: str | None = CELL_DAG_NAS_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> CellDAGNASBlackBoxOptimizationTask:
        dataset = CellDAGNASDataset.from_hub(
            repo_id=repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
        )
        return cls(
            dataset,
            submission_size=submission_size,
            primary_metric=primary_metric,
        )
