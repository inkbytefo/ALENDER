"""
Geometry helpers of PROP_AK_Rifle that the library does not have (yet): two-edge superellipse
lofts, merged rivet domes, merged rib tubes, the slant muzzle brake. All of them read pixels through
landmarks.P and end in workbench.bl.mesh builders, so they are deterministic and idempotent.
Builders live in parts.py.
"""
import math

import bmesh
from mathutils import Vector

import landmarks as L
from workbench import tables
from workbench.bl import mesh, mods


# ---------------------------------------------------------------------------- finishing / plates
def hard(ob, P, bevel=0.0012, segments=2):
    """Hard-surface finish at S3: bevel + weighted normals. Never subsurf plates."""
    if P["bevel"] and bevel:
        mods.bevel(ob, bevel, segments)
        mods.weighted_normal(ob)
    return ob


def plate(name, coll, poly, hw, mat, x0=None, x1=None, **kw):
    """px outline extruded across X: symmetric +-hw, or x0..x1 for one-sided parts."""
    return mesh.plate(name, coll, poly, -hw if x0 is None else x0, hw if x1 is None else x1, mat, **kw)


def smooth(poly, samples):
    """Catmull-Rom smoothed px polyline (removes the kinks of sparse measured points)."""
    return [(p.x, p.y) for p in mesh.catmull([Vector(q) for q in poly], samples)]


# ---------------------------------------------------------------------------- two-edge lofts
def ring_two(a_px, b_px, hw, n, e_a=2.6, e_b=2.6, grow=0.0, taper=1.0):
    """Superellipse ring in the plane through px points a (top / rear) and b, spanning X +-hw.
    e_a / e_b: exponent of the half towards a / b (2 = ellipse, higher = boxier).
    grow (m) inflates the ring in both directions (floorplates, lips).
    taper: width at b / width at a (wedge sections, e.g. a magazine narrowing towards the bullets)."""
    A, B = Vector(L.P(*a_px)), Vector(L.P(*b_px))
    mid, d = (A + B) / 2, (B - A) / 2
    h, dn = d.length, d.normalized()
    ring = []
    for k in range(n):
        t = 2 * math.pi * (k + 0.5) / n
        c, s = math.cos(t), math.sin(t)
        e = e_a if s >= 0 else e_b
        along = math.copysign(abs(s) ** (2.0 / e), s)            # +1 = a, -1 = b
        across = math.copysign(abs(c) ** (2.0 / e), c)
        p = mid - dn * (h + grow) * along
        w = (hw + grow) * (1.0 - (1.0 - taper) * (1.0 - along) / 2.0)
        ring.append(Vector((across * w, p.x, p.y)))
    return ring


def loft_pairs(name, coll, pairs, hws, n, mat, e_a=2.6, e_b=2.6, grow=0.0, taper=1.0, **kw):
    """Loft through one ring_two per (a_px, b_px) station pair."""
    rings = [ring_two(a, b, hw, n, e_a, e_b, grow, taper) for (a, b), hw in zip(pairs, hws)]
    return mesh.loft_rings(name, coll, rings, mat, **kw)


def pairs_between(top, bot, ut, ub, n, bias=1.0):
    """n station pairs between two px polylines: the top point runs ut[0]..ut[1], the bottom point
    ub[0]..ub[1] (different ranges = slanted ends). bias > 1 packs stations towards the start."""
    out = []
    for i in range(n):
        f = (i / (n - 1)) ** bias
        a, b = ut[0] + (ut[1] - ut[0]) * f, ub[0] + (ub[1] - ub[0]) * f
        out.append(((a, tables.polyline_v(top, a)), (b, tables.polyline_v(bot, b))))
    return out


def arc_sample(poly, n):
    """n px points evenly spaced by arc length along a px polyline."""
    pts = [Vector(p) for p in poly]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    tot = sum(seg)
    out = []
    for k in range(n):
        d = tot * k / (n - 1)
        i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]
            i += 1
        out.append(pts[i].lerp(pts[i + 1], min(1.0, d / seg[i]) if seg[i] else 0.0))
    return out


