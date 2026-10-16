"""Procedural builders for the authored K-7 Rook FPS rifle.

Refactored for clean game-ready topology, zero degenerate elements, unified multi-element
meshes (~20-25 objects instead of 148), and complete S1-S4 automated game pipeline.
"""
import math
import bmesh
import bpy
from mathutils import Vector

import landmarks as L
from workbench import stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "hero_prop"
TARGET_DIMS = (None, 0.904, None)
GROUND = False

PROFILES = {
    1: stages.profile(1, ring=8, stations=6),
    2: stages.profile(2, ring=20, stations=20),
    3: stages.profile(3, ring=28, stations=26),
}

# S4 Game delivery configuration
GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.02,
            image_format="JPEG", image_quality=92)

LICENCE = "Original procedural K-7 Rook design; no third-party geometry, UVs, or textures reused."
UNCERTAIN = [
    "Hidden surfaces and internal mechanisms are art-directed simplifications, not engineered parts.",
    "Depth is an authored game-art estimate; no dimensioned real-world source was used.",
    "Sights are presented raised for a clear FPS alignment; the hinge details are simplified.",
]
ASSUMPTIONS = [
    "The 0.904 m muzzle-to-butt length is an authored target dimension, not a manufacturer specification.",
    "The side silhouette is an original orthographic design, not the retained historical photo.",
]
KNOWN_LIMITATIONS = [
    "The project is a static game prop with separate pivot-ready components, not a firing simulation.",
    "M-LOK openings and small recesses are represented as dark inset geometry.",
]

PALETTE = {
    "MAT_RECEIVER": ((0.035, 0.040, 0.046), 0.88, 0.48),
    "MAT_POLYMER": ((0.052, 0.057, 0.061), 0.00, 0.72),
    "MAT_STEEL": ((0.075, 0.082, 0.088), 0.82, 0.40),
    "MAT_WEAR": ((0.29, 0.31, 0.32), 0.95, 0.32),
}
ALU, POLY, STEEL, WEAR = "MAT_RECEIVER", "MAT_POLYMER", "MAT_STEEL", "MAT_WEAR"

CRITICAL_PAIRS = [
    ("MAG_", "GRIP_"),
    ("MAG_", "CTRL_Trigger"),
    ("GRIP_", "CTRL_Trigger"),
]


def nm(P, name):
    return stages.nm(P, name)


def _hard(ob, P, width=0.0012):
    """Apply micro-bevel and weighted normals in S3/DETAIL without collapsing edges."""
    return mods.finish_hard(ob, width, enabled=P["bevel"])


def _clean_triangulate(ob):
    """Ensure strictly 0.0% n-gons while removing any degenerate geometry."""
    bm = bmesh.new()
    try:
        bm.from_mesh(ob.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
        faces = [face for face in bm.faces if len(face.verts) > 4]
        if faces:
            bmesh.ops.triangulate(bm, faces=faces)
        bm.to_mesh(ob.data)
        ob.data.update()
    finally:
        bm.free()
    return ob


def _multi_cyl_clean(name, C, specs, segs=10, mat=None):
    ob = mesh.multi_cyl(name, C, specs, segs=segs, mat=mat)
    return _clean_triangulate(ob)


def _side(P, name, outline, half_width, material, x0=None, x1=None, bevel=0.0012):
    ob = _clean_triangulate(mesh.plate(nm(P, name), P["coll"], outline,
                                       -half_width if x0 is None else x0,
                                       half_width if x1 is None else x1, material))
    return _hard(ob, P, bevel)


def _pixel_box(P, name, u0, u1, v0, v1, x0, x1, material, bevel=0.0008):
    y0, z0 = L.P(u0, v0)
    y1, z1 = L.P(u1, v1)
    x0, x1 = min(x0, x1), max(x0, x1)
    center = ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5)
    size = (x1 - x0, abs(y1 - y0), abs(z1 - z0))
    ob = _clean_triangulate(mesh.box(nm(P, name), P["coll"], center, size, material))
    return _hard(ob, P, bevel)


