import cadquery as cq
import math

# =============================================================================
# Archimedes Auger - STORAGE Variant (Powder Doser)
# =============================================================================

# --- Main Tube Dimensions ---
tube_outer_diameter = 25.0
tube_wall_thickness = 2.0
tube_inner_diameter = tube_outer_diameter - 2 * tube_wall_thickness  # 21.0
tube_outer_radius = tube_outer_diameter / 2  # 12.5
tube_inner_radius = tube_inner_diameter / 2  # 10.5
tube_length = 250.0

# --- Top Cap Dimensions ---
top_cap_height = 6.0
loading_slot_width = 4.0
loading_slot_length = 7.0
loading_slot_bolt_circle_radius = 6.5
loading_slot_count = 4
m3_pilot_diameter = 2.7

# --- Bottom Funnel Dimensions ---
bottom_funnel_height = 12.0
bottom_exit_hole_diameter = 3.0
bottom_exit_hole_radius = bottom_exit_hole_diameter / 2  # 1.5

# --- Internal Screw Dimensions ---
central_shaft_diameter = 8.0
central_shaft_radius = central_shaft_diameter / 2  # 4.0
helix_pitch = 10.0
helix_fin_thickness = 2.0
helix_outer_radius = tube_inner_radius  # 10.5
screw_zone_height = 250.0 / 3  # ~83.33 mm

# --- External Gear Band Dimensions ---
gear_module = 1.0
gear_teeth = 48
gear_face_width = 10.0
gear_tip_diameter = 50.0
gear_root_diameter = 45.5

# --- Calculated Positions ---
tube_bottom_z = bottom_funnel_height
tube_top_z = tube_bottom_z + tube_length

# Screw zone positions
screw_bottom_z = tube_bottom_z  # 12
screw_top_z = tube_bottom_z + screw_zone_height  # ~95.33

# Gear band position
gear_center_z = bottom_funnel_height + screw_zone_height
gear_bottom_z = gear_center_z - gear_face_width / 2
gear_top_z = gear_center_z + gear_face_width / 2

# =============================================================================
# Build the Outer Shell (Tube + Top Cap + Bottom Funnel)
# =============================================================================

# Create the main cylindrical tube (hollow)
outer_tube = (
    cq.Workplane("XY")
    .workplane(offset=tube_bottom_z)
    .circle(tube_outer_radius)
    .circle(tube_inner_radius)
    .extrude(tube_length)
)

# Create the top cap as a solid disc
top_cap = (
    cq.Workplane("XY")
    .workplane(offset=tube_top_z)
    .circle(tube_outer_radius)
    .extrude(top_cap_height)
)

# Create the bottom funnel as a solid cone with bore cut out
# Outer solid cone from tube OD at top to exit hole at bottom
bottom_funnel_outer = (
    cq.Workplane("XY")
    .circle(bottom_exit_hole_radius)
    .workplane(offset=bottom_funnel_height)
    .circle(tube_outer_radius)
    .loft()
)

# Inner tapered bore - from exit hole radius at z=0 to tube inner radius at z=funnel_height
bottom_funnel_inner = (
    cq.Workplane("XY")
    .circle(bottom_exit_hole_radius)
    .workplane(offset=bottom_funnel_height)
    .circle(tube_inner_radius)
    .loft()
)

# Create hollow funnel
bottom_funnel = bottom_funnel_outer.cut(bottom_funnel_inner)

# Combine tube, top cap, and funnel
outer_shell = outer_tube.union(top_cap).union(bottom_funnel)

# =============================================================================
# Create Loading Slots in Top Cap (radially oriented)
# =============================================================================

# Create slots as rectangular cutouts, oriented radially
for i in range(loading_slot_count):
    angle = i * (360.0 / loading_slot_count)
    angle_rad = math.radians(angle)
    x = loading_slot_bolt_circle_radius * math.cos(angle_rad)
    y = loading_slot_bolt_circle_radius * math.sin(angle_rad)
    
    # Create slot oriented radially (length along radial direction)
    slot = (
        cq.Workplane("XY")
        .workplane(offset=tube_top_z - 0.1)
        .center(x, y)
        .transformed(rotate=(0, 0, angle))
        .rect(loading_slot_length, loading_slot_width)  # length radial, width tangential
        .extrude(top_cap_height + 0.2)
    )
    outer_shell = outer_shell.cut(slot)

# =============================================================================
# Create M3 Pilot Hole in Top Cap Center
# =============================================================================

m3_pilot_hole = (
    cq.Workplane("XY")
    .workplane(offset=tube_top_z - 0.1)
    .circle(m3_pilot_diameter / 2)
    .extrude(top_cap_height + 0.2)
)

shell_with_pilot = outer_shell.cut(m3_pilot_hole)

# =============================================================================
# Create the Internal Central Shaft (in screw zone only)
# =============================================================================

central_shaft = (
    cq.Workplane("XY")
    .workplane(offset=screw_bottom_z)
    .circle(central_shaft_radius)
    .extrude(screw_zone_height)
)

# =============================================================================
# Create the Helical Screw Fin using STACKED ROTATED SECTORS
# =============================================================================
# Per feedback: Abandon twistExtrude. Use stacked disc sectors.
# Each sector is a thin wedge from radius 4.0 to 10.5
# Pitch = 10mm/turn means 36 degrees per mm of height (360/10 = 36)
# Fin thickness = 2mm, so each sector spans about 72 degrees of arc

