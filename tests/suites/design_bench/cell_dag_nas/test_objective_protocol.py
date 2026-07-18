from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.cell_dag_nas import (
    CellDAGNASDesignBenchProtocol,
    CellDAGNASExactObjective,
)
from tests.suites.design_bench.cell_dag_nas.conftest import A, B


def test_objective_returns_repeats_and_mean(tiny_cell_dag_nas_dataset) -> None:
    objective = CellDAGNASExactObjective(tiny_cell_dag_nas_dataset)
    outputs = objective.evaluate_batch(
        ({"architecture": A}, {"architecture": B})
    )
    assert outputs[0]["test_accuracies"] == pytest.approx([0.1, 0.1, 0.1])
    assert outputs[0]["mean_test_accuracy"] == 0.1
    assert outputs[1]["mean_test_accuracy"] == 0.9


def test_default_protocol_selects_low_40_percent_without_mean(
    tiny_cell_dag_nas_dataset,
) -> None:
    visible = CellDAGNASDesignBenchProtocol().build_input(
        tiny_cell_dag_nas_dataset
    ).data
    assert len(visible) == 1
    assert visible.column_names == ["architecture", "test_accuracies"]
    assert visible[0]["architecture"] == A
    assert visible[0]["test_accuracies"] == pytest.approx([0.1, 0.1, 0.1])


@pytest.mark.integration
def test_published_protocol_has_frozen_visible_counts(
    published_cell_dag_nas_dataset,
) -> None:
    visible = CellDAGNASDesignBenchProtocol().build_input(
        published_cell_dag_nas_dataset
    ).data
    assert published_cell_dag_nas_dataset.resolved_revision == (
        "1c223e204fa5f88c8a0c55bd9a66865fdb8bcafa"
    )
    assert len(published_cell_dag_nas_dataset.load()) == 423_624
    assert len(visible) == 419_803
    assert visible.column_names == ["architecture", "test_accuracies"]
