"""Measurable quality gates (docs/05_VALIDATION.md). Numbers, not opinions.

    st = validate.stats(objs)                    # tris, bbox, uv/material/scale problems
    hits = validate.intersections(PAIRS, objs)   # world-space BVH overlaps between name prefixes
    chk = validate.Checks(); chk.add("U01", "BLOCKER", ok, "detail") ; chk.result()
    validate.write_report(path, asset, chk, metrics, extra)
    hy = validate.hygiene(objs); validate.hygiene_checks(chk, hy)     # U04 U05 U11 U12
    validate.policy_checks(chk, objs, suffix="_LP")                    # N01 naming, H01 smoothing
    validate.print_checks(chk, objs, min_wall=0.001)                   # P01 watertight, P02 wall

Check ids (docs/05_VALIDATION.md): U01-U16 universal, X01 intersections, R01-R03 reference
silhouette, D01-D02 stage drift, N01 naming, H01 smoothing policy, M01 moving parts,
G01-G08 game delivery, P01-P02 3D print.
"""
import json
import math
import os
import bpy
import bmesh
from mathutils import Vector

from workbench import stages

HARD_BUILDERS = ("plate", "extrude", "box", "multi_cyl")   # never subsurf these (lesson 7)


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


def intersections(pairs, objs, strip_suffix=None):
    """pairs [("EXHAUST_", "FRAME_"), ...] name-prefix pairs that must not touch.
    Names are compared without their stage suffix (_PRIM/_LP/_HP/_LOW/_LODn), so every stage
    uses the same pairs; strip_suffix="X" strips only that suffix (legacy behaviour)."""
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in mesh_objects(objs) if o.visible_get()]
    cache = {}

    def base(n):
        if strip_suffix is None:
            return stages.base_name(n)
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


# ----------------------------------------------------------------------------- mesh hygiene
def hygiene(objs, area_eps=1e-10, len_eps=1e-7):
    """Topology health of the EVALUATED meshes (what gets exported). Totals + per object:
    non_manifold (edges with > 2 faces), boundary (open edges), loose (verts/edges without faces),
    degenerate (faces with ~0 area, ~0-length edges), flipped (manifold edges whose two faces
    disagree in winding), inverted (closed objects with negative volume), ngons, quads, tris."""
    dg = bpy.context.evaluated_depsgraph_get()
    keys = ("non_manifold", "boundary", "loose", "degenerate", "flipped", "inverted")
    per = {}
    tot = dict({k: 0 for k in keys}, ngons=0, quads=0, tris=0, faces=0)
    for o in mesh_objects(objs):
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        eo.to_mesh_clear()
        r = dict({k: 0 for k in keys}, ngons=0, quads=0, tris=0, faces=len(bm.faces))
        for e in bm.edges:
            n = len(e.link_faces)
            if n == 0:
                r["loose"] += 1
            elif n == 1:
                r["boundary"] += 1
            elif n > 2:
                r["non_manifold"] += 1
            elif not e.is_contiguous:
                r["flipped"] += 1
            if e.calc_length() < len_eps:
                r["degenerate"] += 1
        r["loose"] += sum(1 for v in bm.verts if not v.link_edges)
        for f in bm.faces:
            k = len(f.verts)
            r["tris" if k == 3 else "quads" if k == 4 else "ngons"] += 1
            if f.calc_area() < area_eps:
                r["degenerate"] += 1
        if r["boundary"] == 0 and r["non_manifold"] == 0 and bm.faces and bm.calc_volume(signed=True) < 0:
            r["inverted"] = 1
        bm.free()
        per[o.name] = r
        for k in tot:
            tot[k] += r[k]
    tot["ngon_ratio"] = round(tot["ngons"] / max(1, tot["faces"]), 4)
    worst = {k: sorted(((r[k], n) for n, r in per.items() if r[k]), reverse=True)[:6] for k in keys}
    return dict(total=tot, per_object=per, worst=worst)


