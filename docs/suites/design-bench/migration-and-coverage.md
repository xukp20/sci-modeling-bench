# Design-Bench Migration and Upstream Coverage

This page records how SciModelingBench maps the historical Design-Bench
scientific families to current integrations. The inventory uses Design-Bench revision
[`e529395`](https://github.com/brandontrabucco/design-bench/tree/e52939588421b5433f6f2e9b359cf013c542bd89)
and covers its 11 non-toy Dataset families, rather than only the eight headline
Tasks in the [Design-Bench paper](https://proceedings.mlr.press/v162/trabucco22a.html).

See the [suite index](README.md) for the concise Task inventory and common API.

## Coverage Decisions

Design-Bench registers multiple learned Oracle architectures for some data
families. This table treats those registrations as variants of one Dataset,
not as independent scientific datasets.

| Original family | Decision | Current setting | Compatibility boundary |
|---|---|---|---|
| TF Bind 8 | Adapted and canonicalized | [TFBind8](tfbind8.md) | The complete measured domain supports exact sequence lookup. The release removes 256 palindrome expansion duplicates, retains distinct reverse-complement candidates, and publishes both E-score scales. |
| TF Bind 10 | Rebuilt from source observations | [TFBind10 Pho4](tfbind10-pho4.md) | The legacy table resolves conflicting replicates by row order and has an inconvenient score direction. The current Objective derives a maximize-oriented score from raw count replicates. |
| NASBench | Adapted and canonicalized | [CellDAG-NAS](cell-dag-nas.md) | Official NASBench-101 records support graph-invariant identity and repeated outcomes. Isomorphic token aliases remain available without becoming distinct architectures. |
| CIFAR-NAS / ResidualConfig-NAS | Excluded | None | The recovered table is dominated by duplicate configurations that cross the score split. Trustworthy labels would require a new multi-seed CIFAR-10 training campaign. |
| Superconductor | Rebuilt as measured-pool ranking | [Superconductor](superconductor.md) | Composition omits structure, phase, processing, and pressure. The Task ranks measured composition groups instead of treating a Random Forest as truth for arbitrary vectors. |
| Hopper Controller | Rebuilt and relabeled | [Hopper Controller](hopper-controller.md) | The meaningful candidates are 3,200 structured checkpoints. Five hundred modern Hopper-v5 rollouts per policy replace historical single-rollout labels. |
| UTR | Rebuilt as measured-pool ranking | [UTR MRL](utr-mrl.md) | The assay measures a finite sequence collection. Source measurements replace the learned ResNet as the trusted evaluator. |
| GFP | Rebuilt at protein identity | [GFP](gfp.md) | The legacy nucleotide-to-protein conversion creates duplicate protein inputs with conflicting labels. The current release uses the author-provided protein aggregate. |
| ChEMBL | Replaced rather than compatibility-ported | [DrugMatrix](drugmatrix.md) | Legacy rows omit treatment context. DrugMatrix restores dose, duration, vehicle, route, sex, study, and controls, so it defines a new candidate space and Task. |
| Ant Morphology | Deferred | None | Most proposals require silent clipping, while labels depend on an incompletely specified controller and obsolete simulator. A valid modern Task requires complete relabeling. |
| D'Kitty Morphology | Deferred | None | It shares the clipping and controller-coverage problems and includes a historical joint-range bug whose correction changes the physical Task. |

`DrugMatrix` is a replacement for the scientific provenance behind the legacy
ChEMBL setting, not a new version of the same candidate space. Other rebuilt
settings document their own score and identity boundaries on their setting
pages. Scores should not be compared directly with legacy learned-oracle
leaderboards unless a page explicitly defines such parity.

## Excluded And Deferred Settings

ResidualConfig-NAS, Ant Morphology, and D'Kitty Morphology are not partial
package features. No public class, optional dependency, or compatibility alias
is provided for them.

Reconsidering one of these settings requires:

1. a reproducible modern data-generation or simulation recipe;
2. a canonical and valid candidate representation;
3. repeated-label or controller-seed stability checks where applicable;
4. a Task difficulty and metric audit; and
5. labels regenerated under the new semantics.

Excluding these settings is preferable to publishing historical behavior under
a misleading exact-evaluator label.
