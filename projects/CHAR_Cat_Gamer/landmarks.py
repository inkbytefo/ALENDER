"""
Reference landmarks for CHAR_Cat_Gamer  (single source of truth for proportions).

Photo: ref/REAL_REFERENCE.png, 1122 x 1402, ONE image (AI-rendered stylised tabby cat, standing,
arms crossed, red headphones, black sleeveless vest). No cheatsheet, no second view.

  view    FRONT (slightly three-quarter): the character faces the camera, so image right = +X
          (the character's LEFT), the photo plane is X/Z and depth is +Y. Names use the
          character's sides: *_R = image LEFT, *_L = image RIGHT.
  scale   no real size is known. ASSUMED total height ~1.00 m (ear tip v=18 .. ground) ->
          S = 1310 px/m. Cross-checks are impossible (stylised character): UNCERTAIN.
  pitch   the two paws differ by 21 px (image-left paw v 1228..1328, image-right 1214..1300) and the
          tops of both paws are visible -> the camera looks slightly DOWN and the character's right
          foot is forward. ASSUMED pitch 12 deg -> foot depth offset 0.078 m. UNCERTAIN.
  anchor  world origin = ground point between the feet, seen at ANCHOR_PX (mean paw centre row
          1267.5 + 0.036 m paw half height).
  depth   every Y value / depth table is a guess (single front photo): see parts.UNCERTAIN.

MEASURED = measured.py (row scans of ref/REF_MASK.png by measure.py); HAND = read from 2x crops
(+-5 px). The mask is measured only where fur meets the background (blue-channel rule, rim-lit
edges are 3-6 px short); the black vest and the red headphones are hand-traced (MASK_DARK_POLYS).
"""
import math
from refmap_front import FrontRefMap
import measured as M

ASSET = "CHAR_Cat_Gamer"
IMAGE_SIZE = (1122, 1402)
S = 1310.0                        # px per metre (ASSUMED height 1.00 m)
ANCHOR_PX = (565.0, 1313.0)       # ground point between the feet (world origin)
PITCH = math.radians(12.0)        # camera looks down (ASSUMED from the paw offset)

REF = FrontRefMap(S, ANCHOR_PX, PITCH, dist=20.0, image_size=IMAGE_SIZE)
P, P3 = REF.P, REF.P3

# reference-camera anchors: [(world xyz, pixel), ...]
ANCHORS = [((0.0, 0.0, 0.0), ANCHOR_PX), (P3(600, 300, 0.0), (600, 300)), (P3(300, 900, 0.1), (300, 900))]


def interp(tab, t):
    if t <= tab[0][0]:
        return tab[0][1]
    for (t0, a), (t1, b) in zip(tab, tab[1:]):
        if t <= t1:
            return a + (b - a) * (t - t0) / float(t1 - t0)
    return tab[-1][1]


def rows_poly(rows):
    """row table [(v, uL, uR)] -> closed px polygon."""
    return [(r[1], r[0]) for r in rows] + [(r[2], r[0]) for r in reversed(rows)]


def stroke_poly(pts, n_arc=5):
    """thick polyline [(u, v, r_px), ...] -> closed px polygon (round ends)."""
    left, right = [], []
    for i, (u, v, r) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        k = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / k, tx / k
        left.append((u + nx * r, v + ny * r))
        right.append((u - nx * r, v - ny * r))

    def cap(c, p_from, p_to):
        a0 = math.atan2(p_from[1] - c[1], p_from[0] - c[0])
        a1 = math.atan2(p_to[1] - c[1], p_to[0] - c[0])
        while a1 < a0:
            a1 += 2 * math.pi
        return [(c[0] + c[2] * math.cos(a0 + (a1 - a0) * j / n_arc), c[1] + c[2] * math.sin(a0 + (a1 - a0) * j / n_arc))
                for j in range(1, n_arc)]
    return left + cap(pts[-1], left[-1], right[-1]) + right[::-1] + cap(pts[0], right[0], left[0])


def ellipse_poly(c, rx, ry, n=20, rot=0.0):
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
    return out


# --- MEASURED row tables (v, u_left, u_right) -----------------------------------------------------
HEAD_ROWS, EAR_R_ROWS, EAR_L_ROWS = M.HEAD, M.EAR_R, M.EAR_L
LEG_R_ROWS, LEG_L_ROWS = M.LEG_R, M.LEG_L
PAW_R_ROWS, PAW_L_ROWS = M.PAW_R, M.PAW_L

