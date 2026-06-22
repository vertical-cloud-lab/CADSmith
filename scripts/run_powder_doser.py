"""Run the full CADSmith workflow on the Powder Doser assembly, part by part.

This drives the complete AutoFab pipeline (Planner -> Coder -> Executor ->
Validator -> Refiner loop) over every 3D-printed part of the Vertical Cloud
Lab "Powder Doser" (issue #5), using the self-contained engineering prompt in
``data/prompts/powder-doser-assembly-prompt.md``.

Design intent (why this script is shaped the way it is):

* **Part-by-part.** The master prompt describes a 10-part assembly. CADSmith
  converges best on one manifold solid at a time, so each printed part is run
  through the pipeline independently with a focused, self-contained sub-prompt
  that still carries the shared datum / tolerance context from the master
  spec. The assembly is generated last, once the parts are understood.
* **Opus base model.** Per the issue, the base model for every agent is set to
  Claude Opus (``AUTOFAB_BASE_MODEL``). The Validator judge follows the base
  model when it is Opus-class (see ``autofab.agents.get_judge_model``).
* **Resumable.** Each part writes its artifacts under
  ``outputs/powder_doser/<part>/``. A part that already has a ``result.json``
  is skipped, so the autonomous loop can be re-run / continued cheaply.

Usage::

    export ANTHROPIC_API_KEY=...        # required
    export AUTOFAB_BASE_MODEL=claude-opus-4-5
    xvfb-run -a python scripts/run_powder_doser.py            # all parts
    xvfb-run -a python scripts/run_powder_doser.py --only stepper_pinion cap
    xvfb-run -a python scripts/run_powder_doser.py --max-refinements 5

``xvfb-run`` (or any X / OSMesa backend) is needed only for the vision Judge's
VTK render; pass ``--no-vision`` to skip it.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

# Allow running as `python scripts/run_powder_doser.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autofab import agents  # noqa: E402
from autofab.pipeline import Pipeline  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER_PROMPT_PATH = REPO_ROOT / "data" / "prompts" / "powder-doser-assembly-prompt.md"

# Shared datum / tolerance context prepended to every part prompt so each run
# is self-contained while staying faithful to the master spec (sections 1, 6,
# 7 of the prompt). All dimensions are millimetres.
SHARED_CONTEXT = """\
This part belongs to the Vertical Cloud Lab "Powder Doser" — an auger-fed,
screw-metered dry-powder dispenser. Design it as a single, manifold,
FDM-printable solid (0.4 mm nozzle, ~0.2 mm layers; fin/wall features >= 2 mm).
All dimensions are in millimetres.

Shared fits & fasteners (apply where relevant):
- M3 clearance hole = 3.4 mm dia; M3 self-tap pilot = 2.7 mm; M3 setscrew pilot = 2.5 mm.
- M5 clearance hole = 5.4 mm dia.
- Auger / collar / bracket running fit over the 25.0 mm auger OD = bore 25.5 mm.
- Printed gears: module given per part, 20 deg pressure angle.
"""

# Ordered list of the ten 3D-printed parts (plus the bench-test auger and the
# threaded cap, which §2/§3 call out explicitly), each with a focused prompt.
PARTS = [
    (
        "auger_storage_full",
        """\
Archimedes auger — STORAGE variant (primary metering element), full length.

Outer tube: outer diameter 25.0, wall 2.0, so bore inner diameter 21.0
(outer radius 12.5, inner radius 10.5). Tube length 250.0, axis vertical (Z).
Top cap height 6.0 with 4 rectangular loading slots (width 4.0 x length 7.0)
on a 6.5 mm radius bolt circle, evenly spaced 90 degrees apart, plus a central
M3 pilot boss (2.7 mm pilot). Bottom funnel/cap height 12.0 tapering to a
single central exit hole diameter 3.0.

