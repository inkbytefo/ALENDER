"""
Part builders for PROP_AK_Rifle. Every builder takes a LOD profile (LOW = Stage 1, HIGH = Stage 2)
and reads ALL placement from landmarks.py (pixels). Library map: docs/04_MODELING_TOOLKIT.md.

Groups: RECV_ (receiver), SIGHT_, BARREL_, GAS_, FSB_ (front sight), MUZZLE_, WOOD_, GRIP_, MAG_,
CTRL_ (trigger, guard, safety, mag catch, charging handle), FASTENER_.
Right-side-only parts (photo side) sit at -X. LOW objects get _LOW via nm().
"""
import math
import bmesh
from mathutils import Vector

import landmarks as L
from workbench import tables
from workbench.bl import mesh, mods

mesh.set_ref(L.REF)

LOW = dict(name="LOW", ring=12, lathe=12, stations=8, mag_st=10, bevel=False, detail=False,
           C_PRIMARY="02_LOW_PRIMARY", C_SECONDARY="03_LOW_SECONDARY", C_MECH="04_LOW_MECHANICAL",
           C_DETAIL="04_LOW_MECHANICAL")
HIGH = dict(name="HIGH", ring=28, lathe=28, stations=26, mag_st=26, bevel=True, detail=True,
            C_PRIMARY="05_HIGH_BODY", C_SECONDARY="05_HIGH_BODY", C_MECH="06_HIGH_MECHANICAL",
            C_DETAIL="07_DETAILS")

PALETTE = {                                             # <= 4 materials for a prop
    "MAT_STEEL_DARK": ((0.030, 0.031, 0.034), 0.85, 0.42),      # parkerized / blued steel
    "MAT_STEEL_BRIGHT": ((0.50, 0.50, 0.51), 1.0, 0.22),        # bolt carrier (chrome-ish)
    "MAT_WOOD_LAMINATE": ((0.40, 0.11, 0.03), 0.0, 0.32),       # lacquered orange laminate
    "MAT_POLYMER": ((0.028, 0.028, 0.030), 0.0, 0.62),          # pistol grip
}
STEEL, BRIGHT, WOOD, POLY = "MAT_STEEL_DARK", "MAT_STEEL_BRIGHT", "MAT_WOOD_LAMINATE", "MAT_POLYMER"

CRITICAL_PAIRS = [("MAG_", "GRIP_"), ("MAG_", "CTRL_Trigger"), ("MAG_", "CTRL_MagCatch"),
                  ("MAG_", "CTRL_Guard"), ("CTRL_Trigger", "CTRL_Guard"), ("GRIP_", "CTRL_Trigger"),
                  ("WOOD_HandguardUpper", "WOOD_HandguardLower"), ("CTRL_Safety", "CTRL_Charging"),
                  ("CTRL_Safety", "GRIP_"), ("WOOD_Stock", "GRIP_")]


def nm(lod, name):
    return name if lod["name"] == "HIGH" else name + "_LOW"


def hard(ob, lod, bevel=0.0012, segments=2):
    """hard-surface finish at HIGH: bevel + weighted normals. Never subsurf plates."""
    if lod["bevel"] and bevel:
        mods.bevel(ob, bevel, segments)
        mods.weighted_normal(ob)
    return ob


def Y(u):
    return L.P(u, L.BORE_V)[0]


def Z(v):
    return L.P(L.ANCHOR_PX[0], v)[1]


# ============================================================================ geometry helpers
def _arc_sample(poly, n):
    """n points evenly spaced by arc length along a px polyline."""
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
        f = min(1.0, d / seg[i]) if seg[i] else 0.0
        out.append(pts[i].lerp(pts[i + 1], f))
    return out


