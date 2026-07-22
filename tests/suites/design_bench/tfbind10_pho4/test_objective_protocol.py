from __future__ import annotations

import numpy as np

from sci_modeling_bench.cache import ArtifactCache
from sci_modeling_bench.suites.design_bench.tfbind10_pho4 import (
    TFBind10Pho4LowerHalfProtocol,
    TFBind10Pho4PosteriorObjective,
)

from .conftest import SEQUENCES


def test_posterior_objective_returns_derived_affinity_in_order(
    tiny_tfbind10_pho4_dataset,
) -> None:
    objective = TFBind10Pho4PosteriorObjective(tiny_tfbind10_pho4_dataset)

    outputs = objective.evaluate_batch(
        [{"sequence": SEQUENCES[-1]}, {"sequence": SEQUENCES[0]}]
    )

    assert outputs[0]["affinity_score"] > outputs[1]["affinity_score"]
    assert objective.output_fields == ("affinity_score",)
    assert objective.landscape.row_sequence_indices.dtype == np.int32
    assert objective.landscape.row_sequence_indices.shape == (32,)
    assert not objective.landscape.row_sequence_indices.flags.writeable
    assert "affinity_score" not in {
        field.name for field in tiny_tfbind10_pho4_dataset.schema.targets
    }


def test_posterior_objective_reuses_derived_cache(
    tiny_tfbind10_pho4_dataset,
    tmp_path,
    monkeypatch,
) -> None:
    tiny_tfbind10_pho4_dataset._artifact_cache = ArtifactCache(tmp_path)
    first = TFBind10Pho4PosteriorObjective(tiny_tfbind10_pho4_dataset)
    first_report = first.prepare()[0]
    expected = first.evaluate_batch([{"sequence": SEQUENCES[-1]}])

    import sci_modeling_bench.suites.design_bench.tfbind10_pho4.objective as module

    def fail_rebuild(_observations):
        raise AssertionError("valid derived cache should bypass landscape construction")

    monkeypatch.setattr(module, "build_affinity_landscape", fail_rebuild)
    second = TFBind10Pho4PosteriorObjective(tiny_tfbind10_pho4_dataset)
    second_report = second.prepare()[0]

    assert not first_report.cache_hit
    assert second_report.cache_hit
    assert second.evaluate_batch([{"sequence": SEQUENCES[-1]}]) == expected


def test_protocol_exposes_only_raw_lower_half_observations(
    tiny_tfbind10_pho4_dataset,
) -> None:
    protocol = TFBind10Pho4LowerHalfProtocol()
    agent_input = protocol.build_input(tiny_tfbind10_pho4_dataset).data

    assert protocol.protocol_id == "design-bench/tfbind10-pho4-lower-half-v2"
    assert len(agent_input) == 16
    assert set(agent_input["sequence"]) == set(SEQUENCES[:4])
    assert agent_input.column_names == [
        "sequence",
        "replicate_id",
        "bound_count",
        "input_count",
        "bound_fraction",
        "input_fraction",
        "observed_ddg",
    ]
