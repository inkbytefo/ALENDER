"""Close-up review renders of the magazine and buttstock (clay, cavity on).
    python wb.py run projects/PROP_AK_Rifle/closeups.py"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import landmarks as L
from workbench import paths
from workbench.bl import scene, render

scene.open_blend(paths.out(L.ASSET, "blend", L.ASSET + ".blend"))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type, sh.show_cavity, sh.cavity_type = "STUDIO", "MATERIAL", True, "BOTH"
sh.show_specular_highlight = True
OUT = paths.out(L.ASSET, "work", "closeups")
cd = bpy.data.cameras.new("CAM_CLOSE")
cam = bpy.data.objects.new("CAM_CLOSE", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.lens = 70
SHOTS = {                       # target px, direction (x, y, z), distance m
    "mag_right": ((790, 470), (-1.0, -0.25, 0.1), 0.55),
    "mag_left_low": ((790, 470), (1.0, 0.3, -0.35), 0.55),
    "mag_front": ((790, 470), (-0.35, -1.0, 0.25), 0.55),
    "stock_right": ((230, 360), (-1.0, 0.2, 0.15), 0.62),
    "stock_rear": ((40, 360), (-0.45, 1.0, 0.2), 0.40),
    "stock_left_top": ((230, 340), (0.9, 0.35, 0.6), 0.62),
}
for name, (px, d, dist) in SHOTS.items():
    t = Vector(L.P3(*px))
    dv = Vector(d).normalized()
    cam.location = t + dv * dist
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1200, 900
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
print("[CLOSEUPS]", OUT)
