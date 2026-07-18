# Objective API

> **Status:** Experimental. The contract is intentionally small and will grow
> only when concrete scientific benchmarks require it.

An `Objective` is a trusted, Dataset-bound mapping from a valid candidate to one
or more semantic output values. Outputs may be stored Dataset targets, simulator
results, or values derived from multiple observations. The base class provides
common candidate validation and ordered batch semantics while leaving
scientific evaluation to a concrete implementation.

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
| `output_fields` | Non-empty tuple of unique semantic output field names |
| `evaluate(candidate)` | Validate and evaluate one candidate |
| `evaluate_batch(candidates)` | Validate and evaluate an ordered candidate batch |

Construction rejects an empty `objective_id` and duplicate or empty
`output_fields`. An output does not have to be a physical Dataset target. This
allows an Objective to compute, for example, one candidate-level posterior
score from several raw replicate observations without publishing that score as
offline data.

Before scientific evaluation, `evaluate_batch()` validates the Dataset-schema
view returned by `_candidate_for_dataset_validation()`. The default hook returns
the candidate unchanged and therefore calls `dataset.validate_inputs()` on the
public candidate mapping. A lookup Objective may override the hook when its
public candidate is a stable handle for a Dataset input rather than the input
itself. If a candidate is invalid, it
raises `ObjectiveInputError` with `candidate_index` and the corresponding
`ValidationReport`. The concrete implementation is not called for a partially
invalid batch.

After evaluation, the base class verifies that:

- the implementation returned exactly one output per candidate;
- every output is a mapping;
- every output has exactly the declared fields;
- returned dictionaries follow `output_fields` order.

The base class checks output structure, not output values. A concrete Objective
is responsible for producing scientifically valid values and may use
`dataset.validate_targets()` when the output is a persisted Dataset target.

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

`_evaluate_batch()` receives a fully materialized tuple whose candidates have
passed Dataset input validation. It must yield one mapping per candidate
without reordering or deduplicating the batch. A concrete Objective should
document whether each output is observed, analytic, simulated, learned, or
derived from several Dataset fields.

Override `_candidate_for_dataset_validation()` only to translate a public
candidate handle into its Dataset input view. The hook must not silently repair
an invalid scientific input or expose hidden target values.

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

See [TFBind8](../suites/design-bench/tfbind8.md) for an exact persisted-target
lookup and [TFBind10 Pho4](../suites/design-bench/tfbind10-pho4.md) for a score
derived from raw replicate count observations.
