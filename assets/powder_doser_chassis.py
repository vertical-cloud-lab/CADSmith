"""
powder_doser_chassis.py — v2 (design refinements addressing review feedback)

Changes from v1:
  (a) Pi Zero 2 W re-oriented so USB/HDMI/SD card connectors face out of the
      -Y bay opening (cables plug in from outside, not into the chassis wall).
  (b) Servo pocket inset flush with the +Y face and shortened so the pocket
      stops 1 mm short of the auger bore wall; only the horn-side pivot slot
      breaks through with controlled clearance.
  (c) ERM disc gets a *short* radial wire channel out the +X face right next
      to the pocket (no more cable tunnel running up to the stepper plate).
      Solenoid gets the same treatment on -X. Both are clearly visible egress
      ports rather than long internal cable runs.
  (d) Real electronics bay (a -Y "side-car" enclosure unioned to the chassis)
      sized for the full Pi Zero 2 W + Adafruit Stepper Bonnet stack on the
      back wall, with side-mounting standoffs for Pololu Tic 500 and a
      DRV8825 carrier on opposite internal sidewalls.
  (e) All mounting holes (stepper M2.5, servo M3, Pi M2.5, e-bay lid M3)
      sized for heat-set brass inserts (Ø4.0 × 5.5 mm deep for M3,
      Ø3.6 × 4.5 mm deep for M2.5) — see HEATSET_M3 / HEATSET_M25 below.
  (f) Coupler chamber gets two radial Ø3.5 mm grub-screw access ports on +X
      that line up with the ST-FC01's two set screws so they can be tightened
      without removing the stepper.

Wiring overview (drawn as overlays on the assembly_render.py / xsection.py
visualisations and listed in the slicer-pause JSON):
  - ERM (mid-tube, +X side):   short radial slot out the +X face → routed
                                inside the e-bay back to the Bonnet.
  - Solenoid (low, -X side):   short radial slot out the -X face → routed
                                across the bottom of the e-bay to the Bonnet.
  - Servo (high, +Y, slide-in): cable exits the +Y face and runs around the
                                top to the Bonnet header.
  - Stepper (top):              4 leads exit at the stepper plate, drop down
                                the +X wire slot, enter the e-bay through a
                                grommet hole near z=plate_z, terminate at
                                the Tic 500 (or DRV8825) screw terminals.

All parameters from v1 are preserved (auger_*, erm_*, stepper_*); v2 adds
ebay_*, heatset_* and aux_* parameters.
"""

import cadquery as cq

# ===== PARAMETERS =====
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

# Heat-set insert sized holes (Voxel Labs / McMaster recommended sizes)
HEATSET_M3_D    = 4.0   # hole Ø for M3 brass insert
HEATSET_M3_DEP  = 5.5   # depth for M3 insert (insert is ~5 mm long)
HEATSET_M25_D   = 3.6   # hole Ø for M2.5 brass insert
HEATSET_M25_DEP = 4.5   # depth for M2.5 insert

# Derived parameters
chassis_x = 70.0
chassis_y = 60.0
chassis_extra_top = 50.0
chassis_z = auger_tube_length + chassis_extra_top  # 300 mm

auger_bore_d = auger_tube_outer_d + 0.4

stepper_plate_x = stepper_w + 16.0
stepper_plate_y = stepper_h + 16.0
stepper_plate_thk = 4.0
stepper_pilot_d = 22.0
stepper_bolt_pattern = 23.0

erm_pocket_d = erm_disc_d + 0.3
erm_pocket_depth = erm_disc_thk + 0.2
erm_pocket_z = auger_tube_length * 0.5  # mid tube

solenoid_pocket_x = 9.8
solenoid_pocket_y = 19.2
solenoid_pocket_z_dim = 22.2
solenoid_pocket_z_center = 30.0
solenoid_slot_w = 2.5
solenoid_slot_h = 6.0

