"""
Procedural geometry builders for CHAR_Tactical_Mannequin.
Industrial shooting range target dummy on a steel floor stand with spring base.
Watertight BMesh topology, clean normals, low-poly geometry matching ~1600 triangles.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

from workbench.bl import mesh
import landmarks as L


def box_mesh(name, coll, center, size, mat=None, smooth=False):
    """Watertight box mesh."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    cx, cy, cz = center
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((cx, cy, cz)), verts=bm.verts)
    return mesh.finish(name, bm, coll, mat=mat, smooth=smooth, builder="box")


def cylinder_mesh(name, coll, p0, p1, radius, segs=8, mat=None, smooth=True):
    """Watertight cylinder between p0 and p1."""
    bm = bmesh.new()
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    if length < 1e-5:
        length = 0.01
        axis = Vector((0, 0, 1))
    axis_n = axis.normalized()
    n1, n2 = mesh.frame_for(axis_n)
    
    r0 = []
    r1 = []
    for s in range(segs):
        ang = 2.0 * math.pi * s / segs
        radial = math.cos(ang) * n1 + math.sin(ang) * n2
        r0.append(bm.verts.new(p0 + radius * radial))
        r1.append(bm.verts.new(p1 + radius * radial))
        
    for s in range(segs):
        bm.faces.new((r0[s], r1[s], r1[(s + 1) % segs], r0[(s + 1) % segs]))
        
    bm.faces.new(list(reversed(r0)))
    bm.faces.new(r1)
    return mesh.finish(name, bm, coll, mat=mat, smooth=smooth, builder="cylinder")


def build_stand(name, coll, mat_steel, mat_bolt, P):
    """4-legged steel cross floor stand with angled channels and foot pads."""
    bm = bmesh.new()
    detail = P.get("detail", True)
    
    # 1. Central box hub
    hub_cx, hub_cy, hub_cz = L.STAND_HUB_CENTER
    hsx, hsy, hsz = L.STAND_HUB_SIZE
    hub_box = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((hsx, hsy, hsz)), verts=hub_box["verts"])
    bmesh.ops.translate(bm, vec=Vector((hub_cx, hub_cy, hub_cz)), verts=hub_box["verts"])
    
    # 2. 4 Outrigger Legs (+X, -X, +Y, -Y)
    leg_dirs = [Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))]
    pad_w, pad_l, pad_h = L.FOOT_PAD_SIZE
    r_foot = L.FOOT_RADIUS
    
    for ldir in leg_dirs:
        pad_center = ldir * r_foot + Vector((0, 0, pad_h * 0.5))
        pad_size = Vector((pad_l if ldir.x != 0 else pad_w,
                           pad_w if ldir.x != 0 else pad_l,
                           pad_h))
        pbox = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=pad_size, verts=pbox["verts"])
        bmesh.ops.translate(bm, vec=pad_center, verts=pbox["verts"])
        
        start_pt = ldir * (hsx * 0.45) + Vector((0, 0, hub_cz - hsz * 0.2))
        end_pt = ldir * (r_foot - (pad_size.x * 0.3 if ldir.x != 0 else pad_size.y * 0.3)) + Vector((0, 0, pad_h))
        leg_vec = end_pt - start_pt
        leg_mid = (start_pt + end_pt) * 0.5
        
        cross_w = 0.035
        cross_h = 0.030
        lbox = bmesh.ops.create_cube(bm, size=1.0)
        thick = Vector((cross_w if ldir.x == 0 else leg_vec.length,
                        cross_w if ldir.y == 0 else leg_vec.length,
                        cross_h))
        bmesh.ops.scale(bm, vec=thick, verts=lbox["verts"])
        
        pitch = math.atan2(end_pt.z - start_pt.z, (end_pt - start_pt).to_2d().length)
        if ldir.x != 0:
            rot = Matrix.Rotation(pitch * ldir.x, 4, 'Y')
        else:
            rot = Matrix.Rotation(-pitch * ldir.y, 4, 'X')
        bmesh.ops.transform(bm, matrix=rot, verts=lbox["verts"])
        bmesh.ops.translate(bm, vec=leg_mid, verts=lbox["verts"])
        
        if detail:
            g_pts = [
                start_pt + Vector((0, 0, 0.03)),
                start_pt - ldir * 0.01,
                start_pt + ldir * 0.06 - Vector((0, 0, 0.02))
            ]
            perp = Vector((-ldir.y, ldir.x, 0)) * 0.006
            g1 = [bm.verts.new(p - perp) for p in g_pts]
            g2 = [bm.verts.new(p + perp) for p in g_pts]
            bm.faces.new(g1)
            bm.faces.new(list(reversed(g2)))
            for i in range(3):
                bm.faces.new((g1[i], g1[(i + 1) % 3], g2[(i + 1) % 3], g2[i]))
                
    ob = mesh.finish(name, bm, coll, mat=mat_steel, smooth=False, builder="build_stand")
    return ob


