# Task API

`Task` binds a trusted `Dataset` to the `Protocol` that constructs Agent-visible
input and defines how one complete submission is evaluated. The base contract
does not assume that submissions contain candidates or that evaluation uses an
Objective.

## Design Boundary

A Task owns the stable relationship between its Dataset, Agent-visible
Protocol, accepted submission type, and evaluation metrics. It does not execute
an Agent, isolate a process, count interactive queries, manage memory, or
decide which trusted evaluation fields are revealed during a run. Those
policies belong to an external harness.

Objective is intentionally absent from the base Task. Prediction Tasks can
compare submitted predictions with hidden Dataset targets directly. Tasks that
need a trusted candidate-to-target mapping inherit from
`ObjectiveBackedTask`, which requires the Objective and Task to share the exact
same Dataset instance.

```python
class Task(ABC, Generic[AgentInputT, SubmissionT, EvaluationT]):
    task_id: str
    dataset: Dataset
    protocol: Protocol[AgentInputT]

    def build_input(self) -> AgentInputBundle[AgentInputT]: ...
    def evaluate(self, submission: SubmissionT) -> EvaluationT: ...
```

`build_input()` binds the Protocol's disclosure manifest to the concrete
`task_id`. Consumers read domain-specific tables from `bundle.data` and the
uniform machine-readable description from `bundle.manifest`. Submission and
metric semantics remain Task documentation rather than being inferred from the
input tables.

## Submission Evaluation

Every Task returns `SubmissionEvaluation` or a more specific subclass:

| Field | Meaning |
|---|---|
| `task_id` | Stable identifier for the concrete Task definition |
| `submission_validation` | Findings about the complete submission container or shape |
| `metrics` | Named metrics produced for an eligible submission |
| `metric_directions` | Maximize/minimize direction for every supported metric |
| `primary_metric` | Metric selected as the default Task score |
| `metric_direction` | Direction of the primary metric |
| `submission_valid` | Whether the top-level submission contract passed |
| `score` | `metrics[primary_metric]`, or `None` when no official metrics were produced |

Submission validation is distinct from candidate validation. A wrong number of
outputs is a submission problem; one malformed DNA sequence or an ID outside a
candidate pool is a candidate problem.

## Black-Box Optimization

`BlackBoxOptimizationTask` accepts an ordered list of candidates.
`submission_size` defaults to 128 and can be configured when constructing the
Task. Position 1 represents the candidate the Agent predicts to be best.

Every candidate must be legal, scorable, and canonical-unique. If any slot is
invalid or repeated, the result retains candidate-level diagnostics but does
not produce comparable aggregate metrics. A wrong-size or malformed container
is reported through `SubmissionValidationReport` without invoking the
Objective.

Eligible submissions receive the complete common metric set documented in
[Candidate submission metrics](../metrics/candidate-submission-metrics.md).
The Task's `primary_metric` can also be selected at construction time:

```python
task = TFBind8BlackBoxOptimizationTask.from_hub(
    submission_size=64,
    summary_size=16,
    primary_metric="global_ndcg",
)
```

The result adds:

| Field | Meaning |
|---|---|
| `expected_candidates` | Configured submission size |
| `submitted_candidates` | Materialized candidate count |
| `valid_candidates` / `invalid_candidates` | Candidate-level validation counts |
| `evaluation_eligible` | Whether official aggregate metrics were produced |
| `score_field` | Objective output used as the scientific score |
| `summary_size` | Configured `K` used by `*_k_*` metrics; concrete Tasks choose a default profile |
| `reference_scope` / `reference_size` | Identity of the full domain or evaluation pool used by relative metrics |
| `best_candidate_index` | Position of the best legal submitted candidate |
| `best_objective_output` | Complete Objective output for that candidate |
| `candidates` | Ordered per-candidate validation and Objective results |

```python
evaluation = task.evaluate(submission)

evaluation.score
evaluation.metrics["best_score"]
evaluation.metrics["best_k_mean"]
evaluation.metrics["global_ndcg"]
evaluation.metric_directions["best_regret"]
evaluation.candidates[0].validation
```

TFBind8 and CellDAG-NAS use `best_k_mean` with a `full_domain` reference.
TFBind10 Pho4 uses `normalized_enrichment` with its exhaustive DNA 10-mer
`full_domain` reference. Their suite guides define the corresponding candidate
identities, visible inputs, and scientific score fields.

## Candidate-Pool Ranking

`CandidatePoolRankingTask` is the parallel contract for a finite, explicitly
Agent-visible candidate pool. It reuses the candidate validation, Objective,
reference, and common metric behavior above, but interprets
`submission_size` as the scored prefix size `N`.

An Agent submits candidate content in descending predicted quality. At least
`N` candidates are required. Only the first `N` are validated, deduplicated,
checked for pool membership, and sent to the Objective; a longer suffix is
accepted but ignored. The evaluation adds `candidate_pool_size`,
`evaluated_candidates`, and `ignored_candidates`.

Superconductor, Hopper Controller, UTR MRL, GFP, and the six DrugMatrix
endpoint Tasks use this contract. Their Objectives are trusted only over
frozen measured or reproducibly simulated pools, not as evaluators for
arbitrary generated candidates.

## Trust Boundary

Task evaluation returns complete trusted diagnostics. An external harness
decides whether an Agent receives only the primary score, a selected metric
vector, validation counts, or full candidate outputs. Query budgets, feedback
frequency, hidden-data isolation, and snapshots remain outside this package.
