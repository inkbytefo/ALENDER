"""
STAGE 5 - PAINT                   python wb.py build VEH_TT92_Racing_Car --stage 5

Opens the pipeline file VEH_TT92_Racing_Car.blend (stage 4), replaces the flat modelling materials
of the HIGH model with the master-material instances of paint.py (one master node group, 14 PBR
instances, tri-planar projection) and saves the file again. Idempotent: run it as often as you like
while tuning paint.INSTANCES.

Needs the texture sets in material/TT92_*_1K-PNG:  python wb.py run projects/VEH_TT92_Racing_Car/texgen.py
Review renders (Cycles): output/VEH_TT92_Racing_Car/renders/paint_*.png
Not touched: the LOW blockout and the GLB of stage 4 (both keep the flat materials).
"""
import os
import importlib
import bpy
from mathutils import Vector

import stagelib as SL
from stagelib import A
from workbench import paths
from workbench.bl import scene, render
import paint

importlib.reload(paint)

scene.open_blend(paths.out(A, "blend", A + ".blend"))
SL.hide_low()
used = paint.apply(SL.high())
print("[STAGE5] master:", paint.MASTER, "| instances:", len(paint.INSTANCES))
for name in sorted(paint.INSTANCES):                         # every instance must carry a wired normal map
    nt = bpy.data.materials[name].node_tree
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.label == "Normal Map"), None)
    ok = bool(tex and tex.image and tex.image.colorspace_settings.name == "Non-Color" and tex.outputs["Color"].links)
    if not ok:
        raise SystemExit(f"[STAGE5] FAIL: {name} has no Non-Color normal map wired into the master")
for name in sorted(used):
    print(f"[STAGE5]   {name:<22}{used[name]:>4} objects   set {bpy.data.materials[name]['pbr_set']}"
          f"  tile {bpy.data.materials[name]['pbr_tile_m']} m")
missing = sorted(set(paint.INSTANCES) - set(used))
if missing:
    raise SystemExit(f"[STAGE5] FAIL: instances not used by any object: {missing}")
flat = sorted({s.material.name for o in SL.high() if o.type == "MESH" for s in o.material_slots
               if s.material and s.material.name not in paint.INSTANCES})
if flat:
    raise SystemExit(f"[STAGE5] FAIL: HIGH objects still on flat materials: {flat}")
scene.save(paths.out(A, "blend", A + ".blend"))

# ---------------------------------------------------------------- review renders (Cycles, studio lights)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
try:
    sc.cycles.device = "GPU"
except Exception:
    pass
sc.world = sc.world or bpy.data.worlds.new("World")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.045, 0.047, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0
render.studio_lights(center=(0, 0, 0.4), size=2.5, strength=1.6)
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.render.film_transparent = False
SHOTS = {
    "paint_front_34": ((2.4, -3.0, 1.35), (0.0, -0.25, 0.42), 50),
    "paint_rear_34": ((-2.2, 3.1, 1.25), (0.0, 0.45, 0.42), 50),
    "paint_engine": ((0.75, -1.55, 1.25), (0.0, -0.42, 0.60), 50),
    "paint_afterburner": ((-0.85, 2.75, 0.62), (0.0, 1.62, 0.42), 55),
    "paint_cockpit": ((0.95, 1.55, 1.35), (0.0, 0.62, 0.55), 45),
}
for tag, (loc, tgt, lens) in SHOTS.items():
    cd = bpy.data.cameras.new("CAM_" + tag)
    cd.lens = lens
    cam = bpy.data.objects.new("CAM_" + tag, cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(SL.RENDERS, tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("[STAGE5] render", sc.render.filepath)
print("[STAGE5] PASS")
