from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.utr_mrl import UTRMRLCompositionalProtocol


def test_tiny_dataset_and_candidate_rows_validate(tiny_utr_mrl_dataset) -> None:
    report = tiny_utr_mrl_dataset.validate_dataset()
    candidate = UTRMRLCompositionalProtocol().build_input(
        tiny_utr_mrl_dataset
    ).data.candidates[0]

    assert report.valid
    assert tiny_utr_mrl_dataset.validate_inputs(candidate).valid


def test_candidate_schema_rejects_wrong_length(tiny_utr_mrl_dataset) -> None:
    report = tiny_utr_mrl_dataset.validate_inputs({"sequence": "ACGT"})

    assert not report.valid
    assert any(violation.field == "sequence" for violation in report.violations)


@pytest.mark.integration
def test_published_dataset_and_partition_are_frozen(
    published_utr_mrl_dataset,
) -> None:
    protocol = UTRMRLCompositionalProtocol()
    data = published_utr_mrl_dataset.load()
    agent_input = protocol.build_input(published_utr_mrl_dataset).data
    pool = protocol.candidate_pool(published_utr_mrl_dataset)

    assert len(data) == 318_468
    assert len(agent_input.observations) == 76_877
    assert len(agent_input.candidates) == 5_043
    assert len(pool) == 5_043
    assert min(pool["mean_ribosome_load"]) == pytest.approx(0.2857142857145)
    assert max(pool["mean_ribosome_load"]) == pytest.approx(12.0)
