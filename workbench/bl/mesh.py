"""
Procedural mesh builders (bmesh, context-free, deterministic).

Every builder ends in `finish()` which: merges doubles, recalculates normals, writes a box
UV map, sets smooth shading with auto-sharp edges (angle), replaces an existing object of the
same name (so builds are idempotent) and assigns one material.

Choose a builder by shape (docs/04_MODELING_TOOLKIT.md):
  box        blocks, brackets, housings            cyl        rods, axles, pistons, cones
  tube       pipes, frames, cables, springs        lathe      wheels, tyres, discs, lamps, bottles
  plate      photo outline extruded across X      loft_px    tanks, seats, fuselages, bodies
  loft_rings arbitrary ring lists (custom sections) multi_cyl many small cylinders as ONE object
  grid       ground / display planes              from_pydata raw verts/faces
"""
import math
import bpy
import bmesh
from mathutils import Vector

from workbench.tables import interp, polyline_v, lin   # re-exported for convenience
from workbench.bl.scene import coll

_REF = None


def set_ref(ref):
    """Default RefMap used by photo-driven builders (plate, loft_px) when ref= is omitted."""
    global _REF
    _REF = ref


def _ref(ref):
    r = ref or _REF
    if r is None:
        raise ValueError("photo-driven builder needs a RefMap: pass ref= or call mesh.set_ref()")
    return r


# ----------------------------------------------------------------------------- core
def box_uv(bm, scale=0.5):
    """Box projection, `scale` UV units per metre. Continuous (no % 1 wrap: a wrapped face would
    stretch across the whole texture - lesson 28); tiling textures repeat on their own."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = (co[a] * scale, co[b] * scale)


def finish(name, bm, collection, mat=None, smooth=True, sharp_angle=40.0, props=None, builder=None):
    """bmesh -> object: UVs, outward normals, auto-sharp edges, material, idempotent name.
    builder (e.g. "plate") is stored as ob["wb_builder"] for the smoothing-policy check H01."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    box_uv(bm)
    lim = math.radians(sharp_angle)
    for f in bm.faces:
        f.smooth = smooth
    for e in bm.edges:
        e.smooth = len(e.link_faces) == 2 and e.calc_face_angle(0.0) < lim
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    if mat is not None:
        me.materials.append(bpy.data.materials[mat])
    if builder:
        ob["wb_builder"] = builder
    for k, v in (props or {}).items():
        ob[k] = v
    return ob


def frame_for(t):
    """Two unit vectors perpendicular to direction t."""
    t = Vector(t).normalized()
    ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    n = t.cross(ref).normalized()
    return n, t.cross(n).normalized()


def catmull(points, samples):
    """Catmull-Rom resample through control points (samples per segment)."""
    pts = [Vector(p) for p in points]
    if samples <= 1 or len(pts) < 3:
        return pts
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


# ----------------------------------------------------------------------------- primitives
def box(name, collection, center, size, mat=None, rot=None, **kw):
    """Axis box of full `size` at `center`; rot = 3x3 Matrix applied about its centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return finish(name, bm, collection, mat, smooth=False, **{"builder": "box", **kw})


def cyl(name, collection, p0, p1, r, segs=12, mat=None, r1=None, caps=True, **kw):
    """Cylinder (or cone frustum when r1 given) from p0 to p1."""
    return tube(name, collection, [p0, p1], r if r1 is None else [r, r1], segs, mat,
                smooth_path=False, caps=caps, **{"builder": "cyl", **kw})


def tube(name, collection, points, r, segs=12, mat=None, smooth_path=True, samples=4,
         caps=True, **kw):
    """Sweep a circle along a polyline with parallel-transport frames (no twisting).
    r may be a scalar or a list (interpolated along the path)."""
    pts = catmull(points, samples) if smooth_path else [Vector(p) for p in points]
    n = len(pts)
    radii = r if isinstance(r, (list, tuple)) else [r] * n
    if len(radii) != n:
        rr = []
        for i in range(n):
            f = i / (n - 1) * (len(radii) - 1)
            a = int(min(f, len(radii) - 2))
            rr.append(radii[a] + (radii[a + 1] - radii[a]) * (f - a))
        radii = rr
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tangents.append(t.normalized())
    nrm, _ = frame_for(tangents[0])
    bm = bmesh.new()
    rings = []
    for i in range(n):
        t = tangents[i]
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bin_ = t.cross(nrm)
        rings.append([bm.verts.new(pts[i] + radii[i] * (math.cos(2 * math.pi * k / segs) * nrm
                                                       + math.sin(2 * math.pi * k / segs) * bin_))
                      for k in range(segs)])
    for i in range(n - 1):
        for k in range(segs):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % segs],
                          rings[i + 1][(k + 1) % segs], rings[i + 1][k]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return finish(name, bm, collection, mat, **{"builder": "tube", **kw})


def helix(p0, p1, radius, turns, steps_per_turn=16, start=0.0, end=1.0):
    """Points of a helix around segment p0->p1 (springs, threads). Feed to tube(smooth_path=False)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    n1, n2 = frame_for(d)
    steps = int(turns * steps_per_turn)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = 2 * math.pi * turns * t
        pts.append(p0 + d * (start + (end - start) * t) + radius * (math.cos(a) * n1 + math.sin(a) * n2))
    return pts


