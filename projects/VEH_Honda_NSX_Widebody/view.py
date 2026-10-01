"""Quick design review: photo-like 3/4 camera (right side, front right) of the S3 model, MATERIAL workbench.
python wb.py run projects/VEH_Honda_NSX_Widebody/view.py [stage] """
import sys, math, bpy
from mathutils import Vector
from workbench.bl import cameras, render, materials
stage = (sys.argv[-1] if sys.argv[-1] in "123" else "3")
tag = {"1": "S1_PRIMITIVE", "2": "S2_LOWPOLY", "3": "S3_DETAIL"}[stage]
bpy.ops.wm.open_mainfile(filepath=rf"C:\Users\tpoyr\OneDrive\Desktop\blender\output\VEH_Honda_NSX_Widebody\blend\VEH_Honda_NSX_Widebody_{tag}.blend")
out = r"C:\Users\tpoyr\AppData\Local\Temp\claude\C--Users-tpoyr-OneDrive-Desktop-blender\fc99c5d2-0402-4603-a284-d57bf8f48030\scratchpad"
views = {"photo": (-4.6, -5.2, 1.3, 1.1), "front": (-0.5, -7.0, 0.9, 1.1), "rear34": (4.2, 5.2, 1.5, 1.1), "side": (-8.0, 0.0, 0.6, 1.0)}
for name, (x, y, z, f) in views.items():
    loc = Vector((x, y, z)); tgt = Vector((0, -0.1, 0.5))
    d = tgt - loc
    rot = d.to_track_quat("-Z", "Y").to_euler()
    cam = cameras.make("CAM_V", tuple(loc), tuple(rot), lens=40 if name != "side" else 60, collection="09_PRESENTATION")
    bpy.context.scene.camera = cam
    render.workbench(cam, rf"{out}\v_{name}.png", mode="MATERIAL", res=(1080, 720))
