# Candidate Submission Metrics

Candidate-based Tasks accept an ordered list of proposed solutions and evaluate
their trusted outcomes. Black-box optimization is the first Task family to use
this metric vocabulary, but the same distinctions also apply to candidate
ranking, screening, retrieval, and experimental-prioritization Tasks.

## Submission Contract

A black-box optimization Task has a configured `submission_size` `N`, with a
default of 128, and requires exactly `N` candidates. A candidate-pool ranking
Task interprets the same configuration as the scored prefix `K`: it requires
at least `K` candidates and ignores any suffix after the first `K`. In both
cases position 1 is the candidate the Agent expects to be best.

`submission_size` is selected when the Task is constructed. It is not chosen by
an individual submission, and results produced with different values of `N`
must not share one leaderboard. Concrete Tasks also declare a default primary
metric, while callers may select another supported metric when constructing a
Task variant.

The default summary size is `K = min(5, N)`. Candidate identity is
Task-specific: a DNA sequence may be its own identity, while a graph Task may
use a canonical graph hash. Official set and ranking metrics require `N`
scorable, canonical-unique candidates. Validation diagnostics may still be
returned for malformed, illegal, duplicate, or unscorable candidates, but
silently dropping those candidates would make batch metrics gameable.

## Common Metric Vocabulary

The Task computes the complete metric set. `primary_metric` only
selects which value is exposed through the generic `evaluation.score`; it does
not suppress the other metrics.

| Metric | Definition | Uses submitted order | Direction |
| --- | --- | ---: | --- |
| `best_score` | Best trusted outcome among all `N` submitted candidates | No | Objective direction |
| `rank_1_score` | Trusted outcome of the candidate submitted at position 1 | Yes | Objective direction |
| `best_k_mean` | Mean outcome of the truly best `K` candidates within the submission | No | Objective direction |
| `prefix_k_mean` | Mean outcome of the first `K` submitted candidates | Yes | Objective direction |
| `batch_mean` | Mean trusted outcome of all `N` candidates | No | Objective direction |
| `best_regret` | Gap between the reference optimum and `best_score` | No | Minimize |
| `best_k_mean_regret` | Gap between the reference top-`K` mean and `best_k_mean` | No | Minimize |
| `batch_mean_regret` | Gap between the reference top-`N` mean and `batch_mean` | No | Minimize |
| `normalized_enrichment` | Batch quality normalized between reference-pool random selection and its ideal top-`N` set | No | Maximize |
| `global_ndcg` | Discounted quality of the ordered submission relative to the ideal ordered top-`N` reference candidates | Yes | Maximize |
| `reranking_ndcg` | Discounted ordering quality relative to the ideal reordering of the same submitted candidates | Yes | Maximize |

`best_score` preserves the original Design-Bench top-1 interpretation: it is
the best true outcome anywhere in the submitted set. It must not be confused
with `rank_1_score`, which evaluates the Agent's first prediction. The same
distinction applies to `best_k_mean` and `prefix_k_mean`.

The raw score metrics retain the scientific target's units, such as normalized
E-score, test accuracy, or kelvin. Normalized metrics supplement those values;
they do not replace them.

## Objective Direction

Let `u(y)` orient every objective so that larger utility is better:

```text
u(y) = y   for a maximization objective
u(y) = -y  for a minimization objective
```

Selection, sorting, regret, and ranking calculations operate on `u(y)`. Raw
score metrics continue to report the original target value. Each returned
metric therefore needs its own direction metadata; a single evaluation can
contain maximized scientific scores and minimized regret values.

## Reference-Dependent Metrics

Regret, normalized enrichment, and global NDCG require a versioned reference
domain `P`. The Task must declare its scope:

- `full_domain`: an exhaustively known admissible space, such as all TFBind8
  sequences or all canonical graphs in a frozen NAS table;
- `evaluation_pool`: a frozen hidden measured-candidate pool, such as a
  Superconductor held-out pool;
- `best_known`: a versioned benchmark result that is not a proven optimum.

The scope must appear in evaluation metadata and documentation. Metrics against
an `evaluation_pool` or `best_known` reference must not be described as global
scientific regret.

For reference utilities sorted as
`u*_1 >= ... >= u*_N`, the regrets are:

```text
best_regret        = u*_1 - max_i u_i
best_k_mean_regret = mean(u*_[1:K]) - mean(best_K(u_submission))
batch_mean_regret  = mean(u*_[1:N]) - mean(u_submission)
```

For a finite reference pool, normalized enrichment is:

```text
(mean(u_submission) - mean(u_P))
---------------------------------
(mean(top_N(u_P))   - mean(u_P))
```

Random sampling from `P` has expected enrichment near 0, and the ideal top-`N`
set has enrichment 1. Values below 0 are valid. A Task must not emit this
metric when the denominator is zero.

## Ordered Ranking Metrics

`global_ndcg` combines candidate selection and ordering. Its numerator is the
discounted cumulative gain of the submitted order; its denominator uses the
ideal top-`N` ordering from the declared reference domain.

`reranking_ndcg` isolates ordering. It uses the same numerator, but its
denominator is the ideal ordering of only the submitted candidates. A Task can
therefore distinguish these cases:

- high `reranking_ndcg`, low `global_ndcg`: the Agent orders its candidates
  correctly but selected a weak set;
- high set metrics, low `reranking_ndcg`: the Agent found strong candidates but
  cannot rank them reliably;
- high values for both: the Agent selected and prioritized candidates well.

For a finite reference pool, the implementation orients the target and
linearly normalizes it
between the reference-pool minimum and maximum before applying logarithmic rank
discounts. This keeps gains non-negative while preserving target-value gaps.

## Choosing a Primary Metric

Every common black-box optimization Task reports these metrics, but its default primary metric should
match the capability the Task is intended to test. It should also avoid a
metric on which random or simple baselines are already saturated.

Use these guidelines:

- prefer `best_k_mean` when finding one lucky candidate makes `best_score` too
  noisy or easy, but producing a complete high-quality batch is unnecessarily
  strict;
- prefer `normalized_enrichment` or `batch_mean` when the scientific goal is a
  strong candidate set and submission order is not central;
- prefer `global_ndcg` when the Task explicitly requires both selecting and
  prioritizing candidates;
- retain `best_score` as a secondary compatibility metric for legacy
  Design-Bench comparisons.

Defaults should be selected from frozen random, simple-model, and
strong-baseline results. Changing a default primary metric changes Task
semantics and requires a new Task version even when the Dataset is unchanged.

## Task Defaults

| Task | Submission size | Default primary metric | Reason |
| --- | ---: | --- | --- |
| TFBind8 | 128 | `best_k_mean` | More robust and less easily saturated than finding one high-scoring sequence |
| TFBind10 Pho4 measured-pool screening | 128 | `normalized_enrichment` | Replicate audits favor robust batch quality over noisy single-sequence extremes |
| Superconductor measured-pool ranking | 128 | `global_ndcg` | Best-at-128 is already close to saturation; the Task requires both selection and prioritization |
| CellDAG-NAS | 128 | `best_k_mean` | More repeat-stable than top-1 while remaining focused on finding a small set of strong architectures |
