"""
Part builders for VEH_Sonnet_Bike (staged pipeline S1-S5, docs/01_WORKFLOW.md).

Sonnet Bike: Next-gen Cyber-Neo Cafe Racer / Hyper-Roadster redesign based on the inline-4
custom platform with premium terracotta/copper & forged carbon aesthetic, aerodynamic
bodywork, high-performance inverted suspension, digital cockpit, and race detailing.

  S1 PRIMITIVE  masses and silhouettes from simple boxes, cylinders, and plates
  S2 LOWPOLY    real builders with clean topology, no bevels, UV atlas = game LOD0
  S3 DETAIL     hero mesh with bevels, weighted normals, subsurf on lofts, fasteners,
                cooling fins, velocity stacks, multi-piece floating brakes, tire tread
  S4 GAME       bake S3 -> S2 atlas, LOD1-2, collision, Godot/engine-ready glb export
  S5 PRESENT    studio clay and dark showcase renders
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim, materials
from workbench.bl.fasteners import Fasteners

mesh.set_ref(L.REF)

CATEGORY = "hero_vehicle"
TARGET_DIMS = (None, 2.05, 1.045)
GROUND = True

PROFILES = {
    1: stages.profile(1, tube=8, tube_s=1, lathe=16, loft=8, tank_st=8, seat_st=4, spokes=5),
    2: stages.profile(2, tube=12, tube_s=3, lathe=36, loft=18, tank_st=20, seat_st=8, spokes=5),
    3: stages.profile(3, tube=20, tube_s=5, lathe=64, loft=28, tank_st=32, seat_st=14, spokes=5),
}

GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.03)

PALETTE = {
    "MAT_BODY_RED":   ((0.78, 0.28, 0.08), 0.70, 0.18),      # Sonnet signature metallic terracotta / copper
    "MAT_BODY_BLACK": ((0.025, 0.025, 0.028), 0.20, 0.20),   # satin obsidian / forged carbon bodywork
    "MAT_SEAT":       dict(pbr="Leather009", tile_m=0.35),   # PBR textured dark Alcantara/leather
    "MAT_METAL_DARK": ((0.035, 0.036, 0.04), 0.85, 0.32),   # black powdercoat / anodized chassis
    "MAT_METAL_RAW":  ((0.82, 0.83, 0.85), 1.0, 0.14),      # billet aluminum & chrome
    "MAT_ENGINE":     ((0.065, 0.068, 0.072), 0.75, 0.48),  # cast anthracite engine alloy
    "MAT_RUBBER":     ((0.032, 0.032, 0.035), 0.0, 0.65),    # tire & grip rubber
    "MAT_GLASS":      dict(rgb=(0.92, 0.94, 0.96), metallic=0.0, roughness=0.03, alpha=0.15),
}

CRITICAL_PAIRS = [
    ("EXHAUST_Header", "WHEEL_Front_Tire"),
    ("EXHAUST_Muffler", "WHEEL_Rear_Tire"),
    ("WHEEL_Rear_Tire", "FRAME_Swingarm"),
    ("SUSP_Fork", "BODY_Tank"),
    ("CTRL_ClipOn", "BODY_Tank"),
    ("DRIVE_Chain", "WHEEL_Rear_Tire"),
    ("ENGINE_Crankcase", "FRAME_Backbone"),
]

P3 = L.P3


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.003):
    """Hard-surface finish: bevel + weighted normals (never subsurf plates)."""
    if P.get("bevel") and bevel:
        mods.bevel(ob, bevel)
        mods.weighted_normal(ob)
    return ob


def organic(ob, P, levels=2):
    """Organic finish: subdivision surface for smooth lofts."""
    if P.get("subsurf"):
        mods.subsurf(ob, 1, levels)
    return ob


def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def steering():
    """Fork axis and steering axis at rest (fork line through front axle, RAKE_DEG)."""
    rake = math.radians(L.RAKE_DEG)
    up = Vector((0.0, math.sin(rake), math.cos(rake)))
    back = Vector((0.0, math.cos(rake), -math.sin(rake)))
    axle = Vector(L.FRONT_AXLE)
    top_len = (Vector(L.P3(*L.FORK_TOP_PX)) - axle).dot(up)
    fork = {"axle": axle, "up": up, "back": back, "len": top_len, "top": axle + up * top_len}
    base = axle + back * L.FORK_OFFSET
    st = {"top": base + up * (top_len + 0.01), "bottom": base + up * (top_len - 0.20), "up": up}
    return fork, st


def guide_points():
    return {
        "FRONT_AXLE": L.FRONT_AXLE,
        "REAR_AXLE": L.REAR_AXLE,
        "SWINGARM_PIVOT": L.P3(*L.SWINGARM_PIVOT_PX),
        "FORK_TOP": L.P3(*L.FORK_TOP_PX),
        "HEADLIGHT": L.P3(*L.HEADLIGHT_PX),
        "SHOCK_BOTTOM": L.P3(*L.SHOCK_BOTTOM_PX),
        "SHOCK_TOP": L.P3(*L.SHOCK_TOP_PX),
        "FOOTPEG": L.P3(*L.FOOTPEG_PX),
    }


# ============================================================================ WHEELS
def tyre_profile(R, W, rim_r, P):
    hw = W / 2.0
    crown_r = R
    shoulder_r = R - (0.014 if W < 0.15 else 0.020)
    bead_r = rim_r + 0.005
    rim_seat_r = rim_r - 0.010
    n = 6 if P["stage"] <= 2 else 10
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        phi = -math.pi / 2 + math.pi * t
        r = crown_r - (crown_r - shoulder_r) * (abs(math.sin(phi)) ** 1.6)
        x = hw * math.sin(phi)
        pts.append((r, x))
    pts.append((bead_r, hw * 0.75))
    pts.append((rim_seat_r, hw * 0.70))
    pts.append((rim_seat_r, -hw * 0.70))
    pts.append((bead_r, -hw * 0.75))
    return pts


def wheel(P, side, R, W, rim_w, center):
    c = Vector(center)
    C = P["coll"]
    tag = "Front" if side == "F" else "Rear"
    rim_r = 0.2159
    out = []

    # tire
    t = mesh.lathe(nm(P, f"WHEEL_{tag}_Tire"), C, c, tyre_profile(R, W, rim_r, P),
                   P["lathe"], "MAT_RUBBER")
    out.append(t)

    # S3 directional tire tread sipes
    if P["stage"] >= 3:
        specs = []
        n_treads = 18
        for i in range(n_treads):
            a = 2 * math.pi * i / n_treads
            p_center = c + Vector((0, math.cos(a) * (R - 0.003), math.sin(a) * (R - 0.003)))
            p_left = c + Vector((-W * 0.35, math.cos(a + 0.08) * (R - 0.008), math.sin(a + 0.08) * (R - 0.008)))
            p_right = c + Vector((W * 0.35, math.cos(a + 0.08) * (R - 0.008), math.sin(a + 0.08) * (R - 0.008)))
            specs.append((p_left, p_center, 0.002))
            specs.append((p_center, p_right, 0.002))
        sipes = mesh.multi_cyl(nm(P, f"WHEEL_{tag}_TreadSipes"), C, specs, 4, "MAT_RUBBER")
        out.append(sipes)

    # rim: drop center, bead seats, flange lips
    hw = rim_w / 2
    rim_prof = [
        (rim_r + 0.014, -hw), (rim_r + 0.014, -hw + 0.008), (rim_r - 0.002, -hw + 0.014),
        (rim_r - 0.008, -hw * 0.5), (rim_r - 0.016, 0.0), (rim_r - 0.008, hw * 0.5),
        (rim_r - 0.002, hw - 0.014), (rim_r + 0.014, hw - 0.008), (rim_r + 0.014, hw),
        (rim_r - 0.024, hw - 0.005), (rim_r - 0.028, 0.0), (rim_r - 0.024, -hw + 0.005)
    ]
    rim = mesh.lathe(nm(P, f"WHEEL_{tag}_Rim"), C, c, rim_prof, P["lathe"], "MAT_METAL_DARK", sharp_angle=45)
    if P.get("bevel"):
        mods.weighted_normal(rim)
    out.append(rim)

    # air valve stem (S3)
    if P["stage"] >= 3:
        v_loc = c + Vector((0.02, math.cos(0.8) * (rim_r - 0.01), math.sin(0.8) * (rim_r - 0.01)))
        v_stem = mesh.cyl(nm(P, f"WHEEL_{tag}_ValveStem"), C, v_loc, v_loc + Vector((0.015, 0.008, 0.008)),
                          0.004, 8, "MAT_METAL_RAW")
        out.append(v_stem)

    # hub
    hub_w = 0.13 if side == "F" else 0.16
    hub = mesh.lathe(nm(P, f"WHEEL_{tag}_Hub"), C, c,
                     [(0.014, -hub_w / 2), (0.056, -hub_w / 2), (0.064, -hub_w / 2 + 0.02),
                      (0.064, hub_w / 2 - 0.02), (0.056, hub_w / 2), (0.014, hub_w / 2)],
                     max(12, P["lathe"] // 2), "MAT_METAL_DARK", closed=False)
    out.append(hub)

    # 5-split-spoke (Y-spoke) lightweight design
    n = P["spokes"]
    for k in range(n):
        a0 = 2 * math.pi * k / n + (0.35 if side == "F" else 0.0)
        for s in (-1, 1):
            a_hub = a0
            a_rim = a0 + s * 0.15
            p0 = c + Vector((0, math.cos(a_hub) * 0.056, math.sin(a_hub) * 0.056))
            p1 = c + Vector((0, math.cos(a_rim) * (rim_r - 0.02), math.sin(a_rim) * (rim_r - 0.02)))
            r_spoke = [0.012, 0.007] if P["stage"] >= 2 else 0.009
            spk = mesh.tube(nm(P, f"WHEEL_{tag}_Spoke_{k}{'ab'[s > 0]}"), C, [p0, p1],
                            r_spoke, 6 if P["stage"] <= 2 else 10, "MAT_METAL_DARK", smooth_path=False)
            out.append(spk)

    # inner wheel backing dish
    dish = mesh.cyl(nm(P, f"WHEEL_{tag}_Dish"), C, c - Vector((0.002, 0, 0)),
                    c + Vector((0.002, 0, 0)), rim_r + 0.002, max(12, P["lathe"] // 2), "MAT_METAL_DARK")
    out.append(dish)

    # Akira-inspired aerodynamic rear aero disc cover
    if side == "R":
        disc_r = rim_r - 0.002
        for sg, xs in ((1, 0.048), (-1, -0.048)):
            ad = mesh.lathe(nm(P, f"WHEEL_Rear_AeroDisc_{'L' if sg > 0 else 'R'}"), C, c,
                            [(0.038, xs), (disc_r * 0.55, xs + sg * 0.004), (disc_r, xs)],
                            P["lathe"], "MAT_BODY_BLACK", closed=False)
            out.append(ad)
            cap = mesh.cyl(nm(P, f"WHEEL_Rear_AeroCap_{'L' if sg > 0 else 'R'}"), C,
                           c + Vector((xs, 0, 0)), c + Vector((xs + sg * 0.008, 0, 0)),
                           0.042, 16, "MAT_BODY_RED")
            out.append(cap)
    return out


def wheels(P):
    out = []
    out += wheel(P, "F", L.R_TYRE_F, L.W_TYRE_F, 0.089, L.FRONT_AXLE)
    out += wheel(P, "R", L.R_TYRE_R, L.W_TYRE_R, 0.140, L.REAR_AXLE)
    return out


def wheels_prim(P):
    C = P["coll"]
    return [
        prim.wheel_px(nm(P, "WHEEL_Front_Tire"), C, L.FRONT_AXLE_PX, L.R_TYRE_F * L.S, L.W_TYRE_F / 2, segs=16, mat="MAT_RUBBER"),
        prim.wheel_px(nm(P, "WHEEL_Rear_Tire"), C, L.REAR_AXLE_PX, L.R_TYRE_R * L.S, L.W_TYRE_R / 2, segs=16, mat="MAT_RUBBER"),
        prim.wheel_px(nm(P, "WHEEL_Front_Rim"), C, L.FRONT_AXLE_PX, 0.216 * L.S, 0.045, segs=16, mat="MAT_METAL_DARK"),
        prim.wheel_px(nm(P, "WHEEL_Rear_Rim"), C, L.REAR_AXLE_PX, 0.216 * L.S, 0.070, segs=16, mat="MAT_METAL_DARK"),
    ]


# ============================================================================ BRAKES & AXLES
def brake_disc(P, name, center, x, r_out, r_in, thick=0.005, drilled=True):
    c = Vector(center) + Vector((x, 0, 0))
    C = P["coll"]
    out = []

    rotor = mesh.lathe(nm(P, name), C, c,
                       [(r_in, -thick / 2), (r_out, -thick / 2), (r_out, thick / 2), (r_in, thick / 2)],
                       P["lathe"], "MAT_METAL_RAW", sharp_angle=30)
    out.append(rotor)

    c_prof = [(0.056, -0.004), (r_in + 0.004, -0.004), (r_in + 0.004, 0.004), (0.056, 0.004)]
    carrier = mesh.lathe(nm(P, name + "_Carrier"), C, c, c_prof,
                         max(12, P["lathe"] // 2), "MAT_METAL_DARK", sharp_angle=30)
    out.append(carrier)

    if P["stage"] >= 3:
        nb = 8
        for i in range(nb):
            a = 2 * math.pi * i / nb
            bp = c + Vector((0, math.cos(a) * (r_in + 0.002), math.sin(a) * (r_in + 0.002)))
            bob = mesh.cyl(nm(P, f"{name}_Bobbin_{i}"), C, bp - Vector((thick * 0.8, 0, 0)),
                           bp + Vector((thick * 0.8, 0, 0)), 0.0075, 10, "MAT_BODY_RED")
            out.append(bob)

        if drilled:
            specs = []
            for ri, rr in enumerate([r_in + (r_out - r_in) * f for f in (0.35, 0.60, 0.82)]):
                for i in range(24):
                    a = 2 * math.pi * (i + 0.5 * ri) / 24
                    q = c + Vector((0, math.cos(a) * rr, math.sin(a) * rr))
                    specs.append((q + Vector((-thick * 0.52, 0, 0)), q + Vector((thick * 0.52, 0, 0)), 0.0035))
            out.append(mesh.multi_cyl(nm(P, name + "_Holes"), C, specs, 6, "MAT_METAL_DARK"))
    return out


def brakes(P):
    out = []
    C = P["coll"]

    # dual front floating wave discs & radial Brembo-style monobloc calipers
    for s, x in (("R", -0.072), ("L", 0.072)):
        out += brake_disc(P, f"BRAKE_Front_Disc_{s}", L.FRONT_AXLE, x, 0.160, 0.100)
        cp = Vector(P3(803, 468))
        cx = x + (0.018 if x > 0 else -0.018)
        cal = mesh.box(nm(P, f"BRAKE_Front_Caliper_{s}"), C, (cx, cp.y, cp.z),
                       (0.038, 0.052, 0.115), "MAT_METAL_DARK",
                       rot=Matrix.Rotation(math.radians(35), 3, "X"))
        hard(cal, P, bevel=0.005)
        out.append(cal)

        if P["stage"] >= 3:
            logo_p = Vector((cx + (0.020 if cx > 0 else -0.020), cp.y, cp.z))
            logo = mesh.box(nm(P, f"BRAKE_Front_Logo_{s}"), C, logo_p, (0.003, 0.035, 0.055), "MAT_METAL_RAW",
                            rot=Matrix.Rotation(math.radians(35), 3, "X"))
            out.append(logo)

    # rear wave disc & compact underslung caliper
    out += brake_disc(P, "BRAKE_Rear_Disc", L.REAR_AXLE, -0.078, 0.135, 0.075, drilled=False)
    cp = Vector(P3(277, 412))
    r_cal = mesh.box(nm(P, "BRAKE_Rear_Caliper"), C, (-0.092, cp.y, cp.z),
                     (0.035, 0.070, 0.045), "MAT_METAL_DARK")
    hard(r_cal, P, bevel=0.004)
    out.append(r_cal)

    # axles
    fa, ra = Vector(L.FRONT_AXLE), Vector(L.REAR_AXLE)
    out.append(mesh.cyl(nm(P, "SUSP_Front_Axle"), C, fa + Vector((-0.13, 0, 0)),
                        fa + Vector((0.13, 0, 0)), 0.012, 16, "MAT_METAL_RAW"))
    out.append(mesh.cyl(nm(P, "SUSP_Rear_Axle"), C, ra + Vector((-0.17, 0, 0)),
                        ra + Vector((0.17, 0, 0)), 0.013, 16, "MAT_METAL_RAW"))
    return out


def brakes_prim(P):
    C = P["coll"]
    return [
        prim.wheel_px(nm(P, "BRAKE_Front_Disc_R"), C, L.FRONT_AXLE_PX, 0.160 * L.S, 0.004, segs=12, mat="MAT_METAL_RAW", x=-0.072),
        prim.wheel_px(nm(P, "BRAKE_Front_Disc_L"), C, L.FRONT_AXLE_PX, 0.160 * L.S, 0.004, segs=12, mat="MAT_METAL_RAW", x=0.072),
        prim.wheel_px(nm(P, "BRAKE_Rear_Disc"), C, L.REAR_AXLE_PX, 0.135 * L.S, 0.004, segs=12, mat="MAT_METAL_RAW", x=-0.078),
    ]


# ============================================================================ FRAME
def frame(P):
    out = []
    C = P["coll"]
    seg, smp = P["tube"], P["tube_s"]
    fork, st = steering()

    # head tube
    ht = mesh.cyl(nm(P, "FRAME_HeadTube"), C, st["bottom"] - st["up"] * 0.02, st["top"] - st["up"] * 0.05,
                  0.030, seg, "MAT_METAL_DARK")
    hard(ht, P, bevel=0.003)
    out.append(ht)

    # backbone and subframe tubes
    def rail(name, pts, xs, r=0.018, mat="MAT_METAL_DARK"):
        for s, sg in (("L", 1), ("R", -1)):
            xl = xs if isinstance(xs, (list, tuple)) else [xs] * len(pts)
            p = [P3(u, v, sg * x) for (u, v), x in zip(pts, xl)]
            out.append(mesh.tube(nm(P, f"{name}_{s}"), C, p, r, seg, mat, samples=smp))

    rail("FRAME_Backbone", L.FRAME_BACKBONE, [0.035, 0.07, 0.09, 0.10, 0.105, 0.11], 0.018)
    rail("FRAME_RearDown", L.FRAME_REAR_DOWN, [0.11, 0.115, 0.118, 0.118], 0.018)
    rail("UNCERTAIN_FRAME_Downtube", L.FRAME_DOWNTUBE, [0.04, 0.05, 0.06], 0.016)
    rail("FRAME_Subframe_Upper", L.FRAME_SUB_UPPER, [0.05, 0.065, 0.075, 0.08, 0.09, 0.105], 0.011, "MAT_METAL_RAW")
    rail("FRAME_Subframe_Lower", L.FRAME_SUB_LOWER, [0.08, 0.095, 0.108, 0.115], 0.012)

    # front cylinder head hanger gusset
    gusset = mesh.plate(nm(P, "FRAME_Gusset_Front"), C, [(648, 326), (738, 338), (738, 350), (648, 334)],
                        -0.05, 0.05, "MAT_METAL_DARK")
    hard(gusset, P, bevel=0.002)
    out.append(gusset)

    # central frame backbone spine
    p_center = [P3(u, v, 0.0) for (u, v) in L.FRAME_BACKBONE]
    spine = mesh.tube(nm(P, "FRAME_Backbone_Center"), C, p_center, 0.022, seg, "MAT_METAL_DARK", samples=smp)
    out.append(spine)

    # subframe crossmembers
    for i, (u, v, x) in enumerate(((330, 279, 0.058), (470, 301, 0.085))):
        out.append(mesh.cyl(nm(P, f"UNCERTAIN_FRAME_Crossmember_{i}"), C, P3(u, v, -x), P3(u, v, x),
                            0.009, seg, "MAT_METAL_DARK"))

    # CNC swingarm pivot plates
    for s, (x0, x1) in (("L", (0.145, 0.163)), ("R", (-0.163, -0.145))):
        plate = mesh.plate(nm(P, f"FRAME_PivotPlate_{s}"), C, L.PIVOT_PLATE_POLY, x0, x1, "MAT_METAL_DARK")
        hard(plate, P, bevel=0.004)
        out.append(plate)
    return out


def frame_prim(P):
    C = P["coll"]
    return [
        prim.plate_px(nm(P, "FRAME_PivotPlate_L"), C, L.PIVOT_PLATE_POLY, 0.01, mat="MAT_METAL_DARK", x0=0.145, x1=0.163),
        prim.plate_px(nm(P, "FRAME_PivotPlate_R"), C, L.PIVOT_PLATE_POLY, 0.01, mat="MAT_METAL_DARK", x0=-0.163, x1=-0.145),
        prim.plate_px(nm(P, "FRAME_Gusset_Front"), C, [(648, 326), (738, 338), (738, 350), (648, 334)], 0.02, mat="MAT_METAL_DARK", x0=-0.05, x1=0.05),
        prim.cyl_px(nm(P, "FRAME_HeadTube"), C, (770, 250), (778, 296), 0.03, segs=8, mat="MAT_METAL_DARK"),
    ]


# ============================================================================ SWINGARM & REAR HUGGER
def swingarm(P):
    out = []
    C = P["coll"]
    seg = max(P["tube"], 10)
    pv = Vector(P3(*L.SWINGARM_PIVOT_PX))

    # main box-section swingarm arms
    poly = [(495, 458), (300, 459), (268, 461), (262, 468), (262, 482), (268, 489),
            (300, 491), (495, 490), (507, 480), (507, 468)]
    for s, (x0, x1) in (("L", (0.112, 0.142)), ("R", (-0.142, -0.112))):
        arm = mesh.plate(nm(P, f"FRAME_Swingarm_{s}"), C, poly, x0, x1, "MAT_METAL_DARK")
        hard(arm, P, bevel=0.005)
        out.append(arm)

    # box cross-brace behind rear tire
    cb = Vector(P3(470, 474))
    brace = mesh.box(nm(P, "FRAME_Swingarm_Brace"), C, cb, (0.224, 0.05, 0.05), "MAT_METAL_DARK")
    hard(brace, P, bevel=0.004)
    out.append(brace)

    # upper curved tubular cantilever truss brace
    if P["stage"] >= 2:
        for s, sg in (("L", 1), ("R", -1)):
            x_arm = sg * 0.127
            p_pivot = P3(485, 460, x_arm)
            p_arch = P3(380, 412, x_arm)
            p_drop = P3(280, 462, x_arm)
            cant = mesh.tube(nm(P, f"FRAME_Swingarm_Cantilever_{s}"), C, [p_pivot, p_arch, p_drop],
                             0.012, seg, "MAT_METAL_DARK", samples=3)
            out.append(cant)

    # swingarm pivot shaft and outer bolts
    out.append(mesh.cyl(nm(P, "FRAME_Swingarm_PivotShaft"), C, pv + Vector((-0.175, 0, 0)),
                        pv + Vector((0.175, 0, 0)), 0.012, seg, "MAT_METAL_RAW"))
    for s, sg in (("L", 1), ("R", -1)):
        out.append(mesh.cyl(nm(P, f"FASTENER_PivotBolt_{s}"), C, pv + Vector((sg * 0.163, 0, 0)),
                            pv + Vector((sg * 0.175, 0, 0)), 0.020, 6, "MAT_METAL_RAW"))

    # chain adjuster blocks & paddock stand bobbins
    for s, sg in (("L", 1), ("R", -1)):
        y, z = L.P(266, 475)
        adj = mesh.box(nm(P, f"FRAME_Swingarm_ChainAdjuster_{s}"), C, (sg * 0.143, y, z),
                       (0.008, 0.03, 0.026), "MAT_METAL_RAW")
        hard(adj, P, bevel=0.002)
        out.append(adj)
        spool = mesh.cyl(nm(P, f"FRAME_Swingarm_Spool_{s}"), C,
                         Vector((sg * 0.145, y + 0.02, z - 0.025)),
                         Vector((sg * 0.175, y + 0.02, z - 0.025)), 0.014, 12, "MAT_METAL_RAW", r1=0.011)
        out.append(spool)

    # NEW: Rear carbon tire hugger (curved plate extruded across X)
    hugger = mesh.plate(nm(P, "FRAME_RearHugger"), C, L.REAR_HUGGER_POLY, -0.085, 0.085, "MAT_BODY_BLACK")
    hard(hugger, P, bevel=0.002)
    out.append(hugger)

    # Integrated chain guard extending forward along chain top
    cg_p0 = Vector(P3(375, 412, 0.105))
    cg_p1 = Vector(P3(480, 455, 0.105))
    cg = mesh.tube(nm(P, "FRAME_ChainGuard"), C, [cg_p0, cg_p1],
                   0.008, 6, "MAT_BODY_BLACK", smooth_path=False)
    out.append(cg)
    return out


def swingarm_prim(P):
    C = P["coll"]
    return [
        prim.plate_px(nm(P, "FRAME_Swingarm_R"), C, L.SWINGARM_POLY, 0.015, mat="MAT_METAL_DARK", x0=-0.142, x1=-0.112),
        prim.plate_px(nm(P, "FRAME_Swingarm_L"), C, L.SWINGARM_POLY, 0.015, mat="MAT_METAL_DARK", x0=0.112, x1=0.142),
        prim.plate_px(nm(P, "FRAME_Swingarm_Cantilever"), C, L.CANTILEVER_POLY, 0.015, mat="MAT_METAL_DARK", x0=-0.142, x1=-0.112, tol=3),
        prim.plate_px(nm(P, "FRAME_RearHugger"), C, L.REAR_HUGGER_POLY, 0.085, mat="MAT_BODY_BLACK", tol=4),
    ]


# ============================================================================ REAR SUSPENSION
def rear_susp(P):
    out = []
    C = P["coll"]
    seg = max(P["tube"], 10)
    sb, stp = Vector(P3(*L.SHOCK_BOTTOM_PX)), Vector(P3(*L.SHOCK_TOP_PX))
    d = (stp - sb)
    dn = d.normalized()

    # damper body & remote gold reservoir canister
    out.append(mesh.cyl(nm(P, "SUSP_Shock_Rear_Body"), C, sb, stp, 0.022, seg, "MAT_METAL_RAW"))
    out.append(mesh.cyl(nm(P, "SUSP_Shock_Rear_Reservoir"), C, stp - d * 0.25, stp + d * 0.02, 0.028,
                        seg, "MAT_BODY_RED"))

    # threaded preload rings (S3)
    if P["stage"] >= 3:
        p_ring = sb + d * 0.65
        out.append(mesh.cyl(nm(P, "SUSP_Shock_Rear_PreloadRing"), C, p_ring - dn * 0.008, p_ring + dn * 0.008,
                            0.033, seg, "MAT_METAL_DARK"))

    # coil spring in Sonnet metallic copper
    if P["stage"] <= 2:
        out.append(mesh.cyl(nm(P, "SUSP_Shock_Rear_Spring"), C, sb + d * 0.1, sb + d * 0.62, 0.034, 10,
                            "MAT_BODY_RED"))
    else:
        n1, n2 = mesh.frame_for(dn)
        pts = []
        turns, steps = 7, 7 * 16
        for i in range(steps + 1):
            t = i / float(steps)
            a = 2 * math.pi * turns * t
            pts.append(sb + d * (0.1 + 0.52 * t) + 0.031 * (math.cos(a) * n1 + math.sin(a) * n2))
        out.append(mesh.tube(nm(P, "SUSP_Shock_Rear_Spring"), C, pts, 0.0055, 8, "MAT_BODY_RED", smooth_path=False))
    return out


def rear_susp_prim(P):
    return [prim.cyl_px(nm(P, "SUSP_Shock_Rear_Body"), P["coll"], L.SHOCK_BOTTOM_PX, L.SHOCK_TOP_PX, 0.025, segs=8, mat="MAT_METAL_RAW")]


# ============================================================================ DRIVE
def drive(P):
    out = []
    C = P["coll"]
    ra = Vector(L.REAR_AXLE)
    fs = Vector(P3(522, 468))
    xs = 0.105

    # rear wheel sprocket (45T)
    out.append(mesh.lathe(nm(P, "DRIVE_Sprocket_Rear"), C, ra + Vector((xs, 0, 0)),
                          [(0.06, -0.004), (0.098, -0.004), (0.098, 0.004), (0.06, 0.004)],
                          max(16, P["lathe"] // 2), "MAT_METAL_RAW"))

    # front countershaft sprocket (16T)
    out.append(mesh.lathe(nm(P, "DRIVE_Sprocket_Front"), C, fs + Vector((xs, 0, 0)),
                          [(0.01, -0.005), (0.042, -0.005), (0.042, 0.005), (0.01, 0.005)],
                          16, "MAT_METAL_RAW"))

    # 525 drive chain loop
    loop = []
    for i in range(25):
        a = -math.pi / 2 + math.pi * i / 24
        loop.append(ra + Vector((xs, math.cos(a) * 0.100, math.sin(a) * 0.100)))
    for i in range(13):
        a = math.pi / 2 + math.pi * i / 12
        loop.append(fs + Vector((xs, math.cos(a) * 0.045, math.sin(a) * 0.045)))
    loop.append(loop[0])
    out.append(mesh.tube(nm(P, "DRIVE_Chain"), C, loop, 0.006, 6 if P["stage"] <= 2 else 8,
                         "MAT_METAL_DARK", smooth_path=False, caps=False))
    return out


def drive_prim(P):
    return [prim.wheel_px(nm(P, "DRIVE_Sprocket_Rear"), P["coll"], L.REAR_AXLE_PX, 0.098 * L.S, 0.004, segs=12, mat="MAT_METAL_RAW", x=0.105)]


# ============================================================================ FUEL TANK
def _se_v(phi, vt, vb, vmid, et, eb):
    s = math.sin(phi)
    if s >= 0:
        return vmid - (vmid - vt) * abs(s) ** (2.0 / et)
    return vmid + (vb - vmid) * abs(s) ** (2.0 / eb)


def _se_x(phi, hw, et, eb):
    c, s = math.cos(phi), math.sin(phi)
    return hw * abs(c) ** (2.0 / (et if s >= 0 else eb))


def tank_ring(u, vt, vb, hw, v_bound, recess, n_up, n_low, et=2.5, eb=5.0, wd=0.62):
    vmid = vt + (vb - vt) * (1.0 - wd)
    v_bound = min(max(v_bound, vt + 1.0), vb - 3.0)
    lo, hi = -math.pi / 2, math.pi / 2
    for _ in range(40):
        m = (lo + hi) / 2
        if _se_v(m, vt, vb, vmid, et, eb) > v_bound:
            lo = m
        else:
            hi = m
    pb = (lo + hi) / 2
    side = []
    for i in range(n_up + 1):
        ph = math.pi / 2 + (pb - math.pi / 2) * i / n_up
        side.append((_se_x(ph, hw, et, eb), _se_v(ph, vt, vb, vmid, et, eb), False))
    lo2, hi2 = -math.pi / 2, pb
    target = min(v_bound + 1.5, vb - 1.0)
    for _ in range(40):
        m = (lo2 + hi2) / 2
        if _se_v(m, vt, vb, vmid, et, eb) > target:
            lo2 = m
        else:
            hi2 = m
    ps = (lo2 + hi2) / 2
    for i in range(n_low + 1):
        ph = ps + (-math.pi / 2 - ps) * i / n_low
        side.append((_se_x(ph, hw, et, eb) * recess, _se_v(ph, vt, vb, vmid, et, eb), True))
    return side, len(side) - 1


def tank(P):
    n_st = P["tank_st"]
    stations = []
    us = lin(493.0, 755.0, n_st)
    for u in us:
        vt = tables.polyline_v(L.TANK_TOP, u)
        vb = tables.polyline_v(L.TANK_BOTTOM, u)
        hw = tables.interp(L.TANK_HALF_WIDTH, u)
        stations.append((u, vt, max(vb, vt + 2.0), hw, 2.5, 5.0, 0.62))

    if P["stage"] <= 2:
        ob = mesh.loft_px(nm(P, "BODY_Tank"), P["coll"], stations, P["loft"], "MAT_BODY_RED")
        return [ob]

    # Stage 3: boundary-aware loft with black knee recess, creased lip, 2 materials
    bm = bmesh.new()
    crease = bm.edges.layers.float.new("crease_edge")
    rings, blacks = [], []
    for (u, vt, vb, hw, et, eb, wd) in stations:
        black = u < L.TANK_BLACK_U_MAX
        vbnd = tables.polyline_v(L.TANK_BLACK_BOUNDARY, u) if black else vt + (vb - vt) * 0.62
        side, _ = tank_ring(u, vt, vb, hw, vbnd, L.TANK_RECESS if black else 1.0, 9, 7)
        ring = [(x, v) for (x, v, _) in side]
        ring += [(-x, v) for (x, v) in reversed(ring[1:-1])]
        rings.append([bm.verts.new(L.P3(u, v, x)) for (x, v) in ring])
        blacks.append(black)
    n = len(rings[0])
    half = 9 + 1 + 7 + 1
    for i in range(len(rings) - 1):
        for k in range(n):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % n], rings[i + 1][(k + 1) % n], rings[i + 1][k]))
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
    ob = mesh.finish(nm(P, "BODY_Tank"), bm, P["coll"], "MAT_BODY_RED", sharp_angle=75)
    ob.data.materials.append(bpy.data.materials["MAT_BODY_BLACK"])
    mods.subsurf(ob, 1, 2)

    # flush aero filler cap on crown
    cy, cz = L.P(640, 241)
    cap = mesh.lathe(nm(P, "BODY_Tank_FillerCap"), P["coll"], (0.0, cy, cz - 0.005),
                     [(0.001, 0.0), (0.042, 0.0), (0.045, 0.004), (0.04, 0.007), (0.001, 0.007)],
                     32, "MAT_METAL_RAW", axis="Z", closed=True)

    out = [ob, cap]
    for sg in (-1, 1):
        ai_pos = Vector(P3(745, 290, sg * 0.125))
        ai = mesh.box(nm(P, f"BODY_Tank_AirIntake_{'L' if sg > 0 else 'R'}"), P["coll"], ai_pos,
                      (0.025, 0.055, 0.040), "MAT_BODY_BLACK")
        hard(ai, P, bevel=0.002)
        out.append(ai)
    return out


def tank_prim(P):
    return [prim.plate_px(nm(P, "BODY_Tank"), P["coll"], L.TANK_TOP + L.TANK_BOTTOM[::-1], 0.155, mat="MAT_BODY_RED", tol=6)]


# ============================================================================ SEAT & TAIL
def seat(P):
    out = []
    n = P["seat_st"]
    C = P["coll"]

    # ergonomic Alcantara cafe saddle
    st = []
    for u in lin(405.0, 500.0, n):
        vt = tables.polyline_v(L.SEAT_TOP, u)
        vb = tables.polyline_v(L.SEAT_BOTTOM_V, u)
        st.append((u, vt, vb, tables.interp(L.SEAT_HALF_WIDTH, u), 3.2, 6.0, 0.45))
    s_ob = mesh.loft_px(nm(P, "BODY_Seat"), C, st, P["loft"], "MAT_SEAT")
    organic(s_ob, P, levels=2)
    out.append(s_ob)

    # seat hump / cowl
    st_hump = []
    for u in lin(333.0, 410.0, max(4, n)):
        vt = tables.polyline_v(L.HUMP_TOP, u)
        vb = tables.polyline_v(L.HUMP_BOTTOM_V, u)
        st_hump.append((u, vt, vb, tables.interp(L.HUMP_HALF_WIDTH, u), 5.0, 7.0, 0.35))
    h_ob = mesh.loft_px(nm(P, "BODY_Seat_Hump"), C, st_hump, P["loft"], "MAT_BODY_RED")
    organic(h_ob, P, levels=2)
    out.append(h_ob)

    # tail sub-cowl
    st_tail = []
    for u in lin(303.0, 495.0, max(6, n + 4)):
        vt = tables.polyline_v(L.TAIL_TOP, u)
        vb = tables.polyline_v(L.TAIL_BOTTOM, u)
        st_tail.append((u, vt, max(vb, vt + 2.0), tables.interp(L.TAIL_HALF_WIDTH, u), 5.0, 5.0, 0.5))
    t_ob = mesh.loft_px(nm(P, "BODY_Tail"), C, st_tail, max(10, P["loft"] // 2), "MAT_BODY_BLACK")
    organic(t_ob, P, levels=1)
    out.append(t_ob)

    # integrated slim LED strip tail lightblade
    tl = mesh.plate(nm(P, "BODY_TailLight"), C, L.TAILLIGHT_POLY, -0.045, 0.045, "MAT_BODY_RED")
    hard(tl, P, bevel=0.003)
    out.append(tl)

    # left and right side subframe panels
    for s, (x0, x1) in (("L", (0.112, 0.124)), ("R", (-0.124, -0.112))):
        sp = mesh.plate(nm(P, f"BODY_SidePanel_{s}"), C, L.SIDEPANEL_POLY, x0, x1, "MAT_BODY_BLACK")
        hard(sp, P, bevel=0.004)
        out.append(sp)

    # seat undertray pan
    pan_poly = [(305, 268), (345, 272), (410, 285), (500, 295), (500, 306), (410, 298), (345, 284), (305, 278)]
    pan = mesh.plate(nm(P, "BODY_SeatPan"), C, pan_poly, -0.09, 0.09, "MAT_BODY_BLACK")
    hard(pan, P, bevel=0.002)
    out.append(pan)

    # Twin aero venturi flow tunnels inside tail cowl
    for sg in (-1, 1):
        p_front = Vector(P3(390, 275, sg * 0.055))
        p_rear = Vector(P3(318, 276, sg * 0.045))
        tunnel = mesh.tube(nm(P, f"BODY_Tail_Tunnel_{'L' if sg > 0 else 'R'}"), C,
                           [p_front, p_rear], 0.010, 8, "MAT_BODY_BLACK", smooth_path=False)
        out.append(tunnel)

    # Minimalist CNC tail tidy license plate bracket tucked under tail
    p_sub = Vector(P3(320, 280, 0.0))
    p_plate = Vector(P3(295, 290, 0.0))
    tidy_arm = mesh.tube(nm(P, "BODY_TailTidy_Bracket"), C, [p_sub, p_plate],
                         0.006, 6, "MAT_METAL_DARK", smooth_path=False)
    out.append(tidy_arm)

    plate_panel = mesh.plate(nm(P, "BODY_TailTidy_Plate"), C, L.TAIL_TIDY_POLY, -0.07, 0.07, "MAT_BODY_BLACK")
    hard(plate_panel, P, bevel=0.002)
    out.append(plate_panel)

    for sg in (-1, 1):
        p_sig = p_plate + Vector((sg * 0.08, -0.01, 0.02))
        sig = mesh.cyl(nm(P, f"BODY_TailTidy_Signal_{'L' if sg > 0 else 'R'}"), C,
                       p_sig - Vector((sg * 0.016, 0, 0)), p_sig + Vector((sg * 0.01, 0, 0)),
                       0.007, 8, "MAT_BODY_RED")
        out.append(sig)
    return out


def seat_prim(P):
    C = P["coll"]
    pan_poly = [(305, 268), (345, 272), (410, 285), (500, 295), (500, 306), (410, 298), (345, 284), (305, 278)]
    return [
        prim.plate_px(nm(P, "BODY_Seat"), C, L.SEAT_TOP + L.SEAT_BOTTOM_V[::-1], 0.12, mat="MAT_SEAT", tol=4),
        prim.plate_px(nm(P, "BODY_Seat_Hump"), C, L.HUMP_TOP + L.HUMP_BOTTOM_V[::-1], 0.10, mat="MAT_BODY_RED", tol=4),
        prim.plate_px(nm(P, "BODY_SeatPan"), C, pan_poly, 0.09, mat="MAT_BODY_BLACK", tol=4),
        prim.plate_px(nm(P, "BODY_Tail"), C, L.TAIL_TOP + L.TAIL_BOTTOM[::-1], 0.09, mat="MAT_BODY_BLACK", tol=4),
        prim.plate_px(nm(P, "BODY_SidePanel_R"), C, L.SIDEPANEL_POLY, 0.01, mat="MAT_BODY_BLACK", x0=-0.124, x1=-0.112, tol=4),
        prim.plate_px(nm(P, "BODY_SidePanel_L"), C, L.SIDEPANEL_POLY, 0.01, mat="MAT_BODY_BLACK", x0=0.112, x1=0.124, tol=4),
        prim.plate_px(nm(P, "BODY_TailTidy_Plate"), C, L.TAIL_TIDY_POLY, 0.07, mat="MAT_BODY_BLACK", tol=3),
    ]


# ============================================================================ BELLYPAN (NEW)
def bellypan(P):
    out = []
    C = P["coll"]
    bp = mesh.plate(nm(P, "BODY_BellyPan"), C, L.BELLYPAN_POLY, -0.11, 0.11, "MAT_BODY_RED")
    hard(bp, P, bevel=0.003)
    out.append(bp)

    chin_poly = [(715, 535), (708, 552), (660, 556), (590, 554), (530, 550), (540, 544), (650, 548), (705, 538)]
    chin = mesh.plate(nm(P, "BODY_BellyPan_Chin"), C, chin_poly, -0.10, 0.10, "MAT_BODY_BLACK")
    hard(chin, P, bevel=0.002)
    out.append(chin)

    for sg in (-1, 1):
        wp = [Vector(P3(680, 526, sg * 0.11)), Vector(P3(630, 530, sg * 0.14)),
              Vector(P3(570, 535, sg * 0.135)), Vector(P3(590, 538, sg * 0.11))]
        w = mesh.from_pydata(nm(P, f"BODY_BellyPan_Winglet_{'L' if sg > 0 else 'R'}"), C,
                             wp + [p + Vector((0, 0, 0.005)) for p in wp],
                             [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                             mat="MAT_BODY_BLACK")
        out.append(w)
    return out


def bellypan_prim(P):
    return [prim.plate_px(nm(P, "BODY_BellyPan"), P["coll"], L.BELLYPAN_POLY, 0.11, mat="MAT_BODY_RED", tol=3)]


# ============================================================================ COOLING (NEW)
def cooling(P):
    out = []
    C = P["coll"]
    core = mesh.plate(nm(P, "ENGINE_OilCooler"), C, L.OIL_COOLER_POLY, -0.10, 0.10, "MAT_METAL_DARK")
    hard(core, P, bevel=0.003)
    out.append(core)

    mesh_poly = [(743, 350), (767, 353), (756, 408), (732, 405)]
    mesh_screen = mesh.plate(nm(P, "ENGINE_OilCooler_Mesh"), C, mesh_poly, -0.095, 0.095, "MAT_METAL_RAW")
    out.append(mesh_screen)

    c_center = Vector(P3(752, 380, 0.0))
    for sg in (-1, 1):
        bp = c_center + Vector((sg * 0.105, 0, 0))
        brk = mesh.tube(nm(P, f"ENGINE_OilCooler_Bracket_{'L' if sg > 0 else 'R'}"), C,
                        [bp, bp + Vector((0, 0.04, 0.02)), Vector(P3(776, 360, sg * 0.05))],
                        0.006, 6, "MAT_METAL_DARK", smooth_path=False)
        out.append(brk)

        l_start = c_center + Vector((sg * 0.07, 0.02, -0.05))
        l_mid = Vector(P3(715, 430, sg * 0.12))
        l_end = Vector(P3(660, 490, sg * 0.16))
        line = mesh.tube(nm(P, f"ENGINE_OilLine_{'L' if sg > 0 else 'R'}"), C,
                         [l_start, l_mid, l_end], 0.0065, 8, "MAT_RUBBER", smooth_path=False)
        out.append(line)
    return out


def cooling_prim(P):
    return [prim.plate_px(nm(P, "ENGINE_OilCooler"), P["coll"], L.OIL_COOLER_POLY, 0.10, mat="MAT_METAL_DARK", tol=3)]


# ============================================================================ ENGINE
def engine(P):
    out = []
    C = P["coll"]

    # crankcase block
    crank = mesh.plate(nm(P, "ENGINE_Crankcase"), C, L.CRANKCASE_POLY, -0.20, 0.20, "MAT_ENGINE")
    hard(crank, P, bevel=0.012)
    out.append(crank)

    # transmission
    trans = mesh.plate(nm(P, "ENGINE_Transmission"), C, L.TRANSMISSION_POLY, -0.085, 0.085, "MAT_ENGINE")
    hard(trans, P, bevel=0.010)
    out.append(trans)

    # cylinder block & cylinder head
    (a_u, a_v), (b_u, b_v), (c_u, c_v), (d_u, d_v) = L.CYL_POLY
    t = 0.58
    r_mid = (a_u + (d_u - a_u) * t, a_v + (d_v - a_v) * t)
    f_mid = (b_u + (c_u - b_u) * t, b_v + (c_v - b_v) * t)
    ins = 9.0 if P["stage"] >= 3 else 0.0
    blk_poly = [(a_u + ins, a_v), (b_u - ins, b_v), (f_mid[0] - ins, f_mid[1]), (r_mid[0] + ins, r_mid[1])]
    blk = mesh.plate(nm(P, "ENGINE_Block"), C, blk_poly, -0.19 if ins else -0.20, 0.19 if ins else 0.20, "MAT_ENGINE")
    hard(blk, P, bevel=0.006)
    out.append(blk)

    hd_poly = [(r_mid[0] + ins * 0.6, r_mid[1]), (f_mid[0] - ins * 0.6, f_mid[1]), (c_u, c_v), (d_u, d_v)]
    hd = mesh.plate(nm(P, "ENGINE_Head"), C, hd_poly, -0.20 if ins else -0.205, 0.20 if ins else 0.205, "MAT_ENGINE")
    hard(hd, P, bevel=0.006)
    out.append(hd)

    # DOHC Cam Cover
    cam = mesh.plate(nm(P, "ENGINE_CamCover"), C, L.CAMCOVER_POLY, -0.185, 0.185, "MAT_ENGINE")
    hard(cam, P, bevel=0.008)
    out.append(cam)

    # engine side covers
    for s, sg in (("R", -1), ("L", 1)):
        c = Vector(P3(*L.ALT_COVER_PX))
        r = L.ALT_COVER_R / L.S
        cov_prof = [(0.001, sg * 0.03), (r * 0.86, sg * 0.03), (r * 0.97, sg * 0.022),
                    (r, sg * 0.012), (r, 0.0), (0.001, 0.0)]
        cov = mesh.lathe(nm(P, f"ENGINE_Cover_Main_{s}"), C, c + Vector((sg * 0.20, 0, 0)),
                         cov_prof, max(16, P["lathe"] // 2), "MAT_ENGINE", closed=True)
        out.append(cov)

        c2 = Vector(P3(*L.SMALL_COVER_PX))
        r2 = L.SMALL_COVER_R / L.S
        cov2 = mesh.lathe(nm(P, f"ENGINE_Cover_Small_{s}"), C, c2 + Vector((sg * 0.20, 0, 0)),
                          [(0.001, sg * 0.022), (r2 * 0.85, sg * 0.022), (r2, sg * 0.01), (r2, 0.0), (0.001, 0.0)],
                          max(12, P["lathe"] // 3), "MAT_ENGINE", closed=True)
        out.append(cov2)

    # oil sump
    sump = mesh.box(nm(P, "ENGINE_Sump"), C, P3(600, 546), (0.26, 0.28, 0.04), "MAT_ENGINE")
    hard(sump, P, bevel=0.010)
    out.append(sump)

    # spark plug boots and ignition leads (S3)
    if P["stage"] >= 3:
        for i, x_plug in enumerate((-0.14, -0.05, 0.05, 0.14)):
            p_head = Vector(P3(680, 348, x_plug))
            p_boot = p_head + Vector((0, -0.01, 0.03))
            p_coil = Vector(P3(600, 310, x_plug * 0.5))
            out.append(mesh.cyl(nm(P, f"ENGINE_SparkPlug_{i + 1}"), C, p_head, p_boot, 0.008, 8, "MAT_BODY_BLACK"))
            out.append(mesh.tube(nm(P, f"ENGINE_IgnitionWire_{i + 1}"), C, [p_boot, p_boot + Vector((0, 0.02, 0.02)), p_coil],
                                 0.004, 6, "MAT_BODY_RED", smooth_path=False))

    # proud cooling fins
    if P["stage"] >= 3:
        out += engine_fins(P)
    return out


def engine_fins(P):
    (a_u, a_v), (b_u, b_v), (c_u, c_v), (d_u, d_v) = L.CYL_POLY
    bm = bmesh.new()
    n = 15
    for i in range(n):
        t = 0.05 + 0.85 * i / (n - 1)
        if 0.555 < t < 0.61:
            continue
        r0 = (a_u + (d_u - a_u) * t, a_v + (d_v - a_v) * t)
        f0 = (b_u + (c_u - b_u) * t, b_v + (c_v - b_v) * t)
        poly = [(r0[0], r0[1] + 1.0), (f0[0], f0[1] + 1.0), (f0[0], f0[1] - 1.0), (r0[0], r0[1] - 1.0)]
        a = [bm.verts.new(L.P3(u, v, -0.20)) for (u, v) in poly]
        b = [bm.verts.new(L.P3(u, v, 0.20)) for (u, v) in poly]
        bm.faces.new(a); bm.faces.new(list(reversed(b)))
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    ob = mesh.finish(nm(P, "ENGINE_Fins"), bm, P["coll"], "MAT_ENGINE", smooth=False)
    return [ob]


def engine_prim(P):
    C = P["coll"]
    return [
        prim.plate_px(nm(P, "ENGINE_Crankcase"), C, L.CRANKCASE_POLY, 0.20, mat="MAT_ENGINE", tol=4),
        prim.plate_px(nm(P, "ENGINE_Transmission"), C, L.TRANSMISSION_POLY, 0.085, mat="MAT_ENGINE", tol=4),
        prim.plate_px(nm(P, "ENGINE_Block"), C, L.CYL_POLY, 0.19, mat="MAT_ENGINE", tol=4),
        prim.plate_px(nm(P, "ENGINE_CamCover"), C, L.CAMCOVER_POLY, 0.185, mat="MAT_ENGINE", tol=4),
        mesh.box(nm(P, "ENGINE_Sump"), C, P3(600, 546), (0.26, 0.28, 0.04), "MAT_ENGINE"),
    ]


# ============================================================================ INTAKE (RACING CARBS)
def intake(P):
    out = []
    C = P["coll"]
    seg = max(10, P["tube"])
    u0, v0, u1, v1 = L.CARB_BOX
    v_mid = (v0 + v1) / 2

    for i, x in enumerate((-0.15, -0.05, 0.05, 0.15)):
        p_head = Vector(P3(625, v_mid, x * 0.85))
        p_carb_f = Vector(P3(595, v_mid, x))
        p_carb_r = Vector(P3(555, v_mid, x))

        carb = mesh.cyl(nm(P, f"INTAKE_Carb_{i + 1}"), C, p_carb_r, p_carb_f, 0.034, seg, "MAT_METAL_RAW")
        hard(carb, P, bevel=0.003)
        out.append(carb)

        boot = mesh.cyl(nm(P, f"INTAKE_ManifoldBoot_{i + 1}"), C, p_carb_f, p_head,
                        0.028, seg, "MAT_RUBBER", r1=0.030)
        out.append(boot)

        if P["stage"] >= 2:
            p_rear = p_carb_r + (p_carb_r - p_carb_f).normalized() * 0.038
            stack_prof = [(0.024, 0.0), (0.026, 0.015), (0.032, 0.030), (0.042, 0.042), (0.036, 0.042)]
            stack = mesh.lathe(nm(P, f"INTAKE_VelocityStack_{i + 1}"), C, p_carb_r, stack_prof,
                               max(12, P["lathe"] // 2), "MAT_METAL_RAW", axis="Y", closed=False)
            out.append(stack)

    if P["stage"] >= 3:
        p_l = Vector(P3(575, v_mid, -0.16))
        p_r = Vector(P3(575, v_mid, 0.16))
        rail = mesh.cyl(nm(P, "INTAKE_ThrottleShaft"), C, p_l, p_r, 0.005, 8, "MAT_METAL_RAW")
        out.append(rail)
    return out


def intake_prim(P):
    C = P["coll"]
    u0, v0, u1, v1 = L.CARB_BOX
    return [prim.box_px(nm(P, "INTAKE_Carbs"), C, (u0, v0, u1, v1), 0.16, mat="MAT_METAL_RAW")]


# ============================================================================ EXHAUST
def exhaust(P):
    out = []
    C = P["coll"]
    seg, smp = max(P["tube"], 10), P["tube_s"]
    xs = (-0.15, -0.05, 0.05, 0.15)

    # 4 headers sweeping from ports
    for i, x0 in enumerate(xs):
        pts = []
        n = len(L.HEADER_PATH)
        for k, (u, v) in enumerate(L.HEADER_PATH):
            t = k / float(n - 1)
            x = x0 * (1 - t) + (-0.08 + x0 * 0.18) * t
            pts.append(Vector(P3(u, v, x)))
        hdr = mesh.tube(nm(P, f"EXHAUST_Header_{i + 1:02d}"), C, pts, 0.019, seg, "MAT_METAL_RAW", samples=smp)
        out.append(hdr)

        flg = mesh.cyl(nm(P, f"EXHAUST_Flange_{i + 1:02d}"), C,
                       pts[0] + (pts[0] - pts[1]).normalized() * 0.010,
                       pts[0] - (pts[0] - pts[1]).normalized() * 0.012, 0.027, seg, "MAT_METAL_DARK")
        out.append(flg)

        if P["stage"] >= 3:
            p_spr = pts[0] + (pts[1] - pts[0]) * 0.12 + Vector((0, 0, 0.022))
            spr = mesh.cyl(nm(P, f"EXHAUST_Spring_{i + 1:02d}"), C, p_spr, p_spr - (pts[1] - pts[0]) * 0.08,
                           0.0035, 6, "MAT_METAL_RAW")
            out.append(spr)

            for p_mid in (pts[2], pts[4]):
                weld = mesh.cyl(nm(P, f"EXHAUST_PieWeld_{i + 1:02d}_{abs(int(p_mid.x * 100)):02d}"), C,
                                p_mid - Vector((0, 0.004, 0)), p_mid + Vector((0, 0.004, 0)),
                                0.0195, seg, "MAT_BODY_RED")
                out.append(weld)

    # 4-into-1 merged collector
    mid = [P3(u, v, x) for (u, v), x in zip(L.MIDPIPE_PATH, (-0.08, -0.12, -0.16, -0.17))]
    col = mesh.tube(nm(P, "EXHAUST_Collector"), C, mid, [0.034, 0.028, 0.025, 0.025], seg,
                    "MAT_METAL_RAW", samples=smp)
    out.append(col)

    # Upswept slash-cut race muffler (carbon sleeve, titanium slash endcap)
    mf, mr = Vector(P3(*L.MUFFLER_FRONT_PX, -0.17)), Vector(P3(*L.MUFFLER_REAR_PX, -0.17))
    d = (mr - mf).normalized()

    # inlet cone
    out.append(mesh.cyl(nm(P, "EXHAUST_Muffler_Inlet"), C, mf - d * 0.02, mf + d * 0.035, 0.026,
                        seg, "MAT_METAL_RAW", r1=L.MUFFLER_R))
    # carbon muffler sleeve
    muff = mesh.cyl(nm(P, "EXHAUST_Muffler"), C, mf + d * 0.035, mr - d * 0.03, L.MUFFLER_R, seg,
                    "MAT_BODY_BLACK")
    out.append(muff)

    # titanium slash-cut endcap
    slash_mr = mr + d * 0.025
    endcap = mesh.cyl(nm(P, "EXHAUST_Muffler_EndCap"), C, mr - d * 0.03, slash_mr, L.MUFFLER_R + 0.002,
                      seg, "MAT_METAL_RAW", r1=L.MUFFLER_R * 0.72)
    out.append(endcap)

    # honeycomb mesh screen inside outlet
    mesh_screen = mesh.cyl(nm(P, "EXHAUST_Muffler_Mesh"), C, slash_mr - d * 0.008, slash_mr,
                           L.MUFFLER_R * 0.68, seg, "MAT_METAL_DARK")
    out.append(mesh_screen)

    # retaining strap and hanger clamp
    if P["stage"] >= 2:
        for k, t in enumerate((0.35, 0.75)):
            p = mf + (mr - mf) * t
            clp = mesh.cyl(nm(P, f"EXHAUST_Clamp_{k}"), C, p - d * 0.008, p + d * 0.008,
                           L.MUFFLER_R + 0.003, seg, "MAT_METAL_RAW")
            out.append(clp)
    return out


def exhaust_prim(P):
    C = P["coll"]
    mf, mr = Vector(P3(*L.MUFFLER_FRONT_PX, -0.17)), Vector(P3(*L.MUFFLER_REAR_PX, -0.17))
    pts = [P3(u, v, -0.10) for u, v in L.HEADER_PATH]
    mid = [P3(u, v, -0.15) for u, v in L.MIDPIPE_PATH]
    return [
        mesh.tube(nm(P, "EXHAUST_Header"), C, pts, 0.022, 8, "MAT_METAL_RAW", smooth_path=False),
        mesh.tube(nm(P, "EXHAUST_Collector"), C, mid, 0.025, 8, "MAT_METAL_RAW", smooth_path=False),
        mesh.cyl(nm(P, "EXHAUST_Muffler"), C, mf, mr, L.MUFFLER_R, 8, "MAT_BODY_BLACK"),
    ]


# ============================================================================ FRONT SUSPENSION & COCKPIT
def front(P):
    out = []
    C = P["coll"]
    seg = max(P["tube"], 10)
    fork, st = steering()
    ax, up = fork["axle"], fork["up"]
    top = fork["len"]

    # Inverted (USD) forks with Kashima/Öhlins gold anodizing
    for s, sg in (("L", 1), ("R", -1)):
        x = Vector((sg * L.FORK_SPACING, 0, 0))
        out.append(mesh.cyl(nm(P, f"SUSP_Fork_Outer_{s}"), C, ax + x + up * (top + 0.02),
                            ax + x + up * (top - 0.43), 0.028, seg, "MAT_BODY_RED"))
        out.append(mesh.cyl(nm(P, f"SUSP_Fork_Inner_{s}"), C, ax + x + up * (top - 0.43),
                            ax + x + up * 0.06, 0.0235, seg, "MAT_METAL_RAW"))
        foot = mesh.cyl(nm(P, f"SUSP_Fork_Foot_{s}"), C, ax + x + up * 0.07, ax + x - up * 0.035,
                        0.030, seg, "MAT_METAL_DARK")
        hard(foot, P, bevel=0.003)
        out.append(foot)

        if P["stage"] >= 3:
            out.append(mesh.cyl(nm(P, f"SUSP_Fork_Seal_{s}"), C, ax + x + up * (top - 0.43),
                                ax + x + up * (top - 0.45), 0.030, seg, "MAT_RUBBER"))
            out.append(mesh.cyl(nm(P, f"SUSP_Fork_Cap_{s}"), C, ax + x + up * (top + 0.02),
                                ax + x + up * (top + 0.03), 0.025, 12, "MAT_METAL_RAW"))

    # CNC billet triple clamps
    for name, off, h in (("SUSP_TopClamp", top - 0.005, 0.022), ("SUSP_BottomClamp", top - 0.175, 0.040)):
        c = ax + up * off + fork["back"] * 0.012
        rot = Matrix.Rotation(-math.radians(L.RAKE_DEG), 3, "X")
        tc = mesh.box(nm(P, name), C, c, (2 * L.FORK_SPACING + 0.075, 0.075, h), "MAT_METAL_DARK", rot=rot)
        hard(tc, P, bevel=0.004)
        out.append(tc)

    out.append(mesh.cyl(nm(P, "SUSP_SteeringStem"), C, st["bottom"], st["top"], 0.020, seg, "MAT_METAL_DARK"))

    # NEW: Front carbon aerodynamic mudguard & billet struts
    fender = mesh.plate(nm(P, "BODY_FrontFender"), C, L.FRONT_FENDER_POLY, -0.065, 0.065, "MAT_BODY_BLACK")
    hard(fender, P, bevel=0.002)
    out.append(fender)

    rf = L.R_TYRE_F + 0.018
    for s, sg in (("L", 1), ("R", -1)):
        p_foot = ax + Vector((sg * L.FORK_SPACING, 0, 0)) + up * 0.04
        p_m1 = ax + Vector((sg * 0.07, 0, 0)) + Vector((0, -math.sin(math.radians(20)) * rf, math.cos(math.radians(20)) * rf))
        p_m2 = ax + Vector((sg * 0.07, 0, 0)) + Vector((0, -math.sin(math.radians(-25)) * rf, math.cos(math.radians(-25)) * rf))
        strut = mesh.tube(nm(P, f"BODY_FrontFender_Strut_{s}"), C, [p_m1, p_foot, p_m2],
                          0.0055, 6, "MAT_METAL_RAW", smooth_path=False)
        out.append(strut)

    # Next-Gen Cyber Headlight with DRL Halo Ring & Flyscreen
    hc = Vector(P3(*L.HEADLIGHT_PX))
    fy = Vector(P3(815, L.HEADLIGHT_PX[1])).y
    R = L.HEADLIGHT_R
    prof = [(0.001, hc.y + 0.05), (R * 0.55, hc.y + 0.045), (R * 0.9, hc.y + 0.02), (R, hc.y - 0.01),
            (R + 0.004, fy + 0.012), (R + 0.004, fy), (R * 0.88, fy - 0.001), (0.001, fy - 0.004)]
    prof = [(r, y - hc.y) for (r, y) in prof]
    hl_body = mesh.lathe(nm(P, "CTRL_Headlight_Housing"), C, hc, prof,
                         max(16, P["lathe"] // 2), "MAT_BODY_BLACK", axis="Y", closed=True)
    out.append(hl_body)

    lens = mesh.lathe(nm(P, "CTRL_Headlight_Lens"), C, Vector((0, fy - 0.001, hc.z)),
                      [(0.001, -0.012), (R * 0.86, -0.004), (R * 0.87, 0.002), (0.001, 0.002)],
                      max(16, P["lathe"] // 2), "MAT_GLASS", axis="Y", closed=True)
    out.append(lens)

    drl = mesh.lathe(nm(P, "CTRL_Headlight_DRL"), C, Vector((0, fy + 0.002, hc.z)),
                     [(R * 0.80, -0.003), (R * 0.88, -0.003), (R * 0.88, 0.003), (R * 0.80, 0.003)],
                     24, "MAT_BODY_RED", axis="Y", closed=True)
    out.append(drl)

    if P["stage"] >= 3:
        for py_off, pz_off in ((-0.01, 0.025), (0.01, -0.02)):
            proj = mesh.lathe(nm(P, f"CTRL_Headlight_Projector_{'Upper' if pz_off > 0 else 'Lower'}"), C,
                              Vector((0, fy + 0.025, hc.z + pz_off)),
                              [(0.001, -0.006), (0.028, -0.003), (0.030, 0.006), (0.001, 0.006)],
                              16, "MAT_METAL_RAW", axis="Y", closed=True)
            out.append(proj)

    for s, sg in (("L", 1), ("R", -1)):
        p0 = hc + Vector((sg * (R + 0.002), 0.0, 0.0))
        p1 = ax + Vector((sg * L.FORK_SPACING, 0, 0)) + up * (top - 0.13)
        brk = mesh.tube(nm(P, f"CTRL_Headlight_Bracket_{s}"), C,
                        [p0, p0 + Vector((sg * 0.012, 0.015, 0)), p1], 0.007, 8, "MAT_METAL_DARK", smooth_path=False)
        out.append(brk)

    fs = mesh.plate(nm(P, "CTRL_Headlight_Flyscreen"), C, L.FLYSCREEN_POLY, -0.08, 0.08, "MAT_BODY_BLACK")
    hard(fs, P, bevel=0.003)
    out.append(fs)
    return out


def front_prim(P):
    C = P["coll"]
    fork, _ = steering()
    ax, up = fork["axle"], fork["up"]
    top = fork["len"]
    rot = Matrix.Rotation(-math.radians(L.RAKE_DEG), 3, "X")
    return [
        mesh.cyl(nm(P, "SUSP_Fork_Outer_L"), C, ax + Vector((L.FORK_SPACING, 0, 0)) + up * top,
                 ax + Vector((L.FORK_SPACING, 0, 0)), 0.028, 8, "MAT_BODY_RED"),
        mesh.cyl(nm(P, "SUSP_Fork_Outer_R"), C, ax + Vector((-L.FORK_SPACING, 0, 0)) + up * top,
                 ax + Vector((-L.FORK_SPACING, 0, 0)), 0.028, 8, "MAT_BODY_RED"),
        mesh.box(nm(P, "SUSP_TopClamp"), C, ax + up * (top - 0.005), (0.28, 0.075, 0.022), "MAT_METAL_DARK", rot=rot),
        mesh.box(nm(P, "SUSP_BottomClamp"), C, ax + up * (top - 0.175), (0.28, 0.075, 0.040), "MAT_METAL_DARK", rot=rot),
        prim.wheel_px(nm(P, "CTRL_Headlight_Housing"), C, L.HEADLIGHT_PX, L.HEADLIGHT_R * L.S, 0.05, segs=12, mat="MAT_BODY_BLACK"),
        prim.plate_px(nm(P, "BODY_FrontFender"), C, L.FRONT_FENDER_POLY, 0.065, mat="MAT_BODY_BLACK", tol=4),
        prim.plate_px(nm(P, "CTRL_Headlight_Flyscreen"), C, L.FLYSCREEN_POLY, 0.08, mat="MAT_BODY_BLACK", tol=3),
    ]


# ============================================================================ CONTROLS & COCKPIT
def controls(P):
    out = []
    C = P["coll"]
    seg = max(P["tube"], 10)
    fork, st = steering()
    ax, up = fork["axle"], fork["up"]
    top = fork["len"]
    ge = Vector(P3(*L.GRIP_END_PX))

    # clip-on handlebars, levers, master cylinders
    for s, sg in (("L", 1), ("R", -1)):
        clamp = ax + Vector((sg * L.FORK_SPACING, 0, 0)) + up * (top - 0.035)
        end = Vector((sg * 0.335, ge.y, ge.z))
        mid = clamp + (end - clamp) * 0.35

        out.append(mesh.cyl(nm(P, f"CTRL_ClipOn_{s}"), C, clamp, mid, 0.032, seg, "MAT_METAL_DARK"))
        out.append(mesh.cyl(nm(P, f"CTRL_Handlebar_{s}"), C, clamp, end, 0.011, seg, "MAT_METAL_DARK"))

        g0 = clamp + (end - clamp) * 0.52
        grip = mesh.cyl(nm(P, f"CTRL_Grip_{s}"), C, g0, end + (end - clamp).normalized() * 0.012,
                        0.017, seg, "MAT_RUBBER")
        out.append(grip)

        barend = mesh.cyl(nm(P, f"CTRL_BarEnd_{s}"), C, end + (end - clamp).normalized() * 0.012,
                          end + (end - clamp).normalized() * 0.035, 0.016, seg, "MAT_METAL_RAW")
        out.append(barend)

        # CNC Billet Reverse Bar-End Mirrors
        stem_p0 = end + (end - clamp).normalized() * 0.035
        stem_p1 = stem_p0 + Vector((sg * 0.045, -0.02, 0.045))
        m_stem = mesh.tube(nm(P, f"CTRL_BarEnd_Mirror_Stem_{s}"), C, [stem_p0, stem_p1],
                           0.006, 6, "MAT_METAL_RAW", smooth_path=False)
        m_head = mesh.lathe(nm(P, f"CTRL_BarEnd_Mirror_Head_{s}"), C, stem_p1,
                            [(0.001, -0.008), (0.036, -0.006), (0.038, 0.002), (0.001, 0.002)],
                            16, "MAT_BODY_BLACK", axis="X", closed=True)
        m_glass = mesh.cyl(nm(P, f"CTRL_BarEnd_Mirror_Glass_{s}"), C,
                           stem_p1 - Vector((sg * 0.003, 0, 0)), stem_p1 + Vector((sg * 0.002, 0, 0)),
                           0.035, 16, "MAT_GLASS")
        out += [m_stem, m_head, m_glass]

        # switch housing & racing lever
        ch = clamp + (end - clamp) * 0.46
        sh = mesh.box(nm(P, f"CTRL_SwitchHousing_{s}"), C, ch, (0.040, 0.045, 0.045), "MAT_BODY_BLACK")
        hard(sh, P, bevel=0.003)
        out.append(sh)

        lev0 = ch + Vector((0, -0.030, 0.0))
        lev1 = end + Vector((0, -0.060, -0.010))
        out.append(mesh.tube(nm(P, f"CTRL_Lever_{s}"), C, [lev0, lev1], 0.006, 6, "MAT_METAL_RAW", smooth_path=False))

        rp = L.RESERVOIR_L_PX if sg > 0 else L.RESERVOIR_R_PX
        rc = Vector(P3(rp[0], rp[1] + 8, 0.0))
        rc.x = ch.x - sg * 0.01
        res = mesh.cyl(nm(P, f"CTRL_Reservoir_{s}"), C, rc - Vector((0, 0, 0.016)),
                       rc + Vector((0, 0, 0.018)), 0.020, seg, "MAT_GLASS")
        out.append(res)
        out.append(mesh.tube(nm(P, f"CTRL_ReservoirStem_{s}"), C,
                             [rc - Vector((0, 0, 0.016)), ch + Vector((0, 0, 0.020))],
                             0.006, 6, "MAT_METAL_DARK", smooth_path=False))

    # TFT Digital Widescreen Dashboard
    c_dash = ax + up * (top + 0.045) + fork["back"] * 0.03
    rot_dash = Matrix.Rotation(math.radians(-35), 3, "X")
    dash = mesh.box(nm(P, "CTRL_TFT_Dashboard"), C, c_dash, (0.135, 0.075, 0.024), "MAT_METAL_DARK", rot=rot_dash)
    hard(dash, P, bevel=0.003)
    out.append(dash)

    screen = mesh.box(nm(P, "CTRL_TFT_Screen"), C, c_dash + Vector((0, -0.005, 0.008)),
                      (0.120, 0.062, 0.004), "MAT_BODY_BLACK", rot=rot_dash)
    out.append(screen)

    # Transverse Hydraulic Steering Damper
    d_center = ax + up * (top - 0.035) + Vector((0.02, 0.02, 0))
    d_body = mesh.cyl(nm(P, "CTRL_SteeringDamper_Body"), C,
                      d_center - Vector((0.07, 0, 0)), d_center + Vector((0.03, 0, 0)),
                      0.014, 12, "MAT_BODY_RED")
    d_rod = mesh.cyl(nm(P, "CTRL_SteeringDamper_Rod"), C,
                     d_center - Vector((0.11, 0, 0)), d_center + Vector((0.09, 0, 0)),
                     0.006, 8, "MAT_METAL_RAW")
    out.append(d_body); out.append(d_rod)

    # CNC rearset footpegs & pedals
    for s, sg in (("L", 1), ("R", -1)):
        plate = mesh.plate(nm(P, f"CTRL_Rearset_Plate_{s}"), C, L.REARSET_PLATE_POLY,
                           sg * 0.165, sg * 0.175, "MAT_METAL_DARK")
        hard(plate, P, bevel=0.002)
        out.append(plate)

        fp = Vector(P3(*L.FOOTPEG_PX))
        peg = mesh.cyl(nm(P, f"CTRL_Footpeg_{s}"), C, Vector((sg * 0.175, fp.y, fp.z)),
                       Vector((sg * 0.250, fp.y, fp.z)), 0.011, seg, "MAT_METAL_RAW")
        out.append(peg)

        lever_end = Vector(P3(480, 432, sg * 0.18))
        pedal = mesh.tube(nm(P, "CTRL_BrakePedal" if sg < 0 else "CTRL_Shifter"), C,
                          [Vector((sg * 0.18, fp.y, fp.z + 0.02)), lever_end, lever_end + Vector((sg * 0.03, 0, 0))],
                          0.006, 6, "MAT_METAL_RAW", smooth_path=False)
        out.append(pedal)
    return out


def controls_prim(P):
    C = P["coll"]
    rc = Vector(P3(L.RESERVOIR_R_PX[0], L.RESERVOIR_R_PX[1] + 8, -0.22))
    return [
        prim.cyl_px(nm(P, "CTRL_Handlebar_L"), C, L.GRIP_INNER_PX, L.GRIP_END_PX, 0.012, segs=6, mat="MAT_METAL_DARK", x=0.365),
        prim.cyl_px(nm(P, "CTRL_Handlebar_R"), C, L.GRIP_INNER_PX, L.GRIP_END_PX, 0.012, segs=6, mat="MAT_METAL_DARK", x=-0.365),
        prim.wheel_px(nm(P, "CTRL_BarEnd_Mirror_Head_L"), C, L.BAR_END_MIRROR_POLY[0], 0.038 * L.S, 0.01, segs=8, mat="MAT_BODY_BLACK", x=0.418),
        prim.wheel_px(nm(P, "CTRL_BarEnd_Mirror_Head_R"), C, L.BAR_END_MIRROR_POLY[0], 0.038 * L.S, 0.01, segs=8, mat="MAT_BODY_BLACK", x=-0.418),
        mesh.cyl(nm(P, "CTRL_Reservoir_R"), C, rc - Vector((0, 0, 0.016)), rc + Vector((0, 0, 0.018)), 0.020, 8, "MAT_GLASS"),
        prim.box_px(nm(P, "CTRL_TFT_Dashboard"), C, L.TFT_DASH_POLY, 0.07, mat="MAT_METAL_DARK"),
    ]


# ============================================================================ S3 DETAILS (FASTENERS & LINES)
def details(P):
    if not P.get("detail"):
        return []

    C = P["coll"]
    fs = Fasteners(C)
    fork, _ = steering()

    # engine cover bolt rings
    for sg in (-1, 1):
        c = Vector(P3(*L.ALT_COVER_PX))
        r = L.ALT_COVER_R / L.S
        fs.ring("BOLT_M6", c + Vector((sg * 0.230, 0, 0)), (sg, 0, 0), r * 0.78, 10, phase=0.2)

        c2 = Vector(P3(*L.SMALL_COVER_PX))
        r2 = L.SMALL_COVER_R / L.S
        fs.ring("BOLT_M6", c2 + Vector((sg * 0.222, 0, 0)), (sg, 0, 0), r2 * 0.72, 6)

    # axle nuts and swingarm pivot washers
    for sg in (-1, 1):
        fs.place("NUT", Vector(L.FRONT_AXLE) + Vector((sg * 0.13, 0, 0)), (sg, 0, 0))
        fs.place("NUT", Vector(L.REAR_AXLE) + Vector((sg * 0.17, 0, 0)), (sg, 0, 0))
        fs.place("WASHER", Vector(P3(*L.SWINGARM_PIVOT_PX)) + Vector((sg * 0.175, 0, 0)), (sg, 0, 0))

    # triple clamp pinch bolts
    for sg in (-1, 1):
        for off in (fork["len"] - 0.005, fork["len"] - 0.175):
            p = fork["axle"] + fork["up"] * off + Vector((sg * (L.FORK_SPACING + 0.04), 0, 0)) + fork["back"] * 0.03
            fs.place("BOLT_M8", p, (sg, 0, 0))

    # radial caliper mounting bolts
    for sg in (-1, 1):
        cp = Vector(P3(803, 468))
        for dz in (-0.035, 0.035):
            d = Matrix.Rotation(math.radians(35), 3, "X") @ Vector((0, 0, dz))
            fs.place("BOLT_M10", cp + d + Vector((sg * 0.108, 0, 0)), (sg, 0, 0))

    # braided stainless steel front brake lines
    up = fork["up"]
    mc = Vector(P3(L.RESERVOIR_R_PX[0], L.RESERVOIR_R_PX[1] + 30, -0.19))
    cal = Vector(P3(803, 440, -0.095))
    b_line = mesh.tube(nm(P, "CTRL_BrakeLine_Front_R"), C,
                       [mc, mc + Vector((0.05, 0.05, -0.06)),
                        fork["axle"] + up * 0.45 + Vector((-0.14, -0.02, 0)),
                        fork["axle"] + up * 0.20 + Vector((-0.13, -0.035, 0)), cal],
                       0.0045, 8, "MAT_RUBBER", samples=8)
    return [b_line]


# ============================================================================ REGISTRY
PARTS = [
    Part("wheels", wheels, prim=wheels_prim, collision="hull"),
    Part("brakes", brakes, prim=brakes_prim, collision="hull"),
    Part("frame", frame, prim=frame_prim, collision="hull"),
    Part("swingarm", swingarm, prim=swingarm_prim, collision="hull"),
    Part("rear_susp", rear_susp, prim=rear_susp_prim, collision="hull"),
    Part("drive", drive, prim=drive_prim, collision="hull"),
    Part("tank", tank, prim=tank_prim, collision="hull"),
    Part("seat", seat, prim=seat_prim, collision="hull"),
    Part("bellypan", bellypan, prim=bellypan_prim, collision="hull"),
    Part("cooling", cooling, prim=cooling_prim, collision="hull"),
    Part("engine", engine, prim=engine_prim, collision="hull"),
    Part("intake", intake, prim=intake_prim, collision="hull"),
    Part("exhaust", exhaust, prim=exhaust_prim, collision="hull"),
    Part("front", front, prim=front_prim, collision="hull"),
    Part("controls", controls, prim=controls_prim, collision="none"),
    Part("details", details, collision="none"),
]

# Moving / articulated parts hierarchy
PIVOTS = {
    "WHEEL_Front_Tire": lambda: L.FRONT_AXLE,
    "WHEEL_Rear_Tire": lambda: L.REAR_AXLE,
    "FRAME_Swingarm_R": lambda: L.P3(*L.SWINGARM_PIVOT_PX),
    "SUSP_TopClamp": lambda: steering()[1]["bottom"],
}

CHILDREN = {
    "WHEEL_Front_Rim": "WHEEL_Front_Tire",
    "WHEEL_Front_Hub": "WHEEL_Front_Tire",
    "BRAKE_Front_Disc_L": "WHEEL_Front_Tire",
    "BRAKE_Front_Disc_R": "WHEEL_Front_Tire",
    "WHEEL_Rear_Rim": "WHEEL_Rear_Tire",
    "WHEEL_Rear_Hub": "WHEEL_Rear_Tire",
    "BRAKE_Rear_Disc": "WHEEL_Rear_Tire",
    "DRIVE_Sprocket_Rear": "WHEEL_Rear_Tire",
    "WHEEL_Rear_AeroDisc_L": "WHEEL_Rear_Tire",
    "WHEEL_Rear_AeroDisc_R": "WHEEL_Rear_Tire",
    "WHEEL_Rear_AeroCap_L": "WHEEL_Rear_Tire",
    "WHEEL_Rear_AeroCap_R": "WHEEL_Rear_Tire",
    "FRAME_Swingarm_L": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Brace": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Cantilever_L": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Cantilever_R": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Cantilever": "FRAME_Swingarm_R",
    "FRAME_Swingarm_ChainAdjuster_L": "FRAME_Swingarm_R",
    "FRAME_Swingarm_ChainAdjuster_R": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Spool_L": "FRAME_Swingarm_R",
    "FRAME_Swingarm_Spool_R": "FRAME_Swingarm_R",
    "FRAME_RearHugger": "FRAME_Swingarm_R",
    "FRAME_ChainGuard": "FRAME_Swingarm_R",
    "SUSP_BottomClamp": "SUSP_TopClamp",
    "SUSP_SteeringStem": "SUSP_TopClamp",
    "SUSP_Fork_Outer_L": "SUSP_TopClamp",
    "SUSP_Fork_Outer_R": "SUSP_TopClamp",
    "SUSP_Fork_Inner_L": "SUSP_TopClamp",
    "SUSP_Fork_Inner_R": "SUSP_TopClamp",
    "SUSP_Fork_Foot_L": "SUSP_TopClamp",
    "SUSP_Fork_Foot_R": "SUSP_TopClamp",
    "BODY_FrontFender": "SUSP_TopClamp",
    "BODY_FrontFender_Strut_L": "SUSP_TopClamp",
    "BODY_FrontFender_Strut_R": "SUSP_TopClamp",
    "CTRL_Headlight_Housing": "SUSP_TopClamp",
    "CTRL_Headlight_Lens": "SUSP_TopClamp",
    "CTRL_Headlight_DRL": "SUSP_TopClamp",
    "CTRL_Headlight_Flyscreen": "SUSP_TopClamp",
    "CTRL_TFT_Dashboard": "SUSP_TopClamp",
    "CTRL_TFT_Screen": "SUSP_TopClamp",
    "CTRL_SteeringDamper_Body": "SUSP_TopClamp",
    "CTRL_SteeringDamper_Rod": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Stem_L": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Stem_R": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Head_L": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Head_R": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Glass_L": "SUSP_TopClamp",
    "CTRL_BarEnd_Mirror_Glass_R": "SUSP_TopClamp",
    "CTRL_ClipOn_L": "SUSP_TopClamp",
    "CTRL_ClipOn_R": "SUSP_TopClamp",
    "CTRL_Handlebar_L": "SUSP_TopClamp",
    "CTRL_Handlebar_R": "SUSP_TopClamp",
    "CTRL_Grip_L": "SUSP_TopClamp",
    "CTRL_Grip_R": "SUSP_TopClamp",
    "CTRL_BarEnd_L": "SUSP_TopClamp",
    "CTRL_BarEnd_R": "SUSP_TopClamp",
    "CTRL_SwitchHousing_L": "SUSP_TopClamp",
    "CTRL_SwitchHousing_R": "SUSP_TopClamp",
    "CTRL_Lever_L": "SUSP_TopClamp",
    "CTRL_Lever_R": "SUSP_TopClamp",
    "CTRL_Reservoir_L": "SUSP_TopClamp",
    "CTRL_Reservoir_R": "SUSP_TopClamp",
    "CTRL_ReservoirStem_L": "SUSP_TopClamp",
    "CTRL_ReservoirStem_R": "SUSP_TopClamp",
}
