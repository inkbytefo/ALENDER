"""
Reference landmarks for VEH_Gemini_Motorcycle, measured on REAL_REFERENCE.png (1080x720).

All silhouette/placement data is stored in PHOTO PIXELS (u right, v down) so every
number can be traced back to the photograph. `P(u, v)` converts to the model's
rest-pose (Y, Z) in metres.

Photo analysis (see report.json / task.md):
  * Photo shows the bike's RIGHT side (front at image right) -> reference camera at -X.
  * Scale: 400 px/m, derived from tyre sizes (rear 180/55-17 ~0.63 m = 250 px,
    front 120/70-17 ~0.60 m = 240 px). Cross-checks: overall length 820 px = 2.05 m,
    height 418 px = 1.045 m (cheatsheet: ~2050 / ~1050 mm).
  * The rear wheel sits on a paddock stand: rear axle is ~65 mm higher than the
    front in the photo, but only ~15 mm higher at rest (bigger rear tyre).
    => photo is pitched nose-down by THETA ~2.0 deg. P() removes that pitch.

Coordinate convention (docs/02_STANDARDS.md): +Z up, -Y forward, X = width (+X = bike's LEFT).
Root origin: midway between the axles, ground level.
"""
import math
from workbench.refmap import RefMap, pitch_from_two_points

ASSET = "VEH_Gemini_Motorcycle"
S = 400.0                       # px per metre
FRONT_AXLE_PX = (853.0, 496.0)
REAR_AXLE_PX = (276.0, 470.0)
R_TYRE_F = 0.300                # 120/70-17
R_TYRE_R = 0.315                # 180/55-17
W_TYRE_F = 0.120
W_TYRE_R = 0.180

# --- pitch removal: rear axle sits R_TYRE_R - R_TYRE_F higher than the front at rest ---------
THETA, WHEELBASE = pitch_from_two_points(FRONT_AXLE_PX, REAR_AXLE_PX, R_TYRE_R - R_TYRE_F, S)
REF = RefMap(S, FRONT_AXLE_PX, (-WHEELBASE / 2.0, R_TYRE_F), THETA, front_is_right=True,
             image_size=(1080, 720))
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

FRONT_AXLE = (0.0, -WHEELBASE / 2.0, R_TYRE_F)
REAR_AXLE = (0.0, WHEELBASE / 2.0, R_TYRE_R)

# --- front geometry (rest pose) ---------------------------------------------
# Fork line measured through front axle and top clamp (762,238): ~21.4 deg at rest.
RAKE_DEG = 22.0
FORK_TOP_PX = (762.0, 238.0)
FORK_OFFSET = 0.035             # steering axis sits this far behind fork plane
FORK_SPACING = 0.105            # half distance between fork tube centres
HEADLIGHT_PX = (790.0, 276.0)   # housing centre; front rim edge-on at u~815
HEADLIGHT_R = 0.075
GRIP_INNER_PX = (760.0, 244.0)  # clip-on at clamp
GRIP_END_PX = (722.0, 262.0)    # bar end
RESERVOIR_R_PX = (760.0, 200.0) # front brake master (right, -X)
RESERVOIR_L_PX = (741.0, 212.0) # clutch (left, +X)

# --- rear geometry -------------------------------------------------------------
SWINGARM_PIVOT_PX = (495.0, 472.0)
SWINGARM_TOP_V = 461.0          # top edge nearly level in photo
SWINGARM_BOT_V = 491.0
SHOCK_BOTTOM_PX = (478.0, 458.0)   # UNCERTAIN: red spring seen at (475-500, 428-458)
SHOCK_TOP_PX = (506.0, 404.0)

# --- body silhouettes (px) ---------------------------------------------------
TANK_TOP = [(492, 293), (498, 280), (506, 268), (516, 257), (530, 249), (548, 244),
            (575, 242), (620, 241), (680, 240), (706, 241), (726, 245), (740, 252),
            (749, 262), (754, 278), (756, 300), (756, 318), (753, 334)]
TANK_BOTTOM = [(492, 296), (520, 302), (560, 310), (600, 318), (650, 327),
               (700, 334), (740, 338), (753, 336)]
TANK_HALF_WIDTH = [(492, 0.080), (520, 0.125), (560, 0.155), (620, 0.170),
                   (690, 0.172), (735, 0.160), (756, 0.120)]

