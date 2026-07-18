from __future__ import annotations

import numpy as np
import pytest

from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    ACTION_SIZE,
    HIDDEN_SIZE,
    OBSERVATION_SIZE,
    POLICY_SIZE,
    canonical_policy,
    derived_seed,
    policy_identity,
    unpack_policy,
)


def test_policy_canonicalization_and_identity_are_stable() -> None:
    weights = np.arange(POLICY_SIZE, dtype=np.float64) / POLICY_SIZE

    canonical = canonical_policy(weights)

    assert canonical.shape == (POLICY_SIZE,)
    assert canonical.dtype == np.dtype("<f4")
    assert policy_identity(weights) == policy_identity(canonical.tolist())


def test_policy_unpacking_matches_the_frozen_tensor_order() -> None:
    tensors = unpack_policy(np.zeros(POLICY_SIZE, dtype=np.float32))

    assert tuple(tensor.shape for tensor in tensors) == (
        (OBSERVATION_SIZE, HIDDEN_SIZE),
        (HIDDEN_SIZE,),
        (HIDDEN_SIZE, HIDDEN_SIZE),
        (HIDDEN_SIZE,),
        (HIDDEN_SIZE, ACTION_SIZE),
        (ACTION_SIZE,),
        (ACTION_SIZE,),
    )


def test_invalid_policy_shape_or_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="shape"):
        canonical_policy(np.zeros(POLICY_SIZE - 1, dtype=np.float32))
    invalid = np.zeros(POLICY_SIZE, dtype=np.float32)
    invalid[0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        canonical_policy(invalid)


def test_derived_seeds_are_repeatable_and_namespaced() -> None:
    assert derived_seed(7, "reset", 3) == derived_seed(7, "reset", 3)
    assert derived_seed(7, "reset", 3) != derived_seed(7, "action", 3)
