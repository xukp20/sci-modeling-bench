"""Trusted, deterministic cache for derived benchmark artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Generic, TypeVar

from filelock import FileLock

_T = TypeVar("_T")
_CACHE_METADATA = "cache-metadata.json"


@dataclass(frozen=True)
class ArtifactIdentity:
    """Stable identity for one deterministic derived artifact."""

    artifact_id: str
    producer_version: int
    dataset_id: str
    repo_id: str
    config_name: str
    split: str
    resolved_revision: str
    schema_version: int = 1
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id must be non-empty")
        if self.producer_version < 1 or self.schema_version < 1:
            raise ValueError("artifact cache versions must be positive")
        # Fail at construction rather than during a later cache lookup.
        _canonical_json(self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["parameters"] = dict(self.parameters)
        return value

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.payload)).hexdigest()


@dataclass(frozen=True)
class PreparationReport:
    """Observable result of preparing one trusted derived artifact."""

    artifact_id: str
    cache_enabled: bool
    cache_hit: bool
    rebuilt: bool
    path: Path | None
    elapsed_sec: float


@dataclass(frozen=True)
class PreparedArtifact(Generic[_T]):
    """Prepared value paired with its cache report."""

    value: _T
    report: PreparationReport


class ArtifactCache:
    """Cache-aside storage with identity checks and atomic directory writes."""

    def __init__(self, root: str | Path | None = None, *, enabled: bool = True) -> None:
        self._enabled = bool(enabled)
        self._root = _default_cache_root() if root is None else Path(root).expanduser()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def root(self) -> Path:
        return self._root

    @classmethod
    def disabled(cls) -> ArtifactCache:
        return cls(enabled=False)

    def artifact_path(self, identity: ArtifactIdentity) -> Path:
        namespace = re.sub(r"[^A-Za-z0-9_.-]+", "-", identity.artifact_id).strip("-")
        if not namespace:
            raise ValueError("artifact_id does not contain a usable path component")
        return self.root / namespace / identity.digest

    def get_or_build(
        self,
        identity: ArtifactIdentity,
        *,
        load: Callable[[Path], _T],
        build: Callable[[], _T],
        write: Callable[[Path, _T], None],
    ) -> PreparedArtifact[_T]:
        """Load one valid artifact or build and atomically cache it."""

        started = time.monotonic()
        if not self.enabled:
            value = build()
            return PreparedArtifact(
                value,
                PreparationReport(
                    artifact_id=identity.artifact_id,
                    cache_enabled=False,
                    cache_hit=False,
                    rebuilt=False,
                    path=None,
                    elapsed_sec=time.monotonic() - started,
                ),
            )

        path = self.artifact_path(identity)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        lock = FileLock(str(path.with_suffix(".lock")))
        with lock:
            invalid = path.exists()
            if invalid:
                try:
                    self._validate(path, identity)
                    value = load(path)
                    return PreparedArtifact(
                        value,
                        PreparationReport(
                            artifact_id=identity.artifact_id,
                            cache_enabled=True,
                            cache_hit=True,
                            rebuilt=False,
                            path=path,
                            elapsed_sec=time.monotonic() - started,
                        ),
                    )
                except Exception:  # noqa: BLE001 - corrupted caches are rebuilt.
                    shutil.rmtree(path, ignore_errors=True)

            value = build()
            temporary = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
            try:
                temporary.mkdir(mode=0o700)
                write(temporary, value)
                files = _artifact_files(temporary)
                metadata = {
                    "schema_version": 1,
                    "identity": identity.payload,
                    "identity_sha256": identity.digest,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "package_version": _package_version(),
                    "files": files,
                }
                metadata_path = temporary / _CACHE_METADATA
                metadata_path.write_text(
                    json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                for item in temporary.rglob("*"):
                    item.chmod(0o700 if item.is_dir() else 0o600)
                temporary.replace(path)
            finally:
                shutil.rmtree(temporary, ignore_errors=True)

            return PreparedArtifact(
                value,
                PreparationReport(
                    artifact_id=identity.artifact_id,
                    cache_enabled=True,
                    cache_hit=False,
                    rebuilt=invalid,
                    path=path,
                    elapsed_sec=time.monotonic() - started,
                ),
            )

    def _validate(self, path: Path, identity: ArtifactIdentity) -> None:
        metadata = json.loads((path / _CACHE_METADATA).read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("artifact cache metadata must be an object")
        if metadata.get("schema_version") != 1:
            raise ValueError("artifact cache metadata schema is incompatible")
        if metadata.get("identity") != identity.payload:
            raise ValueError("artifact cache identity differs from the request")
        if metadata.get("identity_sha256") != identity.digest:
            raise ValueError("artifact cache identity checksum is invalid")
        raw_files = metadata.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise ValueError("artifact cache contains no declared files")
        expected_names: set[str] = set()
        for item in raw_files:
            if not isinstance(item, dict):
                raise ValueError("artifact cache file metadata is invalid")
            name = str(item.get("path") or "")
            if not name or Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("artifact cache file path is unsafe")
            file_path = path / name
            if not file_path.is_file():
                raise ValueError(f"artifact cache file is missing: {name}")
            if file_path.stat().st_size != item.get("size_bytes"):
                raise ValueError(f"artifact cache file size differs: {name}")
            if _file_sha256(file_path) != item.get("sha256"):
                raise ValueError(f"artifact cache file checksum differs: {name}")
            expected_names.add(name)
        actual_names = {
            str(item.relative_to(path))
            for item in path.rglob("*")
            if item.is_file() and item.name != _CACHE_METADATA
        }
        if actual_names != expected_names:
            raise ValueError("artifact cache contains undeclared files")


def artifact_identity(
    dataset: Any,
    *,
    artifact_id: str,
    producer_version: int,
    split: str,
    schema_version: int = 1,
    parameters: Mapping[str, Any] | None = None,
) -> ArtifactIdentity:
    """Construct an artifact identity from one pinned Dataset instance."""

    return ArtifactIdentity(
        artifact_id=artifact_id,
        producer_version=producer_version,
        dataset_id=str(dataset.metadata.dataset_id),
        repo_id=str(dataset.repo_id),
        config_name=str(dataset.config_name),
        split=split,
        resolved_revision=str(dataset.resolved_revision),
        schema_version=schema_version,
        parameters={} if parameters is None else parameters,
    )


def _default_cache_root() -> Path:
    explicit = os.environ.get("SCI_MODELING_BENCH_CACHE_DIR")
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "sci-modeling-bench"


def _artifact_files(directory: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        files.append(
            {
                "path": str(path.relative_to(directory)),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    if not files:
        raise ValueError("artifact writer produced no files")
    return files


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _package_version() -> str:
    try:
        return version("sci-modeling-bench")
    except PackageNotFoundError:
        return "source-tree"
