from __future__ import annotations

from types import SimpleNamespace

from sci_modeling_bench.dataset import _hub


def test_hub_repository_pins_all_access_to_resolved_revision(
    monkeypatch,
    tmp_path,
) -> None:
    calls: list[tuple[str, str | None]] = []

    class FakeApi:
        def __init__(self, token=None) -> None:
            self.token = token

        def dataset_info(
            self,
            repo_id: str,
            revision: str | None = None,
            timeout: float | None = None,
        ):
            assert timeout == 30.0
            calls.append((repo_id, revision))
            return SimpleNamespace(sha="resolved-sha")

    resource = tmp_path / "resource.md"
    resource.write_text("resource", encoding="utf-8")

    def fake_download(**kwargs):
        assert kwargs["revision"] == "resolved-sha"
        return str(resource)

    def fake_load_dataset(repo_id, **kwargs):
        assert repo_id == "organization/dataset"
        assert kwargs["name"] == "tfbind8"
        assert kwargs["revision"] == "resolved-sha"
        assert kwargs["trust_remote_code"] is False
        return "loaded"

    monkeypatch.setattr(_hub, "HfApi", FakeApi)
    monkeypatch.setattr(_hub, "hf_hub_download", fake_download)
    monkeypatch.setattr(_hub, "load_dataset", fake_load_dataset)

    repository = _hub.HubDatasetRepository.resolve(
        "organization/dataset",
        revision="v1",
    )

    assert calls == [("organization/dataset", "v1")]
    assert repository.read_text("knowledge/resource.md") == "resource"
    assert repository.load(
        "tfbind8",
        "six6_ref_r1",
        streaming=False,
    ) == "loaded"


def test_hub_repository_uses_full_commit_without_metadata_request(monkeypatch) -> None:
    class FailApi:
        def __init__(self, token=None) -> None:
            raise AssertionError("full commit revisions must not query Hub metadata")

    monkeypatch.setattr(_hub, "HfApi", FailApi)
    revision = "0123456789abcdef0123456789abcdef01234567"

    repository = _hub.HubDatasetRepository.resolve(
        "organization/dataset",
        revision=revision,
    )

    assert repository.requested_revision == revision
    assert repository.resolved_revision == revision
