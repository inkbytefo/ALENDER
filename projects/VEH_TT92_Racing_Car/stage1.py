"""
STAGE 1 - LOW POLY / BLOCKOUT for VEH_TT92_Racing_Car
    python wb.py run projects/VEH_TT92_Racing_Car/stage1.py
Milestones: _00_SETUP, _01_GLOBAL_BLOCKOUT, _02_COMPLETE_LOW (+ _STAGE_01_LOW)
The primary photo is a TOP view -> the reference camera is an orthographic top camera;
overlay: python wb.py compare VEH_TT92_Racing_Car output/.../<tag>_ref_clay.png
"""
import os, sys, json, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy

import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
import refcams as RC; importlib.reload(RC)
from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, mesh

A = L.ASSET
WORK = paths.out(A, "work", "stage1")


def review(tag, cams, ref_cams, ortho=True):
    for n, (cam, res) in ref_cams.items():
        render.workbench(cam, os.path.join(WORK, f"{tag}_{n}_clay.png"), "CLAY", transparent=True, res=res)
        render.workbench(cam, os.path.join(WORK, f"{tag}_{n}_mat.png"), "MATERIAL", transparent=True, res=res)
    if ortho:
        render.review_set(cams, WORK, tag, modes=("CLAY",))


def main():
    scene.reset()
    scene.setup_collections()
    materials.ensure(PT.PALETTE)
    ref_cams = RC.make_all(HERE)
    cams = cameras.review_rig(center=(0.0, 0.0, 0.45), length=4.0, width=2.1)
    scene.guides(PT.guide_points())
    g = mesh.grid("GUIDE_GROUND_PLANE", "01_GUIDES", 2.0)
    g.display_type = "WIRE"; g.hide_render = True
    bpy.context.scene.camera = ref_cams["ref"][0]
    scene.save(paths.milestone(A, "00_SETUP"))

    # ---- phase 1: global proportions (wheels + body shell)
    PT.build_global(PT.LOW)
    scene.save(paths.milestone(A, "01_GLOBAL_BLOCKOUT"))
    review("p1", cams, ref_cams, ortho=False)

    # ---- phases 2-8: nose, aero, exhaust, suspension, cockpit, details
    PT.build_all(PT.LOW)
    review("p9", cams, ref_cams)

    objs = [o for o in scene.objects_in(scene.LOW_COLLS) if o.type == "MESH"]
    st = validate.stats(objs)
    stats = {"objects": st["objects"], "tris": st["tris"], "dims": [round(d, 3) for d in st["dims"]],
             "bbox_min": [round(d, 3) for d in st["bbox_min"]],
             "intersections": validate.intersections(PT.CRITICAL_PAIRS, objs)}
    print("[STAGE1] stats", stats)
    print("[STAGE1] top tris", st["top_tris"][:6])
    with open(os.path.join(WORK, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    scene.save(paths.milestone(A, "02_COMPLETE_LOW"))
    scene.save(paths.milestone(A, "STAGE_01_LOW"))
    if stats["intersections"]:
        print("[STAGE1] GATE FAIL: fix intersections before Stage 2")


main()
