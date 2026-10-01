"""
Landmarks for VEH_TT92_Racing_Car - the single source of truth for every size and position.

Two kinds of numbers live here, and each block says which it is:
  [PHOTO]   measured in px on ref/REAL_REFERENCE.png, a near-orthographic TOP view (681 x 1265 px).
            Front of the car = image TOP, image LEFT = car LEFT.
  [DESIGN]  chosen by the user / designer, not measured (heights, engine, front end, stripes ...).
            There is no side photo, so EVERY height (Z) is a design estimate.

Coordinates: +X = car left, -Y = front, +Z up, metres. Origin: centre line, midway between the
axles, on the ground. Convert px with X(u) / Y(v) / m(px) only.

Scale [PHOTO]: rear tyre plan length 225 px = 0.72 m  ->  S = 312.5 px/m
  cross-checks: rear track 447 px = 1.43 m, wheelbase 665 px = 2.13 m.
"""

ASSET = "VEH_TT92_Racing_Car"
IMAGE_SIZE = (681, 1265)
S = 312.5                          # px per metre
U_C = 345.0                        # centre line (px)
V_MID = 584.5                      # Y = 0 (midway between the axle centres)


def X(u):
    return (U_C - u) / S           # image left = car left = +X


def Y(v):
    return (v - V_MID) / S         # image top = front = -Y


def m(px):
    return px / S


def photo_of(x, y):
    return (U_C - x * S, V_MID + y * S)


def interp(table, t):
    """piecewise-linear lookup in [(key, value), ...]."""
    if t <= table[0][0]:
        return table[0][1]
    for (a, va), (b, vb) in zip(table, table[1:]):
        if t <= b:
            return va + (vb - va) * (t - a) / (b - a)
    return table[-1][1]


# ============================================================================ WHEELS [PHOTO]
FRONT_AXLE_V = 252.0               # left-front tyre v 160..345
REAR_AXLE_V = 917.0                # left-rear tyre v 805..1030
WHEELBASE = (REAR_AXLE_V - FRONT_AXLE_V) / S
R_TYRE_F = 185.0 / S / 2           # 0.296 m
R_TYRE_R = 225.0 / S / 2           # 0.360 m
W_TYRE_F = 0.30                    # plan width 96 px
W_TYRE_R = 0.37                    # plan width 118 px
TRACK_HALF_F = ((347 - 140) + (552.5 - 347)) / 2 / S     # tyre centres u 140 / 552.5
TRACK_HALF_R = ((347 - 121) + (568.5 - 347)) / 2 / S     # tyre centres u 121 / 568.5
RIM_RATIO = 0.74                   # rim / tyre radius [DESIGN]

# ============================================================================ BODY SHELL
# The shell is a loft of superellipse sections, one per station v (px along the car).
BODY_NOSE_V = 120.0                # flat nose face
BODY_TAIL_V = 1110.0               # round tail face (radius 0.14 m) carrying the afterburner [DESIGN]
# half width (px). 250 <= v <= 950 [PHOTO]; v < 250 [DESIGN] wedge nose; v > 950 [DESIGN] round tail
BODY_HW_PX = [(120, 60), (124, 66), (130, 70), (140, 74), (150, 77), (165, 81), (185, 87),
              (200, 91), (250, 97), (450, 97), (550, 98), (650, 99), (700, 103), (840, 102),
              (868, 94), (880, 86), (900, 81), (950, 73), (1000, 64), (1050, 54), (1090, 47),
              (1110, 45)]
# top / bottom height (m) [DESIGN]. The nose drops to a low wedge tip (0.40 m), the highest point
# is the cowl ahead of the cockpit (0.78 m), ground clearance 0.12 m.
BODY_ZTOP = [(120, 0.400), (124, 0.425), (130, 0.445), (140, 0.470), (150, 0.490), (170, 0.525),
             (200, 0.570), (250, 0.625), (300, 0.680), (400, 0.710), (500, 0.735), (560, 0.750),
             (620, 0.770), (655, 0.780), (700, 0.760), (800, 0.735), (868, 0.720), (900, 0.700),
             (950, 0.655), (1000, 0.615), (1050, 0.585), (1110, 0.565)]
BODY_ZBOT = [(120, 0.180), (124, 0.165), (130, 0.155), (140, 0.145), (150, 0.140), (170, 0.135),
             (200, 0.130), (250, 0.125), (300, 0.120), (900, 0.120), (950, 0.150), (1000, 0.200),
             (1050, 0.250), (1110, 0.285)]
# section shape [DESIGN]: superellipse exponents of the upper / lower half, height of the widest point
BODY_ETOP = [(120, 2.6), (300, 2.4), (650, 2.6), (880, 2.4), (1000, 2.1), (1110, 2.0)]
BODY_EBOT = [(120, 3.0), (300, 3.4), (880, 3.4), (1000, 2.6), (1110, 2.0)]
BODY_WIDEST = [(120, 0.45), (400, 0.55), (880, 0.55), (1110, 0.50)]


def body_hw(v):
    return m(interp(BODY_HW_PX, v))


# ============================================================================ COCKPIT [PHOTO] plan, [DESIGN] heights
COCKPIT_V = (667.0, 869.0)         # opening front (round arc) / rear (U)
OPEN_HW_PX = [(667, 0), (669, 30), (673, 48), (680, 63), (690, 75), (700, 83), (715, 89),
              (820, 90), (835, 86), (850, 76), (860, 60), (866, 40), (869, 0)]
