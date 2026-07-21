"""Build the dense task montage directly from original SVG nodes and assets."""

from __future__ import annotations

import base64
import re
from pathlib import Path
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[1]
SOURCES = HERE.parent
OUTPUT = ASSETS / "sci-modeling-bench-task-montage.svg"

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def prepare_svg(
    path: Path,
    prefix: str,
    *,
    replacements: dict[str, str] | None = None,
    text_replacements: dict[str, str] | None = None,
) -> ET.Element:
    """Load original SVG code and namespace its IDs and CSS classes."""

    document = path.read_text(encoding="utf-8")
    for old, new in (replacements or {}).items():
        if old not in document:
            raise RuntimeError(f"{path} does not reference expected source {old!r}")
        document = document.replace(old, new)
    for old, new in (text_replacements or {}).items():
        document = document.replace(old, new)
    root = ET.fromstring(document)

    id_map: dict[str, str] = {}
    class_names: set[str] = set()
    for element in root.iter():
        old_id = element.get("id")
        if old_id:
            id_map[old_id] = f"{prefix}-{old_id}"
            element.set("id", id_map[old_id])
        class_names.update(element.get("class", "").split())

    for element in root.iter():
        classes = element.get("class")
        if classes:
            element.set(
                "class",
                " ".join(f"{prefix}-{name}" for name in classes.split()),
            )
        for attribute, value in list(element.attrib.items()):
            for old_id, new_id in id_map.items():
                value = value.replace(f"url(#{old_id})", f"url(#{new_id})")
                if value == f"#{old_id}":
                    value = f"#{new_id}"
            element.set(attribute, value)
        if local_name(element.tag) == "style" and element.text:
            css = element.text
            for name in sorted(class_names, key=len, reverse=True):
                css = re.sub(
                    rf"\.{re.escape(name)}(?![\w-])",
                    f".{prefix}-{name}",
                    css,
                )
            for old_id, new_id in id_map.items():
                css = css.replace(f"url(#{old_id})", f"url(#{new_id})")
            element.text = css
    return root


def serialize(element: ET.Element) -> str:
    return ET.tostring(element, encoding="unicode")


def children_without_chrome(
    root: ET.Element,
    *,
    background_size: tuple[str, str] | None = None,
    excluded_transforms: set[str] | None = None,
) -> str:
    children: list[str] = []
    for child in root:
        name = local_name(child.tag)
        if name in {"title", "desc", "metadata"}:
            continue
        if (
            name == "rect"
            and background_size
            and child.get("width") == background_size[0]
            and child.get("height") == background_size[1]
        ):
            continue
        if child.get("transform") in (excluded_transforms or set()):
            continue
        children.append(serialize(child))
    return "\n".join(children)


def nested_svg(
    x: float,
    y: float,
    width: float,
    height: float,
    view_box: str,
    content: str,
) -> str:
    return (
        f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
        f'viewBox="{view_box}" preserveAspectRatio="xMidYMid meet" overflow="hidden">'
        f'{content}</svg>'
    )


def frame(x: int, y: int, width: int, height: int) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" '
        'fill="#ffffff" stroke="#8f979b" stroke-width="1.25"/>'
    )


def footer_caption(
    x: int,
    y: int,
    title: str,
    description: str,
    *,
    title_size: float = 18,
    body_size: float = 14,
    second_line: str | None = None,
    anchor: str = "start",
) -> str:
    lines = (
        f'<text x="{x}" y="{y}" class="footer" font-size="{title_size}" '
        f'font-style="italic" font-weight="700" text-anchor="{anchor}">{title}</text>'
        f'<text x="{x}" y="{y + 16}" class="footer" font-size="{body_size}" '
        f'text-anchor="{anchor}">'
        f'{description}</text>'
    )
    if second_line is None:
        return lines
    return (
        lines
        + f'<text x="{x}" y="{y + 30}" class="footer" font-size="{body_size}" '
        f'text-anchor="{anchor}">'
        f'{second_line}</text>'
    )


ELEMENT_COLORS = {
    8: "#aa5d50",
    20: "#87906b",
    29: "#a77d4c",
    38: "#667f91",
    39: "#756b8e",
    56: "#3f6780",
    80: "#56697a",
    83: "#80697b",
}


