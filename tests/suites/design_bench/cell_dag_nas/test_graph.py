from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.cell_dag_nas._graph import (
    ArchitectureEncodingError,
    decode_architecture,
)
from tests.suites.design_bench.cell_dag_nas.conftest import A


def test_decode_matches_official_hash() -> None:
    decoded = decode_architecture(A)
    assert decoded.canonical_hash == "043721b9c7fe8c5fad811d47d83132ec"
    assert decoded.num_vertices == 2
    assert decoded.num_edges == 1


def test_decode_rejects_non_full_graph() -> None:
    invalid = A.copy()
    invalid[4] = 9
    with pytest.raises(ArchitectureEncodingError, match="every vertex") as caught:
        decode_architecture(invalid)
    assert caught.value.code == "non_full_dag"
