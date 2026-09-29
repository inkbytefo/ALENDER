"""
Reference landmarks for VEH_FF12_RacingCar  (single source of truth for proportions).

Photo analysis (docs/03_REFERENCE_ANALYSIS.md):
  * Primary reference photo: ref/REAL_REFERENCE.png (681x1265 px, top-down view).
  * Scale: Wheelbase = 2.56 m, measured in photo between front axle (v=205) and rear axle (v=823)
    => 618 px / 2.56 m = 241.406 px/m longitudinal (Y).
  * Track width: 1.46 m (X = +/-0.73 m), with overall width 1.72-1.78 m across wide Yokohama Advan tires.
  * Secondary photos: ref/REF_OBLIQUE.png (oblique 3/4 perspective), ref/MODELING_CHEATSHEET.png
    (cross-sections, side & front orthos).
  * Camera calibration: Top camera at (cx=0.0431, cy=0.4907, cz=6.00), lens=71.97 mm reproduces
    photo wheel positions with RMS reprojection error < 0.2 px.

Coordinate convention (docs/02_STANDARDS.md):
  +Z up, -Y forward (nose), +X = car's LEFT side.
  Root origin at (0, 0, 0) midway between axles on the ground plane (Z=0).
"""
import math
from workbench.refmap import RefMap

ASSET = "VEH_FF12_RacingCar"
IMAGE_SIZE = (681, 1265)

# --- Primary dimensions (metres) --------------------------------------------
WHEELBASE = 2.56
TRACK_WIDTH = 1.46
OVERALL_LENGTH = 3.80
GROUND_CLEARANCE = 0.12
BODY_MAX_HEIGHT = 0.78

# Wheels & Tyres
R_TYRE = 0.36          # ⌀ 0.72 m (Yokohama Advan wide tires)
W_TYRE = 0.32          # Tyre width
R_RIM = 0.23           # 18-inch wire spoke rim (⌀ 0.46 m)
W_RIM = 0.29           # Rim width

# Axle centres in world space (X, Y, Z)
FRONT_AXLE_Y = -WHEELBASE / 2.0  # -1.28 m
REAR_AXLE_Y = WHEELBASE / 2.0   # +1.28 m
AXLE_Z = R_TYRE                 # 0.36 m
HALF_TRACK = TRACK_WIDTH / 2.0  # 0.73 m

AXLE_FL = (+HALF_TRACK, FRONT_AXLE_Y, AXLE_Z)
AXLE_FR = (-HALF_TRACK, FRONT_AXLE_Y, AXLE_Z)
AXLE_RL = (+HALF_TRACK, REAR_AXLE_Y, AXLE_Z)
AXLE_RR = (-HALF_TRACK, REAR_AXLE_Y, AXLE_Z)

# Photo pixels corresponding to axle centres
AXLE_FL_PX = (135.0, 205.0)
AXLE_FR_PX = (567.0, 205.0)
AXLE_RL_PX = (135.0, 823.0)
AXLE_RR_PX = (567.0, 823.0)

# --- Top-Down Reference Map --------------------------------------------------
S_Y = 241.406
S_X = 295.890
ANCHOR_PX = (351.0, 514.0)
ANCHOR_YZ = (0.0, 0.0)

REF = RefMap(S_Y, ANCHOR_PX, ANCHOR_YZ, theta=0.0, front_is_right=False, image_size=IMAGE_SIZE)
REF.view = "TOP"
REF.cam_loc = (0.0431, 0.4907, 6.00)
REF.cam_rot = (0.0, 0.0, math.radians(180.0))
REF.lens = 71.97

def P_top(u, v):
    """Convert photo (u, v) px -> (X, Y) world metres."""
    x = (351.0 - u) / S_X
    y = (v - 514.0) / S_Y
    return x, y

def photo_of_top(x, y):
    """Convert world (X, Y) metres -> photo (u, v) px."""
    u = 351.0 - x * S_X
    v = 514.0 + y * S_Y
    return u, v

P, P3, photo_of = REF.P, REF.P3, REF.photo_of

# Anchors for reference camera alignment check
ANCHORS = [
    ((+0.8947, FRONT_AXLE_Y, AXLE_Z), AXLE_FL_PX),
    ((-0.8947, FRONT_AXLE_Y, AXLE_Z), AXLE_FR_PX),
    ((+0.8947, REAR_AXLE_Y,  AXLE_Z), AXLE_RL_PX),
    ((-0.8947, REAR_AXLE_Y,  AXLE_Z), AXLE_RR_PX),
]

MARKS = [AXLE_FL_PX, AXLE_FR_PX, AXLE_RL_PX, AXLE_RR_PX, ANCHOR_PX]

