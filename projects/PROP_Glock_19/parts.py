"""
Part builders for PROP_Glock_19 (staged pipeline, docs/01_WORKFLOW.md).
Every builder takes a stage profile P and reads ALL placement from landmarks.py (pixels).
Library map: docs/04_MODELING_TOOLKIT.md.

  S1 PRIMITIVE  *_prim builders: boxes / cylinders / simplified outlines from landmarks
  S2 LOWPOLY    the real builders with PROFILES[2] (game LOD0: clean topology, no bevels, shared UV)
  S3 DETAIL     the same builders with PROFILES[3] (bevels, weighted normals, serrations, pins, details)
  S4 GAME       automatic: bake S3 -> S2 atlas, LOD1-2, collision per Part, engine export

Groups: SLIDE_, BARREL_, SIGHT_, RECOIL_, FRAME_, CTRL_, MAG_.
Right-side-only parts sit at -X, left-side-only parts sit at +X.
Stage suffixes (_PRIM / _LP / _HP) come from nm().
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "hero_prop"                 # tables.BUDGETS: S1 < 1.5k, S2: 4k-15k, S3 < 60k
TARGET_DIMS = (0.032, 0.184, 0.124)    # overall (X width across palm swell, Y length, Z height)
GROUND = False                         # hand-held: origin on the bore axis at breech face

PROFILES = {
    1: stages.profile(1, ring=8, lathe=8, stations=6, bevel=False, detail=False, subsurf=False),
    2: stages.profile(2, ring=16, lathe=16, stations=16, bevel=False, detail=False, subsurf=False),
    3: stages.profile(3, ring=28, lathe=28, stations=28, bevel=True, detail=True, subsurf=False),
}

GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.015)
LICENCE = "own procedural build from reference measurements; Glock 19 Gen 4"
UNCERTAIN = [
    "widths across X estimated from Glock 19 technical specifications",
    "internal striker channel simplified behind slide cover plate",
    "magazine internal spring and follower simplified"
]

PALETTE = {
    "MAT_POLYMER": ((0.025, 0.025, 0.028), 0.0, 0.65),            # matte black polymer frame & baseplate
    "MAT_STEEL_NITRIDED": ((0.035, 0.035, 0.038), 0.90, 0.38),     # nitrided Tenifer/nDLC black steel slide & barrel
    "MAT_STEEL_BRIGHT": ((0.55, 0.55, 0.56), 1.0, 0.20),          # bright steel (pins, extractor, spring)
    "MAT_SIGHT_WHITE": ((0.85, 0.85, 0.85), 0.0, 0.30),           # sight contrast dots / outline
}
POLY = "MAT_POLYMER"
STEEL = "MAT_STEEL_NITRIDED"
BRIGHT = "MAT_STEEL_BRIGHT"
WHITE = "MAT_SIGHT_WHITE"

CRITICAL_PAIRS = [
    ("CTRL_TriggerShoe", "FRAME_TriggerGuard"),
    ("MAG_Floorplate", "FRAME_TriggerGuard"),
]


def nm(P, name):
    return stages.nm(P, name)


def triangulate_ngons(ob):
    """Triangulate faces with > 4 verts to satisfy U12 (n-gons <= 5%)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()
    return ob


def hard(ob, P, bevel=0.0012, segments=2):
    """hard-surface finish at S3: bevel + weighted normals. Never subsurf plates (gate H01)."""
    triangulate_ngons(ob)
    if P.get("bevel") and bevel:
        mods.bevel(ob, bevel, segments)
        mods.weighted_normal(ob)
    return ob


# ============================================================================ S1 PRIMITIVES
def slide_prim(P):
    coll = P["coll"]
    b1 = prim.plate_px(nm(P, "SLIDE_Body"), coll, L.SLIDE_OUTLINE, L.HW_SLIDE, STEEL, tol=2.0)
    b2 = prim.box_px(nm(P, "SLIDE_Plate"), coll, L.SLIDE_PLATE_OUTLINE, L.HW_SLIDE * 0.9, POLY)
    triangulate_ngons(b1)
    return [b1, b2]


