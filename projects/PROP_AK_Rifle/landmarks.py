"""
Reference landmarks for PROP_AK_Rifle, measured on ref/REAL_REFERENCE.png (1440x720).
The original portrait photo (ref/REF_ORIGINAL_vertical.png) was rotated 90 deg clockwise.

All silhouettes/points are PHOTO PIXELS (u right, v down), read on zoomed gridded crops
(ref/crops/*.png). Metres only via P().

Photo analysis:
  * The photo shows the rifle's RIGHT side (muzzle on image right; safety lever and charging
    handle visible) -> reference camera at -X. Right-side-only parts sit at negative X.
  * Scale 1598 px/m: overall length 1406 px (butt heel u=26 -> brake tip u=1432) = 0.880 m (AKM).
    Cross-checks: sight radius 566 px (spec 0.378 m -> 1497 px/m, -6 %, rear notch uncertain),
    gas tube 30 px = 19 mm (plausible). Thin dark edges read small on the blown-out background.
  * Tilt 0: barrel centre line v=295 is level from u=1110 to u=1340.
  * Origin: bore axis above the trigger, px (572, 295) = (Y 0, Z 0). -Y = muzzle, +X = left.
"""
from workbench.refmap import RefMap

ASSET = "PROP_AK_Rifle"
IMAGE_SIZE = (1440, 720)
S = 1598.0
ANCHOR_PX = (572.0, 295.0)
ANCHOR_YZ = (0.0, 0.0)
THETA = 0.0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of


def px(m):
    """metres -> pixels (for radii measured in px)."""
    return m * S


def m(p):
    """pixels -> metres."""
    return p / S


BORE_V = 295.0                      # barrel centre line (level)
MUZZLE_U = 1432.0
BUTT_U = 26.0

# --------------------------------------------------------------------------- half widths (m)
# X is never visible in a side photo: AKM knowledge + generic widths of the studied model.
HW_RECV = 0.0155          # stamped receiver side walls
HW_COVER = 0.0165         # dust cover wraps the receiver
HW_RSIGHT = 0.0120        # rear sight base
HW_LEAF = 0.0070
HW_FSB = 0.0100
HW_GASBLOCK = 0.0110
HW_GRIP = 0.0150
HW_MAG = 0.0128           # AKM ribbed steel mag: ~25.6 mm body, ~27.4 mm over the ribs (spec ~1")
HW_GUARD = 0.0045
HW_TRIGGER = 0.0030
HW_CATCH = 0.0065
HW_HG_LOWER = [(852, 0.0185), (885, 0.0205), (940, 0.0195), (1086, 0.0175)]   # finger swell at rear
HW_HG_UPPER = [(935, 0.0160), (1084, 0.0150)]
HW_STOCK = [(40, 0.0215), (150, 0.0210), (260, 0.0190), (330, 0.0165), (400, 0.0148), (433, 0.0142)]

# --------------------------------------------------------------------------- receiver group
RECV_BODY = [(433, 272), (700, 269), (852, 265), (852, 330), (775, 331), (680, 334),
             (640, 338), (560, 339), (433, 341)]
RECV_END_U = (433, 441)             # rear trunnion / stock ferrule band
# dust cover: top polyline and bottom per station (bottom rises over the ejection port)
COVER_TOP = [(441, 266), (445, 258), (450, 252), (460, 246), (470, 240), (480, 232), (490, 228.5),
             (520, 228), (700, 229), (800, 231)]
COVER_BOT = [(441, 270), (690, 269), (698, 250), (800, 249)]
EJECTION_PORT = [(700, 250), (832, 250), (832, 276), (700, 276)]      # bright carrier visible here
CHARGING_KNOB_PX = (818, 257)
CHARGING_KNOB_R_PX = 7.0
REAR_SIGHT_BASE = [(820, 219), (870, 216), (918, 216), (918, 263), (852, 263), (852, 270), (820, 270)]
REAR_SIGHT_LEAF = [(800, 211), (807, 209), (890, 214), (890, 219), (806, 219), (800, 217)]
REAR_SIGHT_SLIDER_PX = (825, 218)
# right-side controls
SAFETY_PIVOT_PX = (535, 292)
SAFETY_PIVOT_R_PX = 11.5
SAFETY_LEVER = [(526, 298), (533, 305), (697, 274), (702, 262), (692, 261), (545, 283), (530, 288)]
TRIGGER_GUARD = [(548, 338), (548, 384), (552, 389), (558, 392), (634, 392), (640, 388), (642, 377),
                 (638, 377), (636, 385), (632, 388), (559, 388), (554, 385), (552, 381), (552, 338)]
TRIGGER = [(569, 340), (578, 340), (579, 348), (582, 357), (586, 365), (592, 372), (597, 380),
           (592, 381), (584, 374), (577, 366), (573, 357), (570, 348)]
MAG_CATCH = [(638, 336), (668, 336), (668, 379), (662, 380), (657, 398), (654, 398), (647, 380),
             (638, 379)]
MAG_CATCH_PIN_PX = (657, 365)
# rivets / pins on the right receiver wall (px)
RIVETS = [(462, 278), (503, 300), (575, 324), (665, 302), (650, 327), (762, 310), (810, 285),
          (836, 284), (447, 318), (447, 300)]

# --------------------------------------------------------------------------- pistol grip
GRIP = [(446, 341), (548, 341), (546, 352), (540, 388), (535, 395), (525, 412), (515, 435),
        (505, 460), (500, 480), (495, 502), (490, 510), (470, 502), (440, 490), (415, 482),
        (411, 479), (427, 445), (445, 412), (460, 385), (464, 372), (460, 360), (452, 352),
        (447, 347)]

