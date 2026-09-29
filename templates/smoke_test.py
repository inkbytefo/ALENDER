"""
Workbench smoke test:   python wb.py test
Exercises every library module once and asserts the results. Output: output/_smoke_test/
Run it after changing anything in workbench/ or upgrading Blender.
"""
import math
import os
import bpy
from mathutils import Vector

from workbench import paths, tables
from workbench.refmap import RefMap
from workbench.bl import scene, mesh, mods, materials, cameras, render, anim, rig, validate, export
from workbench.bl.fasteners import Fasteners

A = "_smoke_test"
OUT = paths.out(A)
fails = []


def check(name, ok, detail=""):
    print(f"[SMOKE] {'PASS' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        fails.append(name)


scene.reset()
scene.setup_collections()
materials.ensure({"MAT_A": "paint_gloss", "MAT_B": "metal_raw", "MAT_R": "rubber", "MAT_S": "skin",
                  "MAT_G": "glass", "MAT_E": "emissive_warm"})
C = "05_HIGH_BODY"

# refmap round trip
ref = RefMap(400, (800, 600), (-0.5, 0.0), math.radians(2.0))
y, z = ref.P(500, 300)
u, v = ref.photo_of(y, z)
check("refmap_roundtrip", abs(u - 500) < 1e-6 and abs(v - 300) < 1e-6)
mesh.set_ref(ref)

# builders
b = mesh.box("PROP_Box", C, (0, 0, 0.25), (0.5, 0.5, 0.5), "MAT_A"); mods.finish_hard(b, 0.01)
mesh.cyl("PROP_Cyl", C, (1, 0, 0), (1, 0, 0.6), 0.15, 24, "MAT_B")
mesh.tube("PROP_Pipe", C, [(-1, 0, 0.1), (-1, 0.4, 0.5), (-1.3, 0.8, 0.5)], 0.04, 12, "MAT_B")
mesh.tube("PROP_Spring", C, mesh.helix((2, 0, 0), (2, 0, 0.5), 0.08, 6), 0.01, 8, "MAT_B", smooth_path=False)
mesh.lathe("PROP_Wheel", C, (0, 1.5, 0.3), [(0.2, -0.05), (0.3, -0.06), (0.3, 0.06), (0.2, 0.05)], 48, "MAT_R")
mesh.lathe("PROP_Bottle", C, (0, -1.5, 0), [(0.001, 0), (0.1, 0), (0.1, 0.3), (0.03, 0.4), (0.03, 0.5), (0.001, 0.5)],
           32, "MAT_G", axis="Z", closed=False)
pl = mesh.plate("PROP_Plate", C, [(500, 600), (700, 600), (650, 450), (520, 480)], -0.05, 0.05, "MAT_A")
st = [(u_, 400, 470, 0.12, 2.5, 4.0, 0.6) for u_ in tables.lin(300, 420, 8)]
lo = mesh.loft_px("PROP_Loft", C, st, 16, "MAT_A"); mods.finish_organic(lo)
mesh.multi_cyl("PROP_Studs", C, [((x, -1, 0), (x, -1, 0.05), 0.02) for x in (0.0, 0.1, 0.2)], 8, "MAT_B")
fs = Fasteners("07_DETAILS", mat="MAT_B")
fs.ring("BOLT_M6", (1, 0, 0.6), (0, 0, 1), 0.1, 6)
check("fastener_instancing", bpy.data.meshes["BOLT_M6"].users == 6)

# boolean (architecture style opening)
wall = mesh.box("ARCH_Wall", C, (0, 3, 1.5), (4, 0.3, 3), "MAT_A")
cut = mesh.box("TEMP_Cutter", "08_TEMP", (0, 3, 1.05), (0.9, 0.6, 2.1))
mods.boolean(wall, cut, apply=True)
check("boolean_applied", len(wall.data.polygons) > 6 and not wall.modifiers)
bpy.data.objects.remove(cut, do_unlink=True)

# character blockout + rig + auto weights
body = rig.skin_body("CHR_Body", C, {k: (x + 3.0, y_, z_) for k, (x, y_, z_) in rig.HUMANOID_JOINTS.items()},
                     rig.HUMANOID_EDGES, rig.HUMANOID_RADII, "MAT_S", apply=True)
joints = {k: (x + 3.0, y_, z_) for k, (x, y_, z_) in rig.HUMANOID_JOINTS.items()}
arm = rig.armature("CHR_Rig", rig.bones_from_joints(joints, rig.HUMANOID_BONES), C)
res, groups = rig.bind_auto(body, arm)
check("rig_auto_weights", "FINISHED" in res and "LeftUpperArm" in groups, f"{len(groups)} groups")
rig.pose_key(arm, 1, {"LeftUpperArm": (0, 0, 0)})
rig.pose_key(arm, 20, {"LeftUpperArm": (0, math.radians(-60), 0)})

# animation
anim.spin(bpy.data.objects["PROP_Wheel"], "X", 1.0, (1, 24), name="wheel_spin-loop")
check("anim_keys", bpy.data.objects["PROP_Wheel"].animation_data is not None)

# validation
objs = validate.mesh_objects(scene.objects_in(scene.HIGH_COLLS))
stt = validate.stats(objs)
check("stats", stt["tris"] > 1000 and not stt["no_uv"], f"{stt['tris']} tris")
hits = validate.intersections([("PROP_Box", "PROP_Cyl"), ("PROP_Box", "PROP_Box")], objs)
check("no_false_intersections", hits == [], hits)
mesh.box("PROP_Overlap", C, (0.2, 0, 0.25), (0.2, 0.2, 0.2), "MAT_A")
objs = validate.mesh_objects(scene.objects_in(scene.HIGH_COLLS))
check("intersection_detected", validate.intersections([("PROP_Box", "PROP_Overlap")], objs) != [])
bpy.data.objects.remove(bpy.data.objects["PROP_Overlap"], do_unlink=True)

# cameras + renders
objs = validate.mesh_objects(scene.objects_in(scene.HIGH_COLLS))
cams = cameras.rig_from_bounds(objs)
render.workbench(cams["CAM_PERSPECTIVE"], os.path.join(OUT, "clay.png"), "CLAY")
render.workbench(cams["CAM_PERSPECTIVE"], os.path.join(OUT, "material.png"), "MATERIAL")
render.studio_lights((1, 1, 0.8), 4.0)
render.beauty(cams["CAM_PERSPECTIVE"], os.path.join(OUT, "beauty_eevee.png"), (640, 400), 8)
check("renders", all(os.path.isfile(os.path.join(OUT, f)) for f in ("clay.png", "material.png", "beauty_eevee.png")))
cam, pivot = anim.turntable((1, 1, 0.8), 9.0, 3.0, (1, 24))
render.animation(cam, os.path.join(OUT, "turntable.mp4"), 1, 24, (480, 270))
check("video", os.path.isfile(os.path.join(OUT, "turntable.mp4")) and os.path.getsize(os.path.join(OUT, "turntable.mp4")) > 1000)

# export + roundtrip
scene.save(os.path.join(OUT, "smoke.blend"))
root = scene.root(A)
exp = [o for o in scene.objects_in(scene.HIGH_COLLS + ("07_DETAILS",)) if o.type in ("MESH", "ARMATURE")]
for o in exp:
    if o.parent is None:
        o.parent = root
glb = os.path.join(OUT, "smoke.glb")
export.glb([root] + exp, glb, animations=True, skins=True)
check("glb_written", os.path.getsize(glb) > 10000)

print("\n[SMOKE] RESULT:", "ALL PASS" if not fails else f"FAILED: {fails}")
if fails:
    raise SystemExit(1)
