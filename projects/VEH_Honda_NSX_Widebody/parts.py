"""
Part builders for VEH_Honda_NSX_Widebody (staged pipeline, docs/01_WORKFLOW.md).

  S1 PRIMITIVE  same builders, coarse rings, no details (masses only)
  S2 LOWPOLY    real builders, no bevels  (game LOD0)
  S3 DETAIL     same builders + bevel/WN, arch lips, spokes, calipers, vents, seams ...

Longitudinal / vertical placement = pixels of ref/REF_SIDE_BLUEPRINT.png through L.P(); widths are
estimates from the cheatsheet front view + photo (UNCERTAIN_BodyWidths).
"""
import math
from mathutils import Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods

mesh.set_ref(L.REF)

CATEGORY = "hero_vehicle"
TARGET_DIMS = (None, None, None)
GROUND = True
PROFILES = {
    1: stages.profile(1, ring=8, ds=80, wseg=10, wd=40, arch=151.0, spokes=0),
    2: stages.profile(2, ring=24, ds=22, wseg=48, wd=20, arch=146.0, spokes=10),
    3: stages.profile(3, ring=26, ds=18, wseg=56, wd=16, arch=145.0, spokes=10),
}
GAME = dict(engine="godot", bake=True, lod=(0.5, 0.25))
PALETTE = {
    "MAT_BODY": ((0.42, 0.004, 0.012), 0.55, 0.16),      # candy red metallic paint
    "MAT_TRIM": "plastic_black",
    "MAT_TIRE": "rubber",
    "MAT_RIM": ((0.022, 0.022, 0.026), 0.9, 0.35),        # black anodised
    "MAT_GLASS": ((0.035, 0.05, 0.06), 0.2, 0.06),
    "MAT_CHROME": "chrome",
    "MAT_LAMP": ((0.82, 0.84, 0.86), 0.0, 0.08),
    "MAT_RED": ((0.55, 0.008, 0.01), 0.0, 0.25),          # tail lamps, brake calipers
}
CRITICAL_PAIRS = [("WHEEL_Tire", "BODY_Shell")]
UNCERTAIN = ["UNCERTAIN_BodyWidths", "UNCERTAIN_Underbody", "UNCERTAIN_Interior",
             "UNCERTAIN_WingEndplates", "UNCERTAIN_Exhaust"]
PIVOTS = {}
CHILDREN = {}

Y = lambda u: L.P(u, 0)[0]
Z = lambda v: L.P(0, v)[1]


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.004):
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def box(P, name, uv, size, x=0.0, mat="MAT_BODY", bevel=0.004, rot=None):
    y, z = L.P(*uv)
    return hard(mesh.box(nm(P, name), P["coll"], (x, y, z), size, mat, rot=rot), P, bevel)


def sym(fn):
    return [fn(1), fn(-1)]


# ---------------------------------------------------------------------------------- body shell
ARCH_R = (144.5, 144.5)                  # px, rear / front wheel arch radius (tyre 142 + clearance)


def body(P):
    prot = set()
    us = {u for u, _ in L.BODY_TOP} | {u for u, _ in L.BODY_HALF_W} | {u for u, _ in L.BODY_BOTTOM}
    for c in L.WHEEL_U:
        a = P["arch"]
        us |= {c + d for d in range(-int(a), int(a) + 1, P["wd"])}
        edge = {c - a - 3, c - a + 1, c + a - 1, c + a + 3}
        us |= edge
        prot |= edge
    prot |= {u for u, _ in L.BODY_TOP} | {u for u, _ in L.BODY_BOTTOM}
    us = sorted(u for u in us if L.BODY_TOP[0][0] <= u <= L.BODY_TOP[-1][0])
    # drop near-duplicates, keep the table stations
    keep, last = [], -999
    for u in us:
        if u - last >= P["ds"] * 0.45 or u in prot or last in prot:
            keep.append(u)
            last = u
    st = []
    for u in keep:
        vt = tables.polyline_v(L.BODY_TOP, u)
        vb = tables.polyline_v(L.BODY_BOTTOM, u)
        hw = tables.interp(L.BODY_HALF_W, u)
        for c in L.WHEEL_U:
            a = P["arch"]
            dx = u - c
            if abs(dx) <= a:                       # upper half-circle only; body continues beside the tyre
                vb = min(vb, L.WHEEL_V - math.sqrt(max(0.0, a * a - dx * dx)))
        vb = max(vb, vt + 16) if vb < vt + 16 else vb
        # flat-ish flanks, crowned top, boxy bottom
        st.append((u, vt, vb, hw, ETOP(u), 8.0, 0.42))
    ob = mesh.loft_px(nm(P, "BODY_Shell"), P["coll"], st, P["ring"], "MAT_BODY", sharp_angle=60.0)
    return [hard(ob, P, 0.006)]


