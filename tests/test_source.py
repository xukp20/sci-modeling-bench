import pytest

from sci_modeling_bench.dataset.source import HubDatasetSource


def test_hub_dataset_source_keeps_config_and_revision() -> None:
    source = HubDatasetSource(
        repo_id="sci-modeling-bench/design-bench",
        config_name="tfbind8",
        revision="main",
    )

    assert source.repo_id == "sci-modeling-bench/design-bench"
    assert source.config_name == "tfbind8"
    assert source.revision == "main"


@pytest.mark.parametrize("field", ["repo_id", "config_name", "revision"])
def test_hub_dataset_source_rejects_empty_values(field: str) -> None:
    values = {
        "repo_id": "organization/dataset",
        "config_name": "config",
        "revision": "main",
    }
    values[field] = " "

    with pytest.raises(ValueError, match=field):
        HubDatasetSource(**values)