def barrel_prim(P):
    coll = P["coll"]
    b1 = prim.box_px(nm(P, "BARREL_Chamber"), coll, L.BARREL_CHAMBER, L.HW_CHAMBER, STEEL)
    b2 = prim.cyl_px(nm(P, "BARREL_Tube"), coll, (690, 160), (1091, 160), L.HW_BARREL, segs=8, mat=STEEL)
    return [b1, b2]


def sights_prim(P):
    coll = P["coll"]
    b1 = prim.box_px(nm(P, "SIGHT_Rear"), coll, L.SIGHT_REAR, L.HW_RSIGHT, POLY)
    b2 = prim.box_px(nm(P, "SIGHT_Front"), coll, L.SIGHT_FRONT, L.HW_FSIGHT, POLY)
    return [b1, b2]


def recoil_prim(P):
    coll = P["coll"]
    b1 = prim.cyl_px(nm(P, "RECOIL_GuideRod"), coll, (690, 195), (1086, 195), 0.004, segs=8, mat=STEEL)
    b2 = prim.box_px(nm(P, "RECOIL_Collar"), coll, L.RECOIL_GUIDE, 0.006, STEEL)
    return [b1, b2]


def frame_prim(P):
    coll = P["coll"]
    b1 = prim.plate_px(nm(P, "FRAME_DustCover"), coll, L.FRAME_DUST_COVER, L.HW_FRAME, POLY, tol=2.0)
    b2 = prim.plate_px(nm(P, "FRAME_TriggerGuard"), coll, L.FRAME_GUARD, L.HW_GUARD, POLY, tol=2.0)
    b3 = prim.plate_px(nm(P, "FRAME_Grip"), coll, L.FRAME_GRIP, L.HW_PALM, POLY, tol=1.5)
    for b in [b1, b2, b3]:
        triangulate_ngons(b)
    return [b1, b2, b3]


def trigger_prim(P):
    coll = P["coll"]
    b1 = prim.plate_px(nm(P, "CTRL_TriggerShoe"), coll, L.CTRL_TRIGGER, L.HW_TRIGGER, POLY, tol=1.5)
    triangulate_ngons(b1)
    return [b1]


def controls_prim(P):
    coll = P["coll"]
    hw = L.HW_FRAME
    b1 = prim.box_px(nm(P, "CTRL_Takedown"), coll, L.CTRL_TAKEDOWN, hw + 0.001, STEEL)
    return [b1]


def mag_prim(P):
    coll = P["coll"]
    b1 = prim.plate_px(nm(P, "MAG_Floorplate"), coll, L.MAG_FLOORPLATE, L.HW_MAG_FLOOR, POLY, tol=2.0)
    triangulate_ngons(b1)
    return [b1]


# ============================================================================ S2 LOWPOLY & S3 DETAIL BUILDERS
def slide(P):
    coll = P["coll"]
    hw = L.HW_SLIDE

    # 1. Main slide body following exact measured reference outline
    ob_slide = mesh.plate(nm(P, "SLIDE_Body"), coll, L.SLIDE_OUTLINE, -hw, hw, STEEL)
    hard(ob_slide, P, 0.0012)

    if P.get("detail"):
        y_ext, z_ext = L.P(560, 110)
        ext = mesh.box(nm(P, "SLIDE_Extractor"), coll, (-hw - 0.0005, y_ext, z_ext),
                       (0.002, 0.012, 0.006), BRIGHT)
        hard(ext, P, 0.0005)

    ob_plate = mesh.plate(nm(P, "SLIDE_Plate"), coll, L.SLIDE_PLATE_OUTLINE,
                          -hw * 0.88, hw * 0.88, POLY)
    hard(ob_plate, P, 0.00015)

    objs = [ob_slide, ob_plate]
    if P.get("detail") and bpy.data.objects.get(nm(P, "SLIDE_Extractor")):
        objs.append(bpy.data.objects.get(nm(P, "SLIDE_Extractor")))
    return objs


