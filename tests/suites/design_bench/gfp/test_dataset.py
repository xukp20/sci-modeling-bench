from __future__ import annotations

from sci_modeling_bench.suites.design_bench.gfp import protein_id


def test_tiny_canonical_dataset_is_valid(tiny_gfp_dataset) -> None:
    report = tiny_gfp_dataset.validate_dataset()

    assert report.valid
    assert len(tiny_gfp_dataset.load()) == 10


def test_dataset_validates_sequence_candidates(tiny_gfp_dataset) -> None:
    sequence = tiny_gfp_dataset.load()[0]["sequence"]

    assert tiny_gfp_dataset.validate_inputs({"sequence": sequence}).valid
    invalid = tiny_gfp_dataset.validate_inputs({"sequence": sequence[:-1] + "X"})
    assert not invalid.valid
    assert {item.code for item in invalid.violations} == {
        "invalid_alphabet_symbol"
    }


def test_protein_id_is_stable_content_identity(tiny_gfp_dataset) -> None:
    row = tiny_gfp_dataset.load()[0]

    assert row["protein_id"] == protein_id(row["sequence"])
    assert row["protein_id"].startswith("gfp_")
