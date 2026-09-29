"""
STAGE 2 - HIGH POLY / REFINED for __ASSET__      python wb.py run projects/__ASSET__/stage2.py
Opens _02_COMPLETE_LOW, hides (keeps) LOW, rebuilds HIGH from the same landmarks, validates,
renders, exports GLB and writes report.json.
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, export

scene.open_blend(paths.milestone("__ASSET__", "02_COMPLETE_LOW"))
import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
A = L.ASSET
WORK = paths.out(A, "work", "stage2")

for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
    scene.set_collection_visible(c, False)
materials.ensure(PT.PALETTE)
PT.build_all(PT.HIGH)
scene.save(paths.milestone(A, "05_FINAL_GEOMETRY"))

high = scene.objects_in(scene.HIGH_COLLS)
root = scene.root(A)
for ob in high:
    if ob.type == "MESH" and ob.data.users == 1:
        scene.origin_to_bbox_center(ob)
    ob.parent = root

objs = validate.mesh_objects(high)
cams = cameras.rig_from_bounds(objs)
ref_cam = bpy.data.objects.get("CAM_REFERENCE")
if ref_cam:
    cams["CAM_REFERENCE"] = ref_cam
    render.workbench(ref_cam, os.path.join(WORK, "high_ref_clay.png"), "CLAY", transparent=True)
render.review_set(cams, paths.out(A, "renders"), "final")

st = validate.stats(objs)
chk = validate.Checks()
validate.standard_checks(chk, st, tri_max=100000, max_materials=8)   # TODO target dims / budget
chk.add("X01", "BLOCKER", not validate.intersections(PT.CRITICAL_PAIRS, objs), "critical intersections")
scene.save(paths.out(A, "blend", A + ".blend"))

glb = paths.out(A, "glb", A + ".glb")
n = len(high) + 1
export.glb([root] + high, glb)
ok, detail = export.roundtrip(glb, n, len({m for o in objs for m in o.data.materials if m}))
chk.add("U15", "BLOCKER", ok, detail)
validate.write_report(os.path.join(HERE, "report.json"), A, chk,
                      metrics={"tris_high": st["tris"], "dims": st["dims"], "objects": st["objects"]})
