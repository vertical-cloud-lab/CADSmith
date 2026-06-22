import cadquery as cq

# ============================================================
# Powder Doser Assembly - Complete Assembly View
# Rebuilt using explicit positioning to avoid transform issues
# ============================================================

# Key dimensions (all in mm)
# Mounting plate
mp_x_min, mp_x_max = -54.0, 54.0
mp_y_min, mp_y_max = -15.0, 115.0
mp_z_thickness = 6.0
mp_top_z = 0.0
mp_u_notch_width = 32.0

# Auger
auger_od = 25.0
auger_length = 250.0
auger_axis_z = 29.25
auger_axis_x = 0.0

# Gear collar (48-tooth band)
gear_collar_od = 50.0
gear_collar_width = 10.0
gear_collar_from_tip = 83.0

# Brackets
bracket_x = 60.0
bracket_y = 12.0
bracket_z = 14.0
bracket_collar_od = 33.5
front_bracket_y = 70.0
rear_bracket_y = 5.0

# NEMA 11 motor
nema_x = 28.0
nema_y = 28.0
nema_z = 32.0
nema_center_x = 32.0

# Motor pinion (16-tooth)
pinion_od = 18.0
pinion_width = 8.0

# Baseplate
bp_x_min, bp_x_max = -100.0, 100.0
bp_y_min, bp_y_max = 55.0, 115.0
bp_z_thickness = 8.0
bp_top_z = -8.0
bp_chamfer = 25.0

# Servos (MG996R)
servo_x = 40.0
servo_y = 20.0
servo_z = 43.0
servo_center_x = 77.0

# Servo pinion (20-tooth)
servo_pinion_od = 20.0
servo_pinion_width = 8.0

# Hinge pins
hinge_pin_dia = 5.0
hinge_pin_z = 29.25
hinge_pin_length = 30.0

# ============================================================
# Build components using explicit construction
# ============================================================

# 1. Mounting Plate with U-notch
mp_width = mp_x_max - mp_x_min  # 108
mp_length = mp_y_max - mp_y_min  # 130
mp_center_y = (mp_y_min + mp_y_max) / 2  # 50

# Create base plate - top at Z=0, bottom at Z=-6
mounting_plate = (
    cq.Workplane("XY")
    .center(0, mp_center_y)
    .box(mp_width, mp_length, mp_z_thickness, centered=(True, True, False))
    .translate((0, 0, -mp_z_thickness))
)

# Cut U-notch at +Y edge
u_notch_depth = 30.0
mounting_plate = (
    mounting_plate
    .faces(">Z")
    .workplane()
    .center(0, mp_y_max - u_notch_depth / 2 - mp_center_y)
    .rect(mp_u_notch_width, u_notch_depth + 1)
    .cutThruAll()
)

# 2. Auger tube (cylinder along Y axis)
# Tip at Y~135, rear at Y~-115
auger_tip_y = 135.0
auger_rear_y = auger_tip_y - auger_length  # -115
auger_center_y = (auger_tip_y + auger_rear_y) / 2  # 10

# Create auger as cylinder along Y using XZ workplane
auger_tube = (
    cq.Workplane("XZ")
    .center(auger_axis_x, auger_axis_z)
    .circle(auger_od / 2)
    .extrude(auger_length / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, auger_center_y, 0))
)

# 3. Gear collar (48-tooth band) at 83mm from +Y end
gear_collar_center_y = auger_tip_y - gear_collar_from_tip  # 52

gear_collar = (
    cq.Workplane("XZ")
    .center(auger_axis_x, auger_axis_z)
    .circle(gear_collar_od / 2)
    .extrude(gear_collar_width / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, gear_collar_center_y, 0))
)

# 4. Front auger bracket - block + collar
# Block sits on plate top (Z=0), extends to Z=14
front_bracket_base = (
    cq.Workplane("XY")
    .center(0, front_bracket_y)
    .box(bracket_x, bracket_y, bracket_z, centered=(True, True, False))
)

# Front bracket collar - cylinder along Y at auger height
front_bracket_collar = (
    cq.Workplane("XZ")
    .center(0, auger_axis_z)
    .circle(bracket_collar_od / 2)
    .extrude(bracket_y / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, front_bracket_y, 0))
)

# 5. Rear auger bracket - block + collar
rear_bracket_base = (
    cq.Workplane("XY")
    .center(0, rear_bracket_y)
    .box(bracket_x, bracket_y, bracket_z, centered=(True, True, False))
)

rear_bracket_collar = (
    cq.Workplane("XZ")
    .center(0, auger_axis_z)
    .circle(bracket_collar_od / 2)
    .extrude(bracket_y / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, rear_bracket_y, 0))
)

# 6. NEMA 11 motor block
# Positioned at X=+32 beside the gear band, bottom at Z=0
nema_center_y = gear_collar_center_y

nema_block = (
    cq.Workplane("XY")
    .center(nema_center_x, nema_center_y)
    .box(nema_x, nema_y, nema_z, centered=(True, True, False))
)

# 7. Motor pinion (16-tooth ring) - at auger axis height
motor_pinion = (
    cq.Workplane("XZ")
    .center(nema_center_x, auger_axis_z)
    .circle(pinion_od / 2)
    .extrude(pinion_width / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, gear_collar_center_y, 0))
)

