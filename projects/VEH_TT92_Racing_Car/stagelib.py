"""
Shared helpers of the stage scripts (stage1_blockout.py ... stage5_workspace.py).

Milestones (output/VEH_TT92_Racing_Car/blend/VEH_TT92_Racing_Car_<TAG>.blend):
    stage 1  00_SETUP, 01_GLOBAL_BLOCKOUT, 02_COMPLETE_LOW
    stage 2  03_HIGH_PRIMARY          stage 3  04_HIGH_MECHANICAL
    stage 4  05_FINAL_GEOMETRY + VEH_TT92_Racing_Car.blend + glb + report.json
    stage 5  VEH_TT92_Racing_Car_WORKSPACE.blend   (the clean file to work in)
Each stage opens the milestone of the stage before it, so any stage can be re-run on its own.
"""
import os
import sys
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy
import landmarks as L
import parts as PT
from workbench import paths
from workbench.bl import scene, render

importlib.reload(L)
importlib.reload(PT)

A = L.ASSET
RENDERS = paths.out(A, "renders")


def work(stage):
    return paths.out(A, "work", f"s{stage}")


def open_milestone(tag):
    scene.open_blend(paths.milestone(A, tag))


def save_milestone(tag):
    scene.save(paths.milestone(A, tag))


def high():
    return scene.objects_in(scene.HIGH_COLLS)


def low():
    return scene.objects_in(scene.LOW_COLLS)


def hide_low():
    """HIGH stages keep the LOW blockout in the file, hidden."""
    for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
        scene.set_collection_visible(c, False)


def review(stage, tag):
    """clay + material render through the reference (top) camera -> output/.../work/s<stage>/."""
    cam = bpy.data.objects["CAM_REFERENCE"]
    for mode, suffix in (("CLAY", "clay"), ("MATERIAL", "mat")):
        render.workbench(cam, os.path.join(work(stage), f"{tag}_ref_{suffix}.png"), mode,
                         transparent=True, res=L.IMAGE_SIZE)
