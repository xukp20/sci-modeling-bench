"""Build the self-contained computational-systems overview SVG."""

from __future__ import annotations

import base64
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
ASSETS = REPOSITORY / "assets"
LAYOUT = HERE / "computational-systems-overview-layout.svg"
OUTPUT = ASSETS / "sci-modeling-bench-computational-systems-overview.svg"

SOURCES = {
    "figure_sources/computational_systems/nasbench-model-structure.svg": (
        HERE / "nasbench-model-structure.svg",
        "image/svg+xml",
    ),
    "figure_sources/computational_systems/hopper-v5-action-space.svg": (
        HERE / "hopper-v5-action-space.svg",
        "image/svg+xml",
    ),
    "references/computational-systems/03-hopper-v5-frame-standing.png": (
        ASSETS / "references/computational-systems/03-hopper-v5-frame-standing.png",
        "image/png",
    ),
    "references/computational-systems/04-hopper-v5-frame-flexed.png": (
        ASSETS / "references/computational-systems/04-hopper-v5-frame-flexed.png",
        "image/png",
    ),
    "references/computational-systems/05-hopper-v5-frame-landing.png": (
        ASSETS / "references/computational-systems/05-hopper-v5-frame-landing.png",
        "image/png",
    ),
}


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def main() -> None:
    document = LAYOUT.read_text(encoding="utf-8")
    for reference, (source, media_type) in SOURCES.items():
        if reference not in document:
            raise RuntimeError(f"layout does not reference {reference!r}")
        document = document.replace(reference, data_uri(source, media_type))
    OUTPUT.write_text(document, encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
