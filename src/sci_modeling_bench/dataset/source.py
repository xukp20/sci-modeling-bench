"""Serializable references to remote dataset sources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HubDatasetSource:
    """Location of one dataset config in a Hugging Face repository."""

    repo_id: str
    config_name: str | None = None
    revision: str | None = None

    def __post_init__(self) -> None:
        if not self.repo_id.strip():
            raise ValueError("repo_id cannot be empty")
        if self.config_name is not None and not self.config_name.strip():
            raise ValueError("config_name cannot be empty")
        if self.revision is not None and not self.revision.strip():
            raise ValueError("revision cannot be empty")
