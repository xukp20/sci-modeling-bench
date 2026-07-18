# Hopper Controller Checkpoint Prioritization

SciModelingBench evaluates structured PPO controller checkpoints with 500
frozen stochastic Hopper-v5 rollouts and exposes a finite-pool ranking Task.
The Task asks an Agent to prioritize 32 measured controllers from a hidden-label
pool; it does not accept arbitrary new weights or run MuJoCo during evaluation.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `HopperControllerCandidatePoolRankingTask` |
| Task ID | `design-bench/hopper-controller-candidate-pool-ranking-v1` |
| Hub config / split | `hopper_controller` / `policies` |
| Agent input | Lower 60% with rollout evidence and an unlabeled upper pool |
| Scored prefix | First 32 distinct policies from the measured pool |
| Objective | Mean of 500 frozen stochastic Hopper-v5 returns |
| Primary metric | `global_ndcg` |

## Dataset

`HopperControllerDataset` contains 3,200 Design-Bench policy vectors. Each
vector parameterizes the same stochastic neural policy:

```text
observation                       11 values
hidden layers                    64, 64
action                            3 values
hidden activation                 tanh
parameter order       W1,b1,W2,b2,W3,b3,logstd
parameter count                    5,126
action distribution             Gaussian
action clipping                 [-1, 1]
```

Every policy is evaluated by 500 independently seeded stochastic rollouts in
the frozen Hopper-v5 recipe. Dataset artifacts are distributed separately from
the Python package. The default source is pinned to the published immutable
Dataset revision:

```python
from sci_modeling_bench.suites.design_bench import HopperControllerDataset

dataset = HopperControllerDataset.from_hub()
policies = dataset.load()

print(len(policies))
# 3200
```

The published revision is
`7b513a5995110f262b8a322cc4bd9ac88e575aee`. It was downloaded from the Hub,
validated over all 3,200 rows, and exercised through the complete Task path.
The implementation still accepts an alternate `repo_id` and `revision`.

## Source and Simulator Identity

The policy vectors and historical returns come from Design-Bench revision
`e52939588421b5433f6f2e9b359cf013c542bd89`. The historical return is retained
only for provenance; it is not the new Objective target.

| Artifact | SHA-256 |
|---|---|
| Design-Bench policy array | `da93f2033436ae5c2f31e584ae42b4b4d043bea29448d78eec6470e4d8ee71d7` |
| Design-Bench historical return array | `8f04be4b81627e59bd83faf42e7aeaed3134dafc8f97d35c3fc887a649d93efd` |
| 500-repeat rollout artifact | `7f9a033b24af476eaed998f9f4d2fb443e9e84c46d8a64765e8b0f3d2cd91e8f` |
| Release Parquet | `950548a4ceaa49068dc3973ec7385673b72eaf60ceb4830dafcae6175616a45a` |

The frozen rollout was generated with Gymnasium 1.3.0, MuJoCo 3.10.0,
Hopper-v5, a 1,000-step maximum horizon, and base seed `20260717`. Every
policy uses the same reset-seed list; action-noise seeds are derived from the
policy identity and repeat index. The release provenance also records the
Hopper XML checksum and exact package versions.

## Build the Release

Simulator dependencies are optional:

```bash
pip install "sci-modeling-bench[hopper-sim]"
```

Generate the complete rollout artifact and an upload-ready Dataset config:

```bash
smb-build-hopper-controller \
  /path/to/hopper_controller-x-0.npy \
  /path/to/hopper_controller-y-0.npy \
  /path/to/hopper-controller-v5-500.npz \
  --repeats 500 \
  --workers 32 \
  --base-seed 20260717 \
  --release-dir /path/to/design-bench-dataset-repo
```

The simulator is needed only for rebuilding or auditing measurements. Loading
the Dataset, constructing the Protocol, exact lookup, and Task evaluation do
not import Gymnasium or MuJoCo.

## Schema

| Column | Type | Meaning |
|---|---|---|
| `policy_weights` | `float32[5126]` | Original structured policy parameters |
| `raw_returns` | `float32[500]` | Every stochastic episodic return |
| `episode_lengths` | `int32[500]` | Aligned episode step counts |
| `terminated` / `truncated` | `bool[500]` | Aligned environment outcomes |
| `mean_return` | `float64` | Arithmetic mean used by the Objective |
| `median_return` | `float64` | Median raw return |
| `return_std` | `float64` | Sample standard deviation |
| `return_standard_error` | `float64` | Sample standard deviation divided by `sqrt(500)` |
| `rollout_count` | `int32` | Always 500 in v1 |
| `policy_identity` | string | Canonical float32 policy identity |
| `source_index` | `int32` | Maintainer provenance; not Agent-visible |
| `source_return` | `float32` | Historical Design-Bench value; not the target |

The release preserves raw measurements. It does not normalize weights, trim
returns, infer PPO trajectory IDs, canonicalize hidden neurons, or publish a
precomputed controller embedding.

## Measurement Audit

| Statistic | Value |
|---|---:|
| Policies | 3,200 |
| Rollouts | 1,600,000 |
| Environment steps | 223,749,627 |
| Mean episode length | `139.844` |
| Mean-return range | `98.286--854.479` |
| Mean-return p05 / p95 | `244.482 / 515.435` |
| Median standard error | `1.991` |
| Five-fold mean-rank Spearman median | `0.99279` |
| Five-fold top-32 Jaccard median | `0.72973` |

