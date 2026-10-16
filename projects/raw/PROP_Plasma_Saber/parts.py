"""
Part builders for PROP_Plasma_Saber (staged pipeline, docs/01_WORKFLOW.md).
Model convention: +Z up, -Y forward (emitter right), +X = object's LEFT side.
Pure procedural bmesh construction, 100% reproducible and deterministic.

  S1 PRIMITIVE  masses + proportions from primitives (boxes, cylinders)
  S2 LOWPOLY    real forms, clean quad topology, no bevels, shared UV atlas (LOD0)
  S3 DETAIL     hero mesh with hard-surface bevels, weighted normals, ribs, cooling fins
  S4 GAME       bake S3 -> S2 atlas, LOD1-2, collision hulls, Godot/Unity/Unreal export
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part, nm
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "hero_prop"                 # tables.BUDGETS
TARGET_DIMS = (None, 0.308, None)      # total length with D-ring (770 px / 2500 = 0.308 m)
GROUND = False                         # Hand-held prop: bore axis at Z = 0
PROFILES = {
    1: stages.profile(1, ring=12, lathe=12, stations=8),
    2: stages.profile(2, ring=32, lathe=32, stations=20),
    3: stages.profile(3, ring=48, lathe=48, stations=32),
}

GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.01, uv_m=2.0)
LICENCE = "Original, copyright-safe tactical plasma saber design; 100% procedural"
UNCERTAIN = ["Radial symmetry assumed for cylindrical chassis", "D-ring loop resting angle"]

# Maximum 4 materials for prop (docs/02_STANDARDS.md)
PALETTE = {
    "MAT_TITANIUM": ((0.045, 0.048, 0.052), 0.90, 0.35),   # Anodized gunmetal titanium
    "MAT_CHROME":   ((0.68, 0.70, 0.72), 0.95, 0.22),      # Brushed aerospace chrome/aluminum
    "MAT_BRONZE":   ((0.55, 0.38, 0.16), 0.88, 0.28),      # Bronze/gold magnetic containment coils
    "MAT_POLYMER":  ((0.030, 0.030, 0.032), 0.05, 0.70),   # Matte textured black grip inlays
}
TITAN, CHROME, BRONZE, POLYMER = "MAT_TITANIUM", "MAT_CHROME", "MAT_BRONZE", "MAT_POLYMER"

CRITICAL_PAIRS = []


def Y(u):
    """World Y of a photo column u."""
    return L.P(u, L.V0)[0]


def Z(v):
    """World Z of a photo row v."""
    return L.P(L.ANCHOR_PX[0], v)[1]


def R(r_px):
    """Metres corresponding to a pixel radius."""
    return r_px / L.S


def hard(ob, P, bevel=0.0015):
    """Hard-surface finish: bevel + weighted normals from S3 on."""
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


# ============================================================================
# 1. EMITTER ASSEMBLY (Emitter shroud, focus coils, radiator base, nozzle)
# ============================================================================
def emitter_prim(P):
    C = P["coll"]
    out = []
    # Base and focus coils cylinder
    out.append(prim.cyl_px(nm(P, "EMIT_Base"), C, (L.EMITTER_BASE_U0, L.V0), (L.EMITTER_BASE_U1, L.V0),
                           R(L.R_EMITTER_COIL), segs=P["ring"], mat=TITAN))
    # Emitter shroud cylinder
    out.append(prim.cyl_px(nm(P, "EMIT_Shroud"), C, (L.EMITTER_SHROUD_U0, L.V0), (L.EMITTER_SHROUD_U1, L.V0),
                           R(L.R_EMITTER_SHROUD), segs=P["ring"], mat=TITAN))
    return out


def emitter(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    # 1a. Radiator base
    y0, y1 = Y(810.0), Y(840.0)
    out.append(hard(mesh.cyl(nm(P, "EMIT_RadiatorBase"), C, (0, y0, 0), (0, y1, 0), R(L.R_COLLAR),
                             segs=ring, mat=TITAN), P, 0.001))

    # 1b. Magnetic focus coil 1
    y0, y1 = Y(840.0), Y(865.0)
    out.append(hard(mesh.cyl(nm(P, "EMIT_Coil1"), C, (0, y0, 0), (0, y1, 0), R(L.R_EMITTER_COIL),
                             segs=ring, mat=BRONZE), P, 0.0008))

    # 1c. Magnetic focus coil 2
    y0, y1 = Y(865.0), Y(890.0)
    out.append(hard(mesh.cyl(nm(P, "EMIT_Coil2"), C, (0, y0, 0), (0, y1, 0), R(L.R_EMITTER_COIL),
                             segs=ring, mat=BRONZE), P, 0.0008))

    # 1d. Angled Emitter Shroud (slanted crown)
    # Outer radius 21 mm, inner radius 15 mm. Rear at Y(890), front cut from Y(935) bottom to Y(1015) top.
    r_out = R(L.R_EMITTER_SHROUD)
    r_in = R(L.R_EMITTER_SHROUD - 15.0)
    y_rear = Y(890.0)
    y_front_top = Y(1015.0)
    y_front_bot = Y(935.0)

    bm = bmesh.new()
    segs = ring
    r_rear_out = []
    r_rear_in = []
    r_front_out = []
    r_front_in = []

    for k in range(segs):
        ang = 2 * math.pi * k / segs
        ca, sa = math.cos(ang), math.sin(ang)
        # Vertical factor t from 0 (bottom sa=-1) to 1 (top sa=+1)
        t = (sa + 1.0) * 0.5
        y_front = y_front_bot + t * (y_front_top - y_front_bot)

        # Rear verts
        r_rear_out.append(bm.verts.new((r_out * ca, y_rear, r_out * sa)))
        r_rear_in.append(bm.verts.new((r_in * ca, y_rear, r_in * sa)))

        # Front verts
        r_front_out.append(bm.verts.new((r_out * ca, y_front, r_out * sa)))
        r_front_in.append(bm.verts.new((r_in * ca, y_front, r_in * sa)))

    # Quads
    for k in range(segs):
        k_next = (k + 1) % segs
        # Outer surface
        bm.faces.new((r_rear_out[k], r_front_out[k], r_front_out[k_next], r_rear_out[k_next]))
        # Inner surface
        bm.faces.new((r_rear_in[k_next], r_front_in[k_next], r_front_in[k], r_rear_in[k]))
        # Front slanted lip
        bm.faces.new((r_front_out[k], r_front_in[k], r_front_in[k_next], r_front_out[k_next]))
        # Rear rim
        bm.faces.new((r_rear_in[k], r_rear_out[k], r_rear_out[k_next], r_rear_in[k_next]))

    shroud_ob = mesh.finish(nm(P, "EMIT_Shroud"), bm, C, TITAN, smooth=True, sharp_angle=35.0)
    out.append(hard(shroud_ob, P, 0.0012))

    # 1e. Internal plasma aperture nozzle
    y0, y1 = Y(905.0), Y(955.0)
    out.append(hard(mesh.cyl(nm(P, "EMIT_Nozzle"), C, (0, y0, 0), (0, y1, 0), R(L.R_NOZZLE),
                             segs=ring, mat=BRONZE), P, 0.0008))

    return out


# ============================================================================
# 2. UPPER CHASSIS / RADIATOR CHOKE
# ============================================================================
def chassis_upper_prim(P):
    C = P["coll"]
    return [prim.cyl_px(nm(P, "CHASSIS_UpperNeck"), C, (L.CHASSIS_UPPER_U0, L.V0), (L.CHASSIS_UPPER_U1, L.V0),
                        R(L.R_CHOKE), segs=P["ring"], mat=CHROME)]


def chassis_upper(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    # Choke neck core
    y0, y1 = Y(760.0), Y(810.0)
    out.append(hard(mesh.cyl(nm(P, "CHASSIS_UpperNeck"), C, (0, y0, 0), (0, y1, 0), R(L.R_CHOKE),
                             segs=ring, mat=CHROME), P, 0.001))

    # Annular cooling fins
    r_fin = R(L.R_COLLAR - 2.5)
    if P["stage"] <= 2:
        # Central cooling collar block
        yc0, yc1 = Y(780.0), Y(795.0)
        out.append(hard(mesh.cyl(nm(P, "CHASSIS_UpperFinBlock"), C, (0, yc0, 0), (0, yc1, 0), r_fin,
                                 segs=ring, mat=CHROME), P, 0.0008))
    else:
        # 4 distinct precision cooling fins in S3
        u_fins = [768.0, 780.0, 792.0, 804.0]
        for idx, uf in enumerate(u_fins):
            yf0 = Y(uf - 3.0)
            yf1 = Y(uf + 3.0)
            out.append(hard(mesh.cyl(nm(P, f"CHASSIS_UpperFin_{idx}"), C, (0, yf0, 0), (0, yf1, 0), r_fin,
                                     segs=ring, mat=CHROME), P, 0.0006))

    return out


# ============================================================================
# 3. PLASMA CRYSTAL CHAMBER
# ============================================================================
def crystal_chamber_prim(P):
    C = P["coll"]
    return [prim.cyl_px(nm(P, "CHAMBER_Housing"), C, (L.CHAMBER_U0, L.V0), (L.CHAMBER_U1, L.V0),
                        R(L.R_POMMEL_CAP), segs=P["ring"], mat=TITAN)]


def crystal_chamber(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    y0, y1 = Y(680.0), Y(760.0)

    # 3a. Structural load-bearing struts (4 struts at 90°, 270°, 0°, 180°)
    # Top strut at 90° (+Z) sits at silhouette top: v from 312.5 to 317.0
    # Bottom strut at 270° (-Z) sits at silhouette bottom: v from 403.0 to 407.5
    r_strut_out = R(L.R_POMMEL_CAP)
    r_strut_in = R(L.R_POMMEL_CAP - 8.0)
    w_strut = 0.004  # 4 mm half-width in tangential direction

    bm = bmesh.new()
    # Build 4 struts as solid curved beams
    angles = [math.pi / 2.0, 3 * math.pi / 2.0, 0.0, math.pi]
    for ang in angles:
        ca, sa = math.cos(ang), math.sin(ang)
        # Tangent vector
        tx, tz = -sa, ca
        # 4 corners at rear (y0)
        p0 = Vector((r_strut_in * ca - w_strut * tx, y0, r_strut_in * sa - w_strut * tz))
        p1 = Vector((r_strut_out * ca - w_strut * tx, y0, r_strut_out * sa - w_strut * tz))
        p2 = Vector((r_strut_out * ca + w_strut * tx, y0, r_strut_out * sa + w_strut * tz))
        p3 = Vector((r_strut_in * ca + w_strut * tx, y0, r_strut_in * sa + w_strut * tz))
        # 4 corners at front (y1)
        p4 = Vector((r_strut_in * ca - w_strut * tx, y1, r_strut_in * sa - w_strut * tz))
        p5 = Vector((r_strut_out * ca - w_strut * tx, y1, r_strut_out * sa - w_strut * tz))
        p6 = Vector((r_strut_out * ca + w_strut * tx, y1, r_strut_out * sa + w_strut * tz))
        p7 = Vector((r_strut_in * ca + w_strut * tx, y1, r_strut_in * sa + w_strut * tz))

        v0, v1, v2, v3 = bm.verts.new(p0), bm.verts.new(p1), bm.verts.new(p2), bm.verts.new(p3)
        v4, v5, v6, v7 = bm.verts.new(p4), bm.verts.new(p5), bm.verts.new(p6), bm.verts.new(p7)

        # 6 faces of the beam
        bm.faces.new((v0, v1, v2, v3))  # rear cap
        bm.faces.new((v7, v6, v5, v4))  # front cap
        bm.faces.new((v1, v5, v6, v2))  # outer face
        bm.faces.new((v3, v2, v6, v7))  # side 1
        bm.faces.new((v0, v3, v7, v4))  # inner face
        bm.faces.new((v0, v4, v5, v1))  # side 2

    struts_ob = mesh.finish(nm(P, "CHAMBER_Struts"), bm, C, TITAN, smooth=True, sharp_angle=40.0)
    out.append(hard(struts_ob, P, 0.001))

    # 3b. Inner containment sapphire tube
    r_tube = R(L.R_POMMEL_CAP - 7.5)
    tube_ob = mesh.cyl(nm(P, "CHAMBER_Sleeve"), C, (0, y0 + 0.002, 0), (0, y1 - 0.002, 0), r_tube,
                       segs=ring, mat=CHROME)
    out.append(hard(tube_ob, P, 0.0008))

    # 3c. Floating Kyber Crystal (double hexagonal bipyramid)
    y_center = Y(720.0)
    c_len = 0.008  # 16 mm total length
    c_rad = R(L.R_CRYSTAL)
    bm_c = bmesh.new()
    v_tip_rear = bm_c.verts.new((0, y_center + c_len, 0))
    v_tip_front = bm_c.verts.new((0, y_center - c_len, 0))
    hex_verts = []
    for i in range(6):
        a = 2 * math.pi * i / 6
        hex_verts.append(bm_c.verts.new((c_rad * math.cos(a), y_center, c_rad * math.sin(a))))
    for i in range(6):
        i_next = (i + 1) % 6
        bm_c.faces.new((v_tip_rear, hex_verts[i], hex_verts[i_next]))
        bm_c.faces.new((v_tip_front, hex_verts[i_next], hex_verts[i]))
    crystal_ob = mesh.finish(nm(P, "CHAMBER_Crystal"), bm_c, C, BRONZE, smooth=False)
    out.append(hard(crystal_ob, P, 0.0005))

    return out


# ============================================================================
# 4. SWITCH MODULE & MID CHASSIS
# ============================================================================
def switch_module_prim(P):
    C = P["coll"]
    out = []
    # Mid cylinder
    out.append(prim.cyl_px(nm(P, "CHASSIS_Mid"), C, (L.SWITCH_U0, L.V0), (L.SWITCH_U1, L.V0),
                           R(L.R_POMMEL_CAP), segs=P["ring"], mat=TITAN))
    # Switch box
    out.append(prim.box_px(nm(P, "CTRL_SwitchBox"), C,
                           (L.SWITCH_BOX_U0, 302.5, L.SWITCH_BOX_U1, 312.5),
                           0.010, mat=TITAN))
    return out


def switch_module(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    # Mid chassis cylinder
    y0, y1 = Y(580.0), Y(680.0)
    out.append(hard(mesh.cyl(nm(P, "CHASSIS_Mid"), C, (0, y0, 0), (0, y1, 0), R(L.R_POMMEL_CAP),
                             segs=ring, mat=TITAN), P, 0.001))

    # Switch box housing on +Z: u from 590 to 670, v from 302.5 to 312.5
    # Height Z = 0.018 to 0.023 m
    yb0, yb1 = Y(590.0), Y(670.0)
    center = (0.0, (yb0 + yb1) * 0.5, 0.0205)
    size = (0.018, abs(yb0 - yb1), 0.005)
    housing = mesh.box(nm(P, "CTRL_Housing"), C, center, size, TITAN)
    out.append(hard(housing, P, 0.0008))

    # Rocker switch 1 (ignition switch)
    yr0, yr1 = Y(605.0), Y(630.0)
    c_rocker = (0.0, (yr0 + yr1) * 0.5, 0.0236)
    s_rocker = (0.010, abs(yr0 - yr1), 0.002)
    rocker = mesh.box(nm(P, "CTRL_Rocker"), C, c_rocker, s_rocker, POLYMER)
    out.append(hard(rocker, P, 0.0005))

    # Aux toggle / dial
    ya0, ya1 = Y(645.0), Y(665.0)
    c_aux = (0.0, (ya0 + ya1) * 0.5, 0.0233)
    s_aux = (0.008, abs(ya0 - ya1), 0.0016)
    aux_dial = mesh.box(nm(P, "CTRL_AuxDial"), C, c_aux, s_aux, CHROME)
    out.append(hard(aux_dial, P, 0.0005))

    return out


# ============================================================================
# 5. GRIP ASSEMBLY
# ============================================================================
def grip_prim(P):
    C = P["coll"]
    return [prim.cyl_px(nm(P, "GRIP_Main"), C, (L.GRIP_U0, L.V0), (L.GRIP_U1, L.V0),
                        R(L.R_MAIN_TUBE), segs=P["ring"], mat=TITAN)]


def grip(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    # 5a. Main titanium grip cylinder: u=350 to 580
    y0, y1 = Y(350.0), Y(580.0)
    out.append(hard(mesh.cyl(nm(P, "GRIP_Main"), C, (0, y0, 0), (0, y1, 0), R(L.R_MAIN_TUBE),
                             segs=ring, mat=TITAN), P, 0.001))

    # 5b. Diamond knurled choke band: u=530 to 580
    yc0, yc1 = Y(530.0), Y(580.0)
    out.append(hard(mesh.cyl(nm(P, "GRIP_Choke"), C, (0, yc0, 0), (0, yc1, 0), R(L.R_MAIN_TUBE + 2.5),
                             segs=ring, mat=CHROME), P, 0.0008))

    # 5c. 6 Longitudinal ribbed polymer grip strips
    # u from 355 to 525, spaced at 60 deg angles (including top 90 deg and bottom 270 deg)
    yr0, yr1 = Y(355.0), Y(525.0)
    r_in = R(L.R_MAIN_TUBE)
    r_out = R(L.R_MAIN_TUBE + 3.75)  # stands proud at 19 mm = 47.5 px
    half_angle = math.radians(7.5)   # 15 degree wide strips

    bm = bmesh.new()
    for i in range(6):
        center_ang = i * (2 * math.pi / 6.0)
        a0 = center_ang - half_angle
        a1 = center_ang + half_angle

        # 4 corners at rear (yr0)
        p0 = Vector((r_in * math.cos(a0), yr0, r_in * math.sin(a0)))
        p1 = Vector((r_out * math.cos(a0), yr0, r_out * math.sin(a0)))
        p2 = Vector((r_out * math.cos(a1), yr0, r_out * math.sin(a1)))
        p3 = Vector((r_in * math.cos(a1), yr0, r_in * math.sin(a1)))

        # 4 corners at front (yr1)
        p4 = Vector((r_in * math.cos(a0), yr1, r_in * math.sin(a0)))
        p5 = Vector((r_out * math.cos(a0), yr1, r_out * math.sin(a0)))
        p6 = Vector((r_out * math.cos(a1), yr1, r_out * math.sin(a1)))
        p7 = Vector((r_in * math.cos(a1), yr1, r_in * math.sin(a1)))

        v0, v1, v2, v3 = bm.verts.new(p0), bm.verts.new(p1), bm.verts.new(p2), bm.verts.new(p3)
        v4, v5, v6, v7 = bm.verts.new(p4), bm.verts.new(p5), bm.verts.new(p6), bm.verts.new(p7)

        bm.faces.new((v0, v1, v2, v3))
        bm.faces.new((v7, v6, v5, v4))
        bm.faces.new((v1, v5, v6, v2))
        bm.faces.new((v3, v2, v6, v7))
        bm.faces.new((v0, v3, v7, v4))
        bm.faces.new((v0, v4, v5, v1))

    ribs_ob = mesh.finish(nm(P, "GRIP_Ribs"), bm, C, POLYMER, smooth=True, sharp_angle=40.0)
    out.append(hard(ribs_ob, P, 0.0006))

    return out


# ============================================================================
# 6. LOWER CHASSIS COUPLER
# ============================================================================
def chassis_lower_prim(P):
    C = P["coll"]
    return [prim.cyl_px(nm(P, "CHASSIS_Lower"), C, (L.CHASSIS_LOWER_U0, L.V0), (L.CHASSIS_LOWER_U1, L.V0),
                        R(L.R_COLLAR), segs=P["ring"], mat=CHROME)]


def chassis_lower(P):
    C = P["coll"]
    ring = P["ring"]
    y0, y1 = Y(325.0), Y(350.0)
    ob = mesh.cyl(nm(P, "CHASSIS_Lower"), C, (0, y0, 0), (0, y1, 0), R(L.R_COLLAR), segs=ring, mat=CHROME)
    return [hard(ob, P, 0.001)]


# ============================================================================
# 7. POMMEL ASSEMBLY (Vented pommel cap and D-ring retention loop)
# ============================================================================
def pommel_prim(P):
    C = P["coll"]
    out = []
    out.append(prim.cyl_px(nm(P, "POMMEL_Cap"), C, (L.POMMEL_U0, L.V0), (L.POMMEL_U1, L.V0),
                           R(L.R_POMMEL_CAP), segs=P["ring"], mat=TITAN))
    out.append(prim.cyl_px(nm(P, "POMMEL_Dring"), C, (L.DRING_U0, L.V0), (L.POMMEL_U0, L.V0),
                           0.010, segs=P["ring"], mat=CHROME))
    return out


def pommel(P):
    C = P["coll"]
    ring = P["ring"]
    out = []

    # 7a. Stepped pommel cap body
    # Base plate: u=265 to 275, r=17 mm
    y0, y1 = Y(265.0), Y(275.0)
    out.append(hard(mesh.cyl(nm(P, "POMMEL_Base"), C, (0, y0, 0), (0, y1, 0), R(L.R_POMMEL_CAP - 6.25),
                             segs=ring, mat=TITAN), P, 0.001))

    # Fluted main pommel body: u=275 to 315, r=19.5 mm
    y0, y1 = Y(275.0), Y(315.0)
    out.append(hard(mesh.cyl(nm(P, "POMMEL_Body"), C, (0, y0, 0), (0, y1, 0), R(L.R_POMMEL_CAP),
                             segs=ring, mat=TITAN), P, 0.001))

    # Flange groove: u=315 to 325, r=17.5 mm
    y0, y1 = Y(315.0), Y(325.0)
    out.append(hard(mesh.cyl(nm(P, "POMMEL_Flange"), C, (0, y0, 0), (0, y1, 0), R(L.R_MAIN_TUBE),
                             segs=ring, mat=CHROME), P, 0.0008))

    # 7b. D-ring bracket
    yb0, yb1 = Y(260.0), Y(268.0)
    center_br = (0.0, (yb0 + yb1) * 0.5, 0.0)
    size_br = (0.008, abs(yb0 - yb1), 0.008)
    bracket = mesh.box(nm(P, "POMMEL_Bracket"), C, center_br, size_br, CHROME)
    out.append(hard(bracket, P, 0.0005))

    # 7c. D-ring retention loop (torus/tube in YZ plane)
    # Loop extends from u=245 to 265, v from 335 to 385 (diameter 50 px = 20 mm)
    loop_radius = R(20.0)
    wire_radius = 0.0015
    y_center = Y(255.0)
    pts = []
    steps = ring
    for i in range(steps):
        a = 2 * math.pi * i / steps
        pts.append((0.0, y_center + loop_radius * math.cos(a) * 0.5, loop_radius * math.sin(a)))
    loop = mesh.tube(nm(P, "POMMEL_Dring"), C, pts, wire_radius, segs=8, mat=CHROME, smooth_path=False)
    out.append(hard(loop, P, 0.0005))

    return out


# ============================================================================
# REGISTRY
# ============================================================================
PARTS = [
    Part("emitter", emitter, collision="hull"),
    Part("chassis_upper", chassis_upper, collision="hull"),
    Part("crystal_chamber", crystal_chamber, collision="hull"),
    Part("switch_module", switch_module, collision="box"),
    Part("grip", grip, collision="hull"),
    Part("chassis_lower", chassis_lower, collision="hull"),
    Part("pommel", pommel, collision="hull"),
]

PIVOTS = {
    "POMMEL_Dring": lambda: L.P3(260.0, 360.0, 0.0),
}
CHILDREN = {}


def guide_points():
    return {
        "ANCHOR": (0.0, *L.P(640.0, 360.0)),
        "EMITTER_TIP": (0.0, *L.P(1015.0, 360.0)),
        "POMMEL_BASE": (0.0, *L.P(265.0, 360.0)),
    }
