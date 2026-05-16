"""
powder_doser_chassis.py — v3 (acts on Edison ANALYSIS-mode P0/P1 findings)

User directives for this revision (paraphrased from the PR thread):
  - Leave the auger architecture as-is (rotates as one body; user wants to
    avoid PLA-on-PLA rubbing for now). Auger script lives in
    powder_doser_auger.py and adds a Ø5 mm spindle on top so it actually
    engages the coupler now.
  - Fix the auger ↔ coupler spindle gap. (See auger script: the auger now
    extends with a Ø5 × 24 mm spindle reaching up into the ST-FC01 bore.
    The chassis side just needs the coupler chamber's lower bore to be a
    proper Ø5+clearance pass-through for the spindle, not a Ø19 cavern.)
  - Servo no longer embedded in a PLA tomb. The +Y face now has a
    bracket-flange landing (4× M3 heat-set inserts) for an external servo
    case, with a small *air-gap standoff lip* between the servo and the
    chassis (thermal mitigation) and a Ø8 horn-axle pass-through. A short
    Ø3.2 mm bushing socket on the -Y side wall catches the back of the
    horn shaft so the horn pin is supported on both sides.
  - E-bay lid heat-set holes were drilling into air. The lid opening is
    now smaller so a real 8.5 mm-wide flange remains for the corner
    inserts; the lid inset is also increased so holes are 6 mm in from
    every edge of the *flange* (not the outer wall).
  - Solenoid pocket rotated 90° about Y so the plunger axis is now along
    X (radial toward the bore), matching the through-bore tap-slot
    direction. Pocket Z extent drops from 22.2 mm to 9.8 mm.
  - Stepper wire grommet relocated to the e-bay's external +X wall
    (Ø5 hole through ebay_wall_thk = 2.5 mm only). The +X vertical wire
    slot now terminates at this grommet so wires drop straight into the
    e-bay cavity instead of dead-ending in a 3.5 mm-deep blind hole.
  - Servo + solenoid bore-breach overlap removed: solenoid moved to
    z_center = 15 (well below the dispense-end region), servo horn axis
    at z = 50, so the two breach slots no longer share any Z range.
  - Tic 500 moved off the Bonnet GPIO stack: a small VHB-mount footprint
    is reserved on the e-bay -X internal sidewall (no obstructions),
    documented in powder_doser_pauses.json. The Tic 500's micro-USB port
    handles host comms so there is no GPIO clash with the Bonnet.

v3 keeps the v2 parameter surface (auger_*, erm_*, stepper_*, heatset_*).
Output solid is assigned to `result`.
"""

import cadquery as cq

# ===== ADJUSTABLE PARAMETERS =====
auger_tube_outer_d   = 25.0
auger_tube_length    = 250.0
auger_wall_thk       = 2.0
auger_stair_thk      = 2.0
auger_stair_pitch    = 10.0
erm_disc_d           = 10.0
erm_disc_thk         = 2.7
stepper_w            = 28.0
stepper_h            = 28.0
stepper_l            = 45.0

# Heat-set insert sized holes
HEATSET_M3_D    = 4.0
HEATSET_M3_DEP  = 5.5
HEATSET_M25_D   = 3.6
HEATSET_M25_DEP = 4.5

# ===== Derived chassis size =====
chassis_x = 70.0
chassis_y = 60.0
chassis_extra_top = 50.0
chassis_z = auger_tube_length + chassis_extra_top  # 300 mm

auger_bore_d = auger_tube_outer_d + 0.4

# Stepper plate
stepper_plate_x = stepper_w + 16.0
stepper_plate_y = stepper_h + 16.0
stepper_plate_thk = 4.0
stepper_pilot_d = 22.0
stepper_bolt_pattern = 23.0

# ERM
erm_pocket_d = erm_disc_d + 0.3
erm_pocket_depth = erm_disc_thk + 0.2
erm_pocket_z = auger_tube_length * 0.5

# --- Solenoid (v3: rotated 90° about Y, plunger axis now along X) ---
# JF-0530B body: 9.6 × 19 × 22 mm. The 22 mm dimension is the plunger axis.
# v3 places that along X so the plunger fires radially toward the bore in
# the same direction as the tap-slot we cut to the bore.
solenoid_pocket_x = 22.2   # plunger axis (was z in v2)
solenoid_pocket_y = 19.2
solenoid_pocket_z_dim = 9.8  # short dimension along Z
# Moved to z=15 (well below servo region) to remove bore-breach Z overlap.
solenoid_pocket_z_center = 15.0
solenoid_slot_w = 6.0  # slot width along Y (matches plunger cross-section)
solenoid_slot_h = 2.5  # slot height along Z (clearance for plunger travel)