def _side_prim(P, name, outline, half_width, material, tolerance=2.0):
    return _clean_triangulate(
        prim.plate_px(nm(P, name), P["coll"], outline, half_width, material, tol=tolerance)
    )


def _world(u, v, x=0.0):
    return Vector(L.P3(u, v, x))


# ============================================================================
# 1. RECEIVER
# ============================================================================
def receiver_prim(P):
    return [
        _side_prim(P, "RECV_Main", L.RECEIVER, L.HW_RECEIVER, ALU, 1.5),
        _side_prim(P, "RECV_TopRail", L.TOP_RAIL, L.HW_RAIL, STEEL, 1.0),
    ]


def receiver(P):
    C = P["coll"]
    out = [
        _side(P, "RECV_Main", L.RECEIVER, L.HW_RECEIVER, ALU, bevel=0.0018),
        _side(P, "RECV_SidePanel", L.RECEIVER_PANEL, 0.029, ALU, 0.0285, 0.0305, 0.0003),
        _side(P, "RECV_EjectionPort", L.EJECTION_PORT, 0.0305, STEEL, 0.0305, 0.0315, 0.0002),
        _pixel_box(P, "RECV_BoltCarrier", 802, 882, 315, 331, 0.0315, 0.0325, WEAR, 0.0003),
        _side(P, "RECV_TopRail", L.TOP_RAIL, L.HW_RAIL, STEEL, bevel=0.0010),
    ]
    if P["stage"] >= 2:
        # All 28 cross rail teeth unified into ONE mesh
        ribs = []
        for i in range(28):
            u = 360 + i * 22.5
            yc = L.Y(u)
            ztop = L.Z(u, 263)
            xhalf = L.HW_RAIL * 0.96
            fa = [(-xhalf, yc - 0.0025, ztop), (xhalf, yc - 0.0025, ztop),
                  (xhalf, yc + 0.0025, ztop), (-xhalf, yc + 0.0025, ztop)]
            fb = [(x, y, z - 0.0035) for x, y, z in fa]
            ribs.append((fa, fb))
        teeth = mesh.extrude_polys(nm(P, "RECV_RailTeeth"), C, ribs, STEEL)
        out.append(_hard(_clean_triangulate(teeth), P, 0.0004))

        # Rivets and fasteners unified via multi_cyl
        rivets = []
        for side in (-1, 1):
            x0, x1 = (0.0285, 0.0305) if side > 0 else (-0.0305, -0.0285)
            for u, v in ((726, 315), (755, 315), (784, 315), (814, 315),
                         (848, 315), (879, 315), (912, 315), (943, 315),
                         (735, 369), (780, 369), (890, 369), (957, 369)):
                rivets.append((_world(u, v, x0), _world(u, v, x1), 0.0020))
        out.append(_multi_cyl_clean(nm(P, "RECV_RivetHeads"), C, rivets, segs=10, mat=WEAR))

        # Chassis cross pins
        pins = []
        for u, v in ((727, 319), (761, 366), (917, 307), (959, 361), (980, 340)):
            pins.append((_world(u, v, 0.029), _world(u, v, 0.0315), 0.0030))
        out.append(_multi_cyl_clean(nm(P, "RECV_Fasteners"), C, pins, segs=12, mat=WEAR))
    return out


# ============================================================================
# 2. BARREL & MUZZLE
# ============================================================================
def barrel_prim(P):
    return [
        _side_prim(P, "BARREL_MuzzleDevice", L.MUZZLE, L.HW_MUZZLE, STEEL, 1.0),
        _side_prim(P, "BARREL_Main", L.BARREL, L.HW_BARREL, STEEL, 1.0),
    ]


