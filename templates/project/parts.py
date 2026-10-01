"""
Part builders for __ASSET__ (staged pipeline, docs/01_WORKFLOW.md). Library map: docs/04_MODELING_TOOLKIT.md.

  S1 PRIMITIVE  *_prim builders: boxes / cylinders / simplified outlines from landmarks
  S2 LOWPOLY    the real builders with PROFILES[2]  (game LOD0: clean topology, no bevels)
  S3 DETAIL     the SAME builders with PROFILES[3]  (bevels, subsurf on lofts, fasteners, details)
  S4 GAME       automatic: bake S3 -> S2 atlas, LOD1-2, collision per Part, engine export

Every builder takes a stage profile P and reads ALL placement from landmarks.py.
Naming: <GROUP>_<Part>[_L|_R] via nm(P, ...) -> stage suffix _PRIM / _LP / _HP added automatically.
Hidden / guessed parts: UNCERTAIN_ prefix. Put everything in P["coll"] (or the legacy C_* keys).
"""
import math
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "__BUDGET__"                # key of workbench.tables.BUDGETS (tri / texture / glb budgets)
TARGET_DIMS = (None, None, None)       # TODO known real size (x, y, z) in metres -> gate U01
GROUND = True                          # lowest point at Z = 0 (False for hand-held props)
PROFILES = {                           # builder knobs per stage (add your own keys)
    1: stages.profile(1, ring=8, stations=4),
    2: stages.profile(2, ring=16, stations=12),
    3: stages.profile(3, ring=32, stations=28),
}
GAME = dict(engine="godot", bake=True, lod=(0.5, 0.25))   # godot | unity | unreal (docs/12)
PALETTE = {                            # <= 8 materials (docs/02_STANDARDS.md)
    "MAT_BODY": "paint_gloss",         # preset names from workbench.bl.materials.PRESETS
    "MAT_TRIM": "metal_dark",
}
CRITICAL_PAIRS = []                    # [("PART_A_", "PART_B_"), ...] must never intersect (gate X01)
UNCERTAIN = []                         # copied into report.json


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.003):
    """hard-surface finish: bevel + weighted normals from S3 on. Never subsurf plates (gate H01)."""
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def organic(ob, P):
    """organic finish: subsurf (viewport L1 / render L2) from S3 on."""
    return mods.finish_organic(ob) if P["subsurf"] else ob


# ------------------------------------------------------------------------- EXAMPLE part "body"
def body_prim(P):
    return [prim.box_px(nm(P, "BODY_Main"), P["coll"], L.BODY_OUTLINE, L.BODY_HALF_WIDTH, "MAT_BODY")]


def body(P):
    ob = mesh.plate(nm(P, "BODY_Main"), P["coll"], L.BODY_OUTLINE,
                    -L.BODY_HALF_WIDTH, L.BODY_HALF_WIDTH, "MAT_BODY")
    return [hard(ob, P, 0.01)]


# ------------------------------------------------------------------------- registry
PARTS = [
    Part("body", body, prim=body_prim, collision="box"),
]
PIVOTS = {}        # {"DOOR_Front_L": lambda: L.P3(u, v, x)}  moving parts: origin on the joint (gate M01)
CHILDREN = {}      # {"DOOR_Handle_L": "DOOR_Front_L"}      parts that ride with a moving part


def guide_points():
    return {"ANCHOR": L.ANCHORS[0][0]}