Internal Archimedean screw occupies ONLY the bottom one-third of the length
(screw top at ~83.33 mm from the bottom); the top two-thirds of the bore is
left open as a loose-powder reservoir. Screw: central shaft diameter 8.0
(radius 4.0) on the axis; single-start helical fin, pitch 10.0 mm/turn,
thickness 2.0; fin outer edge reaches the inner tube wall (radius ~10.5). The
helix is continuous over the bottom third.

External drive gear band (annular — do NOT fill the bore): spur gear module
1.0, 48 teeth, 20 deg pressure angle, face width 10.0; pitch diameter 48.0,
tip diameter 50.0, root diameter 45.5. Band centre is 83.33 mm from the
dispense (bottom) end; the 21 mm bore stays fully open straight through it.
""",
    ),
    (
        "auger_storage_short",
        """\
Archimedes auger — STORAGE variant, SHORT bench-test length (no gear band).

Outer tube: outer diameter 25.0, wall 2.0, bore inner diameter 21.0. Tube
length 90.0, axis vertical (Z). Top cap height 6.0 with 4 rectangular loading
slots (4.0 x 7.0) on a 6.5 mm radius bolt circle 90 deg apart plus a central
M3 pilot boss. Bottom funnel/cap height 12.0 tapering to a central exit hole
diameter 3.0.

Internal Archimedean screw occupies ONLY the bottom one-third (~30 mm); the
top two-thirds of the bore is open reservoir. Screw: central shaft diameter
8.0, single-start helical fin pitch 10.0 mm/turn, thickness 2.0, fin outer
edge reaching the inner wall. No external gear band on this bench-test part.
""",
    ),
    (
        "auger_threaded",
        """\
Archimedes auger — THREADED sealable variant (open filling end, screw-top).

Outer tube: outer diameter 25.0, wall 2.0, bore inner diameter 21.0, length
250.0, axis vertical (Z). The filling (top) end is a smooth open cylinder (no
4-slot cover). Bottom funnel/cap height 12.0 tapering to a central exit hole
diameter 3.0, with the same bottom-third single-start internal screw (shaft
diameter 8.0, pitch 10.0, fin thickness 2.0) and open upper reservoir.

Add a single-start EXTERNAL thread on the top 25.4 mm (1 inch) of the tube:
pitch 4.0 mm/turn, depth 1.0, crest (major) radius 12.5 (flush with the 25 mm
OD), root (minor) radius 11.5, tooth half-angle 58 deg, right-handed. The
thread must be strictly external — crests never exceed the 25 mm OD and roots
cut inward only; do NOT thread the inside of the tube. Keep the 48T drive gear
band (module 1.0, tip dia 50.0, face width 10.0, annular, bore open) centred
83.33 mm from the bottom end.
""",
    ),
    (
        "auger_cap",
        """\
Screw-on CAP for the threaded sealable auger (bottle-cap style).

A closed cup with an INTERNAL single-start thread matching the auger's
external thread but grown radially by 0.35 mm clearance for a hand fit:
pitch 4.0 mm/turn, depth 1.0, internal crest (minor) radius 11.85, internal
root (major) radius 12.85, right-handed. Wall thickness 3.0, solid top 3.0,
about 3.0 mm clearance space above the engaged threads. Outer diameter about
31.7, overall height about 31.0. Add a 1.5 mm x 45 deg chamfer on the top
outer edge. Axis vertical (Z), open end down.
""",
    ),
    (
        "stepper_pinion",
        """\
Stepper PINION for the NEMA 11 motor (couples motor to the 48T auger gear,
3:1 reduction).

Spur gear: 16 teeth, module 1.0, 20 deg pressure angle, face width 10.0;
pitch diameter 16.0, tip diameter 18.0, root diameter 13.5. Axis vertical (Z).
Central bore diameter 5.2 (5.0 mm NEMA 11 round shaft + 0.2 mm radial
slip-fit). A cylindrical hub diameter 9.0 rises 6.0 above the gear top face,
concentric with the bore. An M3 radial setscrew hole (2.5 mm pilot) passes
through the hub wall into the bore, its axis 3.0 mm above the gear top face,
perpendicular to and intersecting the bore.
""",
    ),
    (
        "servo_pinion",
        """\
