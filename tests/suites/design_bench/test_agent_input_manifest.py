from __future__ import annotations

import json

import pytest
from datasets import Dataset as HFDataset

from sci_modeling_bench.protocol import AgentInputBundle, agent_table_view
from sci_modeling_bench.suites.design_bench import (
    DRUGMATRIX_ENDPOINTS,
    CellDAGNASDesignBenchProtocol,
    DrugMatrixCandidatePoolRankingTask,
    DrugMatrixMeasuredPoolProtocol,
    GFPLowerToHigherMeasuredPoolProtocol,
    HopperControllerLowerScoreProtocol,
    SuperconductorMeasuredPoolProtocol,
    TFBind10Pho4LowerHalfProtocol,
    TFBind8BlackBoxOptimizationTask,
    TFBind8DesignBenchProtocol,
    UTRMRLCompositionalProtocol,
)
from tests.suites.design_bench.cell_dag_nas.conftest import (
    tiny_cell_dag_nas_dataset,
)
from tests.suites.design_bench.drugmatrix.conftest import tiny_drugmatrix_dataset
from tests.suites.design_bench.gfp.conftest import tiny_gfp_dataset
from tests.suites.design_bench.hopper_controller.conftest import (
    tiny_hopper_controller_dataset,
)
from tests.suites.design_bench.superconductor.conftest import (
    tiny_superconductor_dataset,
)
from tests.suites.design_bench.tfbind10_pho4.conftest import (
    tiny_tfbind10_pho4_dataset,
)
from tests.suites.design_bench.tfbind8.conftest import (
    tiny_tfbind8_dataset,
    tiny_tfbind8_repository,
)
from tests.suites.design_bench.utr_mrl.conftest import tiny_utr_mrl_dataset


def _assert_complete_manifest(
    bundle: AgentInputBundle[object],
    *,
    expected_views: dict[str, HFDataset],
) -> None:
    manifest = bundle.manifest
    assert manifest.schema_version == 1
    assert manifest.dataset_id
    assert manifest.dataset_version
    assert manifest.dataset_description
    assert manifest.dataset_license
    assert manifest.repo_id
    assert manifest.resolved_revision
    assert manifest.config_name
    assert manifest.split
    assert manifest.split_description
    assert manifest.protocol_id
    assert {view.name for view in manifest.views} == set(expected_views)
    for view in manifest.views:
        table = expected_views[view.name]
        expected_role = "candidates" if view.name == "candidates" else "observations"
        assert view.role == expected_role
        assert view.num_rows == len(table)
        assert [field.name for field in view.fields] == table.column_names
        assert all(field.description for field in view.fields)
        assert all(field.physical_type for field in view.fields)
    json.loads(manifest.model_dump_json())


def test_manifest_rejects_visible_column_without_semantics(
    tiny_tfbind8_dataset,
) -> None:
    unknown = HFDataset.from_dict({"undocumented_value": [1.0]})
    with pytest.raises(ValueError, match="no Dataset FieldSpec"):
        agent_table_view(
            tiny_tfbind8_dataset,
            unknown,
            name="derived",
            role="auxiliary",
            description="A deliberately incomplete derived view.",
        )


def test_tfbind8_manifest_describes_visible_table_and_task(
    tiny_tfbind8_dataset,
) -> None:
    protocol_bundle = TFBind8DesignBenchProtocol().build_input(tiny_tfbind8_dataset)
    _assert_complete_manifest(
        protocol_bundle,
        expected_views={"observations": protocol_bundle.data},
    )
    assert protocol_bundle.manifest.task_id is None

    task_bundle = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=2,
    ).build_input()
    assert task_bundle.manifest.task_id == (
        "design-bench/tfbind8-black-box-optimization-v3"
    )


def test_tfbind10_manifest_exposes_no_candidate_view(
    tiny_tfbind10_pho4_dataset,
) -> None:
    bundle = TFBind10Pho4LowerHalfProtocol().build_input(
        tiny_tfbind10_pho4_dataset
    )
    _assert_complete_manifest(bundle, expected_views={"observations": bundle.data})
    assert [view.name for view in bundle.manifest.views] == ["observations"]
    assert "affinity_score" not in bundle.manifest.model_dump_json()


