# CellDAG-NAS Black-Box Optimization

CellDAG-NAS is the canonical NASBench-101 integration. It searches the DAG and
intermediate operations of a repeated CIFAR-10 CNN cell; it is not the separate
64-dimensional residual-configuration task called `NAS` in the Design-Bench
paper.

The integration combines:

- `CellDAGNASDataset`: 423,624 canonical graphs, all 1,293,208 Design-Bench
  token aliases, and three official 108-epoch training records per graph;
- `CellDAGNASDesignBenchProtocol`: the lowest 40% canonical graphs, expanded
  to aliases with their three raw test accuracies;
- `CellDAGNASExactObjective`: graph-invariant lookup returning the three test
  repeats and their arithmetic mean;
- `CellDAGNASBlackBoxOptimizationTask`: duplicate-aware evaluation of exactly
  128 submitted graph encodings.

## End-to-End Use

```python
from sci_modeling_bench.suites.design_bench import (
    CellDAGNASBlackBoxOptimizationTask,
)

task = CellDAGNASBlackBoxOptimizationTask.from_hub(
    revision="1c223e204fa5f88c8a0c55bd9a66865fdb8bcafa",
)
offline_data = task.build_input()

# Each architecture is a valid 31-token Design-Bench encoding.
submission = [
    {"architecture": architecture}
    for architecture in candidate_architectures
]
evaluation = task.evaluate(submission)

print(evaluation.score)
print(evaluation.metrics["best_score"])
print(evaluation.metrics["best_k_mean_regret"])
print(evaluation.candidates[0].validation)
```

The submission must contain exactly 128 canonical-unique, legal, in-table
graphs. A malformed, duplicate, or unscorable candidate makes the submission
ineligible for official aggregate metrics; diagnostics remain available in the
ordered `evaluation.candidates` records.

## Dataset

| Field | Role | Meaning |
|---|---|---|
| `architecture` | Input | Lexicographically smallest 31-token alias for the graph |
| `test_accuracies` | Target | Three official final test accuracies |
| `mean_test_accuracy` | Target | Arithmetic mean of the three test results |
| `canonical_hash` | Context | Official graph-invariant identity |
| `aliases` | Context | All enumerated 31-token representations |
| `train_accuracies` | Context | Three final train accuracies |
| `validation_accuracies` | Context | Three final validation accuracies |
| `training_times` | Context | Three training times in seconds |

One Dataset row is one canonical graph. Aliases are representations of that
graph, not additional experiments. The three repeats are independent training
runs of the canonical graph and are not additional architectures.

The release is built from the official `nasbench_only108.tfrecord`, pinned to
SHA-256
`4c39c3936e36a85269881d659e44e61a245babcb72cb374eacacf75d0e5f4fd1`.
Every Design-Bench alias is decoded and hashed, and all 1,293,208 processed
mean-test labels match the mean of the three official runs after float32
conversion.

The initial public CellDAG-NAS data release is pinned by commit
`1c223e204fa5f88c8a0c55bd9a66865fdb8bcafa` and tag
`cell-dag-nas-v1.0.0` in `sci-modeling-bench/design-bench`.

Rebuilding the release additionally requires protobuf support:

```bash
python -m pip install "sci-modeling-bench[data-build]"
```

## Default Protocol

The default Protocol sorts canonical graphs by
`(mean_test_accuracy, canonical_hash)` and exposes the lowest 40%:

| Quantity | Value |
|---|---:|
| Visible canonical graphs | 169,449 |
| Hidden canonical graphs | 254,175 |
| Visible alias rows | 419,803 |
| Visible alias fraction | 32.4621% |
| Visible boundary mean test accuracy | 0.9007745783 |

The Agent-visible output has only two columns:

```text
architecture: int8[31]
test_accuracies: float32[3]
```

It does not expose canonical hashes, alias-group IDs, the precomputed mean,
train/validation metrics, or training time. An Agent may choose how to detect
aliases, aggregate repeats, model training collapse, and estimate uncertainty.

