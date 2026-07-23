# Superconductor Candidate-Pool Ranking

SciModelingBench exposes the UCI Superconductivity Data as canonical elemental
composition groups and evaluates ordered candidate selections against retained
measured critical temperatures. The default Task is CPU-friendly and does not
use the learned Random Forest oracle from the original Design-Bench task.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `SuperconductorCandidatePoolRankingTask` |
| Task ID | `design-bench/superconductor-candidate-pool-ranking-v2` |
| Hub config / split | `superconductor` / `composition_groups` |
| Agent input | Lower-temperature labeled groups and an upper-tail unlabeled pool |
| Scored prefix | First 32 distinct candidates from the measured pool |
| Objective | Lookup of the retained group-median critical temperature |
| Primary metric | `global_ndcg` |
| Summary size | 5 materials for the secondary `*_k_*` metrics |

## Load the Dataset

The public artifact is the `superconductor` config in the shared Design-Bench
repository. Pin the repository commit for reproducible runs:

```python
from sci_modeling_bench.suites.design_bench import SuperconductorDataset

dataset = SuperconductorDataset.from_hub(
    revision="b9ec928a5b54e105926e86a2d89be80a07aa0763"
)
groups = dataset.load()

print(len(groups))
# 15164
```

The default split is `composition_groups`. One row is one normalized elemental
composition candidate, not one claim that composition uniquely determines a
material's physical state.

## Scientific Source

The source ZIP contains two row-aligned tables:

- `unique_m.csv`: 86 elemental amount columns from H through Rn, measured
  `critical_temp`, and a material formula;
- `train.csv`: 81 composition-derived descriptors and the same measured
  `critical_temp`.

The 81 descriptors summarize eight elemental properties using unweighted and
composition-weighted statistics. They are useful published baseline features,
but they do not add crystal structure, phase, pressure, defects, or synthesis
conditions.

| Source artifact | SHA-256 |
|---|---|
| UCI ZIP | `87f4490d73390ff94ee01dbf0d7d32abc80b22f2c803d471765cfc46a9f6371e` |
| `unique_m.csv` | `b68ae6b55ea8581eff8b1ffba073a899db7e2d2f7f3b781bb0802f643f51e5f7` |
| `train.csv` | `4dfb6e3a1f6ffd969e5a5e42f093c4800d1e2a6c8b1e309f8fcd9f23d86952f3` |
| Canonical Parquet | `df2f2403cc92567845cfeb58a089f0d585ea83a8c3c33def6dc2c1634fed9f8a` |

The UCI release is CC BY 4.0.

## Source-to-Release Processing

The builder performs the following deterministic transformation:

1. verify the ZIP size, SHA-256, member sizes, CRC32 values, and headers;
2. align `unique_m.csv` and `train.csv` row by row and verify identical targets;
3. reject missing, non-finite, negative, or zero-sum compositions;
4. divide each 86-element amount vector by its sum;
5. round fractions to eight decimal places and group proportional formulas;
6. retain every source row, formula, measured temperature, and descriptor
   vector inside its composition group;
7. use the group median measured temperature as `critical_temp_k`;
8. sort rows by a stable SHA-256-derived `composition_id`.

No disagreement group is deleted. Group standard deviation is descriptive
population standard deviation, not a measurement-error estimate.

```bash
smb-build-superconductor \
  --archive /path/to/superconductivty+data.zip \
  --output-dir /path/to/design-bench-dataset-repo
```

## Dataset Schema

| Column | Role | Meaning |
|---|---|---|
| `composition_id` | Input | Stable ID of the rounded normalized composition |
| `composition` | Context | 86 fractions in fixed H-to-Rn order |
| `representative_formula` | Context | First UCI formula in the group |
| `source_record_ids` | Context | All aligned UCI row IDs |
| `material_formulas` | Context | Formula for every retained source row |
| `critical_temperatures_k` | Context | Every retained measured temperature |
| `critical_temp_k` | Target | Median measured temperature of the group |
| `critical_temp_min_k` / `critical_temp_max_k` | Context | Group measurement range |
| `critical_temp_std_k` | Context | Population standard deviation within the group |
| `observation_count` | Context | Number of retained source rows |
| `descriptor_features_by_observation` | Context | Aligned descriptor vector for every source row |
| `descriptor_features` | Context | Median of the 81 aligned UCI descriptors |

