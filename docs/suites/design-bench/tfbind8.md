# TFBind8 Black-Box Optimization

TFBind8 is the first end-to-end black-box optimization support in
SciModelingBench. It combines:

- `TFBind8Dataset`, a canonical and validated DNA 8-mer binding landscape;
- `TFBind8DesignBenchProtocol`, a deterministic offline-data view compatible
  with the Design-Bench TFBind8-Exact setting at the candidate-set level;
- `TFBind8ExactObjective`, a trusted exact lookup for candidate evaluation.

This release provides the data, visibility, and evaluation primitives. It does
not provide a Task object, optimization agent, benchmark runner, query-budget
enforcement, submission format, or metrics.

## End-to-End Use

```python
from sci_modeling_bench.suites.design_bench import (
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
    TFBind8ExactObjective,
)

REVISION = "2ee2856f4255bb6a64c11b6c2660a6f41418e654"

# Trusted benchmark state
dataset = TFBind8Dataset.from_hub(revision=REVISION)
protocol = TFBind8DesignBenchProtocol()
objective = TFBind8ExactObjective(dataset)

# The external agent receives only this object.
offline_data = protocol.build_input(dataset)

# A candidate returned to the trusted harness is evaluated exactly.
candidate = {"sequence": "AACCGGTT"}
scores = objective.evaluate(candidate)
# {"e_score": ..., "normalized_e_score": ...}
```

In a black-box run, keep `dataset` and `objective` on the trusted side. The
complete TFBind8 table is publicly available, so this integration is a
reproducible reference task rather than a secrecy- or contamination-resistant
benchmark. A harness that wants to simulate hidden evaluation must isolate the
agent from the full Hugging Face cache and external network access, and must
enforce its own query budget or feedback policy.

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

The raw E-score remains float64 so normalization can be reproduced from the
published decimals. The normalized score is float32 for exact parity with the
historical Design-Bench target array.

`TFBind8Validator` checks the full canonical artifact for column order, 65,536
unique sequences, complete `4^8` coverage, deterministic `A<C<G<T` order,
finite scores, reverse-complement score agreement, and exact float32
normalization.

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

## Offline-Data Protocol

`TFBind8DesignBenchProtocol` has Protocol ID
`design-bench/tfbind8-bottom-percentile-v1`. By default it exposes all canonical
candidates at or below the 50th percentile of `normalized_e_score`:

```python
offline_data = TFBind8DesignBenchProtocol().build_input(dataset)

print(offline_data.column_names)
# ["sequence", "normalized_e_score"]
```

The return value is an ordinary Hugging Face `Dataset`, not a new
SciModelingBench Dataset. It contains only `sequence` and the selected target
field.

| Option | Default | Meaning |
|---|---:|---|
| `min_percentile` | `0.0` | Inclusive lower target percentile |
| `max_percentile` | `50.0` | Inclusive upper target percentile |
| `target_field` | `normalized_e_score` | Declared target used for selection and included in output |

Percentiles must be between 0 and 100, and the minimum cannot exceed the
maximum. Selection uses NumPy's linear percentile method, includes values equal
to either threshold, and preserves canonical row order. No randomness or seed
is involved.

For example, a caller can expose the upper half of the raw E-score distribution:

```python
protocol = TFBind8DesignBenchProtocol(
    min_percentile=50.0,
    max_percentile=100.0,
    target_field="e_score",
)
offline_data = protocol.build_input(dataset, split="six6_ref_r1")
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

## Canonicalization

The published source table contains 32,896 rows. Each row holds an 8-mer, its
reverse complement, and their shared E-score. Concatenating both sequence
columns yields 65,792 historical rows. The canonical builder:

1. validates every sequence and reverse-complement pair;
2. expands both sequence columns with their shared E-score;
3. removes the 256 exact repeats created by reverse-complement palindromes;
4. retains non-palindromic reverse complements as separate candidates;
5. verifies complete coverage of all `4^8` legal sequences;
6. sorts sequences deterministically using `A<C<G<T`;
7. min-max normalizes E-score and stores the result as float32.

The resulting Parquet has no duplicate sequences, conflicting labels, missing
8-mers, NaN values, or infinite values.

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
