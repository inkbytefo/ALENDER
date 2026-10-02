"""
Part builders for PROP_AK_Rifle (staged pipeline, docs/01_WORKFLOW.md). Every builder takes a stage
profile P and reads ALL placement from landmarks.py (pixels). Shape helpers: shapes.py.

  S1 PRIMITIVE  *_prim builders: boxes / cylinders / simplified outlines from the same landmarks
  S2 LOWPOLY    the real builders with PROFILES[2] (game LOD0: no bevels, no rivets / ribs)
  S3 DETAIL     the same builders with PROFILES[3] (bevels, ribs, rivets, buttplate details)
  S4 GAME       bake S3 -> S2 atlas, LOD1-2, per-part convex hulls, Godot-ready glb

Groups: RECV_ (receiver), SIGHT_, BARREL_, GAS_, FSB_ (front sight), MUZZLE_, WOOD_, GRIP_, MAG_,
CTRL_ (trigger, guard, safety, mag catch, charging handle), FASTENER_.
Right-side-only parts (photo side) sit at -X.
"""
import math

import bpy
from mathutils import Vector

import landmarks as L
import shapes as S
from shapes import hard, plate
from workbench import tables, stages, silhouette
from workbench.stages import Part, nm
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "hero_prop"                 # tables.BUDGETS
TARGET_DIMS = (None, 0.880, None)      # overall length (AKM, fixed stock, slant brake)
GROUND = False                         # hand-held: origin on the bore axis, parts below Z = 0
PROFILES = {
    1: stages.profile(1, ring=8, lathe=8, stations=6, mag_st=6),
    2: stages.profile(2, ring=16, lathe=16, stations=20, mag_st=16),
    3: stages.profile(3, ring=28, lathe=28, stations=26, mag_st=26),
}
# painted atlas: the PNG masters stay in output/<A>/textures, the glb embeds JPEG (3 x ~6 MB PNG otherwise)
GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.03,
            image_format="JPEG", image_quality=92)
LICENCE = "own procedural build; downloaded AK47.blend studied only, nothing reused"
UNCERTAIN = ["all widths (X) estimated (pure side photo)", "left side mirrored from the right",
             "rear sight leaf / slider simplified", "magazine top and internals not modelled"]

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


def Y(u):
    """world Y of a px column (on the bore line)."""
    return L.P(u, L.BORE_V)[0]


def Z(u, v):
    """world Z of a px point."""
    return L.P(u, v)[1]


# ============================================================================ receiver + sights
def receiver(P):
    C = P["coll"]
    out = [hard(plate(nm(P, "RECV_Body"), C, L.RECV_BODY, L.HW_RECV, STEEL), P, 0.0015),
           hard(plate(nm(P, "RECV_RearTrunnion"), C, L.RECV_TRUNNION, L.HW_TRUNNION, STEEL), P, 0.0012)]
    n = P["stations"]
    pairs = S.pairs_between(L.COVER_TOP, L.COVER_BOT, L.COVER_U, L.COVER_U, n, bias=0.7)   # dense at the round rear
    out.append(S.loft_pairs(nm(P, "RECV_DustCover"), C, pairs, [L.HW_COVER] * n, P["ring"], STEEL,
                            e_a=2.4, e_b=7.0, sharp_angle=50))
    out.append(hard(plate(nm(P, "RECV_WallLeft"), C, L.RECV_WALL_LEFT, 0, STEEL, x0=0.0, x1=L.HW_RECV), P, 0.001))
    out.append(hard(plate(nm(P, "SIGHT_RearBase"), C, L.REAR_SIGHT_BASE, L.HW_RSIGHT, STEEL), P, 0.0012))
    out.append(hard(plate(nm(P, "SIGHT_RearLeaf"), C, L.REAR_SIGHT_LEAF, L.HW_LEAF, STEEL), P, 0.0006))
    out.append(hard(plate(nm(P, "SIGHT_RearPost"), C, L.REAR_SIGHT_POST, L.HW_LEAF * 0.6, STEEL), P, 0.0005))
    y, z = L.P(*L.REAR_SIGHT_SLIDER_PX)
    out.append(hard(mesh.box(nm(P, "SIGHT_Slider"), C, (0, y, z + 0.0005), L.REAR_SIGHT_SLIDER_SIZE, STEEL),
                    P, 0.0008))
    return out


