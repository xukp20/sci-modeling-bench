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
  <a href="https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/README.md">Design-Bench Suite</a>
  &middot;
  <a href="https://huggingface.co/datasets/sci-modeling-bench/design-bench">Dataset Hub</a>
</p>

SciModelingBench separates versioned scientific observations, Agent-visible
inputs, trusted target functions, and benchmark evaluation into explicit,
reusable interfaces. The source tree includes end-to-end TFBind8, TFBind10
Pho4, Superconductor, CellDAG-NAS, Hopper Controller, UTR MRL, GFP, and
DrugMatrix Tasks. The measured-pool integrations retain source observations
and avoid treating legacy learned Design-Bench oracles as experimental truth.

<p align="center">
  <img
    src="https://raw.githubusercontent.com/xukp20/sci-modeling-bench/main/assets/sci-modeling-bench-task-montage.png"
    alt="SciModelingBench task overview: biomolecular design, superconducting materials, preclinical toxicology, neural architecture design, and embodied control"
    width="100%"
  >
</p>

## Installation

SciModelingBench requires Python 3.10 or later.

### Stable Release

Install the latest published version from PyPI:

```bash
python -m pip install sci-modeling-bench
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
- integrity-checked local caching for deterministic derived evaluator artifacts;
- Protocols that construct the information exposed to an optimization agent;
- Tasks that bind Agent input to typed submission and metric semantics;
- optional, lazily loaded domain-knowledge resources.

The package does not define a universal submission format, query budgets,
agent workflows, process isolation, or an evaluation harness.

Hub-backed Tasks enable derived artifact caching by default. Set
`SCI_MODELING_BENCH_CACHE_DIR` to choose a shared local root, call
`task.prepare()` before serving evaluations, or pass `cache=False` when no
persistent derived state is desired. Package upgrades reuse entries whenever
the pinned Dataset revision and derivation version are unchanged.

## Quick Start: TFBind8

The package provides an end-to-end Task for the canonical TFBind8
`SIX6_REF_R1` landscape. It combines the Design-Bench bottom-50% offline-data
Protocol, exact Objective, ordered submission contract, and common candidate
metrics:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

task = TFBind8BlackBoxOptimizationTask.from_hub()
agent_input = task.build_input()
offline_data = agent_input.data

# A uniform, disclosure-scoped description of the visible table.
print(agent_input.manifest.model_dump_json(indent=2))

submission = [
    {"sequence": sequence}
    for sequence in offline_data["sequence"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.score)
print(evaluation.metrics)
print(evaluation.valid_candidates, evaluation.invalid_candidates)
```

When `revision` is omitted, the current default branch of the Dataset
repository is resolved to an immutable commit SHA for that Dataset instance.
For a reproducible benchmark run, pass a full commit SHA explicitly; the
initial TFBind8 release is
`2ee2856f4255bb6a64c11b6c2660a6f41418e654`.

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

| Area | Entry point |
|---|---|
| Documentation | [Documentation index](https://github.com/xukp20/sci-modeling-bench/tree/main/docs) |
| Architecture | [Core concepts and data flow](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/architecture/core-concepts.md) |
| Public interfaces | [API overview](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/api/README.md) |
| Implemented settings | [Design-Bench suite](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/README.md) |
| Evaluation | [Candidate submission metrics](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/metrics/candidate-submission-metrics.md) |
| Changes | [Changelog](https://github.com/xukp20/sci-modeling-bench/blob/main/CHANGELOG.md) |

## Development Status

The public interfaces remain experimental. Pin package versions and Hugging
Face revisions in reproducible runs. New releases are published only after the
complete Dataset, Protocol, Objective, Task, documentation, and tests are
validated together.