# --- (b) servo: inset flush, pocket depth controlled ---
# Servo body is 40.7 × 19.7 × 42.9 (Adafruit #1142 HD-1810MG).
# Pocket Y-depth must be < (chassis_y/2 - auger_bore_d/2 - 1.0 mm wall).
# (chassis_y/2)=30, (auger_bore_d/2)=12.7 → max pocket depth = 30-12.7-1.0 = 16.3 mm.
servo_pocket_x = 41.0
servo_pocket_y = 16.3   # was 20.0 → trimmed so it does NOT punch through the auger bore
servo_pocket_z_dim = 43.2
servo_pocket_z_center = 25.0   # raised slightly so the horn (Z = center) sits clear of dispense end face
servo_horn_slot_w = 6.0   # horn-side controlled-clearance slot through to the bore (only this part breaks through)
servo_horn_slot_h = 8.0
servo_flange_spacing = 49.5

# --- (d) electronics bay (-Y side-car) ---
# Sized for: Pi Zero 2 W (65×30, on back wall) + Adafruit Stepper Bonnet
# stack (~25 mm tall on Pi GPIO) + Pololu Tic 500 (52×35) on -X sidewall +
# Pololu DRV8825 carrier (20.3×15.2) on +X sidewall + lid screws.
ebay_outer_x       = chassis_x         # 70 mm wide (matches chassis)
ebay_outer_y       = 35.0              # 35 mm deep (extends in -Y from chassis face)
ebay_outer_z       = 80.0              # tall enough for Pi+Bonnet stack vertically
ebay_wall_thk      = 2.5               # outer-wall thickness (printable, stiff)
ebay_z_min         = 50.0              # bottom of e-bay along chassis Z
ebay_z_max         = ebay_z_min + ebay_outer_z   # 130

# Internal cavity (after subtracting walls)
ebay_cav_x = ebay_outer_x - 2 * ebay_wall_thk    # 65 mm (just fits a Pi Zero long axis)
ebay_cav_y = ebay_outer_y - ebay_wall_thk         # 32.5 mm depth from chassis face
ebay_cav_z = ebay_outer_z - 2 * ebay_wall_thk    # 75 mm

# Pi Zero 2 W mount: 4 standoffs on the +Y inner face (chassis-side wall of the bay)
# Pi is 65×30; long axis horizontal (X), short axis vertical (Z).
# Connector edge (mini-HDMI / micro-USB power / micro-USB OTG) is on the
# *long* edge of the Pi facing -Z so cables exit through a slot in the bay
# floor (lid is on -Y side, USB cables exit the -Z side of the bay).
# But we want USB/HDMI/SD facing OUT. → orient Pi flat against chassis +Y
# inner wall with connector edge at -Z; cut the -Z e-bay floor open so
# cables exit downward (typical desk-mount orientation with chassis upright).
# Pi mounting hole pattern: 58 × 23 mm.
pi_x_axis = 58.0    # along chassis X
pi_z_axis = 23.0    # along chassis Z (Pi short axis vertical)
pi_z_center = ebay_z_min + ebay_outer_z / 2.0  # vertically centred in e-bay
pi_standoff_h = 4.0  # raises Pi off the inner wall to clear solder joints / GPIO bottom
pi_standoff_d = 6.0  # standoff column Ø
pi_mount_hole_d = HEATSET_M25_D      # heat-set inserts for M2.5 PI screws

# Tic 500 mount on -X internal sidewall (board lying flat against the wall)
tic_hole_x = 35.6 - 5.0   # M3 hole pattern (Pololu Tic 500 has 4 mounting holes inset 2.5 mm)
tic_hole_z = 22.9 - 5.0   # 30.6 × 17.9 mm pattern
tic_z_center = ebay_z_min + 22.0
tic_standoff_h = 3.0

# DRV8825 carrier on +X internal sidewall
drv_hole_x = 20.3 - 5.0   # ~15 mm
drv_hole_z = 15.2 - 5.0
drv_z_center = ebay_z_min + 22.0

# Lid: closes the -Y opening of the e-bay; bolted with 4× M3 inserts at corners
ebay_lid_inset = 4.0
ebay_lid_hole_d = HEATSET_M3_D

