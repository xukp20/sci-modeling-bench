# Stochastic Rollout Evaluation and Uncertainty

## Summary

A rollout return from a stochastic policy or environment is one draw from a
performance distribution. Repeated rollouts estimate quantities such as the
expected return, variability, failure probability, and episode duration.
Means, medians, standard deviations, and standard errors answer different
questions, and paired random-number designs can change the uncertainty of
comparisons without changing each policy's marginal return distribution.

## Scope

### Covered

- Repeated rollout returns and Monte Carlo estimates.
- Mean, median, sample standard deviation, and standard error.
- Heavy tails, heteroscedasticity, and outcome modes.
- Paired seeds and common random numbers.
- Episode lengths and termination indicators as associated outcomes.

### Not covered

- A fixed number of repeats for a particular dataset.
- A query strategy or model-validation workflow.
- A claim that one summary statistic is universally preferable.

## Key concepts and notation

| Symbol or term | Meaning |
| --- | --- |
| \(R_i\) | Return from rollout \(i\) |
| \(n\) | Number of repeated rollouts |
| \(\bar R\) | Arithmetic sample mean |
| \(s_R\) | Sample standard deviation |
| \(\mathrm{SE}(\bar R)\) | Estimated standard error of the sample mean |
| heteroscedasticity | Different policies have different return variances |
| common random numbers | Reusing aligned random inputs when comparing systems |

## Core knowledge

### Return is a distribution

When initial states, dynamics, disturbances, or policy actions are random, a
fixed policy induces a distribution over trajectories and returns. The
distribution may be asymmetric or multimodal. For example, a controller can
have one mode associated with early failure and another associated with
long-lived trajectories.

Different policies can therefore have the same expected return but different
variance, median, tail behavior, or failure probability. Expected return alone
does not describe all aspects of reliability [1].

### Arithmetic mean

The sample mean is

\[
\bar R=\frac{1}{n}\sum_{i=1}^{n}R_i.
\]

For independent identically distributed rollouts with a finite expectation,
it estimates the expected return. The mean uses the magnitude of every
outcome and is sensitive to rare extreme values.

### Median and quantiles

The median estimates the center by probability mass rather than by total
magnitude. It can differ substantially from the mean for skewed or heavy-tailed
returns. A median does not estimate expected cumulative reward and cannot be
substituted for the mean without changing the estimand.

Quantiles and empirical failure rates can reveal outcome structure hidden by
both mean and median.

### Standard deviation and standard error

The sample standard deviation is

\[
s_R=
\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(R_i-\bar R)^2}.
\]

It describes variability among rollout outcomes. The conventional estimated
standard error of the mean is

\[
\mathrm{SE}(\bar R)=\frac{s_R}{\sqrt n}.
\]

Standard deviation and standard error are not interchangeable: the first
describes outcome variability, while the second describes uncertainty in the
estimated mean under sampling assumptions.

### Heteroscedastic policy performance

Policy return variance can change with policy parameters. A policy near a
stability boundary may alternate between early failure and long survival,
while another policy may behave consistently. Treating all policies as if
their measurement noise were identical can obscure this difference.

### Episode outcomes carry additional information

Episode length, termination, truncation, and return should be aligned by
rollout. A large correlation between length and return can arise when reward
accumulates while a system remains operational, but the relationship is not
universal: reward can also include velocity, energy, accuracy, or penalties.

### Common random numbers

Common random numbers evaluate alternative systems using aligned random
inputs. For two policies with paired outcomes \(R_i^{(A)}\) and \(R_i^{(B)}\),
the variance of their mean difference includes their covariance:

\[
\operatorname{Var}(\bar R^{(A)}-\bar R^{(B)})
=
\operatorname{Var}(\bar R^{(A)})
+\operatorname{Var}(\bar R^{(B)})
-2\operatorname{Cov}(\bar R^{(A)},\bar R^{(B)}).
\]

Positive covariance can reduce comparison variance. The benefit is not
automatic; it depends on how systems respond to the shared random inputs and
on whether all relevant random streams are actually paired [2].

## Conditions, limitations, and uncertainty

- The \(s/\sqrt n\) standard error relies on the effective independence and
  representativeness of repeats.
- Heavy tails can make finite-sample means and standard errors unstable.
- A fixed seed set defines a reproducible Monte Carlo estimate but does not
  remove uncertainty about other possible seeds.
- Partial pairing of random sources does not create a fully paired experiment.
- Many-policy comparisons introduce selection effects beyond the uncertainty
  of an individual mean.
- Simulation return measures behavior in the specified simulator, not
  automatically performance in a physical system.

## Related knowledge resources

- `reinforcement_learning_and_episodic_return`: the return being estimated.
- `continuous_control_and_gaussian_policies`: policy sampling as one source of randomness.
- `hopper_locomotion_and_mujoco_dynamics`: contacts and failure in simulated locomotion.

## References

1. Patterson A, Neumann S, White M, White A. Empirical design in reinforcement learning. *Journal of Machine Learning Research*. 2024;25(318):1–63. https://www.jmlr.org/papers/v25/23-0183.html. [Review and guidance]
2. Glasserman P, Yao DD. Some guidelines and guarantees for common random numbers. *Management Science*. 1992;38(6):884–908. https://doi.org/10.1287/mnsc.38.6.884. [Primary theory]
