"""
Reference landmarks for PROP_AK_Rifle, measured on ref/REAL_REFERENCE.png (1440x720).
The original portrait photo (ref/REF_ORIGINAL_vertical.png) was rotated 90 deg clockwise.

All silhouettes/points are PHOTO PIXELS (u right, v down), read on zoomed gridded crops
(ref/crops/*.png). Metres only via P().

Photo analysis:
  * The photo shows the rifle's RIGHT side (muzzle on image right; safety lever and charging
    handle visible) -> reference camera at -X. Right-side-only parts sit at negative X.
  * Scale / perspective: see the ObliqueRefMap block below (the photo is NOT a parallel side view).
  * Origin: bore axis above the trigger, px (572, 295) = (Y 0, Z 0). -Y = muzzle, +X = left.
"""
import math

from workbench.refmap import ObliqueRefMap

ASSET = "PROP_AK_Rifle"
IMAGE_SIZE = (1440, 720)
# Perspective of the photo (2026-10-02): the rifle stood leaning away from the camera, so the butt is
# drawn ~16 % longer / 7 % taller than the muzzle end. Pinhole + yaw fitted to 5 longitudinal stations
# of the factory side section (ref/REF_SECTION_akm_manual.png, AKM repair manual 1968, fig. 115):
# butt, receiver rear, handguard front, gas block front, front sight post -> residuals <= 1.4 mm,
# overall length 0.880 m (AKM spec); the bore line (v 292.8 @u1150, 295 @u1300, 296 @u1400) is level.
# Only the in-plane homography is observable from stations. The camera position (which faces of thick
# parts are visible) comes from parallax evidence: the handguard band (u 1090) and the front sight are
# not thickened -> seen square-on; the buttplate shows its back face -> seen ~16 deg from behind
# (its silhouette overhangs the mid-plane butt end by ~9 px: REF.thickness_px, used by the builders).
# That puts the camera ~3 m away with the principal point right of the frame (cropped photo).
# Cross-checks: front sight post tip (~5 px below the ear tops) 48.5 mm above the bore (spec 48.5),
# sight radius 364 mm (spec 378, rear notch position uncertain). Vertical scale uncertainty ~ +-4 %.
F_PX, YAW, DIST = 4299.7566, 0.1816271, 3.0
PRINCIPAL = (2200.0, 616.1766)
BORE_PX = (1300.0, 295.0)                # a measured point of the bore axis (Z = 0)
ANCHOR_PX = (572.0, 295.0)               # bore axis above the trigger = world origin (Y 0)
_r = ObliqueRefMap(IMAGE_SIZE, F_PX, YAW, DIST, 0.0, BORE_PX, (0.0, 0.0), principal=PRINCIPAL)
REF = ObliqueRefMap(IMAGE_SIZE, F_PX, YAW, DIST, 0.0, BORE_PX, (-_r.P(*ANCHOR_PX)[0], 0.0),
                    front_is_right=True, principal=PRINCIPAL)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of


def m(p, u):
    """pixels -> metres at photo column u (the photo scale changes along the rifle)."""
    return p / REF.scale_at(u)


BORE_V = 295.0                      # barrel centre line (level)
MUZZLE_U = 1432.0
BUTT_U = 26.0

# --------------------------------------------------------------------------- half widths (m)
# X is never visible in a side photo: AKM knowledge + generic widths of the studied model.
HW_RECV = 0.0160          # stamped receiver, 32 mm outside (stock tenon 28 mm, manual fig. 21)
HW_COVER = 0.0178         # dust cover: 34 mm inside (cover mandrel, manual fig. 47) + sheet
HW_TRUNNION = HW_RECV + 0.0008      # rear trunnion / stock ferrule band stands proud of the walls
HW_RSIGHT = 0.0120        # rear sight base
HW_LEAF = 0.0070
HW_FSB = 0.0100
HW_GASBLOCK = 0.0110
HW_GRIP = 0.0150
# magazine mandrel (manual fig. 51): cavity 55 mm deep, 21 mm wide at the spine, 16 mm at the front
HW_MAG = 0.01125          # body 22.5 mm at the spine (+ ribs 1.2 mm each side = 24.9 mm, spec ~1")
MAG_FRONT_TAPER = 17.5 / 22.5       # body width at the front edge / at the spine
HW_GUARD = 0.0045
HW_TRIGGER = 0.0030
HW_CATCH = 0.0065
HW_HG_CAP = 0.0150         # upper handguard retainer
HW_HG_BAND = 0.0195        # front handguard retainer band
HW_HG_RETAINER = 0.0110
HW_LUG = 0.0040           # bayonet lug
HW_FSB_POST = 0.0012
HW_HG_LOWER = [(852, 0.0185), (885, 0.0205), (940, 0.0195), (1086, 0.0175)]   # finger swell at rear
HW_HG_UPPER = [(935, 0.0160), (1084, 0.0150)]
# butt 40 mm / mid 35 mm wide: top view of ref/REF_FOURVIEW_ak47_type3.png (0.99 mm/px); wrist = tenon 28 mm
HW_STOCK = [(40, 0.0200), (150, 0.0195), (260, 0.0180), (330, 0.0162), (400, 0.0148), (433, 0.0142)]

