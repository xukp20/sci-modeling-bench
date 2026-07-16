# SciModelingBench Documentation

SciModelingBench is an observation-grounded framework for scientific modeling
and design benchmarks. Version 0.2.0 provides experimental `Dataset`,
`Objective`, `Protocol`, and `Task` APIs plus an end-to-end black-box
optimization integration for TFBind8.

## Start Here

- [Architecture and core concepts](architecture/core-concepts.md) explains the
  framework boundaries, trust model, and data flow.
- [API documentation](api/README.md) covers the four implemented public
  interfaces:
  - [Dataset API](api/dataset.md)
  - [Objective API](api/objective.md)
  - [Protocol API](api/protocol.md)
  - [Task API](api/task.md)
- [TFBind8](suites/design-bench/tfbind8.md) documents the first supported
  black-box optimization setting, its canonical data, and Design-Bench parity.

## Current Scope

The implemented layers load revision-pinned scientific observations, construct
the information visible to an optimization agent, and evaluate typed Task
submissions against trusted targets. A benchmark runner, query-budget policy,
process-isolation layer, and universal submission schema are not implemented.
Those responsibilities remain with the external harness.

The public interfaces are experimental. Pin dataset revisions and package
versions in reproducible work.

## Maintainers

- [Release process](development/releasing.md)