SERVO PINION (one per MG996R tilt servo; 2:1 step-down to a 40T hinge gear).

Spur gear: 20 teeth, module 0.9083, 20 deg pressure angle, face width about
8.0; pitch diameter 18.17, tip diameter 20.2, root diameter about 15.9. Axis
vertical (Z). Central bore diameter 6.0 for the MG996R 25-tooth output spline,
with a single chordal flat (flat chord 5.0 mm across the 6.0 mm bore) to key
it. A central M3 countersink on the top face for the spline retaining horn
screw (counterbore for an M3 head over a 3.4 mm through hole).
""",
    ),
    (
        "mounting_plate",
        """\
MOUNTING PLATE ("the table") — the tilting platform that carries the auger.

Flat plate, thickness 6.0, lying in the XY plane, symmetric about X=0.
X envelope about -54.1 to +54.1 (width ~108.2). Y envelope about -15 to +115
(~130 deep). Cut an open U-notch in the +Y edge: width 32.0 (X = -16 to +16),
starting 35 mm back from the +Y front edge (so it runs from Y=+115 inward to
Y=+80), open to the +Y edge, for the auger to overhang. Add four M3 clearance
holes (3.4 mm) as bracket mounting points on the top surface near the notch
sides at X = +/-24, Y = +60 and Y = +10. Everything mounts on the top (+Z)
surface; nothing hangs below the plate.
""",
    ),
    (
        "baseplate",
        """\
BASEPLATE — the fixed ground reference that the mounting plate hinges on and
that carries the two tilt servos.

Flat rectangular forward tab in the XY plane, thickness 6.0: X from -100 to
+100 (200 wide), Y from +55 to +115 (60 deep). The two rear corners (the
Y=+115 edge, at X=-100 and X=+100) are chamfered 25.0 x 45 degrees. Four M5
clearance holes (5.4 mm) for mounting at X = +/-80, Y = +68 and Y = +105
(clear of the chamfers). The plate's bottom face sits at Z = -14 (top face at
Z = -8); model it as a flat slab with the four holes and the two chamfers.
""",
    ),
    (
        "auger_bracket",
        """\
AUGER BRACKET — split shaft-collar clamp that supports the spinning auger on
the mounting plate (front and rear use the same part).

A rectangular base flange 60.0 (X) x 12.0 (Y) x 14.0 (Z) lying on the plate,
with two M3 clearance holes (3.4 mm) through it at X = +/-24 (on the Y/Z
centre of the flange). Centred above it, a collar ring: outer diameter 33.5,
bore diameter 25.5 (running fit over the 25 mm auger OD), with the bore axis
horizontal along Y at Z = 29.25 above the flange bottom. The collar is split
by a vertical clamp slot 2.0 mm wide cut from the top down to the bore on the
+X side, with a pair of M3 clamp ears/holes (3.4 mm) straddling the slot so
tightening sets a running fit (do not seize the shaft).
""",
    ),
    (
        "tap_collar",
        """\
TAP COLLAR — independent split collar that vibrates and hammer-taps the auger
tube to stop powder bridging. It must spin-float on the tube, never clamp it.

Collar body: outer diameter 33.5, bore diameter 25.5 (free running fit over
the 25 mm auger OD), collar depth 17.0 along the bore axis (Y). Axis
horizontal along Y. A 2.0 mm clamp slot through one side (sets a running fit
only). On the -X face, a shallow coin-vibration-motor pad: a flat recess
diameter 10.0 x 1.0 mm deep. On the +Z face, a solenoid boss with a 7.5 mm
plunger clearance bore through to the collar bore region, flanked by two M3
clearance holes (3.4 mm) diagonally opposite on an 18.2 mm (across) x 16.0 mm
(along) pattern. On the +X side, a hardstop ear (a small rectangular tab ~10
wide x 8 tall x 6 thick projecting radially) that engages the mount-plate
stop so the collar cannot rotate with the auger.
""",
    ),
    (
        "tap_collar_mount_plate",
        """\
