# SciModelingBench

SciModelingBench is a Python framework for reproducible scientific modeling
and design benchmarks. Version 0.1.0 provides the first experimental package
surface for loading versioned observations, validating scientific schemas,
constructing agent-visible inputs, and evaluating candidates against trusted
objectives.

## Installation

SciModelingBench requires Python 3.10 or later.

From PyPI:

```bash
python -m pip install "sci-modeling-bench==0.1.0"
```

From the GitHub v0.1.0 source tag:

```bash
python -m pip install \
  "git+https://github.com/xukp20/sci-modeling-bench.git@v0.1.0"
```

## Scope

SciModelingBench provides:

- revision-pinned loading of scientific datasets hosted on Hugging Face;
- semantic manifests, schemas, provenance metadata, and structured validation;
- trusted Objectives for candidate-to-target evaluation;
- Protocols that construct the information exposed to an optimization agent;
- optional, lazily loaded domain-knowledge resources.

The package does not yet define Tasks, submission formats, metrics, query
budgets, agent workflows, or evaluation harnesses.

## Minimal TFBind8 Example

The first integration exposes the canonical TFBind8 `SIX6_REF_R1` landscape,
an exact black-box Objective, and the Design-Bench bottom-50% offline-data
Protocol:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
    TFBind8ExactObjective,
)

dataset = TFBind8Dataset.from_hub(
    revision="2ee2856f4255bb6a64c11b6c2660a6f41418e654"
)
offline_data = TFBind8DesignBenchProtocol().build_input(dataset)
score = TFBind8ExactObjective(dataset).evaluate({"sequence": "AACCGGTT"})
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
- [TFBind8 integration](https://github.com/xukp20/sci-modeling-bench/blob/main/docs/suites/design-bench/tfbind8.md)
- [Changelog](https://github.com/xukp20/sci-modeling-bench/blob/main/CHANGELOG.md)

## Release Status

Version 0.1.0 is the initial experimental release. Dataset, Objective, and
Protocol interfaces are implemented but may change as additional scientific
benchmarks are integrated. The TFBind8 code path has been validated against
the pinned public Hugging Face artifact and the legacy Design-Bench arrays.
