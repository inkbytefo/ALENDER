"""
Part builders for VEH_TT92_Racing_Car - HOW every part of the car is made.

  landmarks.py  = WHERE and HOW BIG (all numbers)        parts.py = the geometry recipes
  stage*.py     = WHEN (which builders run in which stage, milestones, checks, renders)

Every builder takes a LOD profile: LOW (stage 1 blockout) or HIGH (stages 2-4, final model) and
returns the objects it created. STAGES at the bottom maps the builders to the stages.

Naming: <GROUP>_<Part>[_L|_R]; LOW objects get the _LOW suffix (nm()); UNCERTAIN_ = hidden in the
photo and mirrored/guessed. Groups: BODY, NOSE, AERO, WHEEL, BRAKE, SUSP, EXHAUST, ENG, COCKPIT,
FASTENER. Axes: +X = car left, -Y = front, +Z up; origin midway between the axles on the ground.
Library map: docs/04_MODELING_TOOLKIT.md.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

import landmarks as L
from workbench.bl import mesh, mods, scene
from workbench.bl.fasteners import Fasteners

LOW = dict(name="LOW", ring=16, body_step=40, lathe=20, tube=8, spokes=0, bevel=False,
           C_PRIMARY="02_LOW_PRIMARY", C_SECONDARY="03_LOW_SECONDARY", C_MECH="04_LOW_MECHANICAL",
           C_DETAIL="04_LOW_MECHANICAL")
HIGH = dict(name="HIGH", ring=40, body_step=16, lathe=56, tube=14, spokes=24, bevel=True,
            C_PRIMARY="05_HIGH_BODY", C_SECONDARY="05_HIGH_BODY", C_MECH="06_HIGH_MECHANICAL",
            C_DETAIL="07_DETAILS")

PALETTE = {                          # name: (base colour, metallic, roughness) - 8 materials max (docs/02)
    "MAT_BODY_RED":   ((0.34, 0.012, 0.010), 0.3, 0.36),
    "MAT_RUBBER":     ((0.018, 0.018, 0.018), 0.0, 0.85),
    "MAT_METAL_DARK": ((0.05, 0.05, 0.055), 0.8, 0.45),
    "MAT_CHROME":     ((0.80, 0.80, 0.80), 1.0, 0.12),
    "MAT_EXHAUST":    ((0.42, 0.36, 0.30), 1.0, 0.40),
    "MAT_LEATHER":    ((0.22, 0.11, 0.05), 0.0, 0.55),
    "MAT_STRIPE":     ((0.78, 0.74, 0.64), 0.0, 0.40),          # bonnet stripes + exhaust heat wrap
    "MAT_GLOW":       dict(rgb=(1.0, 0.30, 0.04), metallic=0.0, roughness=0.5,
                           emission=(1.0, 0.22, 0.02), emission_strength=2.2),   # afterburner liner
}

# name-prefix pairs that must never intersect (validate.intersections)
CRITICAL_PAIRS = [
    ("WHEEL_", "BODY_Shell"), ("WHEEL_", "EXHAUST_"), ("EXHAUST_Pipe", "BODY_Shell"),
    ("WHEEL_", "AERO_"), ("SUSP_Rear_Rod", "EXHAUST_"),
    ("COCKPIT_SteeringWheel", "COCKPIT_Seat"), ("WHEEL_Front", "SUSP_Rear"),
    ("WHEEL_Rear", "SUSP_Front"), ("EXHAUST_", "AERO_"), ("WHEEL_Front_Tire", "BRAKE_"),
    ("WHEEL_Rear_Tire", "BRAKE_"), ("ENG_", "BODY_Shell"),
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


def bay_outline(n_corner=6):
    """closed plan polygon [(x, y)] of the engine bay opening: rounded rectangle, tighter at the rear."""
    y0, y1 = L.Y(L.BAY_V[0]), L.Y(L.BAY_V[1])
    hw = L.BAY_HW
    pts = []
    for (cx, cy, r, a0) in ((hw - L.BAY_R_FRONT, y0 + L.BAY_R_FRONT, L.BAY_R_FRONT, -90),
                            (hw - L.BAY_R_REAR, y1 - L.BAY_R_REAR, L.BAY_R_REAR, 0),
                            (-hw + L.BAY_R_REAR, y1 - L.BAY_R_REAR, L.BAY_R_REAR, 90),
                            (-hw + L.BAY_R_FRONT, y0 + L.BAY_R_FRONT, L.BAY_R_FRONT, 180)):
        for i in range(n_corner + 1):
            a = math.radians(a0 + 90.0 * i / n_corner)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def nose_opening():
    """(y0, zm, a, b): face plane, centre height and half axes (m) of the nose mouth."""
    v = L.BODY_NOSE_V
    hw, zt, zb, et, eb, wd = section_params(v)
    zm = zb + (zt - zb) * wd
    return L.Y(v), zm, hw * L.NOSE_GRILLE[0], (zt - zb) * 0.5 * L.NOSE_GRILLE[1]


def ellipse_pts(y, zm, a, b, n):
    return [(a * math.cos(2 * math.pi * k / n), y, zm + b * math.sin(2 * math.pi * k / n)) for k in range(n)]


def body(lod):
    """BODY_Shell: loft of superellipse sections (subsurf L1 baked at HIGH), then three boolean cuts:
    cockpit opening, engine bay pit, oval nose mouth. Cut walls/floors get the dark material."""
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
    # engine bay: open pit down to BAY_FLOOR_Z
    bay = bay_outline(6 if lod["name"] == "HIGH" else 3)
    cut = mesh.extrude_polys("TEMP_BayCutter", "08_TEMP",
                             [([(x, y, L.BAY_FLOOR_Z) for x, y in bay], [(x, y, 1.5) for x, y in bay])])
    mods.boolean(ob, cut, apply=True)
    bpy.data.objects.remove(cut, do_unlink=True)
    # nose: oval grille pocket cut into the flat face
    ny, nzm, na, nb = nose_opening()
    nn = 40 if lod["name"] == "HIGH" else 16
    front = ellipse_pts(ny - 0.06, nzm, na, nb, nn)
    back = ellipse_pts(ny + L.NOSE_POCKET_DEPTH, nzm, na, nb, nn)
    cut = mesh.extrude_polys("TEMP_NoseCutter", "08_TEMP", [(front, back)])
    mods.boolean(ob, cut, apply=True)
    bpy.data.objects.remove(cut, do_unlink=True)
    # interior faces (cut walls + floors) -> dark material; the boolean can leave an empty slot
    ob.data.materials.clear()
    ob.data.materials.append(bpy.data.materials["MAT_BODY_RED"])
    ob.data.materials.append(bpy.data.materials["MAT_METAL_DARK"])
    for p in ob.data.polygons:
        p.material_index = 0
    v0, v1 = L.COCKPIT_V
    b0, b1 = L.BAY_V
    for p in ob.data.polygons:
        c = p.center
        v = L.V_MID + c.y * L.S
        if v0 - 1 <= v <= v1 + 1 and abs(c.x) <= L.open_hw(min(max(v, v0), v1)) + 0.004 \
                and c.z < L.interp(L.BODY_ZTOP, v) - 0.004:
            p.material_index = 1
        elif b0 - 1 <= v <= b1 + 1 and abs(c.x) <= L.BAY_HW + 0.004 and c.z < top_z(v, c.x) - 0.006:
            p.material_index = 1
        elif c.y < ny + L.NOSE_POCKET_DEPTH + 0.002 and (c.x / na) ** 2 + ((c.z - nzm) / nb) ** 2 < 1.004 \
                and c.y > ny - 0.02:
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
    """Old-JDM mouth: wide flat oval in the wedge tip, chrome lip, five horizontal chrome slats set back
    in the dark pocket and a round centre emblem."""
    hi = lod["name"] == "HIGH"
    y0, zm, a, b = nose_opening()
    out = []
    n = 48 if hi else 20
    ring = [Vector(p) + Vector((0, 0.003, 0)) for p in ellipse_pts(y0, zm, a, b, n)]
    ring.append(ring[0])
    out.append(mesh.tube(nm(lod, "NOSE_Ring"), lod["C_SECONDARY"], ring, 0.011, 8 if hi else 5, "MAT_CHROME",
                         smooth_path=False, caps=False))
    yg = y0 + 0.03
    specs = []
    for t in (-0.66, -0.33, 0.0, 0.33, 0.66):
        c = a * 0.99 * math.sqrt(max(0.0, 1 - t * t))
        specs.append((Vector((-c, yg, zm + t * b)), Vector((c, yg, zm + t * b)), 0.0042))
    out.append(mesh.multi_cyl(nm(lod, "NOSE_Grille"), lod["C_SECONDARY"], specs, 6 if hi else 4, "MAT_CHROME"))
    out.append(mesh.lathe(nm(lod, "NOSE_Emblem"), lod["C_SECONDARY"], (0, yg - 0.012, zm),
                          [(0.0, -0.007), (0.019, -0.006), (0.026, -0.002), (0.026, 0.006), (0.0, 0.006)],
                          24 if hi else 10, "MAT_CHROME", closed=False, axis="Y"))
    return out


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


# ============================================================================ EXHAUST
def exhaust_path():
    return [Vector((L.X(u), L.Y(v), z)) for (u, v, z) in L.EXHAUST_PATH]


def exhaust(lod):
    """EXHAUST_*_R (photo side) + mirrored EXHAUST_*_L: 4 headers per bank -> collector -> wrapped pipe
    that sweeps inwards behind the rear axle and ends inside the afterburner can (afterburners())."""
    out = []
    for side, sg in (("R", 1.0), ("L", -1.0)):
        out += exhaust_side(lod, side, sg)
    return out


def exhaust_side(lod, side, sg):
    """sg = +1 builds the right side (-X, as in the photo); sg = -1 mirrors it across x = 0."""
    def mx(p):
        return Vector((sg * p.x, p.y, p.z))
    out = []
    path = [mx(p) for p in exhaust_path()]
    out.append(mesh.tube(nm(lod, f"EXHAUST_Pipe_{side}"), lod["C_MECH"], path, L.EXHAUST_R,
                         lod["tube"], "MAT_EXHAUST", samples=6))
    # headers: leave the flank at the V8 cylinder pitch, run back and drop into the collector
    # (first pipe point)
    col = path[0]
    zh = 0.505
    for i, v in enumerate(L.HEADER_V):
        x0 = -sg * (flank_x(v, zh) - 0.02)
        k = i - 1.5
        p0 = Vector((x0, L.Y(v), zh))
        p2 = Vector((col.x - sg * 0.02, L.Y(v) + 0.04, 0.485 + 0.006 * k))
        p2b = Vector((col.x - sg * 0.02, L.Y(530) + 0.004 * i, 0.47 + 0.006 * k))
        p3 = col + Vector((0.003 * k, -0.015 - 0.004 * (3 - i), 0.003 * k))
        out.append(mesh.tube(nm(lod, f"EXHAUST_Header_{side}{i + 1}"), lod["C_MECH"], [p0, p2, p2b, p3], 0.017,
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
        out.append(mesh.tube(f"EXHAUST_Wrap_{side}", lod["C_DETAIL"], pts, 0.0045, 6, "MAT_STRIPE",
                             smooth_path=False))
        out.append(mesh.tube(f"EXHAUST_WrapCore_{side}", lod["C_DETAIL"], wp, L.EXHAUST_R + 0.002,
                             lod["tube"], "MAT_STRIPE", smooth_path=False))
    else:
        out.append(mesh.tube(nm(lod, f"EXHAUST_Wrap_{side}"), lod["C_MECH"], wp, L.EXHAUST_WRAP_R, lod["tube"],
                             "MAT_STRIPE", smooth_path=False))
    return out


def path_at(path, y):
    for a, b in zip(path, path[1:]):
        if a.y <= y <= b.y:
            t = (y - a.y) / (b.y - a.y)
            return a.lerp(b, t)
    return path[-1]


# ============================================================================ AFTERBURNER (tail outlet)
def afterburners(lod):
    """EXHAUST_AB_*: one jet-style outlet on the centre line, on the round tail face; both side pipes
    run into it. front -> rear: chrome can sleeved over the tail end with dark heat slots and two band
    rings, an outer and an inner ring of flat converging petals (polygonal exit); inside a glowing
    liner, a flame-holder cone and a ring of teeth; two inlet sleeves swallow the pipe ends."""
    out = []
    hi = lod["name"] == "HIGH"
    CM, CD = lod["C_MECH"], lod["C_DETAIL"]
    seg = lod["lathe"] if hi else 16
    R, re = L.AB_CAN_R, L.AB_EXIT_R
    y1, y2 = L.AB_CAN                        # can front / rear
    y3 = y2 + L.AB_PETAL_LEN                 # exit plane
    hw, zt, zb, et, eb, wd = section_params(L.BODY_TAIL_V)
    c = Vector((0.0, L.Y(L.BODY_TAIL_V), zb + (zt - zb) * wd))      # centre of the tail face

    def P(deg, r, lat):
        a = math.radians(deg)
        return c + Vector((r * math.cos(a), lat, r * math.sin(a)))

    out.append(mesh.lathe(nm(lod, "EXHAUST_AB_Can"), CM, c,
                          [(R, y1), (R, y2), (R - 0.010, y2), (R - 0.010, 0.03), (R - 0.020, 0.03),
                           (R - 0.020, y1)], seg, "MAT_CHROME", axis="Y", sharp_angle=35))
    for i, lat in enumerate((y1 + 0.008, y2 - 0.008)):
        out.append(mesh.lathe(nm(lod, f"EXHAUST_AB_Band_{i + 1}"), CM, c,
                              [(R - 0.002, lat - 0.010), (R + 0.007, lat - 0.010), (R + 0.007, lat + 0.010),
                               (R - 0.002, lat + 0.010)], seg, "MAT_METAL_DARK", axis="Y", sharp_angle=35))
    # glowing liner (back disc + tube) and the flame holder in front of it
    out.append(mesh.lathe(nm(lod, "EXHAUST_AB_Glow"), CM, c,
                          [(0.0, 0.035), (re - 0.010, 0.035), (re - 0.010, y3 - 0.05)], seg, "MAT_GLOW",
                          closed=False, caps=False, axis="Y"))
    out.append(mesh.lathe(nm(lod, "EXHAUST_AB_FlameHolder"), CM, c,
                          [(0.0, 0.16), (0.030, 0.12), (0.052, 0.045), (0.0, 0.045)], max(12, seg // 2),
                          "MAT_METAL_DARK", closed=False, axis="Y"))
    path = exhaust_path()
    for side, sg in (("R", 1.0), ("L", -1.0)):                # sleeves swallowing the pipe ends
        p1 = Vector((sg * path[-1].x, path[-1].y, path[-1].z))
        p0 = Vector((sg * path[-2].x, path[-2].y, path[-2].z))
        d = (p1 - p0).normalized()
        out.append(mesh.cyl(nm(lod, f"EXHAUST_AB_Inlet_{side}"), CM, p1 - d * 0.085, p1 - d * 0.005,
                            L.EXHAUST_R + 0.009, lod["tube"], "MAT_METAL_DARK"))
    if not hi:                                                # LOW: one frustum instead of the petals
        out.append(mesh.lathe(nm(lod, "EXHAUST_AB_Petals"), CM, c,
                              [(R + 0.004, y2), (re, y3), (re - 0.008, y3), (R - 0.006, y2)], seg,
                              "MAT_METAL_DARK", axis="Y"))
        return out
    n = L.AB_PETALS
    pitch = 360.0 / n
    for layer, (off, r0, r1, la, lb, mat) in enumerate((
            (0.0, R + 0.008, re, y2 - 0.006, y3, "MAT_METAL_DARK"),
            (pitch / 2, R, re - 0.008, y2 - 0.012, y3 - 0.022, "MAT_EXHAUST"))):
        polys = []
        da = pitch * (0.43 if layer == 0 else 0.45)
        for k in range(n):
            a = 90.0 + off + k * pitch                        # one petal seam on the top centre line
            outer = [P(a - da, r0, la), P(a + da, r0, la), P(a + da * 0.92, r1, lb), P(a - da * 0.92, r1, lb)]
            inner = [P(a - da, r0 - 0.005, la), P(a + da, r0 - 0.005, la),
                     P(a + da * 0.92, r1 - 0.005, lb), P(a - da * 0.92, r1 - 0.005, lb)]
            polys.append((outer, inner))
        out.append(mesh.extrude_polys(f"EXHAUST_AB_Petals{'Outer' if layer == 0 else 'Inner'}", CD, polys, mat))
    # heat slots around the can (thin dark strips; none where the pipes enter) and the flame-holder teeth
    slots, teeth = [], []
    for k in range(L.AB_SLOTS):
        a = 90.0 + k * 360.0 / L.AB_SLOTS
        if min(abs(math.cos(math.radians(a)) - 1), abs(math.cos(math.radians(a)) + 1)) < 0.12:
            continue                                          # pipe inlet side
        w = 2.4                                               # half width in degrees
        la, lb = y1 + 0.03, y2 - 0.03
        o = [P(a - w, R + 0.0015, la), P(a + w, R + 0.0015, la), P(a + w, R + 0.0015, lb), P(a - w, R + 0.0015, lb)]
        i_ = [P(a - w, R - 0.004, la), P(a + w, R - 0.004, la), P(a + w, R - 0.004, lb), P(a - w, R - 0.004, lb)]
        slots.append((o, i_))
    for k in range(20):
        a = k * 18.0
        o = [P(a - 4, re - 0.012, y3 - 0.10), P(a + 4, re - 0.012, y3 - 0.10),
             P(a + 2.4, re - 0.016, y3 - 0.06), P(a - 2.4, re - 0.016, y3 - 0.06)]
        i_ = [P(a - 4, re - 0.040, y3 - 0.10), P(a + 4, re - 0.040, y3 - 0.10),
              P(a + 2.4, re - 0.030, y3 - 0.06), P(a - 2.4, re - 0.030, y3 - 0.06)]
        teeth.append((o, i_))
    out.append(mesh.extrude_polys("EXHAUST_AB_Slots", CD, slots, "MAT_METAL_DARK"))
    out.append(mesh.extrude_polys("EXHAUST_AB_Teeth", CD, teeth, "MAT_METAL_DARK"))
    return out


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
        p1 = Vector((L.X(u1), L.Y(v1), L.REAR_ROD_Z))
        out.append(mesh.cyl(nm(lod, f"SUSP_Rear_Rod_{side}"), lod["C_MECH"], p0, p1, 0.011, lod["tube"],
                            "MAT_CHROME"))
    return out


# ============================================================================ COCKPIT
def cockpit(lod):
    """COCKPIT_*: steering wheel + column, leather seat, dash, red rim lip, padded cowl roll."""
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
    back = mesh.loft_rings(nm(lod, "COCKPIT_Seat_Back"), lod["C_SECONDARY"],
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


# ============================================================================ BONNET / DECK DETAILS
def body_details(lod):
    """filler caps on the rear deck, air filter on the left bonnet flank, two rows of bonnet louvres."""
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
        out.append(mesh.extrude_polys("BODY_Louvres", lod["C_DETAIL"], polys, "MAT_BODY_RED"))
    return out


# ============================================================================ ENGINE (blown V8 in the bay)
def engine(lod):
    """ENG_*: 60-degree V8 (2 x 4 cyl) with a belt-driven Roots blower and four velocity stacks, sitting
    in the bonnet pit. Crank axis along Y, front = -Y. Everything stays inside |x| < BAY_HW and above
    BAY_FLOOR_Z so it never touches the shell (CRITICAL_PAIRS)."""
    out = []
    hi = lod["name"] == "HIGH"
    CM, CD = lod["C_MECH"], lod["C_DETAIL"]
    yc = L.ENG_Y_CENTRE
    zc = L.ENG_CRANK_Z
    th = math.radians(L.ENG_BANK_DEG)
    seg = lod["lathe"] // 2 if hi else 10
    # lower end: oil pan, crankcase, timing cover, bellhousing
    out.append(hard(mesh.box(nm(lod, "ENG_OilPan"), CM, (0, yc, 0.29), (0.20, 0.30, 0.10), "MAT_METAL_DARK"),
                    lod, 0.006))
    out.append(hard(mesh.box(nm(lod, "ENG_Crankcase"), CM, (0, yc, 0.385), (0.22, 0.34, 0.14), "MAT_METAL_DARK"),
                    lod, 0.006))
    out.append(hard(mesh.box(nm(lod, "ENG_TimingCover"), CM, (0, yc - 0.195, 0.39), (0.17, 0.05, 0.20),
                             "MAT_METAL_DARK"), lod, 0.006))
    out.append(mesh.lathe(nm(lod, "ENG_Bellhousing"), CM, (0, yc + 0.17, zc),
                          [(0.12, -0.03), (0.13, 0.02), (0.125, 0.10), (0.095, 0.14), (0.09, 0.19)],
                          seg, "MAT_METAL_DARK", axis="Y", closed=False))
    # banks: head block + cam cover per bank, one exhaust stub per cylinder towards the bay wall
    for side, sg in (("L", 1.0), ("R", -1.0)):
        rot = Matrix.Rotation(sg * th, 3, "Y")
        ax = rot @ Vector((0, 0, 1))
        nrm = (rot @ Vector((1, 0, 0))) * sg                  # outward normal of the bank
        cen = Vector((0, yc, zc)) + ax * 0.115
        out.append(hard(mesh.box(nm(lod, f"ENG_Bank_{side}"), CM, cen, (0.12, 0.34, 0.19),
                                 "MAT_METAL_DARK", rot=rot), lod, 0.004))
        cc = Vector((0, yc, zc)) + ax * 0.225
        out.append(hard(mesh.box(nm(lod, f"ENG_CamCover_{side}"), CM, cc, (0.10, 0.34, 0.03),
                                 "MAT_CHROME", rot=rot), lod, 0.004))
        cap = cc + ax * 0.012 + Vector((0, 0.10, 0))
        out.append(mesh.cyl(nm(lod, f"ENG_OilCap_{side}"), CD, cap, cap + ax * 0.02, 0.018, 12, "MAT_CHROME"))
        port = cen + nrm * 0.06
        xo = sg * (L.BAY_HW - 0.018)
        for i in range(4):
            y = yc + (i - 1.5) * L.ENG_PITCH
            out.append(mesh.cyl(nm(lod, f"ENG_Port_{side}{i + 1}"), CD, Vector((port.x, y, port.z)),
                                Vector((xo, y, port.z - 0.03)), 0.012, 8, "MAT_EXHAUST"))
    # intake manifold + blower (Roots case, chrome) over the valley
    out.append(hard(mesh.box(nm(lod, "ENG_Intake"), CM, (0, yc, 0.595), (0.14, 0.30, 0.14), "MAT_METAL_DARK"),
                    lod, 0.004))
    out.append(hard(mesh.box(nm(lod, "ENG_Blower"), CM, (0, yc, 0.715), (0.22, 0.30, 0.13), "MAT_CHROME"),
                    lod, 0.012))
    if hi:                                                    # rotor-case ribs on the blower sides
        for sgx, tag in ((1, "L"), (-1, "R")):
            for i in range(7):
                y = yc - 0.12 + 0.04 * i
                out.append(mesh.cyl(f"ENG_BlowerRib_{tag}{i + 1}", CD, Vector((sgx * 0.109, y, 0.715)),
                                    Vector((sgx * 0.116, y, 0.715)), 0.048, 14, "MAT_CHROME"))
    # four velocity stacks facing forward on the blower front
    yf = yc - 0.15
    zs = 0.75
    sp = [(0.019, 0.0), (0.019, -0.03), (0.024, -0.05), (0.031, -0.07), (0.038, -0.088),
          (0.034, -0.09), (0.026, -0.076), (0.016, -0.03), (0.016, 0.0)]
    for i, xs_ in enumerate((-0.105, -0.035, 0.035, 0.105)):
        out.append(mesh.lathe(nm(lod, f"ENG_Stack_{i + 1}"), CM, (xs_, yf, zs), sp, seg + 4, "MAT_CHROME",
                              axis="Y"))
    # belt drive on the front: crank pulley -> blower pulley
    yb = yc - 0.225
    zb2 = 0.68
    out.append(mesh.cyl(nm(lod, "ENG_CrankSnout"), CD, Vector((0, yc - 0.17, zc)), Vector((0, yb, zc)), 0.02, 10,
                        "MAT_CHROME"))
    out.append(mesh.lathe(nm(lod, "ENG_CrankPulley"), CD, (0, yb, zc),
                          [(0.012, -0.01), (0.055, -0.01), (0.055, 0.01), (0.012, 0.01)], seg, "MAT_METAL_DARK",
                          axis="Y"))
    out.append(mesh.cyl(nm(lod, "ENG_BlowerDriveShaft"), CD, Vector((0, yf, zb2)), Vector((0, yb, zb2)),
                        0.012, 8, "MAT_CHROME"))
    out.append(mesh.lathe(nm(lod, "ENG_BlowerPulley"), CD, (0, yb, zb2),
                          [(0.012, -0.01), (0.035, -0.01), (0.035, 0.01), (0.012, 0.01)], seg, "MAT_METAL_DARK",
                          axis="Y"))
    r1, r2 = 0.058, 0.038                                     # belt radius around crank / blower pulley
    nz = (r1 - r2) / (zb2 - zc)
    a0 = math.atan2(nz, math.sqrt(1 - nz * nz))
    belt = []
    for k in range(7):                                        # over the top of the blower pulley
        a = a0 + (math.pi - 2 * a0) * k / 6
        belt.append(Vector((r2 * math.cos(a), yb, zb2 + r2 * math.sin(a))))
    for k in range(7):                                        # under the crank pulley
        a = math.pi - a0 + (math.pi + 2 * a0) * k / 6
        belt.append(Vector((r1 * math.cos(a), yb, zc + r1 * math.sin(a))))
    belt.append(belt[0])
    out.append(mesh.tube(nm(lod, "ENG_Belt"), CD, belt, 0.0045, 6, "MAT_RUBBER", smooth_path=False, caps=False))
    return out


# ============================================================================ PANEL LINES
def seam_specs(bvh, polyline, kind, r=0.0018, step=0.03, sg=1.0):
    """[(p0, p1, r)] short cylinders along a polyline projected on the body. kind 'top': polyline of (x, y)
    dropped vertically; kind 'side': polyline of (y, z) shot horizontally from the +-X side (sg)."""
    dense = []
    for a, b in zip(polyline, polyline[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for i in range(n):
            t = i / n
            dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    dense.append(polyline[-1])
    pts = []
    for p in dense:
        if kind == "top":
            hit = bvh.ray_cast(Vector((p[0], p[1], 3.0)), Vector((0, 0, -1)), 5.0)
        else:
            hit = bvh.ray_cast(Vector((sg * 1.5, p[0], p[1])), Vector((-sg, 0, 0)), 5.0)
        pts.append(None if hit[0] is None else hit[0] - hit[1] * 0.0008)
    return [(a, b, r) for a, b in zip(pts, pts[1:]) if a is not None and b is not None]


def panel_lines(lod):
    """BODY_PanelLines (HIGH only): thin dark grooves projected on the shell - bonnet front seam, two
    shoulder lines, cowl seam, tail deck seam. BODY_BayLip: red lip around the engine bay."""
    out = []
    hi = lod["name"] == "HIGH"
    bvh = body_bvh()
    step = 0.03 if hi else 0.06
    specs = []

    def xs(v):
        return min(L.HOOD_SEAM_X, 0.78 * L.body_hw(v))

    f0, f1 = L.HOOD_SEAM_V
    # bonnet panel: front cross seam (bowed forward), two shoulder lines, cowl cross seam
    front = [(c * xs(f0), L.Y(f0) - 0.025 * (1 - c * c)) for c in [-1 + 2 * i / 12 for i in range(13)]]
    specs += seam_specs(bvh, front, "top", step=step)
    for sg in (1.0, -1.0):
        line = [(sg * xs(v), L.Y(v)) for v in range(int(f0), int(f1), 20)] + [(sg * xs(f1), L.Y(f1))]
        specs += seam_specs(bvh, line, "top", step=step)
    specs += seam_specs(bvh, [(-xs(f1), L.Y(f1)), (xs(f1), L.Y(f1))], "top", step=step)
    # rear deck cross seam
    tv = L.TAIL_SEAM_V
    specs += seam_specs(bvh, [(-0.8 * L.body_hw(tv), L.Y(tv)), (0.8 * L.body_hw(tv), L.Y(tv))], "top", step=step)
    if hi:                                                    # grooves are a HIGH-only detail
        out.append(mesh.multi_cyl("BODY_PanelLines", lod["C_DETAIL"], specs, 4, "MAT_METAL_DARK"))
    # red lip around the engine bay (like the cockpit rim lip)
    rim = [Vector((x * 1.01, y, surface_z(bvh, x * 1.03 + math.copysign(0.004, x), y, 0.7)))
           for x, y in bay_outline(6 if hi else 3)]
    rim.append(rim[0])
    out.append(mesh.tube(nm(lod, "BODY_BayLip"), lod["C_SECONDARY"], rim, 0.011, lod["tube"] - 2, "MAT_BODY_RED",
                         smooth_path=False, caps=False))
    return out


# ============================================================================ FRONT DETAILS (old-JDM wedge)
def surface_ribbon(bvh, rows, cols, lift, thick):
    """(verts, faces) of a thin shell lying on the body: rows = [((xa, ya), (xb, yb)), ...] plan
    cross-sections, each split into `cols` cells and dropped onto the surface along -Z."""
    top, bot = [], []
    for (pa, pb) in rows:
        for c in range(cols + 1):
            t = c / cols
            x, y = pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t
            hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 5.0)
            pt, nr = (hit[0], hit[1]) if hit[0] is not None else (Vector((x, y, 0.5)), Vector((0, 0, 1)))
            top.append(pt + nr * (lift + thick))
            bot.append(pt + nr * (lift - thick * 0.5))
    nr_, nc = len(rows), cols + 1
    verts = top + bot
    off = len(top)
    faces = []

    def idx(r, c):
        return r * nc + c
    for r in range(nr_ - 1):
        for c in range(cols):
            q = (idx(r, c), idx(r, c + 1), idx(r + 1, c + 1), idx(r + 1, c))
            faces.append(q)
            faces.append(tuple(off + i for i in reversed(q)))
    ring = [idx(r, 0) for r in range(nr_)] + [idx(nr_ - 1, c) for c in range(1, nc)] + \
           [idx(r, cols) for r in range(nr_ - 2, -1, -1)] + [idx(0, c) for c in range(cols - 1, 0, -1)]
    for i in range(len(ring)):
        a_, b_ = ring[i], ring[(i + 1) % len(ring)]
        faces.append((a_, b_, off + b_, off + a_))
    return verts, faces


def front_details(lod):
    """slanted twin-lamp eyes (smoked plate + chrome trim + 2 lamps), fender mirrors, chin spoiler,
    twin cream stripes over the bonnet. Everything is dropped on the shell with ray casts."""
    out = []
    hi = lod["name"] == "HIGH"
    bvh = body_bvh()
    CS = lod["C_SECONDARY"]
    (x0, v0), (x1, v1) = L.EYE_LINE
    N = 12 if hi else 4
    for side, sg in (("L", 1.0), ("R", -1.0)):
        c0, c1 = Vector((sg * x0, L.Y(v0))), Vector((sg * x1, L.Y(v1)))
        d = (c1 - c0).normalized()
        nrm = Vector((-d.y, d.x))
        rows = []
        for k in range(N + 1):
            t = k / N
            c = c0.lerp(c1, t)
            w = max(0.006, L.interp(L.EYE_WIDTH, t))
            rows.append((tuple(c + nrm * w / 2), tuple(c - nrm * w / 2)))
        verts, faces = surface_ribbon(bvh, rows, 3 if hi else 1, 0.003, 0.004)
        out.append(mesh.from_pydata(nm(lod, f"BODY_Eye_{side}"), CS, verts, faces, "MAT_METAL_DARK",
                                    smooth=False))
        if hi:
            nc = 4
            ring = [Vector(verts[r * nc]) for r in range(N + 1)] + [Vector(verts[r * nc + 3]) for r in range(N, -1, -1)]
            ring = [p + Vector((0, 0, 0.0015)) for p in ring] + [ring[0] + Vector((0, 0, 0.0015))]
            out.append(mesh.tube(f"BODY_EyeTrim_{side}", lod["C_DETAIL"], ring, 0.0022, 6, "MAT_CHROME",
                                 smooth_path=False, caps=False))
        for j, t in enumerate(L.EYE_LAMPS_T):
            c = c0.lerp(c1, t)
            hit = bvh.ray_cast(Vector((c.x, c.y, 3.0)), Vector((0, 0, -1)), 5.0)
            if hit[0] is None:
                continue
            r = 0.016
            lamp = mesh.lathe(nm(lod, f"BODY_EyeLamp_{side}{j + 1}"), CS, (0, 0, 0),
                              [(0.0, 0.009), (r * 0.75, 0.0085), (r, 0.006), (r * 1.1, 0.004), (r * 1.1, -0.004),
                               (0.0, -0.004)], 20 if hi else 8, "MAT_CHROME", closed=False, axis="Z")
            q = Vector((0, 0, 1)).rotation_difference(hit[1])
            xform(lamp, Matrix.Translation(hit[0] + hit[1] * 0.006) @ q.to_matrix().to_4x4())
            out.append(lamp)
        # fender mirror: chrome stalk + body-colour bullet head facing back
        mx, mv = L.MIRROR_PX
        x, y = sg * mx, L.Y(mv)
        z = surface_z(bvh, x, y, 0.6)
        p0 = Vector((x, y, z - 0.01))
        p1 = Vector((x + sg * 0.025, y + 0.01, z + 0.085))
        out.append(mesh.cyl(nm(lod, f"BODY_MirrorStalk_{side}"), CS, p0, p1, 0.006, 8, "MAT_CHROME"))
        out.append(mesh.lathe(nm(lod, f"BODY_MirrorHead_{side}"), CS, p1,
                              [(0.0, -0.055), (0.012, -0.046), (0.021, -0.028), (0.027, -0.006), (0.027, 0.020),
                               (0.024, 0.030), (0.0, 0.031)], 20 if hi else 8, "MAT_BODY_RED", closed=False,
                              axis="Y"))
        out.append(mesh.lathe(nm(lod, f"BODY_MirrorGlass_{side}"), CS, p1,
                              [(0.0, 0.0335), (0.021, 0.0335), (0.021, 0.029), (0.0, 0.029)], 16 if hi else 8,
                              "MAT_CHROME", closed=False, axis="Y"))
    # chin spoiler: thin dark plate under the mouth, slightly wider than the wedge tip
    f0, f1 = L.CHIN_V
    zf, zr = L.CHIN_Z
    yf, yr = L.Y(f0), L.Y(f1)
    ym = L.Y(122)

    def zc(y):
        return zf + (zr - zf) * (y - yf) / (yr - yf)
    plan = [(-0.19, yf), (0.19, yf), (0.235, ym), (0.235, yr), (-0.235, yr), (-0.235, ym)]
    a = [(x, y, zc(y)) for x, y in plan]
    b = [(x, y, zc(y) + 0.008) for x, y in plan]
    out.append(hard(mesh.extrude_polys(nm(lod, "AERO_ChinSpoiler"), CS, [(a, b)], "MAT_METAL_DARK"), lod, 0.002))
    # twin cream stripes from the nose tip to the engine bay
    s0, s1 = L.STRIPE_V
    xc, w = L.STRIPE_X
    nrow = 40 if hi else 10
    verts, faces = [], []
    for sg in (1.0, -1.0):
        rows = []
        for k in range(nrow + 1):
            v = s0 + (s1 - s0) * k / nrow
            rows.append(((sg * xc - w / 2, L.Y(v)), (sg * xc + w / 2, L.Y(v))))
        vv, ff = surface_ribbon(bvh, rows, 2, 0.0007, 0.0006)
        o = len(verts)
        verts += vv
        faces += [tuple(i + o for i in f) for f in ff]
    out.append(mesh.from_pydata(nm(lod, "BODY_Stripes"), CS, verts, faces, "MAT_STRIPE"))
    return out


# ============================================================================ FASTENERS
def fasteners(lod):
    """FASTENER_*: rivets/bolts dropped on the shell (HIGH only, instanced meshes)."""
    if lod["name"] != "HIGH":
        return []
    fs = Fasteners(lod["C_DETAIL"], mat="MAT_CHROME")
    bvh = body_bvh()

    def on_body(x, y, kind):
        hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 5.0)
        if hit[0] is not None:
            fs.place(kind, hit[0] - hit[1] * 0.001, hit[1])

    # rear deck arc behind the cockpit and along both cockpit flanks
    for i in range(15):
        a = math.pi * i / 14
        on_body(0.24 * math.cos(a), L.Y(L.COCKPIT_V[1]) + 0.04 + 0.05 * math.sin(a), "BOLT_M5")
    for sg in (-1, 1):
        for i in range(10):
            v = L.COCKPIT_V[0] + 30 + (L.COCKPIT_V[1] - L.COCKPIT_V[0] - 60) * i / 9
            on_body(sg * (L.open_hw(v) + 0.035), L.Y(v), "BOLT_M5")
    # bonnet strap bolts behind the nose (v 205) and at the cowl seam
    for v in (205, L.HOOD_SEAM_V[1]):
        for sg in (-1, 1):
            for f in (0.35, 0.7):
                on_body(sg * f * L.body_hw(v), L.Y(v), "BOLT_M6")
    # riveted bonnet panel: rows along both shoulder seams and along the front cross seam
    for sg in (-1, 1):
        v = 150.0
        while v < 615:
            on_body(sg * min(L.HOOD_SEAM_X, 0.78 * L.body_hw(v)), L.Y(v), "BOLT_M5")
            v += 22.0
    for i in range(15):
        c = -1 + 2 * i / 14
        on_body(c * min(L.HOOD_SEAM_X, 0.78 * L.body_hw(L.HOOD_SEAM_V[0])),
                L.Y(L.HOOD_SEAM_V[0]) - 0.025 * (1 - c * c) - 0.012, "BOLT_M5")
    bpy.context.view_layer.update()
    return []


# ============================================================================ PIVOTS
def set_pivots(objs):
    """object origins: wheel parts on their axle (they spin), steering parts on the wheel centre,
    everything else at its bbox centre. Instanced fasteners keep their own origin."""
    shared = {o.data.name for o in objs if o.name.startswith("FASTENER_") and o.data.users > 1}
    for ob in objs:
        if ob.type != "MESH" or ob.data.name in shared:
            continue
        axle = None
        for tag, (x, v, R, W) in WHEELS.items():
            pos, side = tag.split("_")
            if ob.name.startswith(f"WHEEL_{pos}_") and ob.name.endswith("_" + side) \
                    or ob.name == f"BRAKE_Drum_{tag}":
                axle = (x, L.Y(v), R)
        if axle:
            scene.set_origin(ob, axle)
        elif ob.name.startswith("COCKPIT_Steering"):
            scene.set_origin(ob, (L.X(L.STEER_WHEEL_PX[0]), L.Y(L.STEER_WHEEL_PX[1]), L.STEER_WHEEL_Z))
        else:
            scene.origin_to_bbox_center(ob)


# ============================================================================ STAGES
# which builders run in which stage (stage 1 runs ALL of them at LOW; stages 2-4 at HIGH)
STAGES = {
    2: ("wheels", "body", "nose"),                                             # primary forms
    3: ("exhaust", "afterburners", "front_suspension", "rear_suspension", "engine"),   # mechanical
    4: ("cockpit", "body_details", "panel_lines", "front_details", "fasteners"),   # details
}


def build_stage(n, lod):
    return {name: globals()[name](lod) for name in STAGES[n]}


def build_global(lod):
    """global proportions only: wheels + body shell."""
    return {"wheels": wheels(lod), "body": body(lod)}


def build_all(lod):
    parts = {}
    for n in sorted(STAGES):
        parts.update(build_stage(n, lod))
    return parts


def guide_points():
    return {
        "FRONT_AXLE_L": (L.TRACK_HALF_F, L.Y(L.FRONT_AXLE_V), L.R_TYRE_F),
        "FRONT_AXLE_R": (-L.TRACK_HALF_F, L.Y(L.FRONT_AXLE_V), L.R_TYRE_F),
        "REAR_AXLE_L": (L.TRACK_HALF_R, L.Y(L.REAR_AXLE_V), L.R_TYRE_R),
        "REAR_AXLE_R": (-L.TRACK_HALF_R, L.Y(L.REAR_AXLE_V), L.R_TYRE_R),
        "NOSE": (0.0, L.Y(L.BODY_NOSE_V), 0.29), "TAIL": (0.0, L.Y(L.BODY_TAIL_V), 0.425),
        "STEERING_WHEEL": (0.0, L.Y(L.STEER_WHEEL_PX[1]), L.STEER_WHEEL_Z),
    }
