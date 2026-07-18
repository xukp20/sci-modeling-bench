# Dataset API

> **Status:** Experimental. Pin the package version and dataset revision in
> reproducible work.

The `Dataset` layer represents published scientific observations together with
their identity, provenance, semantic field roles, validity rules, split
metadata, and optional domain knowledge. It intentionally does not select
task-specific agent input or evaluate candidate designs.

## Loading a Dataset

Load a repository config directly:

```python
from sci_modeling_bench import Dataset

dataset = Dataset.from_hub(
    "sci-modeling-bench/design-bench",
    config_name="tfbind8",
    revision="full-commit-sha",
)
```

`Dataset.from_hub()` has this signature:

```text
Dataset.from_hub(
    repo_id: str,
    config_name: str | None = None,
    revision: str | None = None,
    *,
    token: str | None = None,
    validator: DatasetValidator | None = None,
) -> Dataset
```

When `config_name` is omitted, the collection manifest's `default_config` is
used. The requested revision, including the repository default when `None`, is
resolved once to a full commit SHA. All manifests, data, and knowledge resources
are read from that SHA with remote code disabled.

For a reusable or replaceable source reference, use `HubDatasetSource`:

```python
from sci_modeling_bench import Dataset, HubDatasetSource

source = HubDatasetSource(
    repo_id="internal-mirror/design-bench",
    config_name="tfbind8",
    revision="full-commit-sha",
)
dataset = Dataset.from_source(source)
```

`Dataset.from_source(source, *, token=None, validator=None)` applies the same
resolution and loading behavior. `HubDatasetSource` stores only repository,
config, and revision identity. Authentication comes from the local Hugging Face
configuration or the explicit `token` argument.

Dataset-specific classes may provide a default source. For example,
`TFBind8Dataset.from_hub()` fills in the Design-Bench repository and config
while still accepting a mirror or pinned revision.

## Dataset Properties

| Property | Type | Meaning |
|---|---|---|
| `repo_id` | `str` | Hugging Face Dataset repository used by this instance |
| `resolved_revision` | `str` | Full commit SHA used for every repository access |
| `config_name` | `str` | Selected repository config |
| `metadata` | `DatasetMetadata` | Dataset ID, version, description, license, sources, and citations |
| `schema` | `DatasetSchema` | Input, target, and context field declarations |
| `default_split` | `str` | Manifest-selected split name |
| `splits` | `tuple[DatasetSplit, ...]` | Immutable split metadata |
| `available_splits` | `tuple[str, ...]` | Declared split names in manifest order |
| `knowledge` | `Knowledge` | Read-only mapping of lazy text resources |
| `features` | Hugging Face `Features` | Physical features for the loaded default split |

Metadata, schema, field, split, constraint, violation, and validation-report
objects are immutable Pydantic models. `HubDatasetSource` and knowledge resource
metadata are immutable dataclasses.

## Splits and Data Loading

```python
split_metadata = dataset.split()  # Default split
named_metadata = dataset.split("six6_ref_r1")

observations = dataset.load()
stream = dataset.load("six6_ref_r1", streaming=True)
```

`split(name=None)` returns metadata for a declared split and raises `ValueError`
for an undeclared name. `load(split=None, *, streaming=False)` returns a standard
Hugging Face `Dataset` or, for streaming loads, an `IterableDataset`.

Non-streaming data are cached by split on the `Dataset` instance. When Hugging
Face feature metadata is available, loading checks that every manifest-declared
field exists. When a split declares `num_rows`, non-streaming loading also
checks the row count. Streaming loads are not cached and cannot perform the
row-count check.

A published split is an observation group with one schema and shared metadata.
It is not an agent-visible train/test view; constructing that view is a
[Protocol](protocol.md) responsibility.

## Semantic Schema

`dataset.schema` contains ordered `inputs`, `targets`, and `context` tuples of
`FieldSpec` objects. Field names must be unique across all roles. Each field has
a name, description, optional unit, `required` flag, and zero or more common
constraints.

| Constraint kind | Model | Behavior |
|---|---|---|
| `range` | `NumericRangeConstraint` | Minimum and maximum numeric bounds; each bound can be inclusive or exclusive |
| `allowed_values` | `AllowedValuesConstraint` | Finite allowed set for scalar values or sequence leaves |
| `alphabet` | `AlphabetConstraint` | Allowed single-character symbols for a string |
| `length` | `LengthConstraint` | Minimum and maximum length for strings or sized sequences |
| `finite` | `FiniteConstraint` | Reject NaN and infinite numeric leaves |

Example field declarations in a config manifest:

```json
{
  "inputs": [
    {
      "name": "sequence",
      "description": "DNA sequence of exactly eight nucleotides.",
      "constraints": [
        {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
        {"kind": "length", "minimum": 8, "maximum": 8}
      ]
    }
  ],
  "targets": [
    {
      "name": "normalized_e_score",
      "description": "Condition-level normalized E-score.",
      "constraints": [
        {"kind": "finite"},
        {"kind": "range", "minimum": 0.0, "maximum": 1.0}
      ]
    }
  ],
  "context": []
}
```

