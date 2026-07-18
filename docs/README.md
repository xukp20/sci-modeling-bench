# SciModelingBench Documentation

SciModelingBench is an observation-grounded framework for scientific modeling
and design benchmarks. It provides experimental `Dataset`, `Objective`,
`Protocol`, and `Task` APIs with end-to-end candidate optimization Tasks.

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
- [TFBind10 Pho4](suites/design-bench/tfbind10-pho4.md) documents raw BET-seq
  replicates, a count-grounded posterior Objective, and upper-pool batch
  optimization.
- [Superconductor](suites/design-bench/superconductor.md) documents measured
  composition groups, lower-to-upper-tail modeling, and ordered pool ranking.
- [CellDAG-NAS](suites/design-bench/cell-dag-nas.md) documents the canonical
  NASBench-101 graph-search Dataset and duplicate-aware Task.
- [Hopper Controller](suites/design-bench/hopper-controller.md) documents
  500-repeat stochastic controller measurements, a lower-score Protocol, and
  finite-pool checkpoint prioritization.
- [Candidate submission metrics](metrics/candidate-submission-metrics.md)
  defines the common score, regret, batch-quality, and ordered-ranking
  vocabulary for black-box optimization and related candidate Tasks.

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