def _ring_two(a_px, b_px, hw, n, e_a=2.6, e_b=2.6, grow=0.0):
    """Superellipse ring in the plane through px points a (top/rear) and b, spanning X +-hw.
    grow (m) inflates the ring in both directions (floorplates, lips)."""
    A = Vector(L.P(*a_px))
    B = Vector(L.P(*b_px))
    mid = (A + B) / 2
    d = (B - A) / 2
    h = d.length
    dn = d.normalized()
    ring = []
    for k in range(n):
        t = 2 * math.pi * (k + 0.5) / n
        c, s = math.cos(t), math.sin(t)
        e = e_a if s >= 0 else e_b
        along = math.copysign(abs(s) ** (2.0 / e), s)            # +1 = a, -1 = b
        across = math.copysign(abs(c) ** (2.0 / e), c)
        p = mid - dn * (h + grow) * along
        ring.append(Vector((across * (hw + grow), p.x, p.y)))
    return ring


def loft_pairs(name, coll, pairs, hws, n, mat, e_a=2.6, e_b=2.6, caps=True, grow=0.0, **kw):
    rings = [_ring_two(a, b, hw, n, e_a, e_b, grow) for (a, b), hw in zip(pairs, hws)]
    return mesh.loft_rings(name, coll, rings, mat, caps=caps, **kw)


def pairs_by_u(top, bot, u0t, u1t, u0b, u1b, n):
    """station pairs: top point at u_t, bottom point at u_b (slanted ends allowed)."""
    out = []
    for i in range(n):
        f = i / (n - 1)
        ut, ub = u0t + (u1t - u0t) * f, u0b + (u1b - u0b) * f
        out.append(((ut, tables.polyline_v(top, ut)), (ub, tables.polyline_v(bot, ub))))
    return out


def plate(name, coll, poly, hw, mat, x0=None, x1=None, **kw):
    a = -hw if x0 is None else x0
    b = hw if x1 is None else x1
    return mesh.plate(name, coll, poly, a, b, mat, **kw)


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


def tubes(name, coll, paths, r, segs, mat, samples=3, taper=False):
    """Several swept tubes merged into ONE object (magazine ribs)."""
    bm = bmesh.new()
    for pts in paths:
        pts = mesh.catmull(pts, samples)
        if taper:                              # short rounded caps instead of flat cut ends
            a0 = (pts[0] - pts[1]).normalized()
            a1 = (pts[-1] - pts[-2]).normalized()
            pts = ([pts[0] + a0 * r * 0.9, pts[0] + a0 * r * 0.5] + list(pts)
                   + [pts[-1] + a1 * r * 0.5, pts[-1] + a1 * r * 0.9])
        n = len(pts)
        tang = []
        for i in range(n):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            tang.append(t)
        nrm, _ = mesh.frame_for(tang[0])
        rings = []
        for i in range(n):
            t = tang[i]
            nrm = (nrm - t * nrm.dot(t)).normalized()
            b = t.cross(nrm)
            rr = r * ({0: 0.45, 1: 0.85, n - 2: 0.85, n - 1: 0.45}.get(i, 1.0) if taper else 1.0)
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


def slant_brake(name, coll, u0, u_top, u_bot, r, bore_r, segs, mat):
    """AKM slant compensator: tube around Y whose front face is a plane (long lower lip)."""
    y0, yt, yb = Y(u0), Y(u_top), Y(u_bot)
    ymid, k = (yt + yb) / 2, (yt - yb) / (2 * r)
    bm = bmesh.new()

    def ring(rad, yfun):
        out = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            x, z = rad * math.cos(a), rad * math.sin(a)
            out.append(bm.verts.new((x, yfun(z), z)))
        return out
    ob_ = ring(r, lambda z: y0)
    of_ = ring(r, lambda z: ymid + z * k)
    if_ = ring(bore_r, lambda z: ymid + z * k)
    ib_ = ring(bore_r, lambda z: y0)
    for A, B in ((ob_, of_), (of_, if_), (if_, ib_), (ib_, ob_)):
        for i in range(segs):
            bm.faces.new((A[i], A[(i + 1) % segs], B[(i + 1) % segs], B[i]))
    return mesh.finish(name, bm, coll, mat, sharp_angle=35)


