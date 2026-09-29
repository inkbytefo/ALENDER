"""
STAGE 1 - LOW POLY / BLOCKOUT for PROP_AK_Rifle      python wb.py run projects/PROP_AK_Rifle/stage1.py
Gate (docs/05_VALIDATION.md): silhouette overlay matches, orthos plausible, 0 critical intersections.
Milestones: _00_SETUP, _01_GLOBAL_BLOCKOUT, _02_COMPLETE_LOW (+ _STAGE_01_LOW).
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate

A = L.ASSET
WORK = paths.out(A, "work", "stage1")
PHOTO = os.path.join(HERE, "ref", "REAL_REFERENCE.png")


def main():
    scene.reset()
    scene.setup_collections()
    materials.ensure(PT.PALETTE)
    ref_cam = cameras.reference_camera(L.REF, L.ANCHORS)
    cameras.reference_image(L.REF, PHOTO, ref_cam)
    bpy.context.scene.camera = ref_cam
    print("[STAGE1] reference camera anchor error px:", ref_cam["anchor_reprojection_error_px"])
    scene.guides(PT.guide_points())
    scene.save(paths.milestone(A, "00_SETUP"))

    # phase 1: global proportions - receiver, barrel, stock, magazine, grip
    PT.receiver(PT.LOW); PT.barrel(PT.LOW)
    PT.woodwork(PT.LOW); PT.buttstock(PT.LOW); PT.magazine(PT.LOW); PT.grip(PT.LOW)
    scene.save(paths.milestone(A, "01_GLOBAL_BLOCKOUT"))
    render.workbench(ref_cam, os.path.join(WORK, "p1_ref_clay.png"), "CLAY", transparent=True, res=L.IMAGE_SIZE)

    # phase 2+: everything
    PT.build_all(PT.LOW)
    objs = validate.mesh_objects(scene.objects_in(scene.LOW_COLLS))
    cams = cameras.rig_from_bounds(objs)
    render.workbench(ref_cam, os.path.join(WORK, "low_ref_clay.png"), "CLAY", transparent=True, res=L.IMAGE_SIZE)
    render.workbench(ref_cam, os.path.join(WORK, "low_ref_mat.png"), "MATERIAL", transparent=True, res=L.IMAGE_SIZE)
    render.review_set(cams, WORK, "low", modes=("CLAY",))

    st = validate.stats(objs)
    stats = {"objects": st["objects"], "tris": st["tris"], "dims": st["dims"],
             "top_tris": st["top_tris"][:8],
             "intersections": validate.intersections(PT.CRITICAL_PAIRS, objs)}
    print("[STAGE1] stats", json.dumps(stats, default=str))
    with open(os.path.join(WORK, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1, default=str)
    scene.save(paths.milestone(A, "02_COMPLETE_LOW"))
    scene.save(paths.milestone(A, "STAGE_01_LOW"))
    if stats["intersections"]:
        print("[STAGE1] GATE FAIL: fix intersections before Stage 2")


main()
