"""Frozen Hopper-v5 rollout adapter used only to build dataset artifacts."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from collections.abc import Sequence
from typing import Any

import numpy as np

POLICY_SIZE = 5_126
OBSERVATION_SIZE = 11
HIDDEN_SIZE = 64
ACTION_SIZE = 3
ENVIRONMENT_ID = "Hopper-v5"
MAX_EPISODE_STEPS = 1_000

_SOURCE_POLICIES: np.ndarray | None = None
_ENVIRONMENT: Any = None
_REPEATS = 0
_BASE_SEED = 0


def policy_identity(weights: Sequence[float] | np.ndarray) -> str:
    """Return the stable identity of one little-endian float32 policy."""

    policy = canonical_policy(weights)
    return "hopper-" + hashlib.sha256(policy.tobytes(order="C")).hexdigest()[:24]


def canonical_policy(weights: Sequence[float] | np.ndarray) -> np.ndarray:
    """Normalize one submitted policy to the frozen byte representation."""

    policy = np.asarray(weights, dtype="<f4")
    if policy.shape != (POLICY_SIZE,):
        raise ValueError(
            f"policy_weights must have shape ({POLICY_SIZE},), got {policy.shape}"
        )
    if not np.all(np.isfinite(policy)):
        raise ValueError("policy_weights must contain only finite values")
    return np.ascontiguousarray(policy)


def unpack_policy(
    weights: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, ...]:
    """Unpack the Stable-Baselines policy tensor order used by Design-Bench."""

    policy = canonical_policy(weights)
    shapes = (
        (OBSERVATION_SIZE, HIDDEN_SIZE),
        (HIDDEN_SIZE,),
        (HIDDEN_SIZE, HIDDEN_SIZE),
        (HIDDEN_SIZE,),
        (HIDDEN_SIZE, ACTION_SIZE),
        (ACTION_SIZE,),
        (ACTION_SIZE,),
    )
    tensors: list[np.ndarray] = []
    offset = 0
    for shape in shapes:
        size = int(np.prod(shape))
        tensors.append(policy[offset : offset + size].reshape(shape))
        offset += size
    if offset != POLICY_SIZE:
        raise RuntimeError("policy unpacking schema does not cover all weights")
    return tuple(tensors)


def rollout_policy(
    weights: Sequence[float] | np.ndarray,
    *,
    reset_seed: int,
    action_seed: int,
    environment: Any | None = None,
) -> tuple[float, int, bool, bool]:
    """Run one stochastic rollout using independently seeded environment/noise."""

    owns_environment = environment is None
    env = environment or _make_environment()
    w1, b1, w2, b2, w3, b3, logstd = unpack_policy(weights)
    noise_scale = np.exp(logstd.astype(np.float64))
    rng = np.random.default_rng(action_seed)
    observation, _ = env.reset(seed=reset_seed)
    total_return = 0.0
    terminated = False
    truncated = False
    length = 0
    try:
        while not (terminated or truncated):
            hidden = np.tanh(observation @ w1 + b1)
            hidden = np.tanh(hidden @ w2 + b2)
            action = hidden @ w3 + b3
            action = action + rng.normal(size=ACTION_SIZE) * noise_scale
            action = np.clip(action, -1.0, 1.0).astype(np.float32)
            if not np.all(np.isfinite(action)):
                raise ValueError("policy produced a non-finite action")
            observation, reward, terminated, truncated, _ = env.step(action)
            if not np.isfinite(reward):
                raise ValueError("simulator produced a non-finite reward")
            total_return += float(reward)
            length += 1
            if length > MAX_EPISODE_STEPS:
                raise RuntimeError("environment exceeded its frozen maximum horizon")
    finally:
        if owns_environment:
            env.close()
    return total_return, length, bool(terminated), bool(truncated)


def initialize_rollout_worker(
    source_path: str,
    repeats: int,
    base_seed: int,
) -> None:
    """Initialize one process with a memory-mapped source and one environment."""

    global _SOURCE_POLICIES, _ENVIRONMENT, _REPEATS, _BASE_SEED
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"
    _SOURCE_POLICIES = np.load(source_path, mmap_mode="r", allow_pickle=False)
    _REPEATS = repeats
    _BASE_SEED = base_seed
    _ENVIRONMENT = _make_environment()


def rollout_source_policy(
    policy_index: int,
) -> tuple[int, str, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Worker entry point that evaluates all repeats for one source policy."""

    if _SOURCE_POLICIES is None or _ENVIRONMENT is None:
        raise RuntimeError("rollout worker has not been initialized")
    policy = _SOURCE_POLICIES[policy_index]
    identity = policy_identity(policy)
    returns = np.empty(_REPEATS, dtype=np.float32)
    lengths = np.empty(_REPEATS, dtype=np.int32)
    terminated = np.empty(_REPEATS, dtype=np.bool_)
    truncated = np.empty(_REPEATS, dtype=np.bool_)
    for repeat in range(_REPEATS):
        result = rollout_policy(
            policy,
            reset_seed=derived_seed(_BASE_SEED, "reset", repeat),
            action_seed=derived_seed(_BASE_SEED, "action", identity, repeat),
            environment=_ENVIRONMENT,
        )
        returns[repeat], lengths[repeat], terminated[repeat], truncated[repeat] = result
    return policy_index, identity, returns, lengths, terminated, truncated


