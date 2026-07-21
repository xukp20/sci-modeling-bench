"""Build a task-level SciModelingBench montage without modifying source figures."""

from __future__ import annotations

import base64
from pathlib import Path


HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[1]
OUTPUT = ASSETS / "sci-modeling-bench-task-montage.svg"


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def cropped_source(
    source_uri: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    view_x: float,
    view_y: float,
    view_width: float,
    view_height: float,
) -> str:
    """Place a viewBox crop of one established 900 x 560 source figure."""

    scale = min(width / view_width, height / view_height)
    rendered_width = view_width * scale
    rendered_height = view_height * scale
    offset_x = x + (width - rendered_width) / 2
    offset_y = y + (height - rendered_height) / 2
    image_x = offset_x - view_x * scale
    image_y = offset_y - view_y * scale
    clip_id = f"crop-{int(x)}-{int(y)}"
    return (
        f'<defs><clipPath id="{clip_id}"><rect x="{offset_x:.3f}" '
        f'y="{offset_y:.3f}" width="{rendered_width:.3f}" '
        f'height="{rendered_height:.3f}"/></clipPath></defs>'
        f'<g clip-path="url(#{clip_id})"><use href="{source_uri}" '
        f'transform="translate({image_x:.3f} {image_y:.3f}) scale({scale:.6f})"/></g>'
    )


def frame(x: int, y: int, width: int, height: int) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" '
        'fill="#ffffff" stroke="#92999d" stroke-width="1.35"/>'
    )


def caption(
    x: int,
    y: int,
    title: str,
    description: str,
    *,
    title_size: float = 23,
    body_size: float = 17.5,
) -> str:
    return (
        f'<text x="{x}" y="{y}" class="caption">'
        f'<tspan font-size="{title_size}" font-style="italic" '
        f'font-weight="700">{title}</tspan>'
        f'<tspan dx="9" font-size="{body_size}" font-style="normal" '
        f'font-weight="400">{description}</tspan>'
        '</text>'
    )