# 8. Baseplate with chamfered corners
# Top at Z=-8, bottom at Z=-16
pts = [
    (bp_x_min, bp_y_min),  # -100, 55
    (bp_x_max, bp_y_min),  # 100, 55
    (bp_x_max, bp_y_max - bp_chamfer),  # 100, 90
    (bp_x_max - bp_chamfer, bp_y_max),  # 75, 115
    (bp_x_min + bp_chamfer, bp_y_max),  # -75, 115
    (bp_x_min, bp_y_max - bp_chamfer),  # -100, 90
]

baseplate = (
    cq.Workplane("XY")
    .moveTo(pts[0][0], pts[0][1])
    .polyline(pts[1:])
    .close()
    .extrude(bp_z_thickness)
    .translate((0, 0, bp_top_z - bp_z_thickness))
)

# 9. Servo envelopes (MG996R) - on baseplate, bottom at Z=-8
servo_center_y = (bp_y_min + bp_y_max) / 2  # 85

left_servo = (
    cq.Workplane("XY")
    .center(-servo_center_x, servo_center_y)
    .box(servo_x, servo_y, servo_z, centered=(True, True, False))
    .translate((0, 0, bp_top_z))
)

right_servo = (
    cq.Workplane("XY")
    .center(servo_center_x, servo_center_y)
    .box(servo_x, servo_y, servo_z, centered=(True, True, False))
    .translate((0, 0, bp_top_z))
)

# 10. Servo pinions - positioned at servo output shaft (mid-height)
servo_pinion_z = bp_top_z + servo_z / 2  # -8 + 21.5 = 13.5

left_servo_pinion = (
    cq.Workplane("XZ")
    .center(-servo_center_x + servo_x / 2 + 5, servo_pinion_z)
    .circle(servo_pinion_od / 2)
    .extrude(servo_pinion_width / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, servo_center_y, 0))
)

right_servo_pinion = (
    cq.Workplane("XZ")
    .center(servo_center_x - servo_x / 2 - 5, servo_pinion_z)
    .circle(servo_pinion_od / 2)
    .extrude(servo_pinion_width / 2)
    .mirror(mirrorPlane="XZ", basePointVector=(0, 0, 0))
    .translate((0, servo_center_y, 0))
)

# 11. Hinge pins - along X at Y=65 (10mm forward of baseplate front edge)
hinge_y = bp_y_min + 10  # 65

# Create hinge pin along X axis using YZ workplane
hinge_pin = (
    cq.Workplane("YZ")
    .center(hinge_y, hinge_pin_z)
    .circle(hinge_pin_dia / 2)
    .extrude(hinge_pin_length / 2)
    .mirror(mirrorPlane="YZ", basePointVector=(0, 0, 0))
)

# ============================================================
# Combine all components - ensure physical connection for union
# Add thin connection bridges between floating components and main body
# ============================================================

# Small bridge to connect baseplate to mounting plate
# Calculate proper height: from mp bottom (-6) to bp bottom (-16)
bridge_height = abs(bp_top_z - bp_z_thickness - (-mp_z_thickness))  # |-16 - (-6)| = 10

bridge_to_baseplate = (
    cq.Workplane("XY")
    .center(0, bp_y_min)
    .box(10, 2, bridge_height + 2, centered=(True, True, False))
    .translate((0, 0, bp_top_z - bp_z_thickness))
)

# Combine mounting plate with baseplate through bridge
main_assembly = (
    mounting_plate
    .union(bridge_to_baseplate)
    .union(baseplate)
)

# Add brackets (physically connected to mounting plate)
main_assembly = (
    main_assembly
    .union(front_bracket_base)
    .union(front_bracket_collar)
    .union(rear_bracket_base)
    .union(rear_bracket_collar)
)

# Add auger and gear collar (touches brackets)
main_assembly = (
    main_assembly
    .union(auger_tube)
    .union(gear_collar)
)

# Add NEMA motor and pinion (motor sits on plate, pinion touches gear collar)
main_assembly = (
    main_assembly
    .union(nema_block)
    .union(motor_pinion)
)

# Add servos (sitting on baseplate)
main_assembly = (
    main_assembly
    .union(left_servo)
    .union(right_servo)
)

# Add servo pinions with small bridges to servos
left_pinion_bridge = (
    cq.Workplane("XY")
    .center(-servo_center_x + servo_x / 2, servo_center_y)
    .box(10, 4, 4, centered=(True, True, False))
    .translate((0, 0, servo_pinion_z - 2))
)

right_pinion_bridge = (
    cq.Workplane("XY")
    .center(servo_center_x - servo_x / 2, servo_center_y)
    .box(10, 4, 4, centered=(True, True, False))
    .translate((0, 0, servo_pinion_z - 2))
)

main_assembly = (
    main_assembly
    .union(left_pinion_bridge)
    .union(left_servo_pinion)
    .union(right_pinion_bridge)
    .union(right_servo_pinion)
)

# Add hinge pin with small bridge to front bracket collar
hinge_bridge = (
    cq.Workplane("XY")
    .center(0, hinge_y)
    .box(4, 10, 4, centered=(True, True, False))
    .translate((0, 0, hinge_pin_z - 2))
)

main_assembly = (
    main_assembly
    .union(hinge_bridge)
    .union(hinge_pin)
)

result = main_assembly