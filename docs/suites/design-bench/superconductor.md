# Superconductor Measured-Pool Optimization

SciModelingBench exposes the UCI Superconductivity Data as canonical elemental
composition groups and evaluates ordered candidate selections against retained
measured critical temperatures. The default Task is CPU-friendly and does not
use the learned Random Forest oracle from the original Design-Bench task.

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
- candidate compositions, IDs, and representative formulas are exposed, but
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

agent_input = SuperconductorMeasuredPoolProtocol().build_input(dataset)
train = agent_input.observations
candidates = agent_input.candidates
element_symbols = agent_input.element_symbols
```

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
The default Task further restricts submissions to IDs in the label-hidden
candidate pool.

## Black-Box Optimization Task

`SuperconductorBlackBoxOptimizationTask` asks an Agent to select and rank
measured candidate groups. `submission_size` defaults to 128. The submitted
list must contain exactly that many legal, unique candidate-pool IDs in
descending predicted quality.

```python
from sci_modeling_bench.suites.design_bench import (
    SuperconductorBlackBoxOptimizationTask,
)

task = SuperconductorBlackBoxOptimizationTask.from_hub(
    revision="b9ec928a5b54e105926e86a2d89be80a07aa0763",
)
agent_input = task.build_input()

submission = [
    {"composition_id": candidate_id}
    for candidate_id in agent_input.candidates["composition_id"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.score)                 # global_ndcg
print(evaluation.metrics["best_score"]) # kelvin
print(evaluation.metrics["batch_mean"])
```

The default primary metric is `global_ndcg`, because random 128-candidate
batches already obtain high best-of-batch temperatures. The Task still returns
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
| True top-128 mean | `128.5665 K` |

A fixed-seed 50,000-trial random baseline gives approximately:

| Random ordered batch metric | Mean | 10th--90th percentile |
|---|---:|---:|
| `best_score` | `133.76 K` | `130.1--136.5 K` |
| `best_k_mean` | `128.25 K` | `123.34--132.51 K` |
| `batch_mean` | `90.43 K` | `88.97--91.92 K` |
| `global_ndcg` | `0.304` | `0.276--0.334` |
| `reranking_ndcg` | `0.762` | `0.726--0.801` |
| `normalized_enrichment` | approximately `0` | `-0.038--0.039` |

The same random sets, reordered by their trusted hidden temperatures, increase
mean `global_ndcg` only from `0.3044` to `0.3995` while making
`reranking_ndcg` equal to `1`. This shows that `global_ndcg` requires both a
strong candidate set and a useful experimental priority order. It is the
default primary metric; `best_score` is secondary because random batches are
already close to the `143 K` pool maximum. The reference is explicitly the
2,985-group measured candidate pool, so all regret and ranking claims are
pool-relative rather than claims about the open-ended materials space.

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
candidates to measured composition IDs. Structure-aware discovery requires a
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
