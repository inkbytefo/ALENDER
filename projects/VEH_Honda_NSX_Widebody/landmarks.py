"""
Landmarks for VEH_Honda_NSX_Widebody (red widebody NSX, hero vehicle, game + render).

TRUTH SOURCES
  * REAL_REFERENCE.png      front 3/4 perspective photo (identity, widths, details) - NOT gate-able
                            as an orthographic image without a camera fit.
  * REF_SIDE_BLUEPRINT.png  right-side view cropped 4x from the cheatsheet panel 4 (AI sheet, but the
                            only orthographic side drawing; consistent with the photo's proportions).
                            REF_MASK.png = its segmented silhouette (intake.py), used by R01/R02.
All longitudinal/vertical numbers are PIXELS of REF_SIDE_BLUEPRINT.png (u right = nose, v down).
Scale: wheelbase 2.53 m (sheet text) = 1157 px between measured axle centres -> 457.3 px/m.
Sheet text says L 4.40 / H 1.15 but the drawn car is 4.27 x 1.06 m at that scale: the drawing wins
(it is what the photo-consistent silhouette is made from); the mismatch is logged in project.md.
Widths come from the sheet front view / photo (side view never shows them): body 1.82 m,
arches 2.00 m, front track 1.68 m  -> tagged UNCERTAIN_BodyWidths.
"""
from workbench.refmap import RefMap

ASSET = "VEH_Honda_NSX_Widebody"
REFERENCE_IMAGE = "REF_SIDE_BLUEPRINT.png"
IMAGE_SIZE = (2040, 556)
S = 457.3
AXLE_F = (1560.0, 410.0)
AXLE_R = (403.0, 410.0)
GROUND_V = 551.0
AXLE_Z = 0.31                       # (551-410)/457.3 = 0.308
REF = RefMap(S, AXLE_F, (-1.265, AXLE_Z), 0.0, front_is_right=True, image_size=IMAGE_SIZE)
REF.ortho = True                  # the drawing is orthographic -> orthographic reference camera
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

ANCHORS = [((0.0, -1.265, AXLE_Z), AXLE_F), ((0.0, 1.265, AXLE_Z), AXLE_R)]
MARKS = [AXLE_F, AXLE_R, (60, 337), (2011, 521), (900, 68)]

WHEEL_U = (AXLE_R[0], AXLE_F[0])            # rear, front
WHEEL_V = 410.0
TIRE_R_PX = 142.0                            # 0.31 m
RIM_R_PX = 100.0                             # black multi-spoke ~19"
TRACK_X = (0.85, 0.85)                       # wheel centre |x| rear, front (front track 1.68 m)
TIRE_W = (0.30, 0.27)                        # rear, front tread width (m)

# --- body shell stations -------------------------------------------------------------------------
# (u, v_top of shell, half_width m).  Cabin (greenhouse) sits on top of it.
BODY_TOP = [(62, 337), (100, 323), (118, 321), (121, 232), (140, 216), (306, 203), (430, 204), (500, 196),
            (570, 192), (660, 205), (740, 222), (900, 234), (1300, 238), (1425, 232), (1456, 240),
            (1560, 238), (1630, 245), (1700, 254), (1780, 276), (1845, 304), (1870, 317), (1877, 328),
            (1898, 328), (1901, 336), (1922, 340), (1929, 348), (1958, 360), (1971, 374), (1979, 377), (1991, 378),
            (1995, 393)]
BODY_BOTTOM = [(62, 474), (84, 505), (200, 531), (260, 548), (1300, 548), (1700, 548), (1900, 548),
               (1960, 545), (1971, 515), (1979, 490), (1990, 419), (1995, 418)]
BODY_HALF_W = [(62, .82), (110, .90), (200, .98), (300, 1.00), (403, 1.00), (520, .99), (640, .94),
               (760, .915), (1250, .915), (1350, .95), (1450, 1.00), (1560, 1.00), (1700, .99),
               (1850, .93), (1960, .84), (1995, .76)]
# greenhouse (cabin): roof top line + half widths (belt width / roof width)
ROOF_TOP = [(574, 174), (581, 168), (617, 156), (654, 156), (664, 148), (668, 112), (714, 104), (733, 88), (782, 84), (822, 76), (894, 68),
            (1074, 72), (1110, 76), (1145, 96), (1202, 116), (1266, 144), (1402, 212), (1430, 230)]
CABIN_BELT_V = [(570, 192), (740, 222), (1430, 233)]
CABIN_BELT_HW = 0.80
CABIN_ROOF_HW = 0.52

# aero / details (px on the blueprint) --------------------------------------------------------------
WING_ENDPLATE = [(105, 80), (206, 88), (245, 108), (304, 112), (304, 207), (250, 218), (150, 224), (121, 232), (105, 229)]
WING_BLADE = [(105, 82), (300, 108), (300, 128), (105, 102)]
WING_UPRIGHT = [(150, 100), (262, 114), (262, 205), (150, 214)]
WING_HALF = 0.88                              # end plates at +-0.88 m (UNCERTAIN)
WING_UP_X = 0.36
SIDE_INTAKE = [(655, 300), (745, 292), (770, 450), (700, 455), (655, 420)]   # dark recess behind door
DOOR_SEAM = [(745, 232), (738, 300), (770, 440), (1305, 440), (1315, 400), (1305, 238)]
MIRROR_UV = (1195, 230)
HEADLIGHT_UV = (1990, 372)                    # slim lens strip near nose (front)
TAIL_UV = (88, 372)
POPUP_UV = [(1640, 246), (1840, 296)]         # closed pop-up headlamp covers (hood)

# reference silhouette (gate R01); R02 uses ref/REF_MASK.png = same drawing, segmented by colour.
SILHOUETTE = [
    [(60, 337), (73, 328), (99, 323), (120, 321), (120, 500), (84, 514), (83, 496), (68, 474), (60, 374)],  # tail
    [(105, 80), (120, 80), (120, 228), (105, 227)],                                                         # wing end plate
    [(120, 80), (206, 88), (209, 92), (222, 92), (229, 104),
    (242, 104), (245, 108), (306, 112), (308, 201), (430, 204), (433, 196), (450, 196), (453, 204),
    (474, 204), (513, 192), (570, 192), (572, 173), (581, 168), (617, 156), (654, 156), (663, 147),
    (665, 112), (714, 104), (733, 88), (782, 84), (797, 76), (822, 76), (825, 72), (894, 72), (897, 68),
    (1074, 72), (1077, 76), (1110, 76), (1121, 84), (1142, 84), (1145, 96), (1158, 96), (1169, 104),
    (1186, 108), (1193, 116), (1202, 116), (1257, 144), (1266, 144), (1402, 212), (1425, 228),
    (1454, 228), (1456, 239), (1469, 244), (1482, 244), (1485, 236), (1558, 236), (1561, 240),
    (1590, 240), (1593, 244), (1630, 244), (1657, 252), (1690, 252), (1693, 256), (1754, 268),
    (1769, 276), (1782, 276), (1817, 292), (1826, 292), (1845, 304), (1854, 304), (1875, 317),
    (1877, 328), (1898, 328), (1901, 336), (1922, 340), (1929, 348), (1958, 360), (1973, 376),
    (1991, 377), (1995, 393), (1995, 418), (1979, 420), (1979, 490), (1971, 492), (1971, 515), (1975, 518), (2011, 522), (2011, 540), (1992, 541), (1965, 546), (1962, 551),
    (201, 551), (198, 531), (130, 523), (120, 519)]]
PART_OUTLINES = {}
