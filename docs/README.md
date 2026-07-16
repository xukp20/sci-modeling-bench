# SciModelingBench Documentation

SciModelingBench is an observation-grounded framework for scientific modeling
and design benchmarks. The first release provides experimental `Dataset`,
`Objective`, and `Protocol` APIs plus an end-to-end black-box optimization
integration for TFBind8.

## Start Here

- [Architecture and core concepts](architecture/core-concepts.md) explains the
  framework boundaries, trust model, and data flow.
- [API documentation](api/README.md) covers the three implemented public
  interfaces:
  - [Dataset API](api/dataset.md)
  - [Objective API](api/objective.md)
  - [Protocol API](api/protocol.md)
- [TFBind8](suites/design-bench/tfbind8.md) documents the first supported
  black-box optimization setting, its canonical data, and Design-Bench parity.

## First-Release Scope

The implemented layers load revision-pinned scientific observations, construct
the information visible to an optimization agent, and evaluate candidates
against trusted targets. A benchmark `Task`, runner, query-budget policy,
submission format, and metrics layer are not implemented. Those responsibilities
remain with the external harness in this release.

The public interfaces are experimental. Pin dataset revisions and package
versions in reproducible work.

## Maintainers

- [Release process](development/releasing.md)
