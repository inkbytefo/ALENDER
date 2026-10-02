"""
Godot 4.x engine package from a model painted with workbench.bl.master (docs/12).

    from workbench.bl import godot
    rep = godot.export_package(A, high_objs, classify, pivots, out_dir, prefix="Gemini", root_name="Gemini")

classify(name) -> (game object name, texture set name)   set None = keep the object's own material
                                                           (glass etc.: not unwrapped, not baked)
                  or None to drop the object from the game mesh
pivots = {game object name: (x, y, z)}                    origins of the parts that move

What it does (same recipe as projects/VEH_TT92_Racing_Car/stage7_game.py, where it was developed):
  1. evaluated, triangulated copies of the parts merged into the game objects (few draw calls)
  2. one non-overlapping 0-1 UV atlas per texture set (smart project + pack), layer "UVMap"
  3. Cycles bakes through the master group (master.BakeRouter): base colour, roughness, metallic,
     emission (EMIT), tangent normal (OpenGL +Y), AO; ORM packed R = AO, G = roughness, B = metallic,
     plus the three maps as separate files
  4. plain Principled materials M_<prefix>_<Set> (back-face culling on), Godot .tres for
     ORMMaterial3D and StandardMaterial3D
  5. convex collision hull named *-convcolonly
  6. GLB (+Y up, tangents, no Draco) and FBX (FBX units scale, -Z forward, Y up)
  7. both files re-imported into an empty scene and measured  -> DESTROYS the scene: the game
     scene is saved to output/<A>/blend/<A>_GAME.blend first
Returns the report dict (also written to <out_dir>/export_report.json); report["ok"] is the verdict.
"""
import os
import json
import time
import numpy as np
import bpy
import bmesh
from mathutils import Vector

from workbench import paths
from workbench.bl import scene, game, uv, assets, master
from workbench.bl.presentation import use_gpu

COLL = "50_GAME"
PASSES = [  # key, bake type, routed socket, non-colour, samples
    ("base", "EMIT", "base", False, 4), ("rough", "EMIT", "rough", True, 4), ("metal", "EMIT", "metal", True, 2),
    ("emission", "EMIT", "emission", False, 2), ("normal", "NORMAL", None, True, 8), ("ao", "AO", None, True, 48),
]


def _pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _save(img, path):
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


