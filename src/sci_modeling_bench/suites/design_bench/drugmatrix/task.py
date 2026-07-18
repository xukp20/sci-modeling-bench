"""Candidate-pool ranking Task for DrugMatrix treatment conditions."""

from __future__ import annotations

from collections.abc import Hashable

from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import (
    CandidatePoolRankingTask,
    CandidateValidationReport,
    CandidateViolation,
)
from sci_modeling_bench.suites.design_bench.drugmatrix.dataset import (
    DEFAULT_DRUGMATRIX_REPO_ID,
    DEFAULT_DRUGMATRIX_REVISION,
    DRUGMATRIX_CONFIG_NAME,
    DrugMatrixDataset,
)
from sci_modeling_bench.suites.design_bench.drugmatrix.objective import (
    DrugMatrixEndpointObjective,
)
from sci_modeling_bench.suites.design_bench.drugmatrix.protocol import (
    DrugMatrixAgentInput,
    DrugMatrixMeasuredPoolProtocol,
)


class DrugMatrixCandidatePoolRankingTask(
    CandidatePoolRankingTask[DrugMatrixAgentInput]
):
    """Select and rank control-deviating measured treatment conditions."""

    task_id = "design-bench/drugmatrix-candidate-pool-ranking-v1"
    default_primary_metric = "global_ndcg"

    def __init__(
        self,
        dataset: DrugMatrixDataset,
        *,
        endpoint: str,
        protocol: DrugMatrixMeasuredPoolProtocol | None = None,
        objective: DrugMatrixEndpointObjective | None = None,
        submission_size: int = 64,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or DrugMatrixMeasuredPoolProtocol()
        selected_objective = objective or DrugMatrixEndpointObjective(
            dataset, endpoint=endpoint
        )
        if selected_objective.endpoint != endpoint:
            raise TaskError("objective endpoint must match the Task endpoint")
        candidate_pool = selected_protocol.candidate_pool(
            dataset, split=selected_objective.split
        )
        score_field = f"{endpoint}_control_deviation"
        self._endpoint = endpoint
        self.task_id = (
            f"design-bench/drugmatrix-{endpoint}-candidate-pool-ranking-v1"
        )
        self._smiles_by_condition_id = {
            str(identity): str(smiles)
            for identity, smiles in zip(
                candidate_pool["condition_id"],
                candidate_pool["canonical_smiles"],
                strict=True,
            )
        }
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            candidate_pool=(
                {"condition_id": identity}
                for identity in candidate_pool["condition_id"]
            ),
            score_field="control_deviation",
            reference_scores=candidate_pool[score_field],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        return str(candidate["condition_id"])

    def _validate_candidate(
        self,
        candidate: Candidate,
        report: CandidateValidationReport,
    ) -> CandidateValidationReport:
        identity = candidate.get("condition_id")
        if not isinstance(identity, str) or not identity:
            return report.with_violation(
                CandidateViolation(
                    code="invalid_condition_id",
                    field="condition_id",
                    message="condition_id must be a non-empty string",
                )
            )
        return super()._validate_candidate(candidate, report)

    def _candidate_for_dataset_validation(self, candidate: Candidate) -> Candidate:
        identity = str(candidate.get("condition_id"))
        return {"canonical_smiles": self._smiles_by_condition_id.get(identity)}

    @classmethod
    def from_hub(
        cls,
        *,
        endpoint: str,
        repo_id: str = DEFAULT_DRUGMATRIX_REPO_ID,
        config_name: str | None = DRUGMATRIX_CONFIG_NAME,
        revision: str | None = DEFAULT_DRUGMATRIX_REVISION,
        token: str | None = None,
        submission_size: int = 64,
        primary_metric: str | None = None,
    ) -> DrugMatrixCandidatePoolRankingTask:
        dataset = DrugMatrixDataset.from_hub(
            repo_id=repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
        )
        return cls(
            dataset,
            endpoint=endpoint,
            submission_size=submission_size,
            primary_metric=primary_metric,
        )
