import bpy
import math
from pathlib import Path

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()
ref_dir = Path("projects/PROP_Colt_1911/ref").resolve()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

for obj in list(bpy.data.objects):
    if "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

world = bpy.data.worlds.new("BlackWorld")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs[1].default_value = 0.0

white_mat = bpy.data.materials.new("WhiteEmission")
white_mat.use_nodes = True
nodes = white_mat.node_tree.nodes
nodes.clear()
emit = nodes.new("ShaderNodeEmission")
emit.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
emit.inputs[1].default_value = 1.0
out = nodes.new("ShaderNodeOutputMaterial")
white_mat.node_tree.links.new(emit.outputs[0], out.inputs[0])

cam_data = bpy.data.cameras.new("PartCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 0.28
cam_obj = bpy.data.objects.new("PartCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0.065, -0.5, 0.025)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

scene = bpy.context.scene
scene.render.resolution_x = 2048
scene.render.resolution_y = 1536
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'BW'
scene.render.image_settings.color_depth = '8'

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.hide_render = True
        obj.data.materials.clear()
        obj.data.materials.append(white_mat)

grip = bpy.data.objects.get("Plaquettes_LOW")
if grip:
    grip.hide_render = False

out_path = ref_dir / "MASK_GRIP_PANEL.png"
scene.render.filepath = str(out_path)
bpy.ops.render.render(write_still=True)
print("Rendered MASK_GRIP_PANEL.png")
