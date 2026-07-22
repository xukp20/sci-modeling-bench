# Derived Artifact Cache

> **Status:** Experimental. Cached artifacts are trusted evaluator state and
> must never be copied into Agent-visible inputs.

SciModelingBench caches deterministic tables and arrays derived from a pinned
Dataset revision. This avoids rebuilding expensive evaluator state every time
a process constructs the same Task. Hugging Face remains the source of the
published observations; the local cache contains only reproducible derived
artifacts.

## Default Behavior

Dataset and Task `from_hub()` factories enable the derived cache by default.
The cache root is selected in this order:

1. `SCI_MODELING_BENCH_CACHE_DIR`;
2. `$XDG_CACHE_HOME/sci-modeling-bench`;
3. `~/.cache/sci-modeling-bench`.

Use an explicit location for a shared benchmark workspace:

```python
task = TFBind10Pho4BlackBoxOptimizationTask.from_hub(
    revision="full-commit-sha",
    cache_dir="/benchmark-cache/sci-modeling-bench",
)
reports = task.prepare()
```

Pass `cache=False` to disable derived caching. Direct Dataset constructors also
leave it disabled unless an `ArtifactCache` is supplied explicitly; this keeps
local fixtures and custom repositories free of unexpected writes.

## Identity and Reuse

An artifact identity includes the artifact and schema versions, Dataset ID,
repository and config, split, resolved Dataset revision, and derivation
parameters. The installed package version is recorded as provenance but is not
part of the identity. A package upgrade therefore reuses an artifact when its
producer version and every semantic input remain unchanged. Code that changes
the derivation must increment that producer version.

Each entry is a directory containing safe data files and JSON metadata. Files
are size- and SHA-256-verified before loading. A corrupt or incomplete entry is
removed and rebuilt. Per-artifact file locks and atomic directory replacement
ensure concurrent workers build a missing artifact only once.

## Preparation Reports

`Task.prepare()` prepares evaluator-side artifacts without evaluating a
submission. It returns zero or more `PreparationReport` records:

| Field | Meaning |
|---|---|
| `artifact_id` | Stable derivation name |
| `cache_enabled` | Whether persistent caching was enabled |
| `cache_hit` | Whether a valid entry was reused |
| `rebuilt` | Whether an invalid existing entry was replaced |
| `path` | Local artifact path, or `None` when disabled |
| `elapsed_sec` | Time spent loading or building the artifact |

At present, TFBind10 Pho4 caches the count-derived affinity landscape and all
six DrugMatrix Tasks share one cached measured-condition pool. Exact-lookup
Tasks use `prepare()` to materialize their in-process lookup ahead of the first
evaluation; their published Hugging Face data remain cached by the `datasets`
library.
