# TFBind8 Black-Box Optimization

TFBind8 is the first end-to-end black-box optimization support in
SciModelingBench. It combines:

- `TFBind8Dataset`, a canonical and validated DNA 8-mer binding landscape;
- `TFBind8DesignBenchProtocol`, a deterministic offline-data view compatible
  with the Design-Bench TFBind8-Exact setting at the candidate-set level;
- `TFBind8ExactObjective`, a trusted exact lookup for candidate evaluation;
- `TFBind8BlackBoxOptimizationTask`, the default ordered 32-candidate
  evaluation contract with `best_k_mean` as its primary metric.

The package does not provide an optimization agent, benchmark runner,
query-budget enforcement, or process isolation.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `TFBind8BlackBoxOptimizationTask` |
| Task ID | `design-bench/tfbind8-black-box-optimization-v3` |
| Hub config / split | `tfbind8` / `six6_ref_r1` |
| Agent input | Lowest 50% of sequences with measured labels |
| Submission | Exactly 32 distinct valid DNA 8-mers |
| Objective | Exact lookup over the complete measured landscape |
| Primary metric | `best_k_mean` |
| Summary size | 5 sequences |

## End-to-End Use

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8BlackBoxOptimizationTask,
)

REVISION = "2ee2856f4255bb6a64c11b6c2660a6f41418e654"

task = TFBind8BlackBoxOptimizationTask.from_hub(revision=REVISION)

# The external agent receives only this bundle.
agent_input = task.build_input()
offline_data = agent_input.data

# The final submission must contain exactly 128 distinct candidates, ordered
# from the Agent's highest to lowest predicted quality.
submission = [
    {"sequence": sequence}
    for sequence in offline_data["sequence"][:128]
]
evaluation = task.evaluate(submission)

print(evaluation.score)
print(evaluation.valid_candidates, evaluation.invalid_candidates)
```

In a black-box run, keep the Task and its Dataset and Objective on the trusted
side. The complete TFBind8 table is publicly available, so this integration is
a reproducible reference task rather than a secrecy- or
contamination-resistant benchmark. A harness that wants to simulate hidden
evaluation must isolate the agent from the full Hugging Face cache and external
network access, and must enforce its own query budget or feedback policy.

See [Architecture and core concepts](../../architecture/core-concepts.md) for
the framework-wide trust model.

## Release Identity

| Field | Value |
|---|---|
| Hugging Face repository | `sci-modeling-bench/design-bench` |
| Config | `tfbind8` |
| Split | `six6_ref_r1` |
| Dataset ID | `design-bench/tfbind8` |
| Dataset version | `1.0.0` |
| Rows | 65,536 |
| Initial release commit | `2ee2856f4255bb6a64c11b6c2660a6f41418e654` |
| Public data tag | `v1.0.0` |

The Hugging Face repository is public. No Hugging Face token is required for
the default source or the pinned `v1.0.0` release.

`TFBind8Dataset.from_hub()` supplies the repository, config, and
`TFBind8Validator` by default. Its `repo_id`, `config_name`, `revision`, and
`validator` arguments remain replaceable for a mirror or another release:

```python
from sci_modeling_bench import HubDatasetSource
from sci_modeling_bench.suites.design_bench import TFBind8Dataset

