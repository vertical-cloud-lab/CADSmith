"""Render the full Powder Doser assembly from several isometric angles.

Loads the committed assembly STEP solid, tessellates it to a temporary STL,
and renders it from a set of isometric viewpoints (four corners plus a
top-down and a low-front angle). Each viewpoint is written as a standalone PNG
and the set is tiled into a single ``assembly_iso_contact_sheet.png``.

Usage::

    xvfb-run -a python scripts/render_assembly_isos.py
    xvfb-run -a python scripts/render_assembly_isos.py \
        --step cad/powder-doser/powder_doser_assembly/part.step \
        --out-dir cad/powder-doser/powder_doser_assembly/iso

``xvfb-run`` (or any X / OSMesa backend) is needed for the offscreen VTK
render. See ``autofab/render.py`` for the rendering primitives.
"""

import argparse
import sys
import tempfile
from pathlib import Path

# Allow running as `python scripts/render_assembly_isos.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autofab.render import render_stl_iso_views  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STEP = REPO_ROOT / "cad" / "powder-doser" / "powder_doser_assembly" / "part.step"


def step_to_stl(step_path: Path, stl_path: Path) -> Path:
    """Tessellate a STEP solid to an STL mesh for rendering."""
    import cadquery as cq

    solid = cq.importers.importStep(str(step_path))
    cq.exporters.export(solid, str(stl_path))
    return stl_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", default=str(DEFAULT_STEP),
                        help="Assembly STEP file to render.")
    parser.add_argument("--out-dir", default=None,
                        help="Directory for the iso PNGs "
                             "(default: <step dir>/iso).")
    parser.add_argument("--prefix", default="assembly",
                        help="Filename prefix for each iso PNG.")
    args = parser.parse_args()

    step_path = Path(args.step).resolve()
    if not step_path.exists():
        raise SystemExit(f"STEP file not found: {step_path}")

    out_dir = Path(args.out_dir).resolve() if args.out_dir else step_path.parent / "iso"
    contact_sheet = out_dir / f"{args.prefix}_iso_contact_sheet.png"

    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "assembly.stl"
        print(f"Tessellating {step_path.name} -> STL ...")
        step_to_stl(step_path, stl_path)
        print(f"Rendering isometric views to {out_dir} ...")
        written = render_stl_iso_views(
            str(stl_path),
            str(out_dir),
            prefix=args.prefix,
            contact_sheet=str(contact_sheet),
        )

    for p in written:
        print(f"  wrote {p}")
    print(f"  wrote {contact_sheet} (contact sheet)")


if __name__ == "__main__":
    main()
