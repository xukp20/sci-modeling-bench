from __future__ import annotations

import pytest

from sci_modeling_bench.dataset.knowledge import Knowledge, KnowledgeResource


def test_knowledge_is_lazy_and_read_only() -> None:
    calls: list[str] = []

    def reader(path: str) -> str:
        calls.append(path)
        return "content"

    resource = KnowledgeResource(
        title="Overview",
        description=None,
        path="knowledge/overview.md",
        media_type="text/markdown",
        _reader=reader,
    )
    knowledge = Knowledge({"domain_overview": resource})

    assert calls == []
    assert list(knowledge) == ["domain_overview"]
    assert knowledge.read_text("domain_overview") == "content"
    assert resource.read_text() == "content"
    assert calls == ["knowledge/overview.md", "knowledge/overview.md"]

    with pytest.raises(TypeError):
        knowledge._resources["new"] = resource  # type: ignore[index]


def test_empty_knowledge_is_falsey() -> None:
    assert not Knowledge()