# ============================================================================ builders
def receiver(lod):
    C = lod["C_PRIMARY"]
    out = []
    body = plate(nm(lod, "RECV_Body"), C, L.RECV_BODY, L.HW_RECV, STEEL)
    out.append(hard(body, lod, 0.0015))
    u0, u1 = L.RECV_END_U
    end = plate(nm(lod, "RECV_RearTrunnion"), C, [(u0, 270), (u1, 270), (u1, 342), (u0, 342)],
                L.HW_RECV + 0.0008, STEEL)
    out.append(hard(end, lod, 0.0012))
    n = lod["stations"]
    us = [441 + (800 - 441) * (i / (n - 1)) ** 0.7 for i in range(n)]      # denser at the round rear
    pairs = [((u, tables.polyline_v(L.COVER_TOP, u)), (u, tables.polyline_v(L.COVER_BOT, u))) for u in us]
    cover = loft_pairs(nm(lod, "RECV_DustCover"), C, pairs, [L.HW_COVER] * n, lod["ring"], STEEL,
                       e_a=2.4, e_b=7.0, sharp_angle=50)
    out.append(cover)
    # left wall above the port level (the port is only on the right side)
    lw = plate(nm(lod, "RECV_WallLeft"), C, [(698, 249), (832, 249), (832, 268), (698, 270)], 0,
               STEEL, x0=0.0, x1=L.HW_RECV)
    out.append(hard(lw, lod, 0.001))
    rs = plate(nm(lod, "SIGHT_RearBase"), C, L.REAR_SIGHT_BASE, L.HW_RSIGHT, STEEL)
    out.append(hard(rs, lod, 0.0012))
    leaf = plate(nm(lod, "SIGHT_RearLeaf"), lod["C_SECONDARY"], L.REAR_SIGHT_LEAF, L.HW_LEAF, STEEL)
    out.append(hard(leaf, lod, 0.0006))
    y, z = L.P(*L.REAR_SIGHT_SLIDER_PX)
    sl = mesh.box(nm(lod, "SIGHT_Slider"), lod["C_SECONDARY"], (0, y, z + 0.0005),
                  (2 * L.HW_LEAF + 0.004, 0.009, 0.006), STEEL)
    out.append(hard(sl, lod, 0.0008))
    return out


def barrel(lod):
    C = lod["C_PRIMARY"]
    s = lod["lathe"]
    prof = [(L.m(r), Y(u)) for (u, r) in L.BARREL]
    out = [mesh.lathe(nm(lod, "BARREL_Main"), C, (0, 0, 0), prof, s, STEEL, closed=False, axis="Y",
                      sharp_angle=30)]
    gb = plate(nm(lod, "GAS_Block"), C, L.GAS_BLOCK, L.HW_GASBLOCK, STEEL)
    out.append(hard(gb, lod, 0.002, 3))
    lug = plate(nm(lod, "GAS_BayonetLug"), lod["C_SECONDARY"], L.BAYONET_LUG, 0.004, STEEL)
    out.append(hard(lug, lod, 0.0008))
    g = L.GAS_TUBE
    zt = Z(g["v"])
    out.append(mesh.cyl(nm(lod, "GAS_Tube"), C, (0, Y(918), zt), (0, Y(g["u1"]), zt), L.m(g["r"]), s,
                        STEEL))
    if lod["detail"]:
        a, b = L.GAS_TUBE_RING_U
        out.append(mesh.cyl(nm(lod, "GAS_TubeRing"), lod["C_DETAIL"], (0, Y(a), zt), (0, Y(b), zt),
                            L.m(g["r"]) + 0.0007, s, STEEL))
    # front sight: base block around the barrel + two protective ears + a thin centre post
    base = [(u, min(v, L.FSB_EAR_BASE_V)) for (u, v) in L.FSB]
    out.append(hard(plate(nm(lod, "FSB_Body"), C, base, L.HW_FSB, STEEL), lod, 0.0015))
    y, z = L.P(*L.FSB_HOLE_PX)
    import bpy
    for side in (-1, 1):
        x0, x1 = sorted((side * L.HW_FSB, side * (L.HW_FSB - L.FSB_EAR_T)))
        ear = plate(nm(lod, "FSB_Ear_" + ("R" if side < 0 else "L")), C,
                    [p for p in L.FSB if p[1] <= L.FSB_EAR_BASE_V + 2] + [(1388, L.FSB_EAR_BASE_V + 2),
                                                                          (1346, L.FSB_EAR_BASE_V + 2)],
                    0, STEEL, x0=x0, x1=x1)
        cut = mesh.cyl("TEMP_FSB_Hole", C, (-0.02, y, z), (0.02, y, z), L.m(L.FSB_HOLE_R_PX), 16, STEEL)
        mods.boolean(ear, cut, apply=True)
        bpy.data.objects.remove(cut, do_unlink=True)
        out.append(hard(ear, lod, 0.0007))
    out.append(hard(plate(nm(lod, "FSB_Post"), C, L.FSB_POST, 0.0012, STEEL), lod, 0.0005))
    b = L.BRAKE
    cu0, cu1, cr = b["collar"]
    out.append(mesh.cyl(nm(lod, "MUZZLE_Collar"), lod["C_SECONDARY"], (0, Y(cu0), 0), (0, Y(cu1), 0),
                        L.m(cr), s, STEEL))
    out.append(slant_brake(nm(lod, "MUZZLE_Brake"), lod["C_SECONDARY"], b["u0"], b["top_end"],
                           b["bot_end"], L.m(b["r"]), L.m(b["bore"]), s, STEEL))
    return out