Identical repeat triples can provide a shortcut for discovering aliases, so
this setting does not isolate graph-isomorphism reasoning by itself.

## Objective and Validation

Candidate validation checks token structure, the operation vocabulary, the
7-vertex and 9-edge limits, and that every vertex lies on an input-output path.
The Objective then computes the NASBench-101 graph-invariant hash and performs
one lookup in the 423,624-graph table.

All aliases of one graph return identical values:

```python
{
    "test_accuracies": [repeat_1, repeat_2, repeat_3],
    "mean_test_accuracy": (repeat_1 + repeat_2 + repeat_3) / 3,
}
```

The default Objective retains failed or collapsed training runs. Removing
them, using the median, or conditioning on training success would define a
different Objective.

## Task Evaluation

The default primary metric is:

```text
best_k_mean
```

For the default `N=128`, `K=min(5, N)=5`. `best_k_mean` is the mean test
accuracy of the five truly best canonical graphs in the submitted set. It is
more stable than a lucky top-1 while remaining focused on finding a small set
of strong architectures rather than requiring all 128 candidates to be near
optimal.

The frozen table is an exhaustively known `full_domain` reference. The Task
therefore reports the complete common metric set, including:

```text
best_score
best_k_mean
batch_mean
best_regret
best_k_mean_regret
batch_mean_regret
normalized_enrichment
global_ndcg
reranking_ndcg
```

The raw score metrics use mean test accuracy and are maximized; regret metrics
are minimized. Callers may select another supported primary metric when
constructing the Task, but results with different primary metrics or
submission sizes must not share one leaderboard.

Per-candidate results distinguish malformed graphs, out-of-table graphs, and
canonical duplicates. Isomorphic aliases have the same candidate identity.
They cannot occupy multiple slots in an eligible submission.

A frozen audit used 5,000 random canonical-unique 128-graph submissions from
the Task's full domain. Random `best_score` was `0.93609 +/- 0.00173`, already
close to the table optimum `0.94318`; random `best_k_mean` was
`0.93378 +/- 0.00127`. Across the three official training repeats, the average
Spearman correlation with the three-repeat target was `0.517` for top-1 and
`0.702` for best-five mean. This is why `best_k_mean`, rather than legacy
`best_score`, is the default primary metric. `normalized_enrichment` remains a
useful secondary measure of full-batch quality.

The historical Design-Bench value `NAS = 1.079 +/- 0.059` belongs to the
different ResidualConfig-NAS task and is not a baseline for CellDAG-NAS.
There is currently no public leaderboard using this exact low-40%, repeat-aware,
strict-offline setting.

## Data Analysis and Modeling Notes

The low-40% Protocol is target-derived. A random draw from its hidden
complement has a higher mean `best_k_mean` (`0.93485 +/- 0.00106`) than a
full-domain random draw, but it is only a split diagnostic, not the Task's
candidate rule or a comparable baseline. Final candidates may be any legal,
in-table canonical graph; all relative metrics use the 423,624-graph
`full_domain` reference.

Two lightweight audit methods demonstrate where modeling work belongs:

| Method | `best_score` | `best_k_mean` | `batch_mean` | `normalized_enrichment` |
| --- | ---: | ---: | ---: | ---: |
| Structural graph heuristic | `0.93630` | `0.93624` | `0.92308` | `0.608` |
| Low-40%-only HistGradientBoosting surrogate | `0.93747` | `0.93423` | `0.92620` | `0.680` |

These are metric audits, not a claimed NAS leaderboard. Suitable declared
method choices include graph and operation features, path or motif counts,
graph-aware surrogates, repeat-aware uncertainty estimates, and search methods
over validated graph encodings. Aliases must be collapsed by canonical graph
identity for final submission, and three test repeats should be treated as
repeated training outcomes rather than three independent architectures.

## Trust Boundary

The full NASBench-101 table is public. The package separates Protocol output
from trusted Objective state, but it does not prevent an Agent from downloading
the source table. Controlled evaluation requires an external harness to isolate
the full Dataset, cache, repository checkout, and network access.