def ETOP(u):
    """superellipse exponent of the shell crown: round tail/waist, crisper nose."""
    return tables.interp([(0, 3.0), (1425, 3.4), (1800, 4.2), (1995, 5.5)], u)


def surface_v(u, x):
    """photo v of the body shell top surface at lateral position x (mirrors the loft section)."""
    vt = tables.polyline_v(L.BODY_TOP, u)
    vb = tables.polyline_v(L.BODY_BOTTOM, u)
    hw = tables.interp(L.BODY_HALF_W, u)
    e, widest = ETOP(u), 0.42
    vm = vt + (vb - vt) * (1.0 - widest)
    r = min(0.999, abs(x) / hw)
    ca = r ** (e / 2.0)
    sa = math.sqrt(max(0.0, 1.0 - ca * ca))
    return vm - (vm - vt) * sa ** (2.0 / e)


def surface_x(u, v):
    """half width of the body shell flank at photo (u, v) (mirrors the loft section)."""
    vt = tables.polyline_v(L.BODY_TOP, u)
    vb = tables.polyline_v(L.BODY_BOTTOM, u)
    hw = tables.interp(L.BODY_HALF_W, u)
    e_top, e_bot, widest = ETOP(u), 8.0, 0.42
    vm = vt + (vb - vt) * (1.0 - widest)
    if v <= vm:
        t = min(0.999, (vm - v) / max(1e-6, vm - vt))
        return hw * (1.0 - t ** e_top) ** (1.0 / e_top)
    t = min(0.999, (v - vm) / max(1e-6, vb - vm))
    return hw * (1.0 - t ** e_bot) ** (1.0 / e_bot)


# ---------------------------------------------------------------------------------- greenhouse
HWR = [(570, .64), (668, .56), (1266, .52), (1425, .74)]


def cabin_station(u):
    vt = tables.polyline_v(L.ROOF_TOP, u)
    vbel = tables.polyline_v(L.CABIN_BELT_V, u)
    hwr = tables.interp(HWR, u)
    return vt, vbel, L.CABIN_BELT_HW, hwr


def cabin_x(u, v):
    """half width of the cabin surface at photo (u, v) - for glass placement."""
    vt, vbel, hwb, hwr = cabin_station(u)
    s = max(0.0, min(1.0, (vbel - v) / max(1e-6, vbel - vt)))
    pts = [(0.0, hwb), (0.5, hwr + (hwb - hwr) * 0.45), (0.9, hwr), (1.0, hwr * 0.6)]
    return tables.interp(pts, s)