# ============================================================================ barrel group
def front_sight(P):
    """Base block around the barrel (the FSB outline below the ear base), two protective ears with
    the adjustment hole, and a thin centre post."""
    C = P["coll"]
    eb = L.FSB_EAR_BASE_V
    # outline without sub-2 px steps: bevels collapse such short edges into 0-area faces (U16)
    fsb = silhouette.simplify(L.FSB + [L.FSB[0]], 1.0)[:-1]
    us = [p[0] for p in fsb]
    base = [(min(us), eb), (max(us), eb)] + [p for p in fsb if p[1] > eb]
    out = [hard(plate(nm(P, "FSB_Body"), C, base, L.HW_FSB, STEEL), P, 0.0008)]
    u0, u1 = L.FSB_EAR_FOOT_U
    ear_poly = [p for p in fsb if p[1] <= eb + 2] + [(u1, eb + 2), (u0, eb + 2)]
    y, z = L.P(*L.FSB_HOLE_PX)
    for side, tag in ((-1, "R"), (1, "L")):
        x0, x1 = sorted((side * L.HW_FSB, side * (L.HW_FSB - L.FSB_EAR_T)))
        ear = plate(nm(P, "FSB_Ear_" + tag), C, ear_poly, 0, STEEL, x0=x0, x1=x1)
        cut = mesh.cyl("TEMP_FSB_Hole", C, (-0.02, y, z), (0.02, y, z), L.m(L.FSB_HOLE_R_PX, L.FSB_HOLE_PX[0]), 16, STEEL)
        mods.boolean(ear, cut, apply=True)
        bpy.data.objects.remove(cut, do_unlink=True)
        out.append(hard(ear, P, 0.0007))
    out.append(hard(plate(nm(P, "FSB_Post"), C, L.FSB_POST, L.HW_FSB_POST, STEEL), P, 0.0005))
    return out


def barrel(P):
    C, s = P["coll"], P["lathe"]
    prof = [(L.m(r, u), Y(u)) for (u, r) in L.BARREL]
    out = [mesh.lathe(nm(P, "BARREL_Main"), C, (0, 0, 0), prof, s, STEEL, closed=False, axis="Y",
                      sharp_angle=30),
           hard(plate(nm(P, "GAS_Block"), C, L.GAS_BLOCK, L.HW_GASBLOCK, STEEL), P, 0.002, 3),
           hard(plate(nm(P, "GAS_BayonetLug"), C, L.BAYONET_LUG, L.HW_LUG, STEEL), P, 0.0008)]
    g = L.GAS_TUBE
    um = (g["um"])                                   # column where v / r were measured
    zt, rt = Z(um, g["v"]), L.m(g["r"], um)
    out.append(mesh.cyl(nm(P, "GAS_Tube"), C, (0, Y(g["u0"]), zt), (0, Y(g["u1"]), zt), rt, s, STEEL))
    if P["detail"]:
        a, b = L.GAS_TUBE_RING_U
        out.append(mesh.cyl(nm(P, "GAS_TubeRing"), C, (0, Y(a), zt), (0, Y(b), zt), rt + 0.0007, s,
                            STEEL))
    out += front_sight(P)
    b = L.BRAKE
    cu0, cu1, cr = b["collar"]
    out.append(mesh.cyl(nm(P, "MUZZLE_Collar"), C, (0, Y(cu0), 0), (0, Y(cu1), 0), L.m(cr, cu0), s, STEEL))
    out.append(S.slant_brake(nm(P, "MUZZLE_Brake"), C, Y(b["u0"]),
                             lambda z: Y(tables.interp(b["front"], L.photo_of(Y(b["u0"]), z)[1])),
                             L.m(b["r"], b["u0"]), L.m(b["bore"], b["u0"]), s, STEEL))
    return out


