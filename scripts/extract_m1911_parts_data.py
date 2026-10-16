import bpy
import mathutils
from pathlib import Path
import json

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

# Remove icosphere
for obj in list(bpy.data.objects):
    if "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# Find magazine and position it inserted
mag = bpy.data.objects.get("Magazine_LOW")
if mag and mag.location.y > 0.05:
    mag.location.y = 0.0

parts_data = {}

for obj in sorted(bpy.data.objects, key=lambda o: o.name):
    if obj.type != 'MESH':
        continue
    me = obj.data
    mw = obj.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    if not verts:
        continue

    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)

    center = [(min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2]
    dims = [max_x - min_x, max_y - min_y, max_z - min_z]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)

    parts_data[obj.name] = {
        "tris": tris,
        "verts": len(verts),
        "min": [round(min_x, 5), round(min_y, 5), round(min_z, 5)],
        "max": [round(max_x, 5), round(max_y, 5), round(max_z, 5)],
        "center": [round(c, 5) for c in center],
        "dims": [round(d, 5) for d in dims],
        "material": [m.name for m in obj.data.materials if m]
    }

out_file = Path("projects/PROP_Colt_1911/ref/PARTS_GEOMETRY.json")
with open(out_file, "w") as f:
    json.dump(parts_data, f, indent=2)

print(f"Extracted {len(parts_data)} parts geometry into {out_file}")
for name, data in parts_data.items():
    print(f"  {name:30s} | {data['tris']:4d} tris | Dims: {data['dims']} | Center: {data['center']}")
