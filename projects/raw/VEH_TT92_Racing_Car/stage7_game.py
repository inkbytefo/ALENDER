"""
STAGE 7 - GAME EXPORT (Godot 4.x)     python wb.py build VEH_TT92_Racing_Car --stage 7

Opens the painted pipeline file (stage 5) and produces an engine package in output/<A>/godot/:
    VEH_TT92_Racing_Car.glb     recommended for Godot (textures embedded)
    VEH_TT92_Racing_Car.fbx     same meshes / UVs, textures referenced from textures/
    textures/T_TT92_<Set>_{BaseColor,Normal,ORM,Roughness,Metallic,AO[,Emission]}.png     4096 px
    materials/M_TT92_<Set>_ORM.tres        ORMMaterial3D      (packed ORM texture)
    materials/M_TT92_<Set>_Standard.tres   StandardMaterial3D (separate roughness / metallic / AO)
    README_GODOT.md, export_report.json

What happens (Godot / glTF best practice, see README_GODOT.md for the sources):
  1. game meshes  the 250 HIGH parts (modifiers applied, triangulated) are merged into 7 objects:
                  Body, Mechanical, SteeringWheel, Wheel_FL/FR/RL/RR - few draw calls, and the parts
                  that move keep their own node with the pivot on the axle
                  (the helical heat-wrap strands are dropped: the wrap core carries the look)
  2. UVs          one non-overlapping 0-1 atlas per texture set ("UVMap"): smart project + pack
                  Body set = shell, front, cockpit, fasteners; Mech set = wheels, engine, exhaust,
                  suspension. Two sets keep the texel density up.
  3. bake         the procedural master material cannot be exported, so it is baked (Cycles) per
                  set: base colour, roughness, metallic, emission (emit passes through the master
                  group), tangent normal (OpenGL +Y), ambient occlusion; packed ORM = R AO,
                  G roughness, B metallic (glTF / Godot convention)
  4. materials    2 plain Principled materials (M_TT92_Body, M_TT92_Mech), backface culling on
  5. collision    one convex hull named *-convcolonly (Godot import hint)
  6. export       GLB (+Y up, tangents, no Draco) and FBX (FBX units scale, -Z forward, Y up)
  7. verify       both files are re-imported into an empty scene and measured; review renders of
                  the baked game model in renders/game_*.png
Godot-side test: GODOTTESTING/testingarea (test_scene.tscn) - import + screenshot with Godot 4.7.2.
"""
import os
import re
import json
import time
import numpy as np
import bpy
import bmesh
from mathutils import Vector

import stagelib as SL
from stagelib import L, PT, A
from workbench import paths
from workbench.bl import scene, render, game, uv, assets
from workbench.bl.presentation import use_gpu
import paint