def barrel(P):
    coll = P["coll"]
    ob_chamber = mesh.plate(nm(P, "BARREL_Chamber"), coll, L.BARREL_CHAMBER,
                            -L.HW_CHAMBER, L.HW_CHAMBER, STEEL)
    hard(ob_chamber, P, 0.0010)

    y_start, z_axis = L.P(690, L.BORE_V)
    y_end, _ = L.P(1091, L.BORE_V)
    segs = P.get("lathe", 16)
    ob_tube = mesh.cyl(nm(P, "BARREL_Tube"), coll, (0, y_start, z_axis), (0, y_end, z_axis),
                       L.HW_BARREL, segs=segs, mat=STEEL)
    hard(ob_tube, P, 0.0008)

    y_bore_start = y_end + 0.012
    ob_bore = mesh.cyl(nm(P, "BARREL_Bore"), coll, (0, y_bore_start, z_axis), (0, y_end + 0.0001, z_axis),
                       L.HW_BORE, segs=segs, mat=STEEL)

    return [ob_chamber, ob_tube, ob_bore]


def sights(P):
    coll = P["coll"]
    ob_rear = mesh.plate(nm(P, "SIGHT_Rear"), coll, L.SIGHT_REAR,
                         -L.HW_RSIGHT, L.HW_RSIGHT, POLY)
    hard(ob_rear, P, 0.0006)

    ob_front = mesh.plate(nm(P, "SIGHT_Front"), coll, L.SIGHT_FRONT,
                          -L.HW_FSIGHT, L.HW_FSIGHT, POLY)
    hard(ob_front, P, 0.0002)

    objs = [ob_rear, ob_front]
    if P.get("detail"):
        y_fdot, z_fdot = L.P(1058, 54)
        dot = mesh.box(nm(P, "SIGHT_FrontDot"), coll, (0.0, y_fdot, z_fdot),
                       (0.0015, 0.001, 0.0015), WHITE)
        objs.append(dot)
    return objs


def recoil(P):
    coll = P["coll"]
    y_start, z_rod = L.P(690, 195)
    y_end, _ = L.P(1086, 195)
    segs = P.get("lathe", 12)
    ob_rod = mesh.cyl(nm(P, "RECOIL_GuideRod"), coll, (0, y_start, z_rod), (0, y_end, z_rod),
                      0.004, segs=segs, mat=STEEL)

    y_c0, _ = L.P(1081, 195)
    y_c1, _ = L.P(1086, 195)
    ob_collar = mesh.cyl(nm(P, "RECOIL_Collar"), coll, (0, y_c0, z_rod), (0, y_c1, z_rod),
                         0.006, segs=segs, mat=STEEL)
    hard(ob_rod, P, 0.0005)
    hard(ob_collar, P, 0.0005)
    return [ob_rod, ob_collar]


def frame(P):
    coll = P["coll"]
    ob_dust = mesh.plate(nm(P, "FRAME_DustCover"), coll, L.FRAME_DUST_COVER,
                         -L.HW_FRAME, L.HW_FRAME, POLY)
    hard(ob_dust, P, 0.0012)

    ob_guard = mesh.plate(nm(P, "FRAME_TriggerGuard"), coll, L.FRAME_GUARD,
                          -L.HW_GUARD, L.HW_GUARD, POLY)
    hard(ob_guard, P, 0.0010)

    ob_grip = mesh.plate(nm(P, "FRAME_Grip"), coll, L.FRAME_GRIP,
                         -L.HW_PALM, L.HW_PALM, POLY)
    hard(ob_grip, P, 0.0015)

    return [ob_dust, ob_guard, ob_grip]


