"""Powder-doser tilt assembly: mounting plate + base plate.

Coordinate system
-----------------
* Origin (0,0,0) sits at the **dispense point** — the powder exit, directly
  above the centre of the cup on the scale.
* +X runs along the auger barrel of the doser (toward the rear of the rig).
* +Y is the hinge axis (horizontal, perpendicular to the auger).
* +Z is up.

Two-part assembly
-----------------
1. ``mounting_plate`` — the doser body bolts onto its top face. A U-slot
   opens out the front (+X face → wait, see HINGE_X below) so no plate
   material crosses the dispense column. Two clevis ears extend up and down
   straddling the plate at y = ±EAR_Y, with the hinge hole bored on the
   hinge axis through z = 0.

2. ``base_plate`` — sits on the bench on four legs. A tall mating tab
   (single tongue that fits between the two mounting-plate ears) rises from
   the front edge of the base plate to the hinge axis at z = 0. A separate
   pivot post toward the rear of the base plate gives a linear actuator a
   clevis point that is offset from the hinge axis, so pushing/pulling the
   actuator rotates the mounting plate (and the doser bolted to it) about
   the hinge.

The base plate's front edge stops *behind* the dispense point so the cup
sits in clear air directly under the dispense column on a tared scale on
the bench — the base plate footprint never crosses x = 0.

Outputs (relative to this file)
-------------------------------
* ``step/mounting_plate.step``
* ``step/base_plate.step``
* ``step/powder_doser_assembly.step``
* ``stl/mounting_plate.stl``
* ``stl/base_plate.stl``
* ``stl/powder_doser_assembly.stl``

All units are millimetres.
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Common geometry
# ---------------------------------------------------------------------------

HINGE_X = -35.0      # x coordinate of the hinge axis (and of the mating tab
                     # and the mounting-plate ears). Negative so the dispense
                     # point (x = 0) sits out past the front edge of the base
                     # plate, leaving the cup in clear air on the bench.
EAR_Y = 14.0         # +/- y position of inner faces of the clevis ears.
EAR_T = 6.0          # ear thickness (in Y).
HINGE_PIN = 5.2      # M5 clearance for the hinge pin.

# ---------------------------------------------------------------------------
# Mounting plate
# ---------------------------------------------------------------------------

MP_X = 130.0         # length along auger
MP_Y = 90.0          # width across hinge axis
MP_T = 6.0           # thickness
MP_X_CENTER = HINGE_X + 20.0   # plate centered slightly forward of hinge
                                # so the dispense U-slot reaches x = 0 cleanly

# Dispense U-slot (opens out the +X edge of the plate so the dispense
# column has clear air beneath it).
U_WIDTH = 28.0
U_DEPTH = 50.0       # how far back from the +X edge

# Doser-body clamp holes (M4 clearance, around the slot).
MP_HOLE_DIA = 4.4
MP_HOLE_POSITIONS = [
    # (dx from plate center, dy)
    (-50, +32), (-50, -32),
    (+50, +32), (+50, -32),
    (   0, +32), (   0, -32),
]

# Clevis ears (extend above and below the plate at y = ±EAR_Y, centered on
# x = HINGE_X). Hinge hole bored through Y at z = 0.
EAR_X = 28.0         # length along X
EAR_Z_TOP = +10.0    # ear top above plate top (gives meat above hinge hole)
EAR_Z_BOT = -28.0    # ear bottom below plate bottom


def make_mounting_plate() -> cq.Workplane:
    # Main slab, top surface at z = 0.
    plate = (
        cq.Workplane("XY")
        .workplane(offset=-MP_T / 2.0)
        .center(MP_X_CENTER, 0)
        .box(MP_X, MP_Y, MP_T)
    )

    # U-slot opening out the +X edge.
    slot_x_center = (MP_X_CENTER + MP_X / 2.0) - U_DEPTH / 2.0 + 5.0
    plate = (
        plate.faces(">Z")
        .workplane(centerOption="CenterOfBoundBox")
        .center(slot_x_center - MP_X_CENTER, 0)
        .rect(U_DEPTH + 10.0, U_WIDTH)
        .cutThruAll()
    )

    # Doser clamp holes.
    for dx, dy in MP_HOLE_POSITIONS:
        plate = (
            plate.faces(">Z")
            .workplane(centerOption="CenterOfBoundBox")
            .center(dx, dy)
            .hole(MP_HOLE_DIA)
        )

    # Clevis ears (two slabs straddling the plate in Z, fused into it).
    ear_h = EAR_Z_TOP - EAR_Z_BOT
    ear_z_center = (EAR_Z_TOP + EAR_Z_BOT) / 2.0
    for sy in (+1, -1):
        cy = sy * (EAR_Y + EAR_T / 2.0)
        ear = (
            cq.Workplane("XY")
            .workplane(offset=ear_z_center)
            .center(HINGE_X, cy)
            .box(EAR_X, EAR_T, ear_h)
        )
        # Round the top of the ear (the part above the plate).
        ear = ear.edges("|Y and >Z").fillet(min(EAR_X, ear_h) / 4.0 - 0.1)
        plate = plate.union(ear)

    # Hinge holes: bore Y-axis cylinders through each ear only (not through
    # the plate). Length covers ear thickness plus margin.
    for sy in (+1, -1):
        cy = sy * (EAR_Y + EAR_T / 2.0)
        cutter = (
            cq.Workplane("XZ")
            .workplane(offset=cy + sy * (EAR_T / 2.0 + 2.0))
            .center(HINGE_X, 0)
            .circle(HINGE_PIN / 2.0)
            .extrude(-sy * (EAR_T + 4.0))
        )
        plate = plate.cut(cutter)

    return plate


# ---------------------------------------------------------------------------
# Base plate
# ---------------------------------------------------------------------------

BP_X = 170.0         # length along auger (stays behind the dispense point)
BP_Y = 140.0         # width
BP_T = 8.0
BP_Z_TOP = -100.0    # top of base plate sits ~100 mm below the dispense
                     # origin (room for cup + scale beneath dispense)
BP_X_FRONT = HINGE_X - 5.0    # front edge stops 5 mm behind hinge so the
                              # tab is at the very front
BP_X_REAR = BP_X_FRONT - BP_X

# Mating tab: single tongue that fits between the mounting-plate ears.
TAB_T = (EAR_Y * 2.0) - 0.6    # 0.3 mm clearance per side
TAB_X = 26.0
TAB_Z_TOP = +6.0               # top of the tab, ear-side
TAB_Z_BOT = BP_Z_TOP           # base of the tab, base-plate-side

# Actuator pivot post (twin ears, offset in -X from hinge so the actuator
# rotates the doser about the hinge axis).
ACT_POST_X = HINGE_X - 90.0
ACT_POST_T = 8.0
ACT_POST_W = 24.0
ACT_POST_H = 35.0
ACT_PIN_Z = BP_Z_TOP + 28.0
ACT_PIN_DIA = 5.2

# Legs.
LEG_DIA = 14.0
LEG_HEIGHT = 75.0
LEG_INSET = 14.0
LEG_HOLE_DIA = 4.4


def make_base_plate() -> cq.Workplane:
    bp_x_center = (BP_X_FRONT + BP_X_REAR) / 2.0
    base = (
        cq.Workplane("XY")
        .workplane(offset=BP_Z_TOP - BP_T / 2.0)
        .center(bp_x_center, 0)
        .box(BP_X, BP_Y, BP_T)
    )

    # Bench bolt-down holes near each corner.
    for sx in (-1, +1):
        for sy in (-1, +1):
            cx = sx * (BP_X / 2.0 - 12.0)
            cy = sy * (BP_Y / 2.0 - 12.0)
            base = (
                base.faces(">Z")
                .workplane(centerOption="CenterOfBoundBox")
                .center(cx, cy)
                .hole(LEG_HOLE_DIA)
            )

    # Mating tab (rises from base top up to z = TAB_Z_TOP).
    tab_h = TAB_Z_TOP - TAB_Z_BOT
    tab_z_center = (TAB_Z_TOP + TAB_Z_BOT) / 2.0
    tab = (
        cq.Workplane("XY")
        .workplane(offset=tab_z_center)
        .center(HINGE_X, 0)
        .box(TAB_X, TAB_T, tab_h)
    )
    # Round the top of the tab (so ears can rotate clear).
    tab = tab.edges("|Y and >Z").fillet(min(TAB_T, TAB_X) / 2.0 - 0.1)
    # Hinge pin hole through Y at z = 0, x = HINGE_X (explicit primitive).
    hinge_cutter = (
        cq.Workplane("XZ")
        .center(HINGE_X, 0)
        .circle(HINGE_PIN / 2.0)
        .extrude(TAB_T * 2.0, both=True)
    )
    tab = tab.cut(hinge_cutter)
    base = base.union(tab)

    # Actuator pivot post.
    post_z_center = BP_Z_TOP + ACT_POST_H / 2.0
    for sy in (-1, +1):
        post = (
            cq.Workplane("XY")
            .workplane(offset=post_z_center)
            .center(ACT_POST_X, sy * (ACT_POST_T / 2.0 + 6.0))
            .box(ACT_POST_W, ACT_POST_T, ACT_POST_H)
        )
        base = base.union(post)
    # Actuator pin hole through Y at (ACT_POST_X, *, ACT_PIN_Z).
    act_cutter = (
        cq.Workplane("XZ")
        .center(ACT_POST_X, ACT_PIN_Z)
        .circle(ACT_PIN_DIA / 2.0)
        .extrude(BP_Y, both=True)
    )
    base = base.cut(act_cutter)

    # Legs (cylinders hanging down off each corner).
    leg_z_top = BP_Z_TOP - BP_T
    for sx in (-1, +1):
        for sy in (-1, +1):
            cx = bp_x_center + sx * (BP_X / 2.0 - LEG_INSET)
            cy = sy * (BP_Y / 2.0 - LEG_INSET)
            leg = (
                cq.Workplane("XY")
                .workplane(offset=leg_z_top)
                .center(cx, cy)
                .circle(LEG_DIA / 2.0)
                .extrude(-LEG_HEIGHT)
            )
            base = base.union(leg)

    return base


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

HINGE_AXIS_POINT = (HINGE_X, 0.0, 0.0)


def make_assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Build the full assembly. ``tilt_deg`` rotates the mounting plate
    about the hinge axis (Y line through HINGE_AXIS_POINT) for
    visualization."""
    mp = make_mounting_plate()
    bp = make_base_plate()

    asm = cq.Assembly()
    asm.add(bp, name="base_plate", color=cq.Color(0.65, 0.65, 0.72))
    asm.add(
        mp,
        name="mounting_plate",
        loc=cq.Location(
            cq.Vector(*HINGE_AXIS_POINT),
            cq.Vector(0, 1, 0),
            tilt_deg,
        ),
        color=cq.Color(0.90, 0.55, 0.20),
    )
    return asm


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_all(out_dir: Path) -> None:
    step_dir = out_dir / "step"
    stl_dir = out_dir / "stl"
    step_dir.mkdir(parents=True, exist_ok=True)
    stl_dir.mkdir(parents=True, exist_ok=True)

    mp = make_mounting_plate()
    bp = make_base_plate()

    cq.exporters.export(mp, str(step_dir / "mounting_plate.step"))
    cq.exporters.export(bp, str(step_dir / "base_plate.step"))
    cq.exporters.export(mp, str(stl_dir / "mounting_plate.stl"))
    cq.exporters.export(bp, str(stl_dir / "base_plate.stl"))

    asm = make_assembly(tilt_deg=0.0)
    asm.save(str(step_dir / "powder_doser_assembly.step"))
    compound = cq.Compound.makeCompound([mp.val(), bp.val()])
    cq.exporters.export(compound, str(stl_dir / "powder_doser_assembly.stl"))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    export_all(here)
    print("Exported STEP + STL to", here)