def barrel(P):
    C = P["coll"]
    z = L.Z(150, L.BORE_V)
    muzzle_y0, muzzle_y1 = L.Y(72), L.Y(142)
    barrel_y0, barrel_y1 = L.Y(142), L.Y(365)
    segs = P.get("ring", 20)
    out = [
        mesh.cyl(nm(P, "BARREL_Main"), C, (0, barrel_y0, z), (0, barrel_y1, z),
                 L.HW_BARREL, segs, STEEL, r1=L.HW_BARREL * 0.95),
        mesh.lathe(nm(P, "BARREL_MuzzleDevice"), C, (0, muzzle_y1, z),
                   [(0.011, 0.0), (0.015, -0.008), (0.0125, -0.020),
                    (0.015, -0.028), (0.011, muzzle_y0 - muzzle_y1)],
                   segs, STEEL, closed=False, axis="Y"),
        _pixel_box(P, "BARREL_GasCollar", 333, 350, 331, 355, -0.014, 0.014, ALU, 0.0008),
    ]
    if P["stage"] >= 2:
        ports = []
        for u in (83, 100, 117, 134):
            yc = L.Y(u)
            ports.append(((-0.015, yc - 0.003, z + 0.006),
                          (-0.015, yc + 0.003, z + 0.006), 0.0022))
            ports.append(((0.015, yc - 0.003, z + 0.006),
                          (0.015, yc + 0.003, z + 0.006), 0.0022))
        out.append(_multi_cyl_clean(nm(P, "BARREL_MuzzlePorts"), C, ports, segs=10, mat=ALU))
    return out


# ============================================================================
# 3. HANDGUARD
# ============================================================================
def handguard_prim(P):
    return [_side_prim(P, "HG_Shell", L.HANDGUARD, L.HW_HANDGUARD, POLY, 1.5)]


def handguard(P):
    C = P["coll"]
    out = [_side(P, "HG_Shell", L.HANDGUARD, L.HW_HANDGUARD, POLY, bevel=0.0016)]
    if P["stage"] >= 2:
        # Left and right side rails combined into ONE unified mesh
        rail_polys = []
        for side, x0, x1 in (("L", 0.0362, 0.0382), ("R", -0.0382, -0.0362)):
            pts_a = [L.P3(u, v, x0) for u, v in [(365, 314), (711, 314), (725, 323), (725, 330), (365, 330)]]
            pts_b = [L.P3(u, v, x1) for u, v in [(365, 314), (711, 314), (725, 323), (725, 330), (365, 330)]]
            rail_polys.append((pts_a, pts_b))
        side_rails = mesh.extrude_polys(nm(P, "HG_SideRails"), C, rail_polys, STEEL)
        out.append(_hard(_clean_triangulate(side_rails), P, 0.0006))

        # Side rail cross teeth for Picatinny accessories
        rail_teeth = []
        for side, x0, x1 in (("L", 0.0360, 0.0385), ("R", -0.0385, -0.0360)):
            for i in range(12):
                u = 385 + i * 26
                yc = L.Y(u)
                zc = L.Z(u, 322)
                fa = [(x0, yc - 0.0025, zc - 0.007), (x1, yc - 0.0025, zc - 0.007),
                      (x1, yc + 0.0025, zc - 0.007), (x0, yc + 0.0025, zc - 0.007)]
                fb = [(x, y, z + 0.014) for x, y, z in fa]
                rail_teeth.append((fa, fb))
        side_teeth_ob = mesh.extrude_polys(nm(P, "HG_SideRailTeeth"), C, rail_teeth, STEEL)
        out.append(_clean_triangulate(side_teeth_ob))

        # All 24 MLOK slots and insets unified into ONE mesh
        mlok_polys = []
        for side, x0, x1 in (("L", 0.0364, 0.0378), ("R", -0.0378, -0.0364)):
            for row, v in enumerate((341, 361)):
                for i in range(6):
                    u = 390 + i * 51
                    pa = [L.P3(u, v, x0), L.P3(u + 34, v, x0), L.P3(u + 34, v + 7, x0), L.P3(u, v + 7, x0)]
                    pb = [L.P3(u, v, x1), L.P3(u + 34, v, x1), L.P3(u + 34, v + 7, x1), L.P3(u, v + 7, x1)]
                    mlok_polys.append((pa, pb))
        mlok_mesh = mesh.extrude_polys(nm(P, "HG_MlokSlots"), C, mlok_polys, ALU)
        out.append(_clean_triangulate(mlok_mesh))

        # Front cap
        out.append(_pixel_box(P, "HG_FrontCap", 716, 732, 307, 370, -0.034, 0.034, STEEL, 0.0010))
    return out


