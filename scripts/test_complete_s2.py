import sys
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")
import bpy
import bmesh
from mathutils import Vector, Matrix
import math
import landmarks as L
from workbench.bl import mesh, materials, validate, mods, prim

palette = {
    "MAT_GUN_STEEL": ((0.08, 0.085, 0.09), 0.8, 0.35),
    "MAT_BARREL_CHROME": ((0.68, 0.68, 0.70), 0.95, 0.18),
    "MAT_WOOD_GRIP": ((0.28, 0.16, 0.09), 0.0, 0.65),
    "MAT_CONTROLS_DARK": ((0.045, 0.045, 0.05), 0.85, 0.28),
}
bpy.ops.wm.read_factory_settings(use_empty=True)
materials.ensure(palette)
mesh.set_ref(L.REF)
coll = "Collection"

def triangulate_ngons(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(me)
    me.update()
    bm.free()
    return ob

# 1. Slide
def build_slide():
    ob = mesh.plate("SLIDE_Main_LP", coll, L.SLIDE_POLY, -L.SLIDE_HALF_WIDTH, L.SLIDE_HALF_WIDTH, "MAT_GUN_STEEL")
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    max_z = max(v.co.z for v in bm.verts)
    top_edges = [e for e in bm.edges if abs(e.verts[0].co.z - max_z) < 0.002 and abs(e.verts[1].co.z - max_z) < 0.002
                 and any(abs(abs(v.co.x) - L.SLIDE_HALF_WIDTH) < 0.002 for v in e.verts)]
    if top_edges:
        bmesh.ops.bevel(bm, geom=top_edges, offset=0.0035, segments=6, profile=0.5, affect='EDGES')
    bm.to_mesh(me)
    me.update()
    bm.free()

    # Ejection port cutout (right side only)
    y0, z0 = L.P(1050.0, 310.0)
    y1, z1 = L.P(1400.0, 420.0)
    ob_port = mesh.box("TEMP_Port", coll, (-L.SLIDE_HALF_WIDTH, (y0+y1)/2, (z0+z1)/2),
                       (0.012, abs(y1-y0), abs(z1-z0)), "MAT_GUN_STEEL")
    mods.boolean(ob, ob_port, apply=True)
    bpy.data.objects.remove(ob_port, do_unlink=True)
    return triangulate_ngons(ob)

# 2. Frame
def build_frame():
    ob = mesh.plate("FRAME_Main_LP", coll, L.FRAME_POLY, -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")
    ob_cutter = mesh.plate("TEMP_Hole", coll, L.TRIGGER_HOLE_POLY, -0.05, 0.05, "MAT_GUN_STEEL")
    mods.boolean(ob, ob_cutter, apply=True)
    bpy.data.objects.remove(ob_cutter, do_unlink=True)

    # 14 Arched mainspring housing grooves on backstrap
    msh_cutters = []
    for i in range(14):
        u_m = 230.0 + i * 8.0
        v_m = 900.0 + i * 25.0
        y_m, z_m = L.P(u_m, v_m)
        c = mesh.box(f"TEMP_MSH_{i}", coll, (0.0, y_m, z_m), (L.FRAME_HALF_WIDTH * 2.2, 0.0012, 0.0008), "MAT_GUN_STEEL")
        c.rotation_euler = (0, math.radians(-15), 0)
        msh_cutters.append(c)

    for c in msh_cutters:
        mods.boolean(ob, c, apply=True)
        bpy.data.objects.remove(c, do_unlink=True)

    return triangulate_ngons(ob)

# 3. Barrel Group
def build_barrel():
    p_front = (0.0, *L.P(1872.6, 420.0))
    p_rear = (0.0, *L.P(385.0, 420.0))
    ob_barrel = mesh.cyl("BARREL_Cylinder_LP", coll, p_rear, p_front, L.BARREL_RADIUS, 32, "MAT_BARREL_CHROME")
    # Chamber hood (square locking block above chamber)
    hy, hz = L.P(1220.0, 360.0)
    ob_hood = mesh.box("BARREL_Hood_LP", coll, (0.0, hy, hz), (0.016, 0.035, 0.018), "MAT_BARREL_CHROME")

    # Bore hole
    p_bore_front = (0.0, p_front[1] - 0.002, p_front[2])
    p_bore_rear = (0.0, p_front[1] + 0.060, p_front[2])
    ob_bore = mesh.cyl("TEMP_Bore", coll, p_bore_front, p_bore_rear, 0.0057, 28, "MAT_BARREL_CHROME")
    mods.boolean(ob_barrel, ob_bore, apply=True)
    bpy.data.objects.remove(ob_bore, do_unlink=True)
    triangulate_ngons(ob_barrel)
    triangulate_ngons(ob_hood)

    # Bushing
    ob_bushing = mesh.cyl("BARREL_Bushing_LP", coll, (0, p_front[1] - 0.001, p_front[2]), (0, p_front[1] + 0.006, p_front[2]),
                          L.BARREL_RADIUS + 0.002, 32, "MAT_GUN_STEEL")
    triangulate_ngons(ob_bushing)

    # Plug
    p_plug = (0.0, *L.P(1872.6, 520.0))
    ob_plug = mesh.cyl("BARREL_Plug_LP", coll, (0, p_plug[1] - 0.001, p_plug[2]), (0, p_plug[1] + 0.035, p_plug[2]),
                       0.0055, 28, "MAT_GUN_STEEL")
    triangulate_ngons(ob_plug)
    return [ob_barrel, ob_hood, ob_bushing, ob_plug]

# 4. Grip Panels & Screws
def build_grips():
    ob_l = mesh.plate("GRIP_Panels_L_LP", coll, L.GRIP_PANEL_POLY,
                      L.FRAME_HALF_WIDTH, L.GRIP_HALF_WIDTH, "MAT_WOOD_GRIP")
    ob_r = mesh.plate("GRIP_Panels_R_LP", coll, L.GRIP_PANEL_POLY,
                      -L.GRIP_HALF_WIDTH, -L.FRAME_HALF_WIDTH, "MAT_WOOD_GRIP")

    for ob in [ob_l, ob_r]:
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        outer = [f for f in bm.faces if abs(f.normal.x) > 0.8]
        if outer:
            bmesh.ops.subdivide_edges(bm, edges=[e for f in outer for e in f.edges], cuts=10, use_grid_fill=True)
            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                bmesh.ops.triangulate(bm, faces=ngons)
        bm.to_mesh(me)
        me.update()
        bm.free()
        triangulate_ngons(ob)

    # 4 grip screws
    screw_locs_px = [(480.0, 680.0), (380.0, 1150.0)]
    screws = []
    for idx, (su, sv) in enumerate(screw_locs_px):
        sy, sz = L.P(su, sv)
        s_l = mesh.cyl(f"GRIP_Screw_L_{idx}_LP", coll, (L.FRAME_HALF_WIDTH, sy, sz), (L.GRIP_HALF_WIDTH + 0.0006, sy, sz),
                       0.0035, 24, "MAT_GUN_STEEL")
        s_r = mesh.cyl(f"GRIP_Screw_R_{idx}_LP", coll, (-L.FRAME_HALF_WIDTH, sy, sz), (-L.GRIP_HALF_WIDTH - 0.0006, sy, sz),
                       0.0035, 24, "MAT_GUN_STEEL")
        slot_l = mesh.box(f"TEMP_Slot_L_{idx}", coll, (L.GRIP_HALF_WIDTH + 0.0005, sy, sz), (0.0010, 0.0008, 0.0070), "MAT_GUN_STEEL")
        slot_r = mesh.box(f"TEMP_Slot_R_{idx}", coll, (-L.GRIP_HALF_WIDTH - 0.0005, sy, sz), (0.0010, 0.0008, 0.0070), "MAT_GUN_STEEL")
        mods.boolean(s_l, slot_l, apply=True)
        mods.boolean(s_r, slot_r, apply=True)
        bpy.data.objects.remove(slot_l, do_unlink=True)
        bpy.data.objects.remove(slot_r, do_unlink=True)
        triangulate_ngons(s_l)
        triangulate_ngons(s_r)
        screws.extend([s_l, s_r])

    return [ob_l, ob_r] + screws

# 5. Magazine
def build_magazine():
    # Magazine body inside grip
    my, mz = L.P(480.0, 950.0)
    ob_mag = mesh.box("MAG_Body_LP", coll, (0.0, my, mz), (0.0135, 0.032, 0.120), "MAT_GUN_STEEL")
    # Base floorplate
    by, bz = L.P(420.0, 1300.0)
    ob_base = mesh.box("MAG_BasePlate_LP", coll, (0.0, by, bz), (0.0150, 0.040, 0.004), "MAT_GUN_STEEL")
    triangulate_ngons(ob_mag)
    triangulate_ngons(ob_base)
    return [ob_mag, ob_base]

# 6. Controls
def build_controls():
    sy, sz = L.P(320.0, 540.0)
    ob_safety = mesh.box("CONTROLS_Safety_LP", coll, (L.FRAME_HALF_WIDTH + 0.0025, sy, sz),
                         (0.004, 0.022, 0.012), "MAT_CONTROLS_DARK")
    triangulate_ngons(ob_safety)

    ss_y, ss_z = L.P(780.0, 535.0)
    ob_slidestop = mesh.box("CONTROLS_SlideStop_LP", coll, (L.FRAME_HALF_WIDTH + 0.0020, ss_y, ss_z),
                            (0.0035, 0.030, 0.009), "MAT_CONTROLS_DARK")
    triangulate_ngons(ob_slidestop)

    mr_y, mr_z = L.P(750.0, 720.0)
    ob_magbtn = mesh.cyl("CONTROLS_MagRelease_LP", coll, (L.FRAME_HALF_WIDTH - 0.002, mr_y, mr_z),
                         (L.FRAME_HALF_WIDTH + 0.0035, mr_y, mr_z), 0.0042, 24, "MAT_CONTROLS_DARK")
    triangulate_ngons(ob_magbtn)
    return [ob_safety, ob_slidestop, ob_magbtn]

# 7. Trigger & Hammer & Sights
def build_trigger():
    ob = mesh.plate("TRIGGER_Shoe_LP", coll, L.TRIGGER_POLY,
                    -L.TRIGGER_HALF_WIDTH, L.TRIGGER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    # 3 Lightening holes
    for i in range(3):
        ty, tz = L.P(860.0, 650.0 + i * 45.0)
        h = mesh.cyl(f"TEMP_TrigHole_{i}", coll, (-0.01, ty, tz), (0.01, ty, tz), 0.0018, 16, "MAT_CONTROLS_DARK")
        mods.boolean(ob, h, apply=True)
        bpy.data.objects.remove(h, do_unlink=True)
    return [triangulate_ngons(ob)]

def build_hammer():
    ob = mesh.plate("HAMMER_Main_LP", coll, L.HAMMER_POLY,
                    -L.HAMMER_HALF_WIDTH, L.HAMMER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    py, pz = L.P(420.0, 540.0)
    ob_hole = mesh.cyl("TEMP_HamHole", coll, (-0.02, py, pz), (0.02, py, pz), 0.0040, 24, "MAT_CONTROLS_DARK")
    mods.boolean(ob, ob_hole, apply=True)
    bpy.data.objects.remove(ob_hole, do_unlink=True)
    return [triangulate_ngons(ob)]

def build_sights():
    ob_f = mesh.plate("SIGHTS_Front_LP", coll, L.SIGHT_FRONT_POLY, -0.0010, 0.0010, "MAT_CONTROLS_DARK")
    ob_r = mesh.plate("SIGHTS_Rear_LP", coll, L.SIGHT_REAR_POLY, -0.0070, 0.0070, "MAT_CONTROLS_DARK")
    ny, nz = L.P(530.0, 260.0)
    ob_notch = mesh.box("TEMP_Notch", coll, (0.0, ny, nz), (0.0026, 0.010, 0.004), "MAT_CONTROLS_DARK")
    mods.boolean(ob_r, ob_notch, apply=True)
    bpy.data.objects.remove(ob_notch, do_unlink=True)
    return [triangulate_ngons(ob_f), triangulate_ngons(ob_r)]

# Build all
objs = []
objs.append(build_slide())
objs.append(build_frame())
objs.extend(build_barrel())
objs.extend(build_grips())
objs.extend(build_magazine())
objs.extend(build_controls())
objs.extend(build_trigger())
objs.extend(build_hammer())
objs.extend(build_sights())

total_tris = sum(len(p.vertices) - 2 for ob in objs for p in ob.data.polygons)
print(f"\n==================================================")
print(f"Total objects: {len(objs)}")
print(f"Total tris: {total_tris}")
for ob in objs:
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"  {ob.name:30s}: {tris:4d} tris")

hy = validate.hygiene(objs)
print(f"Hygiene: {hy['total']}")
print(f"Worst degenerate: {hy['worst']['degenerate']}")
print(f"==================================================\n")
