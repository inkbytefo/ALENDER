import bpy
import math
from pathlib import Path
from PIL import Image
import numpy as np
import json
import sys
sys.path.insert(0, ".")
from workbench.silhouette import simplify

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()
ref_dir = Path("projects/PROP_Colt_1911/ref").resolve()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

for obj in list(bpy.data.objects):
    if "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# Setup black world
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

# Camera
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

parts_to_trace = [
    ("FRAME_POLY", ["Frame_LOW"]),
    ("SLIDE_POLY", ["Slide_LOW", "Slide Front 1_LOW", "Slide Front 2_LOW"]),
    ("HAMMER_POLY", ["Hammer_LOW"]),
    ("TRIGGER_POLY", ["Trigger_LOW"]),
    ("SIGHT_FRONT_POLY", ["Front Sight_LOW"]),
    ("SIGHT_REAR_POLY", ["Rear Sight_LOW"]),
]

result_polys = {}

for poly_name, obj_names in parts_to_trace:
    # Hide all
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.hide_render = True
            obj.data.materials.clear()
            obj.data.materials.append(white_mat)

    # Show only target objects
    found = False
    for oname in obj_names:
        o = bpy.data.objects.get(oname)
        if o:
            o.hide_render = False
            found = True

    if not found:
        print(f"Skipping {poly_name}, objects not found.")
        continue

    temp_path = ref_dir / f"TEMP_{poly_name}.png"
    scene.render.filepath = str(temp_path)
    bpy.ops.render.render(write_still=True)

    # Now trace the boundary
    im = Image.open(temp_path).convert("L")
    arr = np.array(im) > 30

    start_rows, start_cols = np.where(arr)
    if len(start_rows) == 0:
        print(f"No pixels for {poly_name}")
        continue

    start_row = start_rows[0]
    start_col = start_cols[np.where(start_rows == start_row)[0][0]]

    directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    contour = []
    curr = (start_row, start_col)
    dir_idx = 0

    max_steps = 15000
    step = 0
    while step < max_steps:
        contour.append((float(curr[1]), float(curr[0])))
        found_next = False
        for i in range(8):
            check_dir = (dir_idx + 6 + i) % 8
            dr, dc = directions[check_dir]
            nr, nc = curr[0] + dr, curr[1] + dc
            if 0 <= nr < arr.shape[0] and 0 <= nc < arr.shape[1] and arr[nr, nc]:
                curr = (nr, nc)
                dir_idx = check_dir
                found_next = True
                break
        if not found_next or (curr == (start_row, start_col) and step > 10):
            break
        step += 1

    simplified = simplify(contour + [contour[0]], 3.0)
    result_polys[poly_name] = [[round(u, 1), round(v, 1)] for u, v in simplified]
    print(f"{poly_name}: {len(contour)} raw -> {len(simplified)} simplified points.")

    if temp_path.exists():
        temp_path.unlink()

out_json = ref_dir / "ACCURATE_PART_POLYS.json"
with open(out_json, "w") as f:
    json.dump(result_polys, f, indent=2)

print(f"Wrote all part polygons to {out_json}")