def woodwork(lod):
    C = lod["C_PRIMARY"]
    n, rn = lod["stations"], lod["ring"]
    out = []
    # lower handguard: flat-ish top channel, rounded belly, finger swell at the rear
    pairs = pairs_by_u(L.HG_LOWER_TOP, L.HG_LOWER_BOT, 852, 1086, 852, 1086, n)
    hws = [tables.interp(L.HW_HG_LOWER, a[0]) for a, _ in pairs]
    out.append(loft_pairs(nm(lod, "WOOD_HandguardLower"), C, pairs, hws, rn, WOOD, e_a=5.0, e_b=2.6,
                          sharp_angle=80))
    pairs = pairs_by_u(L.HG_UPPER_TOP, L.HG_UPPER_BOT, 935, 1084, 935, 1084, max(6, n // 2))
    hws = [tables.interp(L.HW_HG_UPPER, a[0]) for a, _ in pairs]
    out.append(loft_pairs(nm(lod, "WOOD_HandguardUpper"), C, pairs, hws, rn, WOOD, e_a=2.3, e_b=4.5,
                          sharp_angle=80))
    cap = plate(nm(lod, "RECV_HandguardRearCap"), lod["C_SECONDARY"], L.HG_REAR_CAP, 0.0150, STEEL)
    out.append(hard(cap, lod, 0.002, 3))
    band = plate(nm(lod, "RECV_HandguardBand"), lod["C_SECONDARY"], L.HG_FRONT_BAND, 0.0195, STEEL)
    out.append(hard(band, lod, 0.002, 3))
    return out


# ============================================================================ buttstock (v2)
def _smooth(poly, samples):
    """Catmull-Rom smoothed px polyline (removes kinks of hand-measured points)."""
    return [(p.x, p.y) for p in mesh.catmull([Vector(q) for q in poly], samples)]


def _ring_centre(ring):
    return sum(ring, Vector()) / len(ring)


def _inflate(ring, d, shift=Vector()):
    c = _ring_centre(ring)
    return [p + (p - c).normalized() * d + shift for p in ring]


def buttstock(lod):
    """AKM laminated stock: straight top with a shallow comb dip, straight belly rising to the
    wrist, slab sides with rounded top/bottom, slanted butt; steel buttplate that wraps 3 mm onto
    the wood, with horizontal grip ribs, cleaning-kit trapdoor and two screws on its back face."""
    C = lod["C_PRIMARY"]
    n, rn = lod["stations"] + 10, lod["ring"]
    top = _smooth(L.STOCK_TOP, 4 if lod["detail"] else 1)
    bot = _smooth(L.STOCK_BOT, 4 if lod["detail"] else 1)
    (ut0, ub0), u1 = L.STOCK_BUTT_U, L.STOCK_FRONT_U
    pairs = []
    for i in range(n):
        f = (i / (n - 1)) ** 1.15                      # a bit denser at the butt
        ut, ub = ut0 + (u1 - ut0) * f, ub0 + (u1 - ub0) * f
        pairs.append(((ut, tables.polyline_v(top, ut)), (ub, tables.polyline_v(bot, ub))))
    rings = []
    for (a, b) in pairs:
        u = (a[0] + b[0]) / 2
        rings.append(_ring_two(a, b, tables.interp(L.HW_STOCK, u), rn, L.STOCK_E_TOP, L.STOCK_E_BOT))
    out = [mesh.loft_rings(nm(lod, "WOOD_Stock"), C, rings, WOOD, sharp_angle=80)]

    # buttplate: loft of inflated copies of the butt ring (wrap onto the wood -> back face)
    r0 = rings[0]
    axis = (_ring_centre(rings[1]) - _ring_centre(r0)).normalized()        # points forward (-Y)
    back = -axis
    t = L.BUTTPLATE_T
    bp_rings = [_inflate(r0, 0.0006, axis * L.BUTTPLATE_WRAP), _inflate(r0, 0.0009),
                _inflate(r0, 0.0009, back * t * 0.6), _inflate(r0, 0.0002, back * t)]
    out.append(hard(mesh.loft_rings(nm(lod, "WOOD_ButtPlate"), lod["C_SECONDARY"], bp_rings, STEEL,
                                    sharp_angle=60), lod, 0.0006))
    if lod["detail"]:
        c = _ring_centre(r0) + back * t
        up = (Vector(L.P3(*pairs[0][0])) - Vector(L.P3(*pairs[0][1]))).normalized()
        up = (up - back * up.dot(back)).normalized()
        xa = Vector((1, 0, 0))
        h = (Vector(L.P3(*pairs[0][0])) - Vector(L.P3(*pairs[0][1]))).length / 2
        hw = tables.interp(L.HW_STOCK, ut0) - 0.0035
        polys = []
        for k in range(L.BUTTPLATE_RIBS):
            s = -0.78 + 1.56 * k / (L.BUTTPLATE_RIBS - 1)
            if abs(s - L.TRAPDOOR_AT) < 0.30:                  # ribs stop around the trapdoor
                continue
            o = c + up * (s * h)
            # local plate half width at this height (the butt ring is rounded top and bottom)
            band = [abs(p.x) for p in r0 if abs((p - _ring_centre(r0)).dot(up) - s * h) < 0.004]
            w = min(hw, (max(band) if band else hw) - 0.003)
            if w < 0.006:
                continue
            q = [o + xa * w + up * 0.001, o - xa * w + up * 0.001, o - xa * w - up * 0.001,
                 o + xa * w - up * 0.001]
            polys.append((q, [p + back * 0.0008 for p in q]))
        out.append(mesh.extrude_polys("WOOD_ButtPlate_Ribs", lod["C_DETAIL"], polys, STEEL))
        td = c + up * (L.TRAPDOOR_AT * h)
        out.append(mesh.cyl("WOOD_ButtPlate_Trapdoor", lod["C_DETAIL"], td, td + back * 0.0007,
                            L.TRAPDOOR_R, 24, STEEL))
        hinge = td + up * (L.TRAPDOOR_R + 0.0012)
        out.append(mesh.cyl("WOOD_ButtPlate_TrapdoorHinge", lod["C_DETAIL"], hinge - xa * 0.006,
                            hinge + xa * 0.006, 0.0011, 10, STEEL))
        specs = []
        for s in (0.86, -0.86):
            p = c + up * (s * h)
            specs.append((p, p + back * 0.0009, 0.0033))
        out.append(mesh.multi_cyl("FASTENER_ButtPlateScrews", lod["C_DETAIL"], specs, 12, STEEL))
        # sling swivel: oval base on the belly + swinging loop
        sp = [L.P3(*p) for p in L.SWIVEL_BASE]
        out.append(mesh.tube("CTRL_SlingSwivel_Base", lod["C_DETAIL"], sp, 0.0028, 10, STEEL, smooth_path=False))
        loop = [Vector(L.P3(*p)) for p in L.SWIVEL_LOOP]
        pts = [loop[0] + Vector((-0.009, 0, 0)), loop[1] + Vector((-0.009, 0, 0)), loop[2] + Vector((-0.006, 0, 0)),
               loop[2] + Vector((0.006, 0, 0)), loop[1] + Vector((0.009, 0, 0)), loop[0] + Vector((0.009, 0, 0))]
        out.append(mesh.tube("CTRL_SlingSwivel_Loop", lod["C_DETAIL"], pts, 0.0015, 8, STEEL, samples=3))
    return out


def grip(lod):
    ob = plate(nm(lod, "GRIP_Pistol"), lod["C_PRIMARY"], L.GRIP, L.HW_GRIP, POLY)
    if lod["bevel"]:
        mods.bevel(ob, 0.0065, 4, angle=30)
        mods.weighted_normal(ob)
    return [ob]


# ============================================================================ magazine (v2)
def _mag_frame():
    """AKM 30-rd ribbed steel magazine. The spine (rear edge) and the front edge are circular arcs
    fitted to the photo (rear r=397 px, front r=297 px, max residual 2.5 px). The top section is
    radial (spine -> rear-arc centre, depth ~62.6 mm, spec ~64 mm); the bottom section lies on the
    measured floorplate line. Rear and front points slide along their own arcs in between.
    Returns section(s) -> (rear_px, front_px) with s = 0 top, 1 = body bottom, and s of the
    floorplate outer face."""
    rcx, rcy, rr = L.MAG_REAR_ARC
    fcx, fcy, fr = L.MAG_FRONT_ARC
    Cr, Cf = Vector((rcx, rcy)), Vector((fcx, fcy))
    a, b = Vector(L.MAG_FLOOR_LINE[0]), Vector(L.MAG_FLOOR_LINE[1])
    inward = Vector((-(b - a).y, (b - a).x)).normalized()
    if inward.dot(Cr - a) < 0:                      # towards the magazine top
        inward = -inward

    def hit(C, r, inset, near):
        p0, d = a + inward * inset, b - a           # line shifted inside by `inset` px
        w = p0 - C
        A, B, Cc = d.dot(d), 2 * w.dot(d), w.dot(w) - r * r
        q = math.sqrt(max(0.0, B * B - 4 * A * Cc))
        pts = [p0 + d * ((-B + sg * q) / (2 * A)) for sg in (1, -1)]
        return min(pts, key=lambda p: (p - near).length)

    def ang(C, p):
        return math.atan2(p.y - C.y, p.x - C.x)
    R0 = Vector((rcx - math.sqrt(rr * rr - (L.MAG_TOP_V - rcy) ** 2), L.MAG_TOP_V))
    d0 = (Cr - R0).normalized()
    w = R0 - Cf
    bq, cq = w.dot(d0), w.dot(w) - fr * fr
    F0 = R0 + d0 * (-bq - math.sqrt(max(0.0, bq * bq - cq)))
    tr0, tf0 = ang(Cr, R0), ang(Cf, F0)
    Rb, Fb = hit(Cr, rr, L.MAG_FLOOR_T_PX, b), hit(Cf, fr, L.MAG_FLOOR_T_PX, a)
    Ro = hit(Cr, rr, 0.0, b)
    tr1, tf1 = ang(Cr, Rb), ang(Cf, Fb)

    def section(s):
        t_r, t_f = tr0 + (tr1 - tr0) * s, tf0 + (tf1 - tf0) * s
        return (Cr + rr * Vector((math.cos(t_r), math.sin(t_r))),
                Cf + fr * Vector((math.cos(t_f), math.sin(t_f))))
    s_out = (ang(Cr, Ro) - tr0) / (tr1 - tr0)
    return section, 0.0, 1.0, s_out


def magazine(lod):
    C, D = lod["C_PRIMARY"], lod["C_DETAIL"]
    n = lod["mag_st"]
    rn = max(14, lod["ring"])
    section, th0, th1, th_fp = _mag_frame()
    ths = [th0 + (th1 - th0) * i / (n - 1) for i in range(n)]
    secs = [section(t) for t in ths]
    pairs = [(tuple(R), tuple(F)) for R, F in secs]
    out = [loft_pairs(nm(lod, "MAG_Body"), C, pairs, [L.HW_MAG] * n, rn, STEEL,
                      e_a=L.MAG_E_SPINE, e_b=L.MAG_E_FRONT, sharp_angle=55)]
    # floorplate: slides on the body rails, 1.2 mm proud all round, front lip overhangs
    R0, F0 = section(th1 - 0.012)
    R1, F1 = section(th_fp)
    fwd0, fwd1 = (F0 - R0).normalized(), (F1 - R1).normalized()
    fp_pairs = [(tuple(R0 - fwd0 * 1.0), tuple(F0 + fwd0 * 1.5)), (tuple(R1 - fwd1 * 1.0), tuple(F1 + fwd1 * 1.5))]
    fp = loft_pairs(nm(lod, "MAG_Floorplate"), lod["C_SECONDARY"], fp_pairs, [L.HW_MAG] * 2, rn, STEEL,
                    e_a=L.MAG_E_SPINE, e_b=4.0, grow=0.0008, sharp_angle=40)
    out.append(hard(fp, lod, 0.0006))
    # lip reinforcement plates (welded, both sides, top of the body)
    m_lip = max(2, int(n * L.MAG_LIP_FRAC))
    lp = [(tuple(R.lerp(F, 0.04)), tuple(F.lerp(R, 0.04))) for R, F in secs[:m_lip + 1]]
    out.append(loft_pairs(nm(lod, "MAG_LipPlates"), lod["C_SECONDARY"], lp, [L.HW_MAG + 0.0007] * len(lp), rn,
                          STEEL, e_a=8.0, e_b=8.0, sharp_angle=40))
    # locking lugs: front lug (hooks into the receiver) and rear catch lug (under the mag catch)
    Rt, Ft = secs[0]
    Rl, Fl = section(th0 + (th1 - th0) * 0.07)
    fwd, dn = (Ft - Rt).normalized(), (Rl - Rt).normalized()
    fl = [Ft + dn * 2, Ft + fwd * 5 + dn * 3, Ft + fwd * 5 + dn * 11, Ft + dn * 13]
    rl = [Rl - fwd * 0.0 + dn * 3, Rl - fwd * 6 + dn * 3, Rl - fwd * 6 + dn * 12, Rl + dn * 12]
    for nme, poly, hw in (("MAG_LugFront", fl, 0.0045), ("MAG_LugRear", rl, 0.0070)):
        out.append(hard(plate(nm(lod, nme), lod["C_SECONDARY"], [tuple(p) for p in poly], hw, STEEL),
                        lod, 0.0005))
    if lod["detail"]:
        paths = []

        def rib_pt(t, f, side):
            R, F = section(t)
            p = R.lerp(F, f)
            y, z = L.P(p.x, p.y)
            return Vector((side * (L.HW_MAG - L.MAG_RIB_SINK), y, z))
        for (f, t0, t1) in L.MAG_LONG_RIBS:                          # 3 outward longitudinal ribs
            k = max(4, int((t1 - t0) * n))
            for side in (-1, 1):
                paths.append([rib_pt(t0 + (t1 - t0) * i / k, f, side) for i in range(k + 1)])
        for (t, f0, f1) in L.MAG_SHORT_RIBS:                         # short ribs parallel to the floor
            for side in (-1, 1):
                paths.append([rib_pt(t, f0 + (f1 - f0) * i / 4, side) for i in range(5)])
        out.append(tubes("MAG_Ribs", D, paths, L.MAG_RIB_R, 8, STEEL, samples=1, taper=True))
    return out


def controls(lod):
    C = lod["C_MECH"]
    out = []
    xr = -L.HW_RECV
    out.append(hard(plate(nm(lod, "CTRL_Guard"), C, L.TRIGGER_GUARD, L.HW_GUARD, STEEL), lod, 0.0006))
    out.append(hard(plate(nm(lod, "CTRL_Trigger_Blade"), C, L.TRIGGER, L.HW_TRIGGER, STEEL), lod, 0.0008))
    out.append(hard(plate(nm(lod, "CTRL_MagCatch"), C, L.MAG_CATCH, L.HW_CATCH, STEEL), lod, 0.0008))
    lever = plate(nm(lod, "CTRL_Safety_Lever"), C, L.SAFETY_LEVER, 0, STEEL, x0=xr - 0.0028, x1=xr - 0.0007)
    out.append(hard(lever, lod, 0.0006))
    y, z = L.P(*L.SAFETY_PIVOT_PX)
    out.append(mesh.cyl(nm(lod, "CTRL_Safety_Pivot"), C, (xr, y, z), (xr - 0.0032, y, z),
                        L.m(L.SAFETY_PIVOT_R_PX), lod["lathe"], STEEL))
    # bolt carrier seen through the ejection port + charging handle
    car = plate(nm(lod, "CTRL_Charging_Carrier"), C, L.EJECTION_PORT, 0, BRIGHT, x0=xr - 0.0003, x1=0.0)
    out.append(hard(car, lod, 0.0008))
    y, z = L.P(*L.CHARGING_KNOB_PX)
    prof = [(0.0033, xr), (0.0033, -0.033), (0.0046, -0.0355), (0.0050, -0.041), (0.0042, -0.0455),
            (0.0018, -0.0472)]
    out.append(mesh.lathe(nm(lod, "CTRL_Charging_Handle"), C, (0, y, z), [(r, x) for r, x in prof],
                          lod["lathe"], BRIGHT, closed=False, axis="X", sharp_angle=50))
    return out


def details(lod):
    """HIGH-only small parts: rivets/pins (both sides), stock screw, sling swivel."""
    if not lod["detail"]:
        return []
    C = lod["C_DETAIL"]
    out = [domes("FASTENER_Rivets_R", C, L.RIVETS, -L.HW_RECV, 0.0023, 0.0010, 10, STEEL, -1.0),
           domes("FASTENER_Rivets_L", C, L.RIVETS, L.HW_RECV, 0.0023, 0.0010, 10, STEEL, 1.0)]
    y, z = L.P(*L.MAG_CATCH_PIN_PX)
    out.append(mesh.cyl("FASTENER_MagCatchPin", C, (-L.HW_CATCH - 0.0006, y, z), (L.HW_CATCH + 0.0006, y, z),
                        0.0017, 10, STEEL))
    hw = tables.interp(L.HW_STOCK, 413)
    out.append(domes("FASTENER_StockScrew", C, [(413, 295)], -hw + 0.0003, 0.0030, 0.0008, 12, STEEL, -1.0))
    return out


def build_all(lod):
    return {"receiver": receiver(lod), "barrel": barrel(lod), "wood": woodwork(lod), "grip": grip(lod),
            "stock": buttstock(lod), "mag": magazine(lod), "controls": controls(lod), "details": details(lod)}


def guide_points():
    return {"GUIDE_Bore_Trigger": (0, 0, 0), "GUIDE_Muzzle": L.P3(L.MUZZLE_U, L.BORE_V),
            "GUIDE_ButtHeel": L.P3(L.BUTT_U, 437), "GUIDE_FrontSightPost": L.P3(1369, 219)}


# pivots for game animation (world points)
PIVOTS = {
    "MAG_Body": lambda: L.P3(778, 331),                    # rocks in around the front locking lug
    "CTRL_Trigger_Blade": lambda: L.P3(574, 332),
    "CTRL_Safety_Lever": lambda: L.P3(*L.SAFETY_PIVOT_PX, x=-L.HW_RECV),
    "CTRL_MagCatch": lambda: L.P3(*L.MAG_CATCH_PIN_PX),
    "CTRL_Charging_Handle": lambda: L.P3(*L.CHARGING_KNOB_PX, x=-L.HW_RECV),
}