# Parameters for helix construction
slice_height = 1.0  # 1mm per slice for smooth approximation
num_slices = int(screw_zone_height / slice_height)
degrees_per_mm = 360.0 / helix_pitch  # 36 degrees per mm

# Angular width of the fin (2mm thickness at middle radius)
# At mean radius ~7.25mm, 2mm arc length = 2/(2*pi*7.25)*360 ≈ 15.8 degrees
fin_angular_width = 20.0  # degrees, slightly wider for robustness

helical_fin = None

for i in range(num_slices):
    z_pos = screw_bottom_z + i * slice_height
    start_angle = i * degrees_per_mm * slice_height
    
    # Create a sector (pie slice) from shaft radius to outer radius
    # Using polyline to create a wedge shape
    angle_start_rad = math.radians(start_angle)
    angle_end_rad = math.radians(start_angle + fin_angular_width)
    
    # Points for the wedge: inner arc start, outer arc start, outer arc end, inner arc end
    # We'll approximate with straight edges (good enough for FDM)
    pts = [
        (central_shaft_radius * math.cos(angle_start_rad), central_shaft_radius * math.sin(angle_start_rad)),
        (helix_outer_radius * math.cos(angle_start_rad), helix_outer_radius * math.sin(angle_start_rad)),
        (helix_outer_radius * math.cos(angle_end_rad), helix_outer_radius * math.sin(angle_end_rad)),
        (central_shaft_radius * math.cos(angle_end_rad), central_shaft_radius * math.sin(angle_end_rad)),
    ]
    
    sector = (
        cq.Workplane("XY")
        .workplane(offset=z_pos)
        .polyline(pts)
        .close()
        .extrude(slice_height + 0.1)  # slight overlap to ensure union
    )
    
    if helical_fin is None:
        helical_fin = sector
    else:
        helical_fin = helical_fin.union(sector)

# Combine shaft and helical fin
internal_screw = central_shaft.union(helical_fin)

# Trim the screw to the tube bore (ensure it fits inside)
screw_trim_cylinder = (
    cq.Workplane("XY")
    .workplane(offset=screw_bottom_z - 0.1)
    .circle(helix_outer_radius)
    .extrude(screw_zone_height + 0.2)
)

internal_screw = internal_screw.intersect(screw_trim_cylinder)

# =============================================================================
# Create the External Spur Gear Band (Annular) - Simplified trapezoidal teeth
# =============================================================================

# Gear parameters
tooth_angle = 360.0 / gear_teeth  # 7.5 degrees per tooth
tip_radius = gear_tip_diameter / 2  # 25.0
root_radius = gear_root_diameter / 2  # 22.75

# Create gear profile with proper involute approximation using trapezoids
gear_profile_pts = []

for i in range(gear_teeth):
    center_angle = i * tooth_angle
    
    # Tooth geometry - using trapezoidal approximation
    # Tooth tip is narrower than base (involute characteristic)
    tooth_tip_half_angle = tooth_angle * 0.18  # narrower at tip
    tooth_root_half_angle = tooth_angle * 0.30  # wider at root
    
    # Root before tooth (bottom of valley)
    root_start_angle = center_angle - tooth_angle / 2
    gear_profile_pts.append((
        root_radius * math.cos(math.radians(root_start_angle)),
        root_radius * math.sin(math.radians(root_start_angle))
    ))
    
    # Tooth flank start (at root)
    flank_start_angle = center_angle - tooth_root_half_angle
    gear_profile_pts.append((
        root_radius * math.cos(math.radians(flank_start_angle)),
        root_radius * math.sin(math.radians(flank_start_angle))
    ))
    
    # Tooth tip start
    tip_start_angle = center_angle - tooth_tip_half_angle
    gear_profile_pts.append((
        tip_radius * math.cos(math.radians(tip_start_angle)),
        tip_radius * math.sin(math.radians(tip_start_angle))
    ))
    
    # Tooth tip end
    tip_end_angle = center_angle + tooth_tip_half_angle
    gear_profile_pts.append((
        tip_radius * math.cos(math.radians(tip_end_angle)),
        tip_radius * math.sin(math.radians(tip_end_angle))
    ))
    
    # Tooth flank end (at root)
    flank_end_angle = center_angle + tooth_root_half_angle
    gear_profile_pts.append((
        root_radius * math.cos(math.radians(flank_end_angle)),
        root_radius * math.sin(math.radians(flank_end_angle))
    ))

# Create the gear outer profile
gear_outer = (
    cq.Workplane("XY")
    .workplane(offset=gear_bottom_z)
    .polyline(gear_profile_pts)
    .close()
    .extrude(gear_face_width)
)

# Cut the center bore (tube outer diameter) to make it annular
gear_bore = (
    cq.Workplane("XY")
    .workplane(offset=gear_bottom_z - 0.1)
    .circle(tube_outer_radius)
    .extrude(gear_face_width + 0.2)
)

gear_band = gear_outer.cut(gear_bore)

# =============================================================================
# Final Assembly
# =============================================================================

# Add internal screw to shell
assembly_with_screw = shell_with_pilot.union(internal_screw)

# Add gear band
result = assembly_with_screw.union(gear_band)