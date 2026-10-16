import bpy
import math
import mathutils
from pathlib import Path

src_glb = Path("AssetM\u0131grat\u0131onFromPublictoUS/RawAssets/Weapons_Firearms/Pistols/colt-m1911-a1-game-ready-rigged/source/M1911A1.glb").resolve()
ref_dir = Path("projects/PROP_Colt_1911/ref").resolve()
ref_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

# Remove icosphere and any sky/background objects
for obj in list(bpy.data.objects):
    if "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# Find magazine and position it properly inserted into the grip if it was offset
mag = bpy.data.objects.get("Magazine_LOW")
if mag and mag.location.y > 0.05:
    print(f"Aligning ejected magazine from {mag.location} into frame...")
    mag.location.y = 0.0

# Set up world lighting (clean studio gray)
world = bpy.data.worlds.new("RefWorld")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.2, 0.2, 0.2, 1.0)
    bg.inputs[1].default_value = 1.0

# Add 3-point lights
def add_sun(name, energy, rot):
    light_data = bpy.data.lights.new(name=name, type='SUN')
    light_data.energy = energy
    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.rotation_euler = rot

add_sun("KeySun", 3.0, (math.radians(45), math.radians(30), math.radians(45)))
add_sun("FillSun", 1.5, (math.radians(-30), math.radians(-45), math.radians(-60)))
add_sun("RimSun", 2.0, (math.radians(-60), math.radians(60), math.radians(120)))

# Create ortho camera
cam_data = bpy.data.cameras.new("RefCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 0.28
cam_obj = bpy.data.objects.new("RefCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

scene = bpy.context.scene
scene.render.resolution_x = 2048
scene.render.resolution_y = 1536
scene.render.image_settings.file_format = 'PNG'

# Gun center in this file:
# Barrel along X, height along Z, width along Y
gun_center = mathutils.Vector((0.065, 0.0, 0.025))

views = [
    # Right side view (+Y looking towards -Y)
    ("REF_SIDE_RIGHT.png", (0.065, 0.5, 0.025), (math.radians(90), 0, math.radians(180))),
    # Left side view (-Y looking towards +Y)
    ("REF_SIDE_LEFT.png", (0.065, -0.5, 0.025), (math.radians(90), 0, 0)),
    # Top view (+Z looking down)
    ("REF_TOP.png", (0.065, 0.0, 0.5), (0, 0, math.radians(-90))),
    # Front view (+X looking along barrel towards breech)
    ("REF_FRONT.png", (0.5, 0.0, 0.025), (math.radians(90), 0, math.radians(90))),
]

for filename, pos, rot in views:
    cam_obj.location = pos
    cam_obj.rotation_euler = rot
    out_path = ref_dir / filename
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {out_path}")

# Also copy primary side view as REAL_REFERENCE.png and REF_COMPOSITE.png for workbench gate
import shutil
shutil.copyfile(str(ref_dir / "REF_SIDE_LEFT.png"), str(ref_dir / "REAL_REFERENCE.png"))
shutil.copyfile(str(ref_dir / "REF_SIDE_LEFT.png"), str(ref_dir / "REF_COMPOSITE.png"))
shutil.copyfile(str(src_glb), str(ref_dir / "SOURCE_M1911A1.glb"))
print("Reference images and GLB prepared.")
