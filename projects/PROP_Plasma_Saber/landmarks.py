"""
Reference landmarks for PROP_Plasma_Saber (single source of truth for proportions).

Store silhouettes and key points in PHOTO PIXELS (u right, v down) measured on
ref/REAL_REFERENCE.png, then convert with REF.P().
Model convention: +Z up, -Y forward (emitter right), +X = object's LEFT side.
Scale: 2500 px/m (2.5 px/mm), overall hilt length 750 px = 0.300 m (300 mm).
"""
import math
from workbench.refmap import RefMap

ASSET = "PROP_Plasma_Saber"
IMAGE_SIZE = (1280, 720)
S = 2500.0                       # 2500 px/m -> 2.5 px/mm
ANCHOR_PX = (640.0, 360.0)       # Center of hilt in image (u=640, v=360)
ANCHOR_YZ = (0.0, 0.0)           # World (Y=0, Z=0)
THETA = 0.0                      # Horizontal alignment

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
REF.ortho = True                 # Orthographic reference
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

# Reference-camera anchors: well-separated points along the bore line
ANCHORS = [
    ((0.0, *P(640.0, 360.0)), (640.0, 360.0)),
    ((0.0, *P(1015.0, 360.0)), (1015.0, 360.0)),
    ((0.0, *P(245.0, 360.0)), (245.0, 360.0)),
]

MARKS = [ANCHOR_PX, (265.0, 360.0), (1015.0, 360.0)]

# Centerline
V0 = 360.0

# Key section bounds along U
POMMEL_U0, POMMEL_U1 = 265.0, 325.0
DRING_U0, DRING_U1 = 245.0, 268.0
CHASSIS_LOWER_U0, CHASSIS_LOWER_U1 = 325.0, 350.0
GRIP_U0, GRIP_U1 = 350.0, 580.0
GRIP_RIBS_U0, GRIP_RIBS_U1 = 355.0, 525.0
GRIP_CHOKE_U0, GRIP_CHOKE_U1 = 530.0, 580.0
SWITCH_U0, SWITCH_U1 = 580.0, 680.0
SWITCH_BOX_U0, SWITCH_BOX_U1 = 590.0, 670.0
CHAMBER_U0, CHAMBER_U1 = 680.0, 760.0
CHASSIS_UPPER_U0, CHASSIS_UPPER_U1 = 760.0, 810.0
EMITTER_BASE_U0, EMITTER_BASE_U1 = 810.0, 890.0
EMITTER_SHROUD_U0, EMITTER_SHROUD_U1 = 890.0, 1015.0

# Radii in pixels (divide by S to get metres)
R_MAIN_TUBE = 43.75        # 17.5 mm -> 0.0175 m
R_COLLAR = 50.0            # 20.0 mm -> 0.0200 m
R_CHOKE = 40.0             # 16.0 mm -> 0.0160 m
R_POMMEL_CAP = 48.75       # 19.5 mm -> 0.0195 m
R_EMITTER_COIL = 51.25     # 20.5 mm -> 0.0205 m
R_EMITTER_SHROUD = 52.5    # 21.0 mm -> 0.0210 m
R_NOZZLE = 27.5            # 11.0 mm -> 0.0110 m
R_CRYSTAL = 15.0           # 6.0 mm  -> 0.0060 m

# Reference silhouette polygon (gate R01)
SILHOUETTE_POLY = [
    # Emitter shroud top edge
    (1015.0, 307.5),
    (890.0, 307.5),
    # Bronze focus ring 2 & 1
    (890.0, 308.75),
    (840.0, 308.75),
    # Radiator base
    (840.0, 310.0),
    (810.0, 310.0),
    # Upper choke collar with cooling ribs
    (810.0, 320.0),
    (795.0, 320.0),
    (795.0, 312.5),
    (780.0, 312.5),
    (780.0, 320.0),
    (760.0, 320.0),
    # Crystal chamber top strut
    (760.0, 311.25),
    (680.0, 311.25),
    # Switch box housing (rises on +Z)
    (680.0, 311.25),
    (670.0, 311.25),
    (670.0, 302.5),
    (590.0, 302.5),
    (590.0, 311.25),
    (580.0, 311.25),
    # Grip choke band
    (580.0, 313.75),
    (530.0, 313.75),
    # Grip ribbed section
    (530.0, 312.5),
    (355.0, 312.5),
    (355.0, 316.25),
    (350.0, 316.25),
    # Lower clamp collar
    (350.0, 310.0),
    (325.0, 310.0),
    # Pommel cap
    (325.0, 316.25),
    (315.0, 316.25),
    (315.0, 311.25),
    (275.0, 311.25),
    (275.0, 317.5),
    (265.0, 317.5),
    # D-ring bracket and loop
    (265.0, 335.0),
    (245.0, 335.0),
    (245.0, 385.0),
    (265.0, 385.0),
    # Pommel cap bottom
    (265.0, 402.5),
    (275.0, 402.5),
    (275.0, 408.75),
    (315.0, 408.75),
    (315.0, 403.75),
    (325.0, 403.75),
    # Lower clamp collar bottom
    (325.0, 410.0),
    (350.0, 410.0),
    # Grip bottom
    (350.0, 403.75),
    (355.0, 403.75),
    (355.0, 407.5),
    (530.0, 407.5),
    (530.0, 406.25),
    (580.0, 406.25),
    # Mid collar bottom (switch box is only on +Z)
    (580.0, 408.75),
    (680.0, 408.75),
    # Crystal chamber bottom strut
    (680.0, 408.75),
    (760.0, 408.75),
    # Upper choke collar bottom
    (760.0, 400.0),
    (780.0, 400.0),
    (780.0, 407.5),
    (795.0, 407.5),
    (795.0, 400.0),
    (810.0, 400.0),
    # Radiator & focus rings bottom
    (810.0, 410.0),
    (840.0, 410.0),
    (840.0, 411.25),
    (890.0, 411.25),
    (890.0, 412.5),
    # Angled emitter shroud bottom cut
    (935.0, 412.5),
]

SILHOUETTE = [SILHOUETTE_POLY]
