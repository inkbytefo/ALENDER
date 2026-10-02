"""
Part builders for CHAR_Cat_Gamer (staged pipeline, docs/01_WORKFLOW.md). Library map: docs/04.

Front-view character: widths come from measured photo rows (landmarks / measured.py), every depth
is a guess. One builder per part for all stages; the stage profile only changes resolution
(ring / rows / tube segments) and, from S3, subsurf on organic parts + bevels on the headphones.
Posed statue (arms crossed) - no rig, no T-pose.
Naming: character sides (_R = image left). Stage suffix via nm().
"""
import math
from mathutils import Vector, Matrix

import landmarks as L
import shapes
from workbench import stages
from workbench.stages import Part
from workbench.bl import mesh, mods

mesh.set_ref(L.REF)

CATEGORY = "character"
TARGET_DIMS = None                     # no real size known (height ASSUMED ~1.0 m)
GROUND = True
PROFILES = {
    1: stages.profile(1, ring=6, rows=8, tube=6, samples=1, lat=3, small=False),
    2: stages.profile(2, ring=20, rows=22, tube=16, samples=2, lat=6, small=True),
    3: stages.profile(3, ring=20, rows=22, tube=16, samples=2, lat=6, small=True),
}
GAME = dict(engine="godot", bake=True, lod=(0.5, 0.25))
PALETTE = {                            # <= 6 materials (character)
    "MAT_FUR_GREY": ((0.36, 0.35, 0.35), 0.0, 0.85),
    "MAT_FUR_WHITE": ((0.82, 0.79, 0.76), 0.0, 0.85),
    "MAT_VEST": ((0.05, 0.045, 0.05), 0.0, 0.6),
    "MAT_RED": ((0.62, 0.03, 0.03), 0.0, 0.3),
    "MAT_EYE": ((0.55, 0.27, 0.04), 0.0, 0.15),
    "MAT_DARK": ((0.045, 0.04, 0.04), 0.0, 0.5),
}
CRITICAL_PAIRS = []
UNCERTAIN = [
    "ALL depths (Y): single front photo - head/torso/limb thickness, tail and ear depth are guesses",
    "scale: height assumed ~1.00 m, camera pitch assumed 12 deg",
    "back of the character, right hand (hidden behind the left arm), tail root (behind the leg)",
    "torso under the crossed arms / vest (hand-read rows)",
    "left headphone cup (mostly hidden behind the head)",
]
KNOWN_LIMITATIONS = [
    "fur is a smooth surface; tabby stripes, brows, logos and whiskers are not modelled",
    "posed statue: no rig / T-pose",
    "photo mask: vest and headphones are hand-traced, rim-lit fur edges are 3-6 px short",
]

GREY, WHITE, VEST, RED, EYE, DARK = "MAT_FUR_GREY", "MAT_FUR_WHITE", "MAT_VEST", "MAT_RED", "MAT_EYE", "MAT_DARK"


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.003):
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def organic(ob, P):
    return mods.finish_organic(ob) if P["subsurf"] else ob


def loft(P, name, rows, dc, dhw, mat, **kw):
    return organic(shapes.row_loft(nm(P, name), P["coll"], rows, dc, dhw, P["ring"], mat, n_rows=P["rows"], **kw), P)


def tube(P, name, pts, mat):
    return organic(shapes.px_tube(nm(P, name), P["coll"], pts, P["tube"], mat, samples=P["samples"]), P)


def blob(P, name, c, radii, mat, **kw):
    return organic(shapes.blob(nm(P, name), P["coll"], c, radii, max(6, P["tube"]), P["lat"], mat, **kw), P)


# ------------------------------------------------------------------------- head
def head_front(u, v):
    """depth of the head's camera-side surface at a pixel (same superellipse as the row loft)."""
    rows = L.HEAD_ROWS
    ul = L.interp([(r[0], r[1]) for r in rows], v)
    ur = L.interp([(r[0], r[2]) for r in rows], v)
    rel = max(-0.98, min(0.98, (u - (ul + ur) / 2.0) / ((ur - ul) / 2.0)))
    return L.HEAD_DEPTH_C - L.interp(L.HEAD_DEPTH_HW, v) * math.sqrt(1.0 - rel * rel)


