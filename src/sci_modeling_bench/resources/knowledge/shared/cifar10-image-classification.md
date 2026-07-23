# CIFAR-10 Image Classification

## Summary

CIFAR-10 is a labeled image-classification dataset containing 60,000
\(32\times32\) RGB images in ten mutually exclusive object classes. Its
official partition contains 50,000 training images and 10,000 test images.
The small spatial resolution makes fine object detail limited, and measured
accuracy remains conditional on the chosen training, validation, preprocessing,
and evaluation protocol.

## Scope

### Covered

- CIFAR-10 image dimensions, classes, and official partitions.
- The multiclass classification objective.
- Finite-test-set accuracy and common interpretation limits.

### Not covered

- A particular neural architecture or training recipe.
- A benchmark-specific training/validation split.
- Current state-of-the-art results or architecture rankings.

## Key concepts and notation

| Term | Meaning |
| --- | --- |
| RGB image | Three-channel red, green, and blue pixel array |
| class label | One of ten object categories assigned to an image |
| top-1 accuracy | Fraction whose highest-scoring predicted class is correct |
| training set | Images available for fitting model parameters |
| test set | Held-out images used for final assessment under a protocol |

## Core knowledge

### Dataset composition

CIFAR-10 contains 6,000 images from each of ten classes: airplane, automobile,
bird, cat, deer, dog, frog, horse, ship, and truck. There are 50,000 training
images and 10,000 test images, and each image has \(32\times32\) color pixels
[1,2].

The images were derived from the Tiny Images collection and labeled for the
CIFAR datasets. Their low resolution means that an object occupies relatively
few pixels and can have substantial background, pose, and appearance variation
[2].

### Multiclass classification

For a classifier producing class scores \(z_1,\ldots,z_{10}\), a top-1
prediction is

\[
\hat y=\operatorname*{arg\,max}_{c} z_c.
\]

Given \(N\) labeled examples, empirical top-1 accuracy is

\[
\widehat{\mathrm{acc}}
=\frac{1}{N}\sum_{i=1}^{N}\mathbf 1[\hat y_i=y_i].
\]

Accuracy weights every test image equally. It does not show which classes are
confused, how calibrated probabilities are, or whether mistakes concentrate
in particular visual subgroups.

### Spatial resolution and convolutional processing

At \(32\times32\) resolution, each downsampling step removes a substantial
fraction of spatial positions. Local convolution and pooling can build
increasingly abstract features, but padding, stride, and the number of
resolution changes determine how much spatial information remains.

Image resolution alone does not determine the appropriate network. Channel
width, receptive field, nonlinearities, normalization, regularization, and
optimization also affect learned representations.

### Evaluation partitions

The official dataset supplies training and test partitions. Many experiments
derive a validation subset from the training data for model or architecture
selection. The exact validation construction is an experimental protocol and
should be reported because it changes how many images are used for fitting and
selection.

The test set is finite. Conditional on a fixed set of predictions, empirical
accuracy is an estimate of performance on the test examples, not an exact
property of all possible images from the underlying task distribution.

## Conditions, limitations, and uncertainty

- CIFAR-10 labels represent broad object categories and do not describe
  attributes, localization, or multiple objects.
- The low resolution differs from many modern high-resolution vision tasks.
- Accuracy depends on preprocessing, augmentation, training budget, and the
  precise model-selection protocol.
- Repeated use of the public test set for selection can adapt research choices
  to that set.
- Performance on CIFAR-10 does not guarantee the same ordering on another
  dataset, resolution, or distribution.

## Related knowledge resources

- `convolutional_feature_maps_kernels_and_receptive_fields`: spatial processing
  of RGB feature maps.
- `stochastic_neural_network_training_and_repeated_evaluation`: uncertainty
  across independent training runs.

## References

1. University of Toronto. CIFAR-10 and CIFAR-100 datasets. Accessed
   2026-07-23. https://www.cs.toronto.edu/~kriz/cifar.html
   [Official dataset page]
2. Krizhevsky A. *Learning Multiple Layers of Features from Tiny Images*.
   University of Toronto technical report; 2009.
   https://www.cs.toronto.edu/~kriz/learning-features-2009-TR.pdf
   [Dataset technical report]