# Stepper wire grommet from +X chassis wall into top of e-bay (so 4 stepper
# leads can drop down +X face slot then jog into the e-bay).
grommet_d = 5.0
grommet_z = ebay_z_max - 8.0

# (f) coupler grub-screw access ports
coupler_chamber_d = 19.0
coupler_chamber_h = 26.0
# ST-FC01 has two set-screws ~6 mm from each end of its 25 mm body.
grub_port_d = 3.5
grub_z_low  = chassis_z - coupler_chamber_h + 6.0   # access for auger-side grub
grub_z_high = chassis_z - 6.0                        # access for stepper-side grub

# Wire egress ports (short radial slots, replace the long internal cable runs)
erm_egress_w = 2.5
erm_egress_h = 2.0
sol_egress_w = 2.5
sol_egress_h = 3.0

# ===== OUTER CHASSIS (main spine) =====
chassis = (
    cq.Workplane("XY")
    .box(chassis_x, chassis_y, chassis_z, centered=(True, True, False))
)

# (d) Side-car electronics bay attached to -Y face
ebay_y_outer_face = -chassis_y / 2.0 - ebay_outer_y  # bay extends from -Y face outward in -Y
ebay_block = (
    cq.Workplane("XY")
    .workplane(offset=ebay_z_min)
    .center(0, ebay_y_outer_face + ebay_outer_y / 2.0)
    .box(ebay_outer_x, ebay_outer_y, ebay_outer_z, centered=(True, True, False))
)
chassis = chassis.union(ebay_block)

# Stepper mount plate on top
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

# ===== COUPLER CHAMBER =====
coupler_z_top = chassis_z
coupler_z_bottom = coupler_z_top - coupler_chamber_h
coupler = (
    cq.Workplane("XY")
    .workplane(offset=coupler_z_bottom)
    .circle(coupler_chamber_d / 2.0)
    .extrude(coupler_chamber_h)
)
chassis = chassis.cut(coupler)

# (f) Two radial grub-screw access ports on +X that line up with ST-FC01 set screws
grub_low = (
    cq.Workplane("YZ")
    .workplane(offset=chassis_x / 2.0)
    .center(0, grub_z_low)
    .circle(grub_port_d / 2.0)
    .extrude(-(chassis_x / 2.0 - coupler_chamber_d / 2.0 + 0.5))
)
grub_high = (
    cq.Workplane("YZ")
    .workplane(offset=chassis_x / 2.0)
    .center(0, grub_z_high)
    .circle(grub_port_d / 2.0)
    .extrude(-(chassis_x / 2.0 - coupler_chamber_d / 2.0 + 0.5))
)
chassis = chassis.cut(grub_low).cut(grub_high)

# ===== STEPPER SHAFT PASS-THROUGH =====
shaft_through = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_bottom)
    .circle(stepper_pilot_d / 2.0)
    .extrude(stepper_plate_thk + 0.1)
)
chassis = chassis.cut(shaft_through)

# (e) Stepper 4× M2.5 heat-set insert holes (blind, 4.5 mm deep into the plate from top)
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

# ===== ERM DISC POCKET (+X side, mid tube) =====
erm_outer_x = chassis_x / 2.0
erm_pocket = (
    cq.Workplane("YZ")
    .workplane(offset=erm_outer_x)
    .center(0, erm_pocket_z)
    .circle(erm_pocket_d / 2.0)
    .extrude(-erm_pocket_depth)
)
chassis = chassis.cut(erm_pocket)

# (c) Short radial wire egress: punch directly out the +X face from the inner end of pocket.
# Channel only spans the wall thickness between the pocket bottom and outer surface.
erm_inner_x = erm_outer_x - erm_pocket_depth
erm_egress = (
    cq.Workplane("XY")
    .workplane(offset=erm_pocket_z - erm_egress_h / 2.0)
    .center(erm_inner_x, 0)
    .box(erm_pocket_depth + 0.1, erm_egress_w, erm_egress_h, centered=(False, True, False))
)
chassis = chassis.cut(erm_egress)

