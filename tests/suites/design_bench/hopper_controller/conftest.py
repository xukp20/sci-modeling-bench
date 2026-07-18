"""Hopper Controller test fixtures."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.hopper_controller import (
    EXPECTED_ROLLOUT_COUNT,
    POLICY_SIZE,
    HopperControllerDataset,
    HopperControllerValidator,
    policy_identity,
)


class TinyHopperControllerRepository:
    repo_id = "local/hopper-controller"
    resolved_revision = "tiny-hopper-controller-fixture"

    def __init__(self) -> None:
        policy_count = 10
        weights = np.zeros((policy_count, POLICY_SIZE), dtype=np.float32)
        weights[:, 0] = np.arange(policy_count, dtype=np.float32) / 10
        offsets = np.tile(
            np.asarray([-1.0, 1.0], dtype=np.float32),
            EXPECTED_ROLLOUT_COUNT // 2,
        )
        returns = np.arange(1, policy_count + 1, dtype=np.float32)[:, None] + offsets
        lengths = np.broadcast_to(
            np.arange(100, 100 + policy_count, dtype=np.int32)[:, None],
            returns.shape,
        ).copy()
        means = returns.mean(axis=1, dtype=np.float64)
        standard_deviations = returns.std(axis=1, ddof=1, dtype=np.float64)
        self.data = HFDataset.from_dict(
            {
                "source_index": np.arange(policy_count, dtype=np.int32),
                "policy_identity": [policy_identity(row) for row in weights],
                "policy_weights": weights,
                "source_return": np.arange(1, policy_count + 1, dtype=np.float32),
                "raw_returns": returns,
                "episode_lengths": lengths,
                "terminated": np.ones(returns.shape, dtype=np.bool_),
                "truncated": np.zeros(returns.shape, dtype=np.bool_),
                "rollout_count": np.full(
                    policy_count, EXPECTED_ROLLOUT_COUNT, dtype=np.int32
                ),
                "mean_return": means,
                "median_return": np.median(returns.astype(np.float64), axis=1),
                "return_std": standard_deviations,
                "return_standard_error": (
                    standard_deviations / np.sqrt(EXPECTED_ROLLOUT_COUNT)
                ),
            },
            features=Features(
                {
                    "source_index": Value("int32"),
                    "policy_identity": Value("string"),
                    "policy_weights": Sequence(Value("float32"), length=POLICY_SIZE),
                    "source_return": Value("float32"),
                    "raw_returns": Sequence(
                        Value("float32"), length=EXPECTED_ROLLOUT_COUNT
                    ),
                    "episode_lengths": Sequence(
                        Value("int32"), length=EXPECTED_ROLLOUT_COUNT
                    ),
                    "terminated": Sequence(
                        Value("bool"), length=EXPECTED_ROLLOUT_COUNT
                    ),
                    "truncated": Sequence(
                        Value("bool"), length=EXPECTED_ROLLOUT_COUNT
                    ),
                    "rollout_count": Value("int32"),
                    "mean_return": Value("float64"),
                    "median_return": Value("float64"),
                    "return_std": Value("float64"),
                    "return_standard_error": Value("float64"),
                }
            ),
        )

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


@pytest.fixture
def tiny_hopper_controller_dataset() -> HopperControllerDataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/hopper-controller",
                "version": "test",
                "default_split": "policies",
                "description": "Tiny Hopper Controller fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "policy_weights",
                        "description": "Policy parameter vector.",
                        "constraints": [
                            {
                                "kind": "length",
                                "minimum": POLICY_SIZE,
                                "maximum": POLICY_SIZE,
                            },
                            {"kind": "finite"},
                        ],
                    }
                ],
                "targets": [
                    {
                        "name": "mean_return",
                        "description": "Mean episodic return.",
                        "constraints": [{"kind": "finite"}],
                    }
                ],
                "splits": [
                    {
                        "name": "policies",
                        "description": "Tiny policy table.",
                        "num_rows": 10,
                    }
                ],
            }
        )
    )
    return HopperControllerDataset(
        manifest,
        TinyHopperControllerRepository(),
        config_name="hopper_controller",
        validator=HopperControllerValidator(),
    )