def derived_seed(base_seed: int, *parts: object) -> int:
    """Derive a process-order-independent 32-bit seed."""

    payload = "\0".join((str(base_seed), *(str(part) for part in parts)))
    return int.from_bytes(
        hashlib.sha256(payload.encode("utf-8")).digest()[:4], "little"
    )


def simulator_metadata() -> dict[str, Any]:
    """Describe the exact simulator and policy execution recipe."""

    import gymnasium
    import mujoco

    env = _make_environment()
    try:
        xml_path = Path(env.unwrapped.fullpath)
        xml_sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        spec = env.spec
        return {
            "environment_id": ENVIRONMENT_ID,
            "environment_kwargs": dict(spec.kwargs) if spec is not None else {},
            "maximum_episode_steps": MAX_EPISODE_STEPS,
            "gymnasium_version": gymnasium.__version__,
            "mujoco_version": mujoco.__version__,
            "numpy_version": np.__version__,
            "hopper_xml_path": str(xml_path),
            "hopper_xml_sha256": xml_sha256,
            "observation_size": OBSERVATION_SIZE,
            "action_size": ACTION_SIZE,
            "policy_size": POLICY_SIZE,
            "policy_layers": [OBSERVATION_SIZE, HIDDEN_SIZE, HIDDEN_SIZE, ACTION_SIZE],
            "hidden_activation": "tanh",
            "policy_parameter_order": [
                "W1",
                "b1",
                "W2",
                "b2",
                "W3",
                "b3",
                "logstd",
            ],
            "action_distribution": "Gaussian using policy logstd",
            "action_clip": [-1.0, 1.0],
            "rendering": False,
        }
    finally:
        env.close()


def _make_environment() -> Any:
    try:
        import gymnasium as gym
    except ImportError as exc:
        raise ImportError(
            "Hopper rollout generation requires `pip install "
            "sci-modeling-bench[hopper-sim]`"
        ) from exc
    env = gym.make(ENVIRONMENT_ID)
    if env.observation_space.shape != (OBSERVATION_SIZE,):
        raise RuntimeError("unexpected Hopper observation shape")
    if env.action_space.shape != (ACTION_SIZE,):
        raise RuntimeError("unexpected Hopper action shape")
    if env.spec is None or env.spec.max_episode_steps != MAX_EPISODE_STEPS:
        raise RuntimeError("unexpected Hopper maximum episode length")
    return env
