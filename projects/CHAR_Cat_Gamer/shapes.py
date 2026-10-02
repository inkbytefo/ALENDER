"""
Front-view organic builders for CHAR_Cat_Gamer (project-local until proven; docs/04 "Extending").

  row_loft   measured rows (v, uL, uR) px -> stack of superellipse rings: width from the photo,
             depth from a (guessed) table. Seen from the reference camera the silhouette IS the rows.
  c_shell    like row_loft but an open "C" shell with thickness (vest with a front opening)
  px_tube    mesh.tube through (u, v, depth, r_px) points
  blob       superellipsoid (paws, eyes, muzzle)
"""
import math
from mathutils import Vector

import landmarks as L
from workbench.bl import mesh


def val(x, v):
    return L.interp(x, v) if isinstance(x, (list, tuple)) else x


def smooth_rows(rows, w=1):
    if w <= 0:
        return list(rows)
    out = []
    for i, r in enumerate(rows):
        seg = rows[max(0, i - w):i + w + 1]
        out.append((r[0], sum(s[1] for s in seg) / len(seg), sum(s[2] for s in seg) / len(seg)))
    return out


def pick_rows(rows, n):
    """n rows resampled evenly in v (ends kept), linear interpolation of the edges."""
    if not n or n >= len(rows):
        return list(rows)
    left = [(r[0], r[1]) for r in rows]
    right = [(r[0], r[2]) for r in rows]
    v0, v1 = rows[0][0], rows[-1][0]
    vs = [v0 + (v1 - v0) * i / (n - 1.0) for i in range(n)]
    return [(v, L.interp(left, v), L.interp(right, v)) for v in vs]


def _spow(c, e):
    return math.copysign(abs(c) ** (2.0 / e), c)


def _round(v, v0, v1, top, bot):
    k = 1.0
    if top and v - v0 < top:
        k = min(k, math.sqrt(max(0.0, 1.0 - (1.0 - (v - v0) / top) ** 2)))
    if bot and v1 - v < bot:
        k = min(k, math.sqrt(max(0.0, 1.0 - (1.0 - (v1 - v) / bot) ** 2)))
    return max(k, 0.3)


def row_loft(name, coll, rows, depth_c, depth_hw, ring=16, mat=None, n_rows=None, round_top=0,
             round_bot=0, exp=2.0, smooth=1, round_width=True, **kw):
    rows = pick_rows(smooth_rows(rows, smooth), n_rows)
    v0, v1 = rows[0][0], rows[-1][0]
    rings = []
    for (v, ul, ur) in rows:
        k = _round(v, v0, v1, round_top, round_bot)
        cu, a = (ul + ur) / 2.0, (ur - ul) / 2.0 * (k if round_width else 1.0)
        dc, b = val(depth_c, v), val(depth_hw, v) * k
        rings.append([L.P3(cu + a * _spow(math.cos(2 * math.pi * j / ring), exp), v,
                           dc + b * _spow(math.sin(2 * math.pi * j / ring), exp)) for j in range(ring)])
    return mesh.loft_rings(name, coll, rings, mat, sharp_angle=75.0, **kw)


def c_shell(name, coll, rows, gaps, depth_c, depth_hw, ring=16, mat=None, n_rows=None, thick_px=5.0,
            thick_d=0.004):
    """Open shell: outer superellipse arc from the right gap edge round the back to the left gap edge,
    then the inner arc back. gaps [(v, u_gap_left, u_gap_right)] px on the camera side."""
    rows = pick_rows(rows, n_rows)
    gl = [(g[0], g[1]) for g in gaps]
    gr = [(g[0], g[2]) for g in gaps]
    verts, faces, n = [], [], ring + 1
    for (v, ul, ur) in rows:
        cu, a = (ul + ur) / 2.0, (ur - ul) / 2.0
        dc, b = val(depth_c, v), val(depth_hw, v)
        t_r = -math.acos(max(-0.97, min(0.97, (L.interp(gr, v) - cu) / a)))
        t_l = -math.acos(max(-0.97, min(0.97, (L.interp(gl, v) - cu) / a))) + 2 * math.pi
        ang = [t_r + (t_l - t_r) * j / ring for j in range(n)]
        outer = [L.P3(cu + a * math.cos(t), v, dc + b * math.sin(t)) for t in ang]
        inner = [L.P3(cu + (a - thick_px) * math.cos(t), v, dc + (b - thick_d) * math.sin(t)) for t in ang]
        verts += outer + inner[::-1]
    m = 2 * n
    for i in range(len(rows) - 1):
        for j in range(m):
            a0, a1 = i * m + j, i * m + (j + 1) % m
            faces.append((a0, a1, a1 + m, a0 + m))
    for i in (0, len(rows) - 1):                       # end caps: quad strip between outer and inner arc
        for j in range(n - 1):
            q = (i * m + j, i * m + j + 1, i * m + m - 2 - j, i * m + m - 1 - j)
            faces.append(q if i else q[::-1])
    return mesh.from_pydata(name, coll, verts, faces, mat, sharp_angle=75.0, builder="loft")


def px_tube(name, coll, pts, segs=12, mat=None, samples=2, taper_end=None, **kw):
    """pts [(u, v, depth_m, r_px)]; radius converted at the reference scale."""
    p3 = [L.P3(u, v, d) for (u, v, d, r) in pts]
    radii = [r / L.S for (u, v, d, r) in pts]
    cm = mesh.catmull(p3, samples)
    rr = []
    for i in range(len(cm)):
        f = i / (len(cm) - 1.0) * (len(radii) - 1)
        a = int(min(f, len(radii) - 2))
        rr.append(radii[a] + (radii[a + 1] - radii[a]) * (f - a))
    return mesh.tube(name, coll, cm, rr, segs, mat, smooth_path=False, sharp_angle=75.0, **kw)


def blob_bottom(lat, exp_z=2.0):
    """fraction of rz at which a blob's lowest ring sits (end caps are small flats, not poles)."""
    return _spow(math.sin(math.pi / 2 - math.pi * 0.35 / (lat + 0.7)), exp_z)


def blob(name, coll, center, radii, ring=12, lat=6, mat=None, exp=2.0, rot=None, exp_z=2.0, **kw):
    """Superellipsoid at `center` with radii (rx, ry, rz); rings stacked along local Z, small end caps."""
    c = Vector(center)
    rings = []
    for i in range(lat + 1):
        phi = -math.pi / 2 + math.pi * (i + 0.35) / (lat + 0.7)
        rr, z = _spow(math.cos(phi), exp_z), _spow(math.sin(phi), exp_z)
        ring_pts = []
        for j in range(ring):
            t = 2 * math.pi * j / ring
            p = Vector((radii[0] * rr * _spow(math.cos(t), exp), radii[1] * rr * _spow(math.sin(t), exp),
                        radii[2] * z))
            ring_pts.append(c + (rot @ p if rot is not None else p))
        rings.append(ring_pts)
    return mesh.loft_rings(name, coll, rings, mat, sharp_angle=75.0, **kw)
