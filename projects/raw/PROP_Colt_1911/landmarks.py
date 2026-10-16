"""
Reference landmarks for PROP_Colt_1911 (single source of truth for proportions).

Extracted from orthographic renders of the original Colt M1911-A1 geometry:
- Scale: 7314.2857 px/m (2048 px / 0.28m ortho span)
- Camera: Left side view (-Y towards +Y), front (muzzle) is on image right.
- Coordinates: +Z up, -Y forward (muzzle), +X object's left (controls side).
- Ground contact: lowest point (magazine floorplate) seated at Z = 0.0000 m.
"""
import math
from workbench.refmap import RefMap

ASSET = "PROP_Colt_1911"
IMAGE_SIZE = (2048, 1536)
S = 2048.0 / 0.28                     # 7314.2857 px/m
ANCHOR_PX = (1024.0, 768.0)
ANCHOR_YZ = (-0.065, 0.07625)
THETA = 0.0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

ANCHORS = [
    ((0.0, *P(*ANCHOR_PX)), ANCHOR_PX),
    ((0.0, *P(1872.0, 282.0)), (1872.0, 282.0)),  # Slide front top
    ((0.0, *P(384.0, 282.0)), (384.0, 282.0)),    # Slide rear top
]

# --- Key component bounding widths (in metres, centered around X = 0) --------
SLIDE_HALF_WIDTH = 0.01245           # 24.9 mm total
FRAME_HALF_WIDTH = 0.01125           # 22.5 mm total
GRIP_HALF_WIDTH = 0.0150             # 30.0 mm total across grip screws
TRIGGER_HALF_WIDTH = 0.0040          # 8.0 mm
HAMMER_HALF_WIDTH = 0.00585          # 11.7 mm
BARREL_RADIUS = 0.00725              # 14.5 mm OD

# --- 2D Contours from measured mask (px) -------------------------------------
# Slide main block
SLIDE_POLY = [
    (1665.0, 282.0), (1872.0, 282.0), (1872.0, 290.0), (1877.0, 292.0), (1879.0, 484.0),
    (1879.0, 550.0), (1872.0, 552.0), (1872.0, 581.0), (1547.0, 583.0), (1545.0, 482.0),
    (384.0, 482.0), (389.0, 455.0), (385.0, 447.0), (404.0, 366.0), (419.0, 328.0),
    (448.0, 286.0), (1665.0, 282.0)
]

# Frame complete outline (dust cover, trigger guard, arched backstrap, beavertail tang, lanyard toe)
FRAME_POLY = [
    (390.0, 450.0), (1004.0, 450.0), (1033.0, 451.0), (1034.0, 483.0), (1546.0, 484.0),
    (1546.0, 595.0), (1281.0, 594.0), (1200.0, 599.0), (1181.0, 609.0), (1151.0, 645.0),
    (1137.0, 674.0), (1122.0, 737.0), (1112.0, 759.0), (1100.0, 776.0), (1072.0, 799.0),
    (1047.0, 810.0), (1016.0, 816.0), (819.0, 819.0), (799.0, 824.0), (630.0, 1299.0),
    (633.0, 1303.0), (679.0, 1310.0), (676.0, 1323.0), (610.0, 1314.0), (604.0, 1314.0),
    (596.0, 1325.0), (556.0, 1323.0), (257.0, 1282.0), (240.0, 1284.0), (236.0, 1312.0),
    (229.0, 1316.0), (224.0, 1311.0), (226.0, 1281.0), (194.0, 1275.0), (187.0, 1250.0),
    (189.0, 1211.0), (204.0, 1153.0), (234.0, 1069.0), (314.0, 891.0), (327.0, 886.0),
    (313.0, 884.0), (347.0, 805.0), (358.0, 768.0), (364.0, 721.0), (360.0, 696.0),
    (325.0, 635.0), (222.0, 614.0), (214.0, 593.0), (218.0, 577.0), (228.0, 566.0),
    (266.0, 554.0), (304.0, 551.0), (326.0, 537.0), (385.0, 483.0), (390.0, 450.0)
]

