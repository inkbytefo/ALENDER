"""World-space design landmarks for the independent Vision V2 coupe concept."""
from workbench.refmap import RefMap

ASSET = "VEH_Vision_V2"

# No product photograph is used: these are authored concept dimensions, not measured facts.
TARGET_LENGTH = 4.45
TARGET_WIDTH = 2.04
TARGET_HEIGHT = 1.28
WHEELBASE = 2.70
FRONT_AXLE_Y = -WHEELBASE / 2
REAR_AXLE_Y = WHEELBASE / 2
GROUND_Z = 0.0

# The workbench's camera helper still expects a RefMap. It is intentionally not
# used to claim photo alignment; all build coordinates below are direct metres.
REF = RefMap(100.0, (600.0, 500.0), (0.0, 0.0), 0.0,
             front_is_right=True, image_size=(1200, 1000))
REF.ortho = True

ANCHORS = []
SILHOUETTE = []
PART_OUTLINES = {}
MARKS = []

# y, half-width, hood top, shoulder top
# A long bonnet, compact swept cabin, and short tapering tail give this concept its
# own proportions. These values are design choices, not factory specifications.
BODY = [
    (-2.205, 0.785, 0.605, 0.620),
    (-2.08, 0.865, 0.655, 0.690),
    (-1.82, 0.920, 0.716, 0.770),
    (-1.50, 0.930, 0.748, 0.790),
    (-1.35, 0.918, 0.754, 0.790),
    (-1.05, 0.895, 0.758, 0.785),
    (-0.70, 0.858, 0.766, 0.785),
    (-0.30, 0.858, 0.774, 0.792),
    (0.30, 0.882, 0.778, 0.805),
    (0.72, 0.915, 0.780, 0.818),
    (1.15, 0.928, 0.778, 0.820),
    (1.48, 0.915, 0.764, 0.800),
    (1.82, 0.875, 0.720, 0.750),
    (2.08, 0.820, 0.670, 0.695),
    (2.205, 0.735, 0.625, 0.640),
]

# y, roof height, roof half-width, lower half-width, lower edge z
# The greenhouse has a raised, gently arched roof and a fastback rear screen.
CABIN = [
    (-0.88, 0.790, 0.650, 0.735, 0.735),
    (-0.64, 0.945, 0.620, 0.740, 0.750),
    (-0.31, 1.190, 0.585, 0.735, 0.765),
    (-0.08, 1.265, 0.585, 0.735, 0.775),
    (0.34, 1.280, 0.600, 0.750, 0.780),
    (0.62, 1.245, 0.625, 0.765, 0.785),
    (0.91, 1.100, 0.665, 0.775, 0.785),
    (1.20, 0.825, 0.720, 0.775, 0.765),
]

WHEELS = [
    (FRONT_AXLE_Y, 0.345, 0.205, 0.785),
    (REAR_AXLE_Y, 0.355, 0.225, 0.790),
]

MIRROR_X = 1.020
BODY_END_Y = TARGET_LENGTH / 2