# --------------------------------------------------------------------------- receiver group
RECV_BODY = [(433, 272), (700, 269), (852, 265), (852, 330), (845, 331), (832, 334), (784, 336), (775, 335),
             (680, 334), (640, 338), (560, 339), (433, 341)]      # bottom front measured (cols 784-844)
RECV_TRUNNION = [(433, 270), (441, 270), (441, 342), (433, 342)]     # rear trunnion / stock ferrule band
# left wall above the port level (the ejection port exists only on the right side)
RECV_WALL_LEFT = [(698, 249), (832, 249), (832, 268), (698, 270)]
COVER_U = (441, 800)
# dust cover: top polyline and bottom per station (bottom rises over the ejection port)
# v2: measured on ref/REF_MASK.png (wb.py profile 441 800 215 272 --side top); v1 was up to 4 px high.
COVER_TOP = [(441, 266), (446, 258), (451, 251), (461, 248), (481, 230), (491, 228), (541, 228),
             (591, 229), (655, 232), (730, 232), (798, 235)]
COVER_BOT = [(441, 274), (690, 273), (698, 250), (800, 249)]     # rear overlaps the receiver top (no gap in the photo)
EJECTION_PORT = [(700, 250), (832, 250), (832, 276), (700, 276)]      # bright carrier visible here
CHARGING_KNOB_PX = (818, 257)
CHARGING_KNOB_R_PX = 7.0
# handle revolved about X: (radius m, x m) from the receiver wall to the knob tip
CHARGING_HANDLE = [(0.0033, -HW_RECV), (0.0033, -0.033), (0.0046, -0.0355), (0.0050, -0.041),
                   (0.0042, -0.0455), (0.0018, -0.0472)]
# measured on REF_MASK (measure.py): base top 217-218 from u 812, leaf lies flush, hump at u 870-892
REAR_SIGHT_BASE = [(812, 218), (870, 217), (918, 217), (918, 268), (812, 270)]
REAR_SIGHT_LEAF = [(808, 215), (870, 216), (878, 214), (884, 213), (891, 215), (895, 218), (895, 221),
                   (808, 221)]
REAR_SIGHT_SLIDER_PX = (825, 218)
REAR_SIGHT_SLIDER_SIZE = (2 * HW_LEAF + 0.004, 0.009, 0.006)       # m (x, y, z), sits 0.5 mm high
REAR_SIGHT_POST = [(801, 212), (803, 210), (809, 210), (813, 213), (813, 246), (801, 246)]   # rear upright of the leaf
# right-side controls
SAFETY_PIVOT_PX = (535, 292)
SAFETY_PIVOT_R_PX = 11.5
SAFETY_LEVER = [(526, 298), (533, 305), (697, 274), (702, 262), (692, 261), (545, 283), (530, 288)]
# measured on REF_MASK (measure.py): bottom bar v 388-394
TRIGGER_GUARD = [(548, 338), (548, 384), (552, 390), (560, 394), (632, 393), (640, 389), (642, 377),
                 (638, 377), (636, 384), (631, 387), (561, 388), (555, 385), (552, 381), (552, 338)]
# measured on REF_MASK (measure.py): web behind the blade at the top, hooked blade, tip (596, 381)
TRIGGER = [(555, 341), (580, 341), (580, 349), (578, 357), (580, 365), (586, 372), (593, 377), (596, 381),
           (591, 381), (584, 378), (578, 375), (574, 369), (571, 356), (568, 352), (562, 349), (556, 344)]
