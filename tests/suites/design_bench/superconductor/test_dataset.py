from __future__ import annotations

import pytest


@pytest.mark.integration
def test_published_dataset_and_default_partition_are_frozen(
    published_superconductor_dataset,
) -> None:
    from sci_modeling_bench.suites.design_bench.superconductor import (
        SuperconductorMeasuredPoolProtocol,
    )

    data = published_superconductor_dataset.load()
    protocol = SuperconductorMeasuredPoolProtocol()
    agent_input = protocol.build_input(published_superconductor_dataset)
    pool = protocol.candidate_pool(published_superconductor_dataset)

    assert len(data) == 15_164
    assert len(agent_input.observations) == 16_795
    assert len(agent_input.candidates) == 2_985
    assert len(pool) == 2_985
    assert min(pool["critical_temp_k"]) == pytest.approx(73.05)
    assert max(pool["critical_temp_k"]) == pytest.approx(143.0)
