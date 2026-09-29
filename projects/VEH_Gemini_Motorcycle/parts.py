"""
Part builders for VEH_Gemini_Motorcycle.

Every builder takes a LOD profile. Stage 1 uses LOW (blockout primitives), Stage 2 uses
HIGH (denser sections, subdivision on organic parts, bevels on hard parts, extra detail).
Placement always comes from landmarks.py, so Stage 2 cannot drift from the solved Stage 1
proportions. Library: workbench.bl.mesh / mods (docs/04_MODELING_TOOLKIT.md).
"""
import math
import bpy
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables
from workbench.bl import mesh, mods

mesh.set_ref(L.REF)

PALETTE = {
    "MAT_BODY_RED":   ((0.72, 0.04, 0.03), 0.6, 0.25),
    "MAT_BODY_BLACK": ((0.045, 0.045, 0.05), 0.0, 0.45),
    "MAT_METAL_DARK": ((0.06, 0.06, 0.065), 0.9, 0.45),
    "MAT_METAL_RAW":  ((0.62, 0.63, 0.65), 1.0, 0.3),
    "MAT_RUBBER":     ((0.045, 0.045, 0.045), 0.0, 0.9),
    "MAT_ENGINE":     ((0.08, 0.08, 0.085), 0.8, 0.5),
    "MAT_EXHAUST":    ((0.55, 0.52, 0.48), 1.0, 0.35),
    "MAT_GLASS":      dict(rgb=(0.85, 0.87, 0.9), metallic=0.0, roughness=0.05, alpha=0.35),
}

# name-prefix pairs that must never intersect (validate.intersections)
CRITICAL_PAIRS = [
    ("EXHAUST_", "FRAME_"), ("EXHAUST_", "UNCERTAIN_FRAME_"), ("EXHAUST_Header", "WHEEL_Front_Tire"),
    ("WHEEL_Rear_Tire", "FRAME_Swingarm"), ("SUSP_Fork", "BODY_Tank"), ("CTRL_", "BODY_Tank"),
    ("SUSP_Shock", "BODY_SidePanel"), ("EXHAUST_Muffler", "WHEEL_Rear_Tire"),
    ("ENGINE_", "FRAME_"), ("UNCERTAIN_ENGINE_", "FRAME_"), ("ENGINE_", "UNCERTAIN_FRAME_"),
    ("WHEEL_Front_Tire", "SUSP_Fork"), ("DRIVE_Chain", "WHEEL_Rear_Tire"),
]


def steering():
    """Fork axis and steering axis at rest (fork line through the front axle, RAKE_DEG)."""
    rake = math.radians(L.RAKE_DEG)
    up = Vector((0.0, math.sin(rake), math.cos(rake)))      # up-and-back along the fork
    back = Vector((0.0, math.cos(rake), -math.sin(rake)))   # perpendicular, rearward
    axle = Vector(L.FRONT_AXLE)
    top_len = (Vector(L.P3(*L.FORK_TOP_PX)) - axle).dot(up)
    fork = {"axle": axle, "up": up, "back": back, "len": top_len, "top": axle + up * top_len}
    base = axle + back * L.FORK_OFFSET
    st = {"top": base + up * (top_len + 0.01), "bottom": base + up * (top_len - 0.20), "up": up}
    return fork, st


def guide_points():
    return {
        "FRONT_AXLE": L.FRONT_AXLE, "REAR_AXLE": L.REAR_AXLE,
        "SWINGARM_PIVOT": L.P3(*L.SWINGARM_PIVOT_PX),
        "REAR_SHOCK_TOP": L.P3(*L.SHOCK_TOP_PX), "REAR_SHOCK_BOTTOM": L.P3(*L.SHOCK_BOTTOM_PX),
        "ENGINE_CENTER": L.P3(610, 470), "TANK_CENTER": L.P3(630, 285), "SEAT_CENTER": L.P3(440, 283),
        "HANDLEBAR_CENTER": L.P3(*L.GRIP_INNER_PX), "HEADLIGHT_CENTER": L.P3(*L.HEADLIGHT_PX),
        "STEERING_TOP": tuple(steering()[1]["top"]), "STEERING_BOTTOM": tuple(steering()[1]["bottom"]),
    }


LOW = dict(name="LOW", tube=8, tube_s=2, lathe=20, loft=12, tank_st=10, seat_st=5,
           subsurf=0, bevel=False, prefix="", C_PRIMARY="02_LOW_PRIMARY",
           C_SECONDARY="03_LOW_SECONDARY", C_MECH="04_LOW_MECHANICAL", C_DETAIL="04_LOW_MECHANICAL")
HIGH = dict(name="HIGH", tube=20, tube_s=6, lathe=72, loft=28, tank_st=34, seat_st=14,
            subsurf=2, bevel=True, prefix="", C_PRIMARY="05_HIGH_BODY",
            C_SECONDARY="05_HIGH_BODY", C_MECH="06_HIGH_MECHANICAL", C_DETAIL="07_DETAILS")

P3 = L.P3


def nm(lod, name):
    return name if lod["name"] == "HIGH" else name + "_LOW"


def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def smooth(ob, lod, levels=None, bevel=None):
    lv = 0 if levels is None else min(levels, lod["subsurf"])   # hard-surface: bevel only
    if lv:
        mods.subsurf(ob, 1, lv)          # export/viewport L1, render L2
    if lod["bevel"] and bevel:
        mods.bevel(ob, bevel, 2)
        mods.weighted_normal(ob)
    return ob


