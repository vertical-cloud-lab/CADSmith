import cadquery as cq
import math

# ============================================
# Archimedes Auger - STORAGE variant, SHORT bench-test length
# ============================================

# Main dimensions
tube_outer_diameter = 25.0
tube_wall_thickness = 2.0
tube_bore_inner_diameter = 21.0
tube_length = 90.0

# Top cap dimensions
top_cap_height = 6.0
loading_slot_width = 4.0
loading_slot_length = 7.0
loading_slot_bolt_circle_radius = 6.5
loading_slot_count = 4
m3_pilot_hole_diameter = 2.7

# Bottom funnel dimensions
bottom_funnel_height = 12.0
bottom_exit_hole_diameter = 3.0

# Internal screw dimensions
central_shaft_diameter = 8.0
helical_fin_pitch = 10.0
helical_fin_thickness = 2.0
screw_zone_height = 30.0

# Derived dimensions
tube_outer_radius = tube_outer_diameter / 2.0
tube_inner_radius = tube_bore_inner_diameter / 2.0
shaft_radius = central_shaft_diameter / 2.0
exit_hole_radius = bottom_exit_hole_diameter / 2.0

# Z positions (building from bottom to top)
# Bottom funnel: z = 0 to bottom_funnel_height (12)
# Main tube: z = 12 to 12 + 90 = 102
# Top cap: z = 102 to 102 + 6 = 108
funnel_bottom_z = 0.0
funnel_top_z = bottom_funnel_height
tube_bottom_z = funnel_top_z
tube_top_z = tube_bottom_z + tube_length
cap_bottom_z = tube_top_z
cap_top_z = cap_bottom_z + top_cap_height

# Screw zone is in bottom third of the tube bore
screw_bottom_z = tube_bottom_z
screw_top_z = screw_bottom_z + screw_zone_height

# ============================================
# 1. Create outer tube shell (hollow cylinder)
# ============================================
outer_tube = (
    cq.Workplane("XY")
    .workplane(offset=tube_bottom_z)
    .circle(tube_outer_radius)
    .circle(tube_inner_radius)
    .extrude(tube_length)
)

# ============================================
# 2. Create bottom funnel (truncated cone with exit hole)
# ============================================
# Funnel tapers from tube_outer_radius at top to exit_hole_radius at bottom
# We create a solid cone and subtract a tapered bore

# Outer funnel cone
funnel_outer = (
    cq.Workplane("XY")
    .workplane(offset=funnel_bottom_z)
    .circle(exit_hole_radius + tube_wall_thickness)
    .workplane(offset=bottom_funnel_height)
    .circle(tube_outer_radius)
    .loft()
)

# Inner funnel bore (tapered hole)
funnel_inner = (
    cq.Workplane("XY")
    .workplane(offset=funnel_bottom_z)
    .circle(exit_hole_radius)
    .workplane(offset=bottom_funnel_height)
    .circle(tube_inner_radius)
    .loft()
)

funnel = funnel_outer.cut(funnel_inner)

# ============================================
# 3. Create top cap with loading slots and M3 pilot hole
# ============================================
# Solid disc
top_cap = (
    cq.Workplane("XY")
    .workplane(offset=cap_bottom_z)
    .circle(tube_outer_radius)
    .extrude(top_cap_height)
)

# Cut 4 rectangular loading slots at 90 degrees apart on bolt circle
# Slots are oriented radially
slot_positions_and_angles = []
for i in range(loading_slot_count):
    angle_deg = i * 90.0
    angle_rad = math.radians(angle_deg)
    cx = loading_slot_bolt_circle_radius * math.cos(angle_rad)
    cy = loading_slot_bolt_circle_radius * math.sin(angle_rad)
    slot_positions_and_angles.append((cx, cy, angle_deg))

# Create slots - each slot is a box oriented radially
for cx, cy, angle_deg in slot_positions_and_angles:
    slot = (
        cq.Workplane("XY")
        .workplane(offset=cap_bottom_z)
        .center(cx, cy)
        .rect(loading_slot_length, loading_slot_width)
        .extrude(top_cap_height)
        .rotate((0, 0, 0), (0, 0, 1), angle_deg)
    )
    # Need to recreate slot at correct position after rotation
    slot = (
        cq.Workplane("XY")
        .workplane(offset=cap_bottom_z)
        .transformed(rotate=(0, 0, angle_deg))
        .center(loading_slot_bolt_circle_radius, 0)
        .rect(loading_slot_length, loading_slot_width)
        .extrude(top_cap_height)
    )
    top_cap = top_cap.cut(slot)

# Cut central M3 pilot hole through cap
top_cap = (
    top_cap
    .faces(">Z")
    .workplane()
    .hole(m3_pilot_hole_diameter, depth=top_cap_height)
)