# --- depth tables (metres, ALL GUESSED) : (v, value) ---------------------------------------------------
HEAD_DEPTH_C = -0.02
HEAD_DEPTH_HW = [(140, 0.05), (180, 0.10), (240, 0.135), (320, 0.15), (420, 0.15), (470, 0.13), (506, 0.10)]
EAR_R_DEPTH_C, EAR_L_DEPTH_C, EAR_DEPTH_HW = -0.055, 0.06, 0.022     # head yaw: right ear nearer
TORSO_DEPTH_HW = [(505, 0.06), (560, 0.095), (700, 0.105), (900, 0.11), (1000, 0.10), (1050, 0.07)]
LEG_R_DEPTH_C = [(896, 0.0), (1000, -0.015), (1238, -0.02)]
LEG_L_DEPTH_C = [(896, 0.0), (1000, 0.035), (1226, 0.05)]
LEG_DEPTH_HW = [(896, 0.075), (1050, 0.065), (1238, 0.052)]

# --- HAND: torso under the vest (hidden by arms / vest between v 560 and 790) -------------------------
VEST_ROWS = [(495, 398, 662), (520, 390, 692), (548, 370, 703), (580, 362, 712), (640, 372, 728),
             (700, 385, 738), (790, 400, 722), (850, 386, 734), (880, 378, 742), (905, 380, 744)]
VEST_GAP = [(495, 470, 640), (520, 480, 622), (560, 530, 610), (600, 581, 589), (780, 581, 589),
            (800, 574, 642), (850, 560, 665), (905, 548, 690)]            # (v, u_gap_left, u_gap_right)
VEST_INSET_PX = 7                                                         # torso = vest outline - inset
TORSO_ROWS = ([(v, a + VEST_INSET_PX, b - VEST_INSET_PX) for (v, a, b) in VEST_ROWS if v >= 520] +
              [(960, 380, 745), (1000, 385, 742), (1030, 420, 715), (1050, 470, 670)])
TORSO_ROWS[0] = (505, 470, 650)                                           # neck

# --- HAND: arms / tail centre lines (u, v, depth m, radius px) ----------------------------------------
ARM_R = [(400, 578, 0.00, 44), (397, 650, -0.03, 44), (420, 738, -0.07, 44), (470, 765, -0.135, 44),
         (560, 765, -0.15, 42), (640, 762, -0.14, 40), (700, 765, -0.11, 36)]
ARM_L = [(685, 595, 0.00, 38), (708, 665, -0.03, 42), (731, 754, -0.08, 44), (700, 715, -0.15, 42),
         (650, 685, -0.18, 40), (580, 660, -0.19, 38), (540, 652, -0.19, 36)]
HAND_L = dict(c=(515, 650), d=-0.19, rx=50, rz=40, ry=0.035)              # white paw resting on the right arm
WRISTBAND = [(672, 694, -0.176, 47), (632, 677, -0.184, 47)]
TAIL = [(700, 1000, 0.10, 34), (760, 1026, 0.14, 34), (830, 1038, 0.17, 38), (895, 1040, 0.18, 44),
        (950, 1005, 0.18, 56), (972, 945, 0.18, 61), (970, 875, 0.18, 62), (960, 812, 0.18, 62),
        (935, 765, 0.18, 52)]
TAIL_TIP = [(935, 765, 0.18, 52), (900, 752, 0.18, 46), (865, 768, 0.18, 40), (848, 790, 0.18, 28)]

# --- HAND: paws (ellipsoids on the ground; world metres from px centres) -------------------------------
PAW_R = dict(u=375, y=-0.039, rx=0.074, ry=0.065, rz=0.036)
PAW_L = dict(u=741, y=0.039, rx=0.080, ry=0.065, rz=0.036)

# --- HAND: face ---------------------------------------------------------------------------------------
EYE_R = dict(c=(518, 318), rx=50, rz=42, iris=36, pupil=20)
EYE_L = dict(c=(688, 368), rx=45, rz=38, iris=33, pupil=18)
NOSE = dict(c=(605, 380), rx=17, rz=11)
MUZZLE = dict(c=(605, 418), rx=78, rz=44)

