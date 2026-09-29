"""
PBR library preview:  python wb.py pbr preview [--filter Metal] [--cols 6] [--samples 64] [--root DIR]
Builds one labelled material ball (+ a flat swatch) per texture set in the presentation studio and
renders output/_pbr/pbr_preview[_<filter>].png - look at it before choosing materials for an asset.
"""
import argparse
import math
import os
import sys
import bmesh
import bpy
from mathutils import Vector

from workbench import paths, pbrlib
from workbench.bl import scene, pbr, presentation as pres
from workbench.bl.scene import coll

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--filter", default="")
ap.add_argument("--cols", type=int, default=6)
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--root", default="")
a = ap.parse_args(argv)

scene.reset()
scene.setup_collections()
sets = [s for s in pbrlib.scan(a.root or None) if a.filter.lower() in s["name"].lower()]
if not sets:
    sys.exit("[PBR] no texture sets found")
R, GAP, GAP_Y = 0.22, 0.62, 0.78


def uv_sphere(name, c, r, segs=64, rings=32):
    """UV sphere with a clean vertical seam (duplicated seam column) and u = longitude, v = latitude."""
    verts, faces, uvs = [], [], []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(segs + 1):
            ph = 2 * math.pi * j / segs
            verts.append(c + Vector((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th))))
    w = segs + 1
    for i in range(rings):
        for j in range(segs):
            faces.append((i * w + j, (i + 1) * w + j, (i + 1) * w + j + 1, i * w + j + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = ((vi % w) / segs, 1.0 - (vi // w) / rings)
    me.validate()
    return me
objs = []
cols = min(a.cols, len(sets))
rows = math.ceil(len(sets) / cols)
for i, s in enumerate(sets):
    cx = (i % cols - (cols - 1) / 2) * GAP
    cy = ((rows - 1) / 2 - (i // cols)) * GAP_Y          # first set top-left
    me = uv_sphere("BALL_" + s["name"], Vector((cx, cy, R)), R)
    ob = bpy.data.objects.new("BALL_" + s["name"], me)
    coll("05_HIGH_BODY").objects.link(ob)
    # UV sphere: an INTEGER number of repeats around u, otherwise the texture breaks at the seam
    m = pbr.material("PBR_" + s["name"], s, tile_m=1.0, uv_m=3.0, bump=0.15)
    pbr.assign(ob, m)
    objs.append(ob)
    cu = bpy.data.curves.new("LBL_" + s["name"], "FONT")
    cu.body = s["name"]
    cu.size = 0.055
    cu.align_x = "CENTER"
    t = bpy.data.objects.new("LBL_" + s["name"], cu)
    t.location = (cx, cy - R - 0.10, 0.002)
    coll("05_HIGH_BODY").objects.link(t)
    lm = bpy.data.materials.get("LBL_MAT") or pres._material("LBL_MAT", (0.85, 0.85, 0.85), 0.6)
    cu.materials.append(lm)

pres.studio(objs, "neutral_grey")
cams = pres.hero_cameras(objs + [o for o in bpy.data.objects if o.name.startswith("LBL_")],
                         {"GRID": (0.0, 72.0, 50.0, 0.05, (1920, int(1920 * rows * GAP_Y / (cols * GAP)) // 2 * 2 + 60))})
tag = ("_" + a.filter) if a.filter else ""
out = paths.out("_pbr", "", f"pbr_preview{tag}.png")
pres.render_stills(cams, os.path.dirname(out), "pbr_preview" + tag + "_", "CYCLES", a.samples)
print("[PBR] preview:", os.path.join(os.path.dirname(out), f"pbr_preview{tag}_grid.png"), len(sets), "sets")