COCKPIT_FLOOR_Z = 0.19
STEER_WHEEL_PX = (347, 700)        # 0.35 m wheel, plane ~20 deg off vertical
STEER_WHEEL_R = 55.0 / S
STEER_WHEEL_Z = 0.66
SEAT_V = (735.0, 862.0)            # cushion front -> seat back
COWL_PAD_V = (640.0, 668.0)        # padded leather roll ahead of the opening


def open_hw(v):
    if v <= COCKPIT_V[0] or v >= COCKPIT_V[1]:
        return 0.0
    return m(interp(OPEN_HW_PX, v))


# ============================================================================ BONNET
# louvres + air filter [PHOTO]
LOUVRE_ROWS_U = [(285, 320), (365, 400)]
LOUVRE_V = (265.0, 360.0)
LOUVRE_N = 13
AIR_FILTER_PX = ((273, 322), (273, 372))   # red cylinder on the left bonnet flank, 17 px dia
# engine bay [DESIGN]: open pit in the bonnet between the louvres and the cowl
BAY_V = (386.0, 600.0)             # plan opening front / rear (px)
BAY_HW = 0.165                     # half width (m)
BAY_FLOOR_Z = 0.23
BAY_R_FRONT, BAY_R_REAR = 0.07, 0.04       # corner radii
# panel lines [DESIGN]: bonnet outline (front cross seam, shoulder lines, cowl seam) + tail deck seam
HOOD_SEAM_V = (135.0, 622.0)
HOOD_SEAM_X = 0.235
TAIL_SEAM_V = 935.0
# twin cream stripes from the nose tip to the engine bay [DESIGN]
STRIPE_V = (128.0, 380.0)
STRIPE_X = (0.042, 0.042)          # centre offset, width (m)

# ============================================================================ ENGINE [DESIGN]
# blown 60-degree V8 in the bay: 2 x 4 cylinders, Roots blower, 4 velocity stacks, belt drive.
# Nothing of it is visible in the photos; it is sized to fit the bay and the 4-pipe headers.
ENG_CRANK_Z = 0.36
ENG_BANK_DEG = 30.0                # half V angle
ENG_PITCH = 0.085                  # cylinder pitch
ENG_Y_CENTRE = -0.37               # middle of the blocks (v ~ 469)

# ============================================================================ EXHAUST
# Side pipes: plan up to v 980 on the right [PHOTO]; left = mirror; heights and the run into the tail
# [DESIGN]. Behind the rear axle both pipes sweep inwards and enter the afterburner can.
HEADER_V = [429.0, 456.0, 482.0, 509.0]    # = the V8 cylinder pitch
# right pipe centre line (u px, v px, z m), collector -> afterburner can
EXHAUST_PATH = [(453, 548, 0.400), (457, 600, 0.395), (458, 700, 0.385), (457, 800, 0.375),
                (456, 900, 0.370), (452, 980, 0.375), (435, 1040, 0.395), (412, 1085, 0.415),
                (400, 1112, 0.425)]
EXHAUST_WRAP_V = (640.0, 890.0)    # heat-wrapped section
EXHAUST_R = 9.0 / S                # 18 px pipe
EXHAUST_WRAP_R = 11.0 / S
# ONE afterburner on the centre line, on the round tail face [DESIGN] (jet nozzle / slotted tip /
# glowing collector references). Distances along the car are measured from the tail face (+ = rear).
AB_CAN_R = 0.168                   # chrome can sleeved over the tail end (tail face radius 0.144)
AB_CAN = (-0.035, 0.150)           # can front / rear
AB_PETAL_LEN = 0.23                # converging petals behind the can
AB_EXIT_R = 0.130                  # petal ring radius at the exit
AB_PETALS = 14
AB_SLOTS = 10                      # heat slots around the can

# ============================================================================ REAR DECK + REAR SUSPENSION [PHOTO]
REAR_CAPS_PX = [((297, 893), 13), ((380, 890), 14)]      # filler caps: centre, radius px
REAR_XTUBE_V = 930.0               # transverse tube with two red coil springs
REAR_SPRINGS_U = [(255, 300), (385, 425)]
REAR_RODS_PX = [((230, 950), (300, 1040)), ((465, 950), (390, 1040))]     # tail end [DESIGN]
REAR_ROD_Z = 0.27                  # height of the rod body end 

# ============================================================================ FRONT END [DESIGN]  (front v3, "old JDM wedge")
# Inspiration, not copies: Honda RA300 nose, riveted hot rod, Panigale eyes, fender mirrors.
NOSE_GRILLE = (0.78, 0.60)         # mouth half width / half height as a fraction of the nose face
NOSE_POCKET_DEPTH = 0.12           # dark recess behind the face
EYE_LINE = ((0.070, 188.0), (0.200, 148.0))     # left eye centre line: rear-inner tip -> front-outer (x m, v px)
EYE_WIDTH = [(0.0, 0.008), (0.3, 0.042), (0.75, 0.052), (1.0, 0.040)]   # width (m) along the line
EYE_LAMPS_T = (0.50, 0.78)         # two round lamps along the line
MIRROR_PX = (0.235, 240.0)         # fender mirror foot (x m, v px), left; right mirrored
CHIN_V = (110.0, 150.0)            # chin spoiler front / rear edge
CHIN_Z = (0.172, 0.148)            # its underside height front / rear

# crosses drawn by `python wb.py compare`
MARKS = [(140, FRONT_AXLE_V), (552.5, FRONT_AXLE_V), (121, REAR_AXLE_V), (568.5, REAR_AXLE_V),
         (U_C, BODY_NOSE_V), (U_C, BODY_TAIL_V), STEER_WHEEL_PX]