# ============================================================================ WHEELS
def tyre_profile(R, W, rim_r, lod):
    """closed (radius, lateral) section: bead -> sidewall bulge -> rounded crown -> mirror."""
    side = R - rim_r
    if lod["name"] == "LOW":
        half = [(rim_r, 0.40 * W), (rim_r + 0.5 * side, 0.50 * W), (R - 0.02, 0.44 * W), (R, 0.0)]
    else:
        half = [(rim_r, 0.40 * W), (rim_r + 0.12 * side, 0.445 * W), (rim_r + 0.3 * side, 0.485 * W),
                (rim_r + 0.5 * side, 0.50 * W), (rim_r + 0.68 * side, 0.49 * W),
                (rim_r + 0.8 * side, 0.465 * W)]
        for j in range(9):
            w = 0.44 * W * (1 - j / 8.0)
            half.append((R - 0.12 * side * (w / (0.44 * W)) ** 2, w))
    full = [(r, -w) for (r, w) in half] + [(r, w) for (r, w) in reversed(half[:-1])]
    return full


def wheel(lod, side, R, W, rim_w, center, spokes=5):
    c = Vector(center)
    CP, CM = lod["C_PRIMARY"], lod["C_MECH"]
    tag = "Front" if side == "F" else "Rear"
    rim_r = 0.2159
    t = mesh.lathe(nm(lod, f"WHEEL_{tag}_Tire"), CP, c, tyre_profile(R, W, rim_r, lod),
                lod["lathe"], "MAT_RUBBER")
    # rim: flange + barrel (closed profile)
    hw = rim_w / 2
    rim_prof = [(rim_r + 0.012, -hw), (rim_r + 0.012, -hw + 0.008), (rim_r - 0.002, -hw + 0.012),
                (rim_r - 0.004, hw - 0.012), (rim_r + 0.012, hw - 0.008), (rim_r + 0.012, hw),
                (rim_r - 0.022, hw - 0.004), (rim_r - 0.026, 0.0), (rim_r - 0.022, -hw + 0.004)]
    rim = mesh.lathe(nm(lod, f"WHEEL_{tag}_Rim"), CP, c, rim_prof, lod["lathe"], "MAT_METAL_DARK",
                  sharp_angle=50)
    hub_w = 0.13 if side == "F" else 0.16
    hub = mesh.lathe(nm(lod, f"WHEEL_{tag}_Hub"), CM, c,
                  [(0.012, -hub_w / 2), (0.055, -hub_w / 2), (0.062, -hub_w / 2 + 0.02),
                   (0.062, hub_w / 2 - 0.02), (0.055, hub_w / 2), (0.012, hub_w / 2)],
                  max(12, lod["lathe"] // 3), "MAT_METAL_DARK", closed=False)
    # spokes: Y-split pairs (5 x 2) in the rim centre plane
    n = spokes
    parts = []
    for k in range(n):
        a0 = 2 * math.pi * k / n + (0.3 if side == "F" else 0.0)
        for s in (-1, 1):
            a_hub = a0
            a_rim = a0 + s * 0.16
            p0 = c + Vector((0, math.cos(a_hub) * 0.055, math.sin(a_hub) * 0.055))
            p1 = c + Vector((0, math.cos(a_rim) * (rim_r - 0.02), math.sin(a_rim) * (rim_r - 0.02)))
            ob = mesh.tube(nm(lod, f"WHEEL_{tag}_Spoke_{k}{'ab'[s > 0]}"), CM, [p0, p1],
                        [0.011, 0.007], 6 if lod["name"] == "LOW" else 10, "MAT_METAL_DARK",
                        smooth_path=False)
            parts.append(ob)
    if lod["name"] == "HIGH":
        mods.weighted_normal(rim)
    return [t, rim, hub] + parts


def brake_disc(lod, name, center, x, r_out, r_in, thick=0.005, drilled=True):
    c = Vector(center) + Vector((x, 0, 0))
    col = lod["C_MECH"]
    ob = mesh.lathe(nm(lod, name), col, c,
                 [(r_in, -thick / 2), (r_out, -thick / 2), (r_out, thick / 2), (r_in, thick / 2)],
                 lod["lathe"], "MAT_METAL_RAW", sharp_angle=30)
    out = [ob]
    # carrier (inner spider) as a thin ring to hub
    out.append(mesh.lathe(nm(lod, name + "_Carrier"), col, c,
                       [(0.055, -0.004), (r_in + 0.004, -0.004), (r_in + 0.004, 0.004), (0.055, 0.004)],
                       max(12, lod["lathe"] // 2), "MAT_METAL_DARK", sharp_angle=30))
    if lod["name"] == "HIGH" and drilled:
        # drilled pattern: dark plugs flush on both faces (reads as holes, keeps disc topology clean)
        specs = []
        for ri, rr in enumerate([r_in + (r_out - r_in) * f for f in (0.3, 0.55, 0.8)]):
            for i in range(30):
                a = 2 * math.pi * (i + 0.5 * ri) / 30
                q = c + Vector((0, math.cos(a) * rr, math.sin(a) * rr))
                specs.append((q + Vector((-thick * 0.55, 0, 0)), q + Vector((thick * 0.55, 0, 0)), 0.0035))
        out.append(mesh.multi_cyl(name + "_Holes", lod["C_DETAIL"], specs, 6, "MAT_METAL_DARK"))
    return out


def wheels(lod):
    out = []
    out += wheel(lod, "F", L.R_TYRE_F, L.W_TYRE_F, 0.089, L.FRONT_AXLE)
    out += wheel(lod, "R", L.R_TYRE_R, L.W_TYRE_R, 0.14, L.REAR_AXLE)
    return out


def brakes(lod):
    out = []
    for s, x in (("R", -0.072), ("L", 0.072)):
        out += brake_disc(lod, f"BRAKE_Front_Disc_{s}", L.FRONT_AXLE, x, 0.155, 0.098)
        cp = Vector(P3(803, 468))
        cx = x + (0.018 if x > 0 else -0.018)
        ob = mesh.box(nm(lod, f"BRAKE_Front_Caliper_{s}"), lod["C_MECH"], (cx, cp.y, cp.z),
                   (0.035, 0.05, 0.11), "MAT_METAL_DARK",
                   rot=Matrix.Rotation(math.radians(35), 3, "X"))
        smooth(ob, lod, bevel=0.006)
        out.append(ob)
    out += brake_disc(lod, "BRAKE_Rear_Disc", L.REAR_AXLE, -0.078, 0.135, 0.075, drilled=False)
    cp = Vector(P3(277, 412))
    ob = mesh.box(nm(lod, "BRAKE_Rear_Caliper"), lod["C_MECH"], (-0.092, cp.y, cp.z),
               (0.035, 0.07, 0.045), "MAT_METAL_DARK")
    smooth(ob, lod, bevel=0.005)
    out.append(ob)
    # axles
    fa, ra = Vector(L.FRONT_AXLE), Vector(L.REAR_AXLE)
    out.append(mesh.cyl(nm(lod, "SUSP_Front_Axle"), lod["C_MECH"], fa + Vector((-0.13, 0, 0)),
                     fa + Vector((0.13, 0, 0)), 0.012, 12, "MAT_METAL_RAW"))
    out.append(mesh.cyl(nm(lod, "SUSP_Rear_Axle"), lod["C_MECH"], ra + Vector((-0.17, 0, 0)),
                     ra + Vector((0.17, 0, 0)), 0.013, 12, "MAT_METAL_RAW"))
    return out


# ============================================================================ BODY
def _se_v(phi, vt, vb, vmid, et, eb):
    s = math.sin(phi)
    if s >= 0:
        return vmid - (vmid - vt) * abs(s) ** (2.0 / et)
    return vmid + (vb - vmid) * abs(s) ** (2.0 / eb)


def _se_x(phi, hw, et, eb):
    c, s = math.cos(phi), math.sin(phi)
    return hw * abs(c) ** (2.0 / (et if s >= 0 else eb))


def tank_ring(u, vt, vb, hw, v_bound, recess, n_up, n_low, et=2.5, eb=5.0, wd=0.62):
    """One side (top centre -> bottom centre) with a vertex exactly on the paint line v_bound,
    plus a second vertex 1.5 px below it where the black flank steps inward."""
    vmid = vt + (vb - vt) * (1.0 - wd)
    v_bound = min(max(v_bound, vt + 1.0), vb - 3.0)
    lo, hi = -math.pi / 2, math.pi / 2          # v(phi) decreases with phi
    for _ in range(40):
        m = (lo + hi) / 2
        if _se_v(m, vt, vb, vmid, et, eb) > v_bound:
            lo = m
        else:
            hi = m
    pb = (lo + hi) / 2
    side = []
    for i in range(n_up + 1):                   # top centre .. boundary
        ph = math.pi / 2 + (pb - math.pi / 2) * i / n_up
        side.append((_se_x(ph, hw, et, eb), _se_v(ph, vt, vb, vmid, et, eb), False))
    kb = len(side) - 1
    lo2, hi2 = -math.pi / 2, pb                 # step just below boundary
    target = min(v_bound + 1.5, vb - 1.0)
    for _ in range(40):
        m = (lo2 + hi2) / 2
        if _se_v(m, vt, vb, vmid, et, eb) > target:
            lo2 = m
        else:
            hi2 = m
    ps = (lo2 + hi2) / 2
    for i in range(n_low + 1):                  # step .. bottom centre
        ph = ps + (-math.pi / 2 - ps) * i / n_low
        side.append((_se_x(ph, hw, et, eb) * recess, _se_v(ph, vt, vb, vmid, et, eb), True))
    return side, kb


def tank(lod):
    n_st = lod["tank_st"]
    stations = []
    us = lin(493.0, 755.0, n_st)
    for u in us:
        vt = tables.polyline_v(L.TANK_TOP, u)
        vb = tables.polyline_v(L.TANK_BOTTOM, u)
        hw = tables.interp(L.TANK_HALF_WIDTH, u)
        stations.append((u, vt, max(vb, vt + 2.0), hw, 2.5, 5.0, 0.62))
    if lod["name"] == "LOW":
        ob = mesh.loft_px(nm(lod, "BODY_Tank"), lod["C_PRIMARY"], stations, lod["loft"], "MAT_BODY_RED")
        return [ob]
    # HIGH: paint-line-aware loft, black knee recess, creased lip, 2 materials
    import bmesh
    bm = bmesh.new()
    crease = bm.edges.layers.float.new("crease_edge")
    rings, blacks = [], []
    for (u, vt, vb, hw, et, eb, wd) in stations:
        black = u < L.TANK_BLACK_U_MAX
        vbnd = tables.polyline_v(L.TANK_BLACK_BOUNDARY, u) if black else vt + (vb - vt) * 0.62
        side, kb = tank_ring(u, vt, vb, hw, vbnd, L.TANK_RECESS if black else 1.0, 9, 7)
        ring = [(x, v) for (x, v, _) in side]
        ring += [(-x, v) for (x, v) in reversed(ring[1:-1])]
        rings.append([bm.verts.new(L.P3(u, v, x)) for (x, v) in ring])
        blacks.append(black)
    n = len(rings[0])
    half = 9 + 1 + 7 + 1                          # verts per side incl. both centres
    for i in range(len(rings) - 1):
        for k in range(n):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % n], rings[i + 1][(k + 1) % n], rings[i + 1][k]))
            # side index of this face band (0 = top) ; black if below boundary on a black station
            kk = k if k < half - 1 else (n - 1 - k)
            f.material_index = 1 if (blacks[i] and blacks[i + 1] and kk >= 9) else 0
    for i in range(len(rings) - 1):
        if blacks[i] and blacks[i + 1]:
            for k in (9, 10, n - 9, n - 10):
                e = bm.edges.get((rings[i][k], rings[i + 1][k]))
                if e:
                    e[crease] = 0.85
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    ob = mesh.finish(nm(lod, "BODY_Tank"), bm, lod["C_PRIMARY"], "MAT_BODY_RED", sharp_angle=75)
    ob.data.materials.append(bpy.data.materials["MAT_BODY_BLACK"])
    mods.subsurf(ob, 1, 2)
    # flush aero filler cap on the crown (UNCERTAIN: top of tank not visible in photo)
    cy, cz = L.P(640, 241)
    cap = mesh.lathe("UNCERTAIN_BODY_Tank_FillerCap", lod["C_DETAIL"], (0.0, cy, cz - 0.005),
                  [(0.001, 0.0), (0.042, 0.0), (0.045, 0.004), (0.04, 0.007), (0.001, 0.007)],
                  32, "MAT_METAL_RAW", axis="Z", closed=True)
    return [ob, cap]


def seat(lod):
    out = []
    n = lod["seat_st"]
    st = []
    for u in lin(405.0, 500.0, n):
        vt = tables.polyline_v(L.SEAT_TOP, u)
        vb = tables.polyline_v(L.SEAT_BOTTOM_V, u)
        st.append((u, vt, vb, tables.interp(L.SEAT_HALF_WIDTH, u), 3.2, 6.0, 0.45))
    ob = mesh.loft_px(nm(lod, "BODY_Seat"), lod["C_PRIMARY"], st, lod["loft"], "MAT_BODY_BLACK")
    out.append(smooth(ob, lod, levels=2))
    st = []
    for u in lin(333.0, 410.0, max(4, n)):
        vt = tables.polyline_v(L.HUMP_TOP, u)
        vb = tables.polyline_v(L.HUMP_BOTTOM_V, u)
        st.append((u, vt, vb, tables.interp(L.HUMP_HALF_WIDTH, u), 5.0, 7.0, 0.35))
    ob = mesh.loft_px(nm(lod, "BODY_Seat_Hump"), lod["C_PRIMARY"], st, lod["loft"], "MAT_BODY_BLACK")
    out.append(smooth(ob, lod, levels=2))
    st = []
    for u in lin(303.0, 495.0, max(6, n + 4)):
        vt = tables.polyline_v(L.TAIL_TOP, u)
        vb = tables.polyline_v(L.TAIL_BOTTOM, u)
        st.append((u, vt, max(vb, vt + 2.0), tables.interp(L.TAIL_HALF_WIDTH, u), 5.0, 5.0, 0.5))
    ob = mesh.loft_px(nm(lod, "BODY_Tail"), lod["C_PRIMARY"], st, max(10, lod["loft"] // 2),
                   "MAT_BODY_BLACK")
    out.append(smooth(ob, lod, levels=1))
    ob = mesh.plate(nm(lod, "BODY_TailLight"), lod["C_SECONDARY"], L.TAILLIGHT_POLY, -0.035, 0.035,
                 "MAT_BODY_RED")
    out.append(smooth(ob, lod, bevel=0.003))
    for s, (x0, x1) in (("L", (0.112, 0.124)), ("R", (-0.124, -0.112))):
        ob = mesh.plate(nm(lod, f"BODY_SidePanel_{s}"), lod["C_SECONDARY"], L.SIDEPANEL_POLY, x0, x1,
                     "MAT_BODY_BLACK")
        out.append(smooth(ob, lod, bevel=0.004))
    return out


# ============================================================================ FRAME
def frame(lod):
    out = []
    C = lod["C_PRIMARY"]
    seg, smp = lod["tube"], lod["tube_s"]
    fork, st = steering()
    ht = mesh.cyl(nm(lod, "FRAME_HeadTube"), C, st["bottom"] - st["up"] * 0.02, st["top"] - st["up"] * 0.05,
               0.03, seg, "MAT_METAL_DARK")
    out.append(ht)

    def rail(name, pts, xs, r=0.016, mat="MAT_METAL_DARK"):
        for s, sg in (("L", 1), ("R", -1)):
            xl = xs if isinstance(xs, (list, tuple)) else [xs] * len(pts)
            p = [P3(u, v, sg * x) for (u, v), x in zip(pts, xl)]
            out.append(mesh.tube(nm(lod, f"{name}_{s}"), C, p, r, seg, mat, samples=smp))

    rail("FRAME_Backbone", L.FRAME_BACKBONE, [0.035, 0.07, 0.09, 0.10, 0.105, 0.11], 0.018)
    rail("FRAME_RearDown", L.FRAME_REAR_DOWN, [0.11, 0.115, 0.118, 0.118], 0.018)
    rail("UNCERTAIN_FRAME_Downtube", L.FRAME_DOWNTUBE, [0.04, 0.05, 0.06], 0.016)
    rail("FRAME_Subframe_Upper", L.FRAME_SUB_UPPER, [0.05, 0.065, 0.075, 0.08, 0.09, 0.105], 0.011,
         "MAT_METAL_RAW")
    rail("FRAME_Subframe_Lower", L.FRAME_SUB_LOWER, [0.08, 0.095, 0.108, 0.115], 0.012)
    # cross member at the tail and under the seat
    for i, (u, v, x) in enumerate(((330, 279, 0.058), (470, 301, 0.085))):
        out.append(mesh.cyl(nm(lod, f"UNCERTAIN_FRAME_Crossmember_{i}"), C, P3(u, v, -x), P3(u, v, x),
                         0.009, seg, "MAT_METAL_DARK"))
    for s, (x0, x1) in (("L", (0.145, 0.163)), ("R", (-0.163, -0.145))):
        ob = mesh.plate(nm(lod, f"FRAME_PivotPlate_{s}"), C, L.PIVOT_PLATE_POLY, x0, x1, "MAT_METAL_DARK")
        out.append(smooth(ob, lod, bevel=0.004))
    return out


# ============================================================================ FRONT
def front(lod):
    out = []
    C = lod["C_MECH"]
    seg = max(lod["tube"], 10)
    fork, st = steering()
    ax, up = fork["axle"], fork["up"]
    top = fork["len"]
    for s, sg in (("L", 1), ("R", -1)):
        x = Vector((sg * L.FORK_SPACING, 0, 0))
        # USD fork: black outer tube on top, chrome inner tube below, black axle foot
        out.append(mesh.cyl(nm(lod, f"SUSP_Fork_Outer_{s}"), C, ax + x + up * (top + 0.02),
                         ax + x + up * (top - 0.43), 0.028, seg, "MAT_METAL_DARK"))
        out.append(mesh.cyl(nm(lod, f"SUSP_Fork_Inner_{s}"), C, ax + x + up * (top - 0.43),
                         ax + x + up * 0.06, 0.0235, seg, "MAT_METAL_RAW"))
        foot = mesh.cyl(nm(lod, f"SUSP_Fork_Foot_{s}"), C, ax + x + up * 0.07, ax + x - up * 0.035,
                     0.03, seg, "MAT_METAL_DARK")
        out.append(foot)
        if lod["name"] == "HIGH":
            # dust seal ring and axle pinch bolts
            out.append(mesh.cyl(f"SUSP_Fork_Seal_{s}", lod["C_DETAIL"], ax + x + up * (top - 0.43),
                             ax + x + up * (top - 0.45), 0.030, seg, "MAT_RUBBER"))
    # triple clamps
    for name, off, h in (("SUSP_TopClamp", top - 0.005, 0.022), ("SUSP_BottomClamp", top - 0.175, 0.04)):
        c = ax + up * off + fork["back"] * 0.012
        rot = Matrix.Rotation(-math.radians(L.RAKE_DEG), 3, "X")
        ob = mesh.box(nm(lod, name), C, c, (2 * L.FORK_SPACING + 0.075, 0.075, h), "MAT_METAL_DARK", rot=rot)
        out.append(smooth(ob, lod, bevel=0.004))
    out.append(mesh.cyl(nm(lod, "SUSP_SteeringStem"), C, st["bottom"], st["top"], 0.02, seg, "MAT_METAL_DARK"))
    # headlight (axis along Y, front face at u~815)
    hc = Vector(P3(*L.HEADLIGHT_PX))
    fy = Vector(P3(815, L.HEADLIGHT_PX[1])).y
    R = L.HEADLIGHT_R
    prof = [(0.001, hc.y + 0.05), (R * 0.55, hc.y + 0.045), (R * 0.9, hc.y + 0.02), (R, hc.y - 0.01),
            (R + 0.004, fy + 0.012), (R + 0.004, fy), (R * 0.88, fy - 0.001), (0.001, fy - 0.004)]
    prof = [(r, y - hc.y) for (r, y) in prof]
    out.append(mesh.lathe(nm(lod, "CTRL_Headlight_Housing"), lod["C_SECONDARY"], hc, prof,
                       max(16, lod["lathe"] // 2), "MAT_BODY_BLACK", axis="Y", closed=True))
    out.append(mesh.lathe(nm(lod, "CTRL_Headlight_Lens"), lod["C_SECONDARY"],
                       Vector((0, fy - 0.001, hc.z)),
                       [(0.001, -0.012), (R * 0.86, -0.004), (R * 0.87, 0.002), (0.001, 0.002)],
                       max(16, lod["lathe"] // 2), "MAT_GLASS", axis="Y", closed=True))
    for s, sg in (("L", 1), ("R", -1)):
        p0 = hc + Vector((sg * (R + 0.002), 0.0, 0.0))
        p1 = ax + Vector((sg * L.FORK_SPACING, 0, 0)) + up * (top - 0.13)
        out.append(mesh.tube(nm(lod, f"CTRL_Headlight_Bracket_{s}"), lod["C_SECONDARY"],
                          [p0, p0 + Vector((sg * 0.012, 0.015, 0)), p1], 0.007, 8, "MAT_METAL_DARK",
                          smooth_path=False))
    # clip-on bars
    gi = Vector(P3(*L.GRIP_INNER_PX)); ge = Vector(P3(*L.GRIP_END_PX))
    for s, sg in (("L", 1), ("R", -1)):
        clamp = ax + Vector((sg * L.FORK_SPACING, 0, 0)) + up * (top - 0.035)
        end = Vector((sg * 0.335, ge.y, ge.z))
        mid = clamp + (end - clamp) * 0.35
        out.append(mesh.cyl(nm(lod, f"CTRL_ClipOn_{s}"), C, clamp, mid, 0.034 if lod["name"] == "HIGH" else 0.03,
                         seg, "MAT_METAL_DARK"))
        out.append(mesh.cyl(nm(lod, f"CTRL_Handlebar_{s}"), C, clamp, end, 0.011, seg, "MAT_METAL_DARK"))
        g0 = clamp + (end - clamp) * 0.52
        grip = mesh.cyl(nm(lod, f"CTRL_Grip_{s}"), lod["C_SECONDARY"], g0, end + (end - clamp).normalized() * 0.012,
                     0.017, seg, "MAT_RUBBER")
        out.append(grip)
        # control housing + lever
        ch = clamp + (end - clamp) * 0.46
        out.append(mesh.box(nm(lod, f"CTRL_SwitchHousing_{s}"), lod["C_SECONDARY"], ch,
                         (0.04, 0.045, 0.045), "MAT_BODY_BLACK"))
        lev0 = ch + Vector((0, -0.03, 0.0))
        lev1 = end + Vector((0, -0.06, -0.01))
        out.append(mesh.tube(nm(lod, f"CTRL_Lever_{s}"), lod["C_SECONDARY"], [lev0, lev1], 0.006, 6,
                          "MAT_METAL_RAW", smooth_path=False))
        rp = L.RESERVOIR_L_PX if sg > 0 else L.RESERVOIR_R_PX
        rc = Vector(P3(rp[0], rp[1] + 8, 0.0))
        rc.x = ch.x - sg * 0.01
        out.append(mesh.cyl(nm(lod, f"CTRL_Reservoir_{s}"), lod["C_SECONDARY"], rc - Vector((0, 0, 0.016)),
                         rc + Vector((0, 0, 0.018)), 0.02, seg, "MAT_METAL_RAW"))
        out.append(mesh.tube(nm(lod, f"CTRL_ReservoirStem_{s}"), lod["C_SECONDARY"],
                          [rc - Vector((0, 0, 0.016)), ch + Vector((0, 0, 0.02))], 0.006, 6,
                          "MAT_METAL_DARK", smooth_path=False))
    return out


# ============================================================================ REAR
def rear(lod):
    out = []
    C = lod["C_MECH"]
    seg = max(lod["tube"], 10)
    pv = Vector(P3(*L.SWINGARM_PIVOT_PX))
    poly = [(495, 458), (300, 459), (268, 461), (262, 468), (262, 482), (268, 489),
            (300, 491), (495, 490), (507, 480), (507, 468)]
    for s, (x0, x1) in (("L", (0.112, 0.142)), ("R", (-0.142, -0.112))):
        ob = mesh.plate(nm(lod, f"FRAME_Swingarm_{s}"), C, poly, x0, x1, "MAT_METAL_DARK")
        out.append(smooth(ob, lod, levels=0, bevel=0.005))
    cb = Vector(P3(470, 474))
    ob = mesh.box(nm(lod, "FRAME_Swingarm_Brace"), C, cb, (0.224, 0.05, 0.05), "MAT_METAL_DARK")
    out.append(smooth(ob, lod, bevel=0.004))
    out.append(mesh.cyl(nm(lod, "FRAME_Swingarm_PivotShaft"), C, pv + Vector((-0.175, 0, 0)),
                     pv + Vector((0.175, 0, 0)), 0.012, seg, "MAT_METAL_RAW"))
    for s, sg in (("L", 1), ("R", -1)):
        out.append(mesh.cyl(nm(lod, f"FASTENER_PivotBolt_{s}"), C, pv + Vector((sg * 0.163, 0, 0)),
                         pv + Vector((sg * 0.175, 0, 0)), 0.02, 6, "MAT_METAL_RAW"))
    # rear shock (UNCERTAIN mount points) - centred monoshock
    sb, stp = Vector(P3(*L.SHOCK_BOTTOM_PX)), Vector(P3(*L.SHOCK_TOP_PX))
    d = (stp - sb)
    out.append(mesh.cyl(nm(lod, "SUSP_Shock_Rear_Body"), C, sb, stp, 0.022, seg, "MAT_METAL_RAW"))
    out.append(mesh.cyl(nm(lod, "SUSP_Shock_Rear_Reservoir"), C, stp - d * 0.25, stp + d * 0.02, 0.028,
                     seg, "MAT_METAL_RAW"))
    if lod["name"] == "LOW":
        out.append(mesh.cyl("SUSP_Shock_Rear_Spring_LOW", C, sb + d * 0.1, sb + d * 0.62, 0.034, 10,
                         "MAT_BODY_RED"))
    else:
        # helix spring
        dn = d.normalized()
        n1, n2 = mesh.frame_for(dn)
        pts = []
        turns, steps = 7, 7 * 16
        for i in range(steps + 1):
            t = i / steps
            a = 2 * math.pi * turns * t
            pts.append(sb + d * (0.1 + 0.52 * t) + 0.031 * (math.cos(a) * n1 + math.sin(a) * n2))
        out.append(mesh.tube("SUSP_Shock_Rear_Spring", C, pts, 0.0055, 8, "MAT_BODY_RED", smooth_path=False))
    # chain (left side, +X): sprockets + chain run
    ra = Vector(L.REAR_AXLE)
    fs = Vector(P3(522, 468))
    xs = 0.105
    out.append(mesh.lathe(nm(lod, "DRIVE_Sprocket_Rear"), C, ra + Vector((xs, 0, 0)),
                       [(0.06, -0.004), (0.098, -0.004), (0.098, 0.004), (0.06, 0.004)],
                       max(16, lod["lathe"] // 2), "MAT_METAL_RAW"))
    out.append(mesh.lathe(nm(lod, "DRIVE_Sprocket_Front"), C, fs + Vector((xs, 0, 0)),
                       [(0.01, -0.005), (0.042, -0.005), (0.042, 0.005), (0.01, 0.005)],
                       16, "MAT_METAL_RAW"))
    loop = []
    for i in range(25):                              # rear sprocket, wraps the back
        a = -math.pi / 2 + math.pi * i / 24
        loop.append(ra + Vector((xs, math.cos(a) * 0.1, math.sin(a) * 0.1)))
    for i in range(13):                              # front sprocket, wraps the front
        a = math.pi / 2 + math.pi * i / 12
        loop.append(fs + Vector((xs, math.cos(a) * 0.045, math.sin(a) * 0.045)))
    loop.append(loop[0])
    out.append(mesh.tube(nm(lod, "DRIVE_Chain"), C, loop, 0.006, 6, "MAT_METAL_DARK", smooth_path=False,
                      caps=False))
    # rearsets
    for s, sg in (("L", 1), ("R", -1)):
        ob = mesh.plate(nm(lod, f"CTRL_Rearset_Plate_{s}"), lod["C_SECONDARY"], L.REARSET_PLATE_POLY,
                     sg * 0.165, sg * 0.175, "MAT_METAL_DARK")
        out.append(smooth(ob, lod, bevel=0.002))
        fp = Vector(P3(*L.FOOTPEG_PX))
        out.append(mesh.cyl(nm(lod, f"CTRL_Footpeg_{s}"), lod["C_SECONDARY"],
                         Vector((sg * 0.175, fp.y, fp.z)), Vector((sg * 0.25, fp.y, fp.z)), 0.011, seg,
                         "MAT_METAL_RAW"))
        lever_end = Vector(P3(480, 432, sg * 0.18))
        out.append(mesh.tube(nm(lod, "CTRL_BrakePedal" if sg < 0 else "CTRL_Shifter"), lod["C_SECONDARY"],
                          [Vector((sg * 0.18, fp.y, fp.z + 0.02)), lever_end,
                           lever_end + Vector((sg * 0.03, 0, 0))], 0.006, 6, "MAT_METAL_RAW",
                          smooth_path=False))
    return out


# ============================================================================ ENGINE
def engine(lod):
    out = []
    C = lod["C_MECH"]
    ob = mesh.plate(nm(lod, "ENGINE_Crankcase"), C, L.CRANKCASE_POLY, -0.20, 0.20, "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.012))
    ob = mesh.plate(nm(lod, "ENGINE_Transmission"), C, L.TRANSMISSION_POLY, -0.085, 0.085, "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.01))
    (a_u, a_v), (b_u, b_v), (c_u, c_v), (d_u, d_v) = L.CYL_POLY
    t = 0.58                                     # block / head split along the tilted bank
    r_mid = (a_u + (d_u - a_u) * t, a_v + (d_v - a_v) * t)
    f_mid = (b_u + (c_u - b_u) * t, b_v + (c_v - b_v) * t)
    ins = 9.0 if lod["name"] == "HIGH" else 0.0   # HIGH: finned core inset, fins stand proud
    blk = [(a_u + ins, a_v), (b_u - ins, b_v), (f_mid[0] - ins, f_mid[1]), (r_mid[0] + ins, r_mid[1])]
    ob = mesh.plate(nm(lod, "ENGINE_Block"), C, blk, -0.19 if ins else -0.2, 0.19 if ins else 0.2, "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.006))
    hd = [(r_mid[0] + ins * 0.6, r_mid[1]), (f_mid[0] - ins * 0.6, f_mid[1]), (c_u, c_v), (d_u, d_v)]
    ob = mesh.plate(nm(lod, "ENGINE_Head"), C, hd, -0.2 if ins else -0.205, 0.2 if ins else 0.205,
                 "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.006))
    ob = mesh.plate(nm(lod, "UNCERTAIN_ENGINE_Airbox"), C, L.AIRBOX_POLY, -0.07, 0.07, "MAT_BODY_BLACK")
    out.append(smooth(ob, lod, bevel=0.01))
    ob = mesh.plate(nm(lod, "ENGINE_CamCover"), C, L.CAMCOVER_POLY, -0.185, 0.185, "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.008))
    # covers: right side seen in photo; left side mirrored conservatively
    for s, sg in (("R", -1), ("L", 1)):
        pre = "" if s == "R" else "UNCERTAIN_"
        c = Vector(P3(*L.ALT_COVER_PX))
        r = L.ALT_COVER_R / L.S
        ob = mesh.lathe(nm(lod, f"{pre}ENGINE_Cover_Main_{s}"), C, c + Vector((sg * 0.2, 0, 0)),
                     [(0.001, sg * 0.03), (r * 0.86, sg * 0.03), (r * 0.97, sg * 0.022), (r, sg * 0.012), (r, 0.0), (0.001, 0.0)],
                     max(16, lod["lathe"] // 2), "MAT_ENGINE", closed=True)
        out.append(ob)
        c = Vector(P3(*L.SMALL_COVER_PX))
        r = L.SMALL_COVER_R / L.S
        ob = mesh.lathe(nm(lod, f"{pre}ENGINE_Cover_Small_{s}"), C, c + Vector((sg * 0.2, 0, 0)),
                     [(0.001, sg * 0.022), (r * 0.85, sg * 0.022), (r, sg * 0.01), (r, 0.0), (0.001, 0.0)],
                     max(12, lod["lathe"] // 3), "MAT_ENGINE", closed=True)
        out.append(ob)
    u0, v0, u1, v1 = L.CARB_BOX
    iu0, iv0, iu1, iv1 = L.INTAKE_BOX
    for i, x in enumerate((-0.15, -0.05, 0.05, 0.15)):
        a = Vector(P3(u0, (v0 + v1) / 2, x)); b = Vector(P3(u1, (v0 + v1) / 2 + 6, x))
        out.append(mesh.cyl(nm(lod, f"ENGINE_Carb_{i + 1}"), C, a, b, 0.036, max(10, lod["tube"]),
                         "MAT_METAL_RAW"))
        a2 = Vector(P3(524, (iv0 + iv1) / 2, x * 0.42))       # boots converge into the airbox
        out.append(mesh.cyl(nm(lod, f"ENGINE_Intake_{i + 1}"), C, a2, a + (a2 - a) * 0.02,
                         0.03, max(10, lod["tube"]), "MAT_RUBBER", r1=0.033))
    # sump
    ob = mesh.box(nm(lod, "ENGINE_Sump"), C, P3(600, 546), (0.26, 0.28, 0.04), "MAT_ENGINE")
    out.append(smooth(ob, lod, bevel=0.01))
    if lod["name"] == "HIGH":
        out += engine_fins(lod)
    return out


def engine_fins(lod):
    """Cooling fins on the tilted cylinder bank: one fin profile repeated up the bank, one object."""
    import bmesh
    (a_u, a_v), (b_u, b_v), (c_u, c_v), (d_u, d_v) = L.CYL_POLY
    bm = bmesh.new()
    n = 15
    for i in range(n):
        t = 0.05 + 0.85 * i / (n - 1)
        if 0.555 < t < 0.61:                     # interruption at the block/head joint
            continue
        r0 = (a_u + (d_u - a_u) * t, a_v + (d_v - a_v) * t)
        f0 = (b_u + (c_u - b_u) * t, b_v + (c_v - b_v) * t)
        poly = [(r0[0] - 2, r0[1] + 1.0), (f0[0] + 4, f0[1] + 1.0), (f0[0] + 4, f0[1] - 1.0),
                (r0[0] - 2, r0[1] - 1.0)]
        a = [bm.verts.new(L.P3(u, v, -0.214)) for (u, v) in poly]
        b = [bm.verts.new(L.P3(u, v, 0.214)) for (u, v) in poly]
        bm.faces.new(a); bm.faces.new(list(reversed(b)))
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    ob = mesh.finish("ENGINE_Fins", bm, lod["C_DETAIL"], "MAT_ENGINE", smooth=False)
    return [ob]


# ============================================================================ EXHAUST
def exhaust(lod):
    out = []
    C = lod["C_MECH"]
    seg, smp = max(lod["tube"], 10), lod["tube_s"]
    fa = Vector(L.FRONT_AXLE)
    clear = L.R_TYRE_F + 0.035 + 0.019
    xs = (-0.15, -0.05, 0.05, 0.15)
    for i, x0 in enumerate(xs):
        pts = []
        n = len(L.HEADER_PATH)
        for k, (u, v) in enumerate(L.HEADER_PATH):
            t = k / (n - 1)
            x = x0 * (1 - t) + (-0.08 + x0 * 0.18) * t
            p = Vector(P3(u, v, x))
            if abs(x) < L.W_TYRE_F / 2 + 0.04:            # keep inner pipes off the front tyre
                d = Vector((0, p.y - fa.y, p.z - fa.z))
                if d.length < clear:
                    p = Vector((x, fa.y, fa.z)) + d.normalized() * clear
            pts.append(p)
        out.append(mesh.tube(nm(lod, f"EXHAUST_Header_{i + 1:02d}"), C, pts, 0.019, seg, "MAT_EXHAUST",
                          samples=smp))
        # head flange
        out.append(mesh.cyl(nm(lod, f"EXHAUST_Flange_{i + 1:02d}"), C, pts[0] + (pts[0] - pts[1]).normalized() * 0.01,
                         pts[0] - (pts[0] - pts[1]).normalized() * 0.012, 0.027, seg, "MAT_METAL_DARK"))
    mid = [P3(u, v, x) for (u, v), x in zip(L.MIDPIPE_PATH, (-0.08, -0.12, -0.16, -0.17))]
    out.append(mesh.tube(nm(lod, "EXHAUST_Collector"), C, mid, [0.034, 0.028, 0.025, 0.025], seg,
                      "MAT_EXHAUST", samples=smp))
    mf, mr = Vector(P3(*L.MUFFLER_FRONT_PX, -0.17)), Vector(P3(*L.MUFFLER_REAR_PX, -0.17))
    d = (mr - mf).normalized()
    out.append(mesh.cyl(nm(lod, "EXHAUST_Muffler_Inlet"), C, mf - d * 0.02, mf + d * 0.035, 0.026,
                     seg, "MAT_EXHAUST", r1=L.MUFFLER_R))
    body = mesh.cyl(nm(lod, "EXHAUST_Muffler"), C, mf + d * 0.035, mr - d * 0.03, L.MUFFLER_R, seg,
                 "MAT_BODY_BLACK")
    out.append(body)
    out.append(mesh.cyl(nm(lod, "EXHAUST_Muffler_EndCap"), C, mr - d * 0.03, mr, L.MUFFLER_R + 0.002,
                     seg, "MAT_METAL_RAW", r1=L.MUFFLER_R * 0.8))
    if lod["name"] == "HIGH":
        for k, t in enumerate((0.3, 0.75)):
            p = mf + (mr - mf) * t
            out.append(mesh.cyl(f"EXHAUST_Clamp_{k}", lod["C_DETAIL"], p - d * 0.008, p + d * 0.008,
                             L.MUFFLER_R + 0.003, seg, "MAT_METAL_RAW"))
    return out


def build_all(lod):
    groups = {}
    groups["wheels"] = wheels(lod) + brakes(lod)
    groups["frame"] = frame(lod)
    groups["tank"] = tank(lod)
    groups["seat"] = seat(lod)
    groups["engine"] = engine(lod)
    groups["front"] = front(lod)
    groups["rear"] = rear(lod)
    groups["exhaust"] = exhaust(lod)
    return groups
