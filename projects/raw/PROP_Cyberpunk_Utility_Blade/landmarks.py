"""
Original concept landmarks for PROP_Cyberpunk_Utility_Blade.

There is no reference photo. These are authored orthographic design coordinates, not
measurements from another asset. Pixel coordinates make the concept outline the shared,
testable source for all stages. Side view: blade points image-right = world -Y.
"""
from workbench.refmap import RefMap

ASSET = "PROP_Cyberpunk_Utility_Blade"
IMAGE_SIZE = (640, 480)
REFERENCE_IMAGE = "CONCEPT_TARGET.png"  # procedurally generated, not a photo or external reference
S = 1600.0
ANCHOR_PX = (240.0, 320.0)       # chosen grip-origin station, not measured evidence
ANCHOR_YZ = (0.0, 0.0)
THETA = 0.0

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
REF.ortho = True
P, P3, photo_of = REF.P, REF.P3, REF.photo_of

# Concept bounds: rear of grip u=80, blade tip u=464 => 384 px / 1600 px/m = 0.240 m.
# The depth (X) is a design assumption and cannot be established by the side view.
ANCHORS = [
    ((0.0, *P(*ANCHOR_PX)), ANCHOR_PX),
    ((0.0, *P(464.0, 320.0)), (464.0, 320.0)),
]

# Authored side-view polygons (u right, v down); no photo/reference silhouette exists.
BLADE_OUTLINE = [
    (258, 295), (264, 282), (309, 274), (376, 268), (420, 274),
    (464, 301), (427, 310), (377, 312), (321, 309), (276, 304), (258, 305),
]
HANDLE_OUTLINE = [
    (80, 307), (91, 290), (118, 285), (145, 290), (174, 287),
    (202, 291), (229, 298), (236, 306), (236, 326), (225, 341),
    (197, 346), (165, 347), (138, 353), (109, 346), (88, 335),
]
GUARD_OUTLINE = [(236, 289), (250, 286), (258, 295), (255, 322),
                 (248, 330), (236, 326), (241, 311)]
SCALE_OUTLINE = [
    (98, 307), (111, 296), (139, 299), (165, 296), (191, 300),
    (216, 304), (230, 310), (226, 329), (203, 337), (175, 338),
    (146, 343), (119, 337), (101, 329),
]

# Shallow blade channel and grip accents sit inside the concept silhouette.
BLADE_CHANNEL = [(270, 292), (315, 283), (375, 280), (411, 283),
                 (423, 289), (377, 288), (318, 291), (275, 298)]
HANDLE_INSET = [(112, 310), (137, 304), (166, 303), (197, 307),
                (216, 313), (195, 315), (164, 312), (137, 314)]
BUTTON_CENTER = (216.0, 326.0)

MARKS = [ANCHOR_PX, (464.0, 301.0), (80.0, 307.0)]
SILHOUETTE = [BLADE_OUTLINE, HANDLE_OUTLINE, GUARD_OUTLINE]
PART_OUTLINES = {
    "BLADE_Main": BLADE_OUTLINE,
    "FRAME_Handle": HANDLE_OUTLINE,
    "FRAME_Guard": GUARD_OUTLINE,
}
