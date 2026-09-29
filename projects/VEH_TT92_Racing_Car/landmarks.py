"""
Reference landmarks for VEH_TT92_Racing_Car  (single source of truth for proportions).

PRIMARY PHOTO = ref/REAL_REFERENCE.png, a near-orthographic TOP view (681 x 1265 px).
  * front of the car = image TOP (steering wheel ahead of the seat, engine louvres + exhaust
    headers at the blunt end, exhaust runs back to the pointed tail). The AI cheatsheet has the
    car reversed (pointed end = "nose"); photo wins (project.md).
  * image LEFT = car LEFT = +X ; image TOP = front = -Y ; heights Z are not visible in this photo.
  * the exhaust is on the car's RIGHT (-X), as in the oblique photo.
Scale: rear tyre plan length 225 px = 0.72 m (cheatsheet tyre diameter)  ->  S = 312.5 px/m.
  cross-checks: rear track 447 px = 1.43 m (cheatsheet 1.46 m, -2 %); wheelbase 665 px = 2.13 m
  (front-engined 1950s GP cars 2.2-2.3 m, -5 %).
Centre line: u = 345 (nose 342, cockpit 342-347, tail 347, wheel pairs 346). Built symmetric.
Origin: X = 0 centre line, Y = 0 midway between the axles, Z = 0 ground.
Tilt: none (top view). Perspective of the unknown top camera ignored (body top 0.78 m vs tyres).
HEIGHTS: no side photo exists -> Z tables below are ESTIMATES (cheatsheet: body 0.78 m, ground
  clearance 0.12 m; 250F-type layout) checked against the oblique photo with a fitted camera.
Uncertain: all heights, right front suspension (hidden), underside, engine, canard shapes.
"""
import math

ASSET = "VEH_TT92_Racing_Car"
IMAGE_SIZE = (681, 1265)
S = 312.5                          # px per metre
U_C = 345.0                        # centre line (px): nose 342, cockpit 342-347, tail 347, wheels 346
V_MID = 584.5                      # Y = 0 (midway between axle centres)


def X(u):
    return (U_C - u) / S           # image left = car left = +X


def Y(v):
    return (v - V_MID) / S         # image top = front = -Y


def PT(u, v, z=0.0):
    return (X(u), Y(v), z)


def photo_of(x, y):
    return (U_C - x * S, V_MID + y * S)


def m(px):
    return px / S


def interp(table, t):
    if t <= table[0][0]:
        return table[0][1]
    for (a, va), (b, vb) in zip(table, table[1:]):
        if t <= b:
            return va + (vb - va) * (t - a) / (b - a)
    return table[-1][1]


# --- wheels (top photo) ---------------------------------------------------------------------
FRONT_AXLE_V = 252.0               # left-front tyre v 160..345
REAR_AXLE_V = 917.0                # left-rear tyre v 805..1030
WHEELBASE = (REAR_AXLE_V - FRONT_AXLE_V) / S
R_TYRE_F = 185.0 / S / 2           # 0.296 m
R_TYRE_R = 225.0 / S / 2           # 0.360 m
W_TYRE_F = 0.30                    # plan width 96 px (tread band 85 px)
W_TYRE_R = 0.37                    # plan width 118 px (tread band 108 px)
TRACK_HALF_F = ((347 - 140) + (552.5 - 347)) / 2 / S     # tyre centres u 140 / 552.5
TRACK_HALF_R = ((347 - 121) + (568.5 - 347)) / 2 / S     # tyre centres u 121 / 568.5
RIM_RATIO = 0.74                   # rim / tyre radius (oblique photo: low-profile modern covers)
FRONT_AXLE = (0.0, Y(FRONT_AXLE_V), R_TYRE_F)
REAR_AXLE = (0.0, Y(REAR_AXLE_V), R_TYRE_R)

# --- body plan (half widths in px, measured on the lit right edge; symmetric about U_C) ------
BODY_NOSE_V = 120.0                # blunt nose face (grille dome ahead of it)
BODY_TAIL_V = 1160.0               # pointed tail tip (the thin tail blade runs on to v 1195)
BODY_HW_PX = [(120, 42), (124, 50), (130, 60), (140, 70), (150, 78), (165, 86), (185, 93),
              (200, 96), (250, 97), (450, 97), (550, 98), (650, 99), (700, 103), (840, 102),
              (868, 94), (880, 86), (900, 81), (950, 73), (1000, 63), (1050, 49), (1100, 31),
              (1140, 14), (1160, 2)]
# heights in metres (ESTIMATED, see docstring) keyed by photo v
BODY_ZTOP = [(120, 0.470), (126, 0.505), (135, 0.535), (150, 0.570), (170, 0.600), (200, 0.630),
             (250, 0.660), (300, 0.680), (400, 0.710), (500, 0.735), (560, 0.750), (620, 0.770),
             (655, 0.780), (700, 0.760), (800, 0.735), (868, 0.720), (900, 0.700), (950, 0.655),
             (1000, 0.610), (1050, 0.565), (1100, 0.520), (1140, 0.485), (1160, 0.470)]