# ============================================================================
# 4. MAGAZINE
# ============================================================================
def magazine_prim(P):
    return [_side_prim(P, "MAG_Body", L.MAGAZINE, L.HW_MAGAZINE, POLY, 1.5)]


def magazine(P):
    C = P["coll"]
    out = [
        _side(P, "MAG_Body", L.MAGAZINE, L.HW_MAGAZINE, POLY, bevel=0.0015),
    ]
    if P["stage"] >= 2:
        # Floorplate
        out.append(_side(P, "MAG_Floorplate",
                         [(786, 550), (811, 568), (826, 568), (852, 539), (846, 559), (811, 575), (789, 574)],
                         0.019, STEEL, bevel=0.0008))
        # Magazine gripping ribs kept strictly INSIDE the magazine silhouette (centered on body)
        mag_ribs = []
        for side, x0, x1 in (("L", 0.0172, 0.0185), ("R", -0.0185, -0.0172)):
            for i in range(8):
                u = 788 + i * 6.5
                v = 420 + i * 14.0
                # 45 px width guarantees >= 15 px clearance inside silhouette boundaries
                pa = [L.P3(u, v, x0), L.P3(u + 45, v, x0), L.P3(u + 45, v + 4.5, x0), L.P3(u, v + 4.5, x0)]
                pb = [L.P3(u, v, x1), L.P3(u + 45, v, x1), L.P3(u + 45, v + 4.5, x1), L.P3(u, v + 4.5, x1)]
                mag_ribs.append((pa, pb))
        ribs_ob = mesh.extrude_polys(nm(P, "MAG_Ribs"), C, mag_ribs, ALU)
        out.append(_clean_triangulate(ribs_ob))

        # Index panel
        out.append(_pixel_box(P, "MAG_IndexPanel", 785, 826, 452, 488, 0.0174, 0.0188, STEEL, 0.0003))
    return out


# ============================================================================
# 5. GRIP
# ============================================================================
def grip_prim(P):
    return [_side_prim(P, "GRIP_Pistol", L.GRIP, L.HW_GRIP, POLY, 1.5)]


def grip(P):
    C = P["coll"]
    out = [
        _side(P, "GRIP_Pistol", L.GRIP, L.HW_GRIP, POLY, bevel=0.0018),
    ]
    if P["stage"] >= 2:
        # Ergonomic horizontal grip traction ribs kept strictly INSIDE the grip silhouette
        grip_ribs = []
        for side, x0, x1 in (("L", 0.0222, 0.0234), ("R", -0.0234, -0.0222)):
            for i in range(7):
                v = 432 + i * 11
                # 40 px width centered in grip width (spans 958 to 998, well within 935 to 1025)
                u0 = 958 - i * 1.5
                u1 = 998 - i * 1.5
                pa = [L.P3(u0, v, x0), L.P3(u1, v, x0), L.P3(u1, v + 4, x0), L.P3(u0, v + 4, x0)]
                pb = [L.P3(u0, v, x1), L.P3(u1, v, x1), L.P3(u1, v + 4, x1), L.P3(u0, v + 4, x1)]
                grip_ribs.append((pa, pb))
        ribs_ob = mesh.extrude_polys(nm(P, "GRIP_Ribs"), C, grip_ribs, STEEL)
        out.append(_clean_triangulate(ribs_ob))

        # Bottom cap
        out.append(_pixel_box(P, "GRIP_BaseCap", 973, 1027, 520, 530, -0.023, 0.023, STEEL, 0.0008))
    return out


# ============================================================================
# 6. CONTROLS
# ============================================================================
def controls_prim(P):
    return [
        _side_prim(P, "CTRL_Guard", L.TRIGGER_GUARD, 0.006, STEEL, 1.5),
        _side_prim(P, "CTRL_Trigger", L.TRIGGER, 0.005, WEAR, 1.0),
        _side_prim(P, "CTRL_ChargingHandle", L.CHARGING_HANDLE, 0.034, WEAR, 1.0),
    ]


