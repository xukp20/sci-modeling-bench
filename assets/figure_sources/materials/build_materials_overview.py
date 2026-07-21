"""Build the self-contained materials-discovery overview SVG."""

from __future__ import annotations

import base64
from pathlib import Path

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
ASSETS = REPOSITORY / "assets"
LAYOUT = HERE / "materials-overview-layout.svg"
OUTPUT = ASSETS / "sci-modeling-bench-materials-overview.svg"

MOLECULES = {
    "acetaminophen": "CC(=O)Nc1ccc(O)cc1",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "caffeine": "Cn1cnc2n(C)c(=O)n(C)c(=O)c12",
}

SOURCES = {
    "figure_sources/materials/ybcO-lattice.svg": (
        HERE / "ybco-lattice-cropped.svg",
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
    options.padding = 0.08
    drawer.DrawMolecule(molecule)
    drawer.FinishDrawing()
    destination = HERE / f"{name}.svg"
    destination.write_text(drawer.GetDrawingText(), encoding="utf-8")
    destination.chmod(0o644)
    return destination


def crop_lattice() -> Path:
    """Crop the source SVG to the unit cell and exclude its side annotation."""

    source = ASSETS / "references/materials/01-ybco-lattice.svg"
    document = source.read_text(encoding="utf-8")
    old_geometry = 'width="428.61768"\n   height="608.30255"'
    new_geometry = 'width="194"\n   height="608"\n   viewBox="235 0 194 608"'
    if old_geometry not in document:
        raise RuntimeError("unexpected YBCO source geometry")
    document = document.replace(old_geometry, new_geometry, 1)
    destination = HERE / "ybco-lattice-cropped.svg"
    destination.write_text(document, encoding="utf-8")
    destination.chmod(0o644)
    return destination


def main() -> None:
    sources = dict(SOURCES)
    crop_lattice()
    for name, smiles in MOLECULES.items():
        sources[f"figure_sources/materials/{name}.svg"] = (
            draw_molecule(name, smiles),
            "image/svg+xml",
        )

    document = LAYOUT.read_text(encoding="utf-8")
    for reference, (source, media_type) in sources.items():
        if reference not in document:
            raise RuntimeError(f"layout does not reference {reference!r}")
        document = document.replace(reference, data_uri(source, media_type))
    OUTPUT.write_text(document, encoding="utf-8")
    OUTPUT.chmod(0o644)
    print(OUTPUT)


if __name__ == "__main__":
    main()