MAG_CATCH = [(638, 336), (668, 336), (668, 362), (666, 377), (662, 382), (659, 398), (656, 398), (650, 384),
             (638, 382)]
MAG_CATCH_PIN_PX = (657, 365)
TRIGGER_PIVOT_PX = (574, 332)
# rivets / pins on the right receiver wall (px)
RIVETS = [(462, 278), (503, 300), (575, 324), (665, 302), (650, 327), (762, 310), (810, 285),
          (836, 284), (447, 318), (447, 300)]
RIVET_R, RIVET_H = 0.0023, 0.0010
STOCK_SCREW_PX = (413, 295)

# --------------------------------------------------------------------------- pistol grip
# measured on REF_MASK (measure.py) rows 342-514): back strap, front edge, shelf under the guard, bottom line
GRIP = [(436, 341), (548, 341), (548, 388), (555, 393), (531, 398), (524, 414), (517, 430), (510, 446),
        (503, 462), (496, 478), (490, 496), (491, 510), (486, 514), (475, 510), (460, 502), (438, 494),
        (418, 486), (411, 479), (424, 454), (437, 430), (445, 414), (454, 398), (459, 390), (463, 382),
        (465, 374), (464, 366), (459, 358), (452, 350), (438, 348)]

# the two long edges of the outline, top -> bottom (loft rails, starting inside the receiver);
# the shelf under the guard is left out
GRIP_BACK = [(437, 335), (438, 343), (452, 350), (459, 358), (464, 366), (465, 374), (463, 382), (459, 390), (454, 398),
             (445, 414), (437, 430), (424, 454), (410, 481)]
GRIP_FRONT = [(548, 335), (548, 386), (531, 398), (524, 414), (517, 430), (510, 446), (503, 462), (496, 478),
              (490, 496), (490, 514)]
HW_GRIP_T = [(0.0, 0.0150), (0.35, 0.0155), (1.0, 0.0138)]      # half width top -> bottom (fraction)
GRIP_E_BACK, GRIP_E_FRONT = 2.8, 3.4                           # rounder back strap, flatter front

# --------------------------------------------------------------------------- magazine
# v3: MEASURED on the photo (50 % rule, darkest channel < 150, one sample every 24 rows) instead of
# read by eye. The eye-read v2 spine drifted up to 26 px outward near the bottom (gate R02 wedge).
MAG_REAR = [(669, 338), (673, 362), (680, 386), (687, 410), (697, 434), (708, 458), (721, 482),
            (736, 506), (754, 530), (775, 554), (800, 578), (830, 602), (851, 617), (859, 618)]
MAG_FRONT = [(774, 338), (779, 362), (787, 386), (798, 410), (812, 434), (829, 458), (850, 482),
             (876, 506), (907, 531)]

# magazine (real geometry): spine and front edge are circular arcs, least-squares fitted to the
# measured edges (v3: rear residual max 1.3 px / mean 0.3 px, front 0.7 / 0.2 px; the eye-fitted v2
# arcs were off by up to 19 / 3.8 px on the photo). Features after Small Arms Review: 0.75 mm sheet,
# 3 outward longitudinal ribs + 1 inward spine rib, 5 short horizontal ribs at the bottom,
# welded lip reinforcement plates, front locking lug, rear catch lug, sliding floorplate.
MAG_REAR_ARC = (1073.8, 272.3, 410.4)     # centre u, centre v, radius (px)
MAG_FRONT_ARC = (1066.1, 273.0, 300.8)
MAG_TOP_V = 318.0                         # spine top, hidden inside the receiver (bottom v~333)
# outer bottom (front -> rear). v2 measured on the photo (wb.py profile 812 912 480 630 --photo-thr 150):
# lowest point (852, 617); v1 had the rear end at (818, 616) -> floorplate rotated, 20 px wedge in R02.
MAG_FLOOR_LINE = [(907, 531), (859, 618)]   # measured right edge rows 528-608, lowest point v 617
MAG_FLOOR_T_PX = 4.0                      # floorplate thickness (2.5 mm)
MAG_E_SPINE, MAG_E_FRONT = 5.0, 3.2       # section roundness: flat spine, rounded front
MAG_LIP_FRAC = 0.10
MAG_PIVOT_PX = (778, 331)                 # the magazine rocks in around the front locking lug
# long ribs: (across-depth fraction 0 = spine .. 1 = front, start t, end t) with t 0 = top .. 1 = floor.
# Layout cross-checked on a studied AK magazine model (layout only): all start under the lip plates,
# the front rib runs furthest down, the rear one stops first; two short ribs parallel to the
# floorplate fill the triangle next to the spine.
MAG_LONG_RIBS = [(0.40, 0.13, 0.74), (0.59, 0.13, 0.81), (0.78, 0.13, 0.88)]
MAG_SHORT_RIBS = [(0.84, 0.07, 0.42), (0.915, 0.07, 0.48)]    # (t, from depth, to depth)
MAG_RIB_R, MAG_RIB_SINK = 0.0022, 0.0010  # 3.9 mm wide, 1.2 mm proud (stamped bead)