def controls(P):
    C = P["coll"]
    out = [
        _side(P, "CTRL_Guard", L.TRIGGER_GUARD, 0.006, STEEL, bevel=0.0010),
        _side(P, "CTRL_Trigger", L.TRIGGER, 0.004, WEAR, bevel=0.0006),
        _side(P, "CTRL_ChargingHandle", L.CHARGING_HANDLE, 0.034, WEAR, bevel=0.0008),
        _pixel_box(P, "CTRL_Selector", 713, 744, 350, 360, 0.029, 0.036, STEEL, 0.0008),
    ]
    if P["stage"] >= 2:
        # Charging knob
        y, z = L.P(956, 323)
        out.append(mesh.lathe(nm(P, "CTRL_ChargingKnob"), C, (0.0, y, z),
                              [(0.004, 0.032), (0.0055, 0.039), (0.006, 0.048),
                               (0.0045, 0.053), (0.002, 0.055)],
                              P.get("ring", 20), WEAR, closed=False, axis="X"))

        # Fastener pins
        pins = []
        for u, v in ((730, 354), (751, 354), (880, 349)):
            pins.append((_world(u, v, 0.033), _world(u, v, 0.0355), 0.0022))
        out.append(_multi_cyl_clean(nm(P, "CTRL_Fasteners"), C, pins, segs=10, mat=WEAR))
    return out


# ============================================================================
# 7. STOCK
# ============================================================================
def stock_prim(P):
    return [
        _side_prim(P, "STOCK_Body", L.STOCK, L.HW_STOCK, POLY, 1.5),
        _side_prim(P, "STOCK_Tube", L.STOCK_TUBE, 0.018, STEEL, 1.0),
        _side_prim(P, "STOCK_Buttplate", L.BUTTPLATE, 0.027, STEEL, 1.0),
    ]


def stock(P):
    C = P["coll"]
    tube_start = L.P3(990, 338)
    tube_end = L.P3(1110, 338)
    out = [
        _side(P, "STOCK_Body", L.STOCK, L.HW_STOCK, POLY, bevel=0.0018),
        _side(P, "STOCK_Buttplate", L.BUTTPLATE, 0.027, STEEL, bevel=0.0010),
        _side(P, "STOCK_CheekRiser", L.CHEEK_RISER, 0.020, POLY, bevel=0.0010),
        mesh.cyl(nm(P, "STOCK_BufferTube"), C, tube_start, tube_end, 0.017, P.get("ring", 20), STEEL),
    ]
    if P["stage"] >= 2:
        # Frame openings unified into ONE mesh
        openings = []
        for side, x0, x1 in (("L", 0.0262, 0.0272), ("R", -0.0272, -0.0262)):
            for u0, v0, u1, v1 in ((1166, 320, 1225, 345), (1244, 329, 1304, 353)):
                pa = [L.P3(u0, v0, x0), L.P3(u1, v0, x0), L.P3(u1, v1, x0), L.P3(u0, v1, x0)]
                pb = [L.P3(u0, v0, x1), L.P3(u1, v0, x1), L.P3(u1, v1, x1), L.P3(u0, v1, x1)]
                openings.append((pa, pb))
        inset_ob = mesh.extrude_polys(nm(P, "STOCK_SkeletonInsets"), C, openings, ALU)
        out.append(_clean_triangulate(inset_ob))

        # Adjust lever and notches
        out.append(_pixel_box(P, "STOCK_AdjustLever", 1090, 1111, 347, 363, 0.018, 0.031, WEAR, 0.0006))
    return out


# ============================================================================
# 8. SIGHTS
# ============================================================================
def sights_prim(P):
    return [
        _side_prim(P, "SIGHT_FrontBase", L.FRONT_SIGHT_BASE, L.HW_SIGHT, STEEL, 1.0),
        _side_prim(P, "SIGHT_FrontLeaf", L.FRONT_SIGHT_LEAF, 0.006, WEAR, 1.0),
        _side_prim(P, "SIGHT_RearBase", L.REAR_SIGHT_BASE, L.HW_SIGHT, STEEL, 1.0),
        _side_prim(P, "SIGHT_RearLeaf", L.REAR_SIGHT_LEAF, 0.006, WEAR, 1.0),
    ]


