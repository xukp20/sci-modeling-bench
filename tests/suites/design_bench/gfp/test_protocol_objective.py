from __future__ import annotations

from sci_modeling_bench.suites.design_bench.gfp import (
    GFPLowerToHigherMeasuredPoolProtocol,
    GFPMeasuredObjective,
)


def test_protocol_exposes_visible_source_views_without_candidate_labels(
    tiny_gfp_dataset,
) -> None:
    protocol = GFPLowerToHigherMeasuredPoolProtocol(visible_max_percentile=50.0)

    agent_input = protocol.build_input(tiny_gfp_dataset)
    pool = protocol.candidate_pool(tiny_gfp_dataset)

    assert len(agent_input.protein_observations) == 5
    assert len(agent_input.nucleotide_observations) == 5
    assert len(agent_input.barcode_observations) == 5
    assert len(agent_input.candidates) == 5
    assert "median_log10_brightness" not in agent_input.candidates.column_names
    assert "unique_barcodes" not in agent_input.candidates.column_names
    assert "source_barcode_ids" not in agent_input.barcode_observations.column_names
    assert set(pool["median_log10_brightness"]) == {6.0, 7.0, 8.0, 9.0, 10.0}
    assert len(agent_input.reference_sequence) == 237


def test_objective_preserves_batch_order_and_repeats(tiny_gfp_dataset) -> None:
    data = tiny_gfp_dataset.load()
    objective = GFPMeasuredObjective(tiny_gfp_dataset)

    outputs = objective.evaluate_batch(
        [
            {"sequence": data[7]["sequence"]},
            {"sequence": data[2]["sequence"]},
            {"sequence": data[7]["sequence"]},
        ]
    )

    assert outputs == (
        {"median_log10_brightness": data[7]["median_log10_brightness"]},
        {"median_log10_brightness": data[2]["median_log10_brightness"]},
        {"median_log10_brightness": data[7]["median_log10_brightness"]},
    )
