# Continuous Control and Gaussian Policies

## Summary

Continuous-control policies select real-valued actions such as forces or
torques. A common stochastic policy represents each action dimension with a
Gaussian distribution whose mean is produced by a function of the current
observation and whose standard deviation controls action variability.
Sampling from a Gaussian and subsequently clipping an action to actuator
bounds produces a different distribution from a Gaussian conditioned to lie
within those bounds.

## Scope

### Covered

- Continuous action spaces and bounded actuators.
- Diagonal Gaussian policies, means, standard deviations, and log standard deviations.
- Action sampling, clipping, and their distributional consequences.
- Deterministic mean actions versus stochastic policy execution.

### Not covered

- A particular flattened weight vector or neural-network layout.
- A prescribed policy-learning algorithm.
- Environment-specific actuator identities or reward functions.

## Key concepts and notation

| Symbol or term | Meaning |
| --- | --- |
| \(o\) | Current observation |
| \(\mu_\theta(o)\) | Policy mean action |
| \(\sigma_\theta(o)\) | Positive action standard deviation |
| \(\log\sigma\) | Unconstrained log standard deviation |
| \(\epsilon\) | Standard-normal noise vector |
| \(\odot\) | Elementwise multiplication |
| action bounds | Valid interval imposed by an environment or actuator |

## Core knowledge

### Continuous actions

In continuous control, the action belongs to a subset of
\(\mathbb{R}^{d_a}\). Its components can represent joint torques, forces,
target positions, or other control commands. Different action dimensions can
have different physical meanings even when they share the same numerical
bounds.

An environment may restrict actions to a box
\([a_{\min},a_{\max}]^{d_a}\). A controller and an environment must agree on
the order, units, scaling, and handling of values outside this box.

### Diagonal Gaussian policy

A widely used stochastic continuous-action policy is

\[
\pi_\theta(a\mid o)=
\mathcal{N}\left(a;\mu_\theta(o),
\operatorname{diag}(\sigma_\theta(o)^2)\right).
\]

It can be sampled through reparameterization:

\[
\epsilon\sim\mathcal{N}(0,I),\qquad
a=\mu_\theta(o)+\sigma_\theta(o)\odot\epsilon.
\]

The diagonal form treats action noise components as conditionally independent
given the observation. It does not imply that the resulting physical joint
motions are independent, because the dynamics couple them [1].

### Log standard deviation

Standard deviations must be positive, whereas an unconstrained parameter can
take any real value. Gaussian policies therefore often store

\[
\ell=\log\sigma,\qquad \sigma=\exp(\ell).
\]

Some policies make \(\ell\) depend on the observation; others learn one
state-independent value per action dimension. Increasing \(\ell\) increases
the scale of action variability multiplicatively, not additively.

### Mean action and sampled action are different

The network output \(\mu_\theta(o)\) is the center of the Gaussian, not
necessarily the action executed in an episode. Evaluating only the mean action
removes policy sampling noise and therefore evaluates a different controller
from stochastic execution unless the variance is zero.

### Clipping changes the action distribution

For bounded actions, one implementation is

\[
a_{\mathrm{exec}}=
\operatorname{clip}(a,a_{\min},a_{\max}).
\]

All Gaussian probability mass below or above a bound is mapped to the
corresponding endpoint. This creates point masses at the limits. It is not the
same as sampling from a truncated normal distribution, nor is it the same as
applying a smooth `tanh` transformation. The choice affects both behavior and
the probability model used during policy learning [2].

## Quantitative relationships

For one Gaussian action dimension, the entropy is

\[
\mathcal{H}
=\frac{1}{2}\log(2\pi e\sigma^2)
=\log\sigma+\frac{1}{2}\log(2\pi e).
\]

Thus larger log standard deviation gives larger Gaussian entropy before
action-bound handling. After clipping, the executed-action entropy and moments
are no longer those of the original Gaussian.

## Conditions, limitations, and uncertainty

- A diagonal Gaussian excludes conditional covariance between action-noise
  dimensions.
- Action clipping can make large mean or variance values produce frequent
  saturation at actuator limits.
- The same numerical action can have different physical effects under
  different actuator scaling or simulation models.
- Log standard deviation describes policy randomness, not uncertainty about
  whether the policy is good.
- Deterministic and stochastic evaluations of the same policy parameters need
  not have the same expected return.

## Related knowledge resources

- `reinforcement_learning_and_episodic_return`: policies and return.
- `feedforward_neural_policy_parameterization`: neural mappings from observations to action means.
- `proximal_policy_optimization_and_policy_checkpoints`: stochastic policies in PPO.

## References

1. OpenAI. Part 1: Key Concepts in Reinforcement Learning—Stochastic Policies. *Spinning Up in Deep RL*. https://spinningup.openai.com/en/latest/spinningup/rl_intro.html. Accessed 2026-07-23. [Technical documentation]
2. Chou P-W, Maturana D, Scherer S. Improving stochastic policy gradients in continuous control with deep reinforcement learning using the Beta distribution. *Proceedings of ICML*. 2017;70:834–843. https://proceedings.mlr.press/v70/chou17a.html. [Primary research]