# --------------------------------------------------------------------------- magazine
MAG_REAR = [(678, 333), (686, 380), (697, 430), (708, 462), (720, 493), (735, 520), (753, 547),
            (775, 573), (797, 597), (820, 610), (846, 617)]
MAG_FRONT = [(773, 333), (786, 370), (800, 403), (815, 433), (833, 463), (852, 487), (873, 507),
             (893, 520), (910, 530)]

# magazine v2 (real geometry): spine and front edge are circular arcs fitted to MAG_REAR[:-2] /
# MAG_FRONT (residual <= 2.5 px). Depth along the section = 100 px = 62.6 mm (spec ~64 mm),
# spine arc 218 mm (spec length ~223 mm). Features after Small Arms Review: 0.75 mm sheet,
# 3 outward longitudinal ribs + 1 inward spine rib, 5 short horizontal ribs at the bottom,
# welded lip reinforcement plates, front locking lug, rear catch lug, sliding floorplate.
MAG_REAR_ARC = (1075.7, 315.2, 396.7)     # centre u, centre v, radius (px)
MAG_FRONT_ARC = (1068.0, 280.0, 297.3)
MAG_TOP_V = 318.0                         # spine top, hidden inside the receiver (bottom v~333)
MAG_FLOOR_LINE = [(910, 530), (818, 616)] # outer bottom (front -> rear); lowest point v~617 kept
MAG_FLOOR_T_PX = 4.0                      # floorplate thickness (2.5 mm)
MAG_E_SPINE, MAG_E_FRONT = 5.0, 3.2       # section roundness: flat spine, rounded front
MAG_LIP_FRAC = 0.10
# long ribs: (across-depth fraction 0 = spine .. 1 = front, start t, end t) with t 0 = top .. 1 = floor.
# Layout cross-checked on a studied AK magazine model (layout only): all start under the lip plates,
# the front rib runs furthest down, the rear one stops first; two short ribs parallel to the
# floorplate fill the triangle next to the spine.
MAG_LONG_RIBS = [(0.40, 0.13, 0.74), (0.59, 0.13, 0.81), (0.78, 0.13, 0.88)]
MAG_SHORT_RIBS = [(0.84, 0.07, 0.42), (0.915, 0.07, 0.48)]    # (t, from depth, to depth)
MAG_RIB_R, MAG_RIB_SINK = 0.0022, 0.0010  # 3.9 mm wide, 1.2 mm proud (stamped bead)

# --------------------------------------------------------------------------- barrel group
RECV_FRONT_U = 852
BARREL = [(852, 13.0), (1206, 12.5), (1210, 10.5), (1395, 10.5)]      # (u, radius px)
GAS_BLOCK = [(1190, 243), (1208, 243), (1220, 263), (1230, 273), (1240, 279), (1250, 282),
             (1250, 309), (1206, 309), (1206, 270), (1190, 270)]
BAYONET_LUG = [(1232, 308), (1250, 308), (1250, 318), (1236, 318)]
GAS_TUBE = dict(u0=1084, u1=1200, v=255.0, r=15.0)
GAS_TUBE_RING_U = (1168, 1176)
FSB = [(1346, 282), (1350, 225), (1356, 222), (1360, 219), (1379, 219), (1381, 222), (1386, 281),
       (1390, 284), (1390, 306), (1386, 312), (1378, 318), (1360, 318), (1352, 313), (1348, 306),
       (1346, 300)]
FSB_HOLE_PX = (1366, 268)
FSB_EAR_BASE_V = 284.0              # ears (hood wings) rise above the base block
FSB_EAR_T = 0.0022                  # ear plate thickness (m)
FSB_POST = [(1365, 221), (1367, 219), (1372, 219), (1374, 221), (1374, 285), (1365, 285)]
FSB_HOLE_R_PX = 5.5
BRAKE = dict(collar=(1390, 1400, 12.0), u0=1400, top_end=1418, bot_end=1433, r=11.0, bore=5.0)

# --------------------------------------------------------------------------- wood
HG_LOWER_TOP = [(852, 268), (1086, 270)]
HG_LOWER_BOT = [(852, 326), (870, 331), (890, 331), (930, 321), (980, 318), (1030, 315),
                (1086, 315)]
HG_UPPER_TOP = [(935, 224), (1000, 224), (1060, 226), (1078, 229), (1084, 233)]
HG_UPPER_BOT = [(935, 262), (1084, 259)]
HG_REAR_CAP = [(918, 226), (935, 224), (935, 266), (918, 266)]         # upper handguard retainer
HG_FRONT_BAND = [(1084, 232), (1100, 232), (1100, 322), (1084, 322)]    # handguard retainer band
STOCK_TOP = [(44, 281), (150, 281), (273, 285), (300, 297), (333, 298), (367, 290), (400, 281),
             (433, 273)]
STOCK_BOT = [(38, 437), (100, 428), (160, 420), (267, 387), (333, 363), (400, 347), (433, 340)]
BUTT_PLATE = [(37, 281), (45, 280), (39, 438), (26, 438), (24, 432)]
SLING_SWIVEL_PX = (135, 425)
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
SWIVEL_LOOP = [(118, 430), (140, 438), (160, 444)]

# reference-camera anchors: world points that sit ON the photo plane (x = 0)
ANCHORS = [((0.0, *P(1300, 295)), (1300, 295)), ((0.0, *P(40, 360)), (40, 360)),
           ((0.0, *P(760, 500)), (760, 500))]

MARKS = [(1300, 295), (40, 360), (1369, 219), (818, 257), (535, 292)]