# --- Servo (v3: external bracket, no embedded pocket, both-sides horn support) ---
# Adafruit #1142 HD-1810MG: 40.7 × 19.7 × 42.9 mm
servo_body_x = 40.7
servo_body_y = 19.7  # depth from +Y face out into open air
servo_body_z = 42.9
# Bracket flange dims: matches servo's mounting ears (49.5 mm spacing, 2× M3)
servo_flange_spacing = 49.5
# Horn axle pass-through: Ø8 (clears horn output spline + bushing)
servo_horn_axle_d = 8.0
servo_horn_axle_z = 50.0   # moved up from v2 (z=25) — no overlap with solenoid breach now
# Back-side horn bushing socket (catches the rear pin of the horn for both-sided support)
servo_horn_pin_d = 3.2     # small bearing/bushing pin in -Y face
servo_horn_pin_depth = 4.0
# Air-gap standoff ring around the horn axle so the servo case sits ~2 mm
# off the chassis face (thermal): we model this as a *raised boss* on +Y
# at the horn-axle location, but we keep most of the +Y face flush.
servo_airgap_h = 2.0
servo_airgap_ring_d_outer = 16.0
# Cooling slots: 4× narrow vents around the bracket flange (purely visual /
# for airflow — small enough to print without supports).
servo_vent_w = 2.0
servo_vent_h = 6.0
servo_vent_offset = 26.0   # X-distance from horn axle to each vent pair

# ===== ELECTRONICS BAY (-Y side-car) =====
ebay_outer_x       = chassis_x
ebay_outer_y       = 35.0
ebay_outer_z       = 80.0
ebay_wall_thk      = 2.5
ebay_z_min         = 80.0   # moved up slightly so the bay doesn't shadow the solenoid pocket
ebay_z_max         = ebay_z_min + ebay_outer_z   # 160

ebay_cav_x = ebay_outer_x - 2 * ebay_wall_thk    # 65 mm
ebay_cav_y = ebay_outer_y - ebay_wall_thk         # 32.5 mm
ebay_cav_z = ebay_outer_z - 2 * ebay_wall_thk    # 75 mm

# Pi Zero 2 W mount
pi_x_axis = 58.0
pi_z_axis = 23.0
pi_z_center = ebay_z_min + ebay_outer_z / 2.0
pi_standoff_h = 4.0
pi_standoff_d = 6.0
pi_mount_hole_d = HEATSET_M25_D

# Lid (v3: smaller opening so a real flange remains for heat-set inserts)
# Flange width per side = (ebay_outer_x - ebay_lid_opening_w) / 2.
# v2 flange was 3.5 mm (too narrow for Ø4 inserts). v3 wants ≥8 mm flange.
ebay_lid_opening_w = ebay_cav_x - 12.0   # 53 mm wide → flange = (70-53)/2 = 8.5 mm
ebay_lid_opening_h = ebay_cav_z - 12.0   # 63 mm tall → flange top/bot = (80-63)/2 = 8.5 mm
ebay_lid_inset = 6.0   # 6 mm in from outer edge (well inside the 8.5 mm flange)
ebay_lid_hole_d = HEATSET_M3_D

# Stepper wire grommet — v3: routed directly through e-bay +X external wall
# (2.5 mm wall) rather than the 32+ mm chassis-to-cavity span the v2 grommet
# tried to span (and didn't actually reach).
grommet_d = 5.0
grommet_z = ebay_z_max - 8.0   # near top of bay

# Coupler chamber and spindle pass-through
coupler_chamber_d = 19.0
coupler_chamber_h = 26.0
# v3: the lower 8 mm of the chamber is reduced to a Ø6 spindle pass-through
# so the auger's new Ø5 spindle has a defined guide bushing into the
# coupler (rather than a 19 mm cavern + free-air gap).
spindle_pass_d = 6.0
spindle_pass_h = 8.0
grub_port_d = 3.5
grub_z_low  = chassis_z - coupler_chamber_h + 6.0
grub_z_high = chassis_z - 6.0

# Wire egress ports
erm_egress_w = 2.5
erm_egress_h = 2.0
sol_egress_w = 2.5
sol_egress_h = 3.0

# ===== OUTER CHASSIS (main spine) =====
chassis = (
    cq.Workplane("XY")
    .box(chassis_x, chassis_y, chassis_z, centered=(True, True, False))
)

