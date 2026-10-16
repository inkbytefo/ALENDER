import sys
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")
import bpy
import bmesh
from mathutils import Vector, Matrix
import math
import landmarks as L
from workbench.bl import mesh, materials, validate, mods

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
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
        bm.to_mesh(me)
        me.update()
    bm.free()
    return ob

# 1. Slide
ob_slide = mesh.plate("SLIDE_Main", coll, L.SLIDE_POLY, -L.SLIDE_HALF_WIDTH, L.SLIDE_HALF_WIDTH, "MAT_GUN_STEEL")
# Bevel top long edges to create 1911 rounded slide top
me = ob_slide.data
bm = bmesh.new()
bm.from_mesh(me)
top_edges = []
max_z = max(v.co.z for v in bm.verts)
for e in bm.edges:
    if abs(e.verts[0].co.z - max_z) < 0.002 and abs(e.verts[1].co.z - max_z) < 0.002:
        # Check if near outer X
        if any(abs(abs(v.co.x) - L.SLIDE_HALF_WIDTH) < 0.002 for v in e.verts):
            top_edges.append(e)

if top_edges:
    bmesh.ops.bevel(bm, geom=top_edges, offset=0.0035, segments=4, profile=0.5, affect='EDGES')
bm.to_mesh(me)
me.update()
bm.free()

# Cut ejection port on right side (-X)
# Ejection port: Y from -0.065 to -0.025, Z from 0.088 to 0.110
y0, z0 = L.P(1050.0, 310.0)
y1, z1 = L.P(1400.0, 420.0)
min_y, max_y = min(y0, y1), max(y0, y1)
min_z, max_z = min(z0, z1), max(z0, z1)
ob_port = mesh.box("TEMP_Port", coll, (-L.SLIDE_HALF_WIDTH, (min_y + max_y)/2, (min_z + max_z)/2),
                   (0.012, max_y - min_y, max_z - min_z), "MAT_GUN_STEEL")
mods.boolean(ob_slide, ob_port, apply=True)
bpy.data.objects.remove(ob_port, do_unlink=True)
triangulate_ngons(ob_slide)

print(f"Slide tris: {sum(len(p.vertices) - 2 for p in ob_slide.data.polygons)}")

# 2. Frame
ob_frame = mesh.plate("FRAME_Main", coll, L.FRAME_POLY, -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")
ob_cutter = mesh.plate("CUTTER", coll, L.TRIGGER_HOLE_POLY, -0.05, 0.05, "MAT_GUN_STEEL")
mods.boolean(ob_frame, ob_cutter, apply=True)
bpy.data.objects.remove(ob_cutter, do_unlink=True)
triangulate_ngons(ob_frame)
print(f"Frame tris: {sum(len(p.vertices) - 2 for p in ob_frame.data.polygons)}")

# 3. Barrel & Bushing
# Outer barrel
p_front = (0.0, *L.P(1872.6, 420.0))
p_rear = (0.0, *L.P(385.0, 420.0))
ob_barrel = mesh.cyl("BARREL_Cylinder", coll, p_rear, p_front, L.BARREL_RADIUS, 24, "MAT_BARREL_CHROME")
# Bore hole (45 ACP bore is ~11.43mm, radius 0.0057m)
p_bore_front = (0.0, p_front[1] - 0.002, p_front[2])
p_bore_rear = (0.0, p_front[1] + 0.060, p_front[2])
ob_bore = mesh.cyl("TEMP_Bore", coll, p_bore_front, p_bore_rear, 0.0057, 24, "MAT_BARREL_CHROME")
mods.boolean(ob_barrel, ob_bore, apply=True)
bpy.data.objects.remove(ob_bore, do_unlink=True)
triangulate_ngons(ob_barrel)

# Barrel Bushing & Plug
ob_bushing = mesh.cyl("BARREL_Bushing", coll, (0, p_front[1] - 0.001, p_front[2]), (0, p_front[1] + 0.006, p_front[2]),
                      L.BARREL_RADIUS + 0.002, 24, "MAT_GUN_STEEL")
triangulate_ngons(ob_bushing)

# Recoil plug
p_plug = (0.0, *L.P(1872.6, 520.0))
ob_plug = mesh.cyl("BARREL_Plug", coll, (0, p_plug[1] - 0.001, p_plug[2]), (0, p_plug[1] + 0.035, p_plug[2]),
                   0.0055, 20, "MAT_GUN_STEEL")
triangulate_ngons(ob_plug)

print(f"Barrel group tris: {sum(len(p.vertices) - 2 for ob in [ob_barrel, ob_bushing, ob_plug] for p in ob.data.polygons)}")

# 4. Check hygiene
objs = [ob_slide, ob_frame, ob_barrel, ob_bushing, ob_plug]
hy = validate.hygiene(objs)
print(f"Total tris so far: {sum(len(p.vertices) - 2 for ob in objs for p in ob.data.polygons)}")
print(f"Hygiene: {hy['total']}")