mirror = HubDatasetSource(
    repo_id="internal-mirror/design-bench",
    config_name="tfbind8",
    revision="full-commit-sha",
)
dataset = TFBind8Dataset.from_source(mirror)
```

## Candidate and Targets

The candidate domain is the complete set of uppercase, length-eight DNA strings
over `A`, `C`, `G`, and `T`.

| Column | Semantic role | Hugging Face dtype | Meaning |
|---|---|---|---|
| `sequence` | Input | `string` | Uppercase DNA sequence of length eight |
| `e_score` | Target | `float64` | Published PBM enrichment statistic |
| `normalized_e_score` | Target | `float32` | Condition-level min-max normalization used by Design-Bench |

The published, unnormalized E-score remains float64 so normalization can be
reproduced from the published decimals. The normalized score is float32 for
exact parity with the historical Design-Bench target array.

`TFBind8Validator` checks the full canonical artifact for column order, 65,536
unique sequences, complete `4^8` coverage, deterministic `A<C<G<T` order,
finite scores, reverse-complement score agreement, and exact float32
normalization.

## Data Construction and Audit

### Upstream and Design-Bench representations

The pinned Barrera et al. archive contains a tab-separated
`SIX6_REF_R1_8mers.txt` table with 32,896 rows. Each row supplies an 8-mer, its
reverse complement, and one shared E-score, followed by the published `Median`
and `Z-score` columns. The two sequence columns therefore enumerate the 32,896
reverse-complement orbits of the complete DNA 8-mer space rather than 32,896
unrelated observations.

Here, "original E-score" means the published score before Design-Bench's
min-max transform; it is still a derived PBM statistic, not raw probe intensity.
The first release does not publish the source `Median` and `Z-score` fields
because they are outside the historical TFBind8 optimization target.

The historical Design-Bench processor encodes bases as `A=0`, `C=1`, `G=2`,
and `T=3`, concatenates the two sequence columns, duplicates the shared target,
and stores only a condition-level min-max-normalized float32 target. This
produces 65,792 rows. The SciModelingBench builder reconstructs that historical
representation for parity checks, but publishes a scientific string
representation and retains the original E-score as well.

The audit identified representation and weighting issues that need explicit
handling:

| Finding | Historical consequence | Release decision |
|---|---|---|
| A reverse-complement palindrome appears in both source sequence columns | 256 exact candidate/label rows are repeated after concatenation | Remove only these exact repeats |
| Non-palindromic reverse complements share an assay score | Two different legal sequence strings have the same target | Retain both strings and verify score equality |
| Legacy `x` uses integer tokens | Scientific meaning and alphabet order are external to the array | Publish uppercase DNA strings |
| Legacy `y` contains only the normalized score | The published E-score scale cannot be recovered from `y` alone | Publish both unnormalized and normalized targets |
| The source also contains `Median` and `Z-score` | These fields are not used by the Design-Bench objective | Exclude them from v1 and record the omission rather than treating them as unavailable |
| Legacy row order follows source concatenation | Order is not a canonical identity for the complete space | Sort deterministically with `A<C<G<T` |

No conflicting duplicate labels, malformed sequences, missing legal 8-mers,
NaN targets, or infinite targets were found.

### Source-to-release transformation

The canonical builder:

1. verifies the archive size, SHA-256, member size, CRC32, and table header;
2. validates every sequence and reverse-complement relationship;
3. expands both sequence columns with their shared E-score;
4. removes the 256 exact repeats created by reverse-complement palindromes;
5. retains non-palindromic reverse complements as separate candidates;
6. verifies complete coverage of all `4^8` legal sequences;
7. sorts sequences deterministically using `A<C<G<T`;
8. min-max normalizes E-score over the condition and stores it as float32.

The resulting Parquet has no duplicate sequences. When the pinned historical
NPY files are supplied to the builder, the reconstructed pre-deduplication
token and target arrays match Design-Bench element by element.

### Measured data summary

The following statistics describe the pinned `six6_ref_r1` release, not a
sample:

| Statistic | Value |
|---|---:|
| Source reverse-complement rows | 32,896 |
| Expanded historical rows | 65,792 |
| Canonical unique sequences | 65,536 |
| Reverse-complement palindromes / removed repeats | 256 / 256 |
| Distinct E-score values | 25,239 |
| E-score minimum / maximum | `-0.47907` / `0.49105` |
| E-score mean / standard deviation | `-0.0291607` / `0.1688974` |
| E-score 25th / 50th / 75th percentiles | `-0.15174` / `-0.052895` / `0.0700525` |
| Normalized-score median | `0.4393013` |
| Canonical candidates exposed by the default bottom-50% Protocol | 32,768 |

Tied targets are expected: every non-palindromic reverse-complement pair shares
an E-score, and the published score precision introduces additional ties. The
maximum E-score is shared by one reverse-complement pair. Candidate-level
metrics and data splits should therefore not assume target values are unique.

### Deliberately retained structure

Release canonicalization corrects representation artifacts; it does not turn
the observations into model-ready features. The release deliberately retains:

- both members of every non-palindromic reverse-complement pair;
- the measured target ties and published decimal precision;
- both the published E-score and its monotonic Design-Bench normalization;
- the complete legal 8-mer domain, without a stored train/validation/test split;
- plain DNA strings rather than one-hot, k-mer, motif, or learned features.

Other conditions and replicates in the upstream archive are also not aggregated
into this split. They can be added later as separately identified splits rather
than silently mixed with `SIX6_REF_R1`.

Dataset-specific feature engineering, symmetry handling, split construction,
target transforms, and search representations are method choices. They are not
silently applied by `TFBind8Dataset`.

## Documentation and Agent Visibility

This page is package and benchmark-maintainer documentation. SciModelingBench
does not inject it into a Task input. The default `AgentInputBundle.data`
contains only `sequence` and `normalized_e_score` for the Protocol-selected
offline observations, while `AgentInputBundle.manifest` describes those two
visible fields. A runner may add an explicit task
statement, but should not expose maintainer analysis or optional modeling notes
unless that is part of the declared setting.

For a controlled run, the external harness must also control repository,
documentation, cache, and network access. The complete historical TFBind8
landscape is already public, so this task remains a reproducible integration
and workflow benchmark rather than a contamination-resistant hidden test.

## Exact Objective

`TFBind8ExactObjective` has Objective ID
`design-bench/tfbind8-exact-v1` and returns both targets:

```python
objective = TFBind8ExactObjective(dataset)

