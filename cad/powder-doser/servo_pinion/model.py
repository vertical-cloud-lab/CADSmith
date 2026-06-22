import cadquery as cq
import math

# =============================================================================
# SERVO PINION - 20T Spur Gear for MG996R Servo
# =============================================================================

# Gear parameters
module = 0.9083
num_teeth = 20
pressure_angle_deg = 20
face_width = 8.0

# Calculated gear dimensions
pitch_diameter = module * num_teeth  # 18.166
tip_diameter = 20.2
root_diameter = 15.9
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle_deg))

# Bore and keying parameters
bore_diameter = 6.0
chordal_flat_width = 5.0  # Width of flat chord across the bore

# M3 countersink parameters
m3_clearance_dia = 3.4
m3_counterbore_dia = 6.0
m3_counterbore_depth = 3.5

# Involute gear tooth profile generation
def involute_point(base_r, angle):
    """Calculate a point on the involute curve"""
    x = base_r * (math.cos(angle) + angle * math.sin(angle))
    y = base_r * (math.sin(angle) - angle * math.cos(angle))
    return (x, y)

def create_gear_profile(num_teeth, module, pressure_angle_deg, tip_dia, root_dia):
    """Create a 2D gear profile with involute teeth"""
    pitch_r = (module * num_teeth) / 2
    base_r = pitch_r * math.cos(math.radians(pressure_angle_deg))
    tip_r = tip_dia / 2
    root_r = root_dia / 2
    
    # Angular pitch
    angular_pitch = 2 * math.pi / num_teeth
    
    # Tooth thickness at pitch circle (half of circular pitch for standard gear)
    tooth_thickness_angle = angular_pitch / 2
    
    # Generate points for one tooth profile
    points = []
    
    for i in range(num_teeth):
        tooth_angle = i * angular_pitch
        
        # Root circle arc start
        root_start_angle = tooth_angle - angular_pitch / 4
        
        # Generate involute curve points (left flank)
        inv_points_left = []
        max_inv_angle = math.sqrt((tip_r / base_r) ** 2 - 1) if tip_r > base_r else 0.5
        
        for j in range(8):
            inv_angle = j * max_inv_angle / 7
            px, py = involute_point(base_r, inv_angle)
            # Rotate to tooth position (left flank)
            rot_angle = tooth_angle - tooth_thickness_angle / 2
            rx = px * math.cos(rot_angle) - py * math.sin(rot_angle)
            ry = px * math.sin(rot_angle) + py * math.cos(rot_angle)
            r = math.sqrt(rx**2 + ry**2)
            if r >= root_r and r <= tip_r:
                inv_points_left.append((rx, ry))
        
        # Generate involute curve points (right flank - mirrored)
        inv_points_right = []
        for j in range(8):
            inv_angle = j * max_inv_angle / 7
            px, py = involute_point(base_r, inv_angle)
            py = -py  # Mirror
            # Rotate to tooth position (right flank)
            rot_angle = tooth_angle + tooth_thickness_angle / 2
            rx = px * math.cos(rot_angle) - py * math.sin(rot_angle)
            ry = px * math.sin(rot_angle) + py * math.cos(rot_angle)
            r = math.sqrt(rx**2 + ry**2)
            if r >= root_r and r <= tip_r:
                inv_points_right.append((rx, ry))
        
        # Add root arc point
        root_mid_angle = tooth_angle - angular_pitch / 2
        points.append((root_r * math.cos(root_mid_angle), root_r * math.sin(root_mid_angle)))
        
        # Add left involute (from root to tip)
        if inv_points_left:
            points.extend(inv_points_left)
        
        # Add tip arc
        tip_angle = tooth_angle
        points.append((tip_r * math.cos(tip_angle), tip_r * math.sin(tip_angle)))
        
        # Add right involute (from tip to root)
        if inv_points_right:
            points.extend(reversed(inv_points_right))
    
    return points

# Create simplified gear profile using polygon approximation
def create_simple_gear_profile(num_teeth, tip_r, root_r):
    """Create a simplified gear profile using circular approximation"""
    points = []
    angular_pitch = 2 * math.pi / num_teeth
    
    for i in range(num_teeth):
        tooth_angle = i * angular_pitch
        
        # Root point (valley between teeth)
        root_angle = tooth_angle - angular_pitch / 2
        points.append((root_r * math.cos(root_angle), root_r * math.sin(root_angle)))
        
        # Rising flank
        flank1_angle = tooth_angle - angular_pitch / 4
        mid_r = (tip_r + root_r) / 2
        points.append((mid_r * math.cos(flank1_angle), mid_r * math.sin(flank1_angle)))
        
        # Tip point
        points.append((tip_r * math.cos(tooth_angle), tip_r * math.sin(tooth_angle)))
        
        # Falling flank
        flank2_angle = tooth_angle + angular_pitch / 4
        points.append((mid_r * math.cos(flank2_angle), mid_r * math.sin(flank2_angle)))
    
    return points

# Generate gear tooth profile points
tip_r = tip_diameter / 2
root_r = root_diameter / 2
gear_points = create_simple_gear_profile(num_teeth, tip_r, root_r)

# Create the gear body by extruding the gear profile
gear_profile = cq.Workplane("XY").polyline(gear_points).close()
gear_body = gear_profile.extrude(face_width)

# Create the central bore (6.0 mm diameter)
gear_with_bore = (
    gear_body
    .faces(">Z")
    .workplane()
    .hole(bore_diameter, face_width)
)

# Create the chordal flat for keying to servo spline
# The flat is created by cutting away material to create a 5.0 mm chord across the 6.0 mm bore
# Calculate the depth of cut needed to create a 5.0 mm chord
bore_r = bore_diameter / 2
chord_half = chordal_flat_width / 2
# Distance from center to the flat: d = sqrt(r^2 - (chord/2)^2)
flat_distance = math.sqrt(bore_r**2 - chord_half**2)

# Create a cutting block for the chordal flat (positioned in +X direction)
flat_cut_depth = bore_r - flat_distance  # How deep to cut
flat_cut_width = chordal_flat_width + 2  # Slightly wider for clean cut
flat_cut_length = bore_r + 1  # Long enough to cut through

# Position the cutting block so it creates the flat
cut_x_pos = bore_r - flat_cut_depth / 2

gear_with_flat = (
    gear_with_bore
    .faces(">Z")
    .workplane()
    .center(flat_distance + flat_cut_depth / 2, 0)
    .rect(flat_cut_depth + 0.5, flat_cut_width)
    .cutThruAll()
)

# Add M3 countersunk hole on top face for horn screw
# Counterbore for M3 socket head cap screw
result = (
    gear_with_flat
    .faces(">Z")
    .workplane()
    .cboreHole(m3_clearance_dia, m3_counterbore_dia, m3_counterbore_depth, face_width)
)