def ring_centre(ring):
    return sum(ring, Vector()) / len(ring)


def inflate(ring, d, shift=Vector()):
    """Ring pushed outwards by d (m) from its centre, then moved by shift."""
    c = ring_centre(ring)
    return [p + (p - c).normalized() * d + shift for p in ring]


# ---------------------------------------------------------------------------- merged small parts
def domes(name, coll, pts_px, x_face, r, h, segs, mat, outward=-1.0):
    """Many rivet heads (flattened domes) in ONE object on a face at X = x_face."""
    bm = bmesh.new()
    prof = [(r, 0.0), (r * 0.92, h * 0.45), (r * 0.62, h * 0.85), (0.0, h)]
    for (u, v) in pts_px:
        y, z = L.P(u, v)
        rings = []
        for (rr, hh) in prof:
            if rr == 0.0:
                rings.append([bm.verts.new((x_face + outward * hh, y, z))])
                continue
            rings.append([bm.verts.new((x_face + outward * hh, y + rr * math.cos(2 * math.pi * k / segs),
                                        z + rr * math.sin(2 * math.pi * k / segs))) for k in range(segs)])
        for i in range(len(rings) - 1):
            a_, b_ = rings[i], rings[i + 1]
            for k in range(segs):
                if len(b_) == 1:
                    bm.faces.new((a_[k], a_[(k + 1) % segs], b_[0]))
                else:
                    bm.faces.new((a_[k], a_[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
        bm.faces.new(list(reversed(rings[0])))
    return mesh.finish(name, bm, coll, mat, sharp_angle=60)


def beads(name, coll, paths, r, segs, mat):
    """Stamped ribs: several swept tubes with rounded-off ends, merged into ONE object."""
    bm = bmesh.new()
    for pts in paths:
        pts = [Vector(p) for p in pts]
        a0, a1 = (pts[0] - pts[1]).normalized(), (pts[-1] - pts[-2]).normalized()
        pts = ([pts[0] + a0 * r * 0.9, pts[0] + a0 * r * 0.5] + pts
               + [pts[-1] + a1 * r * 0.5, pts[-1] + a1 * r * 0.9])
        n = len(pts)
        tang = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
        end_scale = {0: 0.45, 1: 0.85, n - 2: 0.85, n - 1: 0.45}
        nrm, _ = mesh.frame_for(tang[0])
        rings = []
        for i in range(n):
            t = tang[i]
            nrm = (nrm - t * nrm.dot(t)).normalized()
            b = t.cross(nrm)
            rr = r * end_scale.get(i, 1.0)
            rings.append([bm.verts.new(pts[i] + rr * (math.cos(2 * math.pi * k / segs) * nrm
                                                     + math.sin(2 * math.pi * k / segs) * b))
                          for k in range(segs)])
        for i in range(n - 1):
            for k in range(segs):
                bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs],
                              rings[i + 1][k]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return mesh.finish(name, bm, coll, mat, sharp_angle=70)


def slant_brake(name, coll, y0, y_front, r, bore_r, segs, mat):
    """AKM slant compensator: tube around the bore (Y) from y0 to a front cut y_front(z) that depends
    on the height only (near-vertical upper face, long lower lip)."""
    bm = bmesh.new()

    def ring(rad, yfun):
        return [bm.verts.new((rad * math.cos(2 * math.pi * i / segs),
                              yfun(rad * math.sin(2 * math.pi * i / segs)),
                              rad * math.sin(2 * math.pi * i / segs))) for i in range(segs)]
    outer_back = ring(r, lambda z: y0)
    outer_front = ring(r, y_front)
    inner_front = ring(bore_r, y_front)
    inner_back = ring(bore_r, lambda z: y0)
    for A, B in ((outer_back, outer_front), (outer_front, inner_front), (inner_front, inner_back),
                 (inner_back, outer_back)):
        for i in range(segs):
            bm.faces.new((A[i], A[(i + 1) % segs], B[(i + 1) % segs], B[i]))
    return mesh.finish(name, bm, coll, mat, sharp_angle=35)
