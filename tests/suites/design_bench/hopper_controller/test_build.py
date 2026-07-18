from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from sci_modeling_bench.suites.design_bench.hopper_controller.build import (
    audit_rollout_artifact,
    build_hopper_controller_release,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    POLICY_SIZE,
    policy_identity,
)


def test_audit_recomputes_artifact_structure_and_gate(tmp_path) -> None:
    rng = np.random.default_rng(17)
    weights = rng.normal(size=(8, POLICY_SIZE)).astype(np.float32)
    raw_returns = np.arange(8, dtype=np.float32)[:, None] + rng.normal(
        scale=0.1, size=(8, 50)
    ).astype(np.float32)
    artifact_path = tmp_path / "rollouts.npz"
    np.savez_compressed(
        artifact_path,
        policy_weights=weights,
        source_return=np.arange(8, dtype=np.float32),
        policy_identity=np.asarray([policy_identity(row) for row in weights]),
        raw_returns=raw_returns,
        episode_lengths=np.full((8, 50), 25, dtype=np.int32),
        terminated=np.ones((8, 50), dtype=np.bool_),
        truncated=np.zeros((8, 50), dtype=np.bool_),
        metadata=np.asarray(json.dumps({"schema_version": 1})),
    )

    report = audit_rollout_artifact(artifact_path)

    assert report["rows"] == 8
    assert report["repeats"] == 50
    assert report["episodes"] == 400
    assert report["environment_steps"] == 10_000
    assert set(report["gate"]) == {
        "signal",
        "fold_spearman",
        "fold_top32",
        "fold_top128",
    }


@pytest.mark.integration
def test_builder_packages_the_formal_rollout_artifact(tmp_path: Path) -> None:
    artifact = os.environ.get("SMB_HOPPER_ARTIFACT")
    if artifact is None:
        pytest.skip("SMB_HOPPER_ARTIFACT is not configured")

    provenance = build_hopper_controller_release(artifact, tmp_path)

    assert provenance["audit"]["rows"] == 3_200
    assert provenance["audit"]["repeats"] == 500
    assert "release_builder_revision" in provenance
    assert (tmp_path / "data/hopper_controller/policies.parquet").is_file()