# --------------------------------------------------------------------------- barrel group
RECV_FRONT_U = 852
BARREL = [(852, 13.0), (1100, 11.5), (1206, 11.5), (1210, 10.0), (1395, 10.0)]      # (u, radius px), measured
GAS_BLOCK = [(1190, 244), (1207, 244), (1217, 261), (1229, 273), (1241, 279), (1250, 283),
             (1250, 307), (1206, 307), (1206, 271), (1190, 271)]
BAYONET_LUG = [(1231, 306), (1251, 306), (1250, 309), (1247, 313), (1241, 315), (1236, 319), (1232, 318)]
GAS_TUBE = dict(u0=918, u1=1206, um=1150, v=256.5, r=14.0)     # runs under the upper handguard from the rear cap
GAS_TUBE_RING_U = (1168, 1176)
# measured on REF_MASK (measure.py) rows 219-318)
FSB = [(1344, 284), (1345, 278), (1346, 266), (1348, 252), (1349, 231), (1354, 224), (1360, 222), (1363, 219),
       (1373, 219), (1377, 221), (1378, 238), (1380, 252), (1382, 266), (1384, 278), (1387, 281), (1391, 284),
       (1391, 306), (1388, 310), (1388, 314), (1385, 316), (1380, 318), (1362, 318), (1359, 316), (1357, 314),
       (1355, 310), (1348, 308), (1345, 304)]
FSB_HOLE_PX = (1366, 268)
FSB_EAR_BASE_V = 284.0              # ears (hood wings) rise above the base block
FSB_EAR_T = 0.0022                  # ear plate thickness (m)
FSB_EAR_FOOT_U = (1345, 1389)       # ear foot, 2 px below the ear base
FSB_POST = [(1365, 221), (1367, 219), (1372, 219), (1374, 221), (1374, 285), (1365, 285)]
FSB_HOLE_R_PX = 5.5
# slant brake: tube r 10 px; front cut (v, u) is kinked in the photo: near-vertical upper face, long lower lip
BRAKE = dict(collar=(1390, 1400, 10.8), u0=1400, r=10.0, bore=5.0,
             front=[(285, 1410), (289, 1412), (296, 1416), (299, 1422), (303, 1432), (305, 1434)])

# --------------------------------------------------------------------------- wood
HG_LOWER_TOP = [(852, 268), (1086, 270)]
# v2: measured with the 50 % rule (python wb.py profile PROP_AK_Rifle 852 1086 300 345 --photo-thr 150);
# the eye-read v1 [(852,326) ... (1030,315),(1086,315)] sat on the lacquer highlight, 3-8 px too high.
HG_LOWER_BOT = [(852, 328), (866, 336), (890, 333), (930, 327), (980, 324), (1030, 322),
                (1086, 321)]
HG_UPPER_TOP = [(935, 227), (960, 227.5), (1000, 229), (1024, 230), (1048, 231), (1072, 233), (1084, 235)]   # measured
HG_UPPER_BOT = [(935, 262), (1084, 259)]
HG_REAR_CAP = [(918, 228), (926, 226), (935, 225), (935, 266), (918, 266)]         # upper handguard retainer
# retainer bridging gas tube and barrel right in front of the band (solid in the photo, u 1097-1110)
HG_RETAINER = [(1097, 240), (1110, 241), (1110, 304), (1101, 306), (1097, 315)]
HG_FRONT_BAND = [(1085, 232), (1093, 232), (1097, 238), (1097, 321), (1094, 323), (1085, 324)]    # handguard retainer band
STOCK_TOP = [(43, 281), (62, 279), (95, 278), (150, 279), (216, 280), (260, 282), (282, 286), (304, 295),
             (326, 298), (348, 294), (370, 288), (392, 281), (414, 276), (433, 274)]     # measured (cols 40-436)
