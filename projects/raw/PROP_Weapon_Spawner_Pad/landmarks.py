"""
Reference landmarks for PROP_Weapon_Spawner_Pad (Sci-fi Gym Floor Weapon Spawner).
Low-profile regular hexagonal metallic platform:
  Outer Diameter = 1.500 m (Radius = 0.750 m)
  Dimensions: Width = 1.500 m (along X), Depth = 1.299 m (along Y), Height = 0.160 m (along Z)
  Floor contact at Z = 0.000 m
"""
import math
from workbench.refmap import RefMap

ASSET = "PROP_Weapon_Spawner_Pad"
IMAGE_SIZE = (720, 572)
S = 200.0                         # px per metre
ANCHOR_PX = (360.0, 286.0)
ANCHOR_YZ = (0.0, 0.08)
THETA = 0.0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
REF.ortho = True
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

ANCHORS = []
MARKS = []
SILHOUETTE = []

# --- Primary Spawner Platform Dimensions (metres) -----------------------------
RADIUS_OUTER = 0.750               # 1.500 m diameter
RADIUS_DECK  = 0.640               # top surface outer radius
RADIUS_STRIP = 0.570               # glowing hexagonal emissive strip
RADIUS_WELL  = 0.350               # central circular projector well
RADIUS_CORE  = 0.115               # central hologram emitter lens
RADIUS_LENS  = 0.048               # 4 satellite projector lenses
LENS_DIST    = 0.215               # radial distance of satellite lenses

HEIGHT_TOTAL = 0.160               # 160 mm total platform height
HEIGHT_BASE  = 0.035               # vertical bottom lip
HEIGHT_DECK  = 0.150               # upper deck surface
HEIGHT_LENS  = 0.160               # raised lens bezels

# Widths / bounding dimensions:
WIDTH_X = 2.0 * RADIUS_OUTER                      # 1.500 m
DEPTH_Y = 2.0 * RADIUS_OUTER * math.cos(math.pi/6) # 1.299 m
HEIGHT_Z = HEIGHT_TOTAL                            # 0.160 m
