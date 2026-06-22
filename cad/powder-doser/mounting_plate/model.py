import cadquery as cq

# Mounting Plate (Table) for Powder Doser
# Flat tilting platform that carries the auger assembly

# ===== PARAMETRIC DIMENSIONS =====
# Plate envelope
plate_x_min = -54.1
plate_x_max = 54.1
plate_y_min = -15.0
plate_y_max = 115.0
plate_thickness = 6.0

# Derived plate dimensions
plate_width = plate_x_max - plate_x_min  # ~108.2
plate_depth = plate_y_max - plate_y_min  # ~130.0

# U-notch parameters (open to +Y edge)
u_notch_width = 32.0
u_notch_x_min = -16.0
u_notch_x_max = 16.0
u_notch_y_start = 80.0  # Where notch begins (inside)
u_notch_y_end = plate_y_max  # Open to +Y edge (115.0)
u_notch_depth = u_notch_y_end - u_notch_y_start  # 35.0

# M3 clearance holes
m3_clearance_dia = 3.4
hole_x_positions = [24.0, -24.0]
hole_y_front = 60.0
hole_y_rear = 10.0

# ===== CREATE MAIN PLATE =====
# Build the plate centered at the geometric center, then translate to match specified envelope
plate_center_x = (plate_x_min + plate_x_max) / 2  # 0.0
plate_center_y = (plate_y_min + plate_y_max) / 2  # 50.0

# Create base plate
main_plate = (
    cq.Workplane("XY")
    .center(plate_center_x, plate_center_y)
    .rect(plate_width, plate_depth)
    .extrude(plate_thickness)
)

# ===== CUT U-NOTCH =====
# Open U-notch at +Y edge: remove material from X=-16 to X=+16, Y=80 to Y=115
# The notch is open to the +Y edge (not a closed pocket)
notch_center_x = (u_notch_x_min + u_notch_x_max) / 2  # 0.0
notch_center_y = (u_notch_y_start + u_notch_y_end) / 2  # 97.5

notch_cutter = (
    cq.Workplane("XY")
    .center(notch_center_x, notch_center_y)
    .rect(u_notch_width, u_notch_depth)
    .extrude(plate_thickness)
)

# Subtract the notch from the plate
plate_with_notch = main_plate.cut(notch_cutter)

# ===== ADD M3 CLEARANCE HOLES =====
# Four holes at positions: (+24, 60), (-24, 60), (+24, 10), (-24, 10)
# These are through-holes for bracket mounting

hole_positions = [
    (hole_x_positions[0], hole_y_front),   # (+24, 60)
    (hole_x_positions[1], hole_y_front),   # (-24, 60)
    (hole_x_positions[0], hole_y_rear),    # (+24, 10)
    (hole_x_positions[1], hole_y_rear),    # (-24, 10)
]

# Use pushPoints to place all holes at once (avoids face selection issues)
result = (
    plate_with_notch
    .faces(">Z")
    .workplane()
    .pushPoints(hole_positions)
    .hole(m3_clearance_dia, plate_thickness)
)