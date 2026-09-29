"""Measurable quality gates (docs/05_VALIDATION.md). Numbers, not opinions.

    st = validate.stats(objs)                    # tris, bbox, uv/material/scale problems
    hits = validate.intersections(PAIRS, objs)   # world-space BVH overlaps between name prefixes
    chk = validate.Checks(); chk.add("U01", "BLOCKER", ok, "detail") ; chk.result()
    validate.write_report(path, asset, chk, metrics, extra)
"""
import json
import os
import bpy
from mathutils import Vector


def mesh_objects(objs):
    return [o for o in objs if o.type == "MESH"]


def stats(objs, top=15):
    """Evaluated (modifiers applied) statistics of mesh objects."""
    objs = mesh_objects(objs)
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    tris = 0
    per = []
    no_uv, empty_slot, bad_scale, used = [], [], [], set()
    for o in objs:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        tris += t
        per.append((t, o.name))
        mw = o.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        eo.to_mesh_clear()
        if not o.data.uv_layers:
            no_uv.append(o.name)
        if not o.data.materials or any(m is None for m in o.data.materials):
            empty_slot.append(o.name)
        used |= {m.name for m in o.data.materials if m}
        if any(abs(s - 1) > 1e-6 for s in o.scale):
            bad_scale.append(o.name)
    per.sort(reverse=True)
    return dict(objects=len(objs), tris=tris, bbox_min=tuple(mn), bbox_max=tuple(mx),
                dims=tuple(mx - mn), no_uv=no_uv, empty_slots=empty_slot, bad_scale=bad_scale,
                materials_used=sorted(used), top_tris=per[:top])


def _tree(o, dg, cache):
    from mathutils.bvhtree import BVHTree
    if o.name not in cache:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        mw = o.matrix_world                      # WORLD space! local-space BVHs give false hits
        verts = [mw @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        eo.to_mesh_clear()
        cache[o.name] = BVHTree.FromPolygons(verts, polys)
    return cache[o.name]


def intersections(pairs, objs, strip_suffix="_LOW"):
    """pairs [("EXHAUST_", "FRAME_"), ...] name-prefix pairs that must not touch.
    Names are compared after removing strip_suffix (so LOW objects use the same pairs)."""
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in mesh_objects(objs) if o.visible_get()]
    cache = {}

    def base(n):
        return n[:-len(strip_suffix)] if strip_suffix and n.endswith(strip_suffix) else n
    hits = set()
    for a, b in pairs:
        A = [o for o in objs if base(o.name).startswith(a)]
        B = [o for o in objs if base(o.name).startswith(b)]
        for oa in A:
            for ob in B:
                if oa is not ob and _tree(oa, dg, cache).overlap(_tree(ob, dg, cache)):
                    hits.add(tuple(sorted((oa.name, ob.name))))
    return sorted(hits)


def symmetry_error(ob, tol=0.001):
    """Max distance of mirrored (-x) vertices to the nearest vertex (metres). 0 = perfectly symmetric."""
    from mathutils.kdtree import KDTree
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    kd = KDTree(len(vs))
    for i, v in enumerate(vs):
        kd.insert(v, i)
    kd.balance()
    return max((kd.find(Vector((-v.x, v.y, v.z)))[2] for v in vs), default=0.0)


class Checks:
    def __init__(self):
        self.items = []

    def add(self, cid, severity, ok, detail):
        self.items.append(dict(id=cid, severity=severity, result="PASS" if ok else "FAIL", detail=str(detail)))
        print(f"   [{severity}] {cid}: {'PASS' if ok else 'FAIL'} - {detail}")
        return ok

    def result(self):
        return "PASS" if all(c["result"] == "PASS" for c in self.items if c["severity"] == "BLOCKER") else "FAIL"

    def summary(self):
        return dict(result=self.result(),
                    blockers_failed=sum(1 for c in self.items if c["severity"] == "BLOCKER" and c["result"] == "FAIL"),
                    warnings=sum(1 for c in self.items if c["severity"] == "WARN" and c["result"] == "FAIL"))


def standard_checks(chk, st, target_dims=None, tol=0.02, tri_target=None, tri_max=None, max_materials=8):
    """Universal checks U01-U10 from a stats() dict."""
    if target_dims:
        d = st["dims"]
        ok = all(abs(d[i] - t) / t <= tol for i, t in enumerate(target_dims) if t)
        chk.add("U01", "BLOCKER", ok, "bbox %.3f x %.3f x %.3f m vs target %s" % (*d, target_dims))
    chk.add("U02", "BLOCKER", not st["bad_scale"], st["bad_scale"] or "all scales 1.0")
    chk.add("U03", "BLOCKER", abs(st["bbox_min"][2]) < 0.002, "lowest z = %.4f" % st["bbox_min"][2])
    chk.add("U06", "BLOCKER", not st["no_uv"], st["no_uv"] or "all meshes have UVs")
    chk.add("U07", "BLOCKER", not st["empty_slots"], st["empty_slots"] or "no empty material slots")
    if tri_max:
        chk.add("U08", "BLOCKER", st["tris"] <= tri_max, f"{st['tris']} tris (max {tri_max})")
    if tri_target:
        chk.add("U09", "WARN", tri_target[0] <= st["tris"] <= tri_target[1], f"{st['tris']} tris (target {tri_target})")
    chk.add("U10", "WARN", len(st["materials_used"]) <= max_materials, f"{len(st['materials_used'])} materials")


def write_report(path, asset, chk, metrics, **extra):
    rep = dict(asset=asset, blender=bpy.app.version_string, summary=chk.summary(), metrics=metrics,
               checks=chk.items, **extra)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, default=str)
    print("[REPORT]", path, rep["summary"])
    return rep
