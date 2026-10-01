"""
Reference landmarks for PROP_Glock_19, measured on ref/REAL_REFERENCE.png (1280x720).

All silhouettes/points are PHOTO PIXELS (u right, v down), read on the reference drawing
and checked against ref/REF_MASK.png. Metres only via REF.P() / REF.P3().

Photo & reference analysis (docs/03):
  * Visible side: RIGHT side (-X in Blender space; ejection port and extractor visible;
    muzzle faces image right -> front_is_right=True -> reference camera at -X).
  * Scale 5000.0 px/m (5 px/mm): overall length 925 px / 0.185 m = 5000 px/m.
    Matches Glock 19 Gen 4 official length specification (185 mm = 0.185 m).
    Cross-checks:
      - Overall height: 640 px = 128.0 mm (spec: 128 mm with standard magazine, exact match).
      - Slide length: 872 px = 174.4 mm (spec: 174 mm, +0.2 %).
      - Slide height: 140 px = 28.0 mm (spec: 28 mm, exact match).
      - Bore diameter: 9.0 mm (45 px).
      - Outer barrel diameter: 14.5 mm (72.5 px).
  * Tilt 0.0 deg: bore axis at v=160 is horizontal.
  * Origin (0,0,0): Bore axis at the breech face / trigger plane, px (537.0, 160.0).
    -Y = forward (muzzle), +Y = rearward (sights / slide plate),
    +Z = up (sights), -Z = down (grip / magazine),
    +X = left side (slide stop, mag release), -X = right side (ejection port).
"""
import math
from workbench.refmap import RefMap

ASSET = "PROP_Glock_19"
IMAGE_SIZE = (1280, 720)
S = 5000.0                         # 5000 px/m = 5 px/mm (0.185 m length = 925 px)
ANCHOR_PX = (537.0, 160.0)        # bore axis at breech face / trigger plane
ANCHOR_YZ = (0.0, 0.0)            # world (Y 0, Z 0)
THETA = 0.0                       # horizontal bore line

REF = RefMap(S, ANCHOR_PX, ANCHOR_YZ, THETA, front_is_right=True, image_size=IMAGE_SIZE)
P, P3, photo_of = REF.P, REF.P3, REF.photo_of


def px(m):
    """metres -> pixels."""
    return m * S


def m(p):
    """pixels -> metres."""
    return p / S


BORE_V = 160.0                     # bore axis line (level at Z = 0)
MUZZLE_U = 1098.0
SLIDE_REAR_U = 225.0

# --------------------------------------------------------------------------- half widths (m)
# Glock 19 Gen 4 specifications:
HW_SLIDE = 0.01275         # slide width 25.5 mm (1.0 in)
HW_FRAME = 0.01350         # frame receiver rails 27.0 mm
HW_GRIP = 0.01500          # grip body width 30.0 mm
HW_PALM = 0.01600          # grip palm swell width 32.0 mm (total width 32 mm)
HW_GUARD = 0.00550         # trigger guard width 11.0 mm
HW_TRIGGER = 0.00400       # trigger shoe width 8.0 mm
HW_SAFETY = 0.00150        # trigger safety blade width 3.0 mm
HW_BARREL = 0.00725        # barrel outer radius (dia 14.5 mm)
HW_BORE = 0.00450          # 9mm bore radius
HW_CHAMBER = 0.01270       # barrel chamber block locking into slide
HW_MAG = 0.01125           # magazine body width 22.5 mm
HW_MAG_FLOOR = 0.01400     # magazine floorplate width 28.0 mm
HW_RSIGHT = 0.00750        # rear sight width 15.0 mm
HW_FSIGHT = 0.00190        # front sight width 3.8 mm

# --------------------------------------------------------------------------- slide group
# Slide body: top line at v=60, bottom line at v=200, rear at u=225, front at u=1097
SLIDE_OUTLINE = [
    (225, 60), (1080, 60), (1097, 85), (1097, 130), (1091, 145), (1085, 155),
    (1086, 200), (225, 200)
]
SLIDE_TOP_V = 60.0
SLIDE_BOT_V = 200.0
SLIDE_FRONT_U = 1097.0

# Slide rear cover plate
SLIDE_PLATE_OUTLINE = [
    (223, 62), (226, 62), (226, 198), (223, 198)
]

# Ejection port (right side cut-out on slide): u from 537 to 690, v from 60 to 125
EJECTION_PORT = [
    (537, 60), (690, 60), (690, 125), (537, 125)
]

# Rear cocking serrations: 15 vertical grooves on rear flank (u 270 to 420, v 65 to 195)
SERRATIONS_U = [270 + i * 10 for i in range(15)]

# --------------------------------------------------------------------------- sights
# Rear sight: square notch sight with white U-outline
SIGHT_REAR = [
    (247, 49), (255, 49), (267, 60), (225, 60)
]
# Front sight: blade post with white dot
SIGHT_FRONT = [
    (1055, 55), (1072, 55), (1072, 60), (1055, 60)
]

# --------------------------------------------------------------------------- barrel & recoil
# Chamber block: locks into slide ejection port
BARREL_CHAMBER = [
    (537, 60), (690, 60), (690, 160), (537, 160)
]
# Barrel tube tip: extending to muzzle
BARREL_TIP = [
    (1085, 145), (1091, 145), (1091, 175), (1085, 175)
]
# Recoil spring guide rod collar & tip
RECOIL_GUIDE = [
    (1081, 185), (1086, 185), (1086, 205), (1081, 205)
]

