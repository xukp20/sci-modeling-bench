# Stochastic Neural-Network Training and Repeated Evaluation

## Summary

Training the same neural architecture repeatedly can produce different learned
weights and evaluation scores. Variation arises from parameter initialization,
data order, data augmentation, stochastic optimization, and implementation
details. Repeated runs sample a performance distribution; their mean,
standard deviation, and standard error describe different properties and
cannot be treated as independent architectures.

## Scope

### Covered

- Sources of randomness in neural-network training.
- Repeated training runs and summary statistics.
- Train, validation, and test roles.
- Failed or atypical runs and protocol dependence.

### Not covered

- The repeat count or outcomes of a particular dataset.
- A rule for discarding runs or selecting architectures.
- A universal probability model for training outcomes.

## Core knowledge

### Sources of run-to-run variation

Random initialization changes the starting weights. Mini-batch sampling and
ordering change the sequence of gradient estimates. Random data augmentation,
dropout, and other stochastic regularization add further variation.
Parallel kernels and numerical libraries can introduce implementation-level
nondeterminism even when user-visible seeds are fixed [1,2].

These sources interact with optimization. Two runs of the same architecture
can enter different regions of parameter space, converge at different rates,
or occasionally fail to reach the usual training regime.

### Repeated-run statistics

For scores \(Y_1,\ldots,Y_n\) from independently trained instances of one
architecture, the arithmetic mean is

\[
\bar Y=\frac{1}{n}\sum_{i=1}^{n}Y_i,
\]

and the sample standard deviation is

\[
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(Y_i-\bar Y)^2}.
\]

The mean estimates expected score under the sampled training procedure.
Standard deviation describes run-to-run dispersion. Under independent,
representative runs with finite variance, \(s/\sqrt n\) estimates the standard
error of the mean. With few repeats, both the distribution shape and its
variance are uncertain [3].

The median estimates a different center and is less sensitive to an extreme
run. Replacing a mean by a median changes the estimand; neither is universally
correct without specifying the scientific question.

### Architecture and run are different units

An architecture is a structural specification. Each independent training run
instantiates and optimizes new weights for that structure. Multiple runs add
evidence about one architecture's training distribution; they do not enlarge
the set of distinct architectures.

Likewise, multiple serialized representations of the same computation graph
are not training repeats. Representation multiplicity and experimental
replication are separate concepts.

### Training, validation, and test measurements

Training metrics measure performance on examples used for weight updates.
Validation metrics support choices that are not learned directly from training
examples, such as architecture or stopping decisions. Test metrics estimate
performance after those choices are fixed. Repeatedly choosing candidates
using test results makes the test set part of the selection process.

High training accuracy does not guarantee validation or test accuracy.
Conversely, a poor training metric can indicate optimization failure rather
than the representational limit of the architecture.

### Atypical and failed runs

Training-score distributions can be skewed or multimodal. One mode may
correspond to ordinary convergence and another to numerical instability,
optimization failure, or a qualitatively different solution. Whether such
runs belong in the target depends on the declared training procedure and
estimand. Removing them after observing outcomes can bias results unless the
rule is defined independently.

## Conditions, limitations, and uncertainty

- Equal random seeds do not guarantee bitwise determinism across hardware,
  library versions, or parallel execution.
- A small number of repeats cannot reliably characterize tails or multimodal
  outcome distributions.
- Standard error describes uncertainty in a mean under sampling assumptions,
  not the variability of an individual future run.
- Differences among runs may reflect both algorithmic randomness and changing
  software or data pipelines.
- Performance distributions are conditional on architecture, data, training
  recipe, budget, and implementation.

## Related knowledge resources

- `neural_architecture_search_spaces_and_performance_evaluation`: performance
  estimates used during architecture search.
- `directed_acyclic_computation_graphs_and_graph_isomorphism`: distinction
  between structural aliases and experimental repeats.

## References

1. Zhuang D, Zhang X, Song SL, Hooker S. Randomness in neural network
   training: Characterizing the impact of tooling. *Proceedings of Machine
   Learning and Systems*. 2022;4.
   https://proceedings.mlsys.org/paper_files/paper/2022/hash/427e0e886ebf87538afdf0badb805b7f-Abstract.html
   [Primary empirical research]
2. Goodfellow I, Bengio Y, Courville A. Optimization for training deep models.
   In: *Deep Learning*. MIT Press; 2016.
   https://www.deeplearningbook.org/contents/optimization.html [Textbook]
3. Bouthillier X, Delaunay P, Bronzi M, et al. Accounting for variance in
   machine learning benchmarks. *Proceedings of Machine Learning and Systems*.
   2021;3. https://arxiv.org/abs/2103.03098 [Primary empirical research]