# --- HAND: headphones -----------------------------------------------------------------------------------
HEAD_YAW = math.radians(28.0)      # head turned to its left: the right cup shows its outer face
CUP_R = dict(inner=(377, 329), d=-0.075, r=0.0725)        # contact point on the head side (px, depth)
CUP_L = dict(inner=(700, 395), d=0.075, r=0.0725)
CUP_THICK, CUSHION_THICK = 0.042, 0.020
BAND = [(342, 245, -0.04, 22), (360, 188, -0.02, 22), (428, 142, 0.0, 24), (520, 127, 0.03, 26),
        (610, 124, 0.05, 26), (700, 148, 0.08, 26), (762, 200, 0.105, 22), (786, 285, 0.11, 22)]   # behind the ears

# --- photo mask helpers (make_mask.py) ------------------------------------------------------------------
MASK_FLOOR_V = 1332
MASK_DARK_POLYS = [               # HAND: dark / red parts that the fur rule cannot see
    [(402, 770), (570, 785), (548, 908), (378, 892), (386, 850), (397, 800)],          # vest lower R panel
    [(640, 790), (715, 795), (730, 840), (742, 882), (692, 912)],                      # vest lower L panel
    [(396, 492), (450, 512), (560, 580), (560, 640), (470, 600), (440, 560), (372, 548), (396, 520)],  # collar R
    [(600, 520), (668, 515), (700, 540), (705, 575), (725, 640), (600, 650), (570, 580)],  # collar L
    [(262, 330), (268, 280), (285, 250), (310, 238), (345, 240), (372, 250), (378, 300), (378, 380),
     (365, 420), (335, 438), (300, 430), (275, 400), (264, 365)],                      # headphone cup R
    [(760, 300), (785, 290), (805, 320), (815, 370), (815, 420), (800, 465), (775, 495), (750, 490),
     (745, 450), (760, 400)],                                                          # headphone cup L
    [(325, 240), (338, 195), (362, 160), (372, 175), (350, 215), (345, 245)],          # band, R end
    [(520, 108), (560, 98), (620, 97), (680, 112), (725, 140), (735, 160), (700, 165), (660, 175),
     (600, 140), (540, 150), (515, 120)],                                              # band, top
    [(895, 790), (960, 790), (960, 870), (905, 870)],                                  # tail dark stripes
    [(912, 900), (1000, 905), (1000, 960), (905, 960)],
    [(885, 990), (950, 990), (940, 1085), (885, 1085)],
    [(396, 492), (470, 480), (560, 505), (560, 580), (450, 512)],                      # neck shadow inside the collar
    [(600, 505), (690, 500), (705, 540), (668, 515)],
    [(353, 640), (400, 640), (432, 776), (398, 768), (362, 722)],                      # rim-lit dark stripes: R arm
    [(357, 1020), (415, 1030), (415, 1065), (357, 1065)], [(352, 1120), (395, 1125), (395, 1155), (352, 1150)],  # R leg
]
MASK_EXCLUDE_POLYS = [[(630, 1300), (900, 1297), (900, 1340), (630, 1340)]]           # floor reflection
CUP_R_OUTLINE, CUP_L_OUTLINE = MASK_DARK_POLYS[4], MASK_DARK_POLYS[5]


def _uvr(pts):
    return [(u, v, r) for (u, v, _d, r) in pts]


MARKS = [ANCHOR_PX, EYE_R["c"], EYE_L["c"], NOSE["c"]]

# reference silhouette (gate R01): union of the part outlines as seen in the photo
PART_OUTLINES = {
    "HEAD_Skull": rows_poly(HEAD_ROWS), "HEAD_Ear_R": rows_poly(EAR_R_ROWS), "HEAD_Ear_L": rows_poly(EAR_L_ROWS),
    "LEG_Upper_R": rows_poly(LEG_R_ROWS), "LEG_Upper_L": rows_poly(LEG_L_ROWS),
    "LEG_Paw_R": rows_poly(PAW_R_ROWS), "LEG_Paw_L": rows_poly(PAW_L_ROWS),
}
SILHOUETTE = list(PART_OUTLINES.values()) + [
    rows_poly(VEST_ROWS), rows_poly(TORSO_ROWS),
    stroke_poly(_uvr(ARM_R)), stroke_poly(_uvr(ARM_L)), ellipse_poly(HAND_L["c"], HAND_L["rx"], HAND_L["rz"]),
    stroke_poly(_uvr(TAIL)), stroke_poly(_uvr(TAIL_TIP)), stroke_poly(_uvr(BAND)),
    CUP_R_OUTLINE, CUP_L_OUTLINE,
]