def trigger(P):
    coll = P["coll"]
    ob_shoe = mesh.plate(nm(P, "CTRL_TriggerShoe"), coll, L.CTRL_TRIGGER,
                         -L.HW_TRIGGER, L.HW_TRIGGER, POLY)
    hard(ob_shoe, P, 0.0006)

    ob_safety = mesh.plate(nm(P, "CTRL_SafetyBlade"), coll, L.CTRL_SAFETY,
                           -L.HW_SAFETY, L.HW_SAFETY, POLY)
    hard(ob_safety, P, 0.0005)

    return [ob_shoe, ob_safety]


def controls(P):
    coll = P["coll"]
    hw = L.HW_FRAME
    objs = []

    ob_td = mesh.plate(nm(P, "CTRL_Takedown"), coll, L.CTRL_TAKEDOWN,
                       -hw - 0.0015, hw + 0.0015, STEEL)
    hard(ob_td, P, 0.0005)
    objs.append(ob_td)

    y_ss, z_ss = L.P(L.CTRL_SLIDESTOP[0][0], L.CTRL_SLIDESTOP[0][1])
    ob_ss = mesh.plate(nm(P, "CTRL_SlideStop"), coll, L.CTRL_SLIDESTOP,
                       hw, hw + 0.0020, STEEL)
    hard(ob_ss, P, 0.0005)
    objs.append(ob_ss)

    for p_name, px_pt in [("PIN_Trigger", L.PIN_TRIGGER),
                           ("PIN_Locking", L.PIN_LOCKING_BLOCK),
                           ("PIN_Housing", L.PIN_HOUSING)]:
        yp, zp = L.P(*px_pt)
        p_ob = mesh.cyl(nm(P, f"CTRL_{p_name}"), coll,
                        (-hw - 0.0005, yp, zp), (hw + 0.0005, yp, zp),
                        0.0015, segs=12, mat=STEEL)
        objs.append(p_ob)

    return objs


def magazine(P):
    coll = P["coll"]
    ob_floor = mesh.plate(nm(P, "MAG_Floorplate"), coll, L.MAG_FLOORPLATE,
                          -L.HW_MAG_FLOOR, L.HW_MAG_FLOOR, POLY)
    hard(ob_floor, P, 0.0010)

    ob_body = mesh.plate(nm(P, "MAG_Body"), coll, L.MAG_BODY,
                         -L.HW_MAG, L.HW_MAG, POLY)
    hard(ob_body, P, 0.0008)

    return [ob_floor, ob_body]


# ============================================================================ registry
PARTS = [
    Part("slide", slide, prim=slide_prim, collision="box"),
    Part("barrel", barrel, prim=barrel_prim, collision="hull"),
    Part("sights", sights, prim=sights_prim, collision="box"),
    Part("recoil", recoil, prim=recoil_prim, collision="box"),
    Part("frame", frame, prim=frame_prim, collision="hull"),
    Part("trigger", trigger, prim=trigger_prim, collision="box"),
    Part("controls", controls, prim=controls_prim, collision="box"),
    Part("magazine", magazine, prim=mag_prim, collision="hull"),
]

PIVOTS = {
    "SLIDE_Body": lambda: L.P3(537, 160, 0.0),
    "CTRL_TriggerShoe": lambda: L.P3(545, 255, 0.0),
}

CHILDREN = {
    "SLIDE_Plate": "SLIDE_Body",
    "SIGHT_Rear": "SLIDE_Body",
    "SIGHT_Front": "SLIDE_Body",
    "CTRL_SafetyBlade": "CTRL_TriggerShoe",
}


def guide_points():
    return {
        "ANCHOR": L.ANCHORS[0][0],
        "MUZZLE": L.ANCHORS[0][0],
        "SLIDE_REAR": L.ANCHORS[1][0],
        "REAR_SIGHT": L.ANCHORS[2][0],
        "MAG_BASE": L.ANCHORS[3][0],
    }
