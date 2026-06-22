import cadquery as cq
import math

# =============================================================================
# Archimedes Auger - Threaded Sealable Variant
# Simplified version to avoid timeout - uses fewer segments
# =============================================================================

# --- Main Tube Parameters ---
tube_od = 25.0
tube_wall = 2.0
tube_id = 21.0
tube_length = 250.0

# --- External Thread Parameters (top) ---
ext_thread_length = 25.4
ext_thread_pitch = 4.0
ext_thread_depth = 1.0
ext_thread_major_r = 12.5
ext_thread_minor_r = 11.5

# --- Bottom Funnel Parameters ---
funnel_height = 12.0
funnel_exit_dia = 3.0

# --- Internal Screw Parameters (bottom third) ---
int_screw_shaft_dia = 8.0
int_screw_pitch = 10.0
int_screw_fin_thickness = 2.0
int_screw_region_length = tube_length / 3.0

# --- Gear Parameters ---
gear_teeth = 48
gear_module = 1.0
gear_tip_dia = 50.0
gear_face_width = 10.0
gear_center_from_bottom = 83.33

# =============================================================================
# Step 1: Create Main Hollow Tube
# =============================================================================
main_tube = (
    cq.Workplane("XY")
    .circle(tube_od / 2)
    .circle(tube_id / 2)
    .extrude(tube_length)
)

# =============================================================================
# Step 2: Create Bottom Funnel
# =============================================================================
# Fill bottom with solid plug, then cut tapered funnel cavity
funnel_plug = (
    cq.Workplane("XY")
    .circle(tube_id / 2)
    .extrude(funnel_height)
)
main_tube = main_tube.union(funnel_plug)

# Cut tapered funnel cavity
funnel_inner = (
    cq.Workplane("XY")
    .circle(funnel_exit_dia / 2)
    .workplane(offset=funnel_height)
    .circle(tube_id / 2)
    .loft()
)
main_tube = main_tube.cut(funnel_inner)

# =============================================================================
# Step 3: Create Internal Screw (simplified helical fin)
# =============================================================================
screw_start_z = funnel_height
screw_end_z = int_screw_region_length
screw_length = screw_end_z - screw_start_z

# Central shaft
central_shaft = (
    cq.Workplane("XY")
    .workplane(offset=screw_start_z)
    .circle(int_screw_shaft_dia / 2)
    .extrude(screw_length)
)
main_tube = main_tube.union(central_shaft)

# Simplified helical fin - use fewer, larger segments
shaft_r = int_screw_shaft_dia / 2
inner_wall_r = tube_id / 2

num_turns = screw_length / int_screw_pitch
segments_per_turn = 8  # Reduced from 36 to avoid timeout
total_segments = int(num_turns * segments_per_turn)

fin_segments = []
for i in range(total_segments):
    t = i / segments_per_turn
    z_base = screw_start_z + t * int_screw_pitch
    
    if z_base + int_screw_fin_thickness > screw_end_z:
        break
    
    angle = t * 360
    angle_rad = math.radians(angle)
    segment_angle_rad = math.radians(360 / segments_per_turn)
    
    # Create wedge segment
    p1 = (shaft_r * math.cos(angle_rad), shaft_r * math.sin(angle_rad))
    p2 = (shaft_r * math.cos(angle_rad + segment_angle_rad), 
          shaft_r * math.sin(angle_rad + segment_angle_rad))
    p3 = (inner_wall_r * math.cos(angle_rad + segment_angle_rad/2),
          inner_wall_r * math.sin(angle_rad + segment_angle_rad/2))
    
    fin_segment = (
        cq.Workplane("XY")
        .workplane(offset=z_base)
        .moveTo(p1[0], p1[1])
        .lineTo(p3[0], p3[1])
        .lineTo(p2[0], p2[1])
        .close()
        .extrude(int_screw_fin_thickness)
    )
    fin_segments.append(fin_segment)

# Union all fin segments at once
for seg in fin_segments:
    main_tube = main_tube.union(seg)

# =============================================================================
# Step 4: Create External Thread (simplified)
# =============================================================================
thread_start_z = tube_length - ext_thread_length

