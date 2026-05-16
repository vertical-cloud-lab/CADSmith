"""Powder doser AUGER — fallback hand-coded part.

CADSmith was run with all 5 agents pinned to claude-opus-4-7 and
max_refinement_iterations=5 on this same prompt (see
outputs/powder_doser_auger_log.json) and failed to produce a manifold helix
sweep across 6 iterations. The Coder repeatedly fell into degenerate
boolean fusions where the helix sweep silently produced an empty solid or
where subsequent unions cleaned the helix away.

This file provides a deterministic equivalent keyed off the SAME
parameters the user requested (auger_tube_outer_d, auger_tube_length,
auger_wall_thk, auger_stair_thk, auger_stair_pitch, plus a top cap and
dispense funnel matching the v5 archimedes-auger from powder-doser PR
#16). It uses cq.Workplane.sweep with isFrenet=True on a helical wire —
the canonical CadQuery helix-fin pattern. All chassis-style cuts/unions
are done BEFORE the helix is added (the helix is the last union with
clean=False) to avoid the OCCT cleanup step erasing the thin fin.

Final shape is assigned to `result`.
"""
import math
import cadquery as cq

# ===== ADJUSTABLE PARAMETERS (mm) — match chassis script =====
auger_tube_outer_d = 25.0
auger_tube_length  = 250.0
auger_wall_thk     = 2.0
auger_stair_thk    = 2.0
auger_stair_pitch  = 10.0

# Derived
outer_r = auger_tube_outer_d / 2.0
inner_r = outer_r - auger_wall_thk
shaft_r = 3.0
fin_sink = 0.4
funnel_h = 12.0
exit_r = 1.5
top_cap_h = 6.0
boss_h = 6.0
# v3: spindle that bridges from top of tube up into the ST-FC01 coupler.
# v3.2: spindle bumped from Ø5 → Ø7 mm to address PLA cantilever bending
# stress (Edison P1: a Ø5 × 24 mm PLA cantilever under 20 N transverse
# load reaches ~39 MPa, above PLA's Z-direction ~30 MPa yield; Ø7 brings
# this down to ~14 MPa, well within margin). The ST-FC01 5–5 mm coupler
# can accommodate up to Ø8 with the supplied bore; user may alternately
# embed a Ø5 steel rod through a Ø5 axial pilot in the spindle.
spindle_d = 7.0
spindle_l = 24.0
m3_pilot_d = 2.5
slot_count = 4
slot_len = 7.0
slot_w = 4.0
slot_r = 6.5

helix_z_start = funnel_h
helix_z_end   = auger_tube_length - top_cap_h
helix_height  = helix_z_end - helix_z_start
n_turns       = max(1, helix_height / auger_stair_pitch)


# ----- Step 1: Solid base cylinder -----
result = cq.Workplane("XY").circle(outer_r).extrude(auger_tube_length)

# ----- Step 2: Cut the straight inner bore -----
bore = (
    cq.Workplane("XY")
    .workplane(offset=funnel_h)
    .circle(inner_r)
    .extrude(auger_tube_length - funnel_h - top_cap_h)
)
result = result.cut(bore)

# ----- Step 3: Cut the dispense funnel cone -----
funnel_cut = cq.Solid.makeCone(exit_r, inner_r, funnel_h)
result = result.cut(cq.Workplane(obj=funnel_cut))

# ----- Step 4: Add the central support shaft -----
shaft = (
    cq.Workplane("XY")
    .workplane(offset=helix_z_start)
    .circle(shaft_r)
    .extrude(helix_height)
)
result = result.union(shaft)

# ----- Step 5: M3 boss below cap -----
boss = (
    cq.Workplane("XY")
    .workplane(offset=auger_tube_length - top_cap_h - boss_h)
    .circle(4.0)
    .extrude(boss_h)
)
result = result.union(boss)

# ----- Step 5b (v3): Ø5 spindle on top of the auger that engages the coupler.
# Bridges the v2 dead-air gap between auger Z=auger_tube_length and the
# coupler chamber bottom. -----
spindle = (
    cq.Workplane("XY")
    .workplane(offset=auger_tube_length)
    .circle(spindle_d / 2.0)
    .extrude(spindle_l)
)
result = result.union(spindle)

# ----- Step 6: Cut M3 pilot through cap + boss -----
pilot_depth = top_cap_h + boss_h
pilot = (
    cq.Workplane("XY")
    .workplane(offset=auger_tube_length - pilot_depth)
    .circle(m3_pilot_d / 2)
    .extrude(pilot_depth + 0.1)
)
result = result.cut(pilot)

# ----- Step 7: Four loading slots through the top cap -----
for i in range(slot_count):
    angle = i * (360.0 / slot_count)
    slot = (
        cq.Workplane("XY")
        .workplane(offset=auger_tube_length - top_cap_h)
        .center(slot_r, 0)
        .rect(slot_len, slot_w)
        .extrude(top_cap_h + 0.2)
    )
    slot = slot.rotate((0, 0, 0), (0, 0, 1), angle)
    result = result.cut(slot)

# ----- Step 8 (LAST): Add the helical fin via swept rectangle on a helix wire.
# We do this last so OCCT's clean() step (run by earlier .union/.cut calls)
# cannot collapse the thin helical surfaces. -----
helix_R = (shaft_r + (inner_r + fin_sink)) / 2.0
fin_radial_w = (inner_r + fin_sink) - shaft_r

helix_wire = cq.Wire.makeHelix(
    pitch=auger_stair_pitch,
    height=helix_height,
    radius=helix_R,
).translate((0, 0, helix_z_start))

# Tangent at start of helix points along (0, 2πR, P) — normalize
tangent = cq.Vector(0.0, 2 * math.pi * helix_R, auger_stair_pitch).normalized()
profile_plane = cq.Plane(
    origin=(helix_R, 0.0, helix_z_start),
    xDir=(1, 0, 0),                  # radial direction
    normal=tangent.toTuple(),
)
fin_wp = (
    cq.Workplane(profile_plane)
    .rect(fin_radial_w, auger_stair_thk)
    .sweep(
        cq.Workplane(obj=helix_wire),
        isFrenet=True,
        makeSolid=True,
        combine=False,
    )
)
print(f"fin sweep: vol={fin_wp.val().Volume():.1f}, valid={fin_wp.val().isValid()}")

# Final: keep the auger as a Compound of [tube_body, fin]. OCCT's boolean
# fusion of a thin helical sweep with the chunky tube body collapses the fin
# even with clean=False (volume drops back to the no-fin value, validity
# becomes False). For visualization / assembly purposes a Compound is
# sufficient — the helix and the body share a frame and render together as a
# single colored part.
tube_body = result.val()
fin_solid = fin_wp.val()
result = cq.Workplane(obj=cq.Compound.makeCompound([tube_body, fin_solid]))

print(f"FINAL: vol={result.val().Volume():.1f}, "
      f"valid={result.val().isValid()}, n_turns={n_turns:.2f}")
