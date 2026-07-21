"""Build a rectangular-photo variant of the materials overview.

This intentionally reads the established v2 layout and changes only the two
photographic masks and borders.  The v2 output remains untouched so the two
compositions can be compared directly.
"""

from __future__ import annotations

import base64
from pathlib import Path
import xml.etree.ElementTree as ET

import build_materials_overview_v2 as v2


OUTPUT = v2.ASSETS / "sci-modeling-bench-materials-overview.svg"


def composition_vector_cells(active_elements: set[int]) -> str:
    """Draw one compact 86-slot vector with only its non-zero elements colored."""

    background_cells = []
    active_cells = []
    cell_width = 2.15
    pitch = 2.75
    for atomic_number in range(1, 87):
        x = (atomic_number - 1) * pitch
        background_cells.append(
            f'<rect x="{x:.2f}" y="0" width="{cell_width}" height="22" '
            'rx="0.55" fill="#eef0f1" stroke="#cdd2d4" stroke-width="0.30"/>'
        )
        if atomic_number in active_elements:
            active_x = x - 0.70
            fill = v2.ELEMENT_COLORS[atomic_number]
            active_cells.append(
                f'<rect x="{active_x:.2f}" y="-3" width="3.55" height="28" '
                f'rx="1.35" fill="{fill}" stroke="#ffffff" stroke-width="0.42"/>'
            )
    return "\n        ".join((*background_cells, *active_cells))


def composition_panel() -> str:
    """Three formula-specific composition encodings feeding a Tc ranking."""

    rows = (
        (
            0,
            'YBa<tspan baseline-shift="sub" font-size="9.5">2</tspan>Cu'
            '<tspan baseline-shift="sub" font-size="9.5">3</tspan>O'
            '<tspan baseline-shift="sub" font-size="9.5">7</tspan>',
            {8, 29, 39, 56},
            447,
        ),
        (
            33,
            'Bi<tspan baseline-shift="sub" font-size="9.5">2</tspan>Sr'
            '<tspan baseline-shift="sub" font-size="9.5">2</tspan>CaCu'
            '<tspan baseline-shift="sub" font-size="9.5">2</tspan>O'
            '<tspan baseline-shift="sub" font-size="9.5">8</tspan>',
            {8, 20, 29, 38, 83},
            433,
        ),
        (
            66,
            'HgBa<tspan baseline-shift="sub" font-size="9.5">2</tspan>Ca'
            '<tspan baseline-shift="sub" font-size="9.5">2</tspan>Cu'
            '<tspan baseline-shift="sub" font-size="9.5">3</tspan>O'
            '<tspan baseline-shift="sub" font-size="9.5">8</tspan>',
            {8, 20, 29, 56, 80},
            419,
        ),
    )
    parts = [
        '  <!-- Formula-specific sparse composition encodings. -->',
        '  <g transform="translate(25 286)">',
        '    <path d="M415 85L451 -4" fill="none" stroke="#7b8489" '
        'stroke-width="0.8"/>',
    ]
    for y, formula, elements, point_x in rows:
        point_y = y + 11
        parts.extend(
            [
                f'    <text x="0" y="{y + 14}" font-family="\'Times New Roman\', Times, serif" '
                f'font-size="14.5" fill="#25292c">{formula}</text>',
                f'    <path d="M98 {point_y}H107" stroke="#9aa0a3" stroke-width="0.7"/>',
                f'    <g transform="translate(110 {y})">',
                f'        {composition_vector_cells(elements)}',
                '    </g>',
                f'    <path d="M348 {point_y}H{point_x - 13}" fill="none" '
                'stroke="#555e65" stroke-width="0.95" marker-end="url(#arrow)"/>',
                f'    <circle cx="{point_x}" cy="{point_y}" r="4.2" fill="#ffffff" '
                'stroke="#39434a" stroke-width="1.15"/>',
            ]
        )
    parts.extend(
        [
            '    <text x="385" y="38" text-anchor="middle" class="small">temperature?</text>',
            '    <text x="0" y="112" class="topic">86-element fractional encoding</text>',
            '    <text x="399" y="112" class="topic">T<tspan baseline-shift="sub" '
            'font-size="10">c</tspan> rank</text>',
            '  </g>',
        ]
    )
    return "\n".join(parts)


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def crop_lattice_with_margin() -> Path:
    """Retain the complete unit-cell outline and add a small safe margin."""

    source = v2.crop_lattice()
    document = source.read_text(encoding="utf-8")
    old_geometry = 'width="152"\n   height="520"\n   viewBox="0 0 152 520"'
    # Add vertical breathing room as well as the existing horizontal margin.
    # Keeping the artwork centred avoids clipping the top and bottom bonds when
    # the nested SVG is fitted into the overview's portrait-shaped viewport.
    new_geometry = 'width="260"\n   height="680"\n   viewBox="0 0 260 680"'
    if old_geometry not in document:
        raise RuntimeError("unexpected v2 lattice geometry")
    document = document.replace(old_geometry, new_geometry, 1)
    old_transform = 'transform="translate(-332.530452,-54.611108)"'
    new_transform = 'transform="translate(-230.530452,25.388892)"'
    if old_transform not in document:
        raise RuntimeError("unexpected v2 lattice crop transform")
    document = document.replace(old_transform, new_transform, 1)

    # The source SVG also contains explanatory callouts to the left of the
    # unit cell. They were hidden by the old tight crop; remove them explicitly
    # so a safer crop can reveal the complete bonds without exposing labels.
    annotation_ids = {
        "text11765",
        "g11787",
        "g11803",
        "g11810",
        "path11822",
        "path11824",
        "text11826",
        "text11830",
    }
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(document)
    parent_by_child = {child: parent for parent in root.iter() for child in parent}
    for element in list(root.iter()):
        if element.get("id") in annotation_ids:
            parent_by_child[element].remove(element)
    document = ET.tostring(root, encoding="unicode")
    destination = v2.HERE / "ybco-lattice-v3-cropped.svg"
    destination.write_text(document, encoding="utf-8")
    destination.chmod(0o644)
    return destination


