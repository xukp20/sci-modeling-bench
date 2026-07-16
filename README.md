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
  <a href="https://huggingface.co/datasets/sci-modeling-bench/design-bench">Dataset Hub</a>
</p>

SciModelingBench separates versioned scientific observations, Agent-visible
inputs, trusted target functions, and benchmark evaluation into explicit,
reusable interfaces. Version `0.2.0` provides experimental Dataset, Objective,
Protocol, and Task APIs plus an end-to-end TFBind8 black-box optimization Task.

## Installation

SciModelingBench requires Python 3.10 or later.

### Stable Release

Install the latest published version from PyPI:

```bash
python -m pip install "sci-modeling-bench==0.2.0"
```

The same release can be installed from its Git tag:

```bash
python -m pip install \
  "git+https://github.com/xukp20/sci-modeling-bench.git@v0.2.0"
```

## What It Provides

SciModelingBench provides:

- revision-pinned loading of scientific datasets hosted on Hugging Face;
- semantic manifests, schemas, provenance metadata, and structured validation;
- trusted Objectives for candidate-to-target evaluation;
- Protocols that construct the information exposed to an optimization agent;
- Tasks that bind Agent input to typed submission and metric semantics;
- optional, lazily loaded domain-knowledge resources.

The package does not define a universal submission format, query budgets,
agent workflows, process isolation, or an evaluation harness.

## Quick Start: TFBind8

The package provides an end-to-end Task for the canonical TFBind8
`SIX6_REF_R1` landscape. It combines the Design-Bench bottom-50% offline-data
Protocol, exact Objective, submission contract, and top-1 metric:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

task = TFBind8BlackBoxOptimizationTask.from_hub(
    revision="2ee2856f4255bb6a64c11b6c2660a6f41418e654"
)
offline_data = task.build_input()

submission = [{"sequence": "AACCGGTT"} for _ in range(128)]
evaluation = task.evaluate(submission)

print(evaluation.score)
print(evaluation.valid_candidates, evaluation.invalid_candidates)
```

The TFBind8 observations are downloaded from the public SciModelingBench
Hugging Face organization and are not bundled in the Python wheel.

## Core Concepts

- **Dataset** binds immutable observations to metadata, semantic fields,
  validation rules, splits, and optional knowledge.
- **Objective** validates candidates and returns declared target values while
  preserving batch order and repeated candidates.
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
- [TFBind8 integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind8.md)
- [Changelog](https://github.com/xukp20/sci-modeling-bench/blob/main/CHANGELOG.md)

## Release Status

Version 0.2.0 adds the experimental Task and submission-evaluation APIs while
preserving the Dataset, Objective, and Protocol interfaces from 0.1.0. These
interfaces may still change as additional scientific benchmarks are integrated.
The TFBind8 code path has been validated against the pinned public Hugging Face
artifact and the legacy Design-Bench arrays.
