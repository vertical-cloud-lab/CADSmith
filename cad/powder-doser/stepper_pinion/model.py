import cadquery as cq
import math

# ========================================
# Stepper Pinion for NEMA 11 Motor
# 16-tooth spur gear with hub and setscrew
# Using simplified tooth profile for valid geometry
# ========================================

# Gear parameters
module = 1.0
num_teeth = 16
pressure_angle_deg = 20
gear_face_width = 10.0

# Derived gear dimensions
pitch_diameter = module * num_teeth  # 16.0 mm
tip_diameter = 18.0  # Given
root_diameter = 13.5  # Given

# Bore and hub parameters
bore_diameter = 5.2  # 5.0 mm shaft + 0.2 mm slip fit
hub_diameter = 9.0
hub_height = 6.0  # Above gear top face

# Setscrew parameters
setscrew_pilot_dia = 2.5  # M3 setscrew pilot
setscrew_height_above_gear = 3.0  # Center of hole above gear top

# Radii
tip_radius = tip_diameter / 2
root_radius = root_diameter / 2
pitch_radius = pitch_diameter / 2

# Create gear blank at tip diameter
gear_blank = (
    cq.Workplane("XY")
    .circle(tip_radius)
    .extrude(gear_face_width)
)

# Calculate tooth space geometry for cutting
# Tooth angular pitch
tooth_angle_deg = 360.0 / num_teeth  # 22.5 degrees

# Tooth thickness at pitch circle (standard = pi*m/2)
tooth_thickness_pitch = math.pi * module / 2  # ~1.57 mm

# Space width at pitch circle
space_width_pitch = math.pi * module / 2  # ~1.57 mm

# Convert to angular width at pitch radius
space_angle_deg = math.degrees(space_width_pitch / pitch_radius)  # ~11.25 degrees

# Depth of tooth space (from tip to root)
tooth_depth = tip_radius - root_radius  # 2.25 mm

# Create trapezoidal tooth space profile for cutting
# Using a slightly tapered slot to approximate involute shape
def create_tooth_space_cutter():
    """Create a single tooth space as a solid to cut from the blank"""
    # Width at bottom (root) - slightly wider due to pressure angle
    pressure_angle_rad = math.radians(pressure_angle_deg)
    
    # Calculate widths at different radii
    # At tip (outer edge of cut)
    half_angle_tip = math.radians(space_angle_deg / 2)
    # At root (inner edge of cut) - wider due to involute
    width_expansion = tooth_depth * math.tan(pressure_angle_rad)
    half_angle_root = math.radians(space_angle_deg / 2) + width_expansion / root_radius
    
    # Create the tooth space as a lofted shape from tip to root
    # Start with a simple approach: rectangular slot at slight angle
    
    # Points for the tooth space (trapezoidal cross-section)
    # Working in a plane perpendicular to the tooth space
    slot_width_outer = 2 * tip_radius * math.sin(half_angle_tip)
    slot_width_inner = 2 * root_radius * math.sin(half_angle_root)
    
    # Create cutter as extruded rectangle, positioned and rotated
    cutter = (
        cq.Workplane("XZ")
        .center(pitch_radius, gear_face_width / 2)
        .rect(tooth_depth * 1.2, gear_face_width)
        .extrude(slot_width_outer, both=True)
    )
    
    return cutter

# Alternative approach: cut rectangular slots at each tooth position
# This creates a simpler but valid gear geometry suitable for FDM printing

# Create the tooth spaces by cutting from the blank
gear_with_teeth = gear_blank

for i in range(num_teeth):
    angle = i * tooth_angle_deg
    angle_rad = math.radians(angle)
    
    # Position of the tooth space center at pitch circle
    cut_center_x = pitch_radius * math.cos(angle_rad)
    cut_center_y = pitch_radius * math.sin(angle_rad)
    
    # Create a slot cutter - rectangular approximation of tooth space
    # Slot dimensions
    slot_depth = tooth_depth + 0.5  # Cut slightly deeper than needed
    slot_width = space_width_pitch * 0.9  # Slightly narrower for tooth contact
    
    # Create slot by positioning a box and cutting
    # The slot is oriented radially
    slot = (
        cq.Workplane("XY")
        .transformed(rotate=(0, 0, angle))
        .center(pitch_radius, 0)
        .rect(slot_depth * 2, slot_width)
        .extrude(gear_face_width)
    )
    
    gear_with_teeth = gear_with_teeth.cut(slot)

# Add back a cylinder at root diameter to clean up the bottom of teeth
root_cylinder = (
    cq.Workplane("XY")
    .circle(root_radius)
    .extrude(gear_face_width)
)

# The gear is the intersection of teeth cut blank with keeping root cylinder solid
# Actually, we need to ensure we don't cut below root diameter
# Rebuild with proper approach

# Start fresh with a cleaner approach
gear_body = (
    cq.Workplane("XY")
    .circle(tip_radius)
    .circle(root_radius)  # Creates an annular ring
    .extrude(gear_face_width)
)

# Add the root cylinder (solid center to root diameter)
root_core = (
    cq.Workplane("XY")
    .circle(root_radius)
    .extrude(gear_face_width)
)

gear_body = gear_body.union(root_core)

# Now cut the tooth spaces from the outer ring only
for i in range(num_teeth):
    angle = i * tooth_angle_deg
    angle_rad = math.radians(angle)
    
    # Slot width at pitch circle
    slot_width = space_width_pitch * 0.85  # Leave material for teeth
    
    # Create radial slot cutter positioned between teeth
    # Cut from root to tip
    cut_length = tip_radius - root_radius + 0.5
    cut_center_radius = (tip_radius + root_radius) / 2
    
    slot = (
        cq.Workplane("XY")
        .transformed(rotate=(0, 0, angle + tooth_angle_deg / 2))  # Offset to cut between teeth
        .center(cut_center_radius, 0)
        .rect(cut_length + 0.5, slot_width)
        .extrude(gear_face_width)
    )
    
    gear_body = gear_body.cut(slot)

# Create the cylindrical hub on top of the gear
hub = (
    cq.Workplane("XY")
    .workplane(offset=gear_face_width)
    .circle(hub_diameter / 2)
    .extrude(hub_height)
)

# Combine gear body and hub
combined = gear_body.union(hub)

# Create the central bore through the entire part
combined = (
    combined
    .faces("<Z")
    .workplane()
    .circle(bore_diameter / 2)
    .cutThruAll()
)

# Create the radial setscrew hole through the hub
# The hole axis is at Z = gear_face_width + setscrew_height_above_gear = 10 + 3 = 13 mm
setscrew_z = gear_face_width + setscrew_height_above_gear

# Create the setscrew hole using a horizontal cylinder
# Position on the outer surface of the hub and cut inward through to bore
combined = (
    combined
    .faces("|X")  # Select faces perpendicular to X
    .workplane(centerOption="CenterOfBoundBox")
    .center(0, setscrew_z - gear_face_width - hub_height / 2)  # Adjust Y (which is Z in part coords)
    .hole(setscrew_pilot_dia, depth=hub_diameter)
)

result = combined