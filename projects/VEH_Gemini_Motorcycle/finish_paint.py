"""
PAINT step of VEH_Gemini_Motorcycle        python wb.py run projects/VEH_Gemini_Motorcycle/finish_paint.py

Run after `python wb.py build VEH_Gemini_Motorcycle` (S1-S3, gated). Opens the hero file
output/.../blend/VEH_Gemini_Motorcycle.blend, puts the master-material instances of paint.py on the
S3 DETAIL model and saves it again (idempotent). Review renders (Cycles): renders/paint_*.png.
The S1 / S2 meshes and the stage GLBs keep the flat modelling materials.
"""
import os
import sys
import importlib
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from workbench import paths, stages
from workbench.bl import scene, render, master
import paint

importlib.reload(paint)
A = "VEH_Gemini_Motorcycle"
HERO = paths.out(A, "blend", A + ".blend")
RENDERS = paths.out(A, "renders")
DETAIL = "30_S3_DETAIL"

scene.open_blend(HERO)
for c in bpy.data.collections:
    if c.name != DETAIL and (c.name[:2].isdigit()) and c.name not in ("09_PRESENTATION", "00_REFERENCE"):
        c.hide_render = c.hide_viewport = True
objs = [o for o in scene.objects_in([DETAIL]) if o.type == "MESH"]
used = paint.apply(objs)
print("[PAINT] master:", master.MASTER, "| instances:", len(paint.INSTANCES), "| objects:", len(objs))
for name in sorted(used):
    m = bpy.data.materials[name]
    print(f"[PAINT]   {name:<20}{used[name]:>4} slots   set {m['pbr_set']}  tile {m['pbr_tile_m']} m")
unused = sorted(set(paint.INSTANCES) - set(used))
bad = master.unwired_normal_maps(paint.INSTANCES)
flat = sorted({s.material.name for o in objs for s in o.material_slots
               if s.material and s.material.name not in paint.INSTANCES} - {"MAT_GLASS"})
if unused or bad or flat:
    raise SystemExit(f"[PAINT] FAIL unused instances {unused} | normal map not wired {bad} | still flat {flat}")
scene.save(HERO)

# ---------------------------------------------------------------- review renders
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.world = sc.world or bpy.data.worlds.new("World")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.045, 0.047, 0.05, 1.0)
render.studio_lights(center=(0, 0, 0.5), size=1.8, strength=1.6)
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
SHOTS = {                                   # the bike's right side (-X) is the photo side
    "paint_right": ((-3.3, 0.0, 0.62), (0.0, 0.0, 0.52), 60),
    "paint_front_34": ((-1.9, -2.3, 1.05), (0.0, -0.05, 0.50), 50),
    "paint_rear_34": ((-1.8, 2.4, 1.0), (0.0, 0.15, 0.50), 50),
    "paint_engine": ((-1.25, -0.35, 0.62), (0.0, -0.02, 0.42), 55),
}
for tag, (loc, tgt, lens) in SHOTS.items():
    cd = bpy.data.cameras.new("CAM_" + tag)
    cd.lens = lens
    cam = bpy.data.objects.new("CAM_" + tag, cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(RENDERS, tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("[PAINT] render", sc.render.filepath)
print("[PAINT] PASS")