# ============================================================================ wood
def woodwork(P):
    C = P["coll"]
    n, rn = P["stations"], P["ring"]
    # lower handguard: flat-ish top channel, rounded belly, finger swell at the rear
    u = (L.HG_LOWER_BOT[0][0], L.HG_LOWER_BOT[-1][0])
    pairs = S.pairs_between(L.HG_LOWER_TOP, L.HG_LOWER_BOT, u, u, n)
    hws = [tables.interp(L.HW_HG_LOWER, a[0]) for a, _ in pairs]
    out = [S.loft_pairs(nm(P, "WOOD_HandguardLower"), C, pairs, hws, rn, WOOD, e_a=5.0, e_b=2.6,
                        sharp_angle=80)]
    u = (L.HG_UPPER_TOP[0][0], L.HG_UPPER_TOP[-1][0])
    pairs = S.pairs_between(L.HG_UPPER_TOP, L.HG_UPPER_BOT, u, u, max(6, n // 2))
    hws = [tables.interp(L.HW_HG_UPPER, a[0]) for a, _ in pairs]
    out.append(S.loft_pairs(nm(P, "WOOD_HandguardUpper"), C, pairs, hws, rn, WOOD, e_a=2.3, e_b=4.5,
                            sharp_angle=80))
    out.append(hard(plate(nm(P, "RECV_HandguardRearCap"), C, L.HG_REAR_CAP, L.HW_HG_CAP, STEEL), P, 0.002, 3))
    out.append(hard(plate(nm(P, "RECV_HandguardBand"), C, L.HG_FRONT_BAND, L.HW_HG_BAND, STEEL), P, 0.002, 3))
    out.append(hard(plate(nm(P, "RECV_HandguardRetainer"), C, L.HG_RETAINER, L.HW_HG_RETAINER, STEEL), P, 0.001))
    return out


def buttstock(P):
    """AKM laminated stock: straight top with a shallow comb dip, straight belly rising to the
    wrist, slab sides with rounded top/bottom, slanted butt; steel buttplate wrapping onto the wood."""
    C = P["coll"]
    n, rn = P["stations"] + 10, P["ring"]
    k = 4 if P["detail"] else 1
    # the butt is seen ~14 deg from behind: its silhouette overhangs the mid-plane end by `d` px
    d = L.REF.thickness_px(L.STOCK_BUTT_U[0], tables.interp(L.HW_STOCK, L.STOCK_BUTT_U[0]))
    pairs = S.pairs_between(S.smooth(L.STOCK_TOP, k), S.smooth(L.STOCK_BOT, k),
                            (L.STOCK_BUTT_U[0] + d, L.STOCK_FRONT_U), (L.STOCK_BUTT_U[1] + d, L.STOCK_FRONT_U),
                            n, bias=1.15)                                   # a bit denser at the butt
    rings = [S.ring_two(a, b, tables.interp(L.HW_STOCK, (a[0] + b[0]) / 2), rn, L.STOCK_E_TOP, L.STOCK_E_BOT)
             for (a, b) in pairs]
    out = [mesh.loft_rings(nm(P, "WOOD_Stock"), C, rings, WOOD, sharp_angle=80)]

    # buttplate: loft of inflated copies of the butt ring (wrap onto the wood -> back face)
    r0 = rings[0]
    axis = (S.ring_centre(rings[1]) - S.ring_centre(r0)).normalized()        # points forward (-Y)
    back, t = -axis, L.BUTTPLATE_T
    bp = [S.inflate(r0, 0.0006, axis * L.BUTTPLATE_WRAP), S.inflate(r0, 0.0009),
          S.inflate(r0, 0.0009, back * t * 0.6), S.inflate(r0, 0.0002, back * t)]
    out.append(hard(mesh.loft_rings(nm(P, "WOOD_ButtPlate"), C, bp, STEEL, sharp_angle=60), P, 0.0006))
    if P["detail"]:
        top_pt, bot_pt = Vector(L.P3(*pairs[0][0])), Vector(L.P3(*pairs[0][1]))
        out += _buttplate_details(P, r0, back, top_pt, bot_pt) + _sling_swivel(P)
    return out


def _buttplate_details(P, r0, back, top_pt, bot_pt):
    """Back face of the buttplate: horizontal grip ribs, cleaning-kit trapdoor + hinge, 2 screws."""
    C = P["coll"]
    centre = S.ring_centre(r0)
    c = centre + back * L.BUTTPLATE_T                      # centre of the plate's back face
    xa = Vector((1, 0, 0))
    up = (top_pt - bot_pt).normalized()                    # in the (slanted) butt plane
    back = xa.cross(up) * (1 if xa.cross(up).dot(back) > 0 else -1)     # face normal, pointing rearwards
    h = (top_pt - bot_pt).length / 2
    hw = tables.interp(L.HW_STOCK, L.STOCK_BUTT_U[0]) - 0.0035
    polys = []
    for k in range(L.BUTTPLATE_RIBS):
        s = -0.78 + 1.56 * k / (L.BUTTPLATE_RIBS - 1)
        if abs(s - L.TRAPDOOR_AT) < 0.30:                  # ribs stop around the trapdoor
            continue
        o = c + up * (s * h)
        # local plate half width at this height (the butt ring is rounded top and bottom)
        band = [abs(p.x) for p in r0 if abs((p - centre).dot(up) - s * h) < 0.004]
        w = min(hw, (max(band) if band else hw) - 0.003)
        if w < 0.006:
            continue
        q = [o + xa * w + up * 0.001, o - xa * w + up * 0.001, o - xa * w - up * 0.001, o + xa * w - up * 0.001]
        polys.append((q, [p + back * 0.0008 for p in q]))
    out = [mesh.extrude_polys(nm(P, "WOOD_ButtPlate_Ribs"), C, polys, STEEL)]
    td = c + up * (L.TRAPDOOR_AT * h)
    out.append(mesh.cyl(nm(P, "WOOD_ButtPlate_Trapdoor"), C, td, td + back * 0.0007, L.TRAPDOOR_R, 24, STEEL))
    hinge = td + up * (L.TRAPDOOR_R + 0.0012)
    out.append(mesh.cyl(nm(P, "WOOD_ButtPlate_TrapdoorHinge"), C, hinge - xa * 0.006, hinge + xa * 0.006,
                        0.0011, 10, STEEL))
    screws = [(c + up * (s * h), c + up * (s * h) + back * 0.0009, 0.0033) for s in (0.86, -0.86)]
    out.append(mesh.multi_cyl(nm(P, "FASTENER_ButtPlateScrews"), C, screws, 12, STEEL))
    return out


def _sling_swivel(P):
    """Oval base on the belly + swinging loop."""
    C = P["coll"]
    base = [L.P3(*p) for p in L.SWIVEL_BASE]
    out = [mesh.tube(nm(P, "CTRL_SlingSwivel_Base"), C, base, 0.0028, 10, STEEL, smooth_path=False)]
    a, b, c = (Vector(L.P3(*p)) for p in L.SWIVEL_LOOP)
    wide, narrow = Vector((0.009, 0, 0)), Vector((0.006, 0, 0))
    loop = [a - wide, b - wide, c - narrow, c + narrow, b + wide, a + wide]
    out.append(mesh.tube(nm(P, "CTRL_SlingSwivel_Loop"), C, loop, 0.0015, 8, STEEL, samples=3))
    return out


def grip(P):
    """Polymer pistol grip: rounded sections lofted between the measured back strap and front edge
    (stations slide along both edges, so the last one lies on the slanted bottom)."""
    n = max(8, P["stations"] // 2 + 4)
    back, front = S.arc_sample(L.GRIP_BACK, n), S.arc_sample(L.GRIP_FRONT, n)
    hws = [tables.interp(L.HW_GRIP_T, i / (n - 1)) for i in range(n)]
    # oblique view: both long edges of the silhouette overhang the mid-plane section (rounded: x0.7)
    pairs = []
    for a, b, hw in zip(back, front, hws):
        d = 0.7 * L.REF.thickness_px((a.x + b.x) / 2, hw)
        pairs.append(((a.x + d, a.y), (b.x - d, b.y)))
    return [S.loft_pairs(nm(P, "GRIP_Pistol"), P["coll"], pairs, hws, P["ring"], POLY,
                         e_a=L.GRIP_E_BACK, e_b=L.GRIP_E_FRONT, sharp_angle=60)]


# ============================================================================ magazine
def _mag_frame():
    """AKM 30-rd ribbed steel magazine. The spine (rear edge) and the front edge are circular arcs
    least-squares fitted to the measured photo edges. The top section is radial (spine -> rear-arc
    centre); the bottom section lies on the measured floorplate line; rear and front points slide
    along their own arcs in between.
    Returns (section, s_out): section(s) -> (rear_px, front_px) with s = 0 top, 1 = body bottom,
    s_out = the floorplate outer face."""
    # oblique view: the spine / front silhouettes overhang the mid-plane section by d px
    d = L.REF.thickness_px(L.MAG_PIVOT_PX[0], L.HW_MAG)
    rcx, rcy, rr = L.MAG_REAR_ARC[0] + d, L.MAG_REAR_ARC[1], L.MAG_REAR_ARC[2]
    fcx, fcy, fr = L.MAG_FRONT_ARC[0] - d * L.MAG_FRONT_TAPER, L.MAG_FRONT_ARC[1], L.MAG_FRONT_ARC[2]
    Cr, Cf = Vector((rcx, rcy)), Vector((fcx, fcy))
    a, b = Vector(L.MAG_FLOOR_LINE[0]), Vector(L.MAG_FLOOR_LINE[1])
    inward = Vector((-(b - a).y, (b - a).x)).normalized()
    if inward.dot(Cr - a) < 0:                      # towards the magazine top
        inward = -inward

    def hit(C, r, inset, near):
        """floor line (shifted inside by `inset` px) x circle; the root nearest to `near`."""
        p0, d = a + inward * inset, b - a
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
    return section, (ang(Cr, Ro) - tr0) / (tr1 - tr0)


def magazine(P):
    C = P["coll"]
    n, rn = P["mag_st"], max(14, P["ring"])
    section, s_out = _mag_frame()
    secs = [section(i / (n - 1)) for i in range(n)]
    pairs = [(tuple(R), tuple(F)) for R, F in secs]
    out = [S.loft_pairs(nm(P, "MAG_Body"), C, pairs, [L.HW_MAG] * n, rn, STEEL,
                        e_a=L.MAG_E_SPINE, e_b=L.MAG_E_FRONT, taper=L.MAG_FRONT_TAPER, sharp_angle=55)]
    # floorplate: slides on the body rails, 0.8 mm proud all round, lips front and rear
    R0, F0 = section(1.0 - 0.012)
    R1, F1 = section(s_out)
    fwd0, fwd1 = (F0 - R0).normalized(), (F1 - R1).normalized()
    fp_pairs = [(tuple(R0 - fwd0 * 1.0), tuple(F0 + fwd0 * 1.5)), (tuple(R1 - fwd1 * 1.0), tuple(F1 + fwd1 * 1.5))]
    out.append(hard(S.loft_pairs(nm(P, "MAG_Floorplate"), C, fp_pairs, [L.HW_MAG] * 2, rn, STEEL,
                                 e_a=L.MAG_E_SPINE, e_b=4.0, grow=0.0008, taper=L.MAG_FRONT_TAPER, sharp_angle=40), P, 0.0004))
    # lip reinforcement plates (welded, both sides, top of the body)
    m_lip = max(2, int(n * L.MAG_LIP_FRAC))
    lp = [(tuple(R.lerp(F, 0.04)), tuple(F.lerp(R, 0.04))) for R, F in secs[:m_lip + 1]]
    out.append(S.loft_pairs(nm(P, "MAG_LipPlates"), C, lp, [L.HW_MAG + 0.0007] * len(lp), rn, STEEL,
                            e_a=8.0, e_b=8.0, taper=L.MAG_FRONT_TAPER, sharp_angle=40))
    # locking lugs: front lug (hooks into the receiver) and rear catch lug (under the mag catch)
    Rt, Ft = secs[0]
    Rl, _ = section(0.07)
    fwd, dn = (Ft - Rt).normalized(), (Rl - Rt).normalized()
    front_lug = [Ft + dn * 2, Ft + fwd * 5 + dn * 3, Ft + fwd * 5 + dn * 11, Ft + dn * 13]
    # rear catch lug: 2 px deep, back face >= 1 px clear of the mag catch
    # (a thinner lug collapses under the bevel: U05)
    back = max(0.0, min(2.0, Rl.x - max(p[0] for p in L.MAG_CATCH) - 1.0))
    bf, ff = Rl - fwd * back, Rl - fwd * back + fwd * 2.0
    rear_lug = [ff + dn * 3, bf + dn * 3, bf + dn * 12, ff + dn * 12]
    for name, poly, hw in (("MAG_LugFront", front_lug, 0.0045), ("MAG_LugRear", rear_lug, 0.0070)):
        out.append(hard(plate(nm(P, name), C, [tuple(p) for p in poly], hw, STEEL), P, 0.0005))
    if P["detail"]:
        out.append(_mag_ribs(P, section, n))
    return out


def _mag_ribs(P, section, n):
    """Stamped ribs on both sides: 3 long ribs along the curve + 2 short ones parallel to the floor."""
    def pt(t, f, side):
        R, F = section(t)
        y, z = L.P(*R.lerp(F, f))
        hw = L.HW_MAG * (1.0 - (1.0 - L.MAG_FRONT_TAPER) * f)          # the body narrows towards the front
        return Vector((side * (hw - L.MAG_RIB_SINK), y, z))
    paths = []
    for (f, t0, t1) in L.MAG_LONG_RIBS:
        k = max(4, int((t1 - t0) * n))
        paths += [[pt(t0 + (t1 - t0) * i / k, f, side) for i in range(k + 1)] for side in (-1, 1)]
    for (t, f0, f1) in L.MAG_SHORT_RIBS:
        paths += [[pt(t, f0 + (f1 - f0) * i / 4, side) for i in range(5)] for side in (-1, 1)]
    return S.beads(nm(P, "MAG_Ribs"), P["coll"], paths, L.MAG_RIB_R, 8, STEEL)


# ============================================================================ controls + fasteners
def controls(P):
    C = P["coll"]
    xr = -L.HW_RECV
    out = [hard(plate(nm(P, "CTRL_Guard"), C, L.TRIGGER_GUARD, L.HW_GUARD, STEEL), P, 0.0006),
           hard(plate(nm(P, "CTRL_Trigger_Blade"), C, L.TRIGGER, L.HW_TRIGGER, STEEL), P, 0.0008),
           hard(plate(nm(P, "CTRL_MagCatch"), C, L.MAG_CATCH, L.HW_CATCH, STEEL), P, 0.0008),
           hard(plate(nm(P, "CTRL_Safety_Lever"), C, L.SAFETY_LEVER, 0, STEEL, x0=xr - 0.0028, x1=xr - 0.0007),
                P, 0.0006)]
    y, z = L.P(*L.SAFETY_PIVOT_PX)
    out.append(mesh.cyl(nm(P, "CTRL_Safety_Pivot"), C, (xr, y, z), (xr - 0.0032, y, z),
                        L.m(L.SAFETY_PIVOT_R_PX, L.SAFETY_PIVOT_PX[0]), P["lathe"], STEEL))
    # bolt carrier seen through the ejection port + charging handle
    out.append(hard(plate(nm(P, "CTRL_Charging_Carrier"), C, L.EJECTION_PORT, 0, BRIGHT, x0=xr - 0.0003, x1=0.0),
                    P, 0.0008))
    y, z = L.P(*L.CHARGING_KNOB_PX)
    out.append(mesh.lathe(nm(P, "CTRL_Charging_Handle"), C, (0, y, z), L.CHARGING_HANDLE, P["lathe"], BRIGHT,
                          closed=False, axis="X", sharp_angle=50))
    return out


def details(P):
    """S3-only small parts: rivets / pins on both receiver walls, mag-catch pin, stock screw."""
    if not P["detail"]:
        return []
    C = P["coll"]
    out = [S.domes(nm(P, "FASTENER_Rivets_" + tag), C, L.RIVETS, side * L.HW_RECV, L.RIVET_R, L.RIVET_H, 10,
                   STEEL, float(side)) for side, tag in ((-1, "R"), (1, "L"))]
    y, z = L.P(*L.MAG_CATCH_PIN_PX)
    out.append(mesh.cyl(nm(P, "FASTENER_MagCatchPin"), C, (-L.HW_CATCH - 0.0006, y, z),
                        (L.HW_CATCH + 0.0006, y, z), 0.0017, 10, STEEL))
    hw = tables.interp(L.HW_STOCK, L.STOCK_SCREW_PX[0])
    out.append(S.domes(nm(P, "FASTENER_StockScrew"), C, [L.STOCK_SCREW_PX], -hw + 0.0003, 0.0030, 0.0008, 12,
                       STEEL, -1.0))
    return out


# ============================================================================ Stage 1 primitives
# Same landmarks, crude shapes: outlines simplified to their main corners, round parts as 8-gons.
# Loft parts become plates of their mean half width.
def receiver_prim(P):
    C = P["coll"]
    return [prim.box_px(nm(P, "RECV_Body"), C, L.RECV_BODY, L.HW_RECV, STEEL),
            prim.plate_px(nm(P, "RECV_DustCover"), C, L.COVER_TOP + L.COVER_BOT[::-1], L.HW_COVER, STEEL, tol=3),
            prim.box_px(nm(P, "SIGHT_RearBase"), C, L.REAR_SIGHT_BASE, L.HW_RSIGHT, STEEL),
            prim.box_px(nm(P, "SIGHT_RearLeaf"), C, L.REAR_SIGHT_LEAF, L.HW_LEAF, STEEL)]


def barrel_prim(P):
    C, s = P["coll"], P["lathe"]
    g, b = L.GAS_TUBE, L.BRAKE
    return [prim.cyl_px(nm(P, "BARREL_Main"), C, (L.BARREL[0][0], L.BORE_V), (L.BARREL[-1][0], L.BORE_V),
                        L.m(L.BARREL[1][1], L.BARREL[1][0]), s, STEEL),
            prim.cyl_px(nm(P, "GAS_Tube"), C, (g["u0"], g["v"]), (g["u1"], g["v"]), L.m(g["r"], g["um"]), s, STEEL),
            prim.box_px(nm(P, "GAS_Block"), C, L.GAS_BLOCK, L.HW_GASBLOCK, STEEL),
            prim.plate_px(nm(P, "FSB_Body"), C, L.FSB, L.HW_FSB, STEEL, tol=4),
            prim.cyl_px(nm(P, "MUZZLE_Brake"), C, (b["collar"][0], L.BORE_V), (b["front"][-1][1], L.BORE_V),
                        L.m(b["r"], b["u0"]), s, STEEL)]


def woodwork_prim(P):
    C = P["coll"]
    return [prim.plate_px(nm(P, "WOOD_HandguardLower"), C, L.HG_LOWER_TOP + L.HG_LOWER_BOT[::-1], 0.019, WOOD, tol=4),
            prim.plate_px(nm(P, "WOOD_HandguardUpper"), C, L.HG_UPPER_TOP + L.HG_UPPER_BOT[::-1], 0.0155, WOOD, tol=4),
            prim.box_px(nm(P, "RECV_HandguardBand"), C, L.HG_FRONT_BAND, L.HW_HG_BAND, STEEL)]


def buttstock_prim(P):
    C = P["coll"]
    return [prim.plate_px(nm(P, "WOOD_Stock"), C, L.STOCK_TOP + L.STOCK_BOT[::-1], 0.020, WOOD, tol=5),
            prim.plate_px(nm(P, "WOOD_ButtPlate"), C, L.BUTT_PLATE, 0.021, STEEL, tol=2)]


def grip_prim(P):
    return [prim.plate_px(nm(P, "GRIP_Pistol"), P["coll"], L.GRIP, L.HW_GRIP, POLY, tol=6)]


def magazine_prim(P):
    return [prim.plate_px(nm(P, "MAG_Body"), P["coll"], L.MAG_REAR + L.MAG_FRONT[::-1], L.HW_MAG, STEEL, tol=5)]


def controls_prim(P):
    C = P["coll"]
    return [prim.plate_px(nm(P, "CTRL_Guard"), C, L.TRIGGER_GUARD, L.HW_GUARD, STEEL, tol=2),
            prim.plate_px(nm(P, "CTRL_Trigger_Blade"), C, L.TRIGGER, L.HW_TRIGGER, STEEL, tol=2),
            prim.box_px(nm(P, "CTRL_MagCatch"), C, L.MAG_CATCH, L.HW_CATCH, STEEL)]


# ============================================================================ registry
# One entry per part group: S1 uses prim, S2/S3 the same real builder with their profiles.
PARTS = [
    Part("receiver", receiver, prim=receiver_prim, collision="hull"),
    Part("barrel", barrel, prim=barrel_prim, collision="hull"),
    Part("woodwork", woodwork, prim=woodwork_prim, collision="hull"),
    Part("buttstock", buttstock, prim=buttstock_prim, collision="hull"),
    Part("grip", grip, prim=grip_prim, collision="hull"),
    Part("magazine", magazine, prim=magazine_prim, collision="hull"),
    Part("controls", controls, prim=controls_prim, collision="none"),
    Part("details", details, collision="none"),              # S3 only (returns [] without detail)
]


def after_build(stage, objs):
    """S3 DETAIL gets the painted master-material instances (bake source of S4, render look)."""
    if stage == 3:
        import paint
        paint.apply(objs)


def guide_points():
    return {"GUIDE_Bore_Trigger": (0, 0, 0), "GUIDE_Muzzle": L.P3(L.MUZZLE_U, L.BORE_V),
            "GUIDE_ButtHeel": L.P3(L.BUTT_U, L.STOCK_BOT[0][1]), "GUIDE_FrontSightPost": L.P3(*L.FSB_POST[1])}


# moving parts for game animation: origin on the joint (world point), keyed by base name
PIVOTS = {
    "MAG_Body": lambda: L.P3(*L.MAG_PIVOT_PX),
    "CTRL_Trigger_Blade": lambda: L.P3(*L.TRIGGER_PIVOT_PX),
    "CTRL_Safety_Lever": lambda: L.P3(*L.SAFETY_PIVOT_PX, x=-L.HW_RECV),
    "CTRL_MagCatch": lambda: L.P3(*L.MAG_CATCH_PIN_PX),
    "CTRL_Charging_Handle": lambda: L.P3(*L.CHARGING_KNOB_PX, x=-L.HW_RECV),
}
# parts that ride with a moving part (child base name -> parent base name)
CHILDREN = {"CTRL_Charging_Carrier": "CTRL_Charging_Handle", "MAG_Floorplate": "MAG_Body", "MAG_Ribs": "MAG_Body",
            "MAG_LipPlates": "MAG_Body", "MAG_LugFront": "MAG_Body", "MAG_LugRear": "MAG_Body",
            "CTRL_Safety_Pivot": "CTRL_Safety_Lever"}