def build_spring(name, coll, mat_spring, mat_sleeve, P):
    """Heavy helical compression spring with square mounting sleeves."""
    bm = bmesh.new()
    turns = L.SPRING_TURNS
    steps_per_turn = 12
    total_steps = int(turns * steps_per_turn)
    radius = L.SPRING_RADIUS
    wire_r = L.SPRING_WIRE_RADIUS
    z_start = L.SPRING_Z_START
    z_end = L.SPRING_Z_END
    
    # 1. Lower mounting sleeve
    ls_box = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(L.SLEEVE_SIZE), verts=ls_box["verts"])
    bmesh.ops.translate(bm, vec=Vector(L.LOWER_SLEEVE_CENTER), verts=ls_box["verts"])
    
    # 2. Upper mounting sleeve
    us_box = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(L.SLEEVE_SIZE), verts=us_box["verts"])
    bmesh.ops.translate(bm, vec=Vector(L.UPPER_SLEEVE_CENTER), verts=us_box["verts"])
    
    # 3. Helical spring coils
    rings = []
    radial_segs = 6
    for i in range(total_steps + 1):
        t = i / total_steps
        ang = 2.0 * math.pi * turns * t
        z = z_start + (z_end - z_start) * t
        cx = radius * math.cos(ang)
        cy = radius * math.sin(ang)
        center = Vector((cx, cy, z))
        
        dz = (z_end - z_start) / (2.0 * math.pi * turns)
        tangent = Vector((-radius * math.sin(ang), radius * math.cos(ang), dz)).normalized()
        norm = Vector((math.cos(ang), math.sin(ang), 0.0)).normalized()
        binorm = tangent.cross(norm).normalized()
        
        ring = []
        for s in range(radial_segs):
            phi = 2.0 * math.pi * s / radial_segs
            p = center + wire_r * (math.cos(phi) * norm + math.sin(phi) * binorm)
            ring.append(bm.verts.new(p))
        rings.append(ring)
        
    for i in range(total_steps):
        r1 = rings[i]
        r2 = rings[i + 1]
        for s in range(radial_segs):
            bm.faces.new((r1[s], r2[s], r2[(s + 1) % radial_segs], r1[(s + 1) % radial_segs]))
            
    bm.faces.new([rings[0][s] for s in reversed(range(radial_segs))])
    bm.faces.new([rings[-1][s] for s in range(radial_segs)])
    
    ob = mesh.finish(name, bm, coll, mat=mat_spring, smooth=True, builder="build_spring")
    return ob


def build_spine(name, coll, mat_steel, P):
    """Vertical square spine channel on rear with 3 cross clamps."""
    bm = bmesh.new()
    
    scx, scy, scz = L.SPINE_CENTER
    ssx, ssy, ssz = L.SPINE_SIZE
    sbox = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((ssx, ssy, ssz)), verts=sbox["verts"])
    bmesh.ops.translate(bm, vec=Vector((scx, scy, scz)), verts=sbox["verts"])
    
    for cz in L.CLAMP_Z_LEVELS:
        cbox = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.100, 0.055, 0.035)), verts=cbox["verts"])
        bmesh.ops.translate(bm, vec=Vector((0.0, scy - 0.005, cz)), verts=cbox["verts"])
        
    ob = mesh.finish(name, bm, coll, mat=mat_steel, smooth=False, builder="build_spine")
    return ob


