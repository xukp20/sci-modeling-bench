# Changelog

All notable changes to SciModelingBench are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-17

### Added

- Pho4 TFBind10 Dataset preserving 4,160,533 published BET-seq count,
  fraction, and observed-ddG rows across four replicates for the complete DNA
  10-mer space, with a reproducible Figshare builder and vectorized validator.
- Count-grounded Pho4 posterior affinity Objective, lower-half raw-observation
  Protocol, label-hidden upper-half candidate pool, and 128-candidate Task with
  `normalized_enrichment` as the default primary metric.
- Canonical Superconductor Dataset with all 21,263 UCI source measurements
  preserved across 15,164 normalized composition groups, published descriptor
  features, deterministic provenance, and a reproducible data builder.
- Superconductor lower-temperature observation Protocol, measured group-median
  Objective, and ordered hidden-pool optimization Task with `global_ndcg` as
  its default primary metric.
- Shared candidate metrics covering raw candidate quality, regret, normalized
  enrichment, global NDCG, and within-submission reranking NDCG.
- Canonical CellDAG-NAS integration for NASBench-101 with graph-aware
  validation, all token aliases, three raw 108-epoch training repeats, a
  low-40%-canonical offline Protocol, exact canonical Objective, and
  duplicate-aware 128-candidate Task evaluation.
- Reproducible `smb-build-cell-dag-nas` data builder with official TFRecord
  verification and exact parity checks against Design-Bench processed scores.

### Changed

- Objectives may declare derived output fields that are not persisted Dataset
  targets, enabling trusted aggregation of replicate observations without
  exposing evaluator labels in offline data.
- **Breaking:** black-box optimization Tasks now require ordered,
  canonical-unique submissions, allow `submission_size` and `primary_metric` to
  be configured at construction, and return the complete common metric set.
  Invalid or duplicate candidate batches retain diagnostics but no longer
  receive fabricated aggregate scores. Migrate a legacy submission by ranking
  it in descending predicted quality, canonicalizing and deduplicating it
  before submission, and reading the selected `primary_metric` from
  `evaluation.score` or the full `evaluation.metrics` mapping.
- **Breaking:** TFBind8 now uses `best_k_mean` as its default primary metric;
  `best_score` remains available for best-of-submission reporting. Existing
  top-1 comparisons should use `evaluation.metrics["best_score"]`; callers
  that require the former default score can construct the Task with
  `primary_metric="best_score"`.
- CellDAG-NAS now uses the shared candidate evaluation contract with canonical
  graph identity, `best_k_mean` as its default primary metric, a `full_domain`
  reference, and the complete common score and regret metric set.

### Known Limitations

- Dataset artifacts and upstream benchmark tables are public. Task APIs define
  a trusted evaluation boundary but do not prevent external lookup; controlled
  agent evaluations still require an external isolation and feedback harness.

## [0.2.0] - 2026-07-16

### Added

- Generic `Task`, `ObjectiveBackedTask`, and structured submission-evaluation
  contracts without requiring every Task to use an Objective.
- Design-Bench-compatible black-box optimization evaluation for fixed
  128-candidate submissions, with separate submission and candidate validation,
  per-candidate diagnostics, and top-1 normalized scoring.
- Default `TFBind8BlackBoxOptimizationTask` composition of the canonical
  Dataset, bottom-50% Protocol, and exact Objective.

## [0.1.0] - 2026-07-16

### Added

- Initial Python 3.10+ package with typed public exports.
- Core Dataset framework for resolving Hugging Face revisions to immutable
  commits, selecting collection configs and splits, loading regular or
  streaming datasets, and checking declared schemas and row counts.
- Strict collection and dataset manifests with provenance metadata, semantic
  input, target, and context fields, common constraints, and split metadata.
- Structured validation reports and dataset-specific validator hooks that
  report violations without mutating observations or candidates.
- Read-only, lazily loaded Knowledge resources pinned to the Dataset revision.
- Minimal Objective and Protocol contracts for validated target evaluation and
  construction of agent-visible inputs.
- One black-box optimization integration for TFBind8 `SIX6_REF_R1`, including
  the complete canonical 65,536-sequence landscape, exact E-score lookup, and
  a Design-Bench-compatible bottom-50% Protocol exposing 32,768 unique offline
  candidates.
- Reproducible TFBind8 release builder and `smb-build-tfbind8` command with
  source checks, canonicalization, integrity validation, provenance output,
  and optional parity checks against legacy Design-Bench arrays.
- Public documentation for the framework concepts and TFBind8 integration.

### Known Limitations

- Dataset, Objective, and Protocol interfaces remain experimental, and a Task
  or evaluation-harness interface is not included in this release.
- Dataset artifacts are distributed separately from the Python package and
  retain their own source, citation, provenance, and license metadata.

[Unreleased]: https://github.com/xukp20/sci-modeling-bench/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/xukp20/sci-modeling-bench/releases/tag/v0.1.0
