import bpy
import mathutils
from pathlib import Path
import json

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

for obj in list(bpy.data.objects):
    if "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

mag = bpy.data.objects.get("Magazine_LOW")
if mag and mag.location.y > 0.05:
    mag.location.y = 0.0

# In our camera setup:
# Camera center at X = 0.065, Z = 0.025
# Scale S = 2048 / 0.28 = 7314.2857 px/m
# Center pixel: (1024, 768)
# U = 1024 + (X - 0.065) * S
# V = 768 - (Z - 0.025) * S

def world_to_uv(x, z):
    S = 2048.0 / 0.28
    u = 1024.0 + (x - 0.065) * S
    v = 768.0 - (z - 0.025) * S
    return round(u, 1), round(v, 1)

key_landmarks = {}

# Slide
slide = bpy.data.objects.get("Slide_LOW")
if slide:
    bbox = [slide.matrix_world @ mathutils.Vector(c) for c in slide.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)
    key_landmarks["SLIDE_REAR_TOP"] = world_to_uv(min_x, max_z)
    key_landmarks["SLIDE_FRONT_TOP"] = world_to_uv(max_x, max_z)
    key_landmarks["SLIDE_FRONT_BOT"] = world_to_uv(max_x, min_z)
    key_landmarks["SLIDE_REAR_BOT"] = world_to_uv(min_x, min_z)

# Frame
frame = bpy.data.objects.get("Frame_LOW")
if frame:
    bbox = [frame.matrix_world @ mathutils.Vector(c) for c in frame.bound_box]
    key_landmarks["FRAME_DUST_COVER_FRONT"] = world_to_uv(max(v.x for v in bbox), 0.057)
    key_landmarks["FRAME_TRIGGER_GUARD_BOT"] = world_to_uv(0.065, min(v.z for v in bbox))
    key_landmarks["FRAME_GRIP_BOT_FRONT"] = world_to_uv(min(v.x for v in bbox) + 0.04, min(v.z for v in bbox))

# Hammer
hammer = bpy.data.objects.get("Hammer_LOW")
if hammer:
    bbox = [hammer.matrix_world @ mathutils.Vector(c) for c in hammer.bound_box]
    key_landmarks["HAMMER_TIP"] = world_to_uv(min(v.x for v in bbox), max(v.z for v in bbox))

# Front & Rear Sight
fsight = bpy.data.objects.get("Front Sight_LOW")
if fsight:
    bbox = [fsight.matrix_world @ mathutils.Vector(c) for c in fsight.bound_box]
    key_landmarks["FRONT_SIGHT_TIP"] = world_to_uv(max(v.x for v in bbox), max(v.z for v in bbox))

rsight = bpy.data.objects.get("Rear Sight_LOW")
if rsight:
    bbox = [rsight.matrix_world @ mathutils.Vector(c) for c in rsight.bound_box]
    key_landmarks["REAR_SIGHT_TIP"] = world_to_uv(min(v.x for v in bbox), max(v.z for v in bbox))

print("Key landmarks extracted:")
for k, v in key_landmarks.items():
    print(f"  {k:30s} = {v}")

with open("projects/PROP_Colt_1911/ref/KEY_LANDMARKS.json", "w") as f:
    json.dump(key_landmarks, f, indent=2)
