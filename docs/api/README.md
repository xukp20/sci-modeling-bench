# API Documentation

The framework exposes four core experimental interfaces:

- [Dataset API](dataset.md): revision-pinned observations, manifests, semantic
  schemas, validation, splits, and knowledge resources.
- [Objective API](objective.md): trusted, Dataset-bound candidate evaluation.
- [Protocol API](protocol.md): construction of agent-visible benchmark input.
- [Task API](task.md): submission contracts, metrics, and composition of
  Dataset, Protocol, and optional Objective resources.

The [derived artifact cache](cache.md) documents evaluator-side preparation,
cache identity, integrity checks, and multi-worker reuse.

For how these interfaces fit together, read
[Architecture and core concepts](../architecture/core-concepts.md). The
[TFBind8](../suites/design-bench/tfbind8.md) and
[Superconductor](../suites/design-bench/superconductor.md) show all four in
complete ordered-candidate workflows.

The [Design-Bench suite index](../suites/design-bench/README.md) lists all
eight implemented integrations.