def cabin(P):
    us = [578, 600, 640, 664, 669, 700, 733, 782, 860, 960, 1074, 1145, 1202, 1266, 1330, 1380, 1424]
    if P["stage"] == 1:
        us = [578, 640, 664, 669, 782, 894, 1074, 1202, 1266, 1424]
    rings = []
    for u in us:
        vt, vbel, hwb, hwr = cabin_station(u)
        vt = min(vt, vbel - 4)
        vm = vbel - 0.5 * (vbel - vt)
        hwm = hwr + (hwb - hwr) * 0.45
        d = min(14.0, 0.25 * (vbel - vt))
        vemb = vbel + 52
        half = [(hwb, vemb), (hwb, vbel), (hwm, vm), (hwr, vt + d), (hwr * 0.6, vt)]
        left = [L.P3(u, v, -x) for x, v in half]
        right = [L.P3(u, v, x) for x, v in reversed(half)]
        rings.append(left + right)
    ob = mesh.loft_rings(nm(P, "CABIN_Greenhouse"), P["coll"], rings, "MAT_BODY", sharp_angle=60.0)
    out = [hard(ob, P, 0.004)]
    if P["stage"] >= 2:
        out += glazing(P)
    return out


def glazing(P):
    import numpy as np
    obs = []
    side = [(802, 112), (1080, 93), (1140, 112), (1305, 232), (805, 224)]
    pts = [(*L.P(u, v), abs(cabin_x(u, v))) for u, v in side]          # (y, z, x_surface)
    A = np.array([[1.0, y, z] for y, z, _ in pts])
    coef = np.linalg.lstsq(A, np.array([x for *_, x in pts]), rcond=None)[0]
    shift = max(x - (coef[0] + coef[1] * y + coef[2] * z) for y, z, x in pts) + 0.006
    for sign in (-1, 1):
        t = 'L' if sign > 0 else 'R'
        f = lambda y, z, d: sign * (coef[0] + coef[1] * y + coef[2] * z + shift - d)
        a = [(f(y, z, 0.0), y, z) for y, z, _ in pts]
        b = [(f(y, z, 0.012), y, z) for y, z, _ in pts]
        obs.append(mesh.extrude_polys(nm(P, f"GLASS_Door_{t}"), P["coll"], [(a, b)], "MAT_GLASS"))
    # windshield + rear window (slabs lying on the cabin surface)
    ws = [(1272, 148, -.50), (1272, 148, .50), (1410, 222, .70), (1410, 222, -.70)]
    a = [(x, L.P(u, v)[0] - 0.004, L.P(u, v)[1] + 0.006) for u, v, x in ws]
    b = [(x, y + 0.012, z - 0.014) for x, y, z in a]
    obs.append(mesh.extrude_polys(nm(P, "GLASS_Windshield"), P["coll"], [(a, b)], "MAT_GLASS"))
    return obs


