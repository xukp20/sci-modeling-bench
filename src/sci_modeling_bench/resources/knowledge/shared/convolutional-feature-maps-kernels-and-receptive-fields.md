# Convolutional Feature Maps, Kernels, and Receptive Fields

## Summary

A convolutional layer applies shared kernels across spatial locations to
produce output feature maps. Kernel size, stride, dilation, padding, input
channels, and output channels determine spatial dimensions, parameter count,
and the theoretical receptive field. A \(1\times1\) convolution mixes channels
at each location, whereas a \(3\times3\) convolution also combines neighboring
spatial positions.

## Scope

### Covered

- Two-dimensional convolution and feature-map channels.
- Kernel size, stride, padding, dilation, and output shape.
- Parameter counts for dense convolutional kernels.
- Theoretical receptive fields and stacked convolutions.

### Not covered

- The operation vocabulary of a particular architecture space.
- A claim that one kernel size is universally more accurate.
- A procedure for selecting or fitting neural architectures.

## Key concepts and notation

| Symbol | Meaning |
| --- | --- |
| \(H,W\) | Input height and width |
| \(C_{\mathrm{in}},C_{\mathrm{out}}\) | Input and output channel counts |
| \(k\) | Square kernel width |
| \(s,p,d\) | Stride, padding, and dilation |
| feature map | Spatial array associated with one channel |
| receptive field | Input region capable of affecting an output unit |

## Core knowledge

### Multi-channel convolution

For an input tensor \(X\), a convolutional output can be written

\[
Y_{i,j,c_o}
= b_{c_o}
+ \sum_{u,v,c_i}
K_{u,v,c_i,c_o}\,
X_{i s+u,\,j s+v,\,c_i},
\]

with indexing adjusted for padding and dilation. Weight sharing means the same
kernel coefficients are applied at different spatial positions. This gives
translation-equivariant linear processing away from boundary and sampling
effects [1,2].

A dense \(k\times k\) convolution with bias has

\[
k^2 C_{\mathrm{in}}C_{\mathrm{out}}+C_{\mathrm{out}}
\]

trainable scalar parameters. Computation also depends on output spatial size,
so parameter count and operation count are distinct quantities.

### Spatial output dimensions

For one spatial dimension, the common output-size formula is

\[
H_{\mathrm{out}}
=
\left\lfloor
\frac{H+2p-d(k-1)-1}{s}+1
\right\rfloor.
\]

The same relationship applies to width. Padding can preserve spatial extent,
stride can subsample it, and dilation spaces kernel elements farther apart
[1]. Framework conventions determine asymmetric padding and rounding details.

### One-by-one convolution

A \(1\times1\) convolution applies a learned linear transformation across
channels independently at every spatial position. It does not expand the
spatial receptive field when stride is one, but it can change channel count,
combine channel information, and introduce a new nonlinearity when followed by
an activation [3].

### Three-by-three convolution

A \(3\times3\) convolution combines each location with a local spatial
neighborhood as well as mixing channels. With unit stride and suitable
padding, it preserves spatial dimensions. Relative to a \(1\times1\)
convolution at equal channel counts, it has nine times as many kernel weights.

Stacking two unit-stride \(3\times3\) convolutions gives a theoretical
\(5\times5\) receptive field; a third gives \(7\times7\), assuming no dilation
and ignoring boundaries. Nonlinearities between layers make the stack
different from one larger linear convolution.

### Theoretical and effective receptive fields

The theoretical receptive field is determined by connectivity, kernel sizes,
strides, and dilation. It states which input positions can affect an output.
The effective influence of those positions after training can be highly
nonuniform and is not specified by theoretical size alone.

## Conditions, limitations, and uncertainty

- Output shape depends on the precise padding and rounding convention.
- Boundary positions do not have the same input neighborhood as interior
  positions when padding is used.
- Parameter count does not determine accuracy, latency, memory traffic, or
  optimization difficulty by itself.
- A larger theoretical receptive field does not guarantee that distant input
  pixels materially affect a trained output.
- Convolutional layers also depend on normalization, activation, initialization,
  and the surrounding graph.

## Related knowledge resources

- `pooling_branching_and_feature_aggregation`: non-convolutional spatial
  aggregation and graph merges.
- `cell_based_convolutional_neural_networks`: convolutional operations inside
  reusable cells.

## References

1. Dumoulin V, Visin F. A guide to convolution arithmetic for deep learning.
   *arXiv*. 2016. https://arxiv.org/abs/1603.07285 [Technical guide]
2. Goodfellow I, Bengio Y, Courville A. Convolutional networks. In:
   *Deep Learning*. MIT Press; 2016.
   https://www.deeplearningbook.org/contents/convnets.html [Textbook]
3. Lin M, Chen Q, Yan S. Network in network. *International Conference on
   Learning Representations*. 2014. https://arxiv.org/abs/1312.4400
   [Primary research]
