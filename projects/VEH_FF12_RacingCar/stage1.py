"""
STAGE 1 - LOW POLY / BLOCKOUT for VEH_FF12_RacingCar      python wb.py run projects/VEH_FF12_RacingCar/stage1.py
Gate (docs/05_VALIDATION.md): silhouette overlay matches, orthos plausible, 0 critical intersections.
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, mesh

A = L.ASSET
WORK = paths.out(A, "work", "stage1")
PHOTO = os.path.join(HERE, "ref", "REAL_REFERENCE.png")

scene.reset()
scene.setup_collections()
materials.ensure(PT.PALETTE)
ref_cam = None
if os.path.isfile(PHOTO):
    ref_cam = cameras.reference_camera(L.REF, L.ANCHORS)
    cameras.reference_image(L.REF, PHOTO, ref_cam)
    print("[STAGE1] reference camera anchor error px:", ref_cam["anchor_reprojection_error_px"])
scene.guides(PT.guide_points())
scene.save(paths.milestone(A, "00_SETUP"))

# Phase 1: Global proportions milestone
PT.wheels(PT.LOW)
bb = mesh.box("TEMP_BoundingVolume", "08_TEMP", (0.0, 0.0, 0.44), (1.84, 4.10, 0.88))
bb.display_type = "WIRE"; bb.hide_render = True
scene.save(paths.milestone(A, "01_GLOBAL_BLOCKOUT"))

# Phase 2-8: Complete all low-poly assemblies
PT.build_all(PT.LOW)
objs = validate.mesh_objects(scene.objects_in(scene.LOW_COLLS))
cams = cameras.rig_from_bounds(objs)
if ref_cam:
    render.workbench(ref_cam, os.path.join(WORK, "low_ref_clay.png"), "CLAY", transparent=True)
    render.workbench(ref_cam, os.path.join(WORK, "low_ref_mat.png"), "MATERIAL", transparent=True)
render.review_set(cams, WORK, "low", modes=("CLAY",))

st = validate.stats(objs)
stats = {"objects": st["objects"], "tris": st["tris"], "dims": st["dims"],
         "intersections": validate.intersections(PT.CRITICAL_PAIRS, objs)}
print("[STAGE1] stats", stats)
json.dump(stats, open(os.path.join(WORK, "stats.json"), "w"), indent=1)

scene.save(paths.milestone(A, "02_COMPLETE_LOW"))
scene.save(paths.milestone(A, "STAGE_01_LOW"))

if stats["intersections"]:
    print("[STAGE1] GATE FAIL: critical intersections found:", stats["intersections"])
else:
    print("[STAGE1] GATE PASS: 0 critical intersections, tri count =", stats["tris"])
