# Protocol API

> **Status:** Experimental. The base class defines only the boundary needed by
> the first concrete benchmark.

A `Protocol` constructs the information made visible to an agent from a
complete `Dataset`. It is the data-disclosure boundary between trusted benchmark
state and agent input.

## Using a Protocol

Concrete suites define the selection or transformation they apply:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
)

dataset = TFBind8Dataset.from_hub(revision="full-commit-sha")
protocol = TFBind8DesignBenchProtocol()
agent_input = protocol.build_input(dataset)
```

The output type belongs to the concrete Protocol. The TFBind8 implementation
returns a standard Hugging Face `Dataset`; another Protocol can return any typed
Python object appropriate for its benchmark.

## Public Contract

`Protocol` is generic in its output type and defines one abstract method:

```python
def build_input(
    self,
    dataset: Dataset,
    *,
    split: str | None = None,
) -> ProtocolOutputT:
    ...
```

A concrete Protocol should declare a stable `protocol_id`, validate its own
configuration and Dataset compatibility, and implement `build_input()` without
mutating the Dataset. The base class does not enforce an output format or
automatically hide columns; those are concrete Protocol responsibilities.

The optional `split` selects a published Dataset split when the implementation
supports it. It does not create a new split or imply train/test semantics.

## Implementing a Protocol

This example exposes only declared input columns from one split:

```python
from datasets import Dataset as HFDataset

from sci_modeling_bench import Dataset, Protocol


class InputsOnlyProtocol(Protocol[HFDataset]):
    protocol_id = "example/inputs-only-v1"

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        observations = dataset.load(split)
        input_fields = [field.name for field in dataset.schema.inputs]
        return observations.select_columns(input_fields)
```

A concrete Protocol may use Hugging Face `select`, `filter`, or `map`, or build
a different immutable or independently owned output. It should make these
behaviors explicit:

- required Dataset ID, schema fields, and supported splits;
- fields visible to the agent;
- selection thresholds and whether boundaries are inclusive;
- ordering, tie handling, randomness, and seed behavior;
- output type and any copies or materialization performed;
- failures reported as `ProtocolError`.

Protocol configuration should fail before returning partial agent input.

## Protocols and Black-Box Isolation

`build_input()` constructs the intended visible object but does not isolate the
agent process. The external harness must ensure the agent cannot access the
complete Dataset, hidden target columns, Objective internals, credentials, or
cached repository artifacts.

The harness remains responsible for query budgets, feedback timing, state, and
deciding which Task evaluation fields are exposed to the Agent. Submission and
metric semantics belong to a [Task](task.md), not Protocol configuration.

## Protocols Are Not Dataset Splits

Dataset splits preserve published observation identity and shared scientific
metadata. Protocol output represents a benchmark-specific view. Keeping these
separate avoids publishing a second copy of canonical data for every selection
policy and makes disclosure logic reviewable in code.

See [TFBind8](../suites/design-bench/tfbind8.md) for the first implementation,
which deterministically exposes the bottom target percentile of the canonical
landscape as offline optimization data.
