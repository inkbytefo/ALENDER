"""Authored orthographic design coordinates for the K-7 Rook.

The retained photograph is historical context only; these landmarks define the new design.
Pixel coordinates keep the Workbench reference camera and silhouette gates deterministic.
"""
from workbench.refmap import RefMap

ASSET = "PROP_K7_Rifle"
IMAGE_SIZE = (1536, 720)
REFERENCE_IMAGE = "K7_DESIGN_REFERENCE.png"
S = 1500.0
ANCHOR_PX = (750.0, 350.0)
ANCHOR_YZ = (0.0, 0.0)
THETA = 0.0
REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=False, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of


def Y(u):
    return P(u, BORE_V)[0]


def Z(u, v):
    return P(u, v)[1]


BORE_V = 350.0
MUZZLE_U = 72.0
BUTT_U = 1428.0

# Side-view shapes; dimensions are a design target, not a measured real-world specification.
MUZZLE = [(72, 330), (88, 324), (126, 324), (142, 332), (142, 356), (126, 363), (88, 363), (72, 357)]
BARREL = [(132, 338), (365, 338), (365, 362), (132, 362)]

HANDGUARD = [
    (344, 306), (360, 292), (390, 286), (690, 286), (724, 300),
    (738, 318), (738, 366), (718, 382), (377, 382), (351, 366),
]
RECEIVER = [
    (690, 302), (714, 284), (958, 284), (988, 302), (1004, 322),
    (1004, 370), (982, 393), (850, 393), (835, 405), (812, 405),
    (797, 393), (710, 393), (690, 374),
]
TOP_RAIL = [(348, 263), (1008, 263), (1008, 290), (348, 290)]

MAGAZINE = [
    (778, 381), (875, 381), (889, 425), (884, 466), (871, 504),
    (848, 536), (810, 571), (792, 575), (775, 560), (764, 528),
    (762, 491), (768, 450), (770, 414),
]
GRIP = [
    (924, 385), (989, 385), (1008, 414), (1018, 452), (1030, 496),
    (1027, 522), (1015, 536), (976, 529), (956, 515), (948, 489),
    (941, 457), (929, 430),
]
TRIGGER_GUARD = [
    (853, 389), (955, 389), (966, 405), (969, 435), (962, 444),
    (872, 444), (860, 435),
]
TRIGGER = [(886, 400), (901, 400), (900, 419), (910, 430), (904, 435), (892, 426)]

STOCK_TUBE = [(986, 312), (1092, 312), (1092, 364), (986, 364)]
STOCK = [
    (1076, 303), (1110, 294), (1323, 294), (1368, 307), (1392, 326),
    (1388, 358), (1350, 374), (1288, 367), (1220, 355), (1158, 365),
    (1110, 354), (1076, 349),
]
BUTTPLATE = [(1380, 310), (1401, 315), (1428, 330), (1428, 352), (1400, 368), (1380, 362)]
CHEEK_RISER = [(1118, 286), (1298, 281), (1321, 294), (1112, 298)]

FRONT_SIGHT_BASE = [(365, 266), (399, 266), (405, 279), (360, 279)]
FRONT_SIGHT_LEAF = [(379, 217), (385, 217), (390, 266), (374, 266)]
FRONT_SIGHT_EARS = [
    [(362, 249), (373, 249), (373, 269), (362, 269)],
    [(391, 249), (402, 249), (402, 269), (391, 269)],
]
REAR_SIGHT_BASE = [(925, 266), (965, 266), (970, 280), (921, 280)]
REAR_SIGHT_LEAF = [
    (925, 267), (932, 267), (932, 220), (938, 214), (944, 220), (944, 267),
    (953, 267), (953, 220), (960, 214), (966, 220), (966, 276), (925, 276),
]
REAR_SIGHT_WINGS = [
    [(918, 239), (928, 239), (928, 268), (918, 268)],
    [(963, 239), (973, 239), (973, 268), (963, 268)],
]

CHARGING_HANDLE = [(941, 313), (964, 313), (970, 321), (970, 330), (960, 335), (941, 331)]
EJECTION_PORT = [(789, 310), (899, 310), (899, 337), (789, 337)]
RECEIVER_PANEL = [(720, 342), (779, 342), (779, 378), (720, 378)]

HW_MUZZLE = 0.015
HW_BARREL = 0.008
HW_HANDGUARD = 0.036
HW_RECEIVER = 0.028
HW_RAIL = 0.023
HW_MAGAZINE = 0.017
HW_GRIP = 0.022
HW_STOCK = 0.026
HW_SIGHT = 0.012

SILHOUETTE = [
    MUZZLE, BARREL, HANDGUARD, RECEIVER, TOP_RAIL, MAGAZINE, GRIP,
    TRIGGER_GUARD, TRIGGER, STOCK_TUBE, STOCK, BUTTPLATE, CHEEK_RISER,
    FRONT_SIGHT_BASE, FRONT_SIGHT_LEAF, *FRONT_SIGHT_EARS,
    REAR_SIGHT_BASE, REAR_SIGHT_LEAF, *REAR_SIGHT_WINGS,
]
PART_OUTLINES = {}
MARKS = [
    (750, BORE_V), (MUZZLE_U, BORE_V), (BUTT_U, 340),
    (382, 266), (944, 266), (820, 390), (952, 322), (1190, 330),
]
ANCHORS = [((0.0, *P(750, BORE_V)), (750, BORE_V)),
           ((0.0, *P(150, BORE_V)), (150, BORE_V)),
           ((0.0, *P(1350, BORE_V)), (1350, BORE_V))]
