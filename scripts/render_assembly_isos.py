"""Render the full Powder Doser assembly from several isometric angles.

The assembly ``model.py`` builds each component as its own CadQuery solid
before unioning them into the printed/STEP result. This script reuses those
individual components so each part can be rendered in its own colour — a brass
auger, grey plates/brackets, black motor & servo bodies, and green pinions —
matching the multi-colour reference renders in the ``vertical-cloud-lab/
powder-doser`` repository.

It renders one full isometric azimuth sweep (``az000`` … ``az315`` at a fixed
~30° elevation), writes each viewpoint as a standalone PNG, and tiles them into
``assembly_iso_contact_sheet.png``.

Usage::

    xvfb-run -a python scripts/render_assembly_isos.py
    xvfb-run -a python scripts/render_assembly_isos.py \
        --model cad/powder-doser/powder_doser_assembly/model.py \
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

from autofab.render import render_colored_iso_views  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSEMBLY_DIR = REPO_ROOT / "cad" / "powder-doser" / "powder_doser_assembly"
DEFAULT_MODEL = ASSEMBLY_DIR / "model.py"

# Component colours keyed by the variable names defined in the assembly
# model.py. Colours echo the reference assembly renders: brass auger, grey
# aluminium plates/brackets/pins, black motor & servo bodies, green pinions.
BRASS = (0.78, 0.60, 0.22)
GREY = (0.66, 0.69, 0.72)
BLACK = (0.13, 0.13, 0.14)
GREEN = (0.30, 0.66, 0.36)

PART_COLORS = {
    # Brass: the auger tube and its drive-gear band.
    "auger_tube": BRASS,
    "gear_collar": BRASS,
    # Grey: printed plates, brackets and the steel hinge pin.
    "mounting_plate": GREY,
    "baseplate": GREY,
    "front_bracket_base": GREY,
    "front_bracket_collar": GREY,
    "rear_bracket_base": GREY,
    "rear_bracket_collar": GREY,
    "hinge_pin": GREY,
    # Black: off-the-shelf motor / servo envelopes.
    "nema_block": BLACK,
    "left_servo": BLACK,
    "right_servo": BLACK,
    # Green: the meshing pinions.
    "motor_pinion": GREEN,
    "left_servo_pinion": GREEN,
    "right_servo_pinion": GREEN,
}


def load_colored_components(model_path: Path, tmp_dir: Path) -> list:
    """Execute the assembly ``model.py`` and export each coloured component.

    Returns a list of ``(stl_path, (r, g, b))`` tuples, one per named component
    in :data:`PART_COLORS`, skipping the union helpers (bridges / ``result``).
    """
    import cadquery as cq

    namespace = {"cq": cq, "__name__": "assembly_model"}
    exec(compile(model_path.read_text(), str(model_path), "exec"), namespace)

    items = []
    for name, color in PART_COLORS.items():
        obj = namespace.get(name)
        if obj is None:
            print(f"  [warn] component '{name}' not found in model; skipping")
            continue
        stl_path = tmp_dir / f"{name}.stl"
        cq.exporters.export(obj, str(stl_path))
        items.append((str(stl_path), color))
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=str(DEFAULT_MODEL),
                        help="Assembly model.py whose components are rendered.")
    parser.add_argument("--out-dir", default=None,
                        help="Directory for the iso PNGs "
                             "(default: <model dir>/iso).")
    parser.add_argument("--prefix", default="assembly_iso",
                        help="Filename prefix for each iso PNG.")
    args = parser.parse_args()

    model_path = Path(args.model).resolve()
    if not model_path.exists():
        raise SystemExit(f"model.py not found: {model_path}")

    out_dir = Path(args.out_dir).resolve() if args.out_dir else model_path.parent / "iso"
    contact_sheet = out_dir / f"{args.prefix}_contact_sheet.png"

    with tempfile.TemporaryDirectory() as tmp:
        print(f"Building coloured components from {model_path.name} ...")
        items = load_colored_components(model_path, Path(tmp))
        print(f"Rendering {len(items)} coloured parts to {out_dir} ...")
        written = render_colored_iso_views(
            items,
            str(out_dir),
            prefix=args.prefix,
            contact_sheet=str(contact_sheet),
        )

    for p in written:
        print(f"  wrote {p}")
    print(f"  wrote {contact_sheet} (contact sheet)")


if __name__ == "__main__":
    main()