`ELEMENT_SYMBOLS` and `DESCRIPTOR_NAMES` provide the ordered names for the two
fixed-length vectors.

## Audit Summary

| Statistic | Value |
|---|---:|
| Source observations retained | 21,263 |
| Canonical composition groups | 15,164 |
| Groups with repeated observations | 2,422 |
| Source rows in repeated groups | 8,521 |
| Maximum group size | 110 |
| Groups removed because labels disagree | 0 |
| Group-median target minimum / maximum | `0.000325 K` / `143 K` |

The repeated groups are scientifically important. The same normalized
composition can have different reported critical temperatures because the
representation omits pressure, phase, structure, processing, and other
conditions. For example, the source contains composition-identical records
with widely separated temperatures. Treating a fitted composition-only model
as an exact physical oracle would erase that ambiguity.

## Agent-Visible Protocol

`SuperconductorMeasuredPoolProtocol` partitions composition groups by their
median measured target:

- visible groups have `critical_temp_k <= 73 K`;
- the candidate pool has `critical_temp_k > 73 K`;
- every source observation belonging to a visible group is exposed with its
  raw measured temperature;
- candidate compositions and representative formulas are exposed, but
  candidate targets are hidden.

The pinned default partition contains:

| Protocol output | Rows |
|---|---:|
| Visible composition groups | 12,179 |
| Visible source observations | 16,795 |
| Label-hidden candidate groups | 2,985 |

```python
from sci_modeling_bench.suites.design_bench import (
    SuperconductorMeasuredPoolProtocol,
)

bundle = SuperconductorMeasuredPoolProtocol().build_input(dataset)
agent_input = bundle.data
train = agent_input.observations
candidates = agent_input.candidates
element_symbols = agent_input.element_symbols
```

The bundle manifest describes both tables and records `element_symbols` (and,
when enabled, `descriptor_names`) as ordered scientific context for the vector
columns.

By default, the Protocol withholds the published descriptor vector so that a
method can construct its own domain representation. Set
`include_descriptors=True` for a declared descriptor-baseline setting. The
Protocol then returns `descriptor_features` and the ordered
`descriptor_names` in both visible observations and candidates.

## Measured Objective

`SuperconductorMeasuredObjective` is a deterministic table lookup from
`composition_id` to the group's median measured `critical_temp_k`:

```python
from sci_modeling_bench.suites.design_bench import (
    SuperconductorMeasuredObjective,
)

objective = SuperconductorMeasuredObjective(dataset)
output = objective.evaluate({"composition_id": groups[0]["composition_id"]})
```

It is exact with respect to the frozen aggregate table, but it is not an exact
physical simulator and does not assign targets to arbitrary new compositions.
The default Task further restricts submissions to full candidate entries from
the label-hidden pool.

## Candidate-Pool Ranking Task

`SuperconductorCandidatePoolRankingTask` asks an Agent to select and rank
measured candidate groups. `submission_size` defaults to 32. The submitted
list must contain at least that many legal, unique candidate-pool entries in
descending predicted quality. Only the configured leading prefix is scored;
any longer suffix is ignored.

```python
from sci_modeling_bench.suites.design_bench import (
    SuperconductorCandidatePoolRankingTask,
)

task = SuperconductorCandidatePoolRankingTask.from_hub(
    revision="b9ec928a5b54e105926e86a2d89be80a07aa0763",
)
bundle = task.build_input()
agent_input = bundle.data

submission = list(agent_input.candidates)[:32]
evaluation = task.evaluate(submission)

print(evaluation.score)                 # global_ndcg
print(evaluation.metrics["best_score"]) # kelvin
print(evaluation.metrics["batch_mean"])
```

The default primary metric is `global_ndcg`, because the 32-candidate prefix
represents a short experimental priority list rather than a large parallel
screen. The Task still returns
all common metrics, including raw best, best-five mean, batch mean, pool regret,
normalized enrichment, and reranking NDCG. The reference scope is
`evaluation_pool`, so regret means regret against this measured pool, not the
unknown optimum of real materials.

For the frozen pool:

| Reference quantity | Value |
|---|---:|
| Pool mean | `90.4297 K` |
| Pool maximum | `143 K` |
| True top-5 mean | `137.74 K` |
| True top-32 mean | `134.3139 K` |

