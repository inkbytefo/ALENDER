import sys
import bpy
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")

import landmarks as L
from workbench.bl import mesh, prim, materials
from workbench import stages

# Ensure materials
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

# 1. Slide
ob_slide = mesh.plate("SLIDE_Main_PRIM", coll, L.SLIDE_POLY, -L.SLIDE_HALF_WIDTH, L.SLIDE_HALF_WIDTH, "MAT_GUN_STEEL")

# 2. Frame
ob_frame = mesh.plate("FRAME_Main_PRIM", coll, L.FRAME_GRIP_POLY, -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")

# 3. Barrel
# Center of barrel in pixel coords: v ~ 420 (Z ~ 0.1264 m)
ob_barrel = prim.cyl_px("BARREL_Bushing_PRIM", coll, (1872.6, 420.0), (385.0, 420.0), L.BARREL_RADIUS, segs=12, mat="MAT_BARREL_CHROME")

# 4. Grip Panels
ob_grip_l = mesh.plate("GRIP_Panels_L_PRIM", coll, L.FRAME_GRIP_POLY, L.FRAME_HALF_WIDTH, L.GRIP_HALF_WIDTH, "MAT_WOOD_GRIP")
ob_grip_r = mesh.plate("GRIP_Panels_R_PRIM", coll, L.FRAME_GRIP_POLY, -L.GRIP_HALF_WIDTH, -L.FRAME_HALF_WIDTH, "MAT_WOOD_GRIP")

# 5. Controls (Trigger + Hammer)
ob_trigger = mesh.plate("TRIGGER_Shoe_PRIM", coll, L.TRIGGER_POLY, -L.TRIGGER_HALF_WIDTH, L.TRIGGER_HALF_WIDTH, "MAT_CONTROLS_DARK")
ob_hammer = mesh.plate("HAMMER_Spur_PRIM", coll, L.HAMMER_POLY, -L.HAMMER_HALF_WIDTH, L.HAMMER_HALF_WIDTH, "MAT_CONTROLS_DARK")

# 6. Sights
ob_fsight = mesh.plate("SIGHTS_Front_PRIM", coll, L.FRONT_SIGHT_POLY, -0.0010, 0.0010, "MAT_CONTROLS_DARK")
ob_rsight = mesh.plate("SIGHTS_Rear_PRIM", coll, L.REAR_SIGHT_POLY, -0.0070, 0.0070, "MAT_CONTROLS_DARK")

# Analyze scene
objs = [ob_slide, ob_frame, ob_barrel, ob_grip_l, ob_grip_r, ob_trigger, ob_hammer, ob_fsight, ob_rsight]
print(f"Created {len(objs)} primitive objects.")

total_tris = 0
min_x = min_y = min_z = float('inf')
max_x = max_y = max_z = float('-inf')

for ob in objs:
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    total_tris += tris
    for v in me.vertices:
        w = ob.matrix_world @ v.co
        min_x = min(min_x, w.x)
        max_x = max(max_x, w.x)
        min_y = min(min_y, w.y)
        max_y = max(max_y, w.y)
        min_z = min(min_z, w.z)
        max_z = max(max_z, w.z)
    print(f"  {ob.name:25s}: {tris:4d} tris")

dx = max_x - min_x
dy = max_y - min_y
dz = max_z - min_z

print(f"\nTotal Tris: {total_tris} (budget < 1500)")
print(f"Bbox X (width): {dx:.4f} m (target: 0.0303 m)")
print(f"Bbox Y (length): {dy:.4f} m (target: 0.2351 m)")
print(f"Bbox Z (height): {dz:.4f} m (target: 0.1463 m)")
print(f"Lowest Z: {min_z:.4f} m")