def lathe(name, collection, center, profile, segs=24, mat=None, closed=True, axis="X", caps=True, **kw):
    """Revolve profile [(radius, axial_offset), ...] around axis X|Y|Z through center.
    closed=True joins last profile point back to the first (solid sections: tyres, rims)."""
    c = Vector(center)
    bm = bmesh.new()
    rings = []
    for (rad, lat) in profile:
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ca, sa = rad * math.cos(a), rad * math.sin(a)
            off = {"X": (lat, ca, sa), "Y": (ca, lat, sa), "Z": (ca, sa, lat)}[axis]
            ring.append(bm.verts.new(c + Vector(off)))
        rings.append(ring)
    m = len(rings)
    for i in range(m if closed else m - 1):
        a_, b_ = rings[i], rings[(i + 1) % m]
        for k in range(segs):
            bm.faces.new((a_[k], a_[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
    if not closed and caps:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    return finish(name, bm, collection, mat, **{"builder": "lathe", **kw})


def multi_cyl(name, collection, specs, segs=8, mat=None):
    """Many small cylinders [(p0, p1, r), ...] merged into ONE object (drill holes, studs)."""
    bm = bmesh.new()
    for (p0, p1, r) in specs:
        p0, p1 = Vector(p0), Vector(p1)
        n1, n2 = frame_for(p1 - p0)
        ra = [bm.verts.new(p0 + r * (math.cos(2 * math.pi * k / segs) * n1
                                     + math.sin(2 * math.pi * k / segs) * n2)) for k in range(segs)]
        rb = [bm.verts.new(v.co + (p1 - p0)) for v in ra]
        for k in range(segs):
            bm.faces.new((ra[k], ra[(k + 1) % segs], rb[(k + 1) % segs], rb[k]))
        bm.faces.new(list(reversed(ra)))
        bm.faces.new(rb)
    return finish(name, bm, collection, mat, smooth=False, builder="multi_cyl")


def extrude_polys(name, collection, polys3d_pairs, mat=None, **kw):
    """Several closed prisms in ONE object: [(front_face_pts, back_face_pts), ...]."""
    bm = bmesh.new()
    for fa, fb in polys3d_pairs:
        a = [bm.verts.new(Vector(p)) for p in fa]
        b = [bm.verts.new(Vector(p)) for p in fb]
        n = len(a)
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    return finish(name, bm, collection, mat, smooth=False, **{"builder": "extrude", **kw})


def grid(name, collection, size=1.0, mat=None):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    return finish(name, bm, collection, mat, smooth=False, builder="grid")


def from_pydata(name, collection, verts, faces, mat=None, **kw):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(v)) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    return finish(name, bm, collection, mat, **{"builder": "pydata", **kw})


# ----------------------------------------------------------------------------- photo-driven
def plate(name, collection, poly_px, x0, x1, mat=None, ref=None, **kw):
    """Reference-photo outline polygon (px) extruded across X from x0 to x1.
    The workhorse for side plates, panels, engine blocks, brackets, swingarms."""
    r = _ref(ref)
    pa = [r.P3(u, v, x0) for (u, v) in poly_px]
    pb = [r.P3(u, v, x1) for (u, v) in poly_px]
    return extrude_polys(name, collection, [(pa, pb)], mat, **{"builder": "plate", **kw})


def superellipse_ring(cx_u, v_top, v_bot, half_w, n, e_top=2.6, e_bot=4.0, widest=0.55):
    """Ring of (x, u, v): rounded section between v_top/v_bot (px) with half width (m).
    e_* exponents: 2 = ellipse, higher = boxier. widest = height fraction (from bottom)
    where the section is widest."""
    pts = []
    v_mid = v_top + (v_bot - v_top) * (1.0 - widest)
    for k in range(n):
        a = 2 * math.pi * k / n
        ca, sa = math.cos(a), math.sin(a)
        x = half_w * math.copysign(abs(ca) ** (2.0 / (e_top if sa >= 0 else e_bot)), ca)
        if sa >= 0:
            v = v_mid - (v_mid - v_top) * abs(sa) ** (2.0 / e_top)
        else:
            v = v_mid + (v_bot - v_mid) * abs(sa) ** (2.0 / e_bot)
        pts.append((x, cx_u, v))
    return pts


def loft_rings(name, collection, rings, mat=None, caps=True, **kw):
    """Closed loft through rings of equal vertex count [[(x,y,z), ...], ...]."""
    bm = bmesh.new()
    vr = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(vr[0])
    for i in range(len(vr) - 1):
        for k in range(n):
            bm.faces.new((vr[i][k], vr[i][(k + 1) % n], vr[i + 1][(k + 1) % n], vr[i + 1][k]))
    if caps:
        bm.faces.new(list(reversed(vr[0])))
        bm.faces.new(vr[-1])
    return finish(name, bm, collection, mat, **{"builder": "loft", **kw})


def loft_px(name, collection, stations, n, mat=None, ref=None, **kw):
    """Side-silhouette loft. stations: [(u, v_top, v_bot, half_w, e_top, e_bot, widest), ...]
    Build stations from photo polylines with tables.polyline_v + a half-width table."""
    r = _ref(ref)
    rings = [[r.P3(uu, vv, x) for (x, uu, vv) in superellipse_ring(u, vt, vb, hw, n, et, eb, wd)]
             for (u, vt, vb, hw, et, eb, wd) in stations]
    return loft_rings(name, collection, rings, mat, **kw)
