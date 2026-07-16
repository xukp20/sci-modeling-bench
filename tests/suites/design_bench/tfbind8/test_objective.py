from __future__ import annotations

import pytest

from sci_modeling_bench.exceptions import ObjectiveInputError, ObjectiveLookupError
from sci_modeling_bench.suites.design_bench.tfbind8 import (
    TFBind8Dataset,
    TFBind8ExactObjective,
)


def test_exact_objective_returns_both_scores(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    objective = TFBind8ExactObjective(tiny_tfbind8_dataset)

    output = objective.evaluate({"sequence": "AACCGGTT"})

    assert output == {"e_score": 0.25, "normalized_e_score": 0.75}


def test_exact_objective_preserves_batch_order_and_repeats(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    objective = TFBind8ExactObjective(tiny_tfbind8_dataset)

    outputs = objective.evaluate_batch(
        [
            {"sequence": "TTTTTTTT"},
            {"sequence": "AAAAAAAA"},
            {"sequence": "TTTTTTTT"},
        ]
    )

    assert outputs == (
        {"e_score": 0.5, "normalized_e_score": 1.0},
        {"e_score": -0.5, "normalized_e_score": 0.0},
        {"e_score": 0.5, "normalized_e_score": 1.0},
    )


def test_exact_objective_rejects_invalid_candidate_with_batch_index(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    objective = TFBind8ExactObjective(tiny_tfbind8_dataset)

    with pytest.raises(ObjectiveInputError) as error:
        objective.evaluate_batch(
            [{"sequence": "AAAAAAAA"}, {"sequence": "AACCGGTX"}]
        )

    assert error.value.candidate_index == 1
    assert not error.value.report.valid


def test_exact_objective_distinguishes_missing_lookup_entry(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    objective = TFBind8ExactObjective(tiny_tfbind8_dataset)

    with pytest.raises(ObjectiveLookupError, match="absent from exact split"):
        objective.evaluate({"sequence": "CCCCCCCC"})


@pytest.mark.integration
def test_published_exact_objective_matches_published_row(
    published_tfbind8_dataset: TFBind8Dataset,
) -> None:
    observations = published_tfbind8_dataset.load()
    objective = TFBind8ExactObjective(published_tfbind8_dataset)

    assert objective.evaluate({"sequence": observations[12345]["sequence"]}) == {
        "e_score": observations[12345]["e_score"],
        "normalized_e_score": observations[12345]["normalized_e_score"],
    }
