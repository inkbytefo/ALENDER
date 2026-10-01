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
check("boolean_no_empty_slots", all(m is not None for m in wall.data.materials) and len(wall.data.materials) == 1,
      [m.name if m else None for m in wall.data.materials])
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

# PBR: synthetic ambientCG-style texture set -> scan -> node tree (no downloaded files needed)
from workbench import pbrlib
from workbench.bl import pbr, assets
tdir = os.path.join(OUT, "pbr_lib", "Test001_1K-PNG")
os.makedirs(tdir, exist_ok=True)
for suffix, rgba in (("Color", (0.6, 0.2, 0.1, 1)), ("Roughness", (0.4, 0.4, 0.4, 1)),
                     ("NormalGL", (0.5, 0.5, 1.0, 1)), ("Metalness", (0.0, 0.0, 0.0, 1))):
    im = bpy.data.images.new("tmp_" + suffix, 8, 8)
    im.pixels[:] = list(rgba) * 64
    im.filepath_raw = os.path.join(tdir, f"Test001_1K-PNG_{suffix}.png")
    im.file_format = "PNG"
    im.save()
tset = pbrlib.find("Test001", os.path.dirname(tdir))
check("pbr_scan", set(tset["maps"]) >= {"base_color", "roughness", "normal_gl", "metallic"}, sorted(tset["maps"]))
pm = materials.ensure({"MAT_PBR_TEST": dict(pbr=tset, tile_m=0.5)})["MAT_PBR_TEST"]
bsdf = next(n for n in pm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
check("pbr_material", bsdf.inputs["Base Color"].is_linked and bsdf.inputs["Normal"].is_linked
      and bsdf.inputs["Roughness"].is_linked and abs(pm.diffuse_color[0] - 0.318) < 0.03,   # sRGB 0.6 -> linear
      f"diffuse {tuple(round(c, 2) for c in pm.diffuse_color[:3])}")
pbr.assign(bpy.data.objects["PROP_Box"], pm)
# assets: join + inspect
j = assets.join([bpy.data.objects["PROP_Cyl"], bpy.data.objects["PROP_Pipe"]], "PROP_Joined", C)
rep = assets.inspect([j])
check("assets_join", rep["meshes"] == 1 and rep["tris"] > 100, f"{rep['tris']} tris")
bpy.data.objects.remove(j, do_unlink=True)

# presentation studio (cyclorama + light rig + auto-framed camera + Cycles still)
from workbench.bl import presentation as pres
from bpy_extras.object_utils import world_to_camera_view
pobjs = [bpy.data.objects[n] for n in ("PROP_Box", "PROP_Cyl", "PROP_Wheel")]
stg = pres.studio(pobjs, "studio_dark")
check("pres_stage", bpy.data.objects.get("PRES_Cyclorama") is not None and len(stg["lights"]) == len(pres.LIGHTS))
pc = pres.hero_cameras(pobjs, {"HERO": pres.SHOTS["HERO_FRONT_34"][:3] + (0.07, (320, 180))})["HERO"]
bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 320, 180
pp = [world_to_camera_view(bpy.context.scene, pc, p) for p in pres.asset_points(pobjs)]
check("pres_framing", all(0.0 <= p.x <= 1.0 and 0.0 <= p.y <= 1.0 for p in pp)
      and max(max(p.x for p in pp) - min(p.x for p in pp), max(p.y for p in pp) - min(p.y for p in pp)) > 0.8,
      "asset fills the frame inside margins")
pres.render_stills({"hero": pc}, OUT, "pres_", "CYCLES", 8)
check("pres_render", os.path.isfile(os.path.join(OUT, "pres_hero.png")))
for o in [o for o in bpy.data.objects if o.name.startswith("PRES_")]:
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- staged pipeline building blocks
import numpy as np
from workbench import stages, silhouette, glbinfo
from workbench.bl import prim, uv, game
P2 = stages.profile(2)
check("stages_names", stages.nm(P2, "RECV_Body_PRIM") == "RECV_Body_LP" and stages.base_name("MAG_Body_LOD2") == "MAG_Body"
      and stages.parse_stage_args(["--from", "3"]) == [3, 4])
check("builder_tag", bpy.data.objects["PROP_Box"].get("wb_builder") == "box"
      and bpy.data.objects["PROP_Plate"].get("wb_builder") == "plate")
mods.subsurf(bpy.data.objects["PROP_Plate"])
check("policy_H01", validate.smoothing_problems([bpy.data.objects["PROP_Plate"], lo]) == ["PROP_Plate"])
bpy.data.objects["PROP_Plate"].modifiers.clear()
check("policy_N01", validate.naming_problems([bpy.data.objects["PROP_Box"], wall], "_LP") == ["PROP_Box", "ARCH_Wall"])
hy = validate.hygiene([bpy.data.objects["PROP_Box"], bpy.data.objects["PROP_Wheel"]])
check("hygiene_closed", hy["total"]["non_manifold"] == 0 and hy["total"]["boundary"] == 0
      and hy["total"]["inverted"] == 0 and hy["total"]["flipped"] == 0, hy["total"])
flip = mesh.box("PROP_Flip", "08_TEMP", (5, 5, 0.5), (0.4, 0.4, 0.4))
flip.data.polygons[0].flip()
hy = validate.hygiene([flip, mesh.grid("PROP_Open", "08_TEMP", 1.0)])
check("hygiene_detects", hy["total"]["flipped"] > 0 and hy["total"]["boundary"] == 4, hy["total"])
for n in ("PROP_Flip", "PROP_Open"):
    bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
pb = prim.box_px("PRIM_Box_PRIM", "08_TEMP", [(500, 600), (700, 600), (650, 450)], 0.05, "MAT_A")
pp = prim.plate_px("PRIM_Plate_PRIM", "08_TEMP", [(500, 600), (600, 598), (700, 600), (650, 450), (520, 480)], 0.05, tol=5)
pw = prim.wheel_px("PRIM_Wheel_PRIM", "08_TEMP", (600, 500), 40, 0.03, 10, "MAT_R")
check("prim_builders", abs(pb.dimensions.y - 0.513) < 0.002 and len(pp.data.polygons) == 6   # ref tilted 2 deg
      and abs(pw.dimensions.z - 0.2 * math.cos(math.pi / 10)) < 0.002,
      f"box {pb.dimensions.y:.3f} plate faces {len(pp.data.polygons)} wheel {pw.dimensions.z:.3f}")
for o in (pb, pp, pw):
    bpy.data.objects.remove(o, do_unlink=True)
ua = [bpy.data.objects[n] for n in ("PROP_Cyl", "PROP_Wheel")]
info = uv.atlas(ua)
ov = uv.overlap(ua)
check("uv_atlas", "UV_Bake" in ua[0].data.uv_layers and ov["overlap"] < 0.01 and ov["outside"] == 0.0, (info, ov))
check("uv_texel", uv.texel_density(ua)["spread"] < 2.0, uv.texel_density(ua))
g0 = game.evaluated_copy(bpy.data.objects["PROP_Wheel"], "PROP_Wheel_LOD0", "08_TEMP", keep_uv="UV_Bake")
g1 = game.lod_copy(g0, 0.5, "PROP_Wheel_LOD1", "08_TEMP")
check("game_lod", len(g0.data.uv_layers) == 1 and game.tris(g1) <= game.tris(g0) * 0.6, f"{game.tris(g0)} -> {game.tris(g1)}")
cols = game.collision({"wheel": [g0]}, {"wheel": "hull"}, "godot", "PROP_Wheel_LOD0", "08_TEMP")
check("game_collision", len(cols) == 1 and cols[0][2] <= 250 and cols[0][1].name.endswith("-convcolonly"),
      [(k, o.name, f) for k, o, f in cols])
tex = game.bake([bpy.data.objects["PROP_Wheel"]], [g0], os.path.join(OUT, "bake"), 64, prefix="T_smoke", ao_samples=4)
nm_ = tex["stats"]["normal_mean"]
check("game_bake", all(os.path.isfile(tex[k]) for k in ("base", "orm", "normal")) and nm_[2] > 0.7,
      tex["stats"])
gm = game.game_material("MAT_Smoke_Baked", tex)
check("game_material", any(n.type == "GROUP" for n in gm.node_tree.nodes)
      and next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Normal"].is_linked)
for o in [g0, g1] + [c for _, c, _ in cols]:
    bpy.data.objects.remove(o, do_unlink=True)
ref_m = silhouette.rasterize([[(10, 10), (60, 10), (60, 40), (10, 40)]], (80, 50))
ren_m = silhouette.rasterize([[(12, 10), (60, 10), (60, 40), (12, 40)]], (80, 50))
sm = silhouette.metrics(ref_m, ren_m)
check("silhouette_metrics", ref_m.sum() == 1500 and 0.95 < sm["iou"] < 0.97 and sm["b_max"] == 2.0, sm)
cam_s = cams["CAM_PERSPECTIVE"]
cam_s["wb_image_size"] = (320, 200)
sp_ = render.silhouette(cam_s, [bpy.data.objects["PROP_Box"]], os.path.join(OUT, "sil_box.png"))
al = render.read_alpha(sp_)
check("render_silhouette", al.shape == (200, 320) and 50 < int((al > 0.5).sum()) < 64000, al.shape)
del cam_s["wb_image_size"]

# Calibrated perspective camera: a known optical-axis point must reproject to
# image centre even when the camera is neither SIDE nor TOP.
from types import SimpleNamespace
from mathutils import Vector
cal_loc = Vector((-4.0, -6.0, 2.0))
cal_target = Vector((0.0, 0.0, 0.7))
cal_rot = (cal_target - cal_loc).to_track_quat('-Z', 'Y').to_euler()
cal_ref = SimpleNamespace(view='CALIBRATED', image_size=(640, 360), S=200,
                          lens=45.0, cam_loc=tuple(cal_loc), cam_rot=tuple(cal_rot))
cal_cam = cameras.reference_camera(cal_ref, [(tuple(cal_target), (320, 180))], name='CAM_CAL_TEST')
check('calibrated_camera_projection', cal_cam['anchor_reprojection_error_px'] < 0.01,
      cal_cam['anchor_reprojection_error_px'])

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
gi = glbinfo.read(glb)
check("glbinfo", gi["tris"] > 1000 and gi["meshes"] >= 10 and gi["skins"] == 1, {k: gi[k] for k in ("tris", "meshes", "materials")})

print("\n[SMOKE] RESULT:", "ALL PASS" if not fails else f"FAILED: {fails}")
if fails:
    raise SystemExit(1)
