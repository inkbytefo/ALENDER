import bpy
import mathutils
from pathlib import Path

p = Path("AssetM\u0131grat\u0131onFromPublictoUS/RawAssets/Weapons_Firearms/Pistols/colt-m1911-a1-game-ready-rigged/source/M1911A1.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))

print("\n--- ALL OBJECTS ---")
mesh_objs = []
for obj in bpy.data.objects:
    if "icosphere" in obj.name.lower():
        print(f"Skipping background/sky object: {obj.name}")
        continue
    print(f"[{obj.type}] {obj.name}: loc={tuple(round(v, 4) for v in obj.location)}, scale={tuple(round(v, 4) for v in obj.scale)}")
    if obj.type == 'MESH':
        mesh_objs.append(obj)
        dims = obj.dimensions
        print(f"    mesh dims: X={dims.x:.4f}, Y={dims.y:.4f}, Z={dims.z:.4f}")

# Compute world-space bounds across all mesh vertices
min_co = mathutils.Vector((float('inf'), float('inf'), float('inf')))
max_co = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))

for obj in mesh_objs:
    mw = obj.matrix_world
    for v in obj.data.vertices:
        wco = mw @ v.co
        min_co.x = min(min_co.x, wco.x)
        min_co.y = min(min_co.y, wco.y)
        min_co.z = min(min_co.z, wco.z)
        max_co.x = max(max_co.x, wco.x)
        max_co.y = max(max_co.y, wco.y)
        max_co.z = max(max_co.z, wco.z)

total_dims = max_co - min_co
print("\n--- WORLD BOUNDING BOX OF ALL MESHES ---")
print(f"Min: ({min_co.x:.4f}, {min_co.y:.4f}, {min_co.z:.4f})")
print(f"Max: ({max_co.x:.4f}, {max_co.y:.4f}, {max_co.z:.4f})")
print(f"Total Dimensions: X={total_dims.x:.4f}m, Y={total_dims.y:.4f}m, Z={total_dims.z:.4f}m")

# Real-world M1911 dimensions:
# Length: ~216 mm (0.216 m)
# Height: ~140 mm (0.140 m)
# Width / Thickness: ~33-35 mm (0.033-0.035 m)
print(f"\nReal Colt 1911 reference: ~0.216m length x 0.140m height x 0.035m width")
