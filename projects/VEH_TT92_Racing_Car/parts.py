"""
Part builders for VEH_TT92_Racing_Car. Every builder takes a LOD profile (LOW = Stage 1,
HIGH = Stage 2) and reads ALL placement from landmarks.py (plan from the top photo, heights from
the Z tables). Library map: docs/04_MODELING_TOOLKIT.md.

Naming: <GROUP>_<Part>[_L|_R]; LOW objects get _LOW via nm(); guessed parts UNCERTAIN_ prefix.
Axes: +X = car LEFT, -Y = front, +Z up; origin midway between the axles on the ground.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

import landmarks as L
from workbench.bl import mesh, mods

LOW = dict(name="LOW", ring=16, body_step=40, lathe=20, tube=8, spokes=0, bevel=False,
           C_PRIMARY="02_LOW_PRIMARY", C_SECONDARY="03_LOW_SECONDARY", C_MECH="04_LOW_MECHANICAL",
           C_DETAIL="04_LOW_MECHANICAL")
HIGH = dict(name="HIGH", ring=40, body_step=16, lathe=56, tube=14, spokes=24, bevel=True,
            C_PRIMARY="05_HIGH_BODY", C_SECONDARY="05_HIGH_BODY", C_MECH="06_HIGH_MECHANICAL",
            C_DETAIL="07_DETAILS")

PALETTE = {                          # 8 materials (docs/02_STANDARDS.md)
    "MAT_BODY_RED":   ((0.34, 0.012, 0.010), 0.3, 0.36),
    "MAT_CARBON":     ((0.035, 0.035, 0.04), 0.3, 0.30),
    "MAT_RUBBER":     ((0.018, 0.018, 0.018), 0.0, 0.85),
    "MAT_METAL_DARK": ((0.05, 0.05, 0.055), 0.8, 0.45),
    "MAT_CHROME":     ((0.80, 0.80, 0.80), 1.0, 0.12),
    "MAT_EXHAUST":    ((0.42, 0.36, 0.30), 1.0, 0.40),
    "MAT_LEATHER":    ((0.22, 0.11, 0.05), 0.0, 0.55),
    "MAT_WRAP":       ((0.40, 0.33, 0.22), 0.0, 0.85),
}

# name-prefix pairs that must never intersect (validate.intersections)
CRITICAL_PAIRS = [
    ("WHEEL_", "BODY_Shell"), ("WHEEL_", "EXHAUST_"), ("EXHAUST_Pipe", "BODY_Shell"),
    ("WHEEL_", "AERO_"), ("WHEEL_", "UNCERTAIN_AERO_"), ("SUSP_Rear_Rod", "EXHAUST_"),
    ("COCKPIT_SteeringWheel", "COCKPIT_Seat"), ("WHEEL_Front", "SUSP_Rear"),
    ("WHEEL_Rear", "SUSP_Front"), ("EXHAUST_", "AERO_"), ("WHEEL_Front_Tire", "BRAKE_"),
    ("WHEEL_Rear_Tire", "BRAKE_"),
]

WHEELS = {  # tag: (x centre, axle v, radius, width)
    "Front_L": (L.TRACK_HALF_F, L.FRONT_AXLE_V, L.R_TYRE_F, L.W_TYRE_F),
    "Front_R": (-L.TRACK_HALF_F, L.FRONT_AXLE_V, L.R_TYRE_F, L.W_TYRE_F),
    "Rear_L": (L.TRACK_HALF_R, L.REAR_AXLE_V, L.R_TYRE_R, L.W_TYRE_R),
    "Rear_R": (-L.TRACK_HALF_R, L.REAR_AXLE_V, L.R_TYRE_R, L.W_TYRE_R),
}


def nm(lod, name):
    return name if lod["name"] == "HIGH" else name + "_LOW"


def hard(ob, lod, bevel=0.003):
    """hard-surface finish: bevel + weighted normals at HIGH, nothing at LOW. Never subsurf plates."""
    return mods.finish_hard(ob, bevel, enabled=lod["bevel"])


def xform(ob, mat):
    """bake a transform into the mesh (keeps object scale/rotation identity)."""
    ob.data.transform(mat)
    ob.data.update()
    return ob


# ============================================================================ BODY SECTIONS
def section_params(v):
    return (L.body_hw(v), L.interp(L.BODY_ZTOP, v), L.interp(L.BODY_ZBOT, v),
            L.interp(L.BODY_ETOP, v), L.interp(L.BODY_EBOT, v), L.interp(L.BODY_WIDEST, v))


def section(v, n):
    """closed superellipse ring [(x, z)] at station v, starting bottom centre, CCW seen from front."""
    hw, zt, zb, et, eb, wd = section_params(v)
    zm = zb + (zt - zb) * wd
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n - math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        x = hw * math.copysign(abs(ca) ** (2.0 / (et if sa >= 0 else eb)), ca)
        if sa >= 0:
            z = zm + (zt - zm) * abs(sa) ** (2.0 / et)
        else:
            z = zm - (zm - zb) * abs(sa) ** (2.0 / eb)
        pts.append((x, z))
    return pts


def top_z(v, x):
    """analytic body top surface height at plan point (v px, x m)."""
    hw, zt, zb, et, eb, wd = section_params(v)
    zm = zb + (zt - zb) * wd
    t = min(abs(x) / hw, 1.0) if hw > 1e-6 else 1.0
    return zm + (zt - zm) * max(0.0, 1.0 - t ** et) ** (1.0 / et)


def flank_x(v, z):
    """analytic body half width at height z (upper half uses e_top, lower e_bot)."""
    hw, zt, zb, et, eb, wd = section_params(v)
    zm = zb + (zt - zb) * wd
    if z >= zm:
        t, e = (z - zm) / (zt - zm), et
    else:
        t, e = (zm - z) / (zm - zb), eb
    return hw * max(0.0, 1.0 - min(t, 1.0) ** e) ** (1.0 / e)


def body_stations(step):
    keys = {v for v, _ in L.BODY_HW_PX} | {v for v, _ in L.BODY_ZTOP} | {v for v, _ in L.OPEN_HW_PX}
    vs = set(keys)
    v = L.BODY_NOSE_V
    while v < L.BODY_TAIL_V:
        vs.add(round(v, 2))
        v += step
    vs = sorted(x for x in vs if L.BODY_NOSE_V <= x <= L.BODY_TAIL_V)
    # thin out keys closer than 4 px (keeps rings well spaced)
    out = [vs[0]]
    for x in vs[1:]:
        if x - out[-1] >= 4.0 or x == vs[-1]:
            out.append(x)
    return out


def cockpit_outline(n_side=24):
    """closed plan polygon of the cockpit opening [(x, y)] (CCW from above)."""
    v0, v1 = L.COCKPIT_V
    vs = [v0 + (v1 - v0) * (0.5 - 0.5 * math.cos(math.pi * i / n_side)) for i in range(n_side + 1)]
    right = [(-L.open_hw(v), L.Y(v)) for v in vs]
    left = [(L.open_hw(v), L.Y(v)) for v in reversed(vs)]
    pts = right + left[1:-1]
    out = []
    for p in pts:
        if not out or (Vector(p) - Vector(out[-1])).length > 1e-4:
            out.append(p)
    return out


def body(lod):
    """BODY_Shell: side/plan-driven loft, cockpit carved with a boolean prism (interior dark)."""
    n = lod["ring"]
    rings = []
    for v in body_stations(lod["body_step"]):
        y = L.Y(v)
        rings.append([(x, y, z) for (x, z) in section(v, n)])
    ob = mesh.loft_rings(nm(lod, "BODY_Shell"), lod["C_PRIMARY"], rings, "MAT_BODY_RED",
                         sharp_angle=80)
    if lod["name"] == "HIGH":
        mods.subsurf(ob, 1, 1)                 # organic loft: subsurf baked BEFORE the boolean
        mods.apply_all(ob)
    # cockpit cutter: vertical prism from the opening outline
    poly = cockpit_outline(32 if lod["name"] == "HIGH" else 12)
    zc = L.COCKPIT_FLOOR_Z
    cut = mesh.extrude_polys("TEMP_CockpitCutter", "08_TEMP",
                             [([(x, y, zc) for x, y in poly], [(x, y, 1.5) for x, y in poly])])
    mods.boolean(ob, cut, apply=True)
    bpy.data.objects.remove(cut, do_unlink=True)
    # interior faces (cut walls + floor) -> dark material; the boolean can leave an empty slot
    ob.data.materials.clear()
    ob.data.materials.append(bpy.data.materials["MAT_BODY_RED"])
    ob.data.materials.append(bpy.data.materials["MAT_METAL_DARK"])
    for p in ob.data.polygons:
        p.material_index = 0
    v0, v1 = L.COCKPIT_V
    for p in ob.data.polygons:
        c = p.center
        v = L.V_MID + c.y * L.S
        if v0 - 1 <= v <= v1 + 1 and abs(c.x) <= L.open_hw(min(max(v, v0), v1)) + 0.004 \
                and c.z < L.interp(L.BODY_ZTOP, v) - 0.004:
            p.material_index = 1
    for p in ob.data.polygons:
        p.use_smooth = True
    if lod["name"] == "HIGH":
        mods.weighted_normal(ob)
    return [ob]


def body_bvh():
    ob = bpy.data.objects.get("BODY_Shell") or bpy.data.objects.get("BODY_Shell_LOW")
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    verts = [ob.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    eo.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def surface_z(bvh, x, y, default):
    hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 5.0)
    return hit[0].z if hit[0] is not None else default


# ============================================================================ NOSE
def nose(lod):
    """NOSE_Grille: dark ribbed carbon dome closing the blunt nose face (oblique photo)."""
    v = L.BODY_NOSE_V
    hw, zt, zb, et, eb, wd = section_params(v)
    zm = zb + (zt - zb) * wd
    y0 = L.Y(v)
    n = lod["ring"]
    k = 17 if lod["name"] == "HIGH" else 4
    rings = []
    for i in range(k):
        t = i / (k - 1)
        s = max(0.05, math.cos(t * math.pi / 2) ** 0.7) * 0.97
        if lod["name"] == "HIGH" and 0 < i < k - 1 and i % 2 == 1:
            s *= 0.95                                    # concentric ribs (oblique photo)
        dy = -0.05 * math.sin(t * math.pi / 2) + 0.006
        rings.append([(x * s, y0 + dy, zm + (z - zm) * s) for (x, z) in section(v, n)])
    ob =mesh.loft_rings(nm(lod, "NOSE_Grille"), lod["C_SECONDARY"], rings, "MAT_CARBON",
                         sharp_angle=70)
    return [ob]


# ============================================================================ WHEELS
def tyre_profile(R, W, rim_r, lod):
    s = R - rim_r
    if lod["name"] == "LOW":
        half = [(rim_r, 0.44 * W), (rim_r + 0.45 * s, 0.50 * W), (R - 0.12 * s, 0.49 * W), (R, 0.40 * W),
                (R, 0.0)]
    else:
        half = [(rim_r, 0.44 * W), (rim_r + 0.15 * s, 0.475 * W), (rim_r + 0.4 * s, 0.50 * W),
                (rim_r + 0.7 * s, 0.50 * W), (R - 0.14 * s, 0.49 * W), (R - 0.06 * s, 0.47 * W),
                (R - 0.015 * s, 0.44 * W), (R, 0.40 * W), (R, 0.2 * W), (R, 0.0)]
    return [(r, -w) for (r, w) in half] + [(r, w) for (r, w) in reversed(half[:-1])]


def wheel(lod, tag):
    x, v, R, W = WHEELS[tag]
    c = Vector((x, L.Y(v), R))
    rim_r = R * L.RIM_RATIO
    out_s = 1.0 if x > 0 else -1.0                      # outboard direction
    CP, CM = lod["C_PRIMARY"], lod["C_MECH"]
    base = f"WHEEL_{tag.split('_')[0]}"
    side = tag.split("_")[1]
    res = [mesh.lathe(nm(lod, f"{base}_Tire_{side}"), CP, c, tyre_profile(R, W, rim_r, lod),
                      lod["lathe"] + (16 if lod["name"] == "HIGH" else 0), "MAT_RUBBER",
                      sharp_angle=60)]
    hw = W * 0.42
    rim_prof = [(rim_r + 0.014, -hw), (rim_r + 0.014, -hw + 0.01), (rim_r - 0.004, -hw + 0.014),
                (rim_r - 0.006, hw - 0.014), (rim_r + 0.014, hw - 0.01), (rim_r + 0.014, hw),
                (rim_r - 0.022, hw - 0.004), (rim_r - 0.026, 0.0), (rim_r - 0.022, -hw + 0.004)]
    res.append(mesh.lathe(nm(lod, f"{base}_Rim_{side}"), CP, c, rim_prof, lod["lathe"],
                          "MAT_METAL_DARK", sharp_angle=50))
    # hub: barrel + knock-off spinner (outboard)
    hub_prof = [(0.018, -0.07 * out_s), (0.055, -0.07 * out_s), (0.06, 0.0), (0.05, 0.05 * out_s),
                (0.035, 0.085 * out_s), (0.018, 0.09 * out_s)]
    if out_s < 0:
        hub_prof = list(reversed(hub_prof))
    res.append(mesh.lathe(nm(lod, f"{base}_Hub_{side}"), CM, c, hub_prof, max(12, lod["lathe"] // 3),
                          "MAT_CHROME", closed=False))
    if lod["spokes"]:
        # laced wire spokes: two layers (outboard / inboard flange) crossing to the rim centre
        specs = []
        ns = lod["spokes"]
        for layer, (dx, ph) in enumerate(((0.05 * out_s, 0.0), (-0.045 * out_s, math.pi / ns))):
            for i in range(ns):
                a = 2 * math.pi * i / ns + ph
                tw = 0.45 * (1 if (i + layer) % 2 else -1)
                p0 = c + Vector((dx, 0.055 * math.cos(a), 0.055 * math.sin(a)))
                p1 = c + Vector((0.0, (rim_r - 0.02) * math.cos(a + tw), (rim_r - 0.02) * math.sin(a + tw)))
                specs.append((p0, p1, 0.0026))
        res.append(mesh.multi_cyl(f"{base}_Spokes_{side}", lod["C_DETAIL"], specs, 5, "MAT_METAL_DARK"))
        # two-eared knock-off
        e0 = c + Vector((0.088 * out_s, 0, 0))
        res.append(hard(mesh.box(f"{base}_Spinner_{side}", lod["C_DETAIL"], e0, (0.018, 0.13, 0.022),
                                 "MAT_CHROME"), lod, 0.004))
    else:
        disc = [(0.05, -0.01), (rim_r - 0.02, -0.01), (rim_r - 0.02, 0.01), (0.05, 0.01)]
        res.append(mesh.lathe(nm(lod, f"{base}_Disc_{side}"), CM, c, disc, lod["lathe"], "MAT_METAL_DARK"))
    # brake drum inside the wheel (finned, dark)
    dr = rim_r * 0.72
    drum = [(0.05, -0.05), (dr, -0.05), (dr, 0.03), (0.05, 0.03)]
    drum = [(r, -w * out_s) for r, w in drum]
    res.append(mesh.lathe(nm(lod, f"BRAKE_Drum_{tag}"), CM, c + Vector((-0.02 * out_s, 0, 0)), drum,
                          lod["lathe"], "MAT_METAL_DARK", sharp_angle=40))
    return res


def wheels(lod):
    out = []
    for tag in WHEELS:
        out += wheel(lod, tag)
    return out


# ============================================================================ AERO
def fins(lod):
    """AERO_SideFin_L/R: flat 'shark' fins behind the front wheels (plan outline from the photo)."""
    out = []
    t = 0.018
    poly = [(u, v) for (u, v) in L.FIN_L_PX]
    poly_root = poly[:-1] + [(262, 470), (262, 380)]      # root buried 12 px into the flank
    for side, sg in (("L", 1.0), ("R", -1.0)):
        pts = [(sg * L.X(u), L.Y(v)) for (u, v) in poly_root]
        if sg < 0:
            pts = list(reversed(pts))
        z0 = L.FIN_Z - t / 2
        # slight dihedral: tip 2 cm higher than the root
        def zz(x, z):
            return z + 0.02 * max(0.0, (abs(x) - 0.3) / 0.33)
        a = [(x, y, zz(x, z0)) for x, y in pts]
        b = [(x, y, zz(x, z0 + t)) for x, y in pts]
        ob = mesh.extrude_polys(nm(lod, f"AERO_SideFin_{side}"), lod["C_SECONDARY"], [(a, b)], "MAT_BODY_RED")
        out.append(hard(ob, lod, 0.005))
    return out


def canards(lod):
    """UNCERTAIN_AERO_*: dark carbon tabs and canard plates beside the nose (shape guessed)."""
    out = []
    for side, sg in (("L", 1.0), ("R", -1.0)):
        u = L.NOSE_TABS_U[0] if sg > 0 else L.NOSE_TABS_U[1]
        x = L.X(u)
        # vertical tab on the nose flank
        y0, y1 = L.Y(125), L.Y(190)
        zb = top_z(150, x) - 0.06
        tab = [(x, y0, zb + 0.10), (x, y1, zb + 0.08), (x, y1, zb), (x, y0 + 0.03, zb - 0.02)]
        a = [(p[0] - 0.004, p[1], p[2]) for p in tab]
        b = [(p[0] + 0.004, p[1], p[2]) for p in tab]
        out.append(hard(mesh.extrude_polys(nm(lod, f"UNCERTAIN_AERO_NoseTab_{side}"), lod["C_SECONDARY"],
                                           [(a, b)], "MAT_CARBON"), lod, 0.002))
        # canard plate from the nose flank out towards the front wheel, sloped 40 deg outboard-down
        pts = [(sg * L.X(u2), L.Y(v2)) for (u2, v2) in L.CANARD_L_PX]
        if sg < 0:
            pts = list(reversed(pts))
        xi = abs(L.X(L.CANARD_L_PX[0][0]))
        z_in = 0.45

        def zc(px):
            return z_in - (abs(px) - xi) * math.tan(math.radians(40))
        a = [(px, py, zc(px)) for px, py in pts]
        b = [(px, py, zc(px) + 0.008) for px, py in pts]
        out.append(hard(mesh.extrude_polys(nm(lod, f"UNCERTAIN_AERO_Canard_{side}"), lod["C_SECONDARY"],
                                           [(a, b)], "MAT_CARBON"), lod, 0.002))
    return out


def tail_blade(lod):
    """AERO_TailBlade: thin blade on the tail ridge, running past the tip to v 1195."""
    v0, v1, vt = 1080.0, 1195.0, L.BODY_TAIL_V
    pts = []
    for v in (v0, 1110, 1140, vt, v1):
        zt = L.interp(L.BODY_ZTOP, min(v, vt))
        pts.append((L.Y(v), zt - 0.03 if v < vt else zt - 0.06))
    top = [(L.Y(v0), L.interp(L.BODY_ZTOP, v0) + 0.012), (L.Y(1140), L.interp(L.BODY_ZTOP, 1140) + 0.02),
           (L.Y(v1), L.interp(L.BODY_ZTOP, vt) + 0.01)]
    poly = [(y, z) for y, z in pts] + list(reversed(top))
    a = [(-0.003, y, z) for y, z in poly]
    b = [(0.003, y, z) for y, z in poly]
    return [hard(mesh.extrude_polys(nm(lod, "AERO_TailBlade"), lod["C_SECONDARY"], [(a, b)],
                                    "MAT_BODY_RED"), lod, 0.0015)]


# ============================================================================ EXHAUST
def exhaust_path():
    pts = []
    for i, (u, v) in enumerate(L.EXHAUST_PX):
        t = i / (len(L.EXHAUST_PX) - 1)
        pts.append(Vector((L.X(u), L.Y(v), L.EXHAUST_Z[0] + (L.EXHAUST_Z[1] - L.EXHAUST_Z[0]) * t)))
    return pts


def exhaust(lod):
    out = []
    path = exhaust_path()
    tip = path[-1] + Vector((-0.012, L.m(L.EXHAUST_TIP_V - L.EXHAUST_PX[-1][1]), 0.0))
    out.append(mesh.tube(nm(lod, "EXHAUST_Pipe"), lod["C_MECH"], path + [tip], L.EXHAUST_R,
                         lod["tube"], "MAT_EXHAUST", samples=6))
    # headers: leave the right flank high (seen above the fin root), run back above the fin and drop
    # into the collector (first pipe point) behind the fin trailing edge
    col = path[0]
    zh = 0.56
    for i, v in enumerate(L.HEADER_V):
        x0 = -(flank_x(v, zh) - 0.02)
        k = i - 1.5
        p0 = Vector((x0, L.Y(v), zh))
        p1 = Vector((x0 - 0.05, L.Y(v) + 0.025, zh - 0.01))
        p2 = Vector((col.x - 0.02 + 0.012 * k, L.Y(495) + 0.012 * k, 0.50 + 0.012 * k))
        p3 = col + Vector((0.003 * k, -0.015, 0.003 * k))
        pts = [p0, p1, p2, p3] if p1.y < p2.y - 0.04 else [p0, p2, p3]
        out.append(mesh.tube(nm(lod, f"EXHAUST_Header_{i + 1}"), lod["C_MECH"], pts, 0.017,
                             lod["tube"], "MAT_EXHAUST", samples=6))
    # heat wrap over the middle section
    wv0, wv1 = L.EXHAUST_WRAP_V
    wp = [p for p in path if L.Y(wv0) <= p.y <= L.Y(wv1)]
    wp = [path_at(path, L.Y(wv0))] + wp + [path_at(path, L.Y(wv1))]
    if lod["name"] == "HIGH":
        pts = []
        for a, b in zip(wp, wp[1:]):
            turns = (b - a).length / 0.012
            seg = mesh.helix(a, b, L.EXHAUST_R + 0.004, turns, 10)
            pts += seg if not pts else seg[1:]
        out.append(mesh.tube("EXHAUST_Wrap", lod["C_DETAIL"], pts, 0.0045, 6, "MAT_WRAP",
                             smooth_path=False))
        out.append(mesh.tube("EXHAUST_WrapCore", lod["C_DETAIL"], wp, L.EXHAUST_R + 0.002, lod["tube"],
                             "MAT_WRAP", smooth_path=False))
    else:
        out.append(mesh.tube(nm(lod, "EXHAUST_Wrap"), lod["C_MECH"], wp, L.EXHAUST_WRAP_R, lod["tube"],
                             "MAT_WRAP", smooth_path=False))
    return out


def path_at(path, y):
    for a, b in zip(path, path[1:]):
        if a.y <= y <= b.y:
            t = (y - a.y) / (b.y - a.y)
            return a.lerp(b, t)
    return path[-1]


# ============================================================================ SUSPENSION
def front_suspension(lod):
    """double wishbones + upright (left seen in the photo; right mirrored, hidden -> UNCERTAIN)."""
    out = []
    r = 0.012
    for side, sg in (("L", 1.0), ("R", -1.0)):
        pre = "SUSP_Front" if sg > 0 else "UNCERTAIN_SUSP_Front"
        xw, v, R, W = WHEELS["Front_" + side]
        yc = L.Y(v)
        xu = sg * (abs(xw) - W / 2 - 0.035)                  # upright plane, inboard of the tyre
        top, bot = Vector((xu, yc, R + 0.12)), Vector((xu, yc, R - 0.13))
        out.append(mesh.cyl(nm(lod, f"{pre}_Upright_{side}"), lod["C_MECH"], bot, top, 0.022,
                            lod["tube"], "MAT_CHROME"))
        out.append(mesh.cyl(nm(lod, f"{pre}_Spindle_{side}"), lod["C_MECH"], Vector((xu, yc, R)),
                            Vector((xw - sg * 0.02, yc, R)), 0.02, lod["tube"], "MAT_CHROME"))
        for arm, apex, zin in (("Upper", top, R + 0.13), ("Lower", bot, R - 0.12)):
            xin = sg * (flank_x(L.FRONT_AXLE_V, zin) - 0.01)
            pf = Vector((xin, L.Y(205), zin))
            pr = Vector((xin, L.Y(295), zin))
            out.append(mesh.tube(nm(lod, f"{pre}_Wishbone{arm}_{side}"), lod["C_MECH"], [pf, apex, pr],
                                 r, lod["tube"], "MAT_CHROME", smooth_path=False))
        # damper (small coil-over, inboard, leaning)
        d0 = Vector((xu - sg * 0.04, yc + 0.03, R - 0.10))
        d1 = Vector((sg * (flank_x(L.FRONT_AXLE_V, R + 0.22) - 0.02), yc + 0.05, R + 0.22))
        out.append(mesh.cyl(nm(lod, f"{pre}_Damper_{side}"), lod["C_MECH"], d0, d1, 0.016, lod["tube"],
                            "MAT_METAL_DARK"))
    return out


def rear_suspension(lod):
    """transverse coil-overs + chrome links to the hub carriers, diagonal radius rods (photo)."""
    out = []
    y = L.Y(L.REAR_XTUBE_V)
    for side, sg in (("L", 1.0), ("R", -1.0)):
        xw, v, R, W = WHEELS["Rear_" + side]
        yc = L.Y(v)
        xh = sg * (abs(xw) - W / 2 - 0.03)
        # hub carrier
        out.append(hard(mesh.box(nm(lod, f"SUSP_Rear_HubCarrier_{side}"), lod["C_MECH"], (xh, yc, R),
                                 (0.05, 0.12, 0.22), "MAT_METAL_DARK"), lod, 0.006))
        out.append(mesh.cyl(nm(lod, f"SUSP_Rear_Axle_{side}"), lod["C_MECH"], Vector((sg * 0.12, yc, R)),
                            Vector((xw - sg * 0.02, yc, R)), 0.022, lod["tube"], "MAT_CHROME"))
        # transverse link + coil-over at z 0.42 (springs u 255..300 / 385..425)
        z = 0.44
        us = L.REAR_SPRINGS_U[0] if sg > 0 else L.REAR_SPRINGS_U[1]
        xa, xb = sorted((L.X(us[0]), L.X(us[1])), key=abs)
        out.append(mesh.cyl(nm(lod, f"SUSP_Rear_Link_{side}"), lod["C_MECH"], Vector((xb, y, z)),
                            Vector((xh, y, z - 0.02)), 0.011, lod["tube"], "MAT_CHROME"))
        out.append(mesh.cyl(nm(lod, f"SUSP_Rear_DamperBody_{side}"), lod["C_MECH"],
                            Vector((xa - sg * 0.04, y, z)), Vector((xb, y, z)), 0.014, lod["tube"],
                            "MAT_CHROME"))
        if lod["name"] == "HIGH":
            pts = mesh.helix(Vector((xa, y, z)), Vector((xb, y, z)), 0.028, 7, 14)
            out.append(mesh.tube(f"SUSP_Rear_Spring_{side}", lod["C_DETAIL"], pts, 0.0055, 8,
                                 "MAT_BODY_RED", smooth_path=False))
        else:
            out.append(mesh.cyl(nm(lod, f"SUSP_Rear_Spring_{side}"), lod["C_MECH"], Vector((xa, y, z)),
                                Vector((xb, y, z)), 0.03, lod["tube"], "MAT_BODY_RED"))
        # diagonal radius rod: hub carrier -> tail underside
        (u0, v0), (u1, v1) = L.REAR_RODS_PX[0 if sg > 0 else 1]
        p0 = Vector((xh - sg * 0.02, L.Y(v0), R - 0.09))      # passes UNDER the exhaust pipe
        p1 = Vector((L.X(u1), L.Y(v1), 0.20))
        out.append(mesh.cyl(nm(lod, f"SUSP_Rear_Rod_{side}"), lod["C_MECH"], p0, p1, 0.011, lod["tube"],
                            "MAT_CHROME"))
    return out


# ============================================================================ COCKPIT
def cockpit(lod):
    out = []
    bvh = body_bvh()
    # steering wheel: torus in a plane leaning 20 deg back from vertical, facing the driver (+Y)
    su, sv = L.STEER_WHEEL_PX
    c = Vector((L.X(su), L.Y(sv), L.STEER_WHEEL_Z))
    R, r = L.STEER_WHEEL_R, 0.011
    k = 10 if lod["name"] == "HIGH" else 6
    prof = [(R + r * math.cos(2 * math.pi * i / k), r * math.sin(2 * math.pi * i / k)) for i in range(k)]
    sw = mesh.lathe(nm(lod, "COCKPIT_SteeringWheel"), lod["C_SECONDARY"], (0, 0, 0), prof,
                    lod["lathe"] + 8, "MAT_LEATHER", axis="Y")
    rot = Matrix.Rotation(math.radians(-20), 4, "X")
    xform(sw, Matrix.Translation(c) @ rot)
    out.append(sw)
    axis = (rot.to_3x3() @ Vector((0, 1, 0))).normalized()
    # spokes (3) + boss
    specs = []
    for a in (90, 210, 330):
        d = rot.to_3x3() @ Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
        specs.append((c + d * 0.02, c + d * (R - 0.005), 0.006))
    out.append(mesh.multi_cyl(nm(lod, "COCKPIT_SteeringSpokes"), lod["C_SECONDARY"], specs, 6, "MAT_CHROME"))
    # column to the dash (forward-down)
    col_end = c - axis * 0.45 + Vector((0, 0, -0.05))
    out.append(mesh.cyl(nm(lod, "COCKPIT_SteeringColumn"), lod["C_SECONDARY"], c - axis * 0.01, col_end,
                        0.014, lod["tube"], "MAT_METAL_DARK"))
    # seat: cushion + curved back (leather)
    v0, v1 = L.SEAT_V
    hw = L.m(70)
    fl = L.COCKPIT_FLOOR_Z
    cv0 = v0 + 35                                         # cushion starts behind the pedal well
    cush = mesh.box(nm(lod, "COCKPIT_Seat_Cushion"), lod["C_SECONDARY"],
                    (0, (L.Y(cv0) + L.Y(v1 - 25)) / 2, fl + 0.05),
                    (1.6 * L.m(55), L.Y(v1 - 25) - L.Y(cv0), 0.10),
                    "MAT_LEATHER")
    out.append(hard(cush, lod, 0.02))
    back_pts = []
    n = 9
    for i in range(n):
        a = math.pi * (0.15 + 0.7 * i / (n - 1))
        back_pts.append((hw * 1.05 * math.cos(a), L.Y(v1 - 12) - 0.06 + 0.05 * math.sin(a)))
    zb0, zb1 = fl + 0.08, 0.60
    a_ = [(x, y, zb0) for x, y in back_pts]
    b_ = [(x, y + 0.04, zb1) for x, y in back_pts]
    # curved shell 5 cm thick: two closed rings (bottom, top) lofted
    back =mesh.loft_rings(nm(lod, "COCKPIT_Seat_Back"), lod["C_SECONDARY"],
                           [[(x, y, z) for (x, y, z) in a_] + [(x, y + 0.05, z) for (x, y, z) in reversed(a_)],
                            [(x, y, z) for (x, y, z) in b_] + [(x, y + 0.05, z) for (x, y, z) in reversed(b_)]],
                           "MAT_LEATHER", sharp_angle=60)
    out.append(hard(back, lod, 0.01))
    # dash panel ahead of the wheel (under the cowl)
    vd = L.COCKPIT_V[0] + 4
    zd = surface_z(bvh, 0.0, L.Y(vd - 6), 0.75) - 0.03
    dash = mesh.box(nm(lod, "COCKPIT_Dash"), lod["C_SECONDARY"], (0, L.Y(vd) + 0.012, zd - 0.09),
                    (2 * L.m(80), 0.02, 0.16), "MAT_METAL_DARK")
    out.append(hard(dash, lod, 0.004))
    # padded roll around the front half of the opening + red lip along the whole rim
    poly = cockpit_outline(32 if lod["name"] == "HIGH" else 12)
    rim = []
    for x, y in poly:
        z = surface_z(bvh, x * 1.02 + math.copysign(0.004, x), y, 0.72)
        rim.append(Vector((x, y, z)))
    rim.append(rim[0])
    out.append(mesh.tube(nm(lod, "COCKPIT_RimLip"), lod["C_SECONDARY"], rim, 0.011, lod["tube"] - 2,
                         "MAT_BODY_RED", smooth_path=False, caps=False))
    v0p, v1p = L.COWL_PAD_V
    pad = [p for p in rim if L.Y(v0p) - 0.01 <= p.y <= L.Y(L.COCKPIT_V[0] + 40)]
    pad.sort(key=lambda p: p.x)
    if len(pad) >= 3:
        pts = [p + Vector((0, -0.01, 0.012)) for p in pad]
        out.append(mesh.tube(nm(lod, "COCKPIT_CowlPad"), lod["C_SECONDARY"], pts, 0.028, lod["tube"],
                             "MAT_LEATHER", samples=3))
    return out


# ============================================================================ SMALL BODY PARTS
def body_details(lod):
    out = []
    bvh = body_bvh()
    # fuel/oil filler caps on the rear deck
    for i, ((u, v), rp) in enumerate(L.REAR_CAPS_PX):
        x, y = L.X(u), L.Y(v)
        z = surface_z(bvh, x, y, 0.65)
        r = L.m(rp)
        out.append(mesh.lathe(nm(lod, f"BODY_FillerCap_{i + 1}"), lod["C_SECONDARY"], (x, y, z - 0.01),
                              [(0.0, 0.0), (r, 0.0), (r, 0.02), (r * 0.85, 0.03), (0.0, 0.032)],
                              max(12, lod["lathe"] // 2), "MAT_CHROME", closed=False, axis="Z"))
    # air filter on the left bonnet flank (red cylinder, axis along Y)
    (u0, v0), (u1, v1) = L.AIR_FILTER_PX
    x = L.X(u0)
    r = L.m(9)
    z = surface_z(bvh, x, L.Y((v0 + v1) / 2), 0.6) + r * 0.4
    out.append(mesh.cyl(nm(lod, "ENGINE_AirFilter_L"), lod["C_SECONDARY"], (x, L.Y(v0), z), (x, L.Y(v1), z),
                        r, lod["tube"], "MAT_BODY_RED"))
    # louvred panel on the left flank (u 235..265)
    vs0, vs1 = L.SIDE_LOUVRE_V
    zc = 0.60
    xs = flank_x((vs0 + vs1) / 2, zc)
    out.append(hard(mesh.box(nm(lod, "BODY_SideLouvrePanel_L"), lod["C_SECONDARY"],
                             (xs - 0.01, (L.Y(vs0) + L.Y(vs1)) / 2, zc), (0.05, L.Y(vs1) - L.Y(vs0), 0.09),
                             "MAT_BODY_RED"), lod, 0.008))
    if lod["name"] == "HIGH":
        polys = []
        # bonnet louvres: raised lips following the surface
        for (ua, ub) in L.LOUVRE_ROWS_U:
            for i in range(L.LOUVRE_N):
                v = L.LOUVRE_V[0] + (L.LOUVRE_V[1] - L.LOUVRE_V[0]) * i / (L.LOUVRE_N - 1)
                pts = []
                for u in (ua, ub):
                    x = L.X(u)
                    pts.append((x, L.Y(v), surface_z(bvh, x, L.Y(v), 0.68)))
                (xa, ya, za), (xb, yb, zb) = pts
                d = 0.006
                fa = [(xa, ya - d, za - 0.004), (xb, yb - d, zb - 0.004), (xb, yb + d, zb + 0.007),
                      (xa, ya + d, za + 0.007)]
                fb = [(p[0], p[1], p[2] - 0.012) for p in fa]
                polys.append((fa, fb))
        # side panel slats
        for i in range(12):
            v = vs0 + 8 + (vs1 - vs0 - 16) * i / 11
            y = L.Y(v)
            x0 = xs + 0.015
            fa = [(x0, y - 0.005, zc - 0.035), (x0, y - 0.005, zc + 0.035), (x0 + 0.008, y + 0.004, zc + 0.035),
                  (x0 + 0.008, y + 0.004, zc - 0.035)]
            fb = [(p[0] - 0.012, p[1], p[2]) for p in fa]
            polys.append((fa, fb))
        out.append(mesh.extrude_polys("BODY_Louvres", lod["C_DETAIL"], polys, "MAT_BODY_RED"))
    return out


def build_global(lod):
    """phase 1: global proportions only (wheels + body shell)."""
    return {"wheels": wheels(lod), "body": body(lod)}


def build_all(lod):
    parts = build_global(lod)
    parts.update(nose=nose(lod), fins=fins(lod), canards=canards(lod), tail=tail_blade(lod),
                 exhaust=exhaust(lod), fsusp=front_suspension(lod), rsusp=rear_suspension(lod),
                 cockpit=cockpit(lod), details=body_details(lod))
    return parts


def guide_points():
    return {
        "FRONT_AXLE_L": (L.TRACK_HALF_F, L.Y(L.FRONT_AXLE_V), L.R_TYRE_F),
        "FRONT_AXLE_R": (-L.TRACK_HALF_F, L.Y(L.FRONT_AXLE_V), L.R_TYRE_F),
        "REAR_AXLE_L": (L.TRACK_HALF_R, L.Y(L.REAR_AXLE_V), L.R_TYRE_R),
        "REAR_AXLE_R": (-L.TRACK_HALF_R, L.Y(L.REAR_AXLE_V), L.R_TYRE_R),
        "NOSE": (0.0, L.Y(L.BODY_NOSE_V), 0.385), "TAIL": (0.0, L.Y(L.BODY_TAIL_V), 0.44),
        "STEERING_WHEEL": (0.0, L.Y(L.STEER_WHEEL_PX[1]), L.STEER_WHEEL_Z),
    }
