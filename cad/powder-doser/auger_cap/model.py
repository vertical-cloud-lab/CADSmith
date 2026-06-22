import cadquery as cq
import math

# Parameters
outer_diameter = 31.7
overall_height = 31.0
wall_thickness = 3.0
top_thickness = 3.0

# Thread parameters
thread_pitch = 4.0
thread_depth = 1.0
thread_minor_radius = 11.85  # internal crest radius (minor)
thread_major_radius = 12.85  # internal root radius (major)
clearance_above_threads = 3.0

# Chamfer
chamfer_size = 1.5

# Derived dimensions
outer_radius = outer_diameter / 2.0
inner_radius = thread_major_radius  # Inner wall at thread root

# Calculate cavity depth (from bottom, open end)
cavity_depth = overall_height - top_thickness  # 28.0

# Thread engagement length
thread_engagement_length = cavity_depth - clearance_above_threads  # 25.0

# Step 1: Create outer cylinder for the cup body
outer_cylinder = (
    cq.Workplane("XY")
    .circle(outer_radius)
    .extrude(overall_height)
)

# Step 2: Add chamfer on top outer edge BEFORE cutting the cavity
# This ensures we have a simple geometry for the chamfer
cup_with_chamfer = (
    outer_cylinder
    .faces(">Z")
    .edges()
    .chamfer(chamfer_size)
)

# Step 3: Cut the internal cavity from the bottom (open end)
# The cavity goes up to just below the top thickness
cup_hollow = (
    cup_with_chamfer
    .faces("<Z")
    .workplane()
    .circle(inner_radius)
    .cutBlind(cavity_depth)
)

# Step 4: Create internal thread grooves using revolved annular rings
# Each thread groove is a triangular profile revolved 360 degrees
# then positioned at helical Z positions

# Thread profile dimensions
# Triangular groove with depth = thread_depth, pointing inward (toward axis)
# The groove cuts from the inner wall (major radius) toward the minor radius

# Create thread grooves as individual annular cuts at each pitch position
# For a right-hand thread viewed from above, the groove spirals upward counterclockwise
# We approximate with horizontal annular grooves (acceptable for FDM printing)

# Number of full thread turns
num_turns = int(thread_engagement_length / thread_pitch)

# Create a single annular groove cutter
# Profile: triangular notch in the XZ plane, revolved around Z
# The groove is at the inner wall, cutting inward

groove_half_height = thread_pitch * 0.35  # Half the Z-extent of the triangular groove

# Create thread grooves
cup_with_thread = cup_hollow

for i in range(num_turns + 1):
    z_pos = i * thread_pitch + groove_half_height  # Center Z of this groove
    
    if z_pos > thread_engagement_length:
        break
    
    # Create a triangular annular groove using a revolved profile
    # Profile points in RZ space (R = distance from Z axis, Z = height)
    # We create this in XZ plane and revolve around Z
    
    # The groove cuts from major_radius (wall) toward minor_radius (deeper)
    # Triangle: apex at minor_radius, base at major_radius
    
    groove_profile = (
        cq.Workplane("XZ")
        .moveTo(thread_major_radius + 0.1, z_pos - groove_half_height)  # Start outside wall
        .lineTo(thread_minor_radius, z_pos)  # Apex of groove (deepest point)
        .lineTo(thread_major_radius + 0.1, z_pos + groove_half_height)  # Back to wall
        .close()
    )
    
    # Revolve the profile 360 degrees around Z axis
    groove_solid = groove_profile.revolve(360, (0, 0, 0), (0, 0, 1))
    
    # Cut the groove from the cup
    cup_with_thread = cup_with_thread.cut(groove_solid)

# Add helical connection between grooves to make it a true thread
# Create a helical ramp connecting the annular grooves
# This is done by creating small wedge cuts that spiral between grooves

segments_per_turn = 36
total_segments = int(num_turns * segments_per_turn) + segments_per_turn

for i in range(total_segments):
    angle = (i / segments_per_turn) * 360  # degrees
    z_base = (i / segments_per_turn) * thread_pitch
    
    if z_base > thread_engagement_length:
        break
    
    # Create a small wedge at this angular position
    angle_rad = math.radians(angle)
    angle_next_rad = math.radians(angle + 360 / segments_per_turn)
    
    # Calculate positions
    x1 = thread_minor_radius * math.cos(angle_rad)
    y1 = thread_minor_radius * math.sin(angle_rad)
    x2 = thread_minor_radius * math.cos(angle_next_rad)
    y2 = thread_minor_radius * math.sin(angle_next_rad)
    
    z1 = z_base
    z2 = z_base + thread_pitch / segments_per_turn
    
    # Create a small box cutter at the thread root to create helical connection
    # Using a small cylinder segment
    wedge_radius = thread_depth * 0.5
    
    # Position a small sphere at the thread root to smooth the helix
    mid_angle = angle_rad + math.radians(180 / segments_per_turn)
    mid_x = (thread_minor_radius + thread_depth * 0.3) * math.cos(mid_angle)
    mid_y = (thread_minor_radius + thread_depth * 0.3) * math.sin(mid_angle)
    mid_z = (z1 + z2) / 2
    
    if mid_z <= thread_engagement_length and mid_z > 0:
        try:
            small_cutter = (
                cq.Workplane("XY")
                .transformed(offset=(mid_x, mid_y, mid_z))
                .sphere(wedge_radius * 0.6)
            )
            cup_with_thread = cup_with_thread.cut(small_cutter)
        except Exception:
            pass

result = cup_with_thread