def head(P):
    out = [loft(P, "HEAD_Skull", L.HEAD_ROWS, L.HEAD_DEPTH_C, L.HEAD_DEPTH_HW, GREY, round_bot=36, round_width=False),
           loft(P, "HEAD_Ear_R", L.EAR_R_ROWS, L.EAR_R_DEPTH_C, L.EAR_DEPTH_HW, GREY),
           loft(P, "HEAD_Ear_L", L.EAR_L_ROWS, L.EAR_L_DEPTH_C, L.EAR_DEPTH_HW, GREY)]
    if not P["small"]:
        return out
    m = L.MUZZLE
    out.append(blob(P, "HEAD_Muzzle", L.P3(*m["c"], head_front(*m["c"]) + 0.012),
                    (m["rx"] / L.S, 0.035, m["rz"] / L.S), WHITE))
    n = L.NOSE
    out.append(blob(P, "HEAD_Nose", L.P3(*n["c"], head_front(*m["c"]) - 0.022),
                    (n["rx"] / L.S, 0.010, n["rz"] / L.S), DARK))
    for side, e in (("R", L.EYE_R), ("L", L.EYE_L)):
        d = head_front(*e["c"])
        out.append(blob(P, "HEAD_Eye_" + side, L.P3(*e["c"], d + 0.012), (e["rx"] / L.S, 0.022, e["rz"] / L.S), WHITE))
        out.append(blob(P, "HEAD_Iris_" + side, L.P3(*e["c"], d - 0.002), (e["iris"] / L.S, 0.012, e["iris"] / L.S), EYE))
        out.append(blob(P, "HEAD_Pupil_" + side, L.P3(*e["c"], d - 0.009), (e["pupil"] / L.S, 0.007, e["pupil"] / L.S), DARK))
    return out


# ------------------------------------------------------------------------- headphones
def _cup(P, side, spec, sgn):
    """cushion + shell cylinders along the head's lateral axis (head yawed by HEAD_YAW)."""
    axis = Vector((sgn * math.cos(L.HEAD_YAW), sgn * math.sin(L.HEAD_YAW), 0.0))
    p0 = Vector(L.P3(*spec["inner"], spec["d"]))
    p1 = p0 + axis * L.CUSHION_THICK
    p2 = p1 + axis * L.CUP_THICK
    segs = max(8, P["tube"] + 8) if P["stage"] > 1 else 8
    return [hard(mesh.cyl(nm(P, "HEADSET_Cushion_" + side), P["coll"], p0, p1, spec["r"] * 0.92, segs, DARK), P, 0.004),
            hard(mesh.cyl(nm(P, "HEADSET_Cup_" + side), P["coll"], p1, p2, spec["r"], segs, RED), P, 0.006)]


def headset(P):
    band = shapes.px_tube(nm(P, "HEADSET_Band"), P["coll"], L.BAND, max(6, P["tube"] // 2), RED, samples=P["samples"])
    return _cup(P, "R", L.CUP_R, -1.0) + _cup(P, "L", L.CUP_L, 1.0) + [band]


# ------------------------------------------------------------------------- body
def torso(P):
    return [loft(P, "BODY_Torso", L.TORSO_ROWS, 0.0, L.TORSO_DEPTH_HW, WHITE, round_bot=40, smooth=0)]


def vest(P):
    hw = [(v, d + 0.007) for (v, d) in L.TORSO_DEPTH_HW]
    ob = shapes.c_shell(nm(P, "VEST_Shell"), P["coll"], L.VEST_ROWS, L.VEST_GAP, 0.0, hw, P["ring"], VEST,
                        n_rows=max(4, P["rows"] // 2), thick_px=5.0, thick_d=0.005)
    return [ob]


def arms(P):
    out = [tube(P, "ARM_Right", L.ARM_R, GREY), tube(P, "ARM_Left", L.ARM_L, GREY)]
    h = L.HAND_L
    out.append(blob(P, "ARM_Hand_L", L.P3(*h["c"], h["d"]), (h["rx"] / L.S, h["ry"], h["rz"] / L.S), WHITE))
    if P["small"]:
        w = L.WRISTBAND
        out.append(hard(mesh.cyl(nm(P, "ARM_Wristband_L"), P["coll"], L.P3(*w[0][:3]), L.P3(*w[1][:3]),
                                 w[0][3] / L.S, P["tube"], RED), P, 0.003))
    return out


def _paw(P, side, s):
    x = L.P3(s["u"], L.ANCHOR_PX[1], 0.0)[0]
    z = s["rz"] * shapes.blob_bottom(P["lat"], 2.8)
    return blob(P, "LEG_Paw_" + side, (x, s["y"], z), (s["rx"], s["ry"], s["rz"]), WHITE, exp=2.6, exp_z=2.8)


def legs(P):
    return [loft(P, "LEG_Upper_R", L.LEG_R_ROWS, L.LEG_R_DEPTH_C, L.LEG_DEPTH_HW, GREY, round_top=30),
            loft(P, "LEG_Upper_L", L.LEG_L_ROWS, L.LEG_L_DEPTH_C, L.LEG_DEPTH_HW, GREY, round_top=30),
            _paw(P, "R", L.PAW_R), _paw(P, "L", L.PAW_L)]


def tail(P):
    return [tube(P, "TAIL_Main", L.TAIL, GREY), tube(P, "TAIL_Tip", L.TAIL_TIP, WHITE)]


# ------------------------------------------------------------------------- registry
PARTS = [
    Part("head", head, collision="hull"),
    Part("headset", headset, collision="hull"),
    Part("torso", torso, collision="hull"),
    Part("vest", vest, collision="none"),
    Part("arms", arms, collision="hull"),
    Part("legs", legs, collision="hull"),
    Part("tail", tail, collision="hull"),
]
PIVOTS = {}
CHILDREN = {}


def guide_points():
    return {"ANCHOR": (0.0, 0.0, 0.0)}
