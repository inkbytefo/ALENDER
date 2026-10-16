"""
Reference landmarks and dimensional hardpoints for CHAR_Tactical_Mannequin.
Shooting range target dummy on a steel floor stand with spring base.
All coordinates in world metres (+Z up, -Y forward, +X object's left).
"""
from mathutils import Vector
from workbench.refmap import RefMap

ASSET = "CHAR_Tactical_Mannequin"
IMAGE_SIZE = (1024, 935)
S = 328.57
ANCHOR_PX = (143.5, 612.0)
ANCHOR_YZ = (0.0, 0.0)
THETA = 0.0
REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=False, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

# Total dimensions
TOTAL_HEIGHT = 1.750
BASE_WIDTH = 0.420
BASE_DEPTH = 0.420
BODY_WIDTH = 0.680
BODY_THICKNESS = 0.016

# Stand & Base hardpoints
BASE_FEET_Z = 0.000
FOOT_PAD_SIZE = (0.060, 0.080, 0.012)
FOOT_RADIUS = 0.170  # gives exactly 2*(0.170 + 0.040) = 0.420m footprint
STAND_HUB_CENTER = (0.0, 0.0, 0.160)
STAND_HUB_SIZE = (0.090, 0.090, 0.080)

# Spring hardpoints
SPRING_Z_START = 0.220
SPRING_Z_END = 0.520
SPRING_RADIUS = 0.040
SPRING_WIRE_RADIUS = 0.0075
SPRING_TURNS = 7.5
LOWER_SLEEVE_CENTER = (0.0, 0.0, 0.210)
UPPER_SLEEVE_CENTER = (0.0, 0.0, 0.540)
SLEEVE_SIZE = (0.070, 0.070, 0.040)

# Back spine channel & clamps
SPINE_Y = 0.032
SPINE_CENTER = (0.0, SPINE_Y, 1.000)
SPINE_SIZE = (0.045, 0.045, 0.900)
CLAMP_Z_LEVELS = [0.720, 1.050, 1.350]

# Silhouette Body Outline & Plates
BODY_Y = 0.000
TORSO_BOTTOM_Z = 0.630
HEAD_TOP_Z = 1.750

# Hit zones
HEAD_PLATE_CENTER = (0.0, -0.010, 1.640)
HEAD_PLATE_SIZE = (0.200, 0.008, 0.190)

CHEST_PLATE_CENTER = (0.0, -0.010, 1.250)
CHEST_PLATE_SIZE = (0.320, 0.008, 0.300)

MID_PLATE_CENTER = (0.0, -0.010, 0.860)
MID_PLATE_SIZE = (0.290, 0.008, 0.320)

ARM_L_CENTER = (0.300, -0.010, 1.210)
ARM_R_CENTER = (-0.300, -0.010, 1.210)
ARM_PLATE_SIZE = (0.080, 0.008, 0.320)

# Critical pairs for intersection / hygiene gates
CRITICAL_PAIRS = []
ANCHORS = []
SILHOUETTE = []
PART_OUTLINES = {}
