# Reinforcement Learning and Episodic Return

## Summary

Reinforcement learning studies an agent that repeatedly observes an
environment, selects actions through a policy, and receives rewards. In an
episodic problem, a trajectory ends after a finite number of transitions, and
its return is the cumulative reward collected during that episode. A policy's
expected return is an expectation over all sources of randomness, not the
outcome of a single episode.

## Scope

### Covered

- Agent–environment interaction, observations, actions, rewards, and policies.
- Trajectories, episodes, undiscounted and discounted return.
- Policy value and expected episodic performance.
- Environment termination and external time-limit truncation.

### Not covered

- A particular controller architecture or parameter serialization.
- A particular environment's reward constants or episode limit.
- A training recipe, model-selection procedure, or candidate-ranking method.

## Key concepts and notation

| Term or symbol | Definition |
| --- | --- |
| \(S_t\) | Environment state at time \(t\) |
| \(O_t\) | Observation available to the agent at time \(t\) |
| \(A_t\) | Action selected by the agent |
| \(R_{t+1}\) | Reward produced after action \(A_t\) |
| \(\pi(a\mid o)\) | Policy distribution over actions conditional on an observation |
| \(\tau\) | Trajectory of observations, actions, and rewards |
| \(T\) | Final transition index of an episode |
| \(G_t\) | Return accumulated after time \(t\) |
| \(\gamma\) | Discount factor, conventionally in \([0,1]\) |

## Core knowledge

### Agent–environment interaction

At each time step, an agent receives an observation, uses a policy to select
an action, and the environment produces a reward and a new state [1]. The
environment includes everything outside the policy's immediate action
selection, including physical dynamics, contacts, process noise, and the
reward rule.

The environment state and the agent's observation need not be identical. An
observation can omit variables, transform them, or contain noisy measurements.
A policy defined on observations therefore does not necessarily have direct
access to the complete physical state.

### Policies can be deterministic or stochastic

A deterministic policy maps an observation to one action. A stochastic policy
defines a conditional distribution:

\[
A_t \sim \pi(\cdot\mid O_t).
\]

Even in deterministic dynamics, a stochastic policy can produce different
trajectories from the same initial state. Conversely, a deterministic policy
can have variable outcomes when initial conditions, disturbances, or the
environment are random.

### Episodic trajectories and return

An episodic task divides interaction into finite trajectories. For an
undiscounted episode, the return after time \(t\) is

\[
G_t=\sum_{k=t}^{T-1}R_{k+1}.
\]

For discounted return,

\[
G_t=\sum_{k=t}^{T-1}\gamma^{k-t}R_{k+1}.
\]

Discounting changes the relative contribution of rewards at different times.
It is not implied merely by reporting an episodic return; the return
convention must be stated [1].

### Expected policy performance

The value of a policy from an initial-state distribution is an expectation:

\[
J(\pi)=\mathbb{E}_{\tau\sim\pi}[G_0].
\]

The expectation includes randomness in initialization, transitions, policy
actions, and any other stochastic component. One observed return is a sample
from this distribution. Repeated episodes estimate \(J(\pi)\), but the
estimate remains uncertain for any finite sample.

### Termination and truncation

Gymnasium distinguishes termination from truncation [2]. Termination indicates
that an environment-defined terminal condition has been reached. Truncation
indicates that an external boundary, commonly a time limit, ended the
trajectory even though the underlying process need not be terminal.

This distinction matters scientifically: a short terminated episode may
represent physical failure, while a full-length truncated episode may
represent survival until the experimental horizon. The numerical return alone
does not always identify which occurred.

## Conditions, limitations, and uncertainty

- Return is meaningful only together with the reward definition and episode
  convention.
- High return does not identify which physical behavior or reward component
  caused it.
- Equal expected returns can arise from different return distributions and
  different failure modes.
- A finite episode limit can change both the observed return and the meaning
  of successful survival.
- An observation can omit state variables needed for fully Markovian control.

## Related knowledge resources

- `continuous_control_and_gaussian_policies`: stochastic policies for continuous actions.
- `stochastic_rollout_evaluation_and_uncertainty`: repeated evaluation of policy returns.
- `proximal_policy_optimization_and_policy_checkpoints`: one method for learning policies.

## References

1. Sutton RS, Barto AG. *Reinforcement Learning: An Introduction*. 2nd ed. MIT Press; 2018. http://incompleteideas.net/book/the-book-2nd.html. [Textbook]
2. Farama Foundation. Gymnasium core API: `Env.step` termination and truncation semantics. https://gymnasium.farama.org/api/env/. Accessed 2026-07-23. [Official documentation]
