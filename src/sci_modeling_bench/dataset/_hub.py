"""Internal Hugging Face repository adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download

from sci_modeling_bench.exceptions import DatasetLoadError


class DatasetRepository(Protocol):
    """Internal resource interface shared by Dataset and Knowledge."""

    repo_id: str
    resolved_revision: str

    def read_text(self, path: str) -> str: ...

    def load(
        self,
        config_name: str,
        split: str,
        *,
        streaming: bool,
    ) -> Any: ...


@dataclass(frozen=True)
class HubDatasetRepository:
    """Pinned view of one Hugging Face Dataset repository."""

    repo_id: str
    requested_revision: str | None
    resolved_revision: str
    token: str | None = field(default=None, repr=False, compare=False)

    @classmethod
    def resolve(
        cls,
        repo_id: str,
        revision: str | None = None,
        *,
        token: str | None = None,
    ) -> HubDatasetRepository:
        try:
            info = HfApi(token=token).dataset_info(repo_id, revision=revision)
        except Exception as exc:
            raise DatasetLoadError(
                f"failed to resolve Hugging Face dataset {repo_id!r}"
            ) from exc
        if not info.sha:
            raise DatasetLoadError(
                f"Hugging Face dataset {repo_id!r} did not return a commit SHA"
            )
        return cls(
            repo_id=repo_id,
            requested_revision=revision,
            resolved_revision=info.sha,
            token=token,
        )

    def read_text(self, path: str) -> str:
        try:
            local_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=path,
                repo_type="dataset",
                revision=self.resolved_revision,
                token=self.token,
            )
            return Path(local_path).read_text(encoding="utf-8")
        except Exception as exc:
            raise DatasetLoadError(
                f"failed to read {path!r} from dataset {self.repo_id!r} "
                f"at revision {self.resolved_revision}"
            ) from exc

    def load(
        self,
        config_name: str,
        split: str,
        *,
        streaming: bool,
    ) -> Any:
        try:
            return load_dataset(
                self.repo_id,
                name=config_name,
                split=split,
                revision=self.resolved_revision,
                streaming=streaming,
                token=self.token,
                trust_remote_code=False,
            )
        except Exception as exc:
            raise DatasetLoadError(
                f"failed to load config {config_name!r}, split {split!r} from "
                f"dataset {self.repo_id!r} at revision {self.resolved_revision}"
            ) from exc
