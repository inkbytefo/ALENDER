"""
Part builders for VEH_FF12_RacingCar.

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

PALETTE = {
    "MAT_BODY_RED":      ((0.78, 0.045, 0.035), 0.15, 0.22),  # Glossy Rosso Corsa
    "MAT_CARBON":        ((0.025, 0.025, 0.025), 0.35, 0.38),  # Woven carbon fiber
    "MAT_RUBBER":        ((0.035, 0.035, 0.035), 0.0, 0.78),   # Yokohama semi-slick rubber
    "MAT_METAL_CHROME":  ((0.92, 0.92, 0.94), 1.0, 0.08),     # Polished alloy & chrome
    "MAT_METAL_DARK":    ((0.07, 0.07, 0.075), 0.95, 0.35),   # Anodized chassis & calipers
    "MAT_EXHAUST":       ((0.52, 0.46, 0.38), 0.85, 0.32),    # Heat-stained bronze stainless
    "MAT_LEATHER_BROWN": ((0.30, 0.15, 0.07), 0.0, 0.58),     # Cognac vintage saddle leather
    "MAT_GLASS":         dict(rgb=(0.92, 0.94, 0.96), metallic=0.0, roughness=0.04, alpha=0.22),
}

# Critical intersection pairs that must NEVER intersect (checked in Stage 1 & 2 gates)
CRITICAL_PAIRS = [
    ("WHEEL_Tire_", "BODY_"),
    ("WHEEL_Tire_", "SUSP_"),
    ("WHEEL_Tire_", "EXHAUST_"),
    ("EXHAUST_", "WHEEL_"),
    ("EXHAUST_Pipe", "COCKPIT_Seat"),
    ("COCKPIT_Steering_", "COCKPIT_Seat"),
]

LOW = dict(
    name="LOW",
    tube_seg=8,
    lathe_seg=24,
    loft_res=16,
    subsurf=0,
    bevel=False,
    C_PRIMARY="02_LOW_PRIMARY",
    C_SECONDARY="03_LOW_SECONDARY",
    C_MECH="04_LOW_MECHANICAL",
    C_DETAIL="04_LOW_MECHANICAL"
)

HIGH = dict(
    name="HIGH",
    tube_seg=16,
    lathe_seg=64,
    loft_res=32,
    subsurf=1,
    bevel=True,
    C_PRIMARY="05_HIGH_BODY",
    C_SECONDARY="05_HIGH_BODY",
    C_MECH="06_HIGH_MECHANICAL",
    C_DETAIL="07_DETAILS"
)


def nm(lod, name):
    return name if lod["name"] == "HIGH" else name + "_LOW"


def smooth(ob, lod, levels=None, bevel_w=None):
    lv = 0 if levels is None else min(levels, lod["subsurf"])
    if lv:
        mods.subsurf(ob, 1, lv)
    if lod["bevel"] and bevel_w:
        mods.bevel(ob, bevel_w, 2)
        mods.weighted_normal(ob)
    return ob


def guide_points():
    return {
        "FRONT_AXLE_L": L.AXLE_FL,
        "FRONT_AXLE_R": L.AXLE_FR,
        "REAR_AXLE_L":  L.AXLE_RL,
        "REAR_AXLE_R":  L.AXLE_RR,
        "NOSE_TIP":     (0.0, -1.90, 0.28),
        "COCKPIT_CTR":  (0.0, 0.30, 0.40),
        "STEERING_CTR": L.STEERING_CENTER,
        "SEAT_CTR":     L.SEAT_CENTER,
        "TAIL_TIP":     (0.0, 1.90, 0.40),
    }


# ============================================================================ WHEELS & TYRES
def tyre_profile(R, W, R_rim, lod):
    """Closed profile (radius, axial_offset) for revolving a wide racing tyre."""
    half_w = W / 2.0
    rim_w = half_w * 0.88
    shoulder_r = R - 0.03
    if lod["name"] == "LOW":
        return [
            (R_rim, -rim_w),
            (shoulder_r, -half_w),
            (R, -half_w * 0.70),
            (R, +half_w * 0.70),
            (shoulder_r, +half_w),
            (R_rim, +rim_w),
            (R_rim - 0.04, 0.0),
        ]
    else:
        # High detail curved crown, rounded shoulders, beaded rim lip
        return [
            (R_rim, -rim_w),
            (R_rim + 0.03, -half_w * 0.96),
            (R_rim + 0.07, -half_w),
            (shoulder_r, -half_w),
            (R - 0.012, -half_w * 0.85),
            (R, -half_w * 0.50),
            (R + 0.002, 0.0),
            (R, +half_w * 0.50),
            (R - 0.012, +half_w * 0.85),
            (shoulder_r, +half_w),
            (R_rim + 0.07, +half_w),
            (R_rim + 0.03, +half_w * 0.96),
            (R_rim, +rim_w),
            (R_rim - 0.02, +rim_w * 0.7),
            (R_rim - 0.04, 0.0),
            (R_rim - 0.02, -rim_w * 0.7),
        ]


def rim_profile(R_rim, W_rim, lod):
    """Drop-center wire wheel rim profile."""
    hw = W_rim / 2.0
    if lod["name"] == "LOW":
        return [
            (R_rim, -hw),
            (R_rim + 0.015, -hw),
            (R_rim - 0.04, -hw * 0.6),
            (R_rim - 0.05, 0.0),
            (R_rim - 0.04, +hw * 0.6),
            (R_rim + 0.015, +hw),
            (R_rim, +hw),
        ]
    else:
        return [
            (R_rim, -hw),
            (R_rim + 0.018, -hw),
            (R_rim + 0.018, -hw + 0.015),
            (R_rim - 0.025, -hw * 0.7),
            (R_rim - 0.055, -hw * 0.3),
            (R_rim - 0.055, +hw * 0.3),
            (R_rim - 0.025, +hw * 0.7),
            (R_rim + 0.018, +hw - 0.015),
            (R_rim + 0.018, +hw),
            (R_rim, +hw),
        ]


def build_wheel(name_tag, center, is_left, lod):
    """Builds one wheel assembly: tyre, rim, hub, wire spokes, knockoff, brake disc & caliper."""
    c = Vector(center)
    sgn = 1.0 if is_left else -1.0
    col_tire = lod["C_PRIMARY"]
    col_mech = lod["C_MECH"]
    seg = lod["lathe_seg"]

    # 1. Tyre
    prof_t = tyre_profile(L.R_TYRE, L.W_TYRE, L.R_RIM, lod)
    t = mesh.lathe(nm(lod, f"WHEEL_Tire_{name_tag}"), col_tire, c, prof_t,
                   segs=seg, mat="MAT_RUBBER", axis="X")
    if lod["name"] == "HIGH":
        mods.finish_hard(t, 0.002)

    # 2. Rim
    prof_r = rim_profile(L.R_RIM, L.W_RIM, lod)
    r = mesh.lathe(nm(lod, f"WHEEL_Rim_{name_tag}"), col_mech, c, prof_r,
                   segs=seg, mat="MAT_CARBON", closed=False, axis="X")
    if lod["name"] == "HIGH":
        mods.finish_hard(r, 0.002)

    # 3. Brake Rotor Disc (inboard side of wheel)
    disc_x = c.x - sgn * 0.09
    disc_center = Vector((disc_x, c.y, c.z))
    prof_d = [(0.06, -0.006), (0.165, -0.006), (0.165, 0.006), (0.06, 0.006)]
    mesh.lathe(nm(lod, f"WHEEL_BrakeDisc_{name_tag}"), col_mech, disc_center, prof_d,
               segs=max(16, seg // 2), mat="MAT_METAL_DARK", axis="X")

    # 4. Brake Caliper (mounted on upright over rotor)
    if lod["name"] == "HIGH":
        caliper_ctr = Vector((disc_x, c.y + 0.04, c.z + 0.12))
        cal = mesh.box(nm(lod, f"WHEEL_BrakeCaliper_{name_tag}"), col_mech, caliper_ctr,
                       (0.052, 0.095, 0.058), mat="MAT_BODY_RED")
        mods.finish_hard(cal, 0.003)

    # 5. Center Hub
    hub_out_x = c.x + sgn * 0.14
    hub_ctr = Vector((hub_out_x, c.y, c.z))
    prof_hub = [(0.001, 0.0), (0.048, 0.0), (0.048, sgn * 0.03), (0.026, sgn * 0.05), (0.001, sgn * 0.05)]
    mesh.lathe(nm(lod, f"WHEEL_Hub_{name_tag}"), col_mech, hub_ctr, prof_hub,
               segs=max(16, seg // 2), mat="MAT_METAL_CHROME", closed=False, axis="X")

    # 6. Classic Wire Spokes (36 criss-cross spokes per wheel)
    if lod["name"] == "HIGH":
        r_hub = 0.044
        r_rim = 0.222
        spoke_specs = []
        num_spokes = 36
        for i in range(num_spokes):
            ang_h = 2 * math.pi * i / num_spokes
            ang_r = 2 * math.pi * (i + 4) / num_spokes
            is_out = (i % 2 == 0)
            x_h = c.x + sgn * (0.06 if is_out else -0.04)
            x_r = c.x + sgn * (0.035 if is_out else -0.035)
            p0 = (x_h, c.y + r_hub * math.cos(ang_h), c.z + r_hub * math.sin(ang_h))
            p1 = (x_r, c.y + r_rim * math.cos(ang_r), c.z + r_rim * math.sin(ang_r))
            spoke_specs.append((p0, p1, 0.0022))
        mesh.multi_cyl(nm(lod, f"WHEEL_Spokes_{name_tag}"), lod["C_DETAIL"], spoke_specs,
                       segs=6, mat="MAT_METAL_CHROME")

    # 7. Knock-off 2-eared spinner
    ear_len = 0.068
    ear_tip1 = hub_ctr + Vector((sgn * 0.04, 0.0, ear_len))
    ear_tip2 = hub_ctr + Vector((sgn * 0.04, 0.0, -ear_len))
    mesh.tube(nm(lod, f"WHEEL_Knockoff_{name_tag}"), col_mech, [ear_tip1, hub_ctr, ear_tip2],
              0.010, max(6, lod["tube_seg"]), mat="MAT_METAL_CHROME")


def wheels(lod):
    build_wheel("FL", L.AXLE_FL, is_left=True, lod=lod)
    build_wheel("FR", L.AXLE_FR, is_left=False, lod=lod)
    build_wheel("RL", L.AXLE_RL, is_left=True, lod=lod)
    build_wheel("RR", L.AXLE_RR, is_left=False, lod=lod)


# ============================================================================ SUSPENSION
def build_suspension_side(is_front, is_left, lod):
    """Builds double wishbones, upright hub, steering/halfshaft, and coilover."""
    col = lod["C_MECH"]
    t_seg = lod["tube_seg"]
    sgn = 1.0 if is_left else -1.0
    prefix = "F" if is_front else "R"
    side = "L" if is_left else "R"
    tag = f"{prefix}_{side}"

    if is_front:
        up1 = (sgn * L.SUSP_F_UPPER_CHASSIS_1[0], L.SUSP_F_UPPER_CHASSIS_1[1], L.SUSP_F_UPPER_CHASSIS_1[2])
        up2 = (sgn * L.SUSP_F_UPPER_CHASSIS_2[0], L.SUSP_F_UPPER_CHASSIS_2[1], L.SUSP_F_UPPER_CHASSIS_2[2])
        u_hub = (sgn * L.SUSP_F_UPPER_HUB[0], L.SUSP_F_UPPER_HUB[1], L.SUSP_F_UPPER_HUB[2])

        lo1 = (sgn * L.SUSP_F_LOWER_CHASSIS_1[0], L.SUSP_F_LOWER_CHASSIS_1[1], L.SUSP_F_LOWER_CHASSIS_1[2])
        lo2 = (sgn * L.SUSP_F_LOWER_CHASSIS_2[0], L.SUSP_F_LOWER_CHASSIS_2[1], L.SUSP_F_LOWER_CHASSIS_2[2])
        l_hub = (sgn * L.SUSP_F_LOWER_HUB[0], L.SUSP_F_LOWER_HUB[1], L.SUSP_F_LOWER_HUB[2])

        rod_in  = (sgn * L.SUSP_F_TIEROD_CHASSIS[0], L.SUSP_F_TIEROD_CHASSIS[1], L.SUSP_F_TIEROD_CHASSIS[2])
        rod_out = (sgn * L.SUSP_F_TIEROD_HUB[0], L.SUSP_F_TIEROD_HUB[1], L.SUSP_F_TIEROD_HUB[2])

        shk_top = (sgn * L.SUSP_F_COILOVER_TOP[0], L.SUSP_F_COILOVER_TOP[1], L.SUSP_F_COILOVER_TOP[2])
        shk_bot = (sgn * L.SUSP_F_COILOVER_BOT[0], L.SUSP_F_COILOVER_BOT[1], L.SUSP_F_COILOVER_BOT[2])
    else:
        up1 = (sgn * L.SUSP_R_UPPER_CHASSIS_1[0], L.SUSP_R_UPPER_CHASSIS_1[1], L.SUSP_R_UPPER_CHASSIS_1[2])
        up2 = (sgn * L.SUSP_R_UPPER_CHASSIS_2[0], L.SUSP_R_UPPER_CHASSIS_2[1], L.SUSP_R_UPPER_CHASSIS_2[2])
        u_hub = (sgn * L.SUSP_R_UPPER_HUB[0], L.SUSP_R_UPPER_HUB[1], L.SUSP_R_UPPER_HUB[2])

        lo1 = (sgn * L.SUSP_R_LOWER_CHASSIS_1[0], L.SUSP_R_LOWER_CHASSIS_1[1], L.SUSP_R_LOWER_CHASSIS_1[2])
        lo2 = (sgn * L.SUSP_R_LOWER_CHASSIS_2[0], L.SUSP_R_LOWER_CHASSIS_2[1], L.SUSP_R_LOWER_CHASSIS_2[2])
        l_hub = (sgn * L.SUSP_R_LOWER_HUB[0], L.SUSP_R_LOWER_HUB[1], L.SUSP_R_LOWER_HUB[2])

        rod_in  = (sgn * L.SUSP_R_HALFOUT_INNER[0], L.SUSP_R_HALFOUT_INNER[1], L.SUSP_R_HALFOUT_INNER[2])
        rod_out = (sgn * L.SUSP_R_HALFOUT_HUB[0], L.SUSP_R_HALFOUT_HUB[1], L.SUSP_R_HALFOUT_HUB[2])

        shk_top = (sgn * L.SUSP_R_COILOVER_TOP[0], L.SUSP_R_COILOVER_TOP[1], L.SUSP_R_COILOVER_TOP[2])
        shk_bot = (sgn * L.SUSP_R_COILOVER_BOT[0], L.SUSP_R_COILOVER_BOT[1], L.SUSP_R_COILOVER_BOT[2])

    # 1. Upper Wishbone A-arm (2 tubes meeting at outer ball joint)
    mesh.tube(nm(lod, f"SUSP_Wishbone_Upper_{tag}"), col, [up1, u_hub, up2],
              0.013, t_seg, mat="MAT_METAL_CHROME")

    # 2. Lower Wishbone A-arm
    mesh.tube(nm(lod, f"SUSP_Wishbone_Lower_{tag}"), col, [lo1, l_hub, lo2],
              0.015, t_seg, mat="MAT_METAL_CHROME")

    # 3. Upright Hub (connecting upper and lower ball joints to wheel axle)
    mesh.tube(nm(lod, f"SUSP_Upright_{tag}"), col, [u_hub, l_hub],
              0.022, t_seg, mat="MAT_METAL_DARK")

    # 4. Steering Tie-Rod (front) or Drive Half-Shaft (rear)
    rod_name = f"SUSP_TieRod_{tag}" if is_front else f"SUSP_HalfShaft_{tag}"
    rod_r = 0.012 if is_front else 0.018
    mesh.tube(nm(lod, rod_name), col, [rod_in, rod_out],
              rod_r, t_seg, mat="MAT_METAL_DARK")

    # 5. Coilover Damper (central damper body + coil spring)
    mesh.cyl(nm(lod, f"SUSP_Damper_{tag}"), col, shk_top, shk_bot,
             0.018, t_seg, mat="MAT_METAL_DARK")
    if lod["name"] == "HIGH":
        # Realistic coil spring around damper body
        spring_pts = mesh.helix(shk_top, shk_bot, 0.028, turns=6, steps_per_turn=12, start=0.15, end=0.85)
        mesh.tube(nm(lod, f"SUSP_Spring_{tag}"), col, spring_pts,
                  0.006, 8, mat="MAT_BODY_RED", smooth_path=False)


def suspension(lod):
    for f in (True, False):
        for s in (True, False):
            build_suspension_side(is_front=f, is_left=s, lod=lod)


# ============================================================================ BODYWORK
def make_torpedo_ring(y, z_bot, z_top, half_w, n, e_top=2.2, e_bot=3.2):
    """Generates an elliptical/superelliptical cross-section ring at longitudinal station Y."""
    z_mid = (z_top + z_bot) / 2.0
    h_top = z_top - z_mid
    h_bot = z_mid - z_bot
    ring = []
    for k in range(n):
        ang = 2.0 * math.pi * k / n
        ca, sa = math.cos(ang), math.sin(ang)
        x = half_w * math.copysign(abs(ca) ** (2.0 / (e_top if sa >= 0 else e_bot)), ca)
        if sa >= 0:
            z = z_mid + h_top * abs(sa) ** (2.0 / e_top)
        else:
            z = z_mid - h_bot * abs(sa) ** (2.0 / e_bot)
        ring.append((x, y, z))
    return ring


def body_shell(lod):
    col = lod["C_PRIMARY"]
    n_ring = lod["loft_res"]

    # 1. Main Cigar / Torpedo Fuselage Loft
    rings = []
    for (y, zb, zt, hw) in L.BODY_STATIONS:
        if y < -1.5:
            et, eb = 2.0, 2.2
        elif y < -0.2:
            et, eb = 2.4, 3.2
        elif y < 0.7:
            et, eb = 2.5, 3.5
        else:
            et, eb = 2.2, 2.6
        rings.append(make_torpedo_ring(y, zb, zt, hw, n_ring, et, eb))

    fuselage = mesh.loft_rings(nm(lod, "BODY_Fuselage"), col, rings, mat="MAT_BODY_RED", caps=True)
    if lod["name"] == "HIGH":
        mods.finish_organic(fuselage, render_levels=2)

    # 2. Cockpit Recess / Cutout
    cut_w = 0.52
    cut_l = L.COCKPIT_CUTOUT_Y[1] - L.COCKPIT_CUTOUT_Y[0]
    cut_y = (L.COCKPIT_CUTOUT_Y[0] + L.COCKPIT_CUTOUT_Y[1]) / 2.0
    cutter = mesh.box(nm(lod, "TEMP_Cockpit_Cutter"), "08_TEMP",
                      (0.0, cut_y, 0.68), (cut_w, cut_l, 0.35), mat="MAT_BODY_RED")
    if lod["name"] == "HIGH":
        mods.boolean(fuselage, cutter, op="DIFFERENCE", apply=True)
        while len(fuselage.data.materials) > 1:
            fuselage.data.materials.pop(index=len(fuselage.data.materials) - 1)
    else:
        cutter.name = nm(lod, "BODY_Cockpit_Opening")
        cutter.display_type = "WIRE"

    # 3. Front Radiator Intake Mouth & Grille Screen
    if lod["name"] == "HIGH":
        grille_ctr = (0.0, -1.905, 0.28)
        prof_grille = [(0.001, 0.0), (0.075, 0.0), (0.082, 0.015), (0.070, 0.022), (0.001, 0.022)]
        mesh.lathe(nm(lod, "BODY_Nose_Grille_Lip"), col, grille_ctr, prof_grille,
                   segs=24, mat="MAT_METAL_CHROME", axis="Y", closed=False)
        mesh.box(nm(lod, "BODY_Nose_Grille_Mesh"), col,
                 (0.0, -1.895, 0.28), (0.13, 0.01, 0.13), mat="MAT_METAL_DARK")

    # 4. Front Splitter / Carbon Wing Assembly
    sp_l = L.SPLITTER_Y_REAR - L.SPLITTER_Y_FRONT
    sp_y = (L.SPLITTER_Y_FRONT + L.SPLITTER_Y_REAR) / 2.0
    sp_w = L.SPLITTER_HALF_W * 2.0
    sp = mesh.box(nm(lod, "BODY_Front_Splitter"), col,
                  (0.0, sp_y, L.SPLITTER_Z), (sp_w, sp_l, 0.016), mat="MAT_CARBON")
    if lod["name"] == "HIGH":
        mods.finish_hard(sp, 0.003)
        for sgn, side in [(1.0, "L"), (-1.0, "R")]:
            ep = mesh.box(nm(lod, f"BODY_Splitter_Endplate_{side}"), col,
                          (sgn * L.SPLITTER_HALF_W, sp_y, L.SPLITTER_Z + 0.04),
                          (0.012, sp_l * 1.05, 0.10), mat="MAT_CARBON")
            mods.finish_hard(ep, 0.002)

        # Splitter support turnbuckle struts
        mesh.tube(nm(lod, "BODY_Splitter_Strut_L"), col,
                  [(0.18, -1.82, 0.09), (0.10, -1.75, 0.26)], 0.005, 8, mat="MAT_METAL_CHROME")
        mesh.tube(nm(lod, "BODY_Splitter_Strut_R"), col,
                  [(-0.18, -1.82, 0.09), (-0.10, -1.75, 0.26)], 0.005, 8, mat="MAT_METAL_CHROME")

    # 5. Dorsal Aerodynamic Fin
    fin_y0, fin_z0 = L.DORSAL_FIN_START
    fin_y1, fin_z1 = L.DORSAL_FIN_END
    fin_poly = [
        (0.0, fin_y0, fin_z0 - 0.04),
        (0.0, fin_y0, fin_z0),
        (0.0, fin_y1 - 0.25, 0.62),
        (0.0, fin_y1, fin_z1),
        (0.0, fin_y1, fin_z1 - 0.05),
        (0.0, 1.28, 0.58),
    ]
    fin_pa = [(+L.DORSAL_FIN_THICK / 2.0, y, z) for (_, y, z) in fin_poly]
    fin_pb = [(-L.DORSAL_FIN_THICK / 2.0, y, z) for (_, y, z) in fin_poly]
    fin = mesh.extrude_polys(nm(lod, "BODY_Dorsal_Fin"), col, [(fin_pa, fin_pb)], mat="MAT_BODY_RED")
    if lod["name"] == "HIGH":
        mods.finish_hard(fin, 0.002)

    # 6. Side Dive Planes / Canards
    canard_l_top = [(x, y, z + 0.008) for (x, y, z) in L.CANARD_L_PTS]
    canard_l_bot = [(x, y, z - 0.008) for (x, y, z) in L.CANARD_L_PTS]
    can_l = mesh.extrude_polys(nm(lod, "BODY_Canard_L"), col, [(canard_l_top, canard_l_bot)], mat="MAT_CARBON")

    canard_r_top = [(x, y, z + 0.008) for (x, y, z) in L.CANARD_R_PTS]
    canard_r_bot = [(x, y, z - 0.008) for (x, y, z) in L.CANARD_R_PTS]
    can_r = mesh.extrude_polys(nm(lod, "BODY_Canard_R"), col, [(canard_r_top, canard_r_bot)], mat="MAT_CARBON")
    if lod["name"] == "HIGH":
        mods.finish_hard(can_l, 0.002)
        mods.finish_hard(can_r, 0.002)

    # 7. High-detail secondary body parts: Louvers, Scoop, Coaming, Diffuser
    if lod["name"] == "HIGH":
        # Hood Louver Arrays (14 pairs along engine hood)
        specs = []
        for row_y in tables.lin(-0.95, -0.35, 14):
            specs.append(((0.10, row_y, 0.64), (0.19, row_y, 0.62), 0.006))
            specs.append(((-0.10, row_y, 0.64), (-0.19, row_y, 0.62), 0.006))
        mesh.multi_cyl(nm(lod, "BODY_Engine_Louvers"), lod["C_DETAIL"], specs, segs=8, mat="MAT_METAL_DARK")

        # Engine Hood Intake Scoop on Left Side
        scoop = mesh.box(nm(lod, "BODY_Engine_Scoop_L"), col,
                         (0.245, -0.65, 0.62), (0.075, 0.22, 0.055), mat="MAT_CARBON")
        mods.finish_hard(scoop, 0.003)

        # Padded leather coaming around cockpit rim
        coaming_pts = [
            (-0.24, 0.66, 0.72), (-0.26, 0.30, 0.65), (-0.26, -0.02, 0.68),
            (0.0, -0.05, 0.71),
            (+0.26, -0.02, 0.68), (+0.26, 0.30, 0.65), (+0.24, 0.66, 0.72),
        ]
        mesh.tube(nm(lod, "BODY_Cockpit_Coaming"), lod["C_DETAIL"], coaming_pts,
                  0.016, 10, mat="MAT_LEATHER_BROWN")

        # Underfloor Rear Diffuser Strakes
        for idx, xs in enumerate([-0.16, 0.0, +0.16]):
            diff = mesh.box(nm(lod, f"BODY_Diffuser_Strake_{idx}"), col,
                            (xs, 1.62, 0.14), (0.008, 0.62, 0.065), mat="MAT_CARBON")
            mods.finish_hard(diff, 0.002)


# ============================================================================ COCKPIT
def cockpit(lod):
    col = lod["C_SECONDARY"]
    c_mech = lod["C_MECH"]

    # 1. Curved Windscreen (acrylic aero deflector)
    ws_w = L.WINDSCREEN_W
    ws_y0, ws_y1 = L.WINDSCREEN_Y
    ws_z0, ws_z1 = L.WINDSCREEN_Z
    ws_curve = [
        (-ws_w * 0.50, ws_y1, ws_z0),
        (-ws_w * 0.35, ws_y0, ws_z1),
        (0.0,          ws_y0 - 0.02, ws_z1 + 0.02),
        (+ws_w * 0.35, ws_y0, ws_z1),
        (+ws_w * 0.50, ws_y1, ws_z0),
    ]
    ws_bot = [(x, y, ws_z0) for (x, y, _) in ws_curve]
    mesh.extrude_polys(nm(lod, "BODY_Windscreen"), col, [(ws_curve, ws_bot)], mat="MAT_GLASS")

    # 2. Aero Bullet Mirror (left cowl)
    if lod["name"] == "HIGH":
        prof_mir = [(0.001, 0), (0.026, 0), (0.026, 0.035), (0.014, 0.055), (0.001, 0.065)]
        mesh.lathe(nm(lod, "BODY_Mirror_L"), col, (0.28, -0.02, 0.77), prof_mir,
                   segs=16, mat="MAT_METAL_CHROME", axis="Y", closed=False)
        mesh.tube(nm(lod, "BODY_Mirror_Stem_L"), col, [(0.26, -0.02, 0.72), (0.28, -0.02, 0.77)],
                  0.006, 8, mat="MAT_METAL_CHROME")

    # 3. Racing Bucket Seat
    seat_w, seat_l, seat_h = L.SEAT_DIMS
    seat_ctr = Vector(L.SEAT_CENTER)
    s_base = mesh.box(nm(lod, "COCKPIT_Seat_Base"), col,
                      (seat_ctr.x, seat_ctr.y, seat_ctr.z),
                      (seat_w, seat_l * 0.75, 0.12), mat="MAT_LEATHER_BROWN")
    s_back = mesh.box(nm(lod, "COCKPIT_Seat_Back"), col,
                      (seat_ctr.x, seat_ctr.y + seat_l * 0.32, seat_ctr.z + seat_h * 0.45),
                      (seat_w * 0.95, 0.10, seat_h * 0.85), mat="MAT_LEATHER_BROWN")
    s_back.rotation_euler = (math.radians(-14.0), 0.0, 0.0)
    if lod["name"] == "HIGH":
        mods.finish_hard(s_base, 0.008)
        mods.finish_hard(s_back, 0.008)

        # Quilted / pleated cushion ridges
        cushion_specs = []
        for dy in tables.lin(-0.12, 0.12, 5):
            cushion_specs.append(((seat_ctr.x - 0.16, seat_ctr.y + dy, seat_ctr.z + 0.065),
                                  (seat_ctr.x + 0.16, seat_ctr.y + dy, seat_ctr.z + 0.065), 0.012))
        mesh.multi_cyl(nm(lod, "COCKPIT_Seat_Pleats"), lod["C_DETAIL"], cushion_specs,
                       segs=8, mat="MAT_LEATHER_BROWN")

        # 4-point Racing Harness straps + rotary camlock buckle
        strap_w, strap_th = 0.045, 0.006
        for sgn in (1.0, -1.0):
            p1 = Vector((sgn * 0.08, seat_ctr.y + 0.30, seat_ctr.z + 0.48))
            p2 = Vector((sgn * 0.07, seat_ctr.y + 0.05, seat_ctr.z + 0.16))
            mesh.box(nm(lod, f"COCKPIT_Harness_{'L' if sgn > 0 else 'R'}"), lod["C_DETAIL"],
                     (p1 + p2) / 2.0, (strap_w, (p2 - p1).length, strap_th), mat="MAT_CARBON")
        mesh.cyl(nm(lod, "COCKPIT_Harness_Buckle"), lod["C_DETAIL"],
                 (0.0, seat_ctr.y + 0.06, seat_ctr.z + 0.17),
                 (0.0, seat_ctr.y + 0.06, seat_ctr.z + 0.19),
                 0.022, 16, mat="MAT_METAL_CHROME")

    # 4. Vintage Steering Wheel Assembly
    st_c = Vector(L.STEERING_CENTER)
    st_r = L.STEERING_R
    st_ang = L.STEERING_ANGLE

    col_end = st_c + Vector((0.0, -0.35, -0.22))
    mesh.tube(nm(lod, "COCKPIT_Steering_Column"), c_mech, [col_end, st_c],
              0.016, lod["tube_seg"], mat="MAT_METAL_DARK")

    prof_rim = [(st_r - 0.012, -0.012), (st_r + 0.012, -0.012),
                (st_r + 0.012, +0.012), (st_r - 0.012, +0.012)]
    rim = mesh.lathe(nm(lod, "COCKPIT_Steering_Rim"), col, st_c, prof_rim,
                     segs=lod["lathe_seg"], mat="MAT_LEATHER_BROWN", axis="Y")
    rim.rotation_euler = (st_ang, 0.0, 0.0)

    for deg in (90.0, 210.0, 330.0):
        rad = math.radians(deg)
        sp_out = st_c + Vector((st_r * math.cos(rad), -st_r * math.sin(rad) * math.sin(st_ang),
                                st_r * math.sin(rad) * math.cos(st_ang)))
        mesh.tube(nm(lod, f"COCKPIT_Steering_Spoke_{int(deg)}"), c_mech, [st_c, sp_out],
                  0.007, 8, mat="MAT_METAL_CHROME")

    # 5. Dashboard & Multi-Gauge Cluster
    dash_c = (0.0, -0.02, 0.62)
    mesh.box(nm(lod, "COCKPIT_Dashboard"), col, dash_c, (0.42, 0.04, 0.14), mat="MAT_METAL_DARK")
    if lod["name"] == "HIGH":
        # Central Tachometer
        prof_g1 = [(0.001, 0), (0.038, 0), (0.041, 0.012), (0.001, 0.012)]
        mesh.lathe(nm(lod, "COCKPIT_Gauge_Tach"), c_mech, (0.0, -0.01, 0.63), prof_g1,
                   segs=16, mat="MAT_METAL_CHROME", axis="Y", closed=False)
        # Left Oil & Right Water Gauges
        prof_g2 = [(0.001, 0), (0.024, 0), (0.026, 0.010), (0.001, 0.010)]
        mesh.lathe(nm(lod, "COCKPIT_Gauge_Oil"), c_mech, (-0.10, -0.01, 0.62), prof_g2,
                   segs=16, mat="MAT_METAL_CHROME", axis="Y", closed=False)
        mesh.lathe(nm(lod, "COCKPIT_Gauge_Water"), c_mech, (+0.10, -0.01, 0.62), prof_g2,
                   segs=16, mat="MAT_METAL_CHROME", axis="Y", closed=False)

        # 3 Drilled Alloy Pedals in Footwell
        for pname, xp in [("Clutch", 0.06), ("Brake", 0.0), ("Throttle", -0.06)]:
            mesh.box(nm(lod, f"COCKPIT_Pedal_{pname}"), c_mech,
                     (xp, -0.62, 0.22), (0.038, 0.010, 0.058), mat="MAT_METAL_CHROME")
            mesh.tube(nm(lod, f"COCKPIT_Pedal_Arm_{pname}"), c_mech,
                      [(xp, -0.62, 0.22), (xp, -0.55, 0.34)], 0.006, 6, mat="MAT_METAL_DARK")

    # 6. Controls: Gated Shifter
    shifter_base = (-0.14, 0.16, 0.32)
    shifter_knob = (-0.14, 0.14, 0.46)
    mesh.tube(nm(lod, "COCKPIT_Shift_Lever"), c_mech, [shifter_base, shifter_knob],
              0.009, 8, mat="MAT_METAL_CHROME")
    prof_knob = [(0.001, 0.0), (0.018, 0.0), (0.018, 0.03), (0.001, 0.03)]
    mesh.lathe(nm(lod, "COCKPIT_Shift_Knob"), col, shifter_knob, prof_knob,
               segs=16, mat="MAT_LEATHER_BROWN", closed=False, axis="Z")


# ============================================================================ EXHAUST
def exhaust(lod):
    col = lod["C_PRIMARY"]
    t_seg = lod["tube_seg"]

    # 1. 4-into-1 Primary Exhaust Header Pipes (emerging from right hood)
    if lod["name"] == "HIGH":
        collector_pt = (-0.31, -0.38, 0.44)
        for i, y_head in enumerate([-0.82, -0.72, -0.62, -0.52]):
            p0 = (-0.23, y_head, 0.48)
            p1 = (-0.29, y_head + 0.08, 0.46)
            mesh.tube(nm(lod, f"EXHAUST_Header_{i}"), col, [p0, p1, collector_pt],
                      0.020, t_seg, mat="MAT_EXHAUST", smooth_path=True)

    # 2. Main Exhaust Runner Pipe (runs down flank)
    pts = [Vector(p) for p in L.EXHAUST_PATH]
    ex = mesh.tube(nm(lod, "EXHAUST_Pipe"), col, pts, L.EXHAUST_R,
                   t_seg, mat="MAT_EXHAUST", smooth_path=True)
    if lod["name"] == "HIGH":
        mods.finish_hard(ex, 0.002)

        # 3. Textured Heat Wrap Section (thick sleeve around mid-pipe)
        wrap_pts = pts[1:5]
        wr = mesh.tube(nm(lod, "EXHAUST_Heat_Wrap"), lod["C_DETAIL"], wrap_pts,
                       L.EXHAUST_WRAP_R, t_seg, mat="MAT_CARBON", smooth_path=True)
        mods.finish_hard(wr, 0.003)

        # Clamp rings on heat wrap ends
        for cp in (wrap_pts[0], wrap_pts[-1]):
            mesh.tube(nm(lod, f"EXHAUST_Clamp_{int(cp.y * 100)}"), lod["C_DETAIL"],
                      [cp - Vector((0.008, 0, 0)), cp + Vector((0.008, 0, 0))],
                      L.EXHAUST_WRAP_R + 0.004, 16, mat="MAT_METAL_CHROME")

        # 4. Flared Megaphone Tailpipe Tip
        tip_start = pts[-1]
        tip_end   = pts[-1] + Vector((0.03, 0.32, 0.02))
        mesh.tube(nm(lod, "EXHAUST_Tip_Megaphone"), col, [tip_start, tip_end],
                  L.EXHAUST_R + 0.015, t_seg, mat="MAT_EXHAUST")


# ============================================================================ CHASSIS & MECHANICS (UNCERTAIN)
def chassis_and_mechanics(lod):
    col = lod["C_MECH"]
    t_seg = max(6, lod["tube_seg"] // 2)

    # Spaceframe chassis tubes (visible through suspension & underside)
    tubes = [
        [(+0.18, -1.40, 0.18), (+0.18, 1.40, 0.18)],
        [(-0.18, -1.40, 0.18), (-0.18, 1.40, 0.18)],
        [(+0.20, -1.30, 0.44), (+0.20, 0.80, 0.44)],
        [(-0.20, -1.30, 0.44), (-0.20, 0.80, 0.44)],
        [(-0.18, -1.30, 0.18), (+0.18, -1.30, 0.18)],
        [(-0.18, -0.05, 0.18), (+0.18, -0.05, 0.18)],
        [(-0.18,  1.28, 0.18), (+0.18,  1.28, 0.18)],
    ]
    for idx, path in enumerate(tubes):
        mesh.tube(nm(lod, f"UNCERTAIN_FRAME_Rail_{idx}"), col, path,
                  0.016, t_seg, mat="MAT_METAL_DARK")

    mesh.box(nm(lod, "UNCERTAIN_ENGINE_Block"), col,
             (0.0, -0.65, 0.38), (0.34, 0.65, 0.35), mat="MAT_METAL_DARK")

    mesh.cyl(nm(lod, "UNCERTAIN_Diff_Transaxle"), col,
             (0.0, 1.28, 0.28), (0.0, 1.28, 0.44), 0.12,
             16, mat="MAT_METAL_DARK")


# ============================================================================ FASTENERS & DETAILS
def fasteners(lod):
    if lod["name"] != "HIGH":
        return

    col = lod["C_DETAIL"]
    # Twin vintage quick-fill fuel caps on rear deck
    for tag, loc in [("L", L.FUEL_CAP_L), ("R", L.FUEL_CAP_R)]:
        prof_cap = [(0.001, 0.0), (L.FUEL_CAP_R_SIZE, 0.0),
                    (L.FUEL_CAP_R_SIZE, 0.015), (0.015, 0.035), (0.001, 0.035)]
        mesh.lathe(nm(lod, f"FASTENER_FuelCap_{tag}"), col, loc, prof_cap,
                   segs=24, mat="MAT_METAL_CHROME", closed=False, axis="Z")

    # Hood latch pins along the engine cowl split line
    specs = []
    for y_pin in (-1.10, -0.80, -0.50, -0.20):
        specs.append(((+0.27, y_pin, 0.54), (+0.28, y_pin, 0.54), 0.008))
        specs.append(((-0.27, y_pin, 0.54), (-0.28, y_pin, 0.54), 0.008))
    mesh.multi_cyl(nm(lod, "FASTENER_Hood_Pins"), col, specs, segs=8, mat="MAT_METAL_CHROME")


# ============================================================================ MASTER BUILD ALL
def build_all(lod):
    wheels(lod)
    suspension(lod)
    body_shell(lod)
    cockpit(lod)
    exhaust(lod)
    chassis_and_mechanics(lod)
    fasteners(lod)