def composition_cells(active_elements: set[int]) -> str:
    backgrounds: list[str] = []
    active: list[str] = []
    pitch = 4.05
    for atomic_number in range(1, 87):
        x = (atomic_number - 1) * pitch
        backgrounds.append(
            f'<rect x="{x:.2f}" y="0" width="3.15" height="22" rx="0.6" '
            'fill="#eef0f1" stroke="#ccd1d3" stroke-width="0.34"/>'
        )
        if atomic_number in active_elements:
            active.append(
                f'<rect x="{x - 1.0:.2f}" y="-4" width="5.15" height="30" '
                f'rx="1.7" fill="{ELEMENT_COLORS[atomic_number]}" '
                'stroke="#ffffff" stroke-width="0.5"/>'
            )
    return "".join((*backgrounds, *active))


def formula_text(x: int, y: int, formula: str) -> str:
    parts = re.split(r"(\d+)", formula)
    content = "".join(
        f'<tspan baseline-shift="sub" font-size="11">{part}</tspan>'
        if part.isdigit()
        else part
        for part in parts
        if part
    )
    return f'<text x="{x}" y="{y}" class="formula">{content}</text>'


def raster_crop(
    uri: str,
    clip_id: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    source_x: float,
    source_y: float,
    source_width: float,
    source_height: float,
    full_width: float,
    full_height: float,
) -> str:
    scale = min(width / source_width, height / source_height)
    rendered_width = source_width * scale
    rendered_height = source_height * scale
    offset_x = x + (width - rendered_width) / 2
    offset_y = y + (height - rendered_height) / 2
    image_x = offset_x - source_x * scale
    image_y = offset_y - source_y * scale
    return (
        f'<defs><clipPath id="{clip_id}"><rect x="{offset_x:.3f}" '
        f'y="{offset_y:.3f}" width="{rendered_width:.3f}" '
        f'height="{rendered_height:.3f}" rx="1.5"/></clipPath></defs>'
        f'<image x="{image_x:.3f}" y="{image_y:.3f}" '
        f'width="{full_width * scale:.3f}" height="{full_height * scale:.3f}" '
        f'href="{uri}" preserveAspectRatio="none" clip-path="url(#{clip_id})"/>'
    )