TAP-COLLAR MOUNT PLATE — bracket-style plate that holds the tap collar's
angular position via a rotation hardstop.

A vertical bracket plate in the XZ plane, thickness 6.0, about 50 wide (X) x
40 tall (Z), with a base foot flange (60 X x 12 Y x 6 Z) at the bottom for
bolting to the mounting plate using two M3 clearance holes (3.4 mm) at
X = +/-24. Above the foot, the upright plate has a central clearance opening
(diameter 34) for the auger/collar to pass, and a hardstop bump — a small
rectangular boss ~10 wide x 8 tall x 6 deep projecting toward the collar — set
to one side of the opening so the tap collar's hardstop ear butts against it
and is prevented from spinning with the auger.
""",
    ),
]

# Final integrative assembly run (tilt 0 deg): a single representative solid
# that places the major parts on their shared datum so the layout in §1 is
# visible. Off-the-shelf parts are modelled as simple envelopes.
ASSEMBLY = (
    "powder_doser_assembly",
    """\
POWDER DOSER ASSEMBLY at tilt = 0 degrees (everything flush). Build a single
combined solid (a union/compound is fine) that shows how the parts fit on a
common datum. Use the auger long axis = +Y; +Z is up; dispense tip at +Y.

Layout (millimetres):
- Mounting plate: flat slab in XY, thickness 6.0, top face at Z = 0, spanning
  X = -54 to +54, Y = -15 to +115, with a 32 mm wide U-notch open at the +Y
  edge.
- Auger: a tube outer diameter 25.0, length 250.0, lying horizontal with its
  axis along Y at Z = +29.25 above the plate top, centred on X = 0, the
  dispense end toward +Y overhanging the notch. Represent it as a plain
  cylinder with a 48-tooth-band collar (a ring outer diameter 50, width 10)
  at 83 mm from the +Y end.
- Two auger brackets (front and rear): rectangular blocks 60 (X) x 12 (Y) x
  14 (Z) on the plate top, each topped by a collar ring outer diameter 33.5
  cradling the auger at Z = 29.25, placed at Y ~ +70 and Y ~ +5.
- NEMA 11 motor block: a 28 x 28 x 32 box envelope beside the gear band at
  X = +32 (the gear centre distance) with its shaft along Y, plus a small
  16-tooth pinion ring (outer diameter 18) meshing the auger band.
- Baseplate: a flat slab X = -100 to +100, Y = +55 to +115, top face at
  Z = -8, with the two rear corners chamfered 25 x 45 deg.
- Two MG996R servo envelopes (40 x 20 x 43 boxes) on the baseplate, mirrored
  about X = 0 at X ~ +/-77, each with a small 20-tooth servo-pinion ring.
- Two M5 hinge pins: cylinders diameter 5.0 along X at the +Y end, at
  Z = +29.25, marking the tilt axis 10 mm forward of the baseplate front edge.

Keep it a clean, manifold representative model — exact gear teeth are not
required for the assembly view, but every listed block/cylinder must be
present in roughly the right place.
""",
)


def _write_part_outputs(out_dir: Path, result, render_src: Path | None):
    """Persist a finished pipeline result to ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if result.final_code:
        (out_dir / "model.py").write_text(result.final_code)

    for src_attr, dst_name in (("final_step_path", "part.step"),
                               ("final_stl_path", "part.stl")):
        src = getattr(result, src_attr)
        if src and Path(src).exists():
            shutil.copy2(src, out_dir / dst_name)

    if render_src and render_src.exists():
        shutil.copy2(render_src, out_dir / "render.png")

    (out_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2))