# Hammer outline
HAMMER_POLY = [
    (236.0, 410.0), (277.0, 423.0), (354.0, 484.0), (372.0, 485.0), (407.0, 467.0),
    (428.0, 469.0), (457.0, 483.0), (470.0, 497.0), (478.0, 520.0), (479.0, 547.0),
    (469.0, 579.0), (459.0, 591.0), (444.0, 598.0), (418.0, 600.0), (393.0, 594.0),
    (372.0, 580.0), (344.0, 530.0), (318.0, 514.0), (274.0, 504.0), (214.0, 507.0),
    (194.0, 520.0), (165.0, 552.0), (162.0, 531.0), (166.0, 517.0), (174.0, 503.0),
    (204.0, 482.0), (218.0, 464.0), (224.0, 447.0), (226.0, 412.0), (236.0, 410.0)
]

# Trigger shoe
TRIGGER_POLY = [
    (874.0, 606.0), (937.0, 607.0), (898.0, 648.0), (886.0, 676.0), (883.0, 697.0),
    (887.0, 733.0), (899.0, 759.0), (937.0, 799.0), (840.0, 797.0), (822.0, 788.0),
    (822.0, 618.0), (839.0, 609.0), (874.0, 606.0)
]

# Trigger guard inner hole (cutout)
TRIGGER_HOLE_POLY = [
    (974.0, 606.0), (1017.0, 607.0), (1057.0, 615.0), (1083.0, 631.0),
    (1106.0, 663.0), (1112.0, 703.0), (1103.0, 739.0), (1074.0, 776.0),
    (1042.0, 794.0), (998.0, 800.0), (938.0, 799.0), (900.0, 759.0),
    (888.0, 733.0), (884.0, 697.0), (887.0, 676.0), (899.0, 648.0),
    (938.0, 608.0), (974.0, 606.0)
]

# Walnut checkered grip panels
GRIP_PANEL_POLY = [
    (608.0, 521.0), (657.0, 525.0), (688.0, 534.0), (764.0, 565.0),
    (770.0, 580.0), (542.0, 1304.0), (537.0, 1312.0), (518.0, 1315.0),
    (303.0, 1285.0), (303.0, 1270.0), (263.0, 1198.0), (539.0, 542.0),
    (571.0, 528.0), (608.0, 521.0)
]

# Sights
SIGHT_FRONT_POLY = [
    (1817.0, 262.0), (1839.0, 266.0), (1861.0, 281.0), (1862.0, 287.0), (1788.0, 287.0),
    (1790.0, 277.0), (1817.0, 262.0)
]

SIGHT_REAR_POLY = [
    (523.0, 255.0), (538.0, 255.0), (540.0, 272.0), (564.0, 281.0), (569.0, 311.0),
    (492.0, 311.0), (497.0, 281.0), (520.0, 273.0), (523.0, 255.0)
]

# Bridged frame silhouette for 2D rasterization with empty trigger hole
_f_idx = [i for i, p in enumerate(FRAME_POLY) if p == (1016.0, 816.0)][0]
FRAME_SILHOUETTE_POLY = FRAME_POLY[:_f_idx+1] + TRIGGER_HOLE_POLY + [(1016.0, 816.0)] + FRAME_POLY[_f_idx+1:]

MARKS = [
    ANCHOR_PX,
    (1872.0, 282.0),  # muzzle top
    (384.0, 282.0),   # slide rear top
    (162.0, 531.0),   # hammer tip
    (596.0, 1325.0),  # magazine floor
]

SILHOUETTE = [
    FRAME_SILHOUETTE_POLY,
    SLIDE_POLY,
    HAMMER_POLY,
    TRIGGER_POLY,
    SIGHT_FRONT_POLY,
    SIGHT_REAR_POLY,
]

PART_OUTLINES = {
    "SLIDE_Main": SLIDE_POLY,
    "FRAME_Main": FRAME_SILHOUETTE_POLY,
    "HAMMER_Main": HAMMER_POLY,
    "TRIGGER_Shoe": TRIGGER_POLY,
    "GRIP_Panels_L": GRIP_PANEL_POLY,
    "GRIP_Panels_R": GRIP_PANEL_POLY,
    "SIGHTS_Front": SIGHT_FRONT_POLY,
    "SIGHTS_Rear": SIGHT_REAR_POLY,
}