output = objective.evaluate({"sequence": "AACCGGTT"})
batch = objective.evaluate_batch(
    [
        {"sequence": "AACCGGTT"},
        {"sequence": "TTTTTTTT"},
        {"sequence": "AACCGGTT"},
    ]
)
```

The Objective validates each candidate through `TFBind8Dataset`, preserves
batch order and repeated candidates, and lazily builds a one-to-one lookup from
the selected canonical split. A syntactically valid sequence missing from that
artifact raises `ObjectiveLookupError`; it is not assigned a fallback or minimum
score.

The exact Objective makes evaluation deterministic, but it does not enforce
black-box policy. Query counts and which returned fields are shown to the agent
remain external-harness decisions.

See the [Objective API](../../api/objective.md) for common batch and error
semantics.

## Default Task

`TFBind8BlackBoxOptimizationTask` combines the default Dataset, Protocol, and
exact Objective:

- `submission_size` defaults to 32 and is configurable at construction time;
- candidates are ordered from the Agent's highest to lowest predicted quality;
- every candidate must be legal, present in the exact landscape, and unique;
- every eligible submission receives the complete common candidate metric set;
- the default primary metric is `best_k_mean`, with `K=5`;
- relative metrics use all 65,536 exact scores as a `full_domain` reference.

Submission-level findings, such as `candidate_count_mismatch`, are represented
by `SubmissionValidationReport`. Each candidate has an independent
`CandidateValidationReport` with Dataset-derived findings such as
`invalid_alphabet_symbol` or the Task-level `duplicate_candidate`. Invalid
submissions retain diagnostics but do not receive official aggregate metrics.

```python
task = TFBind8BlackBoxOptimizationTask.from_hub(
    submission_size=32,
    summary_size=5,
    primary_metric="best_k_mean",
)
visible = task.build_input().data
submission = [
    {"sequence": sequence}
    for sequence in visible["sequence"][:32]
]
result = task.evaluate(submission)

result.submission_valid
result.evaluation_eligible
result.score
result.metrics
result.best_candidate_index
result.candidates[0].validation
result.candidates[0].objective_output
```

The complete result is intended for the trusted harness. The harness decides
whether the Agent sees only the aggregate metric and invalid count or the full
per-candidate outputs. See the [Task API](../../api/task.md).

See [Candidate submission metrics](../../metrics/candidate-submission-metrics.md)
for the score, regret, enrichment, and ordered-ranking formulas. `best_score`
retains Design-Bench's best-of-submission interpretation as a secondary metric.

## Metric Choice and Modeling Notes

The current metric audit used 5,000 uniformly sampled, without-replacement
submissions of 32 sequences from the complete 65,536-sequence reference
domain, with seed `20260720`. The table reports the random mean and its
10th--90th percentile range.

| `best_score` | `best_k_mean` | `batch_mean` | `normalized_enrichment` | `global_ndcg` |
| ---: | ---: | ---: | ---: | ---: |
| `0.8671` (`0.7717--0.9577`) | `0.7533` (`0.6727--0.8314`) | `0.4638` (`0.4257--0.5031`) | `0.0001` (`-0.0721--0.0744`) | `0.4667` (`0.4229--0.5116`) |

The earlier 128-candidate audit gave random `best_k_mean=0.8798`, showing that
a large proposal batch substantially rewarded coverage luck. Reducing the
default to 32 lowers that random mean to `0.7533`, while `K=5` still requires
several strong sequences rather than one extreme. `batch_mean`, enrichment,
and NDCG remain secondary diagnostics.

The release intentionally exposes strings, not a maintainer-selected feature
matrix. Reasonable declared method choices include position-aware one-hot or
k-mer features, motif and interaction terms, and local mutation searches.
Reverse-complement score agreement is a useful scientific consistency check,
but the two non-palindromic strings remain distinct legal candidates and must
not occupy one submitted slot twice. These are modeling choices, not Dataset
preprocessing or extra information supplied by the default Protocol.

## Offline-Data Protocol

`TFBind8DesignBenchProtocol` has Protocol ID
`design-bench/tfbind8-bottom-percentile-v1`. By default it exposes all canonical
candidates at or below the 50th percentile of `normalized_e_score`:

```python
agent_input = TFBind8DesignBenchProtocol().build_input(dataset)
offline_data = agent_input.data

