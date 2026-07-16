<p align="center">
  <img
    src="https://raw.githubusercontent.com/xukp20/sci-modeling-bench/main/assets/sci-modeling-bench-logo.png"
    alt="SciModelingBench logo"
    width="190"
  >
</p>

<h1 align="center">SciModelingBench</h1>

<p align="center">
  <strong>Observation-grounded benchmarks for scientific modeling and design agents.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/sci-modeling-bench/">
    <img alt="PyPI version" src="https://img.shields.io/pypi/v/sci-modeling-bench">
  </a>
  <a href="https://pypi.org/project/sci-modeling-bench/">
    <img alt="Python versions" src="https://img.shields.io/pypi/pyversions/sci-modeling-bench">
  </a>
  <a href="https://pypi.org/project/sci-modeling-bench/">
    <img alt="Development status" src="https://img.shields.io/pypi/status/sci-modeling-bench">
  </a>
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/sci-modeling-bench">
  </a>
</p>

<p align="center">
  <a href="https://github.com/xukp20/sci-modeling-bench/tree/main/docs">Documentation</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/architecture/core-concepts.md">Architecture</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/README.md">API</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind8.md">TFBind8</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind10-pho4.md">TFBind10 Pho4</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/superconductor.md">Superconductor</a>
  &middot;
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/cell-dag-nas.md">CellDAG-NAS</a>
  &middot;
  <a href="https://huggingface.co/datasets/sci-modeling-bench/design-bench">Dataset Hub</a>
</p>

SciModelingBench separates versioned scientific observations, Agent-visible
inputs, trusted target functions, and benchmark evaluation into explicit,
reusable interfaces. The source tree includes end-to-end TFBind8, TFBind10
Pho4, Superconductor, and CellDAG-NAS Tasks.

## Installation

SciModelingBench requires Python 3.10 or later.

### Stable Release

Install the latest published version from PyPI:

```bash
python -m pip install "sci-modeling-bench==0.3.0"
```

The same release can be installed from its Git tag:

```bash
python -m pip install \
  "git+https://github.com/xukp20/sci-modeling-bench.git@v0.3.0"
```

### Development Version

The documentation below follows the current source tree:

```bash
python -m pip install \
  "git+https://github.com/xukp20/sci-modeling-bench.git@main"
```

## What It Provides

SciModelingBench provides:

- revision-pinned loading of scientific datasets hosted on Hugging Face;
- semantic manifests, schemas, provenance metadata, and structured validation;
- trusted Objectives for persisted-target lookup or derived evaluation;
- Protocols that construct the information exposed to an optimization agent;
- Tasks that bind Agent input to typed submission and metric semantics;
- optional, lazily loaded domain-knowledge resources.

The package does not define a universal submission format, query budgets,
agent workflows, process isolation, or an evaluation harness.

## Quick Start: TFBind8

The package provides an end-to-end Task for the canonical TFBind8
`SIX6_REF_R1` landscape. It combines the Design-Bench bottom-50% offline-data
Protocol, exact Objective, ordered submission contract, and common candidate
metrics:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

task = TFBind8BlackBoxOptimizationTask.from_hub(
    revision="b9ec928a5b54e105926e86a2d89be80a07aa0763"
)
offline_data = task.build_input()

submission = [
    {"sequence": sequence}
    for sequence in offline_data["sequence"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.score)
print(evaluation.metrics)
print(evaluation.valid_candidates, evaluation.invalid_candidates)
```

The TFBind8 observations are downloaded from the public SciModelingBench
Hugging Face organization and are not bundled in the Python wheel.

## Core Concepts

- **Dataset** binds immutable observations to metadata, semantic fields,
  validation rules, splits, and optional knowledge.
- **Objective** validates candidates and returns declared persisted or derived
  outputs while preserving batch order and repeated candidates.
- **Protocol** derives the data or context visible to an agent without
  modifying the underlying Dataset.
- **Task** defines one complete submission contract and its evaluation metrics;
  only Objective-backed Task subclasses require an Objective.
- **Knowledge** provides read-only explanatory resources pinned to the same
  dataset revision.

## Dataset Artifacts

Dataset artifacts are hosted separately from this package. Neither the PyPI
distribution nor the GitHub source repository bundles observation tables.
Loaders resolve dedicated Hugging Face Dataset repositories at pinned commits;
the package contains the framework, integrations, validators, and reproducible
builders.

## Documentation

- [Documentation index](https://github.com/xukp20/sci-modeling-bench/tree/main/docs)
- [Architecture and core concepts](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/architecture/core-concepts.md)
- [Dataset API](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/dataset.md)
- [Objective API](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/objective.md)
- [Protocol API](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/protocol.md)
- [Task API](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/task.md)
- [Candidate submission metrics](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/metrics/candidate-submission-metrics.md)
- [TFBind8 integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind8.md)
- [TFBind10 Pho4 integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind10-pho4.md)
- [Superconductor integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/superconductor.md)
- [CellDAG-NAS integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/cell-dag-nas.md)
- [Changelog](https://github.com/xukp20/sci-modeling-bench/blob/main/CHANGELOG.md)

## Development Status

The public interfaces remain experimental. Pin package versions and Hugging
Face revisions in reproducible runs. New releases are published only after the
complete Dataset, Protocol, Objective, Task, documentation, and tests are
validated together.
