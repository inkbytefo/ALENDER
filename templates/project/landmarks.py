"""
Reference landmarks for __ASSET__  (single source of truth for proportions).

Store silhouettes and key points in PHOTO PIXELS (u right, v down) measured on
ref/REAL_REFERENCE.png with `python wb.py grid` / `python wb.py crop`, then convert with REF.P().
Never type metre coordinates for things you can measure in the photo.

Procedure: docs/03_REFERENCE_ANALYSIS.md
  1. which side does the photo show?  front on image right -> front_is_right=True, camera at -X
  2. scale S (px/m) from a KNOWN real dimension; cross-check with 2 other dimensions
  3. anchor: one measured pixel whose world (Y, Z) you define (e.g. a wheel axle, a foot)
  4. tilt THETA if the object is visibly rotated in the photo (else 0)
"""
import math
from workbench.refmap import RefMap

ASSET = "__ASSET__"
IMAGE_SIZE = (1080, 720)          # TODO: size of ref/REAL_REFERENCE.png
S = 400.0                         # TODO px per metre
ANCHOR_PX = (540.0, 600.0)        # TODO measured pixel of the anchor point
ANCHOR_YZ = (0.0, 0.0)            # TODO its world (Y, Z) in metres (Z=0 on the ground)
THETA = 0.0                       # TODO photo tilt (radians), usually 0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

# reference-camera anchors: [(world xyz, pixel), ...] at least two well separated points
ANCHORS = [((0.0, *P(*ANCHOR_PX)), ANCHOR_PX)]

# --- silhouettes / key points (px) ------------------------------------------------------------
# EXAMPLE (replace): outline of the main body seen from the side
BODY_OUTLINE = [(340, 600), (740, 600), (740, 400), (340, 400)]
BODY_HALF_WIDTH = 0.25            # metres (depth is never visible in a side photo: estimate & tag)

# crosses drawn by `python wb.py compare`
MARKS = [ANCHOR_PX]

# reference silhouette (gate R01): closed px polygons whose union is the object seen in the photo.
# Photo truth for gate R02: python wb.py mask __ASSET__  (plain light backgrounds; LOOK at the result).
# Measure edges instead of reading them by eye: python wb.py profile __ASSET__ U0 U1 V0 V1 --side top|bottom
SILHOUETTE = [BODY_OUTLINE]
PART_OUTLINES = {}                # optional {"BODY_Main": BODY_OUTLINE} -> per-part check R03
