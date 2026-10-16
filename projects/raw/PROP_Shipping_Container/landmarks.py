"""
Reference landmarks for PROP_Shipping_Container (20ft standard ISO shipping container).
True ground truth dimensions (metres):
  Length = 6.0 m (along Y: -3.0 to +3.0)
  Width  = 2.4 m (along X: -1.2 to +1.2)
  Height = 2.6 m (along Z: 0.0 to 2.6)
Standard ISO 668 1CC container specifications.
"""
import math
from workbench.refmap import RefMap

ASSET = "PROP_Shipping_Container"
IMAGE_SIZE = (512, 286)
S = 50.0                          # px per metre
ANCHOR_PX = (256.0, 143.0)
ANCHOR_YZ = (0.0, 1.3)
THETA = 0.0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
REF.ortho = True
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

ANCHORS = []
MARKS = []
SILHOUETTE = []

# --- Primary Container Dimensions (metres) ------------------------------------
LENGTH = 6.000                     # along Y
WIDTH = 2.400                      # along X
HEIGHT = 2.600                     # along Z

HALF_L = LENGTH / 2.0              # 3.000
HALF_W = WIDTH / 2.0               # 1.200
Z_GROUND = 0.000
Z_TOP = HEIGHT                     # 2.600

# Corner castings (ISO 1161 standard dimensions):
CASTING_L = 0.178                  # 178 mm along Y
CASTING_W = 0.162                  # 162 mm along X
CASTING_H = 0.118                  # 118 mm along Z
APERTURE_R = 0.032                 # aperture radius

# Frame structural members:
POST_SIZE = 0.150                  # corner post cross-section
RAIL_BOT_H = 0.160                 # bottom rail height
RAIL_TOP_H = 0.120                 # top rail height
SILL_H = 0.160                     # door sill height
HEADER_H = 0.140                   # door header height

# Forklift pockets:
POCKET_SPACING = 2.050             # center-to-center distance along Y
POCKET_Y_FRONT = -POCKET_SPACING / 2.0  # -1.025
POCKET_Y_REAR = POCKET_SPACING / 2.0   # +1.025
POCKET_W = 0.355                   # width along Y
POCKET_H = 0.115                   # height along Z
POCKET_Z_BOT = 0.020               # bottom clearance

# Corrugations:
WALL_THICKNESS = 0.004             # sheet metal
WALL_RIB_DEPTH = 0.042             # rib depth inward/outward
WALL_RIB_PITCH = 0.280             # rib cycle pitch along Y
ROOF_RIB_DEPTH = 0.025
ROOF_RIB_PITCH = 0.250

# Doors (on BOTH ends: Y = -HALF_L and Y = +HALF_L):
DOOR_Z_BOT = SILL_H
DOOR_Z_TOP = Z_TOP - HEADER_H
DOOR_GAP = 0.008                   # central gap between leaves
DOOR_LEAF_W = (WIDTH - 2 * POST_SIZE - DOOR_GAP) / 2.0  # ~1.046 m
LOCKING_BAR_R = 0.018              # 36 mm diameter pipe
BAR_OFFSET_OUTER = 0.360           # distance from outer post
BAR_OFFSET_INNER = 0.720           # distance from outer post
HINGE_COUNT = 4
HINGE_Z_POSITIONS = [0.35, 0.90, 1.50, 2.15]
HANDLE_Z = 1.05
