"""
Part builders for SZK_11. Every builder takes a LOD profile (LOW = Stage 1, HIGH = Stage 2)
and reads ALL placement from landmarks.py. Library map: docs/04_MODELING_TOOLKIT.md.

Naming: <GROUP>_<Part>[_L|_R]  (BODY_, FRAME_, ENGINE_, WHEEL_, CTRL_, ARCH_, CHR_, PROP_ ...)
LOW objects get the suffix _LOW automatically via nm(). Hidden/guessed parts: UNCERTAIN_ prefix.
"""
import math
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables
from workbench.bl import mesh, mods

mesh.set_ref(L.REF)

LOW = dict(name="LOW", tube=8, tube_s=2, lathe=20, loft=12, stations=8, bevel=False,
           C_PRIMARY="02_LOW_PRIMARY", C_SECONDARY="03_LOW_SECONDARY", C_MECH="04_LOW_MECHANICAL",
           C_DETAIL="04_LOW_MECHANICAL")
HIGH = dict(name="HIGH", tube=20, tube_s=6, lathe=64, loft=28, stations=30, bevel=True,
            C_PRIMARY="05_HIGH_BODY", C_SECONDARY="05_HIGH_BODY", C_MECH="06_HIGH_MECHANICAL",
            C_DETAIL="07_DETAILS")

PALETTE = {                          # <= 8 materials (docs/02_STANDARDS.md)
    "MAT_BODY": "paint_gloss",       # preset names from workbench.bl.materials.PRESETS
    "MAT_TRIM": "metal_dark",
}
CRITICAL_PAIRS = []                  # [("PART_A_", "PART_B_"), ...] must never intersect


def nm(lod, name):
    return name if lod["name"] == "HIGH" else name + "_LOW"


def hard(ob, lod, bevel=0.003):
    """hard-surface finish: bevel + weighted normals at HIGH, nothing at LOW. Never subsurf plates."""
    return mods.finish_hard(ob, bevel, enabled=lod["bevel"])


def organic(ob, lod):
    """organic finish: subsurf (viewport L1 / render L2) at HIGH only."""
    return mods.finish_organic(ob) if lod["name"] == "HIGH" else ob


# ------------------------------------------------------------------------- EXAMPLE builders
def body(lod):
    ob = mesh.plate(nm(lod, "BODY_Main"), lod["C_PRIMARY"], L.BODY_OUTLINE,
                    -L.BODY_HALF_WIDTH, L.BODY_HALF_WIDTH, "MAT_BODY")
    return [hard(ob, lod, 0.01)]


def build_all(lod):
    return {"body": body(lod)}


def guide_points():
    return {"ANCHOR": L.ANCHORS[0][0]}
