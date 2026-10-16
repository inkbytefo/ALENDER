"""
GODOT export of VEH_Gemini_Motorcycle      python wb.py run projects/VEH_Gemini_Motorcycle/finish_game.py

Run after finish_paint.py. Opens the painted hero file and writes output/.../godot/ (GLB + FBX,
4K baked textures, ORM + Standard .tres materials) with workbench.bl.godot.export_package.
Game objects: Body (everything static, incl. fork and swingarm), Wheel_Front, Wheel_Rear (pivot on the
axle; discs and rear sprocket ride with them), Glass (headlight lens + reservoirs: keeps its plain
transparent material, not baked). One texture set "Body" for the whole bike.
TEX=512 in the environment gives a quick low-res test.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import landmarks as L
import paint
from workbench import paths, stages
from workbench.bl import scene, master, godot

A = "VEH_Gemini_Motorcycle"
scene.open_blend(paths.out(A, "blend", A + ".blend"))
master.setup(paint.PREFIX)
high = [o for o in scene.objects_in(["30_S3_DETAIL"]) if o.type == "MESH"]
glass = {o.name for o in high if any(s.material and s.material.name == "MAT_GLASS" for s in o.material_slots)}


def classify(name):
    base = stages.base_name(name)
    if name in glass:
        return "Glass", None
    if re.match(r"WHEEL_Front_|BRAKE_Front_Disc", base):
        return "Wheel_Front", "Body"
    if re.match(r"WHEEL_Rear_|BRAKE_Rear_Disc|DRIVE_Sprocket_Rear", base):
        return "Wheel_Rear", "Body"
    return "Body", "Body"


rep = godot.export_package(
    A, high, classify, {"Wheel_Front": L.FRONT_AXLE, "Wheel_Rear": L.REAR_AXLE},
    paths.out(A, "godot"), prefix="Gemini", root_name="Gemini", size=int(os.environ.get("TEX", "4096")),
    emission_strength=paint.INSTANCES["MAT_TAILLIGHT"]["p"]["Emission Strength"],
    readme=os.path.join(HERE, "GODOT.md"))
if not rep["ok"]:
    raise SystemExit("[GAME] FAIL: re-import check")
print("[GAME] PASS", rep["tris"], "tris", rep["files"])
