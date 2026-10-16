import bpy
import mathutils
from pathlib import Path

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

frame = bpy.data.objects.get("Frame_LOW")
mw = frame.matrix_world

S = 2048.0 / 0.28
def world_to_uv(x, z):
    u = 1024.0 + (x - 0.065) * S
    v = 768.0 - (z - 0.025) * S
    return u, v

uv_pts = [world_to_uv((mw @ v.co).x, (mw @ v.co).z) for v in frame.data.vertices]
us = [p[0] for p in uv_pts]
vs = [p[1] for p in uv_pts]

print(f"Frame_LOW U range: {min(us):.1f} to {max(us):.1f}")
print(f"Frame_LOW V range: {min(vs):.1f} to {max(vs):.1f}")

# Dust cover front is at max U
max_u = max(us)
print(f"Frame front (dust cover) max U: {max_u:.1f}")

# Trigger guard loop
tg_pts = [p for p in uv_pts if 750 < p[0] < 1250 and 600 < p[1] < 850]
print(f"Trigger guard points: {len(tg_pts)} points")