# Side-car electronics bay attached to -Y face
ebay_y_outer_face = -chassis_y / 2.0 - ebay_outer_y
ebay_block = (
    cq.Workplane("XY")
    .workplane(offset=ebay_z_min)
    .center(0, ebay_y_outer_face + ebay_outer_y / 2.0)
    .box(ebay_outer_x, ebay_outer_y, ebay_outer_z, centered=(True, True, False))
)
chassis = chassis.union(ebay_block)

# Stepper plate
plate_z_bottom = chassis_z
stepper_plate = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_bottom)
    .box(stepper_plate_x, stepper_plate_y, stepper_plate_thk, centered=(True, True, False))
)
chassis = chassis.union(stepper_plate)
plate_z_top = plate_z_bottom + stepper_plate_thk

# ===== AUGER TUBE BORE =====
auger_bore = (
    cq.Workplane("XY")
    .circle(auger_bore_d / 2.0)
    .extrude(auger_tube_length)
)
chassis = chassis.cut(auger_bore)

# ===== COUPLER CHAMBER + SPINDLE PASS-THROUGH (v3) =====
# Spindle pass-through (Ø6) from top of auger up to bottom of full coupler bore
spindle_pass_z_bottom = auger_tube_length
spindle_pass_z_top = spindle_pass_z_bottom + spindle_pass_h
spindle_pass = (
    cq.Workplane("XY")
    .workplane(offset=spindle_pass_z_bottom)
    .circle(spindle_pass_d / 2.0)
    .extrude(spindle_pass_h)
)
chassis = chassis.cut(spindle_pass)

# Full Ø19 coupler chamber sits above the spindle pass-through
coupler_z_bottom = spindle_pass_z_top
coupler_z_top = chassis_z
coupler = (
    cq.Workplane("XY")
    .workplane(offset=coupler_z_bottom)
    .circle(coupler_chamber_d / 2.0)
    .extrude(coupler_z_top - coupler_z_bottom)
)
chassis = chassis.cut(coupler)

# Two radial grub-screw access ports on +X
def radial_port(z_center, d):
    return (
        cq.Workplane("YZ")
        .workplane(offset=chassis_x / 2.0)
        .center(0, z_center)
        .circle(d / 2.0)
        .extrude(-(chassis_x / 2.0 - coupler_chamber_d / 2.0 + 0.5))
    )
chassis = chassis.cut(radial_port(grub_z_low, grub_port_d))
chassis = chassis.cut(radial_port(grub_z_high, grub_port_d))

# ===== STEPPER SHAFT PASS-THROUGH =====
shaft_through = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_bottom)
    .circle(stepper_pilot_d / 2.0)
    .extrude(stepper_plate_thk + 0.1)
)
chassis = chassis.cut(shaft_through)

half = stepper_bolt_pattern / 2.0
bolt_pts = [(half, half), (-half, half), (half, -half), (-half, -half)]
stepper_inserts = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_top - HEATSET_M25_DEP)
    .pushPoints(bolt_pts)
    .circle(HEATSET_M25_D / 2.0)
    .extrude(HEATSET_M25_DEP + 0.1)
)
chassis = chassis.cut(stepper_inserts)

# ===== ERM POCKET (+X side, mid tube) =====
erm_outer_x = chassis_x / 2.0
erm_pocket = (
    cq.Workplane("YZ")
    .workplane(offset=erm_outer_x)
    .center(0, erm_pocket_z)
    .circle(erm_pocket_d / 2.0)
    .extrude(-erm_pocket_depth)
)
chassis = chassis.cut(erm_pocket)

erm_inner_x = erm_outer_x - erm_pocket_depth
erm_egress = (
    cq.Workplane("XY")
    .workplane(offset=erm_pocket_z - erm_egress_h / 2.0)
    .center(erm_inner_x, 0)
    .box(erm_pocket_depth + 0.1, erm_egress_w, erm_egress_h, centered=(False, True, False))
)
chassis = chassis.cut(erm_egress)

# ===== SOLENOID POCKET (-X side, dispense end, v3 ROTATED 90°) =====
# Plunger axis is now along X. Pocket Z extent is just 9.8 mm at z_center=15.
sol_x_outer = -chassis_x / 2.0
sol_pocket = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_pocket_z_dim / 2.0)
    .center(sol_x_outer + solenoid_pocket_x / 2.0, 0)
    .box(solenoid_pocket_x, solenoid_pocket_y, solenoid_pocket_z_dim, centered=(True, True, False))
)
chassis = chassis.cut(sol_pocket)

