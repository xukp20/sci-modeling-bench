# SciModelingBench Documentation

SciModelingBench provides observation-grounded building blocks for scientific
modeling and design benchmarks. The framework separates versioned data,
agent-visible inputs, trusted evaluation, and Task-level scoring.

> **Project status:** the public APIs remain experimental. Reproducible work
> should pin both the package version and the Hugging Face dataset revision.

## Documentation Map

| Topic | Start here |
|---|---|
| Framework boundaries and data flow | [Architecture and core concepts](architecture/core-concepts.md) |
| Dataset loading, schemas, and validation | [Dataset API](api/dataset.md) |
| Trusted candidate evaluation | [Objective API](api/objective.md) |
| Agent-visible inputs | [Protocol API](api/protocol.md) |
| Submissions and Task composition | [Task API](api/task.md) |
| Evaluator preparation and derived caches | [Derived artifact cache](api/cache.md) |
| Candidate scoring and ranking | [Candidate submission metrics](metrics/candidate-submission-metrics.md) |

The [API overview](api/README.md) provides a shorter entry point to the four
core interfaces.

## Design-Bench Suite

See the [Design-Bench suite index](suites/design-bench/README.md) for the common
Task contract and the [migration and coverage
record](suites/design-bench/migration-and-coverage.md) for modernization
decisions and deferred historical families.

| Setting | Scientific area | Evaluation basis | Task form |
|---|---|---|---|
| [TFBind8](suites/design-bench/tfbind8.md) | DNA binding | Complete measured landscape | Black-box optimization |
| [TFBind10 Pho4](suites/design-bench/tfbind10-pho4.md) | DNA binding | Raw BET-seq replicate counts | Black-box optimization |
| [Superconductor](suites/design-bench/superconductor.md) | Materials | Measured critical temperature | Candidate-pool ranking |
| [CellDAG-NAS](suites/design-bench/cell-dag-nas.md) | Neural architecture search | Official repeated NAS records | Black-box optimization |
| [Hopper Controller](suites/design-bench/hopper-controller.md) | Control | Repeated simulator rollouts | Candidate-pool ranking |
| [UTR MRL](suites/design-bench/utr-mrl.md) | RNA sequence design | Measured translation efficiency | Candidate-pool ranking |
| [GFP](suites/design-bench/gfp.md) | Protein design | Measured median brightness | Candidate-pool ranking |
| [DrugMatrix](suites/design-bench/drugmatrix.md) | Molecular toxicology | Measured control-relative endpoints | Candidate-pool ranking |

Each setting page documents the scientific object, canonical data, evaluator
trust boundary, Task contract, provenance, and recommended modeling work.

## Project Boundary

The package currently handles revision-pinned observations, typed validation,
agent-visible input construction, trusted Objectives, and Task evaluation. The
external harness remains responsible for process isolation, network policy,
query budgets, iterative feedback, and agent orchestration.

## Project Links

- [Python package](https://pypi.org/project/sci-modeling-bench/)
- [Hugging Face datasets](https://huggingface.co/datasets/sci-modeling-bench/design-bench)
- [Release process](development/releasing.md)