A 5,000-trial random baseline for the current `N=32`, `K=5` contract with seed
`20260720` gives approximately:

| Random ordered batch metric | Mean | 10th--90th percentile |
|---|---:|---:|
| `best_score` | `126.73 K` | `115.3--134.7 K` |
| `best_k_mean` | `114.73 K` | `106.10--122.85 K` |
| `batch_mean` | `90.48 K` | `87.45--93.58 K` |
| `global_ndcg` | `0.280` | `0.226--0.336` |
| `normalized_enrichment` | approximately `0` | `-0.068--0.072` |

The previous `N=128` setting covered 4.3% of the measured pool in each query
and placed substantial score weight on a long tail of proposed experiments.
The 32-candidate contract retains candidate selection and useful ordering but
focuses the score on a practical short list. `best_score` remains secondary
because random batches can still approach the `143 K` pool maximum. The reference is explicitly the
2,985-group measured candidate pool, so all regret and ranking claims are
pool-relative rather than claims about the open-ended materials space.

### Data-only reference baselines

The SciModelingBench 0.7.0 reference uses only the 86 raw composition
fractions disclosed by the default Protocol. It does not opt into the UCI
descriptor view, parse formulae, or add elemental, periodic-table, Magpie, or
material-family features. Duplicate visible compositions are averaged by
public composition identity.

| Method | `global_ndcg` | `batch_mean` | `best_k_mean` |
|---|---:|---:|---:|
| Random audit mean | 0.280000 | 90.480 K | 114.730 K |
| Fixed standardized Ridge alpha 1 | **0.453389** | **100.183 K** | **115.740 K** |
| CV-selected histogram gradient boosting | 0.239340 | 87.423 K | 91.680 K |

Ordinary three-fold CV on the visible lower-temperature compositions selected
the fixed tree model with mean held-out Spearman `0.902532`, but that model
transferred below random on the upper candidate pool. The result exposes a
strong distribution-shift failure: visible random-fold accuracy alone is not a
reliable selection criterion for this Task. The official evaluator was not
used to replace the selected tree with Ridge.

## Data Analysis and Modeling Notes

The Dataset deliberately preserves modeling work rather than applying it
silently. Useful method families include:

- compositional features that respect non-negativity and constant-sum geometry;
- periodic-table statistics, Magpie-style descriptors, and the published UCI
  descriptors as explicit baselines;
- material-family or element-set models instead of one globally smooth
  Euclidean landscape;
- group-size, range, and repeated-measurement dispersion as uncertainty
  diagnostics, not direct target replacements;
- ranking losses, calibrated ensembles, conformal intervals, and OOD-aware
  selection when extrapolating from the lower-temperature observations;
- family-held-out or descriptor-distance validation to avoid optimistic random
  row splits.

Repeated normalized compositions expose a central modeling limitation: the
same composition can have different measured temperatures when unrecorded
structure, phase, pressure, or processing differs. The group median is the
frozen measured-pool score, while group range, standard deviation, and count
are uncertainty diagnostics rather than alternative labels. The default
Protocol provides raw composition and observation data; published descriptors
are an explicit opt-in baseline, not hidden maintainer feature engineering.

Models should not infer that every non-negative 86-vector is chemically valid
or synthesizable. This Task avoids that unsupported claim by restricting final
candidates to measured normalized compositions. Structure-aware discovery requires a
richer Dataset and a separately versioned Task.

## Agent Visibility and Leakage

This documentation, the complete HF artifact, and the UCI labels are public.
`task.build_input()` exposes only the declared visible observations and hidden
candidate features, but that API boundary alone does not prevent external
lookup. Controlled evaluations must isolate repository files, caches, and
network access through the external harness. The Task itself remains usable for
reproducible workflow and scientific-modeling experiments outside such an
isolation policy.

## References

- Hamidieh, *A data-driven statistical model for predicting the critical
  temperature of a superconductor*, Computational Materials Science (2018),
  [arXiv:1803.10260](https://arxiv.org/abs/1803.10260).
- [UCI Superconductivity Data](https://archive.ics.uci.edu/dataset/464/superconductivty+data),
  dataset 464, accessed 2026-07-16.
- Trabucco et al., *Design-Bench: Benchmarks for Data-Driven Offline
  Model-Based Optimization* (2022),
  [arXiv:2202.08450](https://arxiv.org/abs/2202.08450).
