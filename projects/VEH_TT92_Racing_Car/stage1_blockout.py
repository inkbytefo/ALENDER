"""
STAGE 1 - BLOCKOUT (LOW)          python wb.py build VEH_TT92_Racing_Car --stage 1

Empty scene -> collections, materials, reference camera + photo, review cameras, guides ->
every part at the LOW profile (few segments, no bevels, no fine details).
Purpose: check proportions and that nothing collides before any detail is added.

Milestones: 00_SETUP, 01_GLOBAL_BLOCKOUT (wheels + body only), 02_COMPLETE_LOW.
Writes work/s1/stats.json (tris, bbox, intersections) used by the stage 4 report.
"""
import os
import json
import bpy

import stagelib as SL
import refcams as RC
from stagelib import L, PT, A
from workbench.bl import scene, materials, cameras, render, validate, mesh

WORK = SL.work(1)

# ---------------------------------------------------------------- scene setup
scene.reset()
scene.setup_collections()
materials.ensure(PT.PALETTE)
ref_cams = RC.make_all(SL.HERE)
cams = cameras.review_rig(center=(0.0, 0.0, 0.45), length=4.0, width=2.1)
scene.guides(PT.guide_points())
ground = mesh.grid("GUIDE_GROUND_PLANE", "01_GUIDES", 2.0)
ground.display_type = "WIRE"
ground.hide_render = True
bpy.context.scene.camera = ref_cams["ref"][0]
SL.save_milestone("00_SETUP")

# ---------------------------------------------------------------- global proportions: wheels + body
PT.build_global(PT.LOW)
SL.save_milestone("01_GLOBAL_BLOCKOUT")
SL.review(1, "global")

# ---------------------------------------------------------------- every part at LOW
# (build_all rebuilds wheels + body too: builders are idempotent, same names are replaced)
PT.build_all(PT.LOW)
SL.review(1, "low")
render.review_set(cams, WORK, "low", modes=("CLAY",))

objs = [o for o in SL.low() if o.type == "MESH"]
st = validate.stats(objs)
stats = {"objects": st["objects"], "tris": st["tris"], "dims": [round(d, 3) for d in st["dims"]],
         "bbox_min": [round(d, 3) for d in st["bbox_min"]],
         "intersections": validate.intersections(PT.CRITICAL_PAIRS, objs)}
print("[STAGE1] stats", stats)
with open(os.path.join(WORK, "stats.json"), "w") as f:
    json.dump(stats, f, indent=1)
SL.save_milestone("02_COMPLETE_LOW")
if stats["intersections"]:
    raise SystemExit("[STAGE1] FAIL: fix the intersections before stage 2")
print("[STAGE1] PASS")
