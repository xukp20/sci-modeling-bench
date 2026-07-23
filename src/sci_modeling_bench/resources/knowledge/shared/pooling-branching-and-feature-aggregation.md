# Pooling, Branching, and Feature Aggregation

## Summary

Pooling summarizes local spatial neighborhoods without a learned convolutional
kernel. Branching computation graphs process one tensor along multiple paths,
and merge operations combine the resulting tensors by summation,
concatenation, or another declared operation. These choices affect spatial
resolution, channel count, path length, information flow, and tensor-shape
requirements.

## Scope

### Covered

- Max pooling and its spatial arithmetic.
- Parallel branches and reconvergent computation paths.
- Elementwise summation and channel concatenation.
- Identity and residual connections as a general graph pattern.

### Not covered

- The precise merge convention of a particular benchmark.
- A ranking of graph motifs or operations.
- A search or feature-engineering strategy.

## Core knowledge

### Max pooling

For a window \(\mathcal W_{ij}\) in one channel, max pooling produces

\[
Y_{i,j,c}=\max_{(u,v)\in\mathcal W_{ij}} X_{u,v,c}.
\]

Pooling is applied independently to channels in its common form. It has no
trainable kernel coefficients, but kernel size, stride, padding, and tie
handling remain part of the operation. A stride larger than one reduces
spatial resolution; unit stride can preserve it with appropriate padding
[1,2].

Max pooling is nonlinear. It retains the maximum activation within a local
window and discards the exact locations and values of non-maximal entries.
This can provide limited local invariance but also loses information.

### Parallel branches

A branching graph sends one tensor through multiple operation sequences.
Branches can differ in depth, receptive field, parameter count, or nonlinear
transformation. Reconvergence makes information from several paths available
to a later computation. Inception modules are a published example of
parallel convolution and pooling branches followed by feature concatenation
[3].

### Elementwise summation

For tensors \(X_1,\ldots,X_m\), an elementwise merge is

\[
Y=\sum_{r=1}^{m}X_r.
\]

The tensors must have compatible shapes and coordinate meanings. Summation
preserves the common output shape and mixes contributions in the same channel
coordinates. It does not preserve each branch as a separately addressable
channel block.

### Concatenation

Channel concatenation writes

\[
Y=\operatorname{concat}(X_1,\ldots,X_m)
\]

along the channel axis. Spatial dimensions must agree, while output channel
count is the sum of branch channel counts. Concatenation preserves branch
features as distinct coordinates but can increase the width and cost of later
operations.

### Identity and residual paths

An identity connection carries \(x\) without a learned transformation.
A residual block combines it with a learned branch,

\[
y=F(x)+x,
\]

when shapes are compatible. Residual connections create shorter computational
and gradient paths in addition to the transformed path. The ResNet study
showed that this parameterization can make substantially deeper networks
easier to optimize, but it does not imply that every added edge or short path
improves every architecture [4].

## Conditions, limitations, and uncertainty

- Branch outputs can be merged only under the declared shape and channel
  semantics; graph connectivity alone is insufficient.
- Pooling behavior depends on stride, padding, window size, and framework
  conventions.
- Summation and concatenation are not interchangeable and change downstream
  channel semantics.
- More paths can add redundancy or capacity, but can also add computation and
  correlated features.
- Residual-learning results obtained in one macro-architecture and training
  regime are not a universal ordering over arbitrary graph motifs.

## Related knowledge resources

- `convolutional_feature_maps_kernels_and_receptive_fields`: tensor operations
  placed on computation paths.
- `directed_acyclic_computation_graphs_and_graph_isomorphism`: structural
  meaning of branches and merges.

## References

1. Goodfellow I, Bengio Y, Courville A. Convolutional networks. In:
   *Deep Learning*. MIT Press; 2016.
   https://www.deeplearningbook.org/contents/convnets.html [Textbook]
2. Dumoulin V, Visin F. A guide to convolution arithmetic for deep learning.
   *arXiv*. 2016. https://arxiv.org/abs/1603.07285 [Technical guide]
3. Szegedy C, Liu W, Jia Y, et al. Going deeper with convolutions.
   *Proceedings of the IEEE Conference on Computer Vision and Pattern
   Recognition*. 2015:1–9.
   https://arxiv.org/abs/1409.4842 [Primary research]
4. He K, Zhang X, Ren S, Sun J. Deep residual learning for image recognition.
   *Proceedings of the IEEE Conference on Computer Vision and Pattern
   Recognition*. 2016:770–778.
   https://openaccess.thecvf.com/content_cvpr_2016/html/He_Deep_Residual_Learning_CVPR_2016_paper.html
   [Primary research]