Hugging Face `Features` remain the authority for physical dtype and shape.
Field specifications add semantic roles and scientific constraints.

This canonical schema may include fields that a task-specific Protocol hides.
Do not forward it unchanged to an Agent. `Protocol.build_input()` returns a
separate `AgentInputManifest` filtered to the actual visible views and fields;
see the [Protocol API](protocol.md).

## Validation

```python
input_report = dataset.validate_inputs(
    {"sequence": "AACCGGTT"},
    context=None,
)
target_report = dataset.validate_targets(
    {"normalized_e_score": 0.5},
    inputs={"sequence": "AACCGGTT"},
    context=None,
)
row_report = dataset.validate_observation(observation)
full_report = dataset.validate_dataset()
```

The validation methods return `ValidationReport`; expected data errors are not
raised as exceptions. A report contains immutable `Violation` objects with a
machine-readable `code`, message, optional field and row index, and `error` or
`warning` severity. `report.valid` is false when at least one error is present.

- `validate_inputs()` checks the input role, context role, physical features,
  common constraints, and custom input hooks. Unknown role fields are rejected.
- `validate_targets()` checks the target and context roles, then passes optional
  inputs and context to custom target checks. It does not separately validate
  the supplied `inputs` mapping.
- `validate_observation()` checks all declared fields in one row and permits
  additional published columns.
- `validate_dataset(data=None)` validates every row and then runs the custom
  dataset-level hook. It can be expensive for large or streaming data.

Validation reports findings without clipping, repairing, or mutating values.

For scientific checks that cannot be expressed in a manifest, subclass
`DatasetValidator` and pass an instance while loading:

```python
from sci_modeling_bench import DatasetValidator, ValidationReport, Violation


class RejectHomopolymers(DatasetValidator):
    def validate_inputs(self, inputs, context=None):
        sequence = inputs.get("sequence")
        if isinstance(sequence, str) and sequence and len(set(sequence)) == 1:
            return ValidationReport(
                violations=(
                    Violation(
                        code="homopolymer",
                        field="sequence",
                        message="homopolymers are not accepted",
                    ),
                )
            )
        return ValidationReport()
```

Custom validators are local code. Dataset repositories cannot provide remotely
executed validators.

## Knowledge Resources

`dataset.knowledge` is always a read-only mapping and is falsey when the
manifest declares no resources. Resource contents are loaded only when read:

```python
for name, resource in dataset.knowledge.items():
    print(name, resource.title, resource.media_type)

overview = dataset.knowledge.read_text("domain_overview")
# Equivalent: dataset.knowledge["domain_overview"].read_text()
```

Supported media types are `text/markdown` and `text/plain`. Resources are read
from the Dataset's resolved repository revision. They should explain scientific
meaning, priors, constraints, and limitations, not contain executable code or
agent workflow instructions.

## Repository Contract

One Hugging Face Dataset repository can publish multiple related configs:

```text
README.md
scimodelingbench.json
manifests/
└── tfbind8.json
data/
└── tfbind8/
    └── six6_ref_r1.parquet
knowledge/
└── tfbind8/
    └── domain-overview.md
```

The Dataset Card's YAML metadata maps configs and splits to data files.
`scimodelingbench.json` maps the same config names to semantic manifests:

```json
{
  "schema_version": 1,
  "default_config": "tfbind8",
  "configs": {
    "tfbind8": {"manifest": "manifests/tfbind8.json"}
  }
}
```

The config manifest schema version is `1` and defines these field groups:

| Field | Meaning |
|---|---|
| `dataset_id`, `version`, `description`, `license` | Stable identity and release metadata |
| `default_split`, `splits` | Published split declarations; each split has a name, description, optional row count, optional sources, and scalar attributes |
| `inputs`, `targets`, `context` | Semantic field roles and constraints |
| `source`, `citation` | Upstream provenance and citation records |
| `knowledge` | Stable snake-case names mapped to repository-relative text resources |

`source`, `citation`, `context`, and `knowledge` may be omitted or empty. Input,
target, and split collections may not be empty. Unknown manifest fields,
duplicate names, unsafe repository paths, and references to undeclared defaults
are rejected. Raw data and preprocessing code may stay upstream, but provenance
should record the source version, revision, and checksum when available.

Dataset loading never executes Python code from the remote repository.

## Exceptions

| Exception | Raised when |
|---|---|
| `ManifestError` | A collection or config manifest is missing, malformed, or internally inconsistent |
| `DatasetLoadError` | A Hub revision or repository resource cannot be resolved or loaded |
| `SchemaMismatchError` | Loaded data omit declared columns or violate a declared non-streaming row count |
| `ValueError` | A caller requests an undeclared split or constructs an invalid `HubDatasetSource` |

All package-specific exceptions inherit from `SciModelingBenchError`.

## Concrete Dataset

See [TFBind8](../suites/design-bench/tfbind8.md) for the first Dataset-specific
loader, validator, exact Objective, and offline-data Protocol.
