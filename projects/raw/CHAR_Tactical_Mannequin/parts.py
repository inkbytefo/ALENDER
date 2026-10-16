"""
Part builders for CHAR_Tactical_Mannequin (staged pipeline, docs/01_WORKFLOW.md).
Industrial shooting range target dummy on a steel floor stand with spring base.
"""
import math
import bpy
from mathutils import Vector, Matrix

import landmarks as L
import shapes
from workbench import stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "large_prop"
TARGET_DIMS = (0.680, 0.420, 1.750)
GROUND = True

PROFILES = {
    1: stages.profile(1, segs=6, detail=False, bevel=False),
    2: stages.profile(2, segs=10, detail=True, bevel=False),
    3: stages.profile(3, segs=12, detail=True, bevel=True),
}

GAME = dict(engine="godot", bake=False, lod=(0.5, 0.25))

PALETTE = {
    "MAT_TARGET_YELLOW": dict(rgb=(0.85, 0.62, 0.08), metallic=0.15, roughness=0.45),
    "MAT_TARGET_STEEL": dict(rgb=(0.18, 0.18, 0.19), metallic=0.90, roughness=0.40),
    "MAT_STAND_STEEL": dict(rgb=(0.12, 0.12, 0.13), metallic=0.88, roughness=0.45),
    "MAT_TARGET_WHITE": dict(rgb=(0.88, 0.88, 0.88), metallic=0.05, roughness=0.55),
}

CRITICAL_PAIRS = []
UNCERTAIN = [
    "Internal spring steel temper grade not specified",
    "Floor bolt anchoring holes assumed standard 12mm industrial pattern",
]

PIVOTS = {
    "SPRING_Unit": lambda: Vector((0.0, 0.0, L.SPRING_Z_START)),
}
CHILDREN = {}


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.002):
    return mods.finish_hard(ob, bevel, enabled=P.get("bevel", False))


# -----------------------------------------------------------------------------
# 1. STAND BASE
# -----------------------------------------------------------------------------
def stand_prim(P):
    coll = P["coll"]
    ob_hub = mesh.box(nm(P, "BASE_Hub"), coll, L.STAND_HUB_CENTER, L.STAND_HUB_SIZE, "MAT_STAND_STEEL")
    ob_legs = mesh.box(nm(P, "BASE_Legs"), coll, (0.0, 0.0, 0.060), (L.BASE_WIDTH, L.BASE_DEPTH, 0.120), "MAT_STAND_STEEL")
    return [ob_hub, ob_legs]


def stand_mesh(P):
    coll = P["coll"]
    ob = shapes.build_stand(nm(P, "BASE_Stand"), coll, "MAT_STAND_STEEL", "MAT_STAND_STEEL", P)
    return [hard(ob, P, bevel=0.002)]


# -----------------------------------------------------------------------------
# 2. SPRING MECHANISM
# -----------------------------------------------------------------------------
def spring_prim(P):
    coll = P["coll"]
    ob_ls = mesh.box(nm(P, "SPRING_LowerSleeve"), coll, L.LOWER_SLEEVE_CENTER, L.SLEEVE_SIZE, "MAT_STAND_STEEL")
    ob_us = mesh.box(nm(P, "SPRING_UpperSleeve"), coll, L.UPPER_SLEEVE_CENTER, L.SLEEVE_SIZE, "MAT_STAND_STEEL")
    ob_sp = shapes.cylinder_mesh(nm(P, "SPRING_CoilPrim"), coll,
                                 (0, 0, L.SPRING_Z_START), (0, 0, L.SPRING_Z_END),
                                 radius=L.SPRING_RADIUS, segs=8, mat="MAT_STAND_STEEL", smooth=True)
    return [ob_ls, ob_us, ob_sp]


def spring_mesh(P):
    coll = P["coll"]
    ob = shapes.build_spring(nm(P, "SPRING_Unit"), coll, "MAT_STAND_STEEL", "MAT_STAND_STEEL", P)
    return [hard(ob, P, bevel=0.002)]


