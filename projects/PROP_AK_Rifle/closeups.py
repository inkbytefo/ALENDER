"""Close-up look-dev renders of the painted S3 hero mesh (Cycles, studio_light stage).
    python wb.py run projects/PROP_AK_Rifle/closeups.py [-- shot ...]
-> output/PROP_AK_Rifle/work/closeups/<shot>.png + sheet.png. Look at these after every paint change:
the gates cannot judge materials."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

import landmarks as L
from workbench import paths, stages
from workbench.bl import scene, cameras, presentation as pres

SHOTS = {                       # target px, view direction towards the camera (x, y, z), distance m
    "receiver_right": ((640, 300), (-1.0, -0.15, 0.25), 0.50),
    "mag_right": ((790, 470), (-1.0, -0.25, 0.10), 0.52),
    "stock_right": ((230, 360), (-1.0, 0.20, 0.15), 0.60),
    "stock_rear": ((40, 360), (-0.45, 1.0, 0.20), 0.40),
    "front_right": ((1250, 280), (-1.0, -0.45, 0.30), 0.50),
    "grip_left": ((500, 400), (1.0, -0.30, -0.10), 0.45),
}
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
scene.open_blend(paths.out(L.ASSET, "blend", L.ASSET + ".blend"))
for c in bpy.data.collections:
    if c.name != stages.STAGES[3]["coll"] and c.name[:2].isdigit():
        scene.set_collection_visible(c.name, False)
scene.set_collection_visible(stages.STAGES[3]["coll"], True)
objs = [o for o in scene.coll(stages.STAGES[3]["coll"]).all_objects if o.type == "MESH"]
pres.studio(objs, "studio_light")
pres.setup_engine("CYCLES", 96)
bpy.context.scene.view_settings.exposure += 1.6        # the stage is lit for whole-asset shots
out = paths.out(L.ASSET, "work", "closeups")
files = []
for name, (px, d, dist) in SHOTS.items():
    if only and name not in only:
        continue
    t = Vector(L.P3(*px))
    cam = cameras.make("PRES_CAM_" + name, t + Vector(d).normalized() * dist, (0, 0, 0), lens=70.0)
    cameras.look_at(cam, t)
    files.append(pres.still(cam, os.path.join(out, name + ".png"), res=(1200, 900)))
print("[CLOSEUPS]", out, len(files))
