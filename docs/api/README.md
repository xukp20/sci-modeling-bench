# API Documentation

The framework exposes four experimental interfaces:

- [Dataset API](dataset.md): revision-pinned observations, manifests, semantic
  schemas, validation, splits, and knowledge resources.
- [Objective API](objective.md): trusted, Dataset-bound candidate evaluation.
- [Protocol API](protocol.md): construction of agent-visible benchmark input.
- [Task API](task.md): submission contracts, metrics, and composition of
  Dataset, Protocol, and optional Objective resources.

For how these interfaces fit together, read
[Architecture and core concepts](../architecture/core-concepts.md). The
[TFBind8](../suites/design-bench/tfbind8.md) and
[Superconductor](../suites/design-bench/superconductor.md) show all four in
complete black-box optimization workflows.
