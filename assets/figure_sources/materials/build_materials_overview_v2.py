"""Build the richer, self-contained materials-discovery overview SVG."""

from __future__ import annotations

import base64
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
ASSETS = REPOSITORY / "assets"
LAYOUT = HERE / "materials-overview-v2-layout.svg"
OUTPUT = ASSETS / "sci-modeling-bench-materials-overview-v2.svg"

MOLECULES = {
    "acetaminophen": "CC(=O)Nc1ccc(O)cc1",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "caffeine": "Cn1cnc2n(C)c(=O)n(C)c(=O)c12",
}

ELEMENT_COLORS = {
    8: "#aa5d50",   # O
    20: "#87906b",  # Ca
    29: "#a77d4c",  # Cu
    38: "#667f91",  # Sr
    39: "#756b8e",  # Y
    56: "#3f6780",  # Ba
    80: "#56697a",  # Hg
    83: "#80697b",  # Bi
}


def data_uri(path: Path, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def draw_molecule(name: str, smiles: str) -> Path:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise RuntimeError(f"invalid SMILES for {name}")
    rdMolDraw2D.PrepareMolForDrawing(molecule)
    drawer = rdMolDraw2D.MolDraw2DSVG(300, 220)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 1.7
    options.padding = 0.06
    drawer.DrawMolecule(molecule)
    drawer.FinishDrawing()
    destination = HERE / f"{name}-v2.svg"
    destination.write_text(drawer.GetDrawingText(), encoding="utf-8")
    destination.chmod(0o644)
    return destination


def crop_lattice() -> Path:
    """Crop away the source annotations and retain the colored YBCO unit cell."""

    source = ASSETS / "references/materials/01-ybco-lattice.svg"
    document = source.read_text(encoding="utf-8")
    old_geometry = 'width="428.61768"\n   height="608.30255"'
    new_geometry = 'width="152"\n   height="520"\n   viewBox="0 0 152 520"'
    if old_geometry not in document:
        raise RuntimeError("unexpected YBCO source geometry")
    document = document.replace(old_geometry, new_geometry, 1)
    # CairoSVG handles nested SVGs with a zero-origin viewBox more consistently.
    # Fold the crop offset into the source artwork's outer transform so that the
    # vector remains portable instead of depending on renderer-specific clipping.
    old_transform = 'transform="translate(-44.530452,-12.611108)"'
    new_transform = 'transform="translate(-332.530452,-54.611108)"'
    if old_transform not in document:
        raise RuntimeError("unexpected YBCO source transform")
    document = document.replace(old_transform, new_transform, 1)
    destination = HERE / "ybco-lattice-v2-cropped.svg"
    destination.write_text(document, encoding="utf-8")
    destination.chmod(0o644)
    return destination


def element_vector_cells() -> str:
    cells = []
    cell_width = 3.2
    pitch = 4.05
    for atomic_number in range(1, 87):
        x = (atomic_number - 1) * pitch
        fill = ELEMENT_COLORS.get(atomic_number, "#e3e5e5")
        stroke = "#ffffff" if atomic_number in ELEMENT_COLORS else "#c9cdce"
        cells.append(
            f'<rect x="{x:.2f}" y="0" width="{cell_width}" height="21" '
            f'rx="0.55" fill="{fill}" stroke="{stroke}" stroke-width="0.35"/>'
        )
    return "\n      ".join(cells)


def main() -> None:
    sources = {
        "figure_sources/materials/ybcO-lattice-v2.svg": (
            crop_lattice(),
            "image/svg+xml",
        ),
        "figure_sources/materials/meissner-levitation.jpg": (
            ASSETS / "references/materials/02-meissner-levitation.jpg",
            "image/jpeg",
        ),
        "figure_sources/materials/sprague-dawley-rat.jpg": (
            ASSETS / "references/materials/03-sprague-dawley-rat.jpg",
            "image/jpeg",
        ),
    }
    for name, smiles in MOLECULES.items():
        sources[f"figure_sources/materials/{name}-v2.svg"] = (
            draw_molecule(name, smiles),
            "image/svg+xml",
        )

    document = LAYOUT.read_text(encoding="utf-8")
    document = document.replace("{{ELEMENT_VECTOR_CELLS}}", element_vector_cells())
    for reference, (source, media_type) in sources.items():
        if reference not in document:
            raise RuntimeError(f"layout does not reference {reference!r}")
        document = document.replace(reference, data_uri(source, media_type))
    OUTPUT.write_text(document, encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