def main() -> None:
    bio_root = prepare_svg(
        SOURCES / "bio/bio-overview-layout.svg",
        "bio",
        replacements={
            "figure_sources/bio/ribosome-translation-clean.svg": data_uri(
                SOURCES / "bio/ribosome-translation-clean.svg", "image/svg+xml"
            ),
            "figure_sources/bio/pho4-dna-transparent.png": data_uri(
                SOURCES / "bio/pho4-dna-transparent.png", "image/png"
            ),
            "figure_sources/bio/gfp-transparent.png": data_uri(
                SOURCES / "bio/gfp-transparent.png", "image/png"
            ),
        },
        text_replacements={"translate(31 20)": "translate(12 20)"},
    )
    bio_content = children_without_chrome(
        bio_root,
        background_size=("900", "560"),
        excluded_transforms={"translate(38 474)"},
    )

    lattice_root = prepare_svg(
        SOURCES / "materials/ybco-lattice-v3-cropped.svg", "lattice"
    )
    lattice_content = children_without_chrome(lattice_root)

    molecule_contents: dict[str, str] = {}
    for name in ("acetaminophen", "ibuprofen", "caffeine"):
        root = prepare_svg(SOURCES / f"materials/{name}-v2.svg", f"mol-{name}")
        molecule_contents[name] = children_without_chrome(root)

    nas_root = prepare_svg(
        SOURCES / "computational_systems/nasbench-model-structure.svg",
        "nas",
        text_replacements={
            "font-size: 8.2px": "font-size: 9.2px",
            "font-size: 7.2px": "font-size: 7.8px",
            "font-size: 6.2px": "font-size: 6.8px",
        },
    )
    nas_defs = next(
        serialize(child) for child in nas_root if local_name(child.tag) == "defs"
    )
    nas_groups = [child for child in nas_root if local_name(child.tag) == "g"]
    if len(nas_groups) != 3:
        raise RuntimeError("unexpected NASBench source group structure")

    hopper_root = prepare_svg(
        SOURCES / "computational_systems/hopper-v5-action-space.svg", "hopper"
    )
    hopper_defs = next(
        serialize(child) for child in hopper_root if local_name(child.tag) == "defs"
    )
    hopper_groups = [child for child in hopper_root if local_name(child.tag) == "g"]
    if len(hopper_groups) != 2:
        raise RuntimeError("unexpected Hopper source group structure")

    meissner_uri = data_uri(
        ASSETS / "references/materials/02-meissner-levitation.jpg", "image/jpeg"
    )
    rat_uri = data_uri(
        ASSETS / "references/materials/03-sprague-dawley-rat.jpg", "image/jpeg"
    )
    rollout_uris = {
        "upright": data_uri(
            ASSETS / "references/computational-systems/03-hopper-v5-frame-standing.png",
            "image/png",
        ),
        "propulsion": data_uri(
            ASSETS / "references/computational-systems/04-hopper-v5-frame-flexed.png",
            "image/png",
        ),
        "landing": data_uri(
            ASSETS / "references/computational-systems/05-hopper-v5-frame-landing.png",
            "image/png",
        ),
    }

    pieces: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="1800" height="1160" viewBox="0 0 1800 1160" role="img" '
        'aria-labelledby="montage-title montage-desc">',
        '<title id="montage-title">SciModelingBench task montage, dense layout</title>',
        '<desc id="montage-desc">Five tightly framed scientific task families built '
        'directly from original SVG elements and source images.</desc>',
        '<style>',
        ".footer, .sectionLabel, .formula { font-family: 'Times New Roman', Times, serif; fill: #171a1c; }",
        ".sectionLabel { font-size: 17px; font-weight: 400; }",
        ".formula { font-size: 16px; }",
        ".rolloutLabel { font-family: 'Times New Roman', Times, serif; fill: #202428; }",
        '</style>',
        '<defs>',
        '<marker id="montage-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
        '<path d="M0 0L7 3.5L0 7Z" fill="#555e65"/></marker>',
        nas_defs,
        hopper_defs,
        '</defs>',
        '<rect width="1800" height="1160" fill="#ffffff"/>',
        frame(15, 15, 990, 535),
        frame(1020, 15, 765, 535),
        frame(15, 565, 410, 580),
        frame(440, 565, 660, 580),
        frame(1115, 565, 670, 580),
        # Bio: original layout nodes, without its old background and footer.
        nested_svg(27, 25, 966, 475, "0 0 900 450", bio_content),
        footer_caption(
            34,
            510,
            "Biomolecular Design:",
            "DNA-binding optimization and 5′UTR-controlled ribosome loading;",
            second_line="GFP sequence–brightness prediction from amino-acid variants.",
        ),
        # Superconductor: original lattice, original photo, redrawn source-native encoding.
        nested_svg(1034, 28, 165, 270, "0 0 260 680", lattice_content),
        raster_crop(
            meissner_uri,
            "meissner-v2",
            x=1210,
            y=30,
            width=560,
            height=265,
            source_x=170,
            source_y=170,
            source_width=2060,
            source_height=1280,
            full_width=2400,
            full_height=1716,
        ),
        '<text x="1116" y="311" text-anchor="middle" class="sectionLabel">YBCO unit cell</text>',
        '<text x="1490" y="311" text-anchor="middle" class="sectionLabel">Meissner levitation</text>',
    ]

    formula_rows = (
        (338, "YBa2Cu3O7", {8, 29, 39, 56}, 1751),
        (387, "Bi2Sr2CaCu2O8", {8, 20, 29, 38, 83}, 1738),
        (436, "HgBa2Ca2Cu3O8", {8, 20, 29, 56, 80}, 1725),
    )
    pieces.append('<path d="M1718 461L1757 329" fill="none" stroke="#737b80" stroke-width="1"/>')
    for row_y, formula, elements, point_x in formula_rows:
        pieces.extend(
            [
                formula_text(1035, row_y + 17, formula),
                f'<g transform="translate(1170 {row_y})">{composition_cells(elements)}</g>',
                f'<path d="M1525 {row_y + 11}H{point_x - 13}" fill="none" '
                'stroke="#555e65" stroke-width="1.15" marker-end="url(#montage-arrow)"/>',
                f'<circle cx="{point_x}" cy="{row_y + 11}" r="5" fill="#ffffff" '
                'stroke="#39434a" stroke-width="1.25"/>',
            ]
        )
    pieces.extend(
        [
            '<text x="1345" y="486" text-anchor="middle" class="sectionLabel">86-element fractional encoding</text>',
            '<text x="1690" y="486" class="sectionLabel">T<tspan baseline-shift="sub" font-size="12">c</tspan> rank</text>',
            footer_caption(
                1038,
                510,
                "Superconducting Materials:",
                "elemental-composition encoding and candidate ranking by measured",
                title_size=18,
                body_size=13.5,
                second_line=(
                    'superconducting critical temperature T<tspan baseline-shift="sub" '
                    'font-size="10">c</tspan>.'
                ),
            ),
            # Toxicology: individual RDKit SVG nodes and original rat photograph.
            nested_svg(28, 580, 118, 94, "0 0 300 220", molecule_contents["acetaminophen"]),
            nested_svg(155, 580, 118, 94, "0 0 300 220", molecule_contents["ibuprofen"]),
            nested_svg(282, 580, 118, 94, "0 0 300 220", molecule_contents["caffeine"]),
            '<text x="87" y="687" text-anchor="middle" class="sectionLabel">acetaminophen</text>',
            '<text x="214" y="687" text-anchor="middle" class="sectionLabel">ibuprofen</text>',
            '<text x="341" y="687" text-anchor="middle" class="sectionLabel">caffeine</text>',
            '<path d="M87 696C120 713 165 716 212 722M214 696V722M341 696C310 713 263 716 216 722" '
            'fill="none" stroke="#6e777d" stroke-width="1.1"/>',
            '<path d="M214 722V742" stroke="#555e65" stroke-width="1.2" '
            'marker-end="url(#montage-arrow)"/>',
            '<text x="229" y="735" class="sectionLabel">treatment response?</text>',
            raster_crop(
                rat_uri,
                "rat-v2",
                x=30,
                y=748,
                width=380,
                height=315,
                source_x=180,
                source_y=120,
                source_width=2440,
                source_height=1660,
                full_width=2816,
                full_height=1880,
            ),
            '<text x="220" y="1071" text-anchor="middle" class="sectionLabel">'
            'measured clinical-pathology response</text>',
            footer_caption(
                32,
                1103,
                "Preclinical Toxicology:",
                "context-aware treatment-condition ranking from",
                title_size=18,
                body_size=14,
                second_line="measured control-relative rat clinical-pathology endpoints.",
            ),
            # NAS: three original SVG groups, enlarged independently with no crop.
            '<text x="455" y="591" class="sectionLabel">NASBench-101 architecture</text>',
            f'<g transform="translate(455 608) scale(1.10)">{serialize(nas_groups[0])}</g>',
            f'<g transform="translate(690 670) scale(1.45) translate(-220 -20)">{serialize(nas_groups[1])}</g>',
            f'<g transform="translate(890 660) scale(1.40) translate(-220 -224)">{serialize(nas_groups[2])}</g>',
            footer_caption(
                1084,
                1103,
                "Neural Architecture Design:",
                "NASBench-101 macro-architecture, cell-operation,",
                title_size=18,
                body_size=14,
                second_line="and channel-allocation search.",
                anchor="end",
            ),
            # Hopper: source body/legend nodes at left, source rollout frames stacked right.
            '<text x="1130" y="591" class="sectionLabel">Hopper-v5 action space</text>',
            f'<g transform="translate(1132 615) scale(1.75) translate(-9 -10)">{serialize(hopper_groups[0])}</g>',
            f'<g transform="translate(1350 765) scale(0.98) translate(-151 -11)">{serialize(hopper_groups[1])}</g>',
        ]
    )

    rollout_rows = ((600, "upright"), (765, "propulsion"), (930, "landing"))
    for index, (row_y, label) in enumerate(rollout_rows):
        pieces.extend(
            [
                raster_crop(
                    rollout_uris[label],
                    f"rollout-{label}",
                    x=1535,
                    y=row_y,
                    width=142,
                    height=142,
                    source_x=75,
                    source_y=110,
                    source_width=330,
                    source_height=330,
                    full_width=480,
                    full_height=480,
                ),
                f'<text x="1687" y="{row_y + 58}" class="rolloutLabel" font-size="15">rollout</text>',
                f'<text x="1687" y="{row_y + 82}" class="rolloutLabel" font-size="19" '
                f'font-style="italic">{label}</text>',
            ]
        )
    pieces.extend(
        [
            footer_caption(
                1132,
                1103,
                "Embodied Control:",
                "Hopper-v5 controller ranking from frozen simulator rollouts",
                title_size=18,
                body_size=14,
                second_line="across upright, propulsion, and landing states.",
            ),
            '</svg>',
        ]
    )

    OUTPUT.write_text("\n".join(pieces), encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
