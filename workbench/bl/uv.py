"""
UVs for game assets (Stage 2 onwards).

    info = uv.atlas(objs)            # one shared smart-project atlas -> UV_Bake (0-1, bakes)
                                     # + UVMap = same islands at uv_m metres / unit (tiling PBR)
    uv.texel_density(objs)           # px per metre per object at a texture size, spread
    uv.overlap(objs)                 # fraction of UV_Bake area covered twice (must be ~0 to bake)

Lesson 28: box UVs are fine for tiling materials, but bakes need a clean non-overlapping 0-1 atlas.
"""
import math
import bpy
import bmesh
import numpy as np


def _select_only(objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def atlas(objs, uv_m=2.0, angle=55.0, margin=0.004, bake_layer="UV_Bake"):
    """One shared smart-project atlas for all objects (consistent texel density):
    bake_layer = the 0-1 atlas, UVMap (first layer) = the same islands scaled to uv_m metres per UV
    unit for tiling PBR textures. Returns area / coverage / texel info."""
    objs = [o for o in objs if o.type == "MESH"]
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.active_index = 0
    _select_only(objs)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    a3 = auv = 0.0
    for o in objs:
        s3, suv = _areas(o, 0)
        a3 += s3
        auv += suv
    k = math.sqrt(a3 / auv) / uv_m if auv else 1.0
    for o in objs:
        me = o.data
        bake = me.uv_layers.get(bake_layer) or me.uv_layers.new(name=bake_layer)
        main = me.uv_layers[0]
        for i, d in enumerate(main.data):
            bake.data[i].uv = d.uv.copy()
            d.uv = d.uv * k
        me.uv_layers.active_index = 0
    return dict(area3d_m2=round(a3, 4), atlas_coverage=round(auv, 3),
                texel_px_per_m_at_2k=round(2048 * math.sqrt(auv / a3), 1) if a3 else 0.0)


def _areas(o, layer):
    """(3D area m2 in world scale, UV area) of one object's base mesh for a UV layer index/name."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uvl = bm.loops.layers.uv[layer] if isinstance(layer, str) else list(bm.loops.layers.uv)[layer]
    s = o.matrix_world.to_scale()
    sc = abs(s.x * s.y * s.z) ** (2.0 / 3.0)
    a3 = auv = 0.0
    for f in bm.faces:
        a3 += f.calc_area() * sc
        us = [l[uvl].uv for l in f.loops]
        auv += abs(sum(us[i].x * us[(i + 1) % len(us)].y - us[(i + 1) % len(us)].x * us[i].y
                       for i in range(len(us)))) / 2
    bm.free()
    return a3, auv


def texel_density(objs, layer="UV_Bake", tex=2048):
    """Per object px/m at a tex x tex texture; spread = max/min (1.0 = perfectly even)."""
    per = {}
    for o in objs:
        if o.type != "MESH" or layer not in o.data.uv_layers:
            continue
        a3, auv = _areas(o, layer)
        if a3 > 1e-9:
            per[o.name] = round(tex * math.sqrt(auv / a3), 1)
    vals = [v for v in per.values() if v > 0]
    return dict(per_object=per, min=min(vals, default=0), max=max(vals, default=0),
                spread=round(max(vals) / min(vals), 2) if vals else 0.0)


def overlap(objs, layer="UV_Bake", res=512):
    """Fraction of the used UV_Bake area covered more than once (sampled on a res x res grid),
    plus the fraction of UV area outside 0-1. Both must be ~0 for a clean bake."""
    count = np.zeros((res, res), np.int16)
    outside = 0.0
    total = 0.0
    g = (np.arange(res) + 0.5) / res
    for o in objs:
        if o.type != "MESH" or layer not in o.data.uv_layers:
            continue
        me = o.data
        me.calc_loop_triangles()
        uvd = me.uv_layers[layer].data
        for t in me.loop_triangles:
            a, b, c = (uvd[i].uv for i in t.loops)
            area = abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
            total += area
            if min(a.x, b.x, c.x) < -1e-4 or min(a.y, b.y, c.y) < -1e-4 or \
                    max(a.x, b.x, c.x) > 1 + 1e-4 or max(a.y, b.y, c.y) > 1 + 1e-4:
                outside += area
            i0, i1 = int(max(0, min(a.x, b.x, c.x) * res)), int(min(res - 1, max(a.x, b.x, c.x) * res))
            j0, j1 = int(max(0, min(a.y, b.y, c.y) * res)), int(min(res - 1, max(a.y, b.y, c.y) * res))
            if i1 < i0 or j1 < j0 or area < 1e-12:
                continue
            X, Y = np.meshgrid(g[i0:i1 + 1], g[j0:j1 + 1])
            d = (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y)
            w0 = ((b.y - c.y) * (X - c.x) + (c.x - b.x) * (Y - c.y)) / d
            w1 = ((c.y - a.y) * (X - c.x) + (a.x - c.x) * (Y - c.y)) / d
            inside = (w0 > 0) & (w1 > 0) & (1 - w0 - w1 > 0)
            count[j0:j1 + 1, i0:i1 + 1] += inside
    used = int((count > 0).sum())
    return dict(overlap=round(int((count > 1).sum()) / max(1, used), 4),
                outside=round(outside / total, 4) if total else 0.0, coverage=round(used / res / res, 3))
