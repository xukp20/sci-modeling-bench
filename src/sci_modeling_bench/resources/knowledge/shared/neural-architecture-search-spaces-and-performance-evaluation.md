# Neural Architecture Search Spaces and Performance Evaluation

## Summary

Neural architecture search (NAS) treats neural-network structure as an
optimization variable. A NAS system is characterized by its search space,
search strategy, and performance-estimation strategy. Architecture performance
is conditional on the dataset, training pipeline, resource budget, and
evaluation protocol; tabular and surrogate benchmarks approximate expensive
training under explicitly frozen conditions.

## Scope

### Covered

- Search spaces, search strategies, and performance estimation.
- Architecture variables versus training hyperparameters and weights.
- Full training, proxy, weight-sharing, tabular, and surrogate evaluation.
- Protocol dependence, ranking, and reproducibility.

### Not covered

- A recommended NAS algorithm or search workflow.
- A particular benchmark's hidden table, candidate rankings, or budget.
- A claim that benchmark performance transfers unchanged to another setting.

## Key concepts and notation

| Term | Meaning |
| --- | --- |
| search space \(\mathcal A\) | Set of representable architectures |
| search strategy | Rule that selects architectures from \(\mathcal A\) |
| performance estimator | Procedure returning evidence about an architecture |
| tabular benchmark | Stored evaluations for a finite architecture set |
| surrogate benchmark | Learned approximation to an evaluation process |
| fidelity | Training or data budget used to estimate final performance |

## Core knowledge

### Three components of NAS

NAS research is commonly organized around three coupled components: the search
space defines possible architectures, the search strategy chooses among them,
and the performance-estimation strategy supplies feedback [1]. A change to any
component changes the optimization problem.

Architecture variables can include operation types, graph connections, layer
widths, and repeated motifs. Training hyperparameters such as learning rate or
optimizer are logically distinct, although some systems optimize both.
Numerical network weights are learned conditional on the architecture and
training procedure.

### Performance estimation

Training every candidate to completion is expensive. Performance can instead
be estimated by shorter training, reduced data, lower resolution, inherited or
shared weights, learning-curve extrapolation, or a predictive surrogate [1].
Each estimator introduces its own bias, variance, and possible change in
architecture ranking.

A validation set is conventionally used for architecture selection, while a
held-out test set is reserved for final assessment. Reusing test outcomes for
iterative selection changes the statistical role of the test set.

### Tabular and surrogate benchmarks

A tabular NAS benchmark stores evaluations of architectures under a fixed
training and evaluation pipeline. Lookup makes repeated search experiments
fast and reproducible, and exhaustive tables can identify graph duplicates
before storage. NAS-Bench-101 established this approach for a finite CNN cell
space [2].

The table does not define intrinsic architecture quality. It records outcomes
under its dataset, macro-architecture, optimizer, schedule, regularization,
hardware implementation, and random trials. A surrogate benchmark extends
coverage by predicting outcomes for architectures not all evaluated
exhaustively, adding model error to the benchmark.

### Accuracy, rank, and resource objectives

Architecture comparisons may target validation accuracy, test accuracy,
training time, parameter count, floating-point operations, latency, memory, or
multiple objectives. Two architectures can exchange order when the objective,
training budget, hardware, or data changes.

Absolute performance prediction and ranking are different statistical tasks.
An estimator with biased absolute values can still preserve ordering, while a
small absolute error can disrupt rankings when architecture scores are tightly
clustered.

### Reproducible comparison

Meaningful NAS comparisons require the search space, available observations,
training pipeline, total search cost, final evaluation procedure, and random
repeats to be reported. Best-practice guidance emphasizes separating the cost
of search from the cost and protocol of final architecture evaluation [3].

## Conditions, limitations, and uncertainty

- A finite tabular benchmark cannot evaluate architectures outside its frozen
  space.
- Proxy and weight-sharing rankings need not match independent full training.
- Results depend on the macro-architecture and training recipe as well as the
  searched cell.
- Selecting the maximum from many noisy estimates introduces winner's-curse
  and multiple-comparison effects.
- Hardware-neutral counts such as parameters or FLOPs do not uniquely
  determine measured latency or energy.
- Reproducibility within a frozen benchmark does not establish external
  validity on other datasets or modern training pipelines.

## Related knowledge resources

- `cell_based_convolutional_neural_networks`: one common class of NAS search
  space.
- `stochastic_neural_network_training_and_repeated_evaluation`: uncertainty in
  performance estimates.

## References

1. Elsken T, Metzen JH, Hutter F. Neural architecture search: A survey.
   *Journal of Machine Learning Research*. 2019;20(55):1–21.
   https://www.jmlr.org/papers/v20/18-598.html [Review]
2. Ying C, Klein A, Christiansen E, Real E, Murphy K, Hutter F.
   NAS-Bench-101: Towards reproducible neural architecture search. *Proceedings
   of Machine Learning Research*. 2019;97:7105–7114.
   https://proceedings.mlr.press/v97/ying19a.html [Primary research]
3. Lindauer M, Hutter F. Best practices for scientific research on neural
   architecture search. *Journal of Machine Learning Research*.
   2020;21(243):1–18.
   https://www.jmlr.org/papers/v21/20-056.html [Methodological review]
