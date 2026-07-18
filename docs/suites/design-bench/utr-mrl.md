# UTR MRL Compositional Ranking

SciModelingBench exposes replicate-averaged mean ribosome load (MRL)
measurements for synthetic 50-nucleotide 5' UTRs. The default Task asks an
Agent to rank a finite measured candidate pool representing an unseen
combination of two translation-initiation factors. It does not use the
learned ResNet oracle from the original Design-Bench UTR task.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `UTRMRLCompositionalRankingTask` |
| Task ID | `design-bench/utr-mrl-egfp-unmodified-compositional-ranking-v1` |
| Hub config / split | `utr_mrl_egfp_unmodified` / `measurements` |
| Agent input | Three labeled uAUG/Kozak groups and one unlabeled combination |
| Scored prefix | First 128 distinct sequences from the measured pool |
| Objective | Lookup of replicate-mean ribosome load |
| Primary metric | `global_ndcg` |

## Load the Dataset

The release is the `utr_mrl_egfp_unmodified` config in the shared Design-Bench
Dataset repository. Pin the repository commit for reproducible runs:

```python
from sci_modeling_bench.suites.design_bench import UTRMRLDataset

dataset = UTRMRLDataset.from_hub(
    revision="2dd09bd522d8fd883e900321fdbd819b747521ea",
)
measurements = dataset.load()

print(len(measurements))
# 318468
```

The default split is `measurements`. It contains the complete canonical table;
the Task-specific visible/hidden partition is constructed by the Protocol and
is not stored as separate train and test splits.

## Scientific Source

Sample et al. measured the effect of randomized 5' UTRs using a massively
parallel translation assay in HEK293T cells. Each variable 50-mer was placed
between a fixed 25-nucleotide primer and an eGFP coding sequence. Polysome
fractionation and sequencing were used to estimate mean ribosome load, a proxy
for translation efficiency.

The source table is the `egfp` config of `morrislab/mrl-sample`, redistributed
for mRNABench from GEO series `GSE114002`. mRNABench averages two experimental
replicates for each RNA-chemistry condition. This release selects the
unmodified-RNA target and retains the 318,468 eGFP sequences present in the
pinned source artifact.

| Source artifact | Identity |
|---|---|
| mRNABench repository | `morrislab/mRNABench@74f96b8e6ae9f41cc3cccff089d826a62d5604b8` |
| HF Dataset revision | `ef67f7cf8a999bb1c412ad6551aa7d9f901cbb95` |
| Source eGFP Parquet SHA-256 | `c007cf66cfcea0807e90baf92ac24b6078102729ad050100bde00f7f0ab4c9b3` |
| Canonical Parquet SHA-256 | `d2d3961e7611a74da5fc609eda1194e97b0ab8a4e6ab095e58db84862b4fc865` |

The upstream HF card labels the source license as unknown. Public availability
does not establish unrestricted redistribution rights; this limitation is
preserved in the Dataset manifest rather than replaced with the Python
package's MIT license.

## Source-to-Release Processing

The builder performs a deterministic, loss-limited transformation:

1. verify the pinned source Parquet size and SHA-256;
2. require 318,468 source rows and the expected mRNABench columns;
3. verify that every construct is the same 855-nucleotide format;
4. verify the fixed 25-nucleotide primer and fixed 780-nucleotide eGFP suffix;
5. extract the variable positions `25:75` as the canonical 50-mer `sequence`;
6. retain the unmodified replicate-mean target as `mean_ribosome_load`;
7. recompute and verify the source uAUG, out-of-frame-uAUG, and simplified
   Kozak annotations from the 50-mer;
8. sort rows lexicographically by sequence and reject duplicate sequences;
9. write raw MRL values without normalization.

```bash
smb-build-utr-mrl \
  --source-parquet /path/to/mrl-sample-egfp.parquet \
  --output-dir /path/to/design-bench-dataset-repo
```

## Dataset Schema

| Column | Role | Meaning | Agent-visible by default |
|---|---|---|---:|
| `sequence` | Input | Uppercase 50-nt variable UTR | Yes |
| `mean_ribosome_load` | Target | Mean of two unmodified-RNA experimental replicates | Observations only |
| `has_uaug` | Context | Whether the 50-mer contains an upstream `ATG` | No |
| `has_out_of_frame_uaug` | Context | Whether any uAUG is out of frame with the main CDS | No |
| `kozak_quality` | Context | `strong`, `weak`, or `mixed` simplified start-context class | No |

The context columns are deterministic audit annotations used to construct the
Protocol partition. They are not precomputed model features exposed to the
Agent. GC content, k-mers, uORFs, secondary structure, and other scientific
representations are deliberately not stored.

The fixed experimental context is recorded once in split metadata:

- reporter: eGFP;
- RNA chemistry: unmodified;
- cell line: HEK293T;
- variable region length: 50 nucleotides;
- target aggregation: mean of two replicates.

