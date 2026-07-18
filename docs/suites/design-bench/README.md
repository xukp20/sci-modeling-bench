# Design-Bench Suite

SciModelingBench rebuilds selected scientific settings from Design-Bench around
versioned observations and explicitly trusted evaluators. It is not an API or
leaderboard compatibility layer for the original package.

The suite currently contains eight complete integrations. Each provides a
Dataset, validator, Agent-visible Protocol, trusted Objective, Task,
reproducible data path, tests, and setting documentation.

## Task Inventory

| Setting | Scientific evidence | Task form | Submission | Primary metric |
|---|---|---|---:|---|
| [TFBind8](tfbind8.md) | Complete measured DNA 8-mer landscape | Black-box optimization | 128 | `best_k_mean` |
| [TFBind10 Pho4](tfbind10-pho4.md) | Four raw BET-seq count replicates over the complete 10-mer domain | Black-box optimization | 128 | `normalized_enrichment` |
| [CellDAG-NAS](cell-dag-nas.md) | Three official NASBench-101 training repeats per canonical graph | Black-box optimization | 128 | `best_k_mean` |
| [Superconductor](superconductor.md) | Measured critical temperatures grouped by composition | Candidate-pool ranking | 128 | `global_ndcg` |
| [Hopper Controller](hopper-controller.md) | 500 frozen Hopper-v5 rollouts per policy | Candidate-pool ranking | 32 | `global_ndcg` |
| [UTR MRL](utr-mrl.md) | Replicate-mean translation measurements | Candidate-pool ranking | 128 | `global_ndcg` |
| [GFP](gfp.md) | Protein-genotype median brightness measurements | Candidate-pool ranking | 128 | `global_ndcg` |
| [DrugMatrix](drugmatrix.md) | Individual-animal clinical-pathology measurements | Candidate-pool ranking | 64 per endpoint | `global_ndcg` |

Black-box optimization requires exactly the configured number of distinct,
valid candidates. Candidate-pool ranking accepts a longer ordered list but
scores only its configured prefix. See [Candidate submission
metrics](../../metrics/candidate-submission-metrics.md) for the shared result
contract.

## Evaluation Policy

The suite chooses the Task form from the evidence available for each setting:

- complete measured or exact domains support free-form black-box optimization;
- finite measurement collections without a trustworthy out-of-pool evaluator
  support candidate-pool ranking;
- repeated measurements remain explicit or are aggregated by a documented
  deterministic Objective;
- learned predictors are modeling baselines, not experimental ground truth;
- changing candidate identity, evaluator semantics, reference scope, or metric
  creates a new Task identity.

The rebuilt settings can therefore differ from historical Design-Bench input
representations and scores. Read [Migration and upstream
coverage](migration-and-coverage.md) for the family-by-family decisions,
excluded settings, and compatibility boundaries.

## Common Usage

Concrete Tasks are available from `sci_modeling_bench.suites.design_bench`:

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

task = TFBind8BlackBoxOptimizationTask.from_hub()
agent_input = task.build_input()
evaluation = task.evaluate(submission)

print(agent_input.manifest.model_dump_json(indent=2))
print(evaluation.score)
print(evaluation.metrics)
```

Every Task returns an `AgentInputBundle`. Domain-specific tables and constants
are under `agent_input.data`; `agent_input.manifest` uniformly describes only
the views and fields disclosed by that Task's Protocol.

Pin the package version and immutable Hugging Face revision for reproducible
runs. The public data artifacts do not create a secrecy boundary; controlled
Agent evaluations require an external harness to isolate data, caches, source
checkout, and network access.

## Reference Pages

- [Framework architecture](../../architecture/core-concepts.md)
- [Task API](../../api/task.md)
- [Objective API](../../api/objective.md)
- [Candidate submission metrics](../../metrics/candidate-submission-metrics.md)
- [Migration and upstream coverage](migration-and-coverage.md)
