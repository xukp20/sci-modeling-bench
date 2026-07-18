# Protocol API

> **Status:** Experimental. Protocol outputs use a uniform disclosure manifest,
> while each concrete Protocol retains its domain-specific data type.

A `Protocol` constructs the information made visible to an Agent from a
complete trusted `Dataset`. It is the disclosure boundary between canonical
benchmark state and Agent input.

## AgentInputBundle

Every `Protocol.build_input()` returns an `AgentInputBundle`:

```python
bundle = protocol.build_input(dataset)

agent_data = bundle.data
manifest = bundle.manifest
```

`bundle.data` belongs to the concrete Protocol. It can be a Hugging Face
`Dataset` or a typed object containing multiple tables and scientific constants.
`bundle.manifest` always has the same public `AgentInputManifest` schema.

The manifest describes exactly the disclosed views, rather than copying the
canonical Dataset manifest. It contains:

- public Dataset identity, version, license, source, citation, repository,
  resolved revision, config, and selected split;
- the stable `protocol_id` and, for `Task.build_input()`, the concrete `task_id`;
- every visible table name, disclosure role (`observations`, `candidates`, or
  `auxiliary`), description, row count, and column in physical order;
- each visible field's semantic role, description, physical type, optional
  unit, required flag, constraints, and canonical source field when applicable;
- public split attributes and Protocol-disclosed scientific constants such as
  element order, policy layout, or a reference sequence.

Hidden canonical columns are not copied into the manifest. A Protocol that
derives or renames a visible column must explicitly declare its semantics.
Building the input fails if any visible table column lacks a canonical
`FieldSpec` or a Protocol-specific `AgentInputField` override.

```python
print(manifest.model_dump_json(indent=2))
```

An external harness can materialize this JSON next to serialized tables. The
package itself does not prescribe a workspace path or physical file format.

## Using a Protocol

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
)

dataset = TFBind8Dataset.from_hub(revision="full-commit-sha")
bundle = TFBind8DesignBenchProtocol().build_input(dataset)

observations = bundle.data
assert bundle.manifest.views[0].name == "observations"
```

Calling the corresponding Task binds the same manifest to a Task identity:

```python
bundle = task.build_input()
print(bundle.manifest.task_id)
```

## Public Contract

`Protocol` is generic in its data type:

```python
def build_input(
    self,
    dataset: Dataset,
    *,
    split: str | None = None,
) -> AgentInputBundle[ProtocolDataT]:
    ...
```

A concrete Protocol declares a stable `protocol_id`, validates its
configuration and Dataset compatibility, constructs independently owned or
immutable visible data, and pairs it with a disclosure-scoped manifest. The
optional `split` selects a published Dataset split; it does not imply an
Agent-visible train/test partition.

## Implementing a Protocol

The public helpers reuse canonical field semantics where possible:

```python
from datasets import Dataset as HFDataset

from sci_modeling_bench import AgentInputBundle, Dataset, Protocol
from sci_modeling_bench.protocol import agent_input_manifest, agent_table_view


class InputsOnlyProtocol(Protocol[HFDataset]):
    protocol_id = "example/inputs-only-v1"

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> AgentInputBundle[HFDataset]:
        selected_split = split or dataset.default_split
        observations = dataset.load(selected_split)
        input_fields = [field.name for field in dataset.schema.inputs]
        visible = observations.select_columns(input_fields)
        view = agent_table_view(
            dataset,
            visible,
            name="observations",
            role="observations",
            description="Agent-visible input fields.",
        )
        return AgentInputBundle(
            data=visible,
            manifest=agent_input_manifest(
                dataset,
                protocol_id=self.protocol_id,
                split=selected_split,
                views=(view,),
            ),
        )
```

Use `agent_input_field()` overrides for renamed, flattened, or derived columns.
Use `AgentInputContext` for constants whose interpretation applies across a
whole view, such as a vector's element order. Protocol configuration should
fail before returning partial data or an incomplete manifest.

## Canonical and Agent Manifests

The repository `DatasetManifest` describes the complete canonical Dataset.
`AgentInputManifest` describes only one Protocol disclosure. They are different
objects because Protocols may filter rows and columns, expand nested records,
construct several views, or intentionally hide partition annotations.

Forwarding the canonical manifest unchanged could advertise hidden target or
context fields that are absent from Agent data. Harnesses should serialize the
`AgentInputManifest`, not expose trusted repository manifests or Dataset
handles.

## Isolation Boundary

An `AgentInputBundle` defines intended visibility but is not a process-security
boundary. The external harness must isolate the complete Dataset, Objectives,
credentials, caches, repository checkout, and network. It also owns query
budgets, feedback timing, and the subset of trusted evaluation fields returned
to the Agent.

Dataset splits preserve canonical observation identity. Protocol outputs are
Task-specific views and should not be published as duplicate canonical splits.
