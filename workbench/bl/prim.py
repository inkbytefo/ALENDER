"""
Stage 1 PRIMITIVE builders: masses and proportions from landmark bounds, nothing else.
Same landmarks as the later stages, so a Stage 1 fix is a Stage 2/3 fix.

  box_px     bounding rectangle of a px outline, extruded across X        receivers, housings, cabins
  plate_px   px outline simplified to a few corners (Douglas-Peucker)     stocks, grips, panels
  cyl_px     cylinder between two px points (any direction), radius in m  barrels, tubes, legs
  wheel_px   cylinder along X at a px centre                              wheels, discs, knobs
  from_objects(objs, "bbox"|"hull")  crude stand-ins from finished parts  migration / fallback

All of them go through workbench.bl.mesh (idempotent names, UVs, builder tag).
"""
import bmesh
import bpy
from mathutils import Vector

from workbench import silhouette
from workbench.bl import mesh
from workbench.bl.mesh import _ref


def bounds_px(poly):
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    return min(us), min(vs), max(us), max(vs)


def box_px(name, coll, poly_or_bounds, hw, mat=None, ref=None, x0=None, x1=None, pad_px=0.0):
    """Bounding rectangle of a px outline (or (u0, v0, u1, v1)) extruded from -hw..hw (or x0..x1).
    A plate, not a world-axis box, so a photo tilt (RefMap theta) is respected."""
    b = poly_or_bounds if len(poly_or_bounds) == 4 and not isinstance(poly_or_bounds[0], (tuple, list)) \
        else bounds_px(poly_or_bounds)
    u0, v0, u1, v1 = b[0] - pad_px, b[1] - pad_px, b[2] + pad_px, b[3] + pad_px
    rect = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    return mesh.plate(name, coll, rect, -hw if x0 is None else x0, hw if x1 is None else x1, mat, ref=ref)


def plate_px(name, coll, poly, hw, mat=None, tol=6.0, ref=None, x0=None, x1=None):
    """Outline simplified to its main corners (tolerance tol px), extruded across X."""
    simp = silhouette.simplify(list(poly) + [poly[0]], tol)[:-1]
    if len(simp) < 3:
        simp = list(poly)
    return mesh.plate(name, coll, simp, -hw if x0 is None else x0, hw if x1 is None else x1, mat, ref=ref)


def cyl_px(name, coll, a_px, b_px, r, segs=8, mat=None, ref=None, x=0.0, r1=None):
    """Cylinder (cone with r1) from px point a to px point b at depth x; radii in metres."""
    R = _ref(ref)
    return mesh.cyl(name, coll, R.P3(*a_px, x), R.P3(*b_px, x), r, segs, mat, r1=r1)


def wheel_px(name, coll, center_px, r_px, hw, segs=12, mat=None, ref=None, x=0.0):
    """Cylinder along X (wheels, discs) at a px centre with a px radius, width 2*hw."""
    R = _ref(ref)
    c = Vector(R.P3(*center_px, x))
    rad = r_px / R.S
    return mesh.cyl(name, coll, c - Vector((hw, 0, 0)), c + Vector((hw, 0, 0)), rad, segs, mat)


def from_objects(objs, name_fn, coll, mode="bbox", mat=None):
    """Crude stand-ins for finished parts (evaluated, world space): mode 'bbox' = world-axis box,
    'hull' = convex hull. name_fn(obj) -> new name. Use to migrate an old project to Stage 1 or as
    a fallback when a part has no primitive builder yet."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        if o.type != "MESH":
            continue
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        pts = [o.matrix_world @ v.co for v in me.vertices]
        eo.to_mesh_clear()
        if not pts:
            continue
        m = mat or (o.data.materials[0].name if o.data.materials and o.data.materials[0] else None)
        if mode == "bbox":
            mn = Vector(map(min, *pts))
            mx = Vector(map(max, *pts))
            out.append(mesh.box(name_fn(o), coll, (mn + mx) / 2, mx - mn, m))
        else:
            bm = bmesh.new()
            vs = [bm.verts.new(p) for p in pts]
            bmesh.ops.convex_hull(bm, input=vs)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            out.append(mesh.finish(name_fn(o), bm, coll, m, smooth=False, builder="hull"))
    return out