# -----------------------------------------------------------------------------
# 3. BACK SPINE & CLAMPS
# -----------------------------------------------------------------------------
def spine_prim(P):
    coll = P["coll"]
    ob = mesh.box(nm(P, "SPINE_Column"), coll, L.SPINE_CENTER, L.SPINE_SIZE, "MAT_STAND_STEEL")
    return [ob]


def spine_mesh(P):
    coll = P["coll"]
    ob = shapes.build_spine(nm(P, "SPINE_Column"), coll, "MAT_STAND_STEEL", P)
    return [hard(ob, P, bevel=0.002)]


# -----------------------------------------------------------------------------
# 4. TARGET BODY SILHOUETTE
# -----------------------------------------------------------------------------
def target_body_prim(P):
    coll = P["coll"]
    ob_h = mesh.box(nm(P, "BODY_Head"), coll, (0.0, 0.0, 1.640), (0.230, L.BODY_THICKNESS, 0.220), "MAT_TARGET_YELLOW")
    ob_t = mesh.box(nm(P, "BODY_Torso"), coll, (0.0, 0.0, 1.050), (0.560, L.BODY_THICKNESS, 0.700), "MAT_TARGET_YELLOW")
    return [ob_h, ob_t]


def target_body_mesh(P):
    coll = P["coll"]
    ob = shapes.build_target_body(nm(P, "BODY_Silhouette"), coll, "MAT_TARGET_YELLOW", P)
    return [hard(ob, P, bevel=0.002)]


# -----------------------------------------------------------------------------
# 5. FRONT HIT PLATES
# -----------------------------------------------------------------------------
def hit_plates_prim(P):
    coll = P["coll"]
    ob_head = mesh.box(nm(P, "PLATE_Head"), coll, L.HEAD_PLATE_CENTER, L.HEAD_PLATE_SIZE, "MAT_TARGET_STEEL")
    ob_chest = mesh.box(nm(P, "PLATE_Chest"), coll, L.CHEST_PLATE_CENTER, L.CHEST_PLATE_SIZE, "MAT_TARGET_STEEL")
    ob_mid = mesh.box(nm(P, "PLATE_Mid"), coll, L.MID_PLATE_CENTER, L.MID_PLATE_SIZE, "MAT_TARGET_STEEL")
    ob_al = mesh.box(nm(P, "PLATE_ArmL"), coll, L.ARM_L_CENTER, L.ARM_PLATE_SIZE, "MAT_TARGET_STEEL")
    ob_ar = mesh.box(nm(P, "PLATE_ArmR"), coll, L.ARM_R_CENTER, L.ARM_PLATE_SIZE, "MAT_TARGET_STEEL")
    return [ob_head, ob_chest, ob_mid, ob_al, ob_ar]


def hit_plates_mesh(P):
    coll = P["coll"]
    ob = shapes.build_hit_plates(nm(P, "PLATE_HitPlates"), coll, "MAT_TARGET_STEEL", "MAT_STAND_STEEL", P)
    return [hard(ob, P, bevel=0.0015)]


# -----------------------------------------------------------------------------
# PARTS REGISTRY
# -----------------------------------------------------------------------------
PARTS = [
    Part("stand", stand_mesh, prim=stand_prim, collision="box"),
    Part("spring", spring_mesh, prim=spring_prim, collision="box"),
    Part("spine", spine_mesh, prim=spine_prim, collision="box"),
    Part("target_body", target_body_mesh, prim=target_body_prim, collision="box"),
    Part("hit_plates", hit_plates_mesh, prim=hit_plates_prim, collision="box"),
]


def guide_points():
    return {
        "BASE": Vector((0.0, 0.0, 0.0)),
        "SPRING": Vector((0.0, 0.0, L.SPRING_Z_START)),
        "TORSO": Vector((0.0, 0.0, 1.100)),
        "HEAD": Vector((0.0, 0.0, 1.640)),
    }