def hygiene_checks(chk, hy, blocker=True, ngon_max=0.05, degenerate_blocker=None):
    """U04 non-manifold, U05 flipped / inverted normals, U11 loose geometry, U12 n-gon ratio,
    U16 degenerate faces/edges (default: same severity as the others; zero-area bevel collapses are
    harmless on a render / bake-source mesh, so Stage 3 passes degenerate_blocker=False)."""
    t, w = hy["total"], hy["worst"]
    sev = "BLOCKER" if blocker else "WARN"
    chk.add("U04", sev, t["non_manifold"] == 0,
            f"{t['non_manifold']} non-manifold edges {w['non_manifold'] or ''}; {t['boundary']} open edges")
    chk.add("U05", sev, t["flipped"] + t["inverted"] == 0,
            f"flipped {t['flipped']}, inverted {t['inverted']} {(w['flipped'] + w['inverted'])[:6] or ''}")
    dsev = sev if degenerate_blocker is None else ("BLOCKER" if degenerate_blocker else "WARN")
    chk.add("U16", dsev, t["degenerate"] == 0, f"{t['degenerate']} degenerate faces/edges {w['degenerate'] or ''}")
    chk.add("U11", sev, t["loose"] == 0, f"{t['loose']} loose verts/edges {w['loose'] or ''}")
    chk.add("U12", "WARN", t["ngon_ratio"] <= ngon_max,
            f"n-gons {t['ngons']}/{t['faces']} faces = {t['ngon_ratio']:.1%} (max {ngon_max:.0%})")


def naming_problems(objs, suffix=None):
    """Names that break docs/02 (GROUP_Part..., no spaces / .001) or lack the stage suffix."""
    return [o.name for o in objs
            if not stages.NAME_RE.match(o.name) or (suffix and not o.name.endswith(suffix))]


def smoothing_problems(objs):
    """Hard-surface builders (plates, boxes, extrusions) carrying a Subdivision modifier (lesson 7)."""
    return [o.name for o in mesh_objects(objs)
            if o.get("wb_builder") in HARD_BUILDERS and any(m.type == "SUBSURF" for m in o.modifiers)]


def policy_checks(chk, objs, suffix=None):
    """N01 naming + stage suffix, H01 no subsurf on hard-surface builders."""
    bad = naming_problems(objs, suffix)
    chk.add("N01", "BLOCKER", not bad, bad[:8] or f"all names GROUP_Part{suffix or ''}")
    sm = smoothing_problems(objs)
    chk.add("H01", "BLOCKER", not sm, sm[:8] or "no subsurf on plates / boxes / extrusions")


def wall_thickness(objs, samples=3000):
    """(min wall thickness m, object): rays from face centres inward along -normal (evaluated)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    best = (math.inf, None)
    for o in mesh_objects(objs):
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        mw = o.matrix_world
        nm3 = mw.to_3x3().inverted().transposed()
        tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        polys = list(me.polygons)
        for p in polys[::max(1, len(polys) // samples)]:
            n = (nm3 @ p.normal).normalized()
            hit = tree.ray_cast(mw @ p.center - n * 1e-5, -n, 1.0)
            if hit[0] is not None and hit[3] < best[0]:
                best = (hit[3], o.name)
        eo.to_mesh_clear()
    return best


def print_checks(chk, objs, min_wall=0.001, hy=None):
    """P01 watertight (no open / non-manifold edges), P02 minimum wall thickness (3D printing)."""
    hy = hy or hygiene(objs)
    t = hy["total"]
    chk.add("P01", "BLOCKER", t["boundary"] == 0 and t["non_manifold"] == 0,
            f"open edges {t['boundary']} {hy['worst']['boundary'] or ''}, non-manifold {t['non_manifold']}")
    w, where = wall_thickness(objs)
    chk.add("P02", "BLOCKER", w >= min_wall, f"min wall {w * 1000:.2f} mm at {where} (min {min_wall * 1000:.1f} mm)")


def write_report(path, asset, chk, metrics, **extra):
    rep = dict(asset=asset, blender=bpy.app.version_string, summary=chk.summary(), metrics=metrics,
               checks=chk.items, **extra)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, default=str)
    print("[REPORT]", path, rep["summary"])
    return rep
