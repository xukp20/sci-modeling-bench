# GFP Measured-Pool Ranking

SciModelingBench reconstructs the Sarkisyan GFP local fitness landscape at the
protein level and evaluates ordered selections from a label-hidden pool of
measured variants. The default Task uses the authors' protein-level aggregate
measurements directly; it does not use the learned Transformer oracle or the
nucleotide-derived duplicate rows from the original Design-Bench release.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `GFPCandidatePoolRankingTask` |
| Task ID | `design-bench/gfp-candidate-pool-ranking-v2` |
| Hub config / split | `gfp` / `protein_genotypes` |
| Agent input | Lower-brightness protein, nucleotide, and barcode evidence plus an unlabeled upper pool |
| Scored prefix | First 128 distinct protein sequences from the measured pool |
| Objective | Lookup of author-provided protein median brightness |
| Primary metric | `normalized_enrichment` |
| Summary size | 16 proteins for the secondary `*_k_*` metrics |

## Quick Start

```python
from sci_modeling_bench.suites.design_bench import (
    GFPCandidatePoolRankingTask,
)

task = GFPCandidatePoolRankingTask.from_hub(
    revision="836f17c81c5cc365d1bf43af3397cd4ed87cb587"
)
bundle = task.build_input()
agent_input = bundle.data

print(len(agent_input.protein_observations))
print(len(agent_input.candidates))

# Rank predicted brightness from highest to lowest.
submission = [
    {"sequence": sequence}
    for sequence in agent_input.candidates["sequence"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.primary_metric, evaluation.score)
print(evaluation.metrics)
print(bundle.manifest.model_dump_json(indent=2))
```

The example preserves the Dataset order and is not a modeling baseline.
Official submissions should contain 128 distinct candidate sequences ordered
from predicted brightest to predicted dimmest.

The manifest describes all four visible tables separately and publishes the
avGFP reference sequence as structured context. Candidate fields do not include
brightness, barcode, coverage, or nucleotide-measurement semantics.

## Scientific Source

