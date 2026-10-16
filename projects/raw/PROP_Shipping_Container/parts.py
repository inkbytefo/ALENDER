"""
Part builders for PROP_Shipping_Container (staged pipeline, docs/01_WORKFLOW.md).
Standard 20ft ISO corrugated steel shipping container (2.4m W x 6.0m L x 2.6m H).
Industrial crisp corrugated walls, heavy locking bar doors on BOTH ends,
stacking corner casting blocks, forklift pockets, and PBR materials.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim, scene

CATEGORY = "large_prop"                # key of workbench.tables.BUDGETS
TARGET_DIMS = (2.400, 6.000, 2.600)    # (width, length, height) in metres -> gate U01
GROUND = True                          # lowest point at Z = 0.000 -> gate U03

PROFILES = {
    1: stages.profile(1, ring=8, stations=4, bevel=False),
    2: stages.profile(2, ring=12, stations=12, bevel=False),
    3: stages.profile(3, ring=16, stations=20, bevel=True),
}

GAME = dict(
    engine="godot",
    bake=True,
    tex=1024,
    lod=(0.5, 0.25),
    drop_small_m=0.03,
    uv_m=2.0
)

# Color variants: "SLATE_BLUE" (default) or "RUST_ORANGE"
COLOR_VARIANT = "SLATE_BLUE"

if COLOR_VARIANT == "RUST_ORANGE":
    BODY_COLOR = (0.42, 0.18, 0.07)   # Industrial rust-orange oxide paint
else:
    BODY_COLOR = (0.18, 0.24, 0.29)   # Desaturated industrial slate blue-grey

PALETTE = {
    "MAT_CONTAINER_BODY": dict(rgb=BODY_COLOR, metallic=0.15, roughness=0.48),
    "MAT_CONTAINER_RUST": dict(rgb=(0.38, 0.16, 0.07), metallic=0.55, roughness=0.78),
    "MAT_HARDWARE_STEEL": dict(rgb=(0.38, 0.40, 0.42), metallic=0.90, roughness=0.32),
    "MAT_RUBBER_SEAL":    dict(rgb=(0.04, 0.04, 0.045), metallic=0.00, roughness=0.88),
}

CRITICAL_PAIRS = []
UNCERTAIN = []


def nm(P, name):
    return stages.nm(P, name)


def hard(ob, P, bevel=0.004):
    """Hard-surface finish: bevel + weighted normals in S3. Never subsurf."""
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


# =============================================================================
# S1 PRIMITIVES
# =============================================================================
def frame_prim(P):
    """S1: Bounding posts, rails and sills."""
    bm = bmesh.new()
    # 4 corner posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * (L.HALF_W - L.POST_SIZE / 2)
            cy = sy * (L.HALF_L - L.POST_SIZE / 2)
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, cy, L.HEIGHT / 2)) @ Matrix.Diagonal((L.POST_SIZE, L.POST_SIZE, L.HEIGHT, 1.0)))
    # 2 bottom side rails
    for sx in (-1, 1):
        cx = sx * (L.HALF_W - 0.05)
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, 0.0, L.RAIL_BOT_H / 2)) @ Matrix.Diagonal((0.08, L.LENGTH - 2 * L.CASTING_L, L.RAIL_BOT_H, 1.0)))
    # 2 top side rails
    for sx in (-1, 1):
        cx = sx * (L.HALF_W - 0.05)
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx, 0.0, L.HEIGHT - L.RAIL_TOP_H / 2)) @ Matrix.Diagonal((0.08, L.LENGTH - 2 * L.CASTING_L, L.RAIL_TOP_H, 1.0)))
    # Front and rear sills/headers
    for sy in (-1, 1):
        cy = sy * (L.HALF_L - 0.06)
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.0, cy, L.SILL_H / 2)) @ Matrix.Diagonal((L.WIDTH - 2 * L.POST_SIZE, 0.08, L.SILL_H, 1.0)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.0, cy, L.HEIGHT - L.HEADER_H / 2)) @ Matrix.Diagonal((L.WIDTH - 2 * L.POST_SIZE, 0.08, L.HEADER_H, 1.0)))
    return [mesh.finish(nm(P, "FRAME_Main"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=False)]


def castings_prim(P):
    """S1: 8 corner casting blocks at exact bbox corners."""
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                cx = sx * (L.HALF_W - L.CASTING_W / 2)
                cy = sy * (L.HALF_L - L.CASTING_L / 2)
                cz = L.CASTING_H / 2 if sz == 0 else L.HEIGHT - L.CASTING_H / 2
                mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((L.CASTING_W, L.CASTING_L, L.CASTING_H, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "CASTING_Corners"), bm, P["coll"], "MAT_HARDWARE_STEEL", smooth=False)]


def walls_prim(P):
    """S1: Flat side wall plates."""
    bm = bmesh.new()
    h = L.HEIGHT - L.RAIL_BOT_H - L.RAIL_TOP_H
    cz = L.RAIL_BOT_H + h / 2
    l = L.LENGTH - 2 * L.POST_SIZE
    for sx in (-1, 1):
        cx = sx * (L.HALF_W - 0.02)
        mat = Matrix.Translation((cx, 0.0, cz)) @ Matrix.Diagonal((0.04, l, h, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "WALL_Sides"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=False)]


def roof_prim(P):
    """S1: Flat roof plate."""
    bm = bmesh.new()
    mat = Matrix.Translation((0.0, 0.0, L.HEIGHT - 0.03)) @ Matrix.Diagonal((L.WIDTH - 2 * 0.08, L.LENGTH - 2 * 0.08, 0.04, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "ROOF_Main"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=False)]


def doors_front_prim(P):
    """S1: Front door slabs."""
    bm = bmesh.new()
    dh = L.HEIGHT - L.SILL_H - L.HEADER_H
    cz = L.SILL_H + dh / 2
    cy = -L.HALF_L + 0.04
    for sx in (-1, 1):
        cx = sx * (L.DOOR_LEAF_W / 2 + L.DOOR_GAP / 2)
        mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((L.DOOR_LEAF_W, 0.04, dh, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "DOOR_Front"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=False)]


def doors_rear_prim(P):
    """S1: Rear door slabs."""
    bm = bmesh.new()
    dh = L.HEIGHT - L.SILL_H - L.HEADER_H
    cz = L.SILL_H + dh / 2
    cy = L.HALF_L - 0.04
    for sx in (-1, 1):
        cx = sx * (L.DOOR_LEAF_W / 2 + L.DOOR_GAP / 2)
        mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((L.DOOR_LEAF_W, 0.04, dh, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "DOOR_Rear"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=False)]


def locking_bars_prim(P):
    """S1: Simplified rod prisms."""
    bm = bmesh.new()
    bh = L.HEIGHT - 0.20
    for sy in (-1, 1):
        y = sy * (L.HALF_L - 0.02)
        for sx in (-1, 1):
            for off in (L.BAR_OFFSET_OUTER, L.BAR_OFFSET_INNER):
                x = sx * (L.HALF_W - L.POST_SIZE + 0.05 - off)
                mat = Matrix.Translation((x, y, L.HEIGHT / 2)) @ Matrix.Diagonal((0.035, 0.035, bh, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return [mesh.finish(nm(P, "HARDWARE_LockingBars"), bm, P["coll"], "MAT_HARDWARE_STEEL", smooth=False)]


# =============================================================================
# S2 LOWPOLY & S3 DETAIL BUILDERS
# =============================================================================
def castings(P):
    """
    Corner casting blocks (ISO 1161):
    8 corner blocks with accurate outer envelope and characteristic recessed oval apertures
    for container twistlocks, lifting hooks, and 5.2m stacking pins.
    Outer dimensions strictly at target bbox (2.4m x 6.0m x 2.6m).
    """
    bm = bmesh.new()
    dx, dy, dz = L.CASTING_W, L.CASTING_L, L.CASTING_H

    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                # Center of this casting block
                cx = sx * (L.HALF_W - dx / 2)
                cy = sy * (L.HALF_L - dy / 2)
                cz = dz / 2 if sz == 0 else L.HEIGHT - dz / 2

                # Outer block
                mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((dx, dy, dz, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat)

                # Recessed twistlock apertures (kept safely within outer bounds)
                # Front/rear aperture
                ay = sy * (L.HALF_L - 0.010)
                mat_a = Matrix.Translation((cx, ay, cz)) @ Matrix.Diagonal((0.060, 0.012, 0.045, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_a)

                # Side aperture
                ax = sx * (L.HALF_W - 0.010)
                mat_s = Matrix.Translation((ax, cy, cz)) @ Matrix.Diagonal((0.012, 0.075, 0.045, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_s)

                # Stacking aperture on top/bottom
                az = 0.008 if sz == 0 else L.HEIGHT - 0.008
                mat_t = Matrix.Translation((cx, cy, az)) @ Matrix.Diagonal((0.070, 0.085, 0.012, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_t)

    ob = mesh.finish(nm(P, "CASTING_Corners"), bm, P["coll"], "MAT_HARDWARE_STEEL", smooth=True, sharp_angle=35.0)
    return [hard(ob, P, 0.003)]


def frame(P):
    """
    Structural container perimeter frame:
    - 4 hollow corner posts
    - 2 bottom side rails with forklift pockets cutouts and reinforcement tunnels
    - 2 top tubular side rails
    - Front and rear transverse sills and headers with rain gutters
    - 10 transverse bottom crossmembers
    """
    bm = bmesh.new()

    # 1. 4 Corner Posts (Z from casting bottom to casting top)
    post_z_bot = L.CASTING_H
    post_z_top = L.HEIGHT - L.CASTING_H
    post_h = post_z_top - post_z_bot
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * (L.HALF_W - L.POST_SIZE / 2)
            cy = sy * (L.HALF_L - L.POST_SIZE / 2)
            mat = Matrix.Translation((cx, cy, post_z_bot + post_h / 2)) @ Matrix.Diagonal((L.POST_SIZE, L.POST_SIZE, post_h, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat)

    # 2. Bottom Side Rails (with forklift pockets)
    rail_y_len = L.LENGTH - 2 * L.CASTING_L
    for sx in (-1, 1):
        rx = sx * (L.HALF_W - 0.045)
        # Rails split around forklift pockets with 1mm clearance gap to eliminate co-incident faces:
        y_bounds = [
            -L.HALF_L + L.CASTING_L,
            L.POCKET_Y_FRONT - L.POCKET_W / 2 - 0.002,
            L.POCKET_Y_FRONT + L.POCKET_W / 2 + 0.002,
            L.POCKET_Y_REAR - L.POCKET_W / 2 - 0.002,
            L.POCKET_Y_REAR + L.POCKET_W / 2 + 0.002,
            L.HALF_L - L.CASTING_L
        ]
        # Solid rail segments
        for y0, y1 in [(y_bounds[0], y_bounds[1]), (y_bounds[2], y_bounds[3]), (y_bounds[4], y_bounds[5])]:
            seg_l = y1 - y0
            seg_y = (y0 + y1) / 2
            mat = Matrix.Translation((rx, seg_y, L.RAIL_BOT_H / 2)) @ Matrix.Diagonal((0.08, seg_l, L.RAIL_BOT_H, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat)

        # Forklift pocket top and bottom bridging plates
        for py in (L.POCKET_Y_FRONT, L.POCKET_Y_REAR):
            # top flange over pocket
            top_h = L.RAIL_BOT_H - (L.POCKET_Z_BOT + L.POCKET_H)
            mat_top = Matrix.Translation((rx, py, L.RAIL_BOT_H - top_h / 2)) @ Matrix.Diagonal((0.078, L.POCKET_W - 0.002, top_h, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_top)
            # bottom flange under pocket
            mat_bot = Matrix.Translation((rx, py, L.POCKET_Z_BOT / 2 + 0.002)) @ Matrix.Diagonal((0.078, L.POCKET_W - 0.002, L.POCKET_Z_BOT, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_bot)

    # Forklift pocket through-sleeves
    for py in (L.POCKET_Y_FRONT, L.POCKET_Y_REAR):
        mat_sleeve = Matrix.Translation((0.0, py, L.POCKET_Z_BOT + L.POCKET_H / 2)) @ Matrix.Diagonal((L.WIDTH - 0.18, L.POCKET_W - 0.02, L.POCKET_H - 0.01, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_sleeve)

    # 3. Top Side Rails
    for sx in (-1, 1):
        rx = sx * (L.HALF_W - 0.045)
        mat = Matrix.Translation((rx, 0.0, L.HEIGHT - L.RAIL_TOP_H / 2)) @ Matrix.Diagonal((0.08, rail_y_len, L.RAIL_TOP_H, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)

    # 4. Front & Rear Sills and Headers
    for sy in (-1, 1):
        sy_sill = sy * (L.HALF_L - 0.065)
        sill_w = L.WIDTH - 2 * L.CASTING_W
        # Sill
        mat_sill = Matrix.Translation((0.0, sy_sill, L.SILL_H / 2)) @ Matrix.Diagonal((sill_w, 0.11, L.SILL_H, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_sill)
        # Header with rain gutter lip
        mat_hdr = Matrix.Translation((0.0, sy_sill, L.HEIGHT - L.HEADER_H / 2)) @ Matrix.Diagonal((sill_w, 0.11, L.HEADER_H, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_hdr)
        # Rain gutter lip overhang
        gy = sy * (L.HALF_L - 0.012)
        mat_gut = Matrix.Translation((0.0, gy, L.HEIGHT - 0.025)) @ Matrix.Diagonal((sill_w, 0.022, 0.025, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_gut)

    # 5. Floor Transverse Crossmembers (underside)
    cm_count = 10
    cm_ys = tables.lin(-L.HALF_L + 0.45, L.HALF_L - 0.45, cm_count)
    for cy in cm_ys:
        if abs(cy - L.POCKET_Y_FRONT) < 0.25 or abs(cy - L.POCKET_Y_REAR) < 0.25:
            continue
        mat_cm = Matrix.Translation((0.0, cy, 0.08)) @ Matrix.Diagonal((L.WIDTH - 0.22, 0.05, 0.10, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_cm)

    ob = mesh.finish(nm(P, "FRAME_Main"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=True, sharp_angle=38.0)
    return [hard(ob, P, 0.004)]


def walls(P):
    """
    Side Walls:
    Industrial crisp corrugated metal sheets on both sides.
    20 trapezoidal corrugation ribs along each 5.6m side wall,
    providing high visual fidelity and authentic container silhouette.
    """
    bm = bmesh.new()

    z_bot = L.RAIL_BOT_H
    z_top = L.HEIGHT - L.RAIL_TOP_H

    y_start = -L.HALF_L + L.POST_SIZE + 0.02
    y_end = L.HALF_L - L.POST_SIZE - 0.02
    total_len = y_end - y_start

    num_ribs = 20
    pitch = total_len / num_ribs

    frac_plateau = 0.28
    frac_slope = 0.18
    frac_valley = 0.36

    for sx in (-1, 1):
        base_x = sx * (L.HALF_W - 0.03)
        depth_dir = -sx  # inwards toward container interior

        verts_bot = []
        verts_top = []

        for i in range(num_ribs):
            y0 = y_start + i * pitch
            y1 = y0 + frac_plateau * pitch
            y2 = y1 + frac_slope * pitch
            y3 = y2 + frac_valley * pitch

            pts_y = [y0, y1, y2, y3]
            depths = [0.0, 0.0, L.WALL_RIB_DEPTH, L.WALL_RIB_DEPTH]

            for py, d in zip(pts_y, depths):
                px = base_x + depth_dir * d
                vb = bm.verts.new(Vector((px, py, z_bot)))
                vt = bm.verts.new(Vector((px, py, z_top)))
                verts_bot.append(vb)
                verts_top.append(vt)

        # Final closing point
        px_end = base_x
        verts_bot.append(bm.verts.new(Vector((px_end, y_end, z_bot))))
        verts_top.append(bm.verts.new(Vector((px_end, y_end, z_top))))

        # Create quad faces along the corrugation strip
        for j in range(len(verts_bot) - 1):
            v0 = verts_bot[j]
            v1 = verts_bot[j + 1]
            v2 = verts_top[j + 1]
            v3 = verts_top[j]
            if sx > 0:
                bm.faces.new((v0, v1, v2, v3))
            else:
                bm.faces.new((v3, v2, v1, v0))

    ob = mesh.finish(nm(P, "WALL_Sides"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=True, sharp_angle=42.0)
    return [hard(ob, P, 0.002)]


def roof(P):
    """
    Corrugated and crowned steel roof panel:
    Spans between top side rails with transverse corrugations and subtle arch for water drainage.
    """
    bm = bmesh.new()

    y_min = -L.HALF_L + L.HEADER_H
    y_max = L.HALF_L - L.HEADER_H

    num_waves = 22
    wave_pitch = (y_max - y_min) / num_waves

    xs = [-L.HALF_W + 0.06, -0.6, 0.0, 0.6, L.HALF_W - 0.06]
    crown_dz = [0.0, 0.015, 0.020, 0.015, 0.0]
    base_z = L.HEIGHT - 0.055

    row_verts = []
    for i in range(num_waves + 1):
        y = y_min + i * wave_pitch
        wave_z = (0.015 if (i % 2 == 1) else 0.0)
        current_row = []
        for x, c_dz in zip(xs, crown_dz):
            z = base_z + c_dz + wave_z
            current_row.append(bm.verts.new(Vector((x, y, z))))
        row_verts.append(current_row)

    for i in range(num_waves):
        r0 = row_verts[i]
        r1 = row_verts[i + 1]
        for j in range(len(xs) - 1):
            bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))

    ob = mesh.finish(nm(P, "ROOF_Main"), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=True, sharp_angle=40.0)
    return [hard(ob, P, 0.002)]


def _build_doors_for_end(P, end_sign, name_prefix):
    """
    Build double doors for one end of the container:
    - Left leaf & Right leaf
    - Perimeter rubber gasket seal
    - 5 horizontal stamped corrugations per leaf
    - 4 heavy strap hinges per leaf welded to corner posts
    """
    bm = bmesh.new()

    dh = L.HEIGHT - L.SILL_H - L.HEADER_H
    z_bot = L.SILL_H + 0.01
    z_top = L.HEIGHT - L.HEADER_H - 0.01
    door_cy = end_sign * (L.HALF_L - 0.050)

    for sx in (-1, 1):
        x_inner = sx * (L.DOOR_GAP / 2)
        x_outer = sx * (L.HALF_W - L.POST_SIZE + 0.02)
        leaf_cx = (x_inner + x_outer) / 2
        leaf_w = abs(x_outer - x_inner)

        # 1. Main door leaf plate
        mat_leaf = Matrix.Translation((leaf_cx, door_cy, (z_bot + z_top) / 2)) @ Matrix.Diagonal((leaf_w, 0.030, dh - 0.02, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_leaf)

        # 2. Horizontal pressed panel stamps (5 horizontal ribs)
        rib_zs = tables.lin(z_bot + 0.20, z_top - 0.20, 5)
        for rz in rib_zs:
            mat_rib = Matrix.Translation((leaf_cx, door_cy + end_sign * 0.010, rz)) @ Matrix.Diagonal((leaf_w - 0.08, 0.015, 0.10, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_rib)

        # 3. Outer Rubber Gasket Lip
        mat_gasket = Matrix.Translation((leaf_cx, door_cy + end_sign * 0.004, (z_bot + z_top) / 2)) @ Matrix.Diagonal((leaf_w + 0.018, 0.010, dh, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat_gasket)

        # 4. Strap Hinges (4 per leaf)
        post_x = sx * (L.HALF_W - L.POST_SIZE / 2)
        hinge_y = end_sign * (L.HALF_L - 0.025)
        for hz in L.HINGE_Z_POSITIONS:
            # Hinge pin barrel on post
            mat_pin = Matrix.Translation((post_x, hinge_y, hz)) @ Matrix.Diagonal((0.040, 0.035, 0.12, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_pin)
            # Strap plate extending onto the door leaf
            strap_cx = (post_x + x_outer - sx * 0.10) / 2
            strap_w = abs(post_x - (x_outer - sx * 0.10))
            mat_strap = Matrix.Translation((strap_cx, door_cy + end_sign * 0.018, hz)) @ Matrix.Diagonal((strap_w, 0.012, 0.065, 1.0))
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_strap)

    ob = mesh.finish(nm(P, name_prefix), bm, P["coll"], "MAT_CONTAINER_BODY", smooth=True, sharp_angle=38.0)
    return [hard(ob, P, 0.003)]


def doors_front(P):
    """Front double doors (Y = -3.0m)."""
    return _build_doors_for_end(P, -1, "DOOR_Front")


def doors_rear(P):
    """Rear double doors (Y = +3.0m)."""
    return _build_doors_for_end(P, 1, "DOOR_Rear")


def locking_bars(P):
    """
    Heavy locking bar assemblies on BOTH ends (8 bars total):
    - 4 vertical pipe rods per end (2 per door leaf)
    - Top & bottom forged locking cams
    - Cam keepers mounted to sill and header
    - Guide brackets / sleeve bushings securing each bar
    - Operating handle levers with security seal catches at Z = 1.05m
    """
    bm = bmesh.new()
    pipe_r = L.LOCKING_BAR_R
    bar_z_bot = L.SILL_H + 0.04
    bar_z_top = L.HEIGHT - L.HEADER_H - 0.04
    segs = 12 if P["stage"] >= 2 else 8

    for end_sign in (-1, 1):
        bar_y = end_sign * (L.HALF_L - 0.022)

        for sx in (-1, 1):
            x_outer_leaf = sx * (L.HALF_W - L.POST_SIZE + 0.02)
            bar_xs = [
                x_outer_leaf - sx * L.BAR_OFFSET_OUTER,
                x_outer_leaf - sx * L.BAR_OFFSET_INNER
            ]

            for bx in bar_xs:
                # 1. Vertical Pipe Rod
                bmesh.ops.create_cone(
                    bm,
                    cap_ends=True,
                    cap_tris=False,
                    segments=segs,
                    radius1=pipe_r,
                    radius2=pipe_r,
                    depth=bar_z_top - bar_z_bot,
                    matrix=Matrix.Translation((bx, bar_y, (bar_z_bot + bar_z_top) / 2))
                )

                # 2. Top and Bottom Locking Cams
                for cam_z, keeper_z in [(bar_z_top + 0.02, L.HEIGHT - L.HEADER_H + 0.02),
                                        (bar_z_bot - 0.02, L.SILL_H - 0.02)]:
                    # Cam head
                    mat_cam = Matrix.Translation((bx, bar_y + end_sign * 0.004, cam_z)) @ Matrix.Diagonal((0.040, 0.030, 0.050, 1.0))
                    bmesh.ops.create_cube(bm, size=1.0, matrix=mat_cam)
                    # Cam keeper bracket on frame
                    mat_keeper = Matrix.Translation((bx, end_sign * (L.HALF_L - 0.020), keeper_z)) @ Matrix.Diagonal((0.055, 0.025, 0.040, 1.0))
                    bmesh.ops.create_cube(bm, size=1.0, matrix=mat_keeper)

                # 3. Mounting Sleeve Brackets (3 per bar)
                bracket_zs = [L.SILL_H + 0.35, L.HANDLE_Z - 0.15, L.HEIGHT - L.HEADER_H - 0.35]
                for bz in bracket_zs:
                    mat_bracket = Matrix.Translation((bx, bar_y - end_sign * 0.008, bz)) @ Matrix.Diagonal((0.050, 0.028, 0.045, 1.0))
                    bmesh.ops.create_cube(bm, size=1.0, matrix=mat_bracket)

                # 4. Operating Latch Handle Lever
                handle_y = bar_y + end_sign * 0.010
                handle_len = 0.26
                mat_hub = Matrix.Translation((bx, handle_y, L.HANDLE_Z)) @ Matrix.Diagonal((0.038, 0.028, 0.050, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_hub)
                # Handle bar extending down
                mat_lever = Matrix.Translation((bx, handle_y + end_sign * 0.006, L.HANDLE_Z - handle_len / 2)) @ Matrix.Diagonal((0.018, 0.014, handle_len, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_lever)
                # Handle catch bracket
                mat_catch = Matrix.Translation((bx, bar_y - end_sign * 0.006, L.HANDLE_Z - handle_len + 0.03)) @ Matrix.Diagonal((0.042, 0.022, 0.035, 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=mat_catch)

    ob = mesh.finish(nm(P, "HARDWARE_LockingBars"), bm, P["coll"], "MAT_HARDWARE_STEEL", smooth=True, sharp_angle=35.0)
    return [hard(ob, P, 0.002)]


# =============================================================================
# REGISTRY
# =============================================================================
PARTS = [
    Part("castings", castings, prim=castings_prim, collision="box"),
    Part("frame", frame, prim=frame_prim, collision="box"),
    Part("walls", walls, prim=walls_prim, collision="box"),
    Part("roof", roof, prim=roof_prim, collision="box"),
    Part("doors_front", doors_front, prim=doors_front_prim, collision="box"),
    Part("doors_rear", doors_rear, prim=doors_rear_prim, collision="box"),
    Part("locking_bars", locking_bars, prim=locking_bars_prim, collision="none"),
]

# Moving / hinged parts:
PIVOTS = {
    "DOOR_Front": lambda: Vector((-L.HALF_W + L.POST_SIZE, -L.HALF_L + 0.035, L.HEIGHT / 2)),
    "DOOR_Rear":  lambda: Vector((-L.HALF_W + L.POST_SIZE, L.HALF_L - 0.035, L.HEIGHT / 2)),
}

CHILDREN = {
    "HARDWARE_LockingBars": "DOOR_Front",
}


def after_build(stage, objs):
    from workbench.bl import materials
    if stage in (2, 3):
        for ob in objs:
            bname = stages.base_name(ob.name)
            if bname in ("DOOR_Front", "DOOR_Rear"):
                mat_list = ["MAT_CONTAINER_BODY", "MAT_CONTAINER_RUST", "MAT_RUBBER_SEAL", "MAT_HARDWARE_STEEL"]
                def door_face_idx(p):
                    cz = p.center.z
                    cx = abs(p.center.x)
                    if cz < L.SILL_H + 0.16:
                        return 1  # MAT_CONTAINER_RUST (bottom dirt/rust accumulation)
                    if cx > L.HALF_W - L.POST_SIZE + 0.01:
                        return 3  # MAT_HARDWARE_STEEL (strap hinges)
                    if cz < L.SILL_H + 0.04 or cz > L.HEIGHT - L.HEADER_H - 0.04 or cx < 0.03:
                        return 2  # MAT_RUBBER_SEAL (perimeter door gasket)
                    return 0      # MAT_CONTAINER_BODY
                materials.assign_by_face(ob, mat_list, door_face_idx)
            elif bname == "FRAME_Main":
                mat_list = ["MAT_CONTAINER_BODY", "MAT_CONTAINER_RUST"]
                def frame_face_idx(p):
                    cz = p.center.z
                    cy = p.center.y
                    if cz < 0.16 or abs(cy - L.POCKET_Y_FRONT) < 0.22 or abs(cy - L.POCKET_Y_REAR) < 0.22:
                        return 1  # MAT_CONTAINER_RUST (bottom sill rust and forklift pockets)
                    return 0      # MAT_CONTAINER_BODY
                materials.assign_by_face(ob, mat_list, frame_face_idx)


def guide_points():
    return {
        "ORIGIN": Vector((0.0, 0.0, 0.0)),
        "TOP_CORNER": Vector((L.HALF_W, L.HALF_L, L.HEIGHT)),
    }