# ============================================
# 4. Create internal central shaft
# ============================================
# Shaft runs from funnel top to some height in the screw zone
# Actually, shaft should extend through the screw zone only
internal_shaft = (
    cq.Workplane("XY")
    .workplane(offset=screw_bottom_z)
    .circle(shaft_radius)
    .extrude(screw_zone_height)
)

# ============================================
# 5. Create helical fin (single-start Archimedean screw)
# ============================================
# The helix makes 3 turns over 30mm (pitch = 10mm/turn)
# Fin extends from shaft_radius (4.0) to tube_inner_radius (10.5)
# Fin thickness = 2.0

num_turns = screw_zone_height / helical_fin_pitch  # 3 turns
total_angle = num_turns * 360.0  # 1080 degrees

# Create helix using a swept profile along a helical path
# Define the fin cross-section (rectangular profile in radial direction)
fin_inner_radius = shaft_radius
fin_outer_radius = tube_inner_radius

# Create a 2D profile for the fin blade (rectangle in XZ plane)
# The profile will be swept along a helix
# Profile: radial extent from shaft to bore wall, thickness 2mm in Z

# Alternative approach: create helix segments using twisted extrusion
# We'll create a thin sector and twist-extrude it

# Create a single blade profile and twist extrude
# The blade is a thin radial "paddle" that gets twisted

# For proper helix, we use multiple segments
segments_per_turn = 36
total_segments = int(num_turns * segments_per_turn)
angle_per_segment = total_angle / total_segments
z_per_segment = screw_zone_height / total_segments

# Build helix as union of small twisted segments
# Create a radial blade profile
blade_profile = (
    cq.Workplane("XZ")
    .moveTo(fin_inner_radius, screw_bottom_z)
    .lineTo(fin_outer_radius, screw_bottom_z)
    .lineTo(fin_outer_radius, screw_bottom_z + helical_fin_thickness)
    .lineTo(fin_inner_radius, screw_bottom_z + helical_fin_thickness)
    .close()
)

# Sweep along helix path
# Create helix path
helix_path = cq.Wire.makeHelix(
    pitch=helical_fin_pitch,
    height=screw_zone_height,
    radius=(fin_inner_radius + fin_outer_radius) / 2.0,
    center=cq.Vector(0, 0, screw_bottom_z),
    dir=cq.Vector(0, 0, 1),
    lefthand=False
)

# Alternative: build helix blade directly using lofted sections
# Create cross-sections at various heights along the helix

helix_sections = []
num_sections = int(num_turns * 12) + 1  # 12 sections per turn

for i in range(num_sections):
    t = i / (num_sections - 1)  # 0 to 1
    z = screw_bottom_z + t * screw_zone_height
    angle = t * total_angle  # degrees
    
    # Create a thin radial blade at this height and rotation
    section = (
        cq.Workplane("XY")
        .workplane(offset=z)
        .transformed(rotate=(0, 0, angle))
        .moveTo(fin_inner_radius, -helical_fin_thickness/2)
        .lineTo(fin_outer_radius, -helical_fin_thickness/2)
        .lineTo(fin_outer_radius, helical_fin_thickness/2)
        .lineTo(fin_inner_radius, helical_fin_thickness/2)
        .close()
    )
    helix_sections.append(section.val())

# Loft between sections to create helical blade
# Use direct OCC approach for helix
from cadquery import Wire, Edge, Vector

# Simpler approach: create helix using multiple small wedge segments
helical_fin = cq.Workplane("XY")

# Create segments
z_step = screw_zone_height / total_segments
angle_step = total_angle / total_segments

for i in range(total_segments):
    z_start = screw_bottom_z + i * z_step
    z_end = z_start + z_step
    angle_start = i * angle_step
    angle_end = angle_start + angle_step
    
    # Create a small wedge segment
    # Bottom face at z_start, rotated by angle_start
    # Top face at z_end, rotated by angle_end
    
    # Use twisted extrusion of a thin radial rectangle
    angle_rad_start = math.radians(angle_start)
    angle_rad_end = math.radians(angle_end)
    
    # Create base profile
    seg = (
        cq.Workplane("XY")
        .workplane(offset=z_start)
        .transformed(rotate=(0, 0, angle_start))
        .moveTo(fin_inner_radius, -helical_fin_thickness/2)
        .lineTo(fin_outer_radius, -helical_fin_thickness/2)
        .lineTo(fin_outer_radius, helical_fin_thickness/2)
        .lineTo(fin_inner_radius, helical_fin_thickness/2)
        .close()
        .twistExtrude(z_step, angle_step)
    )
    
    if i == 0:
        helical_fin = seg
    else:
        helical_fin = helical_fin.union(seg)

# ============================================
# 6. Combine all components
# ============================================
# Union outer tube, funnel, and top cap (the shell)
shell = outer_tube.union(funnel).union(top_cap)

# Union shaft and helical fin (the internal screw)
internal_screw = internal_shaft.union(helical_fin)

# Final assembly: union shell with internal screw
result = shell.union(internal_screw)