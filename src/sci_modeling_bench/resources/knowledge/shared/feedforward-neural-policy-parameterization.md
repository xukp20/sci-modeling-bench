# Feedforward Neural Policy Parameterization

## Summary

A feedforward neural policy maps an observation through affine transformations
and nonlinear activations to an action or to parameters of an action
distribution. Its parameter vector consists of weight matrices and bias
vectors, but parameter values are not a unique representation of the computed
function: hidden-unit permutations and, for some activations, coordinated sign
changes can preserve the input–output mapping.

## Scope

### Covered

- Dense layers, weight matrices, biases, and activation functions.
- Multilayer policies that produce action-distribution parameters.
- Flattened parameter counts and the distinction between blocks and matrices.
- Hidden-unit permutation and sign symmetries.

### Not covered

- Exact offsets or byte order for a particular saved controller.
- A universal matrix-flattening convention.
- A method for predicting policy quality from weights.

## Key concepts and notation

| Symbol or term | Meaning |
| --- | --- |
| \(x\in\mathbb{R}^{d_{\mathrm{in}}}\) | Layer input |
| \(W\in\mathbb{R}^{d_{\mathrm{in}}\times d_{\mathrm{out}}}\) | Weight matrix under a row-vector convention |
| \(b\in\mathbb{R}^{d_{\mathrm{out}}}\) | Bias vector |
| \(\phi\) | Elementwise activation function |
| \(h=\phi(xW+b)\) | Dense-layer output |
| hidden unit | Intermediate coordinate without a fixed external physical identity |

## Core knowledge

### Affine transformations and nonlinearities

Under a row-vector convention, a dense layer computes

\[
z=xW+b,\qquad h=\phi(z).
\]

An equivalent column-vector convention writes \(z=Wx+b\) and stores the
transpose-shaped matrix. Both are common. Matrix shape and multiplication
convention must therefore be known before individual flattened weights can be
assigned input and output meanings [1].

For an \(m\)-input, \(n\)-output dense layer, the number of scalar parameters
is

\[
mn+n,
\]

including the bias. Layer widths and the declared order of parameter blocks
therefore determine block lengths, even though they do not by themselves
determine how each matrix was flattened.

### Multilayer neural policy

A two-hidden-layer policy can be written as

\[
h_1=\phi_1(oW_1+b_1),
\]

\[
h_2=\phi_2(h_1W_2+b_2),
\]

\[
u=h_2W_3+b_3.
\]

The output \(u\) can be an action directly or a parameter such as the mean of
a stochastic action distribution. Additional standalone parameters can
represent quantities such as action log standard deviations.

### Hyperbolic tangent activation

The hyperbolic tangent is

\[
\tanh z=\frac{e^z-e^{-z}}{e^z+e^{-z}},
\]

with range \((-1,1)\). It is odd:

\[
\tanh(-z)=-\tanh(z).
\]

Large-magnitude preactivations lie in saturated regions where the output is
close to \(+1\) or \(-1\), while values near zero are approximately linear.
These are properties of the activation, not guarantees about the behavior of
a complete closed-loop controller.

### Hidden-unit permutation symmetry

Hidden coordinates do not have an externally fixed order. If a permutation
is applied to the outputs of one hidden layer and the inverse-compatible
permutation is applied to the inputs of the following layer, the overall
network function is unchanged [2].

Consequently, two parameter vectors can be far apart in ordinary Euclidean
distance while computing the same function. Conversely, similar weight
statistics do not guarantee similar functions.

### Sign symmetry for odd activations

For an odd activation such as `tanh`, changing the sign of all incoming
weights and the bias of one hidden unit changes the sign of its activation.
Changing the signs of that unit's outgoing weights at the same time cancels
the change. This gives another family of functionally equivalent parameter
representations.

Such symmetries concern coordinated transformations. Arbitrarily changing
individual signs generally changes the network.

### Flattening is serialization

A matrix can be flattened row by row, column by column, or according to a
framework-specific tensor layout. Concatenating multiple weights and biases
adds a second ordering choice. These are serialization conventions rather
than mathematical properties of a feedforward network.

## Conditions, limitations, and uncertainty

- Layer widths determine parameter counts but not the storage order inside a
  matrix block.
- Biases, observation preprocessing, and output transformations are part of
  the policy function and cannot be ignored.
- Weight magnitude is not a coordinate-invariant measure of policy behavior.
- Neural-network symmetries create exact equivalences, while many other
  different parameterizations may be only approximately behaviorally similar.
- Closed-loop behavior also depends on the environment dynamics and the
  distribution of observations encountered.

## Related knowledge resources

- `continuous_control_and_gaussian_policies`: interpretation of policy outputs.
- `proximal_policy_optimization_and_policy_checkpoints`: how policy parameters may be learned.
- `hopper_locomotion_and_mujoco_dynamics`: an example of closed-loop physical control.

## References

1. Goodfellow I, Bengio Y, Courville A. Deep feedforward networks. In: *Deep Learning*. MIT Press; 2016. https://www.deeplearningbook.org/contents/mlp.html. [Textbook]
2. Brea J, Simsek B, Illing B, Gerstner W. Weight-space symmetry in deep networks gives rise to permutation saddles, connected by equal-loss valleys across the loss landscape. *arXiv*. 2019. https://arxiv.org/abs/1907.02911. [Primary theory]