def build_target_body(name, coll, mat_yellow, P):
    """
    Humanoid silhouette backing plate with yellow border.
    Planar profile in XZ extruded across Y.
    """
    bm = bmesh.new()
    
    pts_half = [
        (0.060, 0.630),
        (0.070, 0.640),
        (0.170, 0.680),
        (0.190, 0.740),
        (0.175, 0.850),
        (0.160, 0.950),
        (0.180, 1.080),
        (0.200, 1.250),
        (0.340, 1.360),
        (0.100, 1.480),
        (0.080, 1.500),
        (0.080, 1.530),
        (0.115, 1.570),
        (0.115, 1.700),
        (0.065, 1.750),
        (0.000, 1.750),
    ]
    
    poly = []
    for x, z in pts_half[:-1]:
        poly.append(Vector((x, 0.0, z)))
    poly.append(Vector((0.0, 0.0, pts_half[-1][1])))
    for x, z in reversed(pts_half[:-1]):
        if x > 1e-4:
            poly.append(Vector((-x, 0.0, z)))
            
    half_th = L.BODY_THICKNESS * 0.5
    front_verts = [bm.verts.new(Vector((p.x, -half_th, p.z))) for p in poly]
    back_verts = [bm.verts.new(Vector((p.x, half_th, p.z))) for p in poly]
    
    n = len(poly)
    for i in range(n):
        bm.faces.new((front_verts[i], front_verts[(i + 1) % n], back_verts[(i + 1) % n], back_verts[i]))
        
    c_front = bm.verts.new(Vector((0.0, -half_th, 1.200)))
    c_back = bm.verts.new(Vector((0.0, half_th, 1.200)))
    for i in range(n):
        bm.faces.new((c_front, front_verts[(i + 1) % n], front_verts[i]))
        bm.faces.new((c_back, back_verts[i], back_verts[(i + 1) % n]))
        
    ob = mesh.finish(name, bm, coll, mat=mat_yellow, smooth=False, builder="build_target_body")
    return ob


def add_planar_plate(bm, poly, center, thickness, mat=None):
    """Helper to add an extruded polygon plate centered at `center`."""
    cx, cy, cz = center
    half_th = thickness * 0.5
    fverts = [bm.verts.new(Vector((cx + p[0], cy - half_th, cz + p[1]))) for p in poly]
    bverts = [bm.verts.new(Vector((cx + p[0], cy + half_th, cz + p[1]))) for p in poly]
    n = len(poly)
    for i in range(n):
        bm.faces.new((fverts[i], fverts[(i + 1) % n], bverts[(i + 1) % n], bverts[i]))
    cf = bm.verts.new(Vector((cx, cy - half_th, cz)))
    cb = bm.verts.new(Vector((cx, cy + half_th, cz)))
    for i in range(n):
        bm.faces.new((cf, fverts[(i + 1) % n], fverts[i]))
        bm.faces.new((cb, bverts[i], bverts[(i + 1) % n]))
    return fverts


def add_bullet_dent(bm, center_xyz, radius=0.009, depth=0.005, segs=6):
    """Adds a watertight indented bullet crater cone."""
    cx, cy, cz = center_xyz
    center_v = bm.verts.new(Vector((cx, cy + depth, cz)))
    rim_verts = []
    for s in range(segs):
        ang = 2.0 * math.pi * s / segs
        rx = cx + radius * math.cos(ang)
        rz = cz + radius * math.sin(ang)
        rim_verts.append(bm.verts.new(Vector((rx, cy - 0.001, rz))))
    for s in range(segs):
        bm.faces.new((center_v, rim_verts[s], rim_verts[(s + 1) % segs]))
    bm.faces.new(list(reversed(rim_verts)))