# Cut tube OD down to minor radius in thread zone
thread_zone_cut = (
    cq.Workplane("XY")
    .workplane(offset=thread_start_z)
    .circle(tube_od / 2)
    .circle(ext_thread_minor_r)
    .extrude(ext_thread_length)
)
main_tube = main_tube.cut(thread_zone_cut)

# Add thread teeth - simplified with fewer segments
thread_num_turns = ext_thread_length / ext_thread_pitch
thread_segments_per_turn = 12  # Reduced from 48
thread_total_segments = int(thread_num_turns * thread_segments_per_turn)
tooth_width = ext_thread_pitch * 0.4

thread_segments = []
for i in range(thread_total_segments):
    t = i / thread_segments_per_turn
    z_center = thread_start_z + t * ext_thread_pitch
    
    if z_center + tooth_width/2 > tube_length or z_center - tooth_width/2 < thread_start_z:
        continue
    
    angle = t * 360
    angle_rad = math.radians(angle)
    segment_angle_rad = math.radians(360 / thread_segments_per_turn)
    mid_angle = angle_rad + segment_angle_rad / 2
    
    p1 = (ext_thread_minor_r * math.cos(angle_rad), 
          ext_thread_minor_r * math.sin(angle_rad))
    p2 = (ext_thread_minor_r * math.cos(angle_rad + segment_angle_rad),
          ext_thread_minor_r * math.sin(angle_rad + segment_angle_rad))
    p3 = (ext_thread_major_r * math.cos(mid_angle),
          ext_thread_major_r * math.sin(mid_angle))
    
    tooth_segment = (
        cq.Workplane("XY")
        .workplane(offset=z_center - tooth_width/2)
        .moveTo(p1[0], p1[1])
        .lineTo(p2[0], p2[1])
        .lineTo(p3[0], p3[1])
        .close()
        .extrude(tooth_width)
    )
    thread_segments.append(tooth_segment)

for seg in thread_segments:
    main_tube = main_tube.union(seg)

# =============================================================================
# Step 5: Create 48T Annular Gear
# =============================================================================
gear_z_bottom = gear_center_from_bottom - gear_face_width / 2

pitch_diameter = gear_teeth * gear_module
dedendum = 1.25 * gear_module
gear_root_dia = pitch_diameter - 2 * dedendum
gear_outer_dia = gear_tip_dia

# Create gear blank
gear_blank = (
    cq.Workplane("XY")
    .workplane(offset=gear_z_bottom)
    .circle(gear_outer_dia / 2)
    .circle(tube_od / 2)
    .extrude(gear_face_width)
)
main_tube = main_tube.union(gear_blank)

# Cut gear teeth gaps
tooth_angle = 360 / gear_teeth
outer_r = gear_outer_dia / 2
root_r = gear_root_dia / 2

gear_cuts = []
for i in range(gear_teeth):
    angle = i * tooth_angle
    gap_half_angle = math.radians(tooth_angle * 0.25)
    angle_rad = math.radians(angle)
    
    gap_start = angle_rad - gap_half_angle
    gap_end = angle_rad + gap_half_angle
    
    p1 = (root_r * math.cos(gap_start), root_r * math.sin(gap_start))
    p2 = (outer_r * math.cos(gap_start), outer_r * math.sin(gap_start))
    p3 = (outer_r * math.cos(gap_end), outer_r * math.sin(gap_end))
    p4 = (root_r * math.cos(gap_end), root_r * math.sin(gap_end))
    
    gap_cut = (
        cq.Workplane("XY")
        .workplane(offset=gear_z_bottom - 0.1)
        .moveTo(p1[0], p1[1])
        .lineTo(p2[0], p2[1])
        .lineTo(p3[0], p3[1])
        .lineTo(p4[0], p4[1])
        .close()
        .extrude(gear_face_width + 0.2)
    )
    gear_cuts.append(gap_cut)

for cut in gear_cuts:
    main_tube = main_tube.cut(cut)

# =============================================================================
# Final Result
# =============================================================================
result = main_tube