SIZE = int(os.environ.get("TT92_TEX", "4096"))     # texture size per set (env TT92_TEX=512 for a quick test)
MARGIN = max(4, SIZE // 256)        # bake dilation in px (mip-map safe)
COLL = "50_GAME"
OUT = paths.out(A, "godot")
TEX = os.path.join(OUT, "textures")
os.makedirs(TEX, exist_ok=True)
os.makedirs(os.path.join(OUT, "materials"), exist_ok=True)
EMISSION_STRENGTH = paint.INSTANCES["MAT_AB_GLOW"]["p"]["Emission Strength"]


def classify(name):
    """HIGH object name -> (game object, texture set)."""
    m = re.match(r"WHEEL_(Front|Rear)_\w+_(L|R)$", name) or re.match(r"BRAKE_Drum_(Front|Rear)_(L|R)$", name)
    if m:
        return f"Wheel_{m.group(1)[0]}{m.group(2)}", "Mech"
    if re.match(r"COCKPIT_Steering(Wheel|Spokes)", name):
        return "SteeringWheel", "Body"
    if re.match(r"BODY_|NOSE_|AERO_|COCKPIT_|FASTENER_|ENGINE_AirFilter", name):
        return "Body", "Body"
    return "Mechanical", "Mech"


t_start = time.time()
scene.open_blend(paths.out(A, "blend", A + ".blend"))
if paint.MASTER not in bpy.data.node_groups:
    raise SystemExit("[STAGE7] FAIL: the model is not painted - run stage 5 first")
sc = bpy.context.scene
high = [o for o in SL.high() if o.type == "MESH"]

# ================================================================ 1. game meshes
# the helical heat-wrap strands unwrap into metre-long UV strips and cost 9.6k triangles: the game mesh
# keeps the wrap core under them (same wrap material, baked with its normal map) and drops the strands
DROP = re.compile(r"EXHAUST_Wrap_[LR]$")
groups = {}
for o in high:
    if DROP.match(o.name):
        continue
    gname, tset = classify(o.name)
    c = game.evaluated_copy(o, "TMP_" + o.name, COLL)
    if o.name == "EXHAUST_AB_Glow":                  # seen from inside: faces must point inwards
        c.data.flip_normals()
    groups.setdefault((gname, tset), []).append(c)
objs, set_of = {}, {}
for (gname, tset), parts in sorted(groups.items()):
    ob = assets.join(parts, gname, COLL)
    for p in parts:
        bpy.data.objects.remove(p, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)        # fixed triangulation = same tangents in the engine
    bm.to_mesh(ob.data)
    bm.free()
    while ob.data.uv_layers:
        ob.data.uv_layers.remove(ob.data.uv_layers[0])
    ob.data.uv_layers.new(name="UVMap")
    objs[gname], set_of[gname] = ob, tset
bpy.context.view_layer.update()
print("[STAGE7] game objects:", {n: game.tris(o) for n, o in objs.items()})

# ================================================================ 2. UV atlases (one per set)
uv_info = {}
for tset in ("Body", "Mech"):
    sel = [o for n, o in objs.items() if set_of[n] == tset]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in sel:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = sel[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.0, scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin=0.0015, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    ov = uv.overlap(sel, "UVMap", res=1024)
    td = uv.texel_density(sel, "UVMap", SIZE)
    uv_info[tset] = dict(objects=[o.name for o in sel], overlap=ov, texel_px_per_m=td["per_object"],
                         texel_min=td["min"], texel_max=td["max"], texel_spread=td["spread"])
    print(f"[STAGE7] UV {tset}: overlap {ov}  texel {td['min']}..{td['max']} px/m (spread {td['spread']})")

# ================================================================ pivots + hierarchy
for tag, (x, v, R, W) in PT.WHEELS.items():
    pos, side = tag.split("_")
    scene.set_origin(objs[f"Wheel_{pos[0]}{side}"], (x, L.Y(v), R))
scene.set_origin(objs["SteeringWheel"], (L.X(L.STEER_WHEEL_PX[0]), L.Y(L.STEER_WHEEL_PX[1]), L.STEER_WHEEL_Z))
root = bpy.data.objects.new("TT92", None)
scene.coll(COLL).objects.link(root)
col = game.collision({"body": [objs["Body"]]}, {"body": "hull"}, "godot", "Body", COLL)
for ob in list(objs.values()) + [c[1] for c in col]:
    ob.parent = root
bpy.context.view_layer.update()

# ================================================================ 3. bake
sc.render.engine = "CYCLES"
device = use_gpu()
sc.cycles.use_denoising = False
if sc.world is None:
    sc.world = bpy.data.worlds.new("WORLD_Bake")
sc.world.light_settings.distance = 0.25
targets = {t: assets.join([o for n, o in objs.items() if set_of[n] == t], "BAKE_" + t, COLL) for t in ("Body", "Mech")}
for o in bpy.data.objects:                           # AO must only see the two bake targets
    o.hide_render = o.name not in ("BAKE_Body", "BAKE_Mech")
for t in targets.values():
    t.hide_set(False)

grp = bpy.data.node_groups[paint.MASTER]
g_out = next(n for n in grp.nodes if n.type == "GROUP_OUTPUT")
bsdf = next(n for n in grp.nodes if n.type == "BSDF_PRINCIPLED")
emit = grp.nodes.new("ShaderNodeEmission")
src = {k: bsdf.inputs[s].links[0].from_socket for k, s in
       (("base", "Base Color"), ("rough", "Roughness"), ("metal", "Metallic"), ("emission", "Emission Color"),
        ("coat", "Coat Weight"), ("coat_rough", "Coat Roughness"))}
# a clear coat cannot be exported: fold most of it into the roughness the engine will see
k_coat = grp.nodes.new("ShaderNodeMath"); k_coat.operation = "MULTIPLY"; k_coat.inputs[1].default_value = 0.75
grp.links.new(src["coat"], k_coat.inputs[0])
r_eff = grp.nodes.new("ShaderNodeMix"); r_eff.data_type = "FLOAT"
grp.links.new(k_coat.outputs[0], next(s for s in r_eff.inputs if s.identifier == "Factor_Float"))
grp.links.new(src["rough"], next(s for s in r_eff.inputs if s.identifier == "A_Float"))
grp.links.new(src["coat_rough"], next(s for s in r_eff.inputs if s.identifier == "B_Float"))
src["rough"] = next(s for s in r_eff.outputs if s.identifier == "Result_Float")


def route(sock):
    """master group output = emission of `sock` (bake a material input) or the real BSDF (None)."""
    for l in list(g_out.inputs[0].links):
        grp.links.remove(l)
    if sock is None:
        grp.links.new(bsdf.outputs[0], g_out.inputs[0])
    else:
        for l in list(emit.inputs["Color"].links):
            grp.links.remove(l)
        grp.links.new(sock, emit.inputs["Color"])
        grp.links.new(emit.outputs[0], g_out.inputs[0])


def pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def save(img, path):
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


PASSES = [  # key, bake type, routed socket, non-colour, samples
    ("base", "EMIT", "base", False, 4), ("rough", "EMIT", "rough", True, 4), ("metal", "EMIT", "metal", True, 2),
    ("emission", "EMIT", "emission", False, 2), ("normal", "NORMAL", None, True, 8), ("ao", "AO", None, True, 48),
]
tex, bake_times = {}, {}
for tset, target in targets.items():
    mats = [m for m in target.data.materials if m]
    nodes = []
    for m in mats:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        m.node_tree.nodes.active = n
        nodes.append((m, n))
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    imgs = {}
    for key, btype, sock, non_color, samples in PASSES:
        t0 = time.time()
        img = bpy.data.images.new(f"BAKE_{tset}_{key}", SIZE, SIZE, alpha=False)
        img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        for m, n in nodes:
            n.image = img
        route(src[sock] if sock else None)
        sc.cycles.samples = samples
        kw = dict(type=btype, margin=MARGIN, use_clear=True, target="IMAGE_TEXTURES")
        if btype == "NORMAL":
            kw["normal_space"] = "TANGENT"
        bpy.ops.object.bake(**kw)
        imgs[key] = img
        bake_times[f"{tset}_{key}"] = round(time.time() - t0, 1)
        print(f"[STAGE7] bake {tset:<5}{key:<9}{bake_times[f'{tset}_{key}']:>7.1f} s")
    route(None)
    for m, n in nodes:
        m.node_tree.nodes.remove(n)
    orm = np.ones((SIZE, SIZE, 4), np.float32)
    orm[..., 0] = pixels(imgs["ao"])[..., 0]
    orm[..., 1] = pixels(imgs["rough"])[..., 0]
    orm[..., 2] = pixels(imgs["metal"])[..., 0]
    oimg = bpy.data.images.new(f"BAKE_{tset}_orm", SIZE, SIZE, alpha=False)
    oimg.colorspace_settings.name = "Non-Color"
    oimg.pixels.foreach_set(orm.ravel())
    emis = pixels(imgs["emission"])[..., :3]
    tex[tset] = dict(
        base=save(imgs["base"], os.path.join(TEX, f"T_TT92_{tset}_BaseColor.png")),
        normal=save(imgs["normal"], os.path.join(TEX, f"T_TT92_{tset}_Normal.png")),
        orm=save(oimg, os.path.join(TEX, f"T_TT92_{tset}_ORM.png")),
        # the same three maps as separate greyscale files, for StandardMaterial3D
        roughness=save(imgs["rough"], os.path.join(TEX, f"T_TT92_{tset}_Roughness.png")),
        metallic=save(imgs["metal"], os.path.join(TEX, f"T_TT92_{tset}_Metallic.png")),
        ao=save(imgs["ao"], os.path.join(TEX, f"T_TT92_{tset}_AO.png")),
        stats=dict(base_mean=[round(float(v), 3) for v in pixels(imgs["base"])[..., :3].reshape(-1, 3).mean(0)],
                   normal_mean=[round(float(v), 3) for v in pixels(imgs["normal"])[..., :3].reshape(-1, 3).mean(0)],
                   orm_mean=[round(float(v), 3) for v in orm[..., :3].reshape(-1, 3).mean(0)],
                   emission_max=round(float(emis.max()), 3)))
    if emis.max() > 0.02:
        tex[tset]["emission"] = save(imgs["emission"], os.path.join(TEX, f"T_TT92_{tset}_Emission.png"))
    print(f"[STAGE7] textures {tset}:", tex[tset]["stats"])
for n in (emit, k_coat, r_eff):
    grp.nodes.remove(n)
for t in targets.values():
    bpy.data.objects.remove(t, do_unlink=True)

# ================================================================ 4. game materials
gmat = {}
for tset in ("Body", "Mech"):
    m = game.game_material(f"M_TT92_{tset}", tex[tset])
    if "emission" in tex[tset]:
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        e = nt.nodes.new("ShaderNodeTexImage")
        e.image = bpy.data.images.load(tex[tset]["emission"], check_existing=True)
        e.location = (-700, -600)
        nt.links.new(e.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = EMISSION_STRENGTH
    m.use_backface_culling = True
    gmat[tset] = m
for n, o in objs.items():
    game.assign_single([o], gmat[set_of[n]])

# ================================================================ Godot materials (.tres): ORM + Standard
RES = f"res://{A}/textures/"            # put the godot/ folder into the project as res://<A>/


def tres(kind, tset):
    t = tex[tset]
    files = [("albedo", "BaseColor"), ("normal", "Normal")]
    files += [("orm", "ORM")] if kind == "ORM" else [("rough", "Roughness"), ("metal", "Metallic"), ("ao", "AO")]
    if "emission" in t:
        files.append(("emission", "Emission"))
    ext = [f'[ext_resource type="Texture2D" path="{RES}T_TT92_{tset}_{suffix}.png" id="{i + 1}"]'
           for i, (_, suffix) in enumerate(files)]
    rid = {k: f'ExtResource("{i + 1}")' for i, (k, _) in enumerate(files)}
    body = [f"albedo_texture = {rid['albedo']}"]
    if kind == "ORM":
        body.append(f"orm_texture = {rid['orm']}")
    else:                                # grayscale files: channel 4 = TEXTURE_CHANNEL_GRAYSCALE
        body += ["metallic = 1.0", f"metallic_texture = {rid['metal']}", "metallic_texture_channel = 4",
                 "roughness = 1.0", f"roughness_texture = {rid['rough']}", "roughness_texture_channel = 4",
                 "ao_enabled = true", f"ao_texture = {rid['ao']}", "ao_texture_channel = 4"]
    body += ["normal_enabled = true", f"normal_texture = {rid['normal']}"]
    if "emission" in t:
        body += ["emission_enabled = true", f"emission_texture = {rid['emission']}",
                 f"emission_energy_multiplier = {EMISSION_STRENGTH}"]
    typ = "ORMMaterial3D" if kind == "ORM" else "StandardMaterial3D"
    head = f'[gd_resource type="{typ}" load_steps={len(files) + 1} format=3]'
    lines = [head, ''] + ext + ['', '[resource]', f'resource_name = "M_TT92_{tset}_{kind}"'] + body
    path = os.path.join(OUT, "materials", f"M_TT92_{tset}_{kind}.tres")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return os.path.basename(path)


tres_files = [tres(kind, tset) for tset in ("Body", "Mech") for kind in ("ORM", "Standard")]
print("[STAGE7] godot materials:", tres_files)
import shutil
shutil.copyfile(os.path.join(SL.HERE, "GODOT.md"), os.path.join(OUT, "README_GODOT.md"))

# ================================================================ review renders of the game model
for o in bpy.data.objects:
    o.hide_render = not (o.name in objs)
    if o.type == "MESH":
        o.hide_set(o.name not in objs)
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.045, 0.047, 0.05, 1.0)
render.studio_lights(center=(0, 0, 0.4), size=2.5, strength=1.6)
for o in bpy.data.objects:
    if o.name.startswith("REVIEW_LIGHT_"):
        o.hide_render = False
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
for tag, loc, tgt in (("game_front_34", (2.4, -3.0, 1.35), (0.0, -0.25, 0.42)),
                      ("game_rear_34", (-2.2, 3.1, 1.25), (0.0, 0.45, 0.42))):
    cd = bpy.data.cameras.new("CAM_" + tag)
    cam = bpy.data.objects.new("CAM_" + tag, cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(SL.RENDERS, tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("[STAGE7] render", sc.render.filepath)

# ================================================================ 5/6. save + export
export_objs = [root] + list(objs.values()) + [c[1] for c in col]
for o in export_objs:
    o.hide_set(False)
    o.hide_render = False
game_tris = sum(game.tris(o) for o in objs.values())
world = [o.matrix_world @ Vector(c) for o in objs.values() for c in o.bound_box]
dims = [round(max(p[i] for p in world) - min(p[i] for p in world), 3) for i in range(3)]
scene.save(paths.out(A, "blend", A + "_GAME.blend"))

glb_path = os.path.join(OUT, A + ".glb")
fbx_path = os.path.join(OUT, A + ".fbx")
bpy.ops.object.select_all(action="DESELECT")
for o in export_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=False, export_texcoords=True, export_normals=True, export_tangents=True,
                          export_materials="EXPORT", export_image_format="AUTO", export_cameras=False,
                          export_lights=False, export_animations=False, export_skins=False,
                          export_draco_mesh_compression_enable=False, export_extras=False)
bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={"EMPTY", "MESH"},
                         apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
                         use_tspace=True, mesh_smooth_type="OFF", use_mesh_modifiers=False,
                         path_mode="RELATIVE", embed_textures=False, bake_anim=False, add_leaf_bones=False)
print("[STAGE7] exported", glb_path, round(os.path.getsize(glb_path) / 1e6, 1), "MB |", fbx_path,
      round(os.path.getsize(fbx_path) / 1e6, 1), "MB")


# ================================================================ 7. verify by re-import (destroys the scene)
def reimport(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.import_scene.fbx(filepath=path)
    bpy.context.view_layer.update()
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in ms if "convcol" not in o.name for c in o.bound_box]
    return dict(
        nodes=sorted(o.name for o in bpy.data.objects),
        meshes=len(ms), tris=sum(game.tris(o) for o in ms if "convcol" not in o.name),
        uv_layers=sorted({l.name for o in ms for l in o.data.uv_layers}),
        meshes_without_uv=[o.name for o in ms if not o.data.uv_layers and "convcol" not in o.name],
        materials=sorted(m.name for m in bpy.data.materials if m.users),
        images={i.name: list(i.size) for i in bpy.data.images if i.size[0]},
        dims_m=[round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)],
        scales=sorted({tuple(round(s, 4) for s in o.matrix_world.to_scale()) for o in ms}))


check = {"glb": reimport(glb_path), "fbx": reimport(fbx_path)}
ok = True
for kind, r in check.items():
    good = (r["tris"] == game_tris and not r["meshes_without_uv"] and sorted(r["dims_m"]) == sorted(dims)
            and len([m for m in r["materials"] if m.startswith("M_TT92_")]) == 2)
    ok &= good
    print(f"[STAGE7] re-import {kind}: {'OK' if good else 'FAIL'} meshes {r['meshes']} tris {r['tris']}/{game_tris} "
          f"dims {r['dims_m']} (model {dims}) materials {r['materials']} uv {r['uv_layers']} images {len(r['images'])}")

report = dict(asset=A, engine="Godot 4.x", texture_size=SIZE, bake_device=device, bake_seconds=bake_times,
              tris=game_tris, dims_m=dims, uv=uv_info, textures={k: {m: os.path.basename(p) for m, p in v.items()
                                                                  if m != "stats"} | {"stats": v["stats"]}
                                                              for k, v in tex.items()},
              collision=[(k, f) for k, _, f in [(c[0], None, c[2]) for c in col]],
              godot_materials=tres_files, reimport=check, seconds=round(time.time() - t_start, 1))
with open(os.path.join(OUT, "export_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("[STAGE7]", "PASS" if ok else "FAIL", f"({report['seconds']} s)")
if not ok:
    raise SystemExit("[STAGE7] FAIL: re-import check")