def build_hit_plates(name, coll, mat_plate, mat_bolt, P):
    """Bolted front hit plates: Head, Chest, Midsection, Left & Right Arms."""
    bm = bmesh.new()
    th = 0.008
    py = -L.BODY_THICKNESS * 0.5 - th * 0.5
    detail = P.get("detail", True)
    
    # 1. Head Octagonal Plate
    hw, hh, c = 0.090, 0.085, 0.035
    head_poly = [
        (-hw + c, -hh), (hw - c, -hh),
        (hw, -hh + c), (hw, hh - c),
        (hw - c, hh), (-hw + c, hh),
        (-hw, hh - c), (-hw, -hh + c)
    ]
    hc = Vector((0.0, py, L.HEAD_PLATE_CENTER[2]))
    add_planar_plate(bm, head_poly, hc, th)
    
    if detail:
        add_bullet_dent(bm, (0.025, py - th * 0.5, hc.z + 0.030))
        add_bullet_dent(bm, (-0.035, py - th * 0.5, hc.z - 0.020))
        add_bullet_dent(bm, (0.045, py - th * 0.5, hc.z - 0.040))
        
    # 2. Chest Octagonal Plate
    cw, ch, cc = 0.140, 0.130, 0.045
    chest_poly = [
        (-cw + cc, -ch), (cw - cc, -ch),
        (cw, -ch + cc), (cw, ch - cc),
        (cw - cc, ch), (-cw + cc, ch),
        (-cw, ch - cc), (-cw, -ch + cc)
    ]
    cc_pos = Vector((0.0, py, L.CHEST_PLATE_CENTER[2]))
    add_planar_plate(bm, chest_poly, cc_pos, th)
    
    if detail:
        add_bullet_dent(bm, (0.000, py - th * 0.5, cc_pos.z + 0.010))
        add_bullet_dent(bm, (-0.050, py - th * 0.5, cc_pos.z + 0.050))
        add_bullet_dent(bm, (0.060, py - th * 0.5, cc_pos.z - 0.040))
        add_bullet_dent(bm, (-0.030, py - th * 0.5, cc_pos.z - 0.060))
        
    # 3. Midsection Plate
    mw, mh, mc = 0.135, 0.140, 0.035
    mid_poly = [
        (-mw + mc, -mh), (mw - mc, -mh),
        (mw, -mh + mc), (mw, mh - mc),
        (mw - mc, mh), (-mw + mc, mh),
        (-mw, mh - mc), (-mw, -mh + mc)
    ]
    mc_pos = Vector((0.0, py, L.MID_PLATE_CENTER[2]))
    add_planar_plate(bm, mid_poly, mc_pos, th)
    
    if detail:
        add_bullet_dent(bm, (0.015, py - th * 0.5, mc_pos.z + 0.040))
        add_bullet_dent(bm, (-0.040, py - th * 0.5, mc_pos.z - 0.030))
        add_bullet_dent(bm, (0.035, py - th * 0.5, mc_pos.z - 0.050))
        
    # 4. Arm Hit Plates (Left and Right)
    aw, ah = 0.040, 0.140
    arm_poly = [
        (-aw + 0.015, -ah), (aw - 0.015, -ah),
        (aw, -ah + 0.020), (aw, ah - 0.020),
        (aw - 0.015, ah), (-aw + 0.015, ah),
        (-aw, ah - 0.020), (-aw, -ah + 0.020)
    ]
    la_pos = Vector((L.ARM_L_CENTER[0], py, L.ARM_L_CENTER[2]))
    add_planar_plate(bm, arm_poly, la_pos, th)
    if detail:
        add_bullet_dent(bm, (la_pos.x, py - th * 0.5, la_pos.z + 0.030))
        add_bullet_dent(bm, (la_pos.x + 0.010, py - th * 0.5, la_pos.z - 0.040))
        
    ra_pos = Vector((L.ARM_R_CENTER[0], py, L.ARM_R_CENTER[2]))
    add_planar_plate(bm, arm_poly, ra_pos, th)
    if detail:
        add_bullet_dent(bm, (ra_pos.x, py - th * 0.5, ra_pos.z + 0.030))
        add_bullet_dent(bm, (ra_pos.x - 0.010, py - th * 0.5, ra_pos.z - 0.040))
        
    ob = mesh.finish(name, bm, coll, mat=mat_plate, smooth=False, builder="build_hit_plates")
    return ob