def run_part(name: str, prompt_body: str, args, work_dir: Path) -> dict:
    """Run one part through the full pipeline; return a summary dict."""
    out_dir = work_dir / name
    result_json = out_dir / "result.json"
    if result_json.exists() and not args.force:
        data = json.loads(result_json.read_text())
        print(f"[skip] {name} already done (converged={data.get('converged')})")
        return {"part": name, **_summary_from_dict(data), "skipped": True}

    print("\n" + "#" * 70)
    print(f"# PART: {name}")
    print("#" * 70)

    full_prompt = f"{SHARED_CONTEXT}\n{prompt_body}"
    pipeline = Pipeline(
        output_dir=str(out_dir / "_work"),
        max_error_retries=args.max_error_retries,
        max_refinement_iterations=args.max_refinements,
        verbose=True,
        use_vision=not args.no_vision,
    )
    start = time.time()
    result = pipeline.run(full_prompt, name=name)
    wall_s = time.time() - start

    # The last render is named <name>_iter<N>_render.png in the work dir.
    render_src = None
    renders = sorted((out_dir / "_work").glob(f"{name}_iter*_render.png"))
    if renders:
        render_src = renders[-1]

    _write_part_outputs(out_dir, result, render_src)
    summary = {
        "part": name,
        "converged": result.converged,
        "iterations": len(result.iterations),
        "llm_calls": result.total_llm_calls,
        "wall_seconds": round(wall_s, 1),
        "is_valid": bool(result.final_geometry and result.final_geometry.get("is_valid")),
        "volume_mm3": result.final_geometry.get("volume") if result.final_geometry else None,
        "skipped": False,
    }
    print(f"[done] {name}: converged={summary['converged']} "
          f"valid={summary['is_valid']} iters={summary['iterations']} "
          f"calls={summary['llm_calls']} {summary['wall_seconds']}s")
    return summary


def _summary_from_dict(data: dict) -> dict:
    geo = data.get("final_geometry") or {}
    return {
        "converged": data.get("converged"),
        "iterations": data.get("total_iterations"),
        "llm_calls": data.get("total_llm_calls"),
        "is_valid": bool(geo.get("is_valid")),
        "volume_mm3": geo.get("volume"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="cad/powder-doser")
    parser.add_argument("--max-refinements", type=int, default=3)
    parser.add_argument("--max-error-retries", type=int, default=3)
    parser.add_argument("--no-vision", action="store_true",
                        help="Skip the VTK three-view render / vision Judge.")
    parser.add_argument("--only", nargs="*", default=None,
                        help="Run only these part names (plus 'assembly').")
    parser.add_argument("--skip-assembly", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Re-run parts even if result.json exists.")
    args = parser.parse_args()

    work_dir = (REPO_ROOT / args.output_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"Base model : {agents.get_base_model()}")
    print(f"Judge model: {agents.get_judge_model()}")
    print(f"Output dir : {work_dir}")

    selected = PARTS
    run_assembly = not args.skip_assembly
    if args.only:
        wanted = set(args.only)
        selected = [p for p in PARTS if p[0] in wanted]
        run_assembly = ("assembly" in wanted) or (ASSEMBLY[0] in wanted)

    agents.reset_token_usage()
    summaries = []
    for name, body in selected:
        try:
            summaries.append(run_part(name, body, args, work_dir))
        except Exception as exc:  # keep the autonomous loop going
            print(f"[error] {name} raised {type(exc).__name__}: {exc}")
            summaries.append({"part": name, "converged": False, "error": str(exc)})

    if run_assembly:
        try:
            summaries.append(run_part(ASSEMBLY[0], ASSEMBLY[1], args, work_dir))
        except Exception as exc:
            print(f"[error] assembly raised {type(exc).__name__}: {exc}")
            summaries.append({"part": ASSEMBLY[0], "converged": False, "error": str(exc)})

    tokens = agents.get_token_usage()
    summary_doc = {
        "base_model": agents.get_base_model(),
        "judge_model": agents.get_judge_model(),
        "token_usage": tokens,
        "parts": summaries,
    }
    (work_dir / "summary.json").write_text(json.dumps(summary_doc, indent=2))

    print("\n" + "=" * 70)
    print("POWDER DOSER — RUN SUMMARY")
    print("=" * 70)
    for s in summaries:
        print(f"  {s['part']:<26} converged={s.get('converged')} "
              f"valid={s.get('is_valid')} vol={s.get('volume_mm3')}")
    print(f"\nToken usage: {tokens}")
    print(f"Summary written to {work_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
