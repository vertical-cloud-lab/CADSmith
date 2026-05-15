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

# Derived parameters
chassis_x = 70.0
chassis_y = 60.0
chassis_extra_top = 50.0
chassis_z = auger_tube_length + chassis_extra_top

auger_bore_d = auger_tube_outer_d + 0.4

stepper_plate_x = stepper_w + 16.0
stepper_plate_y = stepper_h + 16.0
stepper_plate_thk = 4.0
stepper_pilot_d = 22.0
stepper_bolt_pattern = 23.0
stepper_bolt_hole_d = 3.0

coupler_chamber_d = 19.0
coupler_chamber_h = 26.0

erm_pocket_d = erm_disc_d + 0.3
erm_pocket_depth = erm_disc_thk + 0.2
erm_pocket_z = auger_tube_length * 0.5
erm_wire_w = 1.5
erm_wire_d = 2.0

solenoid_pocket_x = 9.8
solenoid_pocket_y = 19.2
solenoid_pocket_z_dim = 22.2
solenoid_pocket_z_center = 30.0
solenoid_slot_w = 2.5
solenoid_slot_h = 6.0
solenoid_wire = 2.0

servo_pocket_x = 41.0
servo_pocket_y = 20.0
servo_pocket_z_dim = 43.2
servo_pocket_z_center = 15.0
servo_flange_hole_d = 3.2
servo_flange_spacing = 49.5

pi_bay_x = 70.0
pi_bay_y = 35.0
pi_bay_depth = 1.5
pi_board_x = 65.0
pi_board_y = 30.0
pi_mount_hole_d = 2.9
pi_mount_pat_x = 58.0
pi_mount_pat_y = 23.0
pi_bay_z_min = 60.0
pi_bay_z_max = 130.0

stepper_wire_slot_w = 4.0
stepper_wire_slot_d = 3.0

# ===== OUTER CHASSIS =====
chassis = (
    cq.Workplane("XY")
    .box(chassis_x, chassis_y, chassis_z, centered=(True, True, False))
)

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

# ===== STEPPER SHAFT PASS-THROUGH =====
shaft_through = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_bottom)
    .circle(stepper_pilot_d / 2.0)
    .extrude(stepper_plate_thk + 0.1)
)
chassis = chassis.cut(shaft_through)

# ===== STEPPER 4x M2.5 CLEARANCE HOLES =====
half = stepper_bolt_pattern / 2.0
bolt_pts = [(half, half), (-half, half), (half, -half), (-half, -half)]
stepper_bolts = (
    cq.Workplane("XY")
    .workplane(offset=plate_z_bottom)
    .pushPoints(bolt_pts)
    .circle(stepper_bolt_hole_d / 2.0)
    .extrude(stepper_plate_thk + 0.1)
)
chassis = chassis.cut(stepper_bolts)

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

# ERM wire egress channel — offset vertically so it's a distinct slot in the wall
# Channel runs from inner end of pocket out to +X exterior, offset above the pocket center
erm_channel_z = erm_pocket_z + erm_pocket_d / 2.0 + erm_wire_d / 2.0 + 0.5
erm_channel = (
    cq.Workplane("XY")
    .workplane(offset=erm_channel_z - erm_wire_d / 2.0)
    .center(erm_outer_x - (erm_pocket_depth + 2.0) / 2.0, 0)
    .box(erm_pocket_depth + 2.0, erm_wire_w, erm_wire_d, centered=(True, True, False))
)
chassis = chassis.cut(erm_channel)

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
slot_end_x = 0.0
slot_len = slot_end_x - slot_start_x
sol_slot = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_slot_h / 2.0)
    .center(slot_start_x, 0)
    .box(slot_len, solenoid_slot_w, solenoid_slot_h, centered=(False, True, False))
)
chassis = chassis.cut(sol_slot)

# Solenoid wire channel (small redundant slot)
sol_wire = (
    cq.Workplane("XY")
    .workplane(offset=solenoid_pocket_z_center - solenoid_wire / 2.0)
    .center(sol_x_outer, 0)
    .box(2.0, solenoid_wire, solenoid_wire, centered=(False, True, False))
)
chassis = chassis.cut(sol_wire)

# ===== SERVO POCKET (+Y side, through-pocket, slide-in) =====
servo_y_outer = chassis_y / 2.0
servo_pocket = (
    cq.Workplane("XY")
    .workplane(offset=servo_pocket_z_center - servo_pocket_z_dim / 2.0)
    .center(0, servo_y_outer - servo_pocket_y / 2.0)
    .box(servo_pocket_x, servo_pocket_y, servo_pocket_z_dim, centered=(True, True, False))
)
chassis = chassis.cut(servo_pocket)

# ===== SERVO 2x M3 FLANGE HOLES =====
# Through-holes along Z at +/- flange_spacing/2 in X, at servo Y center
servo_flange_offset = servo_flange_spacing / 2.0
servo_y_center = servo_y_outer - servo_pocket_y / 2.0
servo_holes = (
    cq.Workplane("XY")
    .pushPoints([(servo_flange_offset, servo_y_center), (-servo_flange_offset, servo_y_center)])
    .circle(servo_flange_hole_d / 2.0)
    .extrude(chassis_z + stepper_plate_thk + 1)
)
chassis = chassis.cut(servo_holes)

# ===== PI ZERO 2 W ELECTRONICS BAY (-Y face) =====
pi_bay_z_center = (pi_bay_z_min + pi_bay_z_max) / 2.0
pi_bay_z_height = pi_bay_z_max - pi_bay_z_min
pi_y_outer = -chassis_y / 2.0
# Recessed pocket: 70(X) x 1.5(Y deep) x 70(Z), opening to -Y face
pi_bay = (
    cq.Workplane("XY")
    .workplane(offset=pi_bay_z_min)
    .center(0, pi_y_outer + pi_bay_depth / 2.0)
    .box(pi_bay_x, pi_bay_depth, pi_bay_z_height, centered=(True, True, False))
)
chassis = chassis.cut(pi_bay)

# Pi Zero 4x mounting holes through chassis along Y axis
pi_hx = pi_mount_pat_x / 2.0
pi_hz_center = pi_bay_z_center
pi_hz_half = pi_mount_pat_y / 2.0
pi_hole_pts = [
    ( pi_hx, pi_hz_center + pi_hz_half),
    (-pi_hx, pi_hz_center + pi_hz_half),
    ( pi_hx, pi_hz_center - pi_hz_half),
    (-pi_hx, pi_hz_center - pi_hz_half),
]
pi_holes = (
    cq.Workplane("XZ")
    .pushPoints(pi_hole_pts)
    .circle(pi_mount_hole_d / 2.0)
    .extrude(chassis_y + 2.0)
)
chassis = chassis.cut(pi_holes)

# ===== STEPPER WIRE ROUTING SLOT (+X face, vertical) =====
# 4 mm wide (Y) x 3 mm deep (into -X from +X face), from ERM pocket up to plate
wire_slot_z_bottom = erm_pocket_z
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