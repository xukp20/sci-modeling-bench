"""Frozen Hopper-v5 policy rollout Dataset and integrity validation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from numbers import Integral, Real
from pathlib import Path
from typing import Any

import numpy as np

from sci_modeling_bench.dataset import (
    Dataset,
    DatasetValidator,
    HubDatasetSource,
    ValidationReport,
    Violation,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    MAX_EPISODE_STEPS,
    POLICY_SIZE,
    canonical_policy,
    policy_identity,
)

DEFAULT_HOPPER_CONTROLLER_REPO_ID = "sci-modeling-bench/design-bench"
DEFAULT_HOPPER_CONTROLLER_REVISION = (
    "7b513a5995110f262b8a322cc4bd9ac88e575aee"
)
HOPPER_CONTROLLER_CONFIG_NAME = "hopper_controller"
HOPPER_CONTROLLER_DEFAULT_SPLIT = "policies"
DEFAULT_HOPPER_CONTROLLER_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_HOPPER_CONTROLLER_REPO_ID,
    config_name=HOPPER_CONTROLLER_CONFIG_NAME,
    revision=DEFAULT_HOPPER_CONTROLLER_REVISION,
)

EXPECTED_POLICY_COUNT = 3_200
EXPECTED_ROLLOUT_COUNT = 500
_DATASET_ID = "design-bench/hopper-controller"
_EXPECTED_COLUMNS = (
    "source_index",
    "policy_identity",
    "policy_weights",
    "source_return",
    "raw_returns",
    "episode_lengths",
    "terminated",
    "truncated",
    "rollout_count",
    "mean_return",
    "median_return",
    "return_std",
    "return_standard_error",
)


class HopperControllerDataset(Dataset):
    """Structured PPO policies with 500 frozen stochastic Hopper-v5 rollouts."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_HOPPER_CONTROLLER_REPO_ID,
        config_name: str | None = HOPPER_CONTROLLER_CONFIG_NAME,
        revision: str | None = DEFAULT_HOPPER_CONTROLLER_REVISION,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> HopperControllerDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or HopperControllerValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_HOPPER_CONTROLLER_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> HopperControllerDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or HopperControllerValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )


class HopperControllerValidator(DatasetValidator):
    """Check policy identity, raw rollout alignment, and derived summaries."""

    def validate_inputs(
        self,
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        weights = inputs.get("policy_weights")
        if weights is None:
            return ValidationReport()
        try:
            canonical_policy(weights)
        except (TypeError, ValueError) as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="invalid_policy_weights",
                        field="policy_weights",
                        message=str(exc),
                    ),
                )
            )
        return ValidationReport()

    def validate_observation(
        self,
        observation: Mapping[str, Any],
    ) -> ValidationReport:
        violations: list[Violation] = []
        weights = observation.get("policy_weights")
        try:
            expected_identity = policy_identity(weights)
        except (TypeError, ValueError) as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="invalid_policy_weights",
                        field="policy_weights",
                        message=str(exc),
                    ),
                )
            )
        if observation.get("policy_identity") != expected_identity:
            violations.append(
                Violation(
                    code="policy_identity_mismatch",
                    field="policy_identity",
                    message="policy_identity must match the canonical float32 weights",
                )
            )

        source_index = observation.get("source_index")
        if (
            isinstance(source_index, bool)
            or not isinstance(source_index, Integral)
            or not 0 <= int(source_index) < EXPECTED_POLICY_COUNT
        ):
            violations.append(
                Violation(
                    code="invalid_source_index",
                    field="source_index",
                    message=(
                        f"source_index must be an integer in [0, "
                        f"{EXPECTED_POLICY_COUNT - 1}]"
                    ),
                )
            )

        source_return = observation.get("source_return")
        if (
            isinstance(source_return, bool)
            or not isinstance(source_return, Real)
            or not math.isfinite(float(source_return))
        ):
            violations.append(
                Violation(
                    code="invalid_source_return",
                    field="source_return",
                    message="source_return must be finite",
                )
            )

        raw_returns = _numeric_vector(observation.get("raw_returns"))
        episode_lengths = _numeric_vector(observation.get("episode_lengths"))
        terminated = _sequence(observation.get("terminated"))
        truncated = _sequence(observation.get("truncated"))
        aligned = (
            raw_returns is not None
            and episode_lengths is not None
            and terminated is not None
            and truncated is not None
            and len(raw_returns)
            == len(episode_lengths)
            == len(terminated)
            == len(truncated)
            == EXPECTED_ROLLOUT_COUNT
        )
        if not aligned:
            violations.append(
                Violation(
                    code="rollout_measurement_alignment",
                    message=(
                        "raw returns, episode outcomes, and flags must contain "
                        f"exactly {EXPECTED_ROLLOUT_COUNT} aligned values"
                    ),
                )
            )
            return ValidationReport(violations=tuple(violations))

        assert raw_returns is not None
        assert episode_lengths is not None
        assert terminated is not None
        assert truncated is not None
        if not np.all(np.isfinite(raw_returns)):
            violations.append(
                Violation(
                    code="non_finite_raw_return",
                    field="raw_returns",
                    message="raw_returns must contain only finite values",
                )
            )
        if not np.all(
            (episode_lengths >= 1) & (episode_lengths <= MAX_EPISODE_STEPS)
        ):
            violations.append(
                Violation(
                    code="invalid_episode_length",
                    field="episode_lengths",
                    message=(
                        f"episode lengths must be in [1, {MAX_EPISODE_STEPS}]"
                    ),
                )
            )
        if any(not isinstance(value, (bool, np.bool_)) for value in terminated):
            violations.append(
                Violation(
                    code="invalid_terminated_flag",
                    field="terminated",
                    message="terminated must contain boolean values",
                )
            )
        if any(not isinstance(value, (bool, np.bool_)) for value in truncated):
            violations.append(
                Violation(
                    code="invalid_truncated_flag",
                    field="truncated",
                    message="truncated must contain boolean values",
                )
            )
        if not all(bool(term) or bool(trunc) for term, trunc in zip(
            terminated, truncated, strict=True
        )):
            violations.append(
                Violation(
                    code="unfinished_rollout",
                    message="every rollout must terminate or truncate",
                )
            )

        if observation.get("rollout_count") != EXPECTED_ROLLOUT_COUNT:
            violations.append(
                Violation(
                    code="rollout_count_mismatch",
                    field="rollout_count",
                    message=f"rollout_count must equal {EXPECTED_ROLLOUT_COUNT}",
                )
            )
        if np.all(np.isfinite(raw_returns)):
            expected = {
                "mean_return": float(np.mean(raw_returns, dtype=np.float64)),
                "median_return": float(np.median(raw_returns)),
                "return_std": float(np.std(raw_returns, ddof=1, dtype=np.float64)),
            }
            expected["return_standard_error"] = (
                expected["return_std"] / math.sqrt(EXPECTED_ROLLOUT_COUNT)
            )
            for field, value in expected.items():
                actual = observation.get(field)
                if (
                    isinstance(actual, bool)
                    or not isinstance(actual, Real)
                    or not math.isfinite(float(actual))
                    or not math.isclose(
                        float(actual), value, rel_tol=0.0, abs_tol=1e-10
                    )
                ):
                    violations.append(
                        Violation(
                            code=f"{field}_mismatch",
                            field=field,
                            message=f"{field} must be recomputed from raw_returns",
                        )
                    )
        return ValidationReport(violations=tuple(violations))

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="hopper_controller_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        if len(data) != EXPECTED_POLICY_COUNT:
            violations.append(
                Violation(
                    code="hopper_controller_policy_count",
                    message=(
                        f"expected {EXPECTED_POLICY_COUNT} policies, got {len(data)}"
                    ),
                )
            )
        identities = list(data["policy_identity"])
        if len(set(identities)) != len(identities):
            violations.append(
                Violation(
                    code="duplicate_policy_identity",
                    field="policy_identity",
                    message="policy identities must be unique",
                )
            )
        source_indices = list(data["source_index"])
        if source_indices != list(range(len(data))):
            violations.append(
                Violation(
                    code="source_policy_order_mismatch",
                    field="source_index",
                    message="canonical rows must preserve Design-Bench source order",
                )
            )
        return ValidationReport(violations=tuple(violations))


def _sequence(value: object) -> Sequence[Any] | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return None


def _numeric_vector(value: object) -> np.ndarray | None:
    sequence = _sequence(value)
    if sequence is None:
        return None
    try:
        array = np.asarray(sequence, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    return array if array.ndim == 1 else None