# ---------------------------------------------------------------------------------- wheels
def wheels(P):
    obs = []
    for i, (u, wx, tw) in enumerate(zip(L.WHEEL_U, L.TRACK_X, L.TIRE_W)):
        cy, cz = L.P(u, L.WHEEL_V)
        hw = tw / 2
        for sign in (-1, 1):
            side = "R" if sign < 0 else "L"
            tag = f"{i}_{side}"
            c = (sign * wx, cy, cz)
            tire = [(0.215, -hw), (0.262, -hw), (0.298, -hw * .85), (0.310, -hw * .45),
                    (0.310, hw * .45), (0.298, hw * .85), (0.262, hw), (0.215, hw)]
            obs.append(mesh.lathe(nm(P, "WHEEL_Tire_" + tag), P["coll"], c, tire, P["wseg"], "MAT_TIRE"))
            rim = [(0.185, -hw * .92), (0.232, -hw * .92), (0.236, -hw * .70), (0.222, -hw * .70),
                   (0.222, hw * .70), (0.236, hw * .70), (0.232, hw * .92), (0.185, hw * .92)]
            obs.append(mesh.lathe(nm(P, "WHEEL_Rim_" + tag), P["coll"], c, rim, P["wseg"], "MAT_RIM"))
            obs.append(mesh.cyl(nm(P, f"WHEEL_Dish_{tag}"), P["coll"], (c[0] - sign * hw * .35 - 0.01, cy, cz),
                                (c[0] - sign * hw * .35 + 0.01, cy, cz), 0.20, P["wseg"], "MAT_RIM"))
            if P["stage"] < 2:
                continue
            face = sign * (hw * .62)
            n = P["spokes"]
            for k in range(n):
                a = 2 * math.pi * k / n + (0.3 if i else 0.1)
                da = math.radians(10)
                vs = []
                for xx in (face - sign * 0.02, face):
                    for r, t in ((0.05, -0.55 * da * 2), (0.215, -da), (0.215, da), (0.05, 0.55 * da * 2)):
                        vs.append((c[0] + xx, cy + r * math.cos(a + t), cz + r * math.sin(a + t)))
                obs.append(hard(mesh.from_pydata(nm(P, f"WHEEL_Spoke_{tag}_{k}"), P["coll"], vs,
                    [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                    "MAT_RIM"), P, 0.002))
            obs.append(mesh.lathe(nm(P, f"WHEEL_Hub_{tag}"), P["coll"], (c[0] + sign * hw * .55, cy, cz),
                                  [(0.0, -0.015), (0.055, -0.015), (0.055, 0.015), (0.0, 0.015)],
                                  16, "MAT_CHROME", closed=False))
            # brake disc + caliper (behind spokes)
            obs.append(mesh.lathe(nm(P, f"BRAKE_Disc_{tag}"), P["coll"], (c[0] - sign * 0.03, cy, cz),
                                  [(0.085, -0.012), (0.185, -0.012), (0.185, 0.012), (0.085, 0.012)],
                                  P["wseg"], "MAT_CHROME"))
            ang = math.radians(35 if i else -35) + math.pi / 2
            ccy, ccz = cy + 0.15 * math.cos(ang), cz + 0.15 * math.sin(ang)
            obs.append(hard(mesh.box(nm(P, f"BRAKE_Caliper_{tag}"), P["coll"],
                (c[0] - sign * 0.03, ccy, ccz), (0.07, 0.15, 0.07), "MAT_RED",
                rot=Matrix.Rotation(ang - math.pi / 2, 3, "X")), P, 0.004))
    return obs


# ---------------------------------------------------------------------------------- arch lips
def flares(P):
    if P["stage"] < 2:
        return []
    obs = []
    n = 18 if P["stage"] == 2 else 34
    for i, u in enumerate(L.WHEEL_U):
        a = P["arch"]
        cy, cz = L.P(u, L.WHEEL_V)
        R = a / L.S
        hwx = tables.interp(L.BODY_HALF_W, u)
        for sign in (-1, 1):
            rings = []
            for j in range(n + 1):
                t = -0.15 + (math.pi + 0.30) * j / n          # from behind-low over the top to ahead-low
                th = t
                row = []
                for r, x in ((R - 0.004, hwx - 0.03), (R - 0.004, hwx + 0.018),
                             (R + 0.040, hwx + 0.018), (R + 0.040, hwx - 0.03)):
                    row.append((sign * x, cy + r * math.cos(th), cz + r * math.sin(th)))
                rings.append(row)
            obs.append(hard(mesh.loft_rings(nm(P, f"FLARE_{i}_{'L' if sign > 0 else 'R'}"),
                                            P["coll"], rings, "MAT_BODY"), P, 0.004))
    return obs


# ---------------------------------------------------------------------------------- aero
def aero(P):
    obs = []
    c = P["coll"]
    # front splitter, side skirts, rear lower valance
    obs.append(hard(mesh.plate(nm(P, "AERO_Splitter"), c,
        [(1790, 543), (1962, 551), (2008, 541), (2010, 522), (1996, 520), (1990, 536), (1790, 534)],
        -0.88, 0.88, "MAT_TRIM"), P, 0.005))
    for sign in (-1, 1):
        x0, x1 = sorted((sign * 0.83, sign * 0.955))
        obs.append(hard(mesh.plate(nm(P, f"AERO_Skirt_{'L' if sign > 0 else 'R'}"), c,
            [(650, 520), (1305, 520), (1322, 546), (668, 549)], x0, x1, "MAT_TRIM"), P, 0.004))
    obs.append(hard(mesh.plate(nm(P, "AERO_RearLip"), c,
        [(72, 494), (84, 514), (198, 531), (300, 545), (300, 522), (130, 500)],
        -0.80, 0.80, "MAT_TRIM"), P, 0.004))
    # rear wing: end plates, blade, uprights
    for sign in (-1, 1):
        x0, x1 = sorted((sign * L.WING_HALF, sign * (L.WING_HALF - 0.025)))
        obs.append(hard(mesh.plate(nm(P, f"WING_EndPlate_{'L' if sign > 0 else 'R'}"), c,
            L.WING_ENDPLATE, x0, x1, "MAT_TRIM"), P, 0.003))
        x0, x1 = sorted((sign * L.WING_UP_X, sign * (L.WING_UP_X + 0.03)))
        obs.append(hard(mesh.plate(nm(P, f"WING_Upright_{'L' if sign > 0 else 'R'}"), c,
            L.WING_UPRIGHT, x0, x1, "MAT_TRIM"), P, 0.003))
    obs.append(hard(mesh.plate(nm(P, "WING_Blade"), c, L.WING_BLADE, -L.WING_HALF + 0.01,
                               L.WING_HALF - 0.01, "MAT_TRIM"), P, 0.004))
    return obs


# ---------------------------------------------------------------------------------- lamps / grilles
def lamps(P):
    if P["stage"] < 2:
        return []
    obs = []
    for s in (-1, 1):
        t = 'L' if s > 0 else 'R'
        # slim front lens strips at the nose corners, amber marker on the fender
        y, z = L.P(1990, 398)
        obs.append(hard(mesh.box(nm(P, f"LAMP_Front_{t}"), P["coll"], (s * .66, y + .012, z), (.30, .028, .045),
                                 "MAT_LAMP"), P, 0.003))
        obs.append(hard(mesh.box(nm(P, f"LAMP_Marker_{t}"), P["coll"], (s * (surface_x(1900, 372) + .004), *L.P(1900, 372)),
                                 (.03, .07, .035), "MAT_RED"), P, 0.002))
        # tail lamp blocks (full-width strip split by the centre)
        y, z = L.P(66, 365)
        obs.append(hard(mesh.box(nm(P, f"LAMP_Tail_{t}"), P["coll"], (s * .42, y - .012, z), (.62, .03, .06),
                                 "MAT_RED"), P, 0.003))
    y, z = L.P(66, 365)
    obs.append(mesh.box(nm(P, "TRIM_TailBand"), P["coll"], (0, y - .004, z), (1.46, .02, .09), "MAT_TRIM"))
    y, z = L.P(1990, 402)
    obs.append(hard(mesh.box(nm(P, "BADGE_Honda"), P["coll"], (0, y + .012, z), (.075, .012, .05), "MAT_CHROME"), P, 0.002))
    # front fascia openings: centre intake + corner intakes
    y, z = L.P(1978, 470)
    obs.append(hard(mesh.box(nm(P, "GRILLE_Centre"), P["coll"], (0, y + .006, z), (.92, .02, .13), "MAT_TRIM"), P, 0.003))
    for s in (-1, 1):
        obs.append(hard(mesh.box(nm(P, f"GRILLE_Corner_{'L' if s > 0 else 'R'}"), P["coll"],
                                 (s * .72, y + .006, z + .01), (.2, .02, .10), "MAT_TRIM"), P, 0.003))
    return obs


# ---------------------------------------------------------------------------------- details
def details(P):
    if P["stage"] < 2:
        return []
    obs = []
    slope = math.atan2((304 - 276), (1845 - 1780) * 1.0) * 0.9
    for s in (-1, 1):
        t = 'L' if s > 0 else 'R'
        # closed pop-up headlamp covers on the hood (sunk so only a lip stands proud)
        y, z = L.P(1800, surface_v(1800, .60))
        obs.append(hard(mesh.box(nm(P, f"HOOD_PopUp_{t}"), P["coll"], (s * .60, y, z - .018),
            (.36, .36, .05), "MAT_BODY", rot=Matrix.Rotation(slope, 3, "X")), P, 0.008))
        y, z = L.P(1860, surface_v(1860, .60))
        obs.append(hard(mesh.box(nm(P, f"HOOD_PopUpVent_{t}"), P["coll"], (s * .60, y, z - .010),
            (.30, .05, .03), "MAT_TRIM", rot=Matrix.Rotation(slope, 3, "X")), P, 0.003))
        # mirror
        y, z = L.P(*L.MIRROR_UV)
        obs.append(mesh.cyl(nm(P, f"MIRROR_Stem_{t}"), P["coll"], (s * .78, y, z - .02), (s * .90, y, z + .015), .018, 8, "MAT_TRIM"))
        obs.append(hard(mesh.box(nm(P, f"MIRROR_Housing_{t}"), P["coll"], (s * .93, y, z + .03), (.12, .17, .095), "MAT_BODY"), P, 0.02))
        # door seam + handle + side intake recess
        hwd = tables.interp(L.BODY_HALF_W, 1000)
        pts = [L.P3(u, v, s * (hwd + 0.004)) for u, v in L.DOOR_SEAM]
        obs.append(mesh.tube(nm(P, f"TRIM_DoorSeam_{t}"), P["coll"], pts, .0022, 6, "MAT_TRIM"))
        obs.append(hard(mesh.box(nm(P, f"TRIM_Handle_{t}"), P["coll"], (s * (hwd + .006), *L.P(790, 262)), (.02, .09, .018), "MAT_TRIM"), P, 0.002))
        yi, zi = L.P(712, 372)
        obs.append(hard(mesh.box(nm(P, f"TRIM_SideIntake_{t}"), P["coll"], (s * (surface_x(712, 372) - .004), yi, zi),
                                 (.03, .26, .36), "MAT_TRIM"), P, 0.004))
        # exhaust tips (hidden / guessed)
    for s in (-1, 1):
        y, z = L.P(92, 498)
        obs.append(mesh.cyl(nm(P, f"UNCERTAIN_Exhaust_{'L' if s > 0 else 'R'}"), P["coll"],
                            (s * .34, y - .16, z), (s * .34, y - .005, z), .04, 14, "MAT_CHROME"))
    return obs


# ---------------------------------------------------------------------------------- hidden mass
def underbody(P):
    y0, y1 = Y(L.WHEEL_U[1] + P["arch"] + 4), Y(205)
    z0, z1 = Z(548), Z(L.WHEEL_V - P["arch"] - 1)
    return [mesh.box(nm(P, "UNCERTAIN_Underbody"), P["coll"], (0, (y0 + y1) / 2, (z0 + z1) / 2),
                     (1.30, abs(y1 - y0), abs(z1 - z0)), "MAT_TRIM")]


def interior(P):
    if P["stage"] < 2:
        return []
    obs = []
    for s in (-1, 1):
        y, z = L.P(1000, 255)
        obs.append(hard(mesh.box(nm(P, f"UNCERTAIN_Seat_{'L' if s > 0 else 'R'}"), P["coll"], (s * .34, y, z),
                                 (.42, .55, .5), "MAT_TRIM"), P, 0.02))
    y, z = L.P(1340, 238)
    obs.append(hard(mesh.box(nm(P, "UNCERTAIN_Dash"), P["coll"], (0, y, z), (1.2, .30, .14), "MAT_TRIM"), P, 0.02))
    return obs


PARTS = [
    Part("body", body, collision="hull"),
    Part("cabin", cabin, collision="hull"),
    Part("wheels", wheels, collision="hull"),
    Part("flares", flares, collision="none"),
    Part("aero", aero, collision="hull"),
    Part("lamps", lamps, collision="none"),
    Part("details", details, collision="none"),
    Part("underbody", underbody, collision="box"),
    Part("interior", interior, collision="none"),
]


def guide_points():
    return {"FRONT_AXLE": (0, -1.265, L.AXLE_Z), "REAR_AXLE": (0, 1.265, L.AXLE_Z)}