Returns are heteroscedastic and heavy-tailed. Strong policies can usually fail
after a few hundred steps yet occasionally survive much longer and earn returns
above 2,000. Episode length and return are therefore valuable paired outcomes,
not redundant metadata. The v1 score remains expected episodic return, defined
as the arithmetic mean of all 500 frozen repeats.

## Agent-Visible Protocol

`HopperControllerLowerScoreProtocol` ranks rows by `(mean_return,
policy_identity)`. The lowest 60% are visible observations and the highest 40%
form the label-hidden candidate pool. There is no discarded gap.

| Protocol output | Rows | Fields |
|---|---:|---|
| Observations | 1,920 | weights, 500 returns, 500 lengths, outcome flags |
| Candidates | 1,280 | weights only |

The Protocol orders each view by stable policy identity rather than source row,
and does not expose historical labels, source index, policy identity, PPO run,
or checkpoint number.

```python
from sci_modeling_bench.suites.design_bench import (
    HopperControllerLowerScoreProtocol,
)

agent_input = HopperControllerLowerScoreProtocol().build_input(dataset)
observations = agent_input.observations
candidates = agent_input.candidates

print(len(observations), len(candidates))
# 1920 1280
```

`HopperControllerAgentInput` also states the architecture, parameter order,
activation, action distribution, action clipping, rollout count, and target
aggregation. These are necessary scientific semantics, not processed features.

## Measured Objective

`HopperControllerMeasuredObjective` canonicalizes a submitted vector as
little-endian float32, computes its stable identity, and exactly looks up the
500-repeat mean:

```python
from sci_modeling_bench.suites.design_bench import (
    HopperControllerMeasuredObjective,
)

objective = HopperControllerMeasuredObjective(dataset)
output = objective.evaluate({
    "policy_weights": policies[0]["policy_weights"],
})
```

The Objective is exact with respect to the frozen measurement table. It is not
an arbitrary-policy simulator. The Task additionally restricts submissions to
the label-hidden candidate pool.

## Candidate-Pool Ranking Task

`HopperControllerCandidatePoolRankingTask` requires at least 32 ordered,
unique candidates. Only the leading 32 are evaluated; a longer suffix is
ignored. Candidates must contain full policy weights rather than an ID.

```python
from sci_modeling_bench.suites.design_bench import (
    HopperControllerCandidatePoolRankingTask,
)

task = HopperControllerCandidatePoolRankingTask(dataset)
agent_input = task.build_input()

submission = list(agent_input.candidates)[:32]
evaluation = task.evaluate(submission)

print(evaluation.primary_metric)       # global_ndcg
print(evaluation.metrics["batch_mean"])
print(evaluation.metrics["best_k_mean"])
```

The reference scope is the 1,280-policy evaluation pool. The default primary
metric is `global_ndcg`, which rewards both selecting strong policies and
placing them early. The report also contains raw `best_score`, top-five
`best_k_mean`, `batch_mean` (mean@32), regret, normalized enrichment, and
within-submission reranking NDCG. Exact top-set overlap is not a score because
policies near the cutoff are statistically close.

For the frozen v1 pool:

| Reference or baseline | Mean@32 |
|---|---:|
| Random candidate batch, median | `484.24` |
| Privileged per-run linear checkpoint trend diagnostic | `511.97` |
| Privileged trial/checkpoint Ridge diagnostic | `512.12` |
| Raw-weight Ridge diagnostic | `528.29` |
| Oracle top 32 | `638.57` |

The gap shows that the Task has learnable signal without being saturated by a
simple raw-vector model. The two privileged trajectory rows use true PPO run
and checkpoint coordinates that the Protocol withholds. They are leakage
diagnostics, not Agent-available baselines.

## Modeling Considerations

The original weights contain strong smooth checkpoint structure consistent
with multiple PPO training runs. This structure is deliberately retained but
not annotated. Recovering a training trajectory from weight continuity and
using its visible return curve is a valid modeling strategy; it does not
directly reveal hidden returns. Even a diagnostic model given the true run and
checkpoint coordinates remains well below the Oracle top-32 mean.

Useful analyses include:

- treating network layers and learned `logstd` separately;
- checking whether policies lie on training trajectories or manifolds;
- modeling non-monotonic checkpoint performance rather than nearest-neighbor
  copying;
- using repeat variance, episode survival, and heavy-tail diagnostics as
  auxiliary targets;
- accounting for hidden-unit permutation and tanh sign symmetries;
- using uncertainty-aware ensembles and ranking losses for top-tail selection.

The Dataset does not assert a legal numeric box for arbitrary weights. In this
Task, legality means finite `float32[5126]` content that exactly matches one
published candidate. Online controller generation, PPO retraining, real-robot
safety, and optima outside the measured pool are out of scope.

## References

- Published Dataset revision,
  <https://huggingface.co/datasets/sci-modeling-bench/design-bench/tree/7b513a5995110f262b8a322cc4bd9ac88e575aee>.
- Trabucco et al., *Design-Bench: Benchmarks for Data-Driven Offline
  Model-Based Optimization*, 2022, <https://arxiv.org/abs/2202.08450>.
- Design-Bench source at the referenced revision,
  <https://github.com/brandontrabucco/design-bench/tree/e52939588421b5433f6f2e9b359cf013c542bd89>.
- Todorov, Erez, and Tassa, *MuJoCo: A Physics Engine for Model-Based
  Control*, 2012, <https://doi.org/10.1109/IROS.2012.6386109>.