The source is the GFP local fitness landscape measured by Sarkisyan et al.
using fluorescence-activated cell sorting and DNA barcodes. The frozen source
release is [Figshare article 3102154, version 1](https://doi.org/10.6084/m9.figshare.3102154.v1),
published under CC BY 4.0.

The benchmark uses five author-provided files:

| Source file | Role |
|---|---|
| `amino_acid_genotypes_to_brightness.tsv` | Canonical protein-level aggregate target |
| `nucleotide_genotypes_to_brightness.tsv` | Synonymous nucleotide-genotype aggregates |
| `barcodes_to_brightness.tsv` | Filtered individual-barcode brightness measurements |
| `genotypes.tsv` | Barcode genotype and sequencing-coverage context |
| `avGFP_reference_sequence.fa` | Frozen nucleotide reference used to reconstruct sequences |

The target is the authors' `medianBrightness`, represented as
`median_log10_brightness`. It is the median log-brightness over accepted
barcodes associated with one amino-acid genotype. Larger values are better.

## Why This Is Not the Legacy GFP Task

The original Design-Bench artifact contains 56,086 nucleotide-genotype rows
but discards nucleotide identity after translating each row to a protein
sequence. It consequently contains only 51,715 unique proteins. Among the
1,202 duplicated protein groups, 1,201 have conflicting labels; the wild-type
protein alone appears 534 times with brightness values from approximately
3.514 to 4.033.

The author release already provides the correct protein-level aggregation.
After removing 2,310 stop-containing genotypes, it contains 51,715 unique,
237-residue proteins. SciModelingBench rebuilds from that table rather than
averaging the semantically conflicting legacy rows.

The legacy Transformer oracle is also excluded. A learned predictor can be a
useful baseline, but it is not scientific ground truth for newly generated
sequences and its ranking in the measured high-brightness tail is unreliable.

## Canonical Dataset

The public artifact is the `gfp` config in the shared Design-Bench Dataset
repository. Its default `protein_genotypes` split has one row per canonical
protein and preserves aligned lower-level observations as list columns.

| Release item | Value |
|---|---|
| Dataset revision | `836f17c81c5cc365d1bf43af3397cd4ed87cb587` |
| Canonical rows | 51,715 proteins |
| Nucleotide observations | 56,086 |
| Filtered barcode observations | 65,678 |
| Parquet SHA-256 | `5340280e9e01b9ed2c32cbb429d2d4bb28513f44daa764511be4db8b6fb66d98` |

| Column | Role | Meaning |
|---|---|---|
| `protein_id` | Context | Stable SHA-256-derived join identifier |
| `sequence` | Input | Unique uppercase 237-residue amino-acid sequence |
| `aa_mutations` | Context | Author substitution notation relative to avGFP |
| `mutation_count` | Context | Number of amino-acid substitutions |
| `unique_barcodes` | Context | Barcodes supporting the protein aggregate |
| `median_log10_brightness` | Target | Author protein-level median brightness |
| `brightness_std` | Context | Author-reported barcode dispersion, nullable |
| `nucleotide_*` list columns | Context | Aligned nucleotide-genotype aggregates |
| `barcode_*` list columns | Context | Aligned filtered barcode measurements and coverage |

The builder reconstructs each protein from the frozen reference, validates
the source residue and zero-based position in every mutation token, removes
stop-containing variants, joins lower-level observations, rejects broken
foreign keys, and sorts rows by `protein_id`. It does not normalize, clip, or
replace measured brightness values.

No structure, stability, conservation, positional-effect, or epistasis
feature is precomputed. The lower-level measurement fields are retained so a
method can decide how to model replicate consistency, synonymous variation,
coverage, censoring, and uncertainty.

## Agent-Visible Input

`GFPLowerToHigherMeasuredPoolProtocol` partitions canonical proteins by the
80th percentile of `median_log10_brightness`:

- `protein_observations`: lower 80% protein rows with labels and aggregate
  measurement context;
- `nucleotide_observations`: nucleotide aggregates belonging only to visible
  proteins;
- `barcode_observations`: filtered barcode measurements belonging only to
  visible proteins;
- `candidates`: upper 20% measured proteins with sequence-derived fields only;
- `reference_sequence`: the 237-residue avGFP reference.

The partition is performed by protein identity before lower-level tables are
expanded. Candidate barcode counts, dispersions, coverage, nucleotide
measurements, and brightness values are therefore not exposed through a join.
The candidate pool is finite: the Task does not claim that arbitrary proteins
can be evaluated exactly.

## Objective and Task

`GFPMeasuredObjective` performs a deterministic, ordered batch lookup from
canonical sequence to the frozen protein-level measurement. "Measured" means
exact lookup in this release, not a noiseless physical oracle over all protein
space.

`GFPCandidatePoolRankingTask` requires at least 128 candidate mappings:

```python
[{"sequence": "..."}, ...]
```

Only the first 128 candidates are scored. They must be valid 237-residue
sequences, distinct, and members of the label-hidden evaluation pool. Candidate
identity is the full canonical sequence. A violation in the scored prefix
returns per-candidate diagnostics and no comparable aggregate metrics.

The primary metric is `normalized_enrichment`, computed relative to random
selection from the complete evaluation pool and its measured top-128 batch.
It rewards a consistently bright experimental batch without requiring the
weakly replicated upper tail to define a reliable 128-way ordering. The
result also reports `global_ndcg`, top-16 and batch means, rank-sensitive
diagnostics, and pool-relative regrets. See
[candidate submission metrics](../../metrics/candidate-submission-metrics.md)
for the common definitions.

## Difficulty Audit

Under the frozen lower-80%/upper-20% Protocol, the candidate pool contains
10,343 measured proteins and the visible side contains 41,372. For 128-item
submissions, an initial CPU audit produced:

| Method | Pool Spearman | Normalized enrichment | Global NDCG |
|---|---:|---:|---:|
| Random, 50,000 trials | approximately 0 | approximately 0 | 0.228 |
| Mutation count only | 0.015 | -0.064 | 0.177 |
| Position-wise one-hot Ridge | 0.238 | 0.214 | 0.402 |
| Categorical histogram gradient boosting | 0.251 | 0.270 | 0.437 |
| Measured-label ordering | 1.000 | 1.000 | 1.000 |

The simple models detect substantial signal but do not saturate the ranking
problem. The current 5,000-trial random audit gives
`normalized_enrichment=0.00005` on average with a
`-0.02860--0.02879` 10th--90th percentile range; the previous table remains
valid because `N=128` is unchanged. A random 80/20 split was rejected because the same one-hot Ridge
baseline reached about 0.937 global NDCG, making it a weak test of scientific
modeling.

## Measurement and Trust Boundaries

- The landscape is local to avGFP and does not cover arbitrary proteins.
- Dark variants are censored near a measurement floor around `log10(20)`.
- Most proteins have one accepted barcode; `brightness_std` is available for
  only 1,680 proteins and must not be interpreted as zero when missing.
- The brightest measured variants are weakly replicated, so top-1 brightness
  is a secondary diagnostic rather than the primary score.
- The Dataset is public. A strict benchmark runner must isolate the complete
  Hub artifact, evaluator state, caches, and network from the Agent and decide
  what final or intermediate feedback to reveal.

## Rebuild

```bash
smb-build-gfp \
  --amino-acid-table /path/to/amino_acid_genotypes_to_brightness.tsv \
  --nucleotide-table /path/to/nucleotide_genotypes_to_brightness.tsv \
  --barcode-table /path/to/barcodes_to_brightness.tsv \
  --genotypes-table /path/to/genotypes.tsv \
  --reference-fasta /path/to/avGFP_reference_sequence.fa \
  --output-dir /path/to/design-bench-dataset-repo
```

The builder verifies pinned file sizes and SHA-256 checksums before writing the
Parquet artifact, manifest, provenance record, and Dataset card entry.

## Citation

- Sarkisyan et al., [Local fitness landscape of the green fluorescent protein](https://doi.org/10.1038/nature17995), Nature 2016.
- Trabucco et al., [Design-Bench: Benchmarks for Data-Driven Offline Model-Based Optimization](https://proceedings.mlr.press/v162/trabucco22a.html), ICML 2022.