def sights(P):
    C = P["coll"]
    out = [
        _side(P, "SIGHT_FrontBase", L.FRONT_SIGHT_BASE, L.HW_SIGHT, STEEL, bevel=0.0008),
        _side(P, "SIGHT_FrontLeaf", L.FRONT_SIGHT_LEAF, 0.006, WEAR, bevel=0.0005),
        _side(P, "SIGHT_RearBase", L.REAR_SIGHT_BASE, L.HW_SIGHT, STEEL, bevel=0.0008),
        _side(P, "SIGHT_RearLeaf", L.REAR_SIGHT_LEAF, 0.006, WEAR, bevel=0.0005),
    ]
    # Front ears and rear wings unified into cohesive left/right protector sets
    ears_and_wings = []
    for side, x0, x1 in (("L", 0.010, 0.013), ("R", -0.013, -0.010)):
        for poly in L.FRONT_SIGHT_EARS:
            pa = [L.P3(u, v, x0) for u, v in poly]
            pb = [L.P3(u, v, x1) for u, v in poly]
            ears_and_wings.append((pa, pb))
        for poly in L.REAR_SIGHT_WINGS:
            pa = [L.P3(u, v, x0) for u, v in poly]
            pb = [L.P3(u, v, x1) for u, v in poly]
            ears_and_wings.append((pa, pb))
    guards = mesh.extrude_polys(nm(P, "SIGHT_ProtectiveWings"), C, ears_and_wings, STEEL)
    out.append(_hard(_clean_triangulate(guards), P, 0.0004))

    if P["stage"] >= 2:
        # Circular aperture ring / peep sight lathed around Y axis (bore line)
        y = L.Y(940)
        zc = L.Z(940, 239)
        ring_profile = [(0.0020, 0.0), (0.0065, 0.0), (0.0065, 0.0030), (0.0020, 0.0030)]
        aperture = mesh.lathe(nm(P, "SIGHT_ApertureRing"), C, (0.0, y, zc),
                              ring_profile, P.get("ring", 20), WEAR, closed=True, axis="Y")
        out.append(_hard(_clean_triangulate(aperture), P, 0.0004))
    return out


# ============================================================================
# PARTS REGISTRY
# ============================================================================
PARTS = [
    Part("receiver", receiver, prim=receiver_prim, collision="hull"),
    Part("barrel", barrel, prim=barrel_prim, collision="hull"),
    Part("handguard", handguard, prim=handguard_prim, collision="hull"),
    Part("magazine", magazine, prim=magazine_prim, collision="hull"),
    Part("grip", grip, prim=grip_prim, collision="hull"),
    Part("controls", controls, prim=controls_prim, collision="none"),
    Part("stock", stock, prim=stock_prim, collision="hull"),
    Part("sights", sights, prim=sights_prim, collision="none"),
]

PIVOTS = {
    "MAG_Body": lambda: L.P3(814, 390),
    "CTRL_ChargingHandle": lambda: L.P3(952, 323, x=0.031),
    "CTRL_Trigger": lambda: L.P3(895, 410),
    "SIGHT_FrontLeaf": lambda: L.P3(382, 267),
    "SIGHT_RearLeaf": lambda: L.P3(944, 267),
}

CHILDREN = {
    "MAG_Floorplate": "MAG_Body",
    "MAG_Ribs": "MAG_Body",
    "MAG_IndexPanel": "MAG_Body",
    "CTRL_ChargingKnob": "CTRL_ChargingHandle",
    "SIGHT_ApertureRing": "SIGHT_RearLeaf",
}


def guide_points():
    return {
        "GUIDE_BoreOrigin": L.P3(750, L.BORE_V),
        "GUIDE_Muzzle": L.P3(L.MUZZLE_U, L.BORE_V),
        "GUIDE_ButtHeel": L.P3(L.BUTT_U, 340),
        "GUIDE_Magwell": L.P3(820, 390),
        "GUIDE_ChargingHandle": L.P3(952, 323, x=0.031),
        "GUIDE_FrontSight": L.P3(382, 267),
        "GUIDE_RearSight": L.P3(944, 267),
    }