def _tres(out_dir, res_dir, prefix, tset, kind, has_emission, strength):
    files = [("albedo", "BaseColor"), ("normal", "Normal")]
    files += [("orm", "ORM")] if kind == "ORM" else [("rough", "Roughness"), ("metal", "Metallic"), ("ao", "AO")]
    if has_emission:
        files.append(("emission", "Emission"))
    ext = [f'[ext_resource type="Texture2D" path="{res_dir}textures/T_{prefix}_{tset}_{suffix}.png" id="{i + 1}"]'
           for i, (_, suffix) in enumerate(files)]
    rid = {k: f'ExtResource("{i + 1}")' for i, (k, _) in enumerate(files)}
    body = [f"albedo_texture = {rid['albedo']}"]
    if kind == "ORM":
        body.append(f"orm_texture = {rid['orm']}")
    else:                                    # grayscale files: channel 4 = TEXTURE_CHANNEL_GRAYSCALE
        body += ["metallic = 1.0", f"metallic_texture = {rid['metal']}", "metallic_texture_channel = 4",
                 "roughness = 1.0", f"roughness_texture = {rid['rough']}", "roughness_texture_channel = 4",
                 "ao_enabled = true", f"ao_texture = {rid['ao']}", "ao_texture_channel = 4"]
    body += ["normal_enabled = true", f"normal_texture = {rid['normal']}"]
    if has_emission:
        body += ["emission_enabled = true", f"emission_texture = {rid['emission']}",
                 f"emission_energy_multiplier = {strength}"]
    typ = "ORMMaterial3D" if kind == "ORM" else "StandardMaterial3D"
    lines = [f'[gd_resource type="{typ}" load_steps={len(files) + 1} format=3]', ""] + ext + \
            ["", "[resource]", f'resource_name = "M_{prefix}_{tset}_{kind}"'] + body
    name = f"M_{prefix}_{tset}_{kind}.tres"
    with open(os.path.join(out_dir, "materials", name), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return name


def _reimport(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.import_scene.fbx(filepath=path)
    bpy.context.view_layer.update()
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    vis = [o for o in ms if "convcol" not in o.name]
    pts = [o.matrix_world @ Vector(c) for o in vis for c in o.bound_box]
    return dict(nodes=sorted(o.name for o in bpy.data.objects), meshes=len(ms),
                tris=sum(game.tris(o) for o in vis),
                uv_layers=sorted({l.name for o in ms for l in o.data.uv_layers}),
                meshes_without_uv=[o.name for o in vis if not o.data.uv_layers],
                materials=sorted(m.name for m in bpy.data.materials if m.users),
                images={i.name: list(i.size) for i in bpy.data.images if i.size[0]},
                dims_m=[round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)])


def export_package(asset, high, classify, pivots, out_dir, prefix, root_name=None, size=4096,
                   emission_strength=1.0, res_dir=None, collision_from="Body", readme=None):
    t_start = time.time()
    margin = max(4, size // 256)
    tex_dir = os.path.join(out_dir, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "materials"), exist_ok=True)
    res_dir = res_dir or f"res://{asset}/"
    sc = bpy.context.scene

    # ---- 1. game meshes
    groups = {}
    for o in high:
        cls = classify(o.name)
        if cls is None:
            continue
        groups.setdefault(cls, []).append(game.evaluated_copy(o, "TMP_" + o.name, COLL))
    objs, set_of = {}, {}
    for (gname, tset), parts in sorted(groups.items(), key=lambda kv: kv[0][0]):
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
    sets = sorted({t for t in set_of.values() if t})
    print("[GODOT] game objects:", {n: game.tris(o) for n, o in objs.items()}, "sets", sets)

    # ---- 2. UV atlases
    uv_info = {}
    for tset in sets:
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
        td = uv.texel_density(sel, "UVMap", size)
        uv_info[tset] = dict(objects=[o.name for o in sel], overlap=ov, texel_min=td["min"], texel_max=td["max"],
                             texel_spread=td["spread"])
        print(f"[GODOT] UV {tset}: {ov}  texel {td['min']}..{td['max']} px/m")

    # ---- pivots, root, collision
    for name, pt in pivots.items():
        if name in objs:
            scene.set_origin(objs[name], pt)
    root = bpy.data.objects.new(root_name or prefix, None)
    scene.coll(COLL).objects.link(root)
    col = game.collision({"body": [objs[collision_from]]}, {"body": "hull"}, "godot", collision_from, COLL)
    for ob in list(objs.values()) + [c[1] for c in col]:
        ob.parent = root
    bpy.context.view_layer.update()

    # ---- 3. bake
    sc.render.engine = "CYCLES"
    device = use_gpu()
    sc.cycles.use_denoising = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("WORLD_Bake")
    sc.world.light_settings.distance = 0.25
    targets = {t: assets.join([o for n, o in objs.items() if set_of[n] == t], "BAKE_" + t, COLL) for t in sets}
    for o in bpy.data.objects:                           # AO must only see the bake targets
        o.hide_render = not o.name.startswith("BAKE_")
    for t in targets.values():
        t.hide_set(False)
    router = master.BakeRouter()
    tex, bake_times = {}, {}
    for tset, target in targets.items():
        nodes = []
        for m in [m for m in target.data.materials if m]:
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
            img = bpy.data.images.new(f"BAKE_{tset}_{key}", size, size, alpha=False)
            img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
            for m, n in nodes:
                n.image = img
            router.route(sock)
            sc.cycles.samples = samples
            kw = dict(type=btype, margin=margin, use_clear=True, target="IMAGE_TEXTURES")
            if btype == "NORMAL":
                kw["normal_space"] = "TANGENT"
            bpy.ops.object.bake(**kw)
            imgs[key] = img
            bake_times[f"{tset}_{key}"] = round(time.time() - t0, 1)
        router.route(None)
        for m, n in nodes:
            m.node_tree.nodes.remove(n)
        orm = np.ones((size, size, 4), np.float32)
        orm[..., 0] = _pixels(imgs["ao"])[..., 0]
        orm[..., 1] = _pixels(imgs["rough"])[..., 0]
        orm[..., 2] = _pixels(imgs["metal"])[..., 0]
        oimg = bpy.data.images.new(f"BAKE_{tset}_orm", size, size, alpha=False)
        oimg.colorspace_settings.name = "Non-Color"
        oimg.pixels.foreach_set(orm.ravel())
        emis = _pixels(imgs["emission"])[..., :3]

        def P(suffix):
            return os.path.join(tex_dir, f"T_{prefix}_{tset}_{suffix}.png")
        tex[tset] = dict(base=_save(imgs["base"], P("BaseColor")), normal=_save(imgs["normal"], P("Normal")),
                         orm=_save(oimg, P("ORM")), roughness=_save(imgs["rough"], P("Roughness")),
                         metallic=_save(imgs["metal"], P("Metallic")), ao=_save(imgs["ao"], P("AO")),
                         stats=dict(base_mean=[round(float(v), 3) for v in
                                               _pixels(imgs["base"])[..., :3].reshape(-1, 3).mean(0)],
                                    normal_mean=[round(float(v), 3) for v in
                                                 _pixels(imgs["normal"])[..., :3].reshape(-1, 3).mean(0)],
                                    emission_max=round(float(emis.max()), 3)))
        if emis.max() > 0.02:
            tex[tset]["emission"] = _save(imgs["emission"], P("Emission"))
        print(f"[GODOT] baked {tset}:", tex[tset]["stats"])
    router.close()
    for t in targets.values():
        bpy.data.objects.remove(t, do_unlink=True)

    # ---- 4. materials (+ .tres)
    tres = []
    for tset in sets:
        m = game.game_material(f"M_{prefix}_{tset}", tex[tset])
        if "emission" in tex[tset]:
            nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            e = nt.nodes.new("ShaderNodeTexImage")
            e.image = bpy.data.images.load(tex[tset]["emission"], check_existing=True)
            nt.links.new(e.outputs["Color"], b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = emission_strength
        m.use_backface_culling = True
        for n, o in objs.items():
            if set_of[n] == tset:
                game.assign_single([o], m)
        tres += [_tres(out_dir, res_dir, prefix, tset, kind, "emission" in tex[tset], emission_strength)
                 for kind in ("ORM", "Standard")]
    if readme and os.path.isfile(readme):
        import shutil
        shutil.copyfile(readme, os.path.join(out_dir, "README_GODOT.md"))

    # ---- 5/6. save + export
    export_objs = [root] + list(objs.values()) + [c[1] for c in col]
    for o in bpy.data.objects:
        o.hide_render = o not in export_objs
    for o in export_objs:
        o.hide_set(False)
    game_tris = sum(game.tris(o) for o in objs.values())
    world = [o.matrix_world @ Vector(c) for o in objs.values() for c in o.bound_box]
    dims = [round(max(p[i] for p in world) - min(p[i] for p in world), 3) for i in range(3)]
    scene.save(paths.out(asset, "blend", asset + "_GAME.blend"))
    glb_path = os.path.join(out_dir, asset + ".glb")
    fbx_path = os.path.join(out_dir, asset + ".fbx")
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

    # ---- 7. verify (destroys the scene)
    check = {"glb": _reimport(glb_path), "fbx": _reimport(fbx_path)}
    ok = True
    for kind, r in check.items():
        good = (r["tris"] == game_tris and not [n for n in r["meshes_without_uv"] if set_of.get(n.split(".")[0])]
                and sorted(r["dims_m"]) == sorted(dims)
                and len([m for m in r["materials"] if m.startswith(f"M_{prefix}_")]) == len(sets))
        ok &= good
        print(f"[GODOT] re-import {kind}: {'OK' if good else 'FAIL'} meshes {r['meshes']} tris {r['tris']}/{game_tris} "
              f"dims {r['dims_m']} (model {dims}) materials {r['materials']}")
    report = dict(asset=asset, engine="Godot 4.x", ok=bool(ok), texture_size=size, bake_device=device,
                  bake_seconds=bake_times, objects={n: set_of[n] for n in objs}, tris=game_tris, dims_m=dims,
                  uv=uv_info, textures={k: {m: os.path.basename(p) for m, p in v.items() if m != "stats"}
                                        | {"stats": v["stats"]} for k, v in tex.items()},
                  collision=[[c[0], c[2]] for c in col], godot_materials=tres, files=dict(
                      glb_mb=round(os.path.getsize(glb_path) / 1e6, 1), fbx_mb=round(os.path.getsize(fbx_path) / 1e6, 1)),
                  reimport=check, seconds=round(time.time() - t_start, 1))
    with open(os.path.join(out_dir, "export_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("[GODOT]", "PASS" if ok else "FAIL", f"({report['seconds']} s)")
    return report