def main() -> None:
    bio_uri = data_uri(ASSETS / "sci-modeling-bench-bio-overview.svg", "image/svg+xml")
    materials_uri = data_uri(
        ASSETS / "sci-modeling-bench-materials-overview-v3-rect.svg",
        "image/svg+xml",
    )
    systems_uri = data_uri(
        ASSETS / "sci-modeling-bench-computational-systems-overview.svg",
        "image/svg+xml",
    )
    logo_uri = data_uri(ASSETS / "sci-modeling-bench-logo.png", "image/png")

    pieces: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1250" '
        'viewBox="0 0 1800 1250" role="img" aria-labelledby="title desc">',
        '<title id="title">SciModelingBench scientific task montage</title>',
        '<desc id="desc">Five framed task families: biomolecular design, '
        'superconducting materials, preclinical toxicology, neural architecture '
        'design, and embodied control.</desc>',
        '<style>',
        ".caption { font-family: 'Times New Roman', Times, serif; fill: #151515; }",
        ".header { font-family: 'Times New Roman', Times, serif; fill: #171a1c; }",
        '</style>',
        '<defs>',
        f'<image id="bio-source" x="0" y="0" width="900" height="560" href="{bio_uri}"/>',
        f'<image id="materials-source" x="0" y="0" width="900" height="560" href="{materials_uri}"/>',
        f'<image id="systems-source" x="0" y="0" width="900" height="560" href="{systems_uri}"/>',
        '</defs>',
        '<rect width="1800" height="1250" fill="#ffffff"/>',
        # Compact logo and wordmark. The source logo is cropped inside the nested SVG.
        '<svg x="38" y="20" width="66" height="66" viewBox="145 120 965 980" '
        'preserveAspectRatio="xMidYMid meet" overflow="hidden">'
        f'<image x="0" y="0" width="1254" height="1254" href="{logo_uri}"/>'
        '</svg>',
        '<text x="119" y="58" class="header" font-size="32" font-weight="700">'
        'SciModelingBench</text>',
        '<text x="120" y="82" class="header" font-size="15.5" fill="#555d62">'
        'Scientific modeling and design tasks</text>',
        # Frames: two modules above, three below.
        frame(40, 110, 1080, 600),
        frame(1140, 110, 620, 600),
        frame(40, 730, 400, 480),
        frame(460, 730, 500, 480),
        frame(980, 730, 780, 480),
        # Bio remains one connected composition. Crop away its existing footer.
        cropped_source(
            "#bio-source",
            x=52,
            y=122,
            width=1056,
            height=528,
            view_x=0,
            view_y=0,
            view_width=900,
            view_height=450,
        ),
        caption(
            58,
            684,
            "Biomolecular Design:",
            "DNA binding, 5′UTR-controlled translation, and GFP sequence–brightness prediction.",
            title_size=21,
            body_size=15.5,
        ),
        # Superconductor context above; formula encodings and ranking below.
        cropped_source(
            "#materials-source",
            x=1160,
            y=125,
            width=155,
            height=315,
            view_x=0,
            view_y=0,
            view_width=150,
            view_height=265,
        ),
        cropped_source(
            "#materials-source",
            x=1310,
            y=125,
            width=425,
            height=315,
            view_x=150,
            view_y=25,
            view_width=285,
            view_height=230,
        ),
        cropped_source(
            "#materials-source",
            x=1155,
            y=435,
            width=590,
            height=205,
            view_x=10,
            view_y=270,
            view_width=475,
            view_height=145,
        ),
        caption(
            1158,
            684,
            "Superconducting Materials:",
            "composition-based ranking by measured T<tspan baseline-shift=\"sub\" font-size=\"10\">c</tspan>.",
            title_size=18.5,
            body_size=13.5,
        ),
        # DrugMatrix molecular inputs and in-vivo measured response.
        cropped_source(
            "#materials-source",
            x=52,
            y=742,
            width=376,
            height=135,
            view_x=432,
            view_y=0,
            view_width=410,
            view_height=180,
        ),
        cropped_source(
            "#materials-source",
            x=52,
            y=870,
            width=376,
            height=270,
            view_x=486,
            view_y=170,
            view_width=322,
            view_height=265,
        ),
        caption(
            57,
            1184,
            "Preclinical Toxicology:",
            "rat clinical-pathology ranking.",
            title_size=17,
            body_size=13,
        ),
        # NASBench macro skeleton and two faithful architecture examples.
        cropped_source(
            "#systems-source",
            x=472,
            y=742,
            width=218,
            height=390,
            view_x=15,
            view_y=15,
            view_width=205,
            view_height=470,
        ),
        cropped_source(
            "#systems-source",
            x=686,
            y=742,
            width=262,
            height=190,
            view_x=220,
            view_y=35,
            view_width=155,
            view_height=215,
        ),
        cropped_source(
            "#systems-source",
            x=686,
            y=934,
            width=262,
            height=198,
            view_x=220,
            view_y=250,
            view_width=155,
            view_height=235,
        ),
        caption(
            477,
            1184,
            "Neural Architecture Design:",
            "NASBench-101 cell search.",
            title_size=17,
            body_size=13,
        ),
        # Hopper action space followed by three frozen rollout states.
        cropped_source(
            "#systems-source",
            x=992,
            y=742,
            width=180,
            height=390,
            view_x=370,
            view_y=15,
            view_width=235,
            view_height=230,
        ),
        cropped_source(
            "#systems-source",
            x=1184,
            y=742,
            width=180,
            height=390,
            view_x=605,
            view_y=15,
            view_width=230,
            view_height=230,
        ),
        cropped_source(
            "#systems-source",
            x=1376,
            y=742,
            width=180,
            height=390,
            view_x=365,
            view_y=245,
            view_width=235,
            view_height=245,
        ),
        cropped_source(
            "#systems-source",
            x=1568,
            y=742,
            width=180,
            height=390,
            view_x=605,
            view_y=245,
            view_width=230,
            view_height=245,
        ),
        caption(
            997,
            1184,
            "Embodied Control:",
            "Hopper-v5 policy ranking from frozen simulator rollouts.",
            title_size=17,
            body_size=13.5,
        ),
        '</svg>',
    ]

    OUTPUT.write_text("\n".join(pieces), encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
