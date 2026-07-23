# Proximal Policy Optimization and Policy Checkpoints

## Summary

Proximal Policy Optimization (PPO) is an on-policy policy-gradient method that
alternates between collecting trajectories with the current stochastic policy
and optimizing a surrogate objective. Its clipped objective limits the
incentive for a new policy to move too far from the behavior policy on sampled
actions. A saved checkpoint records parameters at one point in a stochastic
training process; checkpoint order does not by itself guarantee monotonically
improving evaluation return.

## Scope

### Covered

- Policy gradients, behavior policies, and on-policy data.
- The PPO probability ratio and clipped surrogate objective.
- Actor and value-function roles.
- Stochastic optimization and checkpoint interpretation.

### Not covered

- PPO hyperparameters for a particular training run.
- Reconstruction of hidden run or checkpoint identifiers.
- Instructions for training, fine-tuning, or selecting a controller.

## Key concepts and notation

| Symbol or term | Meaning |
| --- | --- |
| \(\pi_\theta\) | Current policy with parameters \(\theta\) |
| \(\pi_{\theta_{\mathrm{old}}}\) | Policy that generated the training trajectories |
| \(A_t\) | Advantage estimate at time \(t\) |
| \(r_t(\theta)\) | New-to-old action-probability ratio |
| \(\epsilon\) | PPO clipping parameter |
| actor | Parameterized policy |
| critic | Learned value estimate used to construct advantages |
| checkpoint | Saved parameter state at a training time |

## Core knowledge

### Policy-gradient learning

Policy-gradient methods adjust policy parameters to increase an estimate of
expected return. Training trajectories are sampled from a policy, and sampled
actions are weighted by estimates of whether their outcomes were better or
worse than a baseline.

The gradient estimate is stochastic because it depends on finite trajectories,
sampled actions, initial states, and estimated advantages.

### PPO is on-policy

PPO collects a batch of trajectories with the current behavior policy and
then performs one or more optimization epochs using that batch [1]. The data
distribution changes as the policy changes. PPO is therefore categorized as
on-policy even though it reuses the most recent batch for several minibatch
updates.

### Probability ratio

PPO compares the probability of a recorded action under the new and old
policies:

\[
r_t(\theta)=
\frac{\pi_\theta(A_t\mid O_t)}
{\pi_{\theta_{\mathrm{old}}}(A_t\mid O_t)}.
\]

The ratio is evaluated on actions sampled from the old policy. It is not a
direct ratio of trajectory returns.

### Clipped surrogate objective

The PPO-Clip objective is commonly written

\[
L^{\mathrm{CLIP}}(\theta)=
\mathbb{E}_t\left[
\min\left(
r_t(\theta)A_t,\,
\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)A_t
\right)
\right].
\]

Clipping removes some incentive for probability ratios to move beyond a
specified interval in directions that would increase the sampled surrogate.
It is not a hard guarantee on weight-space distance, action-space distance,
or improvement in true expected return [1,2].

### Actor and value function

The actor determines the action distribution. A value function or critic
estimates expected future return and is used to form lower-variance advantage
estimates. Actor and critic objectives are related during training but their
parameters and outputs have different meanings.

A deployed policy checkpoint may contain only actor parameters even if a
critic was used during training.

### Checkpoints are samples from an optimization trajectory

Training checkpoints record the optimizer state or model parameters at
particular update times. Later checkpoints have undergone more updates, but
several effects prevent checkpoint index from being a universal performance
scale:

- trajectory batches are random;
- advantage and value estimates are approximate;
- minibatch optimization is stochastic;
- the clipped objective is a surrogate;
- exploration variance can change;
- evaluation itself can have Monte Carlo noise.

PPO was designed to make useful policy updates practical and comparatively
stable, not to guarantee that every saved checkpoint improves true expected
return [1,2].

## Conditions, limitations, and uncertainty

- PPO has multiple implementation variants, including choices for advantage
  estimation, value clipping, entropy bonuses, normalization, and early
  stopping.
- Weight-space displacement is not equivalent to policy-distribution
  displacement.
- A checkpoint does not encode its training step unless that metadata is
  saved separately.
- Policies from different random initializations can follow different
  parameter trajectories.
- Evaluation should distinguish randomness in training from randomness in
  executing a fixed stochastic policy.

## Related knowledge resources

- `reinforcement_learning_and_episodic_return`: expected return and trajectories.
- `continuous_control_and_gaussian_policies`: a common PPO actor distribution.
- `feedforward_neural_policy_parameterization`: checkpoint parameter structure.
- `stochastic_rollout_evaluation_and_uncertainty`: evaluating fixed checkpoints.

## References

1. Schulman J, Wolski F, Dhariwal P, Radford A, Klimov O. Proximal Policy Optimization Algorithms. *arXiv*. 2017. https://arxiv.org/abs/1707.06347. [Primary research]
2. OpenAI. Proximal Policy Optimization. *Spinning Up in Deep RL*. https://spinningup.openai.com/en/latest/algorithms/ppo.html. Accessed 2026-07-23. [Technical documentation]
