# TFBind10 Pho4

TFBind10 Pho4 is a measured-pool DNA sequence optimization Task built from the
BET-seq assay of Le et al. It replaces Design-Bench's clipped per-row ddG lookup
with raw replicate observations and a deterministic count-grounded evaluator.

## Scientific Object

Each candidate is an uppercase DNA flank sequence of length 10 over
`A`, `C`, `G`, and `T`. The complete domain contains `4^10 = 1,048,576`
sequences. The source experiment reports four Pho4 replicates and 4,160,533
sequence-replicate observations.

The canonical `observations` split contains:

| Field | Role | Meaning |
|---|---|---|
| `sequence` | input | DNA 10-mer candidate |
| `replicate_id` | context | Pho4 replicate 1 through 4 |
| `bound_count` | context | raw bound-library read count |
| `input_count` | context | raw input-library read count |
| `bound_fraction` | context | published count/depth bound fraction |
| `input_fraction` | context | published count/depth input fraction |
| `observed_ddg` | target | published per-replicate `-RT log(bound/input)` in kcal/mol |

Signed infinite `observed_ddg` values are retained when exactly one count is
zero. They are experimental observations, not invalid floating-point artifacts.
No replicate is averaged, no aggregate affinity label is stored, and no
complement sequence is synthesized.

## Source And Release

The release is built from version 1 of the Fordyce Lab
[BET-seq Processed Data](https://doi.org/10.6084/m9.figshare.5728467.v1),
licensed CC BY 4.0. The builder reads
`data/Manuscript_Data/counts.txt.gz`, selects the published `pho4` rows, renames
columns, narrows integer storage types, and otherwise preserves source values
and order.

The pinned archive SHA-256 is
`3f6bc76273b00f5e1fb074b8e181077907eb265f12f443546f6da7db8c90f91e`.
The generated Parquet SHA-256 is
`4fe5a39d1999e05d9e2969098cbdb4e31a694c3f1ab7d94be638f765963b3006`.
The published Hugging Face revision is
`51155f061b77c9f56a0ad8cf3b04c4ae481a7274`.

```python
from sci_modeling_bench.suites.design_bench import TFBind10Pho4Dataset

dataset = TFBind10Pho4Dataset.from_hub(
    revision="51155f061b77c9f56a0ad8cf3b04c4ae481a7274"
)
observations = dataset.load()
```

`dataset.validate_dataset()` performs vectorized release checks, including
replicate row counts and depths, complete 10-mer coverage, uniqueness of each
sequence-replicate pair, fraction/count consistency, signed-infinity ddG
semantics, and the input library shared by replicates 3 and 4.

## Posterior Objective

`TFBind10Pho4PosteriorObjective` returns one maximize-oriented
`affinity_score` for each measured sequence. It pools all four bound libraries,
counts the shared replicate-3/replicate-4 input library once, and applies an
`alpha = 1` symmetric Dirichlet posterior:

```text
affinity_score = RT * (
    digamma(bound_count + alpha)
    - digamma(bound_depth + 4^10 * alpha)
    - digamma(input_count + alpha)
    + digamma(input_depth + 4^10 * alpha)
)
```

Here `RT = 0.593 kcal/mol`. The output is computed from multiple raw Dataset
rows and therefore is intentionally not a persisted Dataset target. It is
finite for zero-count sequences and deterministic for a pinned data revision.

This is a trusted measurement model, not an exact physical binding oracle.
Pseudocount choice, assay noise, and replicate disagreement still limit
fine-grained ranking, especially at extreme scores.

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind10Pho4PosteriorObjective,
)

objective = TFBind10Pho4PosteriorObjective(dataset)
output = objective.evaluate({"sequence": "AACCGGTTAA"})
print(output["affinity_score"])
```

## Agent Input Protocol

`TFBind10Pho4LowerHalfProtocol` partitions unique sequences at the median
posterior affinity score:

- 524,300 lower-half sequences are visible through all 2,087,323 of their raw
  replicate rows;
- 524,276 upper-half sequence identities form the label-hidden candidate pool;
- the Agent does not receive `affinity_score` for either side.

The median has 144 tied sequences. The Protocol places ties on the visible
side using `score <= median`, which keeps the two sides deterministic.

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind10Pho4LowerHalfProtocol,
)

agent_input = TFBind10Pho4LowerHalfProtocol().build_input(dataset)
print(agent_input.observations.column_names)
print(agent_input.candidates.column_names)  # ["sequence"]
```