# v2: measured on ref/REF_MASK.png (wb.py profile 38 433 330 448 --side bottom); v1 belly was 4-7 px
# inside the photo edge. u 100-191 interpolated (the sling swivel hangs below the edge there).
STOCK_BOT = [(38, 438), (70, 436), (100, 428), (130, 421), (160, 414), (191, 407), (256, 389), (288, 383),
             (328, 372), (352, 363), (425, 344), (433, 341)]
BUTT_PLATE = [(37, 281), (45, 280), (39, 438), (26, 438), (24, 432)]
# buttstock v2 (AKM laminate: straight top + shallow comb dip, slab sides, steel buttplate with
# horizontal ribs, cleaning-kit trapdoor, 2 screws; sling swivel on the belly)
STOCK_BUTT_U = (43, 32)                   # wood rear end (buttplate back face = photo u 37/26)
STOCK_FRONT_U = 433
STOCK_E_TOP, STOCK_E_BOT = 3.4, 3.0
BUTTPLATE_T = 0.0035                      # behind the wood
BUTTPLATE_WRAP = 0.0040                   # wraps forward onto the wood (dark 6 px band in photo)
BUTTPLATE_RIBS = 11
TRAPDOOR_AT, TRAPDOOR_R = -0.05, 0.0095   # centre (fraction of half height, + = up), radius m
SWIVEL_BASE = [(106, 428), (130, 425)]
SWIVEL_LOOP = [(128, 430), (146, 435.5), (164, 442.5)]

# reference-camera anchors: world points that sit ON the photo plane (x = 0)
ANCHORS = [((0.0, *P(1300, 295)), (1300, 295)), ((0.0, *P(40, 360)), (40, 360)),
           ((0.0, *P(760, 500)), (760, 500))]

MARKS = [(1300, 295), (40, 360), (1369, 219), (818, 257), (535, 292)]


# --------------------------------------------------------------------------- silhouette (gate R01)
# The measured outlines above, as closed px polygons. Their union is the reference silhouette the
# reference-camera render is scored against (IoU + boundary distance). Photo truth = ref/REF_MASK.png
# (python wb.py mask PROP_AK_Rifle --fill 760,258 745,262 45,408 -> gate R02).
def _band(u0, u1, v, r):
    return [(u0, v - r), (u1, v - r), (u1, v + r), (u0, v + r)]


def _circle(c, r, n=12):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


_B = BRAKE
SILHOUETTE = [
    RECV_BODY, COVER_TOP + COVER_BOT[::-1], REAR_SIGHT_BASE, REAR_SIGHT_LEAF, REAR_SIGHT_POST, EJECTION_PORT,
    RECV_TRUNNION,
    STOCK_TOP + STOCK_BOT[::-1], BUTT_PLATE, GRIP, MAG_REAR + MAG_FRONT[::-1],
    [(u, BORE_V - r) for (u, r) in BARREL] + [(u, BORE_V + r) for (u, r) in BARREL[::-1]],
    GAS_BLOCK, BAYONET_LUG, _band(GAS_TUBE["u0"], GAS_TUBE["u1"], GAS_TUBE["v"], GAS_TUBE["r"]), FSB, FSB_POST,
    _band(_B["collar"][0], _B["collar"][1], BORE_V, _B["collar"][2]),
    [(_B["u0"], BORE_V - _B["r"])] + [(u, v) for (v, u) in _B["front"]] + [(_B["u0"], BORE_V + _B["r"])],
    HG_LOWER_TOP + HG_LOWER_BOT[::-1], HG_UPPER_TOP + HG_UPPER_BOT[::-1], HG_REAR_CAP, HG_FRONT_BAND, HG_RETAINER,
    TRIGGER_GUARD, TRIGGER, MAG_CATCH, SAFETY_LEVER, _circle(SAFETY_PIVOT_PX, SAFETY_PIVOT_R_PX),
    _circle(CHARGING_KNOB_PX, CHARGING_KNOB_R_PX),
]
