from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sci_modeling_bench.cache import ArtifactCache, ArtifactIdentity


def _identity() -> ArtifactIdentity:
    return ArtifactIdentity(
        artifact_id="test-derived-table",
        producer_version=1,
        dataset_id="test/dataset",
        repo_id="local/repository",
        config_name="default",
        split="train",
        resolved_revision="0123456789abcdef",
    )


def _prepare(cache: ArtifactCache, build):
    return cache.get_or_build(
        _identity(),
        load=lambda directory: (directory / "value.txt").read_text(encoding="utf-8"),
        build=build,
        write=lambda directory, value: (directory / "value.txt").write_text(
            value, encoding="utf-8"
        ),
    )


def test_cache_reuses_valid_artifact_and_rebuilds_corruption(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path)
    first = _prepare(cache, lambda: "first")
    second = _prepare(cache, lambda: "unexpected")

    assert first.value == second.value == "first"
    assert not first.report.cache_hit
    assert second.report.cache_hit
    assert first.report.path is not None

    metadata_path = first.report.path / "cache-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["files"][0]["sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    rebuilt = _prepare(cache, lambda: "rebuilt")
    assert rebuilt.value == "rebuilt"
    assert rebuilt.report.rebuilt
    assert not rebuilt.report.cache_hit


def test_disabled_cache_writes_nothing(tmp_path: Path) -> None:
    prepared = _prepare(ArtifactCache(tmp_path, enabled=False), lambda: "value")

    assert prepared.value == "value"
    assert not prepared.report.cache_enabled
    assert prepared.report.path is None
    assert list(tmp_path.iterdir()) == []


def test_concurrent_preparation_builds_once(tmp_path: Path) -> None:
    cache = ArtifactCache(tmp_path)
    count = 0
    count_lock = threading.Lock()

    def build() -> str:
        nonlocal count
        with count_lock:
            count += 1
        time.sleep(0.05)
        return "shared"

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: _prepare(cache, build), range(4)))

    assert count == 1
    assert [result.value for result in results] == ["shared"] * 4
    assert sum(result.report.cache_hit for result in results) == 3
