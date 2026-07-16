# Objective API

> **Status:** Experimental. The contract is intentionally small and will grow
> only when concrete scientific benchmarks require it.

An `Objective` is a trusted, Dataset-bound mapping from a valid candidate to one
or more target values. It provides common candidate validation and ordered batch
semantics while leaving scientific evaluation to a concrete implementation.

## Using an Objective

Concrete suites provide Objective implementations. TFBind8 uses an exact lookup:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8Dataset,
    TFBind8ExactObjective,
)

dataset = TFBind8Dataset.from_hub(revision="full-commit-sha")
objective = TFBind8ExactObjective(dataset)

single = objective.evaluate({"sequence": "AACCGGTT"})
batch = objective.evaluate_batch(
    [
        {"sequence": "AACCGGTT"},
        {"sequence": "TTTTTTTT"},
        {"sequence": "AACCGGTT"},
    ]
)
```

`evaluate()` returns one `dict[str, Any]`. `evaluate_batch()` materializes the
candidate iterable and returns a tuple of dictionaries in input order. Repeated
candidates are preserved rather than deduplicated.

## Public Contract

Every concrete Objective defines:

| Member | Contract |
|---|---|
| `objective_id` | Non-empty stable identifier for the evaluation behavior |
| `dataset` | Dataset instance bound at construction |
| `output_fields` | Non-empty tuple of unique Dataset target field names |
| `evaluate(candidate)` | Validate and evaluate one candidate |
| `evaluate_batch(candidates)` | Validate and evaluate an ordered candidate batch |

Construction rejects an empty `objective_id`, duplicate or empty
`output_fields`, and output fields not declared in `dataset.schema.targets`.

Before scientific evaluation, `evaluate_batch()` calls
`dataset.validate_inputs()` for every candidate. If a candidate is invalid, it
raises `ObjectiveInputError` with `candidate_index` and the corresponding
`ValidationReport`. The concrete implementation is not called for a partially
invalid batch.

After evaluation, the base class verifies that:

- the implementation returned exactly one output per candidate;
- every output is a mapping;
- every output has exactly the declared fields;
- returned dictionaries follow `output_fields` order.

The base class checks output structure, not target values. A concrete Objective
is responsible for producing scientifically valid target values and may use
`dataset.validate_targets()` when appropriate.

## Implementing an Objective

Subclass `Objective`, declare a stable ID and output fields, and implement the
protected batch hook:

```python
from collections.abc import Iterable

from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput


class SequenceLengthObjective(Objective):
    objective_id = "example/sequence-length-v1"

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("score",)

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        for candidate in candidates:
            yield {"score": float(len(candidate["sequence"]))}
```

The bound Dataset must declare `score` as a target. `_evaluate_batch()` receives
a fully materialized tuple whose candidates have passed Dataset input
validation. It must yield one mapping per candidate without reordering or
deduplicating the batch.

Use a Dataset-specific constructor when an Objective requires a particular
dataset ID or split. Fail such compatibility checks during construction rather
than after an expensive evaluation begins.

## Exceptions

| Exception | Meaning |
|---|---|
| `ObjectiveError` | Base class for Objective failures, including an empty Objective ID |
| `ObjectiveInputError` | A candidate failed Dataset input validation; exposes `candidate_index` and `report` |
| `ObjectiveLookupError` | A valid candidate is absent from an exact lookup artifact |
| `ObjectiveOutputError` | Declared output fields, output count, or output mappings violate the contract |

## Boundary

An Objective does not decide which observations an agent sees, enforce query
budgets, manage iterative feedback, parse submissions, or calculate benchmark
metrics. Agent visibility belongs to a [Protocol](protocol.md), submission and
metric semantics belong to a [Task](task.md), and interaction policy belongs to
an external harness.

See [TFBind8](../suites/design-bench/tfbind8.md) for the first exact black-box
Objective.