SEAT_TOP = [(405, 268), (412, 276), (440, 281), (470, 287), (500, 292)]
SEAT_BOTTOM_V = [(405, 292), (440, 296), (470, 298), (500, 300)]
SEAT_HALF_WIDTH = [(405, 0.105), (450, 0.125), (500, 0.13)]

HUMP_TOP = [(333, 257), (338, 254), (396, 253), (401, 256), (406, 266), (410, 276)]
HUMP_BOTTOM_V = [(333, 272), (370, 276), (410, 282)]
HUMP_HALF_WIDTH = [(333, 0.085), (410, 0.105)]

TAIL_TOP = [(303, 270), (320, 269), (345, 272), (380, 282), (410, 290), (440, 292), (495, 296)]
TAIL_BOTTOM = [(303, 273), (320, 277), (345, 282), (372, 290), (395, 298), (440, 301), (495, 304)]
TAIL_HALF_WIDTH = [(303, 0.050), (340, 0.075), (400, 0.100), (495, 0.120)]

TAILLIGHT_POLY = [(305, 262), (334, 256), (336, 268), (309, 268)]

# black side panel / subframe cover (both sides), photo outline
SIDEPANEL_POLY = [(398, 299), (496, 303), (538, 342), (512, 398), (478, 404), (440, 355)]

# --- engine (px) ---------------------------------------------------------------
CRANKCASE_POLY = [(535, 421), (620, 418), (700, 438), (705, 520), (690, 542),
                  (535, 545)]
TRANSMISSION_POLY = [(512, 426), (540, 421), (540, 545), (522, 545), (512, 530)]
CYL_POLY = [(612, 428), (712, 442), (741, 350), (636, 338)]   # block + head, tilted fwd
CAMCOVER_POLY = [(632, 344), (744, 356), (748, 342), (640, 332)]
ALT_COVER_PX = (575.0, 480.0); ALT_COVER_R = 55.0
SMALL_COVER_PX = (648.0, 482.0); SMALL_COVER_R = 31.0
AIRBOX_POLY = [(505, 306), (560, 314), (640, 328), (636, 346), (560, 362), (515, 365), (503, 340)]  # UNCERTAIN
CARB_BOX = (532, 355, 620, 402)       # u0, v0, u1, v1
INTAKE_BOX = (490, 358, 540, 386)

# --- exhaust (px centreline) ----------------------------------------------------
HEADER_PATH = [(733, 398), (748, 412), (756, 440), (755, 475), (744, 506),
               (722, 532), (692, 546), (650, 550)]
MIDPIPE_PATH = [(650, 550), (600, 551), (540, 550), (492, 546)]
MUFFLER_FRONT_PX = (490.0, 540.0)
MUFFLER_REAR_PX = (402.0, 527.0)
MUFFLER_R = 0.048

# --- frame (px centrelines) ------------------------------------------------------
FRAME_BACKBONE = [(778, 296), (730, 312), (660, 322), (590, 330), (530, 338), (505, 360)]
FRAME_REAR_DOWN = [(505, 360), (500, 410), (497, 470), (500, 505)]
FRAME_DOWNTUBE = [(786, 330), (776, 360), (764, 385)]          # UNCERTAIN: head -> cyl-head mount
FRAME_SUB_UPPER = [(312, 274), (345, 281), (395, 297), (440, 300), (500, 303), (530, 336)]
FRAME_SUB_LOWER = [(400, 300), (440, 352), (478, 398), (500, 410)]
PIVOT_PLATE_POLY = [(478, 395), (528, 392), (532, 500), (500, 512), (476, 500)]

FOOTPEG_PX = (446.0, 425.0)
REARSET_PLATE_POLY = [(430, 410), (462, 404), (470, 440), (440, 446)]

# --- tank paint / knee recess (Stage 2) --------------------------------------------
# Red upper shell overhangs a black recessed knee flank; below this line (and u < 662)
# the tank side is black and set inward.
TANK_BLACK_BOUNDARY = [(488, 290), (495, 276), (505, 266), (520, 259), (540, 258), (560, 262),
                       (590, 268), (620, 276), (640, 285), (655, 295), (662, 306), (664, 340)]
TANK_BLACK_U_MAX = 662.0
TANK_RECESS = 0.9            # x-scale of the recessed black flank

# landmarks drawn as crosses by `wb.py compare`
MARKS = [REAR_AXLE_PX, FRONT_AXLE_PX, SWINGARM_PIVOT_PX, HEADLIGHT_PX, FORK_TOP_PX]
