"""Build the self-contained biomolecular overview SVG.

The layout stays human-editable while the published SVG embeds all raster and
vector source images so PDF/PNG exporters cannot silently drop local assets.
"""

from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image, ImageChops


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
ASSETS = REPOSITORY / "assets"
LAYOUT = HERE / "bio-overview-layout.svg"
OUTPUT = ASSETS / "sci-modeling-bench-bio-overview.svg"

PHO4_SOURCE = ASSETS / "references/bio/01-pho4-dna-1a0a.jpg"
GFP_SOURCE = ASSETS / "references/bio/05-gfp-1gfl.jpg"
PHO4_TRANSPARENT = HERE / "pho4-dna-transparent.png"
GFP_TRANSPARENT = HERE / "gfp-transparent.png"

SOURCES = {
    "figure_sources/bio/ribosome-translation-clean.svg": (
        HERE / "ribosome-translation-clean.svg",
        "image/svg+xml",
    ),
    "figure_sources/bio/pho4-dna-transparent.png": (
        PHO4_TRANSPARENT,
        "image/png",
    ),
    "figure_sources/bio/gfp-transparent.png": (
        GFP_TRANSPARENT,
        "image/png",
    ),
}


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def remove_white_background(source: Path, destination: Path) -> None:
    """Create a softly antialiased, tightly cropped transparent structure image."""

    image = Image.open(source).convert("RGBA")
    red, green, blue, _ = image.split()
    darkest = ImageChops.darker(red, ImageChops.darker(green, blue))
    alpha = darkest.point(lambda value: max(0, min(255, (247 - value) * 17)))
    image.putalpha(alpha)

    bounds = alpha.getbbox()
    if bounds is None:
        raise RuntimeError(f"no non-white content detected in {source}")
    left, top, right, bottom = bounds
    padding = 6
    bounds = (
        max(0, left - padding),
        max(0, top - padding),
        min(image.width, right + padding),
        min(image.height, bottom + padding),
    )
    image.crop(bounds).save(destination, optimize=True)
    destination.chmod(0o644)


def main() -> None:
    remove_white_background(PHO4_SOURCE, PHO4_TRANSPARENT)
    remove_white_background(GFP_SOURCE, GFP_TRANSPARENT)
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