BODY_ZBOT = [(120, 0.300), (126, 0.265), (135, 0.240), (150, 0.205), (170, 0.175), (200, 0.150),
             (250, 0.130), (300, 0.120), (900, 0.120), (950, 0.140), (1000, 0.170),
             (1050, 0.220), (1100, 0.290), (1140, 0.360), (1160, 0.400)]
# section shape (superellipse exponents) keyed by v: front round, mid fuller, tail peaked ridge
BODY_ETOP = [(120, 2.2), (300, 2.4), (650, 2.6), (880, 2.4), (1000, 1.8), (1160, 1.5)]
BODY_EBOT = [(120, 2.4), (300, 3.4), (880, 3.4), (1160, 2.4)]
BODY_WIDEST = [(120, 0.50), (400, 0.55), (880, 0.55), (1160, 0.45)]

# --- cockpit (top photo) ---------------------------------------------------------------------
COCKPIT_V = (667.0, 869.0)         # opening front (round arc) / rear (U)
OPEN_HW_PX = [(667, 0), (669, 30), (673, 48), (680, 63), (690, 75), (700, 83), (715, 89),
              (820, 90), (835, 86), (850, 76), (860, 60), (866, 40), (869, 0)]
COCKPIT_FLOOR_Z = 0.19
STEER_WHEEL_PX = (347, 700)        # ellipse 110 x 38 px -> 0.35 m wheel, plane ~20 deg off vertical
STEER_WHEEL_R = 55.0 / S
STEER_WHEEL_Z = 0.66
SEAT_V = (735.0, 862.0)            # cushion front -> seat back
COWL_PAD_V = (640.0, 668.0)        # dark padded roll ahead of the opening

# --- side fins (plan outlines, left; right = mirror) -----------------------------------------
FIN_L_PX = [(250, 372), (225, 364), (195, 360), (170, 361), (156, 368), (153, 380), (162, 400),
            (178, 425), (198, 452), (222, 478), (246, 500), (252, 470)]
FIN_Z = 0.42                       # ESTIMATED: below the exhaust headers (headers are seen above the fin root)

# --- bonnet louvres (two rows on top) + left side louvre panel ------------------------------
LOUVRE_ROWS_U = [(285, 320), (365, 400)]
LOUVRE_V = (265.0, 360.0)
LOUVRE_N = 13
SIDE_LOUVRE_V = (340.0, 510.0)     # left flank panel, u 235..265
AIR_FILTER_PX = ((273, 322), (273, 372))   # red cylinder on the left bonnet flank, 17 px dia

# --- exhaust (right side, -X) -------------------------------------------------------------------
HEADER_V = [340.0, 385.0, 430.0, 475.0]
EXHAUST_PX = [(453, 525), (457, 600), (458, 700), (457, 800), (456, 900), (455, 980), (458, 1040)]
EXHAUST_TIP_V = 1060.0
EXHAUST_WRAP_V = (640.0, 890.0)
EXHAUST_R = 9.0 / S                # 18 px pipe
EXHAUST_WRAP_R = 11.0 / S

# --- rear deck details ---------------------------------------------------------------------------
REAR_CAPS_PX = [((297, 893), 13), ((380, 890), 14)]
REAR_XTUBE_V = 930.0               # transverse chrome tube u 215..480 with two red coil springs
REAR_SPRINGS_U = [(255, 300), (385, 425)]
REAR_RODS_PX = [((230, 950), (290, 1060)), ((465, 950), (410, 1060))]

# --- front suspension (left visible; right mirrored = UNCERTAIN) --------------------------------
FRONT_WISHBONE_PX = [(255, 205), (205, 250), (255, 290)]   # chrome A-arm apex at the upright

# --- canards / carbon pieces at the nose (UNCERTAIN shapes) ------------------------------------
NOSE_TABS_U = (277, 412)           # small vertical carbon tabs, v 125..190
CANARD_L_PX = [(250, 140), (250, 198), (196, 200), (196, 146)]   # sloped carbon canard (grey trapezoid)
EXHAUST_Z = (0.40, 0.36)           # ESTIMATED: oblique photo shows lower flank below the wrapped pipe

# crosses drawn by `python wb.py compare`
MARKS = [(140, FRONT_AXLE_V), (552.5, FRONT_AXLE_V), (121, REAR_AXLE_V), (568.5, REAR_AXLE_V),
         (U_C, BODY_NOSE_V), (U_C, BODY_TAIL_V), STEER_WHEEL_PX]


def body_hw(v):
    return m(interp(BODY_HW_PX, v))


def open_hw(v):
    if v <= COCKPIT_V[0] or v >= COCKPIT_V[1]:
        return 0.0
    return m(interp(OPEN_HW_PX, v))

# --- oblique photo (ref/REF_OBLIQUE.png, 631 x 1121) -----------------------------------------------
# A camera fit (refcams.fit_oblique) was tried with 5 anchors: only the two right wheel centres have
# KNOWN heights, the rest depend on this model's own height estimates -> degenerate fit (14.9 mm lens,
# 17.5 px mean error, render did not cover the car). Disabled; the oblique photo is used qualitatively.
OBLIQUE_SIZE = (631, 1121)
OBLIQUE_ANCHORS = []