# Plunger slot from inner end of pocket through to bore (now along X, matching plunger axis)
slot_start_x = sol_x_outer + solenoid_pocket_x
sol_slot = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_slot_h / 2.0)
    .center(slot_start_x, 0)
    .box(-slot_start_x, solenoid_slot_w, solenoid_slot_h, centered=(False, True, False))
)
chassis = chassis.cut(sol_slot)

sol_egress = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - sol_egress_h / 2.0)
    .center(sol_x_outer, 0)
    .box(2.5, sol_egress_w, sol_egress_h, centered=(False, True, False))
)
chassis = chassis.cut(sol_egress)

# ===== SERVO BRACKET (+Y face, v3 — external mount, no embedded pocket) =====
# The v2 deep PLA-tomb pocket is gone. v3 puts the servo OUTSIDE the
# chassis on a bracket flange and supports the horn pin on BOTH sides.
servo_y_face = chassis_y / 2.0
servo_y_back = -chassis_y / 2.0

# 1) Horn-axle pass-through (Ø8) all the way from +Y face to -Y face so the
#    horn shaft is supported on both sides.
horn_axle = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_face)
    .center(0, servo_horn_axle_z)
    .circle(servo_horn_axle_d / 2.0)
    .extrude(-chassis_y)
)
chassis = chassis.cut(horn_axle)

# 2) Air-gap standoff ring around the horn axle (raised boss on +Y face,
#    2 mm tall, Ø16 outer) so the servo case sits 2 mm off the chassis for
#    cooling airflow.
airgap_ring = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_face)
    .center(0, servo_horn_axle_z)
    .circle(servo_airgap_ring_d_outer / 2.0)
    .extrude(servo_airgap_h)
)
chassis = chassis.union(airgap_ring)
# Re-cut the horn axle so the ring is also pierced
horn_axle_in_ring = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_face + servo_airgap_h + 0.1)
    .center(0, servo_horn_axle_z)
    .circle(servo_horn_axle_d / 2.0)
    .extrude(-(servo_airgap_h + 0.2))
)
chassis = chassis.cut(horn_axle_in_ring)

# 3) Servo bracket flange: 4× M3 heat-set inserts in a rectangular pattern
#    matching the servo's mounting ears (one pair at ±half_spacing X, top/bot).
flange_pts = [
    ( servo_flange_spacing / 2.0,  servo_horn_axle_z + servo_body_z / 2.0 - 3.0),
    (-servo_flange_spacing / 2.0,  servo_horn_axle_z + servo_body_z / 2.0 - 3.0),
    ( servo_flange_spacing / 2.0,  servo_horn_axle_z - servo_body_z / 2.0 + 3.0),
    (-servo_flange_spacing / 2.0,  servo_horn_axle_z - servo_body_z / 2.0 + 3.0),
]
flange_inserts = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_face + HEATSET_M3_DEP)
    .pushPoints(flange_pts)
    .circle(HEATSET_M3_D / 2.0)
    .extrude(-HEATSET_M3_DEP - 0.1)
)
chassis = chassis.cut(flange_inserts)

# 4) Back-side horn pin bushing socket on the -Y face (small blind hole at
#    horn axle that gives the rear of the horn shaft a bushing seat).
back_bushing = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_back)
    .center(0, servo_horn_axle_z)
    .circle(servo_horn_pin_d / 2.0)
    .extrude(servo_horn_pin_depth)
)
chassis = chassis.cut(back_bushing)

# 5) Ventilation slots around the bracket flange (purely thermal — small
#    vertical slits left and right of the airgap ring).
for sgn in (-1, +1):
    vent = (
        cq.Workplane("XZ")
        .workplane(offset=servo_y_face)
        .center(sgn * servo_vent_offset, servo_horn_axle_z)
        .rect(servo_vent_w, servo_vent_h)
        .extrude(-(chassis_y - 4.0))
    )
    chassis = chassis.cut(vent)

# ===== ELECTRONICS BAY CAVITY =====
ebay_cav_y_center = ebay_y_outer_face + ebay_wall_thk + ebay_cav_y / 2.0
ebay_cav_z_min = ebay_z_min + ebay_wall_thk
ebay_cavity = (
    cq.Workplane("XY")
    .workplane(offset=ebay_cav_z_min)
    .center(0, ebay_cav_y_center)
    .box(ebay_cav_x, ebay_cav_y, ebay_cav_z, centered=(True, True, False))
)
chassis = chassis.cut(ebay_cavity)

