"""Lazy, read-only domain knowledge resources bound to a dataset revision."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class KnowledgeResource:
    """Metadata and lazy text access for one knowledge resource."""

    title: str
    description: str | None
    path: str
    media_type: str
    _reader: Callable[[str], str] = field(repr=False, compare=False)

    def read_text(self) -> str:
        """Read this resource from the dataset's resolved repository revision."""

        return self._reader(self.path)


class Knowledge(Mapping[str, KnowledgeResource]):
    """Read-only mapping of stable names to lazily loaded text resources."""

    def __init__(self, resources: Mapping[str, KnowledgeResource] | None = None) -> None:
        self._resources = MappingProxyType(dict(resources or {}))

    def __getitem__(self, name: str) -> KnowledgeResource:
        return self._resources[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._resources)

    def __len__(self) -> int:
        return len(self._resources)

    def read_text(self, name: str) -> str:
        """Read a named resource without eagerly loading any other resource."""

        return self[name].read_text()