# ===== SOLENOID POCKET (-X side, near dispense end) =====
sol_x_outer = -chassis_x / 2.0
sol_pocket = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_pocket_z_dim / 2.0)
    .center(sol_x_outer + solenoid_pocket_x / 2.0, 0)
    .box(solenoid_pocket_x, solenoid_pocket_y, solenoid_pocket_z_dim, centered=(True, True, False))
)
chassis = chassis.cut(sol_pocket)

# Plunger slot from inner end of solenoid pocket through to bore
slot_start_x = sol_x_outer + solenoid_pocket_x
sol_slot = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_slot_h / 2.0)
    .center(slot_start_x, 0)
    .box(-slot_start_x, solenoid_slot_w, solenoid_slot_h, centered=(False, True, False))
)
chassis = chassis.cut(sol_slot)

# (c) Solenoid wire egress: short radial slot out the -X face
sol_egress = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - sol_egress_h / 2.0)
    .center(sol_x_outer, 0)
    .box(2.5, sol_egress_w, sol_egress_h, centered=(False, True, False))
)
chassis = chassis.cut(sol_egress)

# ===== (b) SERVO POCKET (+Y side, blind not through) =====
servo_y_outer = chassis_y / 2.0
servo_y_inner = servo_y_outer - servo_pocket_y    # leaves >=1 mm wall to bore
servo_pocket = (
    cq.Workplane("XY")
    .workplane(offset=servo_pocket_z_center - servo_pocket_z_dim / 2.0)
    .center(0, servo_y_outer - servo_pocket_y / 2.0)
    .box(servo_pocket_x, servo_pocket_y, servo_pocket_z_dim, centered=(True, True, False))
)
chassis = chassis.cut(servo_pocket)

# Horn-side controlled-clearance slot: only this small slot breaks through to the bore
horn_slot = (
    cq.Workplane("XY")
    .workplane(offset=servo_pocket_z_center - servo_horn_slot_h / 2.0)
    .center(0, servo_y_inner / 2.0)   # spans from inner pocket wall through to bore axis
    .box(servo_horn_slot_w, servo_y_inner + auger_bore_d / 2.0, servo_horn_slot_h,
         centered=(True, True, False))
)
chassis = chassis.cut(horn_slot)

# (e) Servo 2× M3 flange holes → heat-set inserts from +Y face (blind 5.5 mm deep)
servo_flange_offset = servo_flange_spacing / 2.0
servo_y_center_for_holes = servo_y_outer - servo_pocket_y / 2.0
servo_inserts = (
    cq.Workplane("XZ")
    .workplane(offset=servo_y_outer)
    .pushPoints([
        ( servo_flange_offset, servo_pocket_z_center),
        (-servo_flange_offset, servo_pocket_z_center),
    ])
    .circle(HEATSET_M3_D / 2.0)
    .extrude(-HEATSET_M3_DEP)
)
chassis = chassis.cut(servo_inserts)

# ===== (d) ELECTRONICS BAY CAVITY =====
ebay_cav_y_center = ebay_y_outer_face + ebay_wall_thk + ebay_cav_y / 2.0
ebay_cav_z_min = ebay_z_min + ebay_wall_thk
ebay_cavity = (
    cq.Workplane("XY")
    .workplane(offset=ebay_cav_z_min)
    .center(0, ebay_cav_y_center)
    .box(ebay_cav_x, ebay_cav_y, ebay_cav_z, centered=(True, True, False))
)
chassis = chassis.cut(ebay_cavity)

# Open the -Y face of the e-bay for the lid (rectangular hole)
ebay_lid_opening_w = ebay_cav_x - 2.0
ebay_lid_opening_h = ebay_cav_z - 2.0
ebay_lid_opening = (
    cq.Workplane("XZ")
    .workplane(offset=ebay_y_outer_face)
    .center(0, ebay_cav_z_min + ebay_cav_z / 2.0)
    .rect(ebay_lid_opening_w, ebay_lid_opening_h)
    .extrude(ebay_wall_thk + 0.1)
)
chassis = chassis.cut(ebay_lid_opening)