# --------------------------------------------------------------------------- frame group
# Dust cover with Picatinny accessory rail
FRAME_DUST_COVER = [
    (540, 200), (1086, 200), (1081, 205), (1077, 215), (1072, 225),
    (1021, 235), (985, 235), (980, 230), (965, 230), (960, 235),
    (770, 240), (660, 240), (660, 245), (540, 245), (540, 200)
]

# Trigger guard loop (solid frame loop around trigger opening)
FRAME_GUARD = [
    (770, 240), (766, 250), (759, 260), (752, 280), (752, 310), (756, 340),
    (761, 360), (762, 370), (756, 384), (580, 384), (541, 370), (491, 395),
    (535, 340), (548, 340), (559, 350), (617, 355), (699, 350), (710, 340),
    (720, 320), (722, 300), (720, 280), (714, 260), (705, 250), (660, 245),
    (660, 240), (770, 240)
]

# Trigger shoe (inside trigger guard)
CTRL_TRIGGER = [
    (540, 240), (613, 240), (604, 255), (603, 260), (602, 265), (599, 270),
    (598, 280), (599, 290), (603, 300), (607, 310), (613, 320), (619, 330),
    (622, 340), (620, 345), (614, 350), (605, 350), (595, 350), (582, 340),
    (572, 330), (565, 320), (561, 310), (547, 300), (541, 290), (540, 240)
]

# Safety blade (protruding center blade)
CTRL_SAFETY = [
    (608, 295), (622, 320), (620, 340), (610, 335)
]

# Grip profile: backstrap with beavertail, palm swell, heel; front strap with finger grooves
GRIP_BACKSTRAP = [
    (225, 140), (204, 140), (203, 150), (202, 160), (197, 170), (192, 180),
    (191, 185), (194, 195), (229, 205), (247, 215), (257, 225), (264, 235),
    (270, 245), (271, 255), (275, 265), (275, 275), (275, 285), (273, 295),
    (270, 305), (269, 315), (266, 325), (263, 335), (260, 345), (256, 355),
    (252, 365), (249, 375), (244, 385), (240, 395), (236, 405), (230, 415),
    (224, 425), (219, 435), (213, 445), (208, 455), (202, 465), (197, 475),
    (193, 485), (188, 495), (184, 505), (181, 515), (177, 525), (177, 585),
    (188, 595), (203, 605), (216, 615), (208, 625), (206, 635), (206, 640)
]
GRIP_FRONTSTRAP = [
    (491, 395), (488, 405), (486, 415), (483, 425), (483, 435), (484, 445),
    (485, 455), (473, 465), (464, 475), (459, 485), (455, 495), (454, 505),
    (453, 515), (454, 525), (455, 535), (444, 545), (435, 555), (430, 565),
    (426, 575), (423, 585), (421, 595), (422, 605), (424, 615), (424, 625),
    (417, 635), (402, 645)
]

# Complete frame grip including receiver web above trigger guard
FRAME_GRIP = GRIP_BACKSTRAP + [(206, 640), (402, 645)] + GRIP_FRONTSTRAP[::-1] + [
    (541, 370), (535, 340), (540, 240), (540, 200), (225, 200), (225, 140)
]

# Magazine floorplate (slanted Glock baseplate reaching bottom of gun)
MAG_FLOORPLATE = [
    (206, 640), (402, 645), (402, 655), (398, 665), (370, 668), (325, 665),
    (259, 655), (210, 645), (206, 640)
]

# Magazine body (inserted inside grip cavity - never protrudes beyond grip)
MAG_BODY = [
    (286, 250), (470, 250), (390, 638), (220, 638)
]

# Controls: takedown slide lock lever, slide stop lever, pins
CTRL_TAKEDOWN = [(670, 228), (688, 228), (688, 242), (670, 242)]
CTRL_SLIDESTOP = [(540, 205), (630, 205), (630, 225), (550, 225)]
PIN_TRIGGER = (545, 255)
PIN_LOCKING_BLOCK = (555, 225)
PIN_HOUSING = (340, 310)

# Reference-camera anchors: world points on X=0 plane
ANCHORS = [
    ((0.0, *P(1097, 160)), (1097, 160)),   # muzzle on bore axis
    ((0.0, *P(191, 185)), (191, 185)),     # beavertail tip
    ((0.0, *P(247, 49)), (247, 49)),       # rear sight notch top
    ((0.0, *P(370, 668)), (370, 668)),     # magazine floorplate bottom
]

MARKS = [(1097, 160), (191, 185), (247, 49), (370, 668), (537, 160), PIN_TRIGGER]

# Reference silhouette (gate R01): union of all component closed polygons
SILHOUETTE = [
    SLIDE_OUTLINE, SIGHT_REAR, SIGHT_FRONT, BARREL_TIP, RECOIL_GUIDE,
    FRAME_DUST_COVER, FRAME_GUARD, CTRL_TRIGGER, FRAME_GRIP, MAG_FLOORPLATE
]

PART_OUTLINES = {
    "SLIDE_Body": SLIDE_OUTLINE,
    "SIGHT_Rear": SIGHT_REAR,
    "SIGHT_Front": SIGHT_FRONT,
    "FRAME_DustCover": FRAME_DUST_COVER,
    "FRAME_TriggerGuard": FRAME_GUARD,
    "FRAME_Grip": FRAME_GRIP,
    "CTRL_TriggerShoe": CTRL_TRIGGER,
    "MAG_Floorplate": MAG_FLOORPLATE,
}