def main() -> None:
    sources = {
        "figure_sources/materials/ybcO-lattice-v2.svg": (
            crop_lattice_with_margin(),
            "image/svg+xml",
        ),
        "figure_sources/materials/meissner-levitation.jpg": (
            v2.ASSETS / "references/materials/02-meissner-levitation.jpg",
            "image/jpeg",
        ),
        "figure_sources/materials/sprague-dawley-rat.jpg": (
            v2.ASSETS / "references/materials/03-sprague-dawley-rat.jpg",
            "image/jpeg",
        ),
    }
    for name, smiles in v2.MOLECULES.items():
        sources[f"figure_sources/materials/{name}-v2.svg"] = (
            v2.draw_molecule(name, smiles),
            "image/svg+xml",
        )

    document = v2.LAYOUT.read_text(encoding="utf-8")
    replacements = {
        "SciModelingBench materials discovery tasks, enriched layout":
            "SciModelingBench materials discovery tasks, rectangular photographs",
        '<clipPath id="latticeCrop"><rect x="19" y="4" width="125" height="226"/></clipPath>':
            '<clipPath id="latticeCrop"><rect x="24" y="20" width="116" height="200"/></clipPath>',
        '<image x="19" y="4" width="125" height="226"':
            '<image x="24" y="20" width="116" height="200"',
        '<text x="82" y="245" text-anchor="middle" class="detail">YBCO unit cell</text>':
            '<text x="82" y="253" text-anchor="middle" class="detail">YBCO unit cell</text>',
        '<clipPath id="meissnerCrop"><ellipse cx="302" cy="136" rx="145" ry="89"/></clipPath>':
            '<clipPath id="meissnerCrop"><rect x="164" y="47" width="268" height="178" rx="2"/></clipPath>',
        '<clipPath id="ratCrop"><ellipse cx="646" cy="292" rx="158" ry="112"/></clipPath>':
            '<clipPath id="ratCrop"><rect x="488" y="180" width="316" height="224" rx="2"/></clipPath>',
        '<ellipse cx="302" cy="136" rx="145" ry="89" fill="none" stroke="#c7d0d5" stroke-width="0.75"/>':
            '<rect x="164" y="47" width="268" height="178" rx="2" fill="none" stroke="#c7d0d5" stroke-width="0.75"/>',
        '<ellipse cx="646" cy="292" rx="158" ry="112" fill="none" stroke="#c7d0d5" stroke-width="0.75"/>':
            '<rect x="488" y="180" width="316" height="224" rx="2" fill="none" stroke="#c7d0d5" stroke-width="0.75"/>',
        '<text x="642" y="164" class="small">treatment</text>':
            '<text x="642" y="172" class="small">treatment response?</text>',
        '<text x="0" y="0" font-size="18.5" font-style="italic" font-weight="700">Materials Discovery:</text>\n'
        '    <text x="199" y="0" font-size="14.3">superconducting T<tspan baseline-shift="sub" font-size="10">c</tspan> ranking from composition and drug-response ranking from measured rat studies.</text>':
            '<text x="0" y="0"><tspan font-size="17.5" font-style="italic" '
            'font-weight="700">Materials Discovery &amp; Preclinical Toxicology:</tspan>'
            '<tspan dx="10" font-size="13.2" font-style="normal" font-weight="400">'
            'superconducting T<tspan baseline-shift="sub" font-size="9.5">c</tspan>'
            ' ranking and measured rat toxicology-response ranking.</tspan></text>',
    }
    for old, new in replacements.items():
        if old not in document:
            raise RuntimeError(f"expected v2 layout fragment not found: {old!r}")
        document = document.replace(old, new, 1)

    composition_start = document.index(
        "  <!-- Composition formulas encoded into a sparse 86-element vector. -->"
    )
    composition_end = document.index(
        "  <!-- Drug structures converge on the measured in-vivo response context. -->"
    )
    document = (
        document[:composition_start]
        + composition_panel()
        + "\n\n"
        + document[composition_end:]
    )
    for reference, (source, media_type) in sources.items():
        if reference not in document:
            raise RuntimeError(f"layout does not reference {reference!r}")
        document = document.replace(reference, data_uri(source, media_type))

    OUTPUT.write_text(document, encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