def test_cell_dag_manifest_describes_generated_alias_view(
    tiny_cell_dag_nas_dataset,
) -> None:
    bundle = CellDAGNASDesignBenchProtocol().build_input(
        tiny_cell_dag_nas_dataset
    )
    _assert_complete_manifest(bundle, expected_views={"observations": bundle.data})


def test_superconductor_manifest_describes_vectors_and_element_order(
    tiny_superconductor_dataset,
) -> None:
    bundle = SuperconductorMeasuredPoolProtocol(
        visible_max_percentile=50.0,
        include_descriptors=True,
    ).build_input(tiny_superconductor_dataset)
    _assert_complete_manifest(
        bundle,
        expected_views={
            "observations": bundle.data.observations,
            "candidates": bundle.data.candidates,
        },
    )
    context = {item.name: item.value for item in bundle.manifest.context}
    assert len(context["element_symbols"]) == 86
    assert len(context["descriptor_names"]) == 81


def test_hopper_manifest_describes_rollouts_and_policy_layout(
    tiny_hopper_controller_dataset,
) -> None:
    bundle = HopperControllerLowerScoreProtocol(visible_fraction=0.5).build_input(
        tiny_hopper_controller_dataset
    )
    _assert_complete_manifest(
        bundle,
        expected_views={
            "observations": bundle.data.observations,
            "candidates": bundle.data.candidates,
        },
    )
    context = {item.name: item.value for item in bundle.manifest.context}
    assert context["parameter_order"] == ["W1", "b1", "W2", "b2", "W3", "b3", "logstd"]
    assert context["rollout_count"] == 500


def test_gfp_manifest_covers_every_multilevel_view_without_candidate_labels(
    tiny_gfp_dataset,
) -> None:
    bundle = GFPLowerToHigherMeasuredPoolProtocol(
        visible_max_percentile=50.0
    ).build_input(tiny_gfp_dataset)
    _assert_complete_manifest(
        bundle,
        expected_views={
            "protein_observations": bundle.data.protein_observations,
            "nucleotide_observations": bundle.data.nucleotide_observations,
            "barcode_observations": bundle.data.barcode_observations,
            "candidates": bundle.data.candidates,
        },
    )
    candidates = next(
        view for view in bundle.manifest.views if view.name == "candidates"
    )
    assert "median_log10_brightness" not in {field.name for field in candidates.fields}
    assert {item.name for item in bundle.manifest.context} == {"reference_sequence"}


def test_utr_manifest_does_not_disclose_partition_annotations(
    tiny_utr_mrl_dataset,
) -> None:
    bundle = UTRMRLCompositionalProtocol().build_input(tiny_utr_mrl_dataset)
    _assert_complete_manifest(
        bundle,
        expected_views={
            "observations": bundle.data.observations,
            "candidates": bundle.data.candidates,
        },
    )
    serialized = bundle.manifest.model_dump_json()
    assert "has_uaug" not in serialized
    assert "kozak_quality" not in serialized


@pytest.mark.parametrize("endpoint", DRUGMATRIX_ENDPOINTS)
def test_drugmatrix_manifest_supports_every_endpoint_task(
    tiny_drugmatrix_dataset,
    endpoint: str,
) -> None:
    protocol_bundle = DrugMatrixMeasuredPoolProtocol().build_input(
        tiny_drugmatrix_dataset
    )
    _assert_complete_manifest(
        protocol_bundle,
        expected_views={
            "observations": protocol_bundle.data.observations,
            "candidates": protocol_bundle.data.candidates,
        },
    )
    task_bundle = DrugMatrixCandidatePoolRankingTask(
        tiny_drugmatrix_dataset,
        endpoint=endpoint,
        submission_size=2,
    ).build_input()
    assert task_bundle.manifest.task_id == (
            f"design-bench/drugmatrix-{endpoint}-candidate-pool-ranking-v2"
    )