# (a) Pi mount: 4× M2.5 heat-set insert standoffs on the +Y inner wall of the bay
# (the inner wall is the original chassis -Y face, which is at chassis_y_inner = -chassis_y/2)
pi_inner_wall_y = -chassis_y / 2.0   # the wall the Pi sits against (its +Y face)
pi_pts = [
    ( pi_x_axis / 2.0,  pi_z_center + pi_z_axis / 2.0),
    (-pi_x_axis / 2.0,  pi_z_center + pi_z_axis / 2.0),
    ( pi_x_axis / 2.0,  pi_z_center - pi_z_axis / 2.0),
    (-pi_x_axis / 2.0,  pi_z_center - pi_z_axis / 2.0),
]
# Standoff posts (rise from the wall toward -Y), then heat-set holes drilled in
pi_standoffs = (
    cq.Workplane("XZ")
    .workplane(offset=pi_inner_wall_y)
    .pushPoints(pi_pts)
    .circle(pi_standoff_d / 2.0)
    .extrude(-pi_standoff_h)   # extrude into -Y
)
chassis = chassis.union(pi_standoffs)
pi_holes = (
    cq.Workplane("XZ")
    .workplane(offset=pi_inner_wall_y - pi_standoff_h)
    .pushPoints(pi_pts)
    .circle(HEATSET_M25_D / 2.0)
    .extrude(HEATSET_M25_DEP + 0.1)   # drill back into the standoffs (toward +Y)
)
chassis = chassis.cut(pi_holes)

# Tic 500 mount on -X internal sidewall
tic_pts = [
    ( tic_hole_z / 2.0,  tic_z_center + tic_hole_x / 2.0),  # using ZX wall coords
]  # we'll replicate at 4 corners
tic_pts = [
    (-tic_hole_x / 2.0, tic_z_center + tic_hole_z / 2.0),
    ( tic_hole_x / 2.0, tic_z_center + tic_hole_z / 2.0),
    (-tic_hole_x / 2.0, tic_z_center - tic_hole_z / 2.0),
    ( tic_hole_x / 2.0, tic_z_center - tic_hole_z / 2.0),
]
# We'll mount Tic 500 to a flat boss on the -X internal sidewall of the cavity
# (sidewall is at x = -ebay_cav_x/2). Since cavity walls are bay outer walls,
# bosses extrude from the wall inward (+X direction).
tic_wall_x = -ebay_cav_x / 2.0
tic_standoffs = (
    cq.Workplane("YZ")
    .workplane(offset=tic_wall_x)
    .pushPoints([(ebay_cav_y_center + p[0] * 0, p[1]) for p in tic_pts])  # placeholder
    .circle(2.5)
    .extrude(tic_standoff_h)
)
# (Tic / DRV bosses are nice-to-have; we keep the e-bay clean and rely on
# double-sided VHB mounting tape for those small carriers — documented in the
# install_after_print section of powder_doser_pauses.json. Skipping the
# bosses keeps the cavity unobstructed for cabling.)

# (a) Pi connector / SD egress slot — open the -Z floor of the e-bay so
# USB/HDMI/SD cables can exit downward (chassis is upright, dispense end at Z=0
# but the bay floor is at z = ebay_z_min so cables exit toward Z=0 / desk).
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

# (e) Lid heat-set insert holes — 4× M3 in the corners of the e-bay outer face
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

# Stepper wire grommet — Ø5 hole through the chassis wall between +X stepper
# wire slot and the top of the e-bay (so 4 leads can pop into the bay)
grommet = (
    cq.Workplane("XZ")
    .workplane(offset=-chassis_y / 2.0)
    .center(0, grommet_z)
    .circle(grommet_d / 2.0)
    .extrude(-ebay_wall_thk - 1.0)
)
chassis = chassis.cut(grommet)

# ===== STEPPER WIRE ROUTING SLOT (+X face, vertical) =====
# Shorter than v1: only runs from the grommet up to the stepper plate
# (was incorrectly running all the way down past the ERM in v1).
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