# Lid opening on -Y face (v3: smaller so we keep a real 8.5 mm flange)
ebay_lid_opening = (
    cq.Workplane("XZ")
    .workplane(offset=ebay_y_outer_face)
    .center(0, ebay_z_min + ebay_outer_z / 2.0)
    .rect(ebay_lid_opening_w, ebay_lid_opening_h)
    .extrude(ebay_wall_thk + 0.1)
)
chassis = chassis.cut(ebay_lid_opening)

# Pi standoffs + inserts on +Y inner wall of e-bay
pi_inner_wall_y = -chassis_y / 2.0
pi_pts = [
    ( pi_x_axis / 2.0,  pi_z_center + pi_z_axis / 2.0),
    (-pi_x_axis / 2.0,  pi_z_center + pi_z_axis / 2.0),
    ( pi_x_axis / 2.0,  pi_z_center - pi_z_axis / 2.0),
    (-pi_x_axis / 2.0,  pi_z_center - pi_z_axis / 2.0),
]
pi_standoffs = (
    cq.Workplane("XZ")
    .workplane(offset=pi_inner_wall_y)
    .pushPoints(pi_pts)
    .circle(pi_standoff_d / 2.0)
    .extrude(-pi_standoff_h)
)
chassis = chassis.union(pi_standoffs)
pi_holes = (
    cq.Workplane("XZ")
    .workplane(offset=pi_inner_wall_y - pi_standoff_h)
    .pushPoints(pi_pts)
    .circle(HEATSET_M25_D / 2.0)
    .extrude(HEATSET_M25_DEP + 0.1)
)
chassis = chassis.cut(pi_holes)

# Pi connector / SD egress slot in the -Z floor of the e-bay
pi_cable_slot_w = 50.0
pi_cable_slot_d = ebay_outer_y - ebay_wall_thk
pi_cable_slot = (
    cq.Workplane("XY")
    .workplane(offset=ebay_z_min - 0.1)
    .center(0, ebay_y_outer_face + ebay_wall_thk + pi_cable_slot_d / 2.0)
    .box(pi_cable_slot_w, pi_cable_slot_d, ebay_wall_thk + 0.2,
         centered=(True, True, False))
)
chassis = chassis.cut(pi_cable_slot)

# Lid heat-set insert holes — v3: 6 mm in from the *outer edge*, comfortably
# inside the 8.5 mm flange that now surrounds the lid opening.
lid_hole_pts = [
    ( ebay_outer_x / 2.0 - ebay_lid_inset,  ebay_z_min + ebay_lid_inset),
    (-ebay_outer_x / 2.0 + ebay_lid_inset,  ebay_z_min + ebay_lid_inset),
    ( ebay_outer_x / 2.0 - ebay_lid_inset,  ebay_z_max - ebay_lid_inset),
    (-ebay_outer_x / 2.0 + ebay_lid_inset,  ebay_z_max - ebay_lid_inset),
]
lid_inserts = (
    cq.Workplane("XZ")
    .workplane(offset=ebay_y_outer_face + HEATSET_M3_DEP)
    .pushPoints(lid_hole_pts)
    .circle(HEATSET_M3_D / 2.0)
    .extrude(-HEATSET_M3_DEP - 0.1)
)
chassis = chassis.cut(lid_inserts)

# Stepper wire grommet — v3: through the e-bay +X *external* wall directly
# into the cavity (only ebay_wall_thk = 2.5 mm of solid material to traverse,
# so the wires actually make it through).
grommet = (
    cq.Workplane("YZ")
    .workplane(offset=chassis_x / 2.0)
    .center(ebay_cav_y_center, grommet_z)
    .circle(grommet_d / 2.0)
    .extrude(-(ebay_wall_thk + 0.5))
)
chassis = chassis.cut(grommet)

# ===== STEPPER WIRE ROUTING SLOT (+X face, vertical) =====
# v3: extends from the stepper plate down to the grommet so wires drop
# straight in. (v2 wire slot stopped at grommet_z too but the grommet
# was non-functional.)
stepper_wire_slot_w = 4.0
stepper_wire_slot_d = 3.0
wire_slot_z_bottom = grommet_z - 5.0
wire_slot_z_top = chassis_z
wire_slot_height = wire_slot_z_top - wire_slot_z_bottom
wire_slot = (
    cq.Workplane("XY")
    .workplane(offset=wire_slot_z_bottom)
    .center(chassis_x / 2.0 - stepper_wire_slot_d / 2.0, 0)
    .box(stepper_wire_slot_d, stepper_wire_slot_w, wire_slot_height, centered=(True, True, False))
)
chassis = chassis.cut(wire_slot)

result = chassis