The Agent is responsible for replicate handling, zero-count treatment,
feature construction, sequence modeling, and candidate ranking. The Protocol
does not publish a pre-aggregated training label.

## Optimization Task

`TFBind10Pho4BlackBoxOptimizationTask` requires an ordered batch of 128 unique,
valid sequences from the upper-half candidate pool. It reports the complete
common candidate metric set and uses `normalized_enrichment` as its default
primary metric:

```text
(submitted batch mean - candidate-pool mean)
-------------------------------------------------
(measured top-128 pool mean - candidate-pool mean)
```

Random pool selection has expectation zero. A value of one means that the
submitted batch mean equals the frozen measured pool's top-128 batch mean; it
does not claim a theoretical or independently validated physical optimum.

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind10Pho4BlackBoxOptimizationTask,
)

task = TFBind10Pho4BlackBoxOptimizationTask.from_hub(
    revision="51155f061b77c9f56a0ad8cf3b04c4ae481a7274"
)
agent_input = task.build_input()

submission = [
    {"sequence": sequence}
    for sequence in agent_input.candidates["sequence"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.primary_metric)  # normalized_enrichment
print(evaluation.score)
print(evaluation.metrics)
```

A wrong batch size is a submission-level error. Invalid DNA, duplicate
sequences, and visible or otherwise out-of-pool candidates receive candidate
diagnostics. Any such batch is ineligible for aggregate benchmark metrics.

## Data Analysis, Metric Choice, and Modeling Notes

The Protocol preserves raw replicate counts rather than publishing a
maintainer-aggregated training label. This matters because zero counts and
library-depth differences can produce extreme per-replicate `observed_ddg`
values. The trusted posterior Objective pools the four bound libraries and
counts the shared input library for replicates 3 and 4 once; an Agent must make
its own corresponding data-handling and modeling choices from the visible rows.

The metric audit used 20,000 random 128-sequence submissions from the frozen
upper-half pool. Mono- and dinucleotide Ridge models train only on the visible
lower half. The validated-NN row is an external diagnostic landscape, not a
baseline available through the Task input.

| Method or diagnostic | `best_score` | `best_k_mean` | `batch_mean` | `global_ndcg` | `normalized_enrichment` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random mean | `0.8440` | `0.6359` | `0.1935` | `0.1055` | `0.0001` |
| Mono-nucleotide Ridge | `0.4841` | `0.4404` | `0.2435` | `0.1358` | `0.0354` |
| Di-nucleotide Ridge | `0.4471` | `0.4248` | `0.2715` | `0.1529` | `0.0551` |
| Validated-NN diagnostic | `1.5687` | `1.4543` | `0.5706` | `0.3194` | `0.2659` |

The simple sequence models improve full-batch metrics while random batches
often contain an extreme single count-derived score. Across replicate splits,
the correlation of method rankings was `0.938` for both `batch_mean` and
`normalized_enrichment`, compared with `0.554` for `best_score` and `0.731`
for `best_k_mean`. The normalized form is the default because it has random
expectation zero and top-128-pool value one, while preserving the same ranking
as `batch_mean` for this frozen pool.

Useful method families include count-aware posterior or uncertainty estimates,
position and k-mer sequence features, motif and interaction models, and
ranking models that select from the provided candidate IDs. Methods should not
fit a clipped per-row ddG as though it were an exact affinity label, and must
not use hidden-pool labels to choose the final batch.

## Rebuild

After downloading the pinned Figshare archive:

```bash
smb-build-tfbind10-pho4 \
  --archive BET-seq_processed_data.tar.gz \
  --output-dir ./tfbind10-pho4-release
```

The builder verifies the 861 MB archive, the nested count artifact, every
source row, replicate totals, count-derived fractions and ddG, sequence
coverage, shared-library semantics, and the generated artifact checksum.

## Scope And Limitations

- This setting evaluates selection and ranking within a measured finite pool;
  it does not extrapolate to arbitrary sequence lengths or alphabets.
- The derived Objective is more robust to zero counts and replicate depth than
  a clipped single-row ddG lookup, but it remains assay-grounded rather than
  an exact biochemical oracle.
- `best_score` and `best_k_mean` are retained as diagnostics. The default uses
  batch enrichment because replicate audits found aggregate batch quality more
  stable than extreme single-candidate scores.
- Cbf1 is not included in this Task because the audited raw aggregate did not
  show sufficient agreement with the available independent titration data for
  the same evaluator design.
