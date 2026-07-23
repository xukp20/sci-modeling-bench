# Hopper Locomotion and MuJoCo Dynamics

## Summary

The Gymnasium MuJoCo Hopper environment represents a planar, articulated
one-legged body controlled by torques at its thigh, leg, and foot joints.
Locomotion requires coordinated contact, posture, and forward motion. The
standard Hopper-v5 observation contains torso and joint positions followed by
their velocities, while its reward combines survival, forward velocity, and a
quadratic control penalty. These definitions are specific to the documented
Hopper environment version and are not universal laws of legged locomotion.

## Scope

### Covered

- The articulated Hopper body and its generalized coordinates.
- Standard Hopper-v5 observation and action semantics.
- The default reward, initialization, health, termination, and truncation rules.
- Contact dynamics and physical dependencies in hopping locomotion.
- The role and limitations of MuJoCo simulation.

### Not covered

- A collection of saved policies or their parameter-vector serialization.
- Simulator seeds, measured policy returns, or candidate rankings.
- A controller-design or policy-training procedure.

## Key concepts and notation

| Term or symbol | Meaning |
| --- | --- |
| torso | Main body of the planar hopper |
| thigh, leg, foot | Serial articulated links below the torso |
| \(q_{\mathrm{pos}}\) | Generalized positions and joint angles |
| \(q_{\mathrm{vel}}\) | Generalized translational and angular velocities |
| torque | Rotary actuator command applied at a hinge joint |
| contact | Interaction between the foot/body and the ground |
| frame skip | Number of MuJoCo integration frames per environment action |

## Core knowledge

### Articulated planar hopper

Hopper is a two-dimensional articulated system with a torso and one leg
composed of thigh, leg, and foot links. The root can translate horizontally
and vertically and rotate in the plane. Three actuated hinge joints connect
the lower links [1].

Unlike unconstrained flight, hopping contains alternating contact and
non-contact phases. Ground contact introduces impacts and contact forces, so
the dynamics are hybrid: continuous motion is interrupted by discrete changes
in contact state.

### Standard Hopper-v5 action space

The standard action is a three-dimensional vector in \([-1,1]^3\). In order,
the components control [1]:

| Index | Actuator |
| ---: | --- |
| 0 | Torque on the thigh joint |
| 1 | Torque on the leg joint |
| 2 | Torque on the foot joint |

The numerical bounds are simulator controls. The physical response also
depends on actuator parameters, body inertias, joint geometry, damping,
contacts, and integration settings.

### Standard Hopper-v5 observation

With the default setting that excludes absolute horizontal torso position,
the observation has 11 components in the following order [1]:

| Index | Quantity | Unit |
| ---: | --- | --- |
| 0 | Torso height | m |
| 1 | Torso angle | rad |
| 2 | Thigh-joint angle | rad |
| 3 | Leg-joint angle | rad |
| 4 | Foot-joint angle | rad |
| 5 | Horizontal torso velocity | m/s |
| 6 | Vertical torso velocity | m/s |
| 7 | Torso angular velocity | rad/s |
| 8 | Thigh-joint angular velocity | rad/s |
| 9 | Leg-joint angular velocity | rad/s |
| 10 | Foot-joint angular velocity | rad/s |

Omitting absolute horizontal position encourages policies whose decisions do
not depend on where the hopper is along the track. Horizontal velocity remains
observable.

### Default reward

For the documented default Hopper-v5 configuration, the per-step reward is

\[
r_t=r_{\mathrm{healthy}}+
w_{\mathrm{forward}}\frac{x_{t+1}-x_t}{\Delta t}
-w_{\mathrm{control}}\lVert a_t\rVert_2^2,
\]

where \(r_{\mathrm{healthy}}=1\),
\(w_{\mathrm{forward}}=1\), and
\(w_{\mathrm{control}}=10^{-3}\) [1].

The default MuJoCo timestep is \(0.002\) s and the default frame skip is four,
giving \(\Delta t=0.008\) s per environment step. Return therefore reflects
several coupled quantities: remaining healthy, moving forward, and limiting
the squared action magnitude.

### Initialization and episode end

The default initial generalized position is a small uniform perturbation
around \([0,1.25,0,0,0,0]\); velocities receive a small uniform perturbation
around zero [1]. These perturbations create variation in trajectories even
before stochastic policy actions are considered.

With default health settings, the episode terminates if relevant state values
leave their allowed range, torso height falls below \(0.7\) m, or torso angle
leaves \([-0.2,0.2]\) rad. An episode that does not terminate is truncated
after 1,000 environment steps [1].

### Physical dependencies

Forward hopping requires more than producing large actuator commands.
Joint torques alter link accelerations and ground reaction forces; their
effects depend on current posture, velocity, and contact state. Excessive or
poorly timed torque can destabilize the torso, increase control cost, or
produce an unfavorable landing.

Episode duration and forward speed are related to return under the default
reward, but they are not identical. A long episode can move slowly, and a
shorter episode can accumulate substantial forward reward before failure.

### MuJoCo simulation

MuJoCo is a rigid-body physics engine designed for articulated systems,
contacts, and model-based control [2]. A simulation result is conditional on
the model XML, masses and inertias, contact parameters, actuator definitions,
integrator, timestep, frame skip, software version, and wrapper behavior.

The same policy parameters can therefore yield different returns when any of
these definitions changes.

## Conditions, limitations, and uncertainty

- The observation order, reward constants, health ranges, and horizon above
  describe the documented default Hopper-v5 environment.
- Custom XML files and constructor arguments can change the dynamics or task
  definition.
- Numerical simulation approximates a specified mechanical model; it does not
  establish transfer to a physical robot.
- Contact-rich dynamics can be sensitive to small differences in initial
  state, actions, and numerical implementation.
- High episodic return does not uniquely identify a gait, stability margin,
  energy efficiency, or robustness outside the evaluation distribution.

## Related knowledge resources

- `reinforcement_learning_and_episodic_return`: reward accumulation and episode endings.
- `continuous_control_and_gaussian_policies`: stochastic torque commands.
- `feedforward_neural_policy_parameterization`: observation-to-action mappings.
- `stochastic_rollout_evaluation_and_uncertainty`: repeated locomotion outcomes.

## References

1. Farama Foundation. Hopper—Gymnasium MuJoCo environments. https://gymnasium.farama.org/environments/mujoco/hopper/. Accessed 2026-07-23. [Official environment documentation]
2. Todorov E, Erez T, Tassa Y. MuJoCo: A physics engine for model-based control. *2012 IEEE/RSJ International Conference on Intelligent Robots and Systems*. 2012:5026–5033. https://doi.org/10.1109/IROS.2012.6386109. [Primary research]