print(offline_data.column_names)
# ["sequence", "normalized_e_score"]
```

The bundle's `data` is an ordinary Hugging Face `Dataset`, not a new
SciModelingBench Dataset. It contains only `sequence` and the selected target
field. Its `manifest` supplies the public Dataset identity and complete visible
field semantics without forwarding hidden canonical columns.

| Option | Default | Meaning |
|---|---:|---|
| `min_percentile` | `0.0` | Inclusive lower target percentile |
| `max_percentile` | `50.0` | Inclusive upper target percentile |
| `target_field` | `normalized_e_score` | Declared target used for selection and included in output |

Percentiles must be between 0 and 100, and the minimum cannot exceed the
maximum. Selection uses NumPy's linear percentile method, includes values equal
to either threshold, and preserves canonical row order. No randomness or seed
is involved.

For example, a caller can expose the upper half of the unnormalized E-score
distribution:

```python
protocol = TFBind8DesignBenchProtocol(
    min_percentile=50.0,
    max_percentile=100.0,
    target_field="e_score",
)
offline_data = protocol.build_input(dataset, split="six6_ref_r1").data
```

See the [Protocol API](../../api/protocol.md) for the common visibility
boundary.

## Design-Bench Parity

The default Protocol reproduces the historical TFBind8-Exact offline candidate
set after deduplication:

- the historical array has 32,898 visible rows at or below its median;
- 130 of those rows repeat reverse-complement palindromes;
- the canonical Protocol returns 32,768 unique candidates;
- the canonical and historical candidate sets are equal after deduplication.

This preserves which designs are visible without giving palindromic sequences
double training weight. The canonical release also has exact element-wise
parity with the complete historical Design-Bench `x` and `y` arrays before
deduplication: zero mismatched elements and zero maximum absolute target
difference.

## Provenance and Rebuilding

The fixed source archive identity is:

```text
size:   100799246 bytes
sha256: 30778471f1c5167698ac3d2b18fb54098ddaddbaa0550448afb25567e5075231
```

The initial canonical Parquet SHA-256 is:

```text
c9539b5807b151cd0f248d9090053323376cdd38db5a6a0c29afd200d34b7977
```

The release repository stores its complete machine-readable report at
`provenance/tfbind8/six6_ref_r1.json`.

After obtaining the pinned source archive, build an upload-ready repository:

```bash
smb-build-tfbind8 \
  --archive /path/to/TF_binding_landscapes.zip \
  --output-dir artifacts/tfbind8/hf_repo
```

For historical parity verification, also provide the directory containing
`tf_bind_8-x-0.npy` and `tf_bind_8-y-0.npy`:

```bash
smb-build-tfbind8 \
  --archive /path/to/TF_binding_landscapes.zip \
  --legacy-data-dir /path/to/tf_bind_8-SIX6_REF_R1 \
  --output-dir artifacts/tfbind8/hf_repo
```

The builder rejects source identity changes, malformed DNA, broken
reverse-complement pairs, conflicting duplicates, incomplete sequence spaces,
and legacy parity failures.

## Scientific and License Scope

The E-score is a relative enrichment statistic for the `SIX6_REF_R1` PBM
condition. It is not an absolute binding energy and should not be compared
directly across transcription factors without reviewing assay normalization.

Barrera et al. deposited the PBM data in UniPROBE under accession `BAR15A`.
UniPROBE applies a separate academic-use license to files containing 60-mer
probe sequences. This public release contains only derived contiguous 8-mer
observations and uses `license: other`; the package MIT license does not replace
the terms attached to the upstream observations. Users should review the
dataset card and upstream terms before redistribution or commercial use.

## References

- Barrera et al., *Survey of variation in human transcription factors reveals
  prevalent DNA binding changes*, Science (2016),
  [DOI 10.1126/science.aad2257](https://doi.org/10.1126/science.aad2257).
  Accessed 2026-07-16.
- Trabucco et al., *Design-Bench: Benchmarks for Data-Driven Offline Model-Based
  Optimization* (2022), [arXiv:2202.08450](https://arxiv.org/abs/2202.08450).
  Accessed 2026-07-16.
- Design-Bench TFBind8 preprocessing,
  [commit `e52939588421b5433f6f2e9b359cf013c542bd89`](https://github.com/brandontrabucco/design-bench/blob/e52939588421b5433f6f2e9b359cf013c542bd89/process/process_raw_tf_bind_8.py).
  Accessed 2026-07-16.
- Barrera et al. PBM TF binding landscapes,
  [pinned source archive](https://drive.google.com/file/d/1xS6N5qSwyFLC-ZPTADYrxZuPHjBkZCrj/view),
  UniPROBE accession `BAR15A`, archive SHA-256 shown above. Accessed 2026-07-16.
