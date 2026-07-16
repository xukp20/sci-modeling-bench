# Task API

`Task` binds a trusted `Dataset` to the `Protocol` that constructs Agent-visible
input and defines how one complete submission is evaluated. The base contract
does not assume that submissions contain candidates or that evaluation uses an
Objective.

```python
class Task(ABC, Generic[AgentInputT, SubmissionT, EvaluationT]):
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

The Task returns the complete trusted evaluation. An external harness remains
responsible for deciding which fields are shown to an Agent, enforcing query
budgets, and isolating hidden data and evaluator internals.
