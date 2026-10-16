"""
Part builders for PROP_Weapon_Spawner_Pad (Sci-fi Gym Floor Weapon Spawner).
Hexagonal floor-mounted metallic platform (1.5m diameter x 0.16m height) with beveled perimeter,
concentric glowing cyan emissive border strip, and central projector lenses to illuminate floating weapons.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim, scene

CATEGORY = "large_prop"
TARGET_DIMS = (1.500, 1.299, 0.160)    # (width, length, height) in metres -> gate U01
GROUND = True                          # lowest point at Z = 0.000 -> gate U03

PROFILES = {
    1: stages.profile(1, ring=8, stations=4, bevel=False),
    2: stages.profile(2, ring=20, stations=16, bevel=False),
    3: stages.profile(3, ring=32, stations=24, bevel=True),
}

GAME = dict(
    engine="godot",
    bake=True,
    tex=1024,
    lod=(0.5, 0.25),
    drop_small_m=0.02,
    uv_m=2.0
)

PALETTE = {
    "MAT_METAL_CHASSIS": dict(rgb=(0.12, 0.13, 0.15), metallic=0.88, roughness=0.38),
    "MAT_DECK_PLATE":    dict(rgb=(0.24, 0.26, 0.28), metallic=0.80, roughness=0.44),
    "MAT_EMISSIVE_CYAN": dict(rgb=(0.05, 0.82, 0.96), metallic=0.00, roughness=0.15,
                              emission=(0.05, 0.85, 1.0), emission_strength=8.0),
    "MAT_OPTICAL_GLASS": dict(rgb=(0.06, 0.10, 0.12), metallic=0.10, roughness=0.08, alpha=0.5),
}

CRITICAL_PAIRS = []
UNCERTAIN = []


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.003):
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def _hex_corners(radius, z):
    """6 corner vertices of a regular hexagon in the XY plane."""
    pts = []
    for k in range(6):
        ang = k * (math.pi / 3.0)
        pts.append(Vector((radius * math.cos(ang), radius * math.sin(ang), z)))
    return pts


# =============================================================================
# S1 PRIMITIVES
# =============================================================================
def base_prim(P):
    """S1: Bounding hexagonal base prism."""
    bm = bmesh.new()
    b0 = [_hex_corners(L.RADIUS_OUTER, 0.0)[k] for k in range(6)]
    b1 = [_hex_corners(L.RADIUS_DECK, L.HEIGHT_DECK)[k] for k in range(6)]
    v0 = [bm.verts.new(p) for p in b0]
    v1 = [bm.verts.new(p) for p in b1]
    # triangulate end caps to avoid n-gons
    c0 = bm.verts.new(Vector((0, 0, 0)))
    c1 = bm.verts.new(Vector((0, 0, L.HEIGHT_DECK)))
    for k in range(6):
        bm.faces.new((v0[(k + 1) % 6], v0[k], c0))
        bm.faces.new((v1[k], v1[(k + 1) % 6], c1))
        bm.faces.new((v0[k], v0[(k + 1) % 6], v1[(k + 1) % 6], v1[k]))
    return [mesh.finish(nm(P, "BASE_Platform"), bm, P["coll"], "MAT_METAL_CHASSIS", smooth=False)]


def deck_prim(P):
    """S1: Upper hexagonal deck slab."""
    bm = bmesh.new()
    b0 = [_hex_corners(L.RADIUS_DECK, L.HEIGHT_DECK)[k] for k in range(6)]
    b1 = [_hex_corners(L.RADIUS_DECK, L.HEIGHT_DECK + 0.005)[k] for k in range(6)]
    v0 = [bm.verts.new(p) for p in b0]
    v1 = [bm.verts.new(p) for p in b1]
    c0 = bm.verts.new(Vector((0, 0, L.HEIGHT_DECK)))
    c1 = bm.verts.new(Vector((0, 0, L.HEIGHT_DECK + 0.005)))
    for k in range(6):
        bm.faces.new((v0[(k + 1) % 6], v0[k], c0))
        bm.faces.new((v1[k], v1[(k + 1) % 6], c1))
        bm.faces.new((v0[k], v0[(k + 1) % 6], v1[(k + 1) % 6], v1[k]))
    return [mesh.finish(nm(P, "DECK_Plates"), bm, P["coll"], "MAT_DECK_PLATE", smooth=False)]


def emissive_strip_prim(P):
    """S1: Hexagonal emissive ribbon."""
    bm = bmesh.new()
    w = 0.015
    r0 = L.RADIUS_STRIP - w / 2
    r1 = L.RADIUS_STRIP + w / 2
    z = L.HEIGHT_DECK + 0.006
    p0 = _hex_corners(r0, z)
    p1 = _hex_corners(r1, z)
    v0 = [bm.verts.new(p) for p in p0]
    v1 = [bm.verts.new(p) for p in p1]
    for k in range(6):
        bm.faces.new((v0[k], v0[(k + 1) % 6], v1[(k + 1) % 6], v1[k]))
    return [mesh.finish(nm(P, "EMISSIVE_HexStrip"), bm, P["coll"], "MAT_EMISSIVE_CYAN", smooth=False)]


def projector_hub_prim(P):
    """S1: Central cylindrical well."""
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=16,
        radius1=L.RADIUS_WELL,
        radius2=L.RADIUS_WELL,
        depth=0.040,
        matrix=Matrix.Translation((0.0, 0.0, L.HEIGHT_DECK - 0.015))
    )
    return [mesh.finish(nm(P, "PROJECTOR_Hub"), bm, P["coll"], "MAT_METAL_CHASSIS", smooth=False)]


def lenses_prim(P):
    """S1: 5 projector lens cylinders."""
    bm = bmesh.new()
    # Central lens
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=12,
        radius1=L.RADIUS_CORE,
        radius2=L.RADIUS_CORE,
        depth=0.012,
        matrix=Matrix.Translation((0.0, 0.0, L.HEIGHT_TOTAL - 0.006))
    )
    # 4 satellite lenses
    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        lx = L.LENS_DIST * math.cos(ang)
        ly = L.LENS_DIST * math.sin(ang)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=12,
            radius1=L.RADIUS_LENS,
            radius2=L.RADIUS_LENS,
            depth=0.012,
            matrix=Matrix.Translation((lx, ly, L.HEIGHT_TOTAL - 0.006))
        )
    return [mesh.finish(nm(P, "LENSES_Projector"), bm, P["coll"], "MAT_OPTICAL_GLASS", smooth=False)]


# =============================================================================
# S2 LOWPOLY & S3 DETAIL BUILDERS
# =============================================================================
def base(P):
    """
    Main Hexagonal Base Chassis:
    - Vertical bottom perimeter lip (Z = 0 to 0.035m)
    - 45-degree chamfered skirt ring rising to deck level (Z = 0.035 to 0.145m)
    - 6 recessed technical vent panels with horizontal cooling slats
    """
    bm = bmesh.new()

    z0 = 0.000
    z1 = L.HEIGHT_BASE
    z2 = L.HEIGHT_DECK - 0.005

    r0 = _hex_corners(L.RADIUS_OUTER, z0)
    r1 = _hex_corners(L.RADIUS_OUTER, z1)
    r2 = _hex_corners(L.RADIUS_DECK, z2)

    v0 = [bm.verts.new(p) for p in r0]
    v1 = [bm.verts.new(p) for p in r1]
    v2 = [bm.verts.new(p) for p in r2]

    # Bottom floor face (triangulated fan from center to avoid n-gon)
    c0 = bm.verts.new(Vector((0, 0, z0)))
    for k in range(6):
        bm.faces.new((v0[(k + 1) % 6], v0[k], c0))

    # Vertical bottom lip faces
    for k in range(6):
        bm.faces.new((v0[k], v0[(k + 1) % 6], v1[(k + 1) % 6], v1[k]))

    # Chamfered side faces
    for k in range(6):
        bm.faces.new((v1[k], v1[(k + 1) % 6], v2[(k + 1) % 6], v2[k]))

    # Top boundary ring connecting to inner well
    rw = _hex_corners(L.RADIUS_WELL + 0.02, z2)
    vw = [bm.verts.new(p) for p in rw]
    for k in range(6):
        bm.faces.new((v2[k], v2[(k + 1) % 6], vw[(k + 1) % 6], vw[k]))

    # 6 Recessed Maintenance Vent Blocks with horizontal cooling slats
    vent_len = 0.28
    vent_h = 0.045
    for k in range(6):
        ang_mid = (k + 0.5) * (math.pi / 3.0)
        nx = math.cos(ang_mid)
        ny = math.sin(ang_mid)
        r_mid = (L.RADIUS_OUTER * math.cos(math.pi / 6) + L.RADIUS_DECK * math.cos(math.pi / 6)) / 2
        cx = r_mid * nx
        cy = r_mid * ny
        cz = (z1 + z2) / 2

        # Vent housing frame
        mat_vent = Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(ang_mid + math.pi / 2, 4, 'Z') @ Matrix.Diagonal((vent_len, 0.024, vent_h, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_vent)

        # 2 Horizontal cooling louvre slats inside each vent
        for dz_slat in (-0.010, 0.010):
            mat_slat = Matrix.Translation((cx, cy, cz + dz_slat)) @ Matrix.Rotation(ang_mid + math.pi / 2, 4, 'Z') @ Matrix.Diagonal((vent_len - 0.04, 0.028, 0.007, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_slat)

    ob = mesh.finish(nm(P, "BASE_Platform"), bm, P["coll"], "MAT_METAL_CHASSIS", smooth=True, sharp_angle=38.0)
    return [hard(ob, P, 0.003)]


def deck(P):
    """
    Upper Hexagonal Deck Plates:
    - 6 segmented radial trapezoid panels
    - Perimeter edge bevels and dual tech grip tread pattern plates
    """
    bm = bmesh.new()

    z_top = L.HEIGHT_DECK
    r_outer = L.RADIUS_DECK
    r_inner = L.RADIUS_WELL + 0.01

    p_outer = _hex_corners(r_outer, z_top)
    p_inner = _hex_corners(r_inner, z_top)

    vo = [bm.verts.new(p) for p in p_outer]
    vi = [bm.verts.new(p) for p in p_inner]

    # Deck panel quads
    for k in range(6):
        bm.faces.new((vi[k], vi[(k + 1) % 6], vo[(k + 1) % 6], vo[k]))

    # Dual Grip Tread / Tech Detail Plates on each sector
    for k in range(6):
        ang_mid = (k + 0.5) * (math.pi / 3.0)
        nx = math.cos(ang_mid)
        ny = math.sin(ang_mid)

        for r_frac in (0.75, 0.90):
            r_panel = (r_outer * r_frac + r_inner * (1.0 - r_frac + 0.2)) / 2
            px = r_panel * nx
            py = r_panel * ny
            mat_grip = Matrix.Translation((px, py, z_top + 0.002)) @ Matrix.Rotation(ang_mid + math.pi / 2, 4, 'Z') @ Matrix.Diagonal((0.24, 0.045, 0.004, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_grip)

    ob = mesh.finish(nm(P, "DECK_Plates"), bm, P["coll"], "MAT_DECK_PLATE", smooth=True, sharp_angle=35.0)
    return [hard(ob, P, 0.002)]


def emissive_strip(P):
    """
    Hexagonal Glowing Emissive Border Strip:
    - Recessed neon cyan light channel running around the deck perimeter
    """
    bm = bmesh.new()

    w = 0.018
    r_in = L.RADIUS_STRIP - w / 2
    r_out = L.RADIUS_STRIP + w / 2
    z = L.HEIGHT_DECK + 0.003

    p0 = _hex_corners(r_in, z)
    p1 = _hex_corners(r_out, z)
    p2 = _hex_corners(r_in, z - 0.006)
    p3 = _hex_corners(r_out, z - 0.006)

    v0 = [bm.verts.new(p) for p in p0]
    v1 = [bm.verts.new(p) for p in p1]
    v2 = [bm.verts.new(p) for p in p2]
    v3 = [bm.verts.new(p) for p in p3]

    for k in range(6):
        bm.faces.new((v0[k], v0[(k + 1) % 6], v1[(k + 1) % 6], v1[k]))
        bm.faces.new((v2[k], v2[(k + 1) % 6], v0[(k + 1) % 6], v0[k]))
        bm.faces.new((v1[k], v1[(k + 1) % 6], v3[(k + 1) % 6], v3[k]))

    ob = mesh.finish(nm(P, "EMISSIVE_HexStrip"), bm, P["coll"], "MAT_EMISSIVE_CYAN", smooth=True, sharp_angle=35.0)
    return [hard(ob, P, 0.001)]


def projector_hub(P):
    """
    Central Circular Projector Well & Lens Bezels:
    - Circular stepped well with outer bezel ring
    - 8 bolt accents along the perimeter ring
    - 4 raised satellite lens bezel housings with concentric flanges
    - Central core housing with stepped collar
    """
    bm = bmesh.new()
    segs = 28 if P["stage"] >= 2 else 16

    z_well_bot = L.HEIGHT_DECK - 0.035
    z_well_top = L.HEIGHT_DECK + 0.003

    # 1. Outer Circular Bezel Ring
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_WELL + 0.025,
        radius2=L.RADIUS_WELL + 0.025,
        depth=0.012,
        matrix=Matrix.Translation((0.0, 0.0, z_well_top - 0.006))
    )

    # 2. Recessed Well Floor Disc
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_WELL,
        radius2=L.RADIUS_WELL,
        depth=0.010,
        matrix=Matrix.Translation((0.0, 0.0, z_well_bot + 0.005))
    )

    # 3. Concentric Stepped Intermediate Ring
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_WELL * 0.72,
        radius2=L.RADIUS_WELL * 0.72,
        depth=0.016,
        matrix=Matrix.Translation((0.0, 0.0, z_well_bot + 0.008))
    )

    # 4. Central Core Raised Housing Bezel
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_CORE + 0.018,
        radius2=L.RADIUS_CORE + 0.018,
        depth=0.026,
        matrix=Matrix.Translation((0.0, 0.0, z_well_bot + 0.013))
    )

    # 5. 4 Satellite Projector Raised Lens Bezels
    lens_segs = 16 if P["stage"] >= 2 else 12
    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        lx = L.LENS_DIST * math.cos(ang)
        ly = L.LENS_DIST * math.sin(ang)
        # Base collar
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=lens_segs,
            radius1=L.RADIUS_LENS + 0.015,
            radius2=L.RADIUS_LENS + 0.015,
            depth=0.026,
            matrix=Matrix.Translation((lx, ly, z_well_bot + 0.013))
        )
        # Top stepped rim
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=lens_segs,
            radius1=L.RADIUS_LENS + 0.018,
            radius2=L.RADIUS_LENS + 0.018,
            depth=0.006,
            matrix=Matrix.Translation((lx, ly, z_well_bot + 0.024))
        )

    # 6. 8 Fastener / Bolt Accents on outer ring
    for k in range(8):
        ang_bolt = k * (math.pi / 4.0)
        bx = (L.RADIUS_WELL + 0.012) * math.cos(ang_bolt)
        by = (L.RADIUS_WELL + 0.012) * math.sin(ang_bolt)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=8,
            radius1=0.008,
            radius2=0.008,
            depth=0.004,
            matrix=Matrix.Translation((bx, by, z_well_top))
        )

    ob = mesh.finish(nm(P, "PROJECTOR_Hub"), bm, P["coll"], "MAT_METAL_CHASSIS", smooth=True, sharp_angle=35.0)
    return [hard(ob, P, 0.002)]


def lenses(P):
    """
    Upward-Facing Projector Optics & Emitter Cores:
    - Central primary projector lens (height strictly capped at Z = 0.160m)
    - 4 satellite convex projector lenses (height strictly capped at Z = 0.160m)
    - Concentric emissive projector rings to illuminate floating weapons
    """
    bm = bmesh.new()
    segs = 24 if P["stage"] >= 2 else 16
    lens_segs = 16 if P["stage"] >= 2 else 12

    # 1. Central Projector Optic Disc
    z_core = L.HEIGHT_TOTAL - 0.006
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_CORE,
        radius2=L.RADIUS_CORE - 0.010,
        depth=0.012,
        matrix=Matrix.Translation((0.0, 0.0, z_core))
    )

    # Central inner glowing focal spot
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=segs,
        radius1=L.RADIUS_CORE * 0.55,
        radius2=L.RADIUS_CORE * 0.55,
        depth=0.006,
        matrix=Matrix.Translation((0.0, 0.0, z_core + 0.003))
    )

    # 2. 4 Satellite Projector Optics
    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        lx = L.LENS_DIST * math.cos(ang)
        ly = L.LENS_DIST * math.sin(ang)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=lens_segs,
            radius1=L.RADIUS_LENS,
            radius2=L.RADIUS_LENS - 0.006,
            depth=0.012,
            matrix=Matrix.Translation((lx, ly, z_core))
        )
        # Inner emitter focal spot
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=lens_segs,
            radius1=L.RADIUS_LENS * 0.60,
            radius2=L.RADIUS_LENS * 0.60,
            depth=0.004,
            matrix=Matrix.Translation((lx, ly, z_core + 0.004))
        )

    ob = mesh.finish(nm(P, "LENSES_Projector"), bm, P["coll"], "MAT_OPTICAL_GLASS", smooth=True, sharp_angle=30.0)
    return [hard(ob, P, 0.001)]


# =============================================================================
# REGISTRY
# =============================================================================
PARTS = [
    Part("base", base, prim=base_prim, collision="box"),
    Part("deck", deck, prim=deck_prim, collision="box"),
    Part("emissive_strip", emissive_strip, prim=emissive_strip_prim, collision="none"),
    Part("projector_hub", projector_hub, prim=projector_hub_prim, collision="box"),
    Part("lenses", lenses, prim=lenses_prim, collision="none"),
]

PIVOTS = {}
CHILDREN = {}


def after_build(stage, objs):
    """Assign multi-materials to lenses: optical glass surface + glowing emissive core."""
    from workbench.bl import materials
    if stage in (2, 3):
        for ob in objs:
            bname = stages.base_name(ob.name)
            if bname == "LENSES_Projector":
                mat_list = ["MAT_OPTICAL_GLASS", "MAT_EMISSIVE_CYAN"]
                def lens_face_idx(p):
                    dist = math.hypot(p.center.x, p.center.y)
                    if dist < L.RADIUS_CORE * 0.65 and p.center.z > L.HEIGHT_TOTAL - 0.006:
                        return 1
                    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
                        sx = L.LENS_DIST * math.cos(ang)
                        sy = L.LENS_DIST * math.sin(ang)
                        if math.hypot(p.center.x - sx, p.center.y - sy) < L.RADIUS_LENS * 0.65 and p.center.z > L.HEIGHT_TOTAL - 0.006:
                            return 1
                    return 0
                materials.assign_by_face(ob, mat_list, lens_face_idx)


def guide_points():
    return {
        "ORIGIN": Vector((0.0, 0.0, 0.0)),
        "TOP_CENTER": Vector((0.0, 0.0, L.HEIGHT_TOTAL)),
        "OUTER_HEX": Vector((L.RADIUS_OUTER, 0.0, 0.0)),
    }
