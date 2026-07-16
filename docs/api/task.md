# Task API

`Task` binds a trusted `Dataset` to the `Protocol` that constructs Agent-visible
input and defines how one complete submission is evaluated. The base contract
does not assume that submissions contain candidates or that evaluation uses an
Objective.

## Design Boundary

A Task is a benchmark definition, not an Agent runner. It owns the stable
relationship between:

- the Dataset that supplies trusted observations and validation;
- the Protocol that derives Agent-visible input;
- the accepted submission type;
- the evaluation result and primary metric.

The Task does not execute an Agent, isolate a process, count interactive
queries, manage memory, or decide how much evaluation detail is returned during
a run. Those policies belong to an external harness. This separation allows the
same Task to be used by different Agent workflows without changing its scoring
semantics.

Objective is intentionally not part of the base Task. Some Tasks need a trusted
candidate-to-target function, while prediction or model-submission Tasks can
compare a submission with trusted Dataset targets directly. Requiring every
Task to expose an Objective would incorrectly model those problem types as
black-box optimization.

## Base Contract

```python
class Task(ABC, Generic[AgentInputT, SubmissionT, EvaluationT]):
    task_id: str
    dataset: Dataset
    protocol: Protocol[AgentInputT]

    def build_input(self) -> AgentInputT: ...
    def evaluate(self, submission: SubmissionT) -> EvaluationT: ...
```

Prediction Tasks can accept predicted targets or an implementation with a
`predict` interface and compare its output with trusted Dataset targets. Tasks
that require a candidate-to-target mapping can instead inherit from
`ObjectiveBackedTask`, which adds a Dataset-bound `Objective` without placing
that assumption in the base class.

`Task.build_input()` always delegates to the bound Protocol. Task subclasses
implement `evaluate()` because the accepted submission and metric are
problem-specific. `ObjectiveBackedTask` additionally checks that its Objective
is bound to the exact same Dataset instance as the Task, avoiding evaluation
against a different revision or config.

## Submission Evaluation

Every Task returns a `SubmissionEvaluation` or a more specific subclass. Its
`SubmissionValidationReport` describes only the top-level submission contract,
such as an invalid container, wrong number of outputs, or incompatible output
shape. It does not represent Dataset-level candidate validity.

```python
evaluation.submission_valid
evaluation.metrics
evaluation.primary_metric
evaluation.metric_direction
evaluation.score
```

`score` is the value named by `primary_metric`. The explicit direction allows
both maximized scores and minimized losses.

| Field | Meaning |
|---|---|
| `task_id` | Stable identifier for the concrete Task definition |
| `submission_validation` | Findings about the complete submission container or shape |
| `metrics` | Named benchmark metrics produced by the Task |
| `primary_metric` | Metric used as the default Task score |
| `metric_direction` | Whether higher or lower primary-metric values are better |
| `submission_valid` | Computed from submission-level error violations |
| `score` | Value of `metrics[primary_metric]`, when present |

`SubmissionValidationReport` is deliberately distinct from Dataset validation.
For example, a list containing the wrong number of predictions is a submission
problem; an individual DNA sequence containing an invalid symbol is a
candidate problem. Keeping them separate prevents one malformed candidate from
being confused with a malformed submission container.

## Design-Bench Black-Box Optimization

`DesignBenchBlackBoxOptimizationTask` is an `ObjectiveBackedTask` that accepts
exactly 128 candidates and uses the maximum candidate score as its primary
metric. It returns `BlackBoxOptimizationEvaluation`.

Each nested `CandidateEvaluation` has a separate
`CandidateValidationReport`. Candidate violations are translated from the
bound Dataset input contract and are never copied into the submission-level
report. Invalid candidates occupy submission slots, receive no fabricated
Objective output, and are excluded from the maximum. An all-invalid submission
receives the normalized floor score `0.0`.

```python
evaluation.valid_candidates
evaluation.invalid_candidates
evaluation.best_candidate_index
evaluation.best_objective_output
evaluation.candidates[0].validation
```

An incorrect candidate count is a submission-level failure and receives the
same floor score without invoking the Objective.

The concrete result adds these fields:

| Field | Meaning |
|---|---|
| `expected_candidates` | Required candidate count, currently 128 |
| `submitted_candidates` | Materialized candidate count |
| `valid_candidates` / `invalid_candidates` | Candidate-level validation counts |
| `score_field` | Objective output used for candidate ranking |
| `aggregation` | Candidate aggregation, currently `max` |
| `best_candidate_index` | Position of the best legal submitted candidate |
| `best_objective_output` | Complete Objective output for that candidate |
| `candidates` | Ordered per-candidate validation and Objective results |

Candidate order and duplicates are preserved. The result contains trusted
diagnostic detail; it does not imply that every field should be revealed to an
Agent during iterative optimization.

## TFBind8 Task

The default TFBind8 Task composes the canonical Dataset, bottom-50% Protocol,
and exact lookup Objective:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

task = TFBind8BlackBoxOptimizationTask.from_hub(revision="v1.0.0")
offline_data = task.build_input()

submission = [{"sequence": "AACCGGTT"} for _ in range(128)]
evaluation = task.evaluate(submission)

print(evaluation.submission_valid)
print(evaluation.score)
print(evaluation.best_candidate_index)
```

See the [TFBind8 suite guide](../suites/design-bench/tfbind8.md) for its data,
validation, exact scoring, and Design-Bench parity.

## Trust Boundary

The Task returns the complete trusted evaluation. An external harness remains
responsible for deciding which fields are shown to an Agent, enforcing query
budgets, and isolating hidden data and evaluator internals.