These constants describe what the measurements mean; they are not repeated as
per-row AgentInput fields.

## Compositional Protocol

`UTRMRLCompositionalProtocol` uses two sequence-derived biological factors:

- `has_uaug`: whether an upstream start codon occurs before the main eGFP CDS;
- `kozak_quality`: a simplified class derived from the final three UTR bases
  immediately before the fixed main `ATG`.

The Protocol exposes three observed combinations and withholds the fourth:

| uAUG | Kozak | Protocol role | Rows |
|---|---|---|---:|
| absent | strong | labeled observations | 35,534 |
| absent | weak | labeled observations | 2,533 |
| present | strong | labeled observations | 38,810 |
| present | weak | label-hidden candidate pool | 5,043 |

Rows classified as `mixed` Kozak are retained in the Dataset but excluded from
this Protocol. The Agent receives only raw sequences and visible labels:

```python
from sci_modeling_bench.suites.design_bench import UTRMRLCompositionalProtocol

bundle = UTRMRLCompositionalProtocol().build_input(dataset)
agent_input = bundle.data

print(agent_input.observations.column_names)
# ['sequence', 'mean_ribosome_load']

print(agent_input.candidates.column_names)
# ['sequence']
```

The bundle manifest describes exactly these two views and does not include the
hidden per-row `has_uaug` or `kozak_quality` partition annotations.

The split definition is public, but per-row annotations are not exposed. A
method must derive any useful motif, frame, composition, or structural
representation from the sequence itself.

## Measured Objective

`UTRMRLMeasuredObjective` is a deterministic lookup from a measured 50-mer to
its frozen replicate-mean MRL:

```python
from sci_modeling_bench.suites.design_bench import UTRMRLMeasuredObjective

objective = UTRMRLMeasuredObjective(dataset)
output = objective.evaluate({"sequence": measurements[0]["sequence"]})
```

It is exact with respect to the released table, not an exact evaluator for the
open `4^50` sequence landscape. The ranking Task only accepts candidates from
the measured hidden pool and never uses this lookup to score arbitrary new
sequences.

## Candidate-Pool Ranking Task

`UTRMRLCompositionalRankingTask` requires at least 128 unique candidate-pool
sequences ordered by predicted MRL. Only the first 128 are evaluated; a longer
suffix is accepted and ignored.

```python
from sci_modeling_bench.suites.design_bench import (
    UTRMRLCompositionalRankingTask,
)

task = UTRMRLCompositionalRankingTask.from_hub(
    revision="2dd09bd522d8fd883e900321fdbd819b747521ea",
)
bundle = task.build_input()
agent_input = bundle.data

submission = list(agent_input.candidates)[:128]
evaluation = task.evaluate(submission)

print(evaluation.primary_metric)  # global_ndcg
print(evaluation.score)
print(evaluation.metrics["normalized_enrichment"])
```

The reference scope is the 5,043-sequence measured evaluation pool. All
ranking, regret, and enrichment claims are pool-relative and must not be
interpreted as optimization over arbitrary 5' UTRs.

## Metric Audit

The primary metric is `global_ndcg`, which evaluates both candidate selection
and submitted priority order. A fixed 128-candidate audit gave:

| Baseline | Pool Spearman | `global_ndcg` | `normalized_enrichment` | True top-128 recovered |
|---|---:|---:|---:|---:|
| Random ordered submissions | - | `0.591` | approximately `0` | approximately 3 in expectation |
| uAUG-count + GC heuristic | `0.261` | `0.684` | `0.256` | 6 |
| Positional one-hot Ridge | `0.343` | `0.740` | `0.404` | 15 |
| Positional + k-mer/domain Ridge | `0.555` | `0.844` | `0.658` | 30 |
| k-mer/domain histogram gradient boosting | `0.645` | `0.864` | `0.723` | 35 |

The best lightweight baseline selected a batch with mean MRL `7.105`, while
the measured pool's ideal top-128 mean is `7.918`. The Task therefore has a
clear signal and a measurable benefit from sequence-aware representation, but
is not saturated by the tested CPU baselines. `normalized_enrichment` and raw
batch metrics remain secondary diagnostics; noisy single-candidate top-1 is
not the primary score.

## Trust Boundary

Replicate averaging is more stable than the single-replicate Design-Bench
table, but MRL remains an experimental estimate in one fixed construct and
cell context. The source redistribution does not retain per-sequence read
depth or the two replicate values, so this release cannot independently
estimate measurement uncertainty for each row. MRL is also not equivalent to
protein yield, mRNA stability, therapeutic efficacy, or performance under a
different reporter, chemistry, or cell type.

No Knowledge resources are included in the first release. Domain documentation
may be added later as separately indexed Dataset resources without changing
the raw Agent-visible sequence tables.