# --- Body stations: (Y, z_bot, z_top, half_width_x) --------------------------
# Shaped according to cheatsheet cross-sections S1-S5 and photo silhouettes
BODY_STATIONS = [
    # S1: Nose cone tip & front intake
    (-1.90, 0.20, 0.38, 0.09),
    (-1.75, 0.17, 0.43, 0.14),
    (-1.55, 0.15, 0.49, 0.19),
    # S2: Front cowl / suspension station
    (-1.28, 0.14, 0.58, 0.24),
    (-1.00, 0.13, 0.63, 0.27),
    # S3: Mid-body engine cowl with dual louver rows
    (-0.65, 0.12, 0.68, 0.285),
    (-0.30, 0.12, 0.68, 0.29),
    # S4: Cockpit surround (cutout above z=0.55 between Y=-0.05 and Y=0.68)
    (-0.05, 0.12, 0.72, 0.29),
    (+0.30, 0.12, 0.66, 0.29),
    (+0.68, 0.13, 0.78, 0.26),  # Headrest fairing peak
    # S5: Rear body & tapered tail
    (+1.00, 0.14, 0.68, 0.23),
    (+1.28, 0.16, 0.60, 0.21),  # Rear axle station
    (+1.60, 0.18, 0.50, 0.15),
    (+1.90, 0.24, 0.42, 0.06),  # Cigar tail tip
]

# Front splitter / carbon wing
SPLITTER_Y_FRONT = -1.95
SPLITTER_Y_REAR  = -1.55
SPLITTER_HALF_W  = 0.55
SPLITTER_Z       = 0.08

# Dorsal stability fin (centerline X=0, along rear deck)
DORSAL_FIN_START = (+0.68, 0.78)   # (Y, Z) behind driver headrest
DORSAL_FIN_END   = (+2.15, 0.38)   # (Y, Z) extends past tail tip
DORSAL_FIN_THICK = 0.012

# Side dive planes / aero wings
CANARD_L_PTS = [(0.28, -0.45, 0.26), (0.56, -0.42, 0.26), (0.54, -0.10, 0.26), (0.28, -0.05, 0.26)]
CANARD_R_PTS = [(-0.28, -0.45, 0.26), (-0.52, -0.42, 0.26), (-0.50, -0.10, 0.26), (-0.28, -0.05, 0.26)]

# Exhaust path (runs down right flank -X)
EXHAUST_PATH = [
    (-0.26, -0.68, 0.48),
    (-0.31, -0.38, 0.44),
    (-0.35,  0.05, 0.38),
    (-0.35,  0.65, 0.38),
    (-0.34,  1.25, 0.38),
    (-0.30,  1.65, 0.40),
]
EXHAUST_R = 0.038        # ⌀ 76 mm pipe
EXHAUST_WRAP_R = 0.046   # ⌀ 92 mm heat wrap section (from Y=-0.25 to Y=0.85)

# Cockpit components
COCKPIT_CUTOUT_Y = (-0.05, 0.68)
COCKPIT_FLOOR_Z  = 0.16
STEERING_CENTER  = (0.0, 0.08, 0.66)
STEERING_R       = 0.18
STEERING_ANGLE   = math.radians(24.0)

SEAT_CENTER      = (0.0, 0.44, 0.30)
SEAT_DIMS        = (0.42, 0.50, 0.52)  # (width, length, height)

WINDSCREEN_Y     = (-0.05, 0.10)
WINDSCREEN_Z     = (0.72, 0.86)
WINDSCREEN_W     = 0.42

# Fuel filler caps (twin caps on rear deck behind headrest)
FUEL_CAP_L = (+0.14, 0.96, 0.69)
FUEL_CAP_R = (-0.14, 0.96, 0.69)
FUEL_CAP_R_SIZE = 0.040

# Suspension geometry (metres)
# Front wishbones
SUSP_F_UPPER_CHASSIS_1 = (0.22, -1.36, 0.45)
SUSP_F_UPPER_CHASSIS_2 = (0.22, -1.20, 0.45)
SUSP_F_LOWER_CHASSIS_1 = (0.20, -1.36, 0.20)
SUSP_F_LOWER_CHASSIS_2 = (0.20, -1.20, 0.20)
SUSP_F_UPPER_HUB       = (0.60, -1.28, 0.44)
SUSP_F_LOWER_HUB       = (0.60, -1.28, 0.22)
SUSP_F_TIEROD_CHASSIS  = (0.22, -1.18, 0.34)
SUSP_F_TIEROD_HUB      = (0.60, -1.18, 0.34)
SUSP_F_COILOVER_TOP    = (0.24, -1.28, 0.48)
SUSP_F_COILOVER_BOT    = (0.52, -1.28, 0.24)

# Rear wishbones
SUSP_R_UPPER_CHASSIS_1 = (0.18,  1.18, 0.46)
SUSP_R_UPPER_CHASSIS_2 = (0.18,  1.38, 0.46)
SUSP_R_LOWER_CHASSIS_1 = (0.16,  1.18, 0.20)
SUSP_R_LOWER_CHASSIS_2 = (0.16,  1.38, 0.20)
SUSP_R_UPPER_HUB       = (0.60,  1.28, 0.45)
SUSP_R_LOWER_HUB       = (0.60,  1.28, 0.22)
SUSP_R_HALFOUT_INNER   = (0.14,  1.28, 0.36)
SUSP_R_HALFOUT_HUB     = (0.60,  1.28, 0.36)
SUSP_R_COILOVER_TOP    = (0.20,  1.28, 0.50)
SUSP_R_COILOVER_BOT    = (0.52,  1.28, 0.24)
