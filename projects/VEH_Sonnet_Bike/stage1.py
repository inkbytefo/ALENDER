"""
STAGE 1 - LOW POLY / STRUCTURAL BLOCKOUT  (VEH_Gemini_Motorcycle)
    python wb.py run projects/VEH_Gemini_Motorcycle/stage1.py
Milestones: <ASSET>_00_SETUP, _01_GLOBAL_BLOCKOUT, _02_COMPLETE_LOW (+ _STAGE_01_LOW)
Review: output/<ASSET>/work/stage1/*.png  ->  python wb.py compare <ASSET> <..._ref_clay.png>
"""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, mesh

A = L.ASSET
WORK = paths.out(A, "work", "stage1")


def review(tag, cams, ref_cam, ortho=True):
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_clay.png"), "CLAY", transparent=True)
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_mat.png"), "MATERIAL", transparent=True)
    if ortho:
        render.review_set(cams, WORK, tag, modes=("CLAY",))


def main():
    # ---- setup: scene, collections, palette, cameras, guides (the skeleton)
    scene.reset()
    scene.setup_collections()
    materials.ensure(PT.PALETTE)
    ref_cam = cameras.reference_camera(L.REF, [(L.REAR_AXLE, L.REAR_AXLE_PX), (L.FRONT_AXLE, L.FRONT_AXLE_PX)])
    cameras.reference_image(L.REF, os.path.join(HERE, "ref", "REAL_REFERENCE.png"), ref_cam)
    cams = cameras.review_rig(center=(0.0, 0.0, 0.55), length=2.4, width=1.3)
    scene.guides(PT.guide_points())
    g = mesh.grid("GUIDE_GROUND_PLANE", "01_GUIDES", 1.6)
    g.display_type = "WIRE"; g.hide_render = True
    bpy.context.scene.camera = ref_cam
    scene.save(paths.milestone(A, "00_SETUP"))
    print("[STAGE1] reference camera anchor error px:", ref_cam["anchor_reprojection_error_px"])

    # ---- phase 1: global proportions (wheels + bounding volume)
    PT.wheels(PT.LOW)
    front_px, rear_px = 973, 153
    bb = mesh.box("TEMP_BoundingVolume", "08_TEMP",
                  (0, (L.P(front_px, 0)[0] + L.P(rear_px, 0)[0]) / 2, 1.045 / 2), (0.78, 2.05, 1.045))
    bb.display_type = "WIRE"; bb.hide_render = True
    scene.save(paths.milestone(A, "01_GLOBAL_BLOCKOUT"))
    review("p1", cams, ref_cam, ortho=False)

    # ---- phases 2-9: frame, tank, seat/tail, engine, front, rear, exhaust, secondary parts
    PT.build_all(PT.LOW)
    review("p9", cams, ref_cam)

    # ---- phase 10-12: validation + cleanup
    objs = [o for o in scene.objects_in(scene.LOW_COLLS) if o.type == "MESH"]
    st = validate.stats(objs)
    stats = {"objects": st["objects"], "tris": st["tris"],
             "intersections": validate.intersections(PT.CRITICAL_PAIRS, objs)}
    print("[STAGE1] stats", stats)
    with open(os.path.join(WORK, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    scene.save(paths.milestone(A, "02_COMPLETE_LOW"))
    scene.save(paths.milestone(A, "STAGE_01_LOW"))
    if stats["intersections"]:
        print("[STAGE1] GATE FAIL: fix intersections before Stage 2")


main()
