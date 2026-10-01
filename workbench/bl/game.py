"""
Stage 4 GAME: turn the Stage 2 LOWPOLY (LOD0 base) + Stage 3 DETAIL (bake source) into a
game-ready package (docs/12_GAME_READY.md).

    lod0 = game.copies(lp_objs, 0, "40_S4_GAME", keep_uv="UV_Bake")    # evaluated copies, 1 UV set
    game.set_pivots(lod0, PIVOTS)                                     # moving parts on their joints
    tex = game.bake(hp_objs, list(lod0.values()), folder, 2048)       # base / ORM / normal PNGs
    mat = game.game_material("MAT_A_Baked", tex)                      # glTF-ready material
    body = game.merge(static, "A_Body_LOD0", coll)
    lods = game.lod_copies(obj, [0.5, 0.25], coll)                   # LOD1, LOD2 (collapse)
    cols = game.collision({"receiver": objs}, {"receiver": "hull"}, "godot", "A_Body_LOD0", coll)
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from workbench import stages, tables
from workbench.bl import scene, assets


# ----------------------------------------------------------------------------- copies / pivots
def evaluated_copy(o, name, coll, keep_uv=None):
    """New object `name` with o's evaluated mesh (modifiers applied) and world matrix.
    keep_uv: keep only that UV layer, renamed "UVMap" (game meshes carry one UV set)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    me.name = name + "_Mesh"
    if keep_uv and keep_uv in me.uv_layers:
        for l in [l for l in me.uv_layers if l.name != keep_uv]:
            me.uv_layers.remove(l)
        me.uv_layers[0].name = "UVMap"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = o.matrix_world.copy()
    scene.coll(coll).objects.link(ob)
    for k in ("wb_part", "wb_builder"):
        if k in o:
            ob[k] = o[k]
    return ob


def copies(objs, lod, coll, keep_uv="UV_Bake"):
    """{base_name: copy named <base>_LOD<lod>} for mesh objects."""
    return {stages.base_name(o.name): evaluated_copy(o, f"{stages.base_name(o.name)}_LOD{lod}", coll, keep_uv)
            for o in objs if o.type == "MESH"}


def set_pivots(objs_by_base, pivots):
    """Origins: pivots {base: callable() -> xyz} for moving parts, bbox centre for the rest."""
    for base, ob in objs_by_base.items():
        fn = pivots.get(base)
        if fn:
            scene.set_origin(ob, fn())
        else:
            scene.origin_to_bbox_center(ob)


def merge(objs, name, coll):
    """Join mesh objects into ONE object (world space, materials kept as slots)."""
    return assets.join(objs, name, coll)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def diag(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector(map(max, *bb)) - Vector(map(min, *bb))).length


def lod_copy(ob, ratio, name, coll):
    """Collapse-decimated copy of a game mesh (same origin / world matrix / materials / UVs)."""
    me = ob.data.copy()
    me.name = name + "_Mesh"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    new = bpy.data.objects.new(name, me)
    new.matrix_world = ob.matrix_world.copy()
    scene.coll(coll).objects.link(new)
    if ratio < 0.999:
        assets.decimate(new, max(4, int(tris(ob) * ratio)), weld_rel=0)
    return new


# ----------------------------------------------------------------------------- collision
def collision(groups, modes, engine, render_name, coll, max_faces=250):
    """One convex hull ("hull") or world-axis box ("box") per group of objects {key: [objs]}.
    Names follow tables.ENGINES[engine]["col"](render_name, i). Returns [(key, ob, faces)]."""
    dg = bpy.context.evaluated_depsgraph_get()
    namer = tables.ENGINES[engine]["col"]
    out = []
    i = 0
    for key in sorted(groups):
        mode = modes.get(key, "hull")
        if mode in (None, "none") or not groups[key]:
            continue
        pts = []
        for o in groups[key]:
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            pts += [o.matrix_world @ v.co for v in me.vertices]
            eo.to_mesh_clear()
        bm = bmesh.new()
        if mode == "box":
            mn, mx = Vector(map(min, *pts)), Vector(map(max, *pts))
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=mx - mn, verts=bm.verts)
            bmesh.ops.translate(bm, vec=(mn + mx) / 2, verts=bm.verts)
        else:
            vs = [bm.verts.new(p) for p in pts]
            bmesh.ops.convex_hull(bm, input=vs)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bmesh.ops.triangulate(bm, faces=bm.faces)
        name = namer(render_name, i)
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        me = bpy.data.meshes.new(name + "_Mesh")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        scene.coll(coll).objects.link(ob)
        if len(me.polygons) > max_faces:
            m = ob.modifiers.new("Decimate", "DECIMATE")
            m.ratio = max_faces / len(me.polygons)
            from workbench.bl import mods
            mods.apply_all(ob)
        ob.display_type = "WIRE"
        ob["wb_collision"] = key
        out.append((key, ob, len(ob.data.polygons)))
        i += 1
    return out


# ----------------------------------------------------------------------------- bake
BAKE_MAPS = (("base", "DIFFUSE", False), ("normal", "NORMAL", True), ("ao", "AO", True),
             ("rough", "ROUGHNESS", True), ("metal", "EMIT", True))


def _new_image(name, size, non_color):
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, size, size, alpha=False)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def _principled(mat):
    if mat is None or not mat.use_nodes:
        return None
    return next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _metal_to_emission(mats):
    """Route Metallic into Emission (value or link) so an EMIT bake records metalness. Returns undo."""
    undo = []
    for m in mats:
        b = _principled(m)
        if b is None:
            continue
        ec, es = b.inputs["Emission Color"], b.inputs["Emission Strength"]
        state = (m, tuple(ec.default_value), es.default_value, [l.from_socket for l in ec.links])
        for l in list(ec.links):
            m.node_tree.links.remove(l)
        met = b.inputs["Metallic"]
        if met.is_linked:
            m.node_tree.links.new(met.links[0].from_socket, ec)
        else:
            v = met.default_value
            ec.default_value = (v, v, v, 1.0)
        es.default_value = 1.0
        undo.append(state)
    return undo


def _undo_emission(undo):
    for m, col, strength, links in undo:
        b = _principled(m)
        ec = b.inputs["Emission Color"]
        for l in list(ec.links):
            m.node_tree.links.remove(l)
        for s in links:
            m.node_tree.links.new(s, ec)
        ec.default_value = col
        b.inputs["Emission Strength"].default_value = strength


def bake(high, low_objs, folder, size=2048, prefix="T", extrusion=None, margin=8, ao_samples=32,
         ao_distance=None):
    """Cycles selected-to-active bake of the DETAIL meshes onto the game meshes' atlas ("UVMap").
    Writes <prefix>_base.png (sRGB), _normal.png (tangent, OpenGL +Y), _orm.png (R=AO, G=rough,
    B=metal) into folder and returns {map: path}. The game meshes are not modified."""
    from workbench.bl.presentation import use_gpu
    sc = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    sc.render.engine = "CYCLES"
    device = use_gpu()
    if sc.world is None:
        sc.world = bpy.data.worlds.new("WORLD_Bake")
    size_m = max(diag(o) for o in low_objs)
    sc.world.light_settings.distance = ao_distance or max(0.02, 0.08 * size_m)
    extrusion = extrusion if extrusion is not None else max(0.002, 0.006 * size_m)
    target = assets.join(low_objs, prefix + "_BAKE_TARGET", low_objs[0].users_collection[0].name)   # visible + renderable
    target.hide_render = False
    target.data.materials.clear()
    tmat = bpy.data.materials.new(prefix + "_BAKE_MAT")
    tmat.use_nodes = True
    target.data.materials.append(tmat)
    for p in target.data.polygons:
        p.material_index = 0
    node = tmat.node_tree.nodes.new("ShaderNodeTexImage")
    tmat.node_tree.nodes.active = node
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    hi = [o for o in high if o.type == "MESH"]
    for o in hi:
        o.hide_set(False)
        o.hide_render = False
        o.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    mats = {m for o in hi for m in o.data.materials if m}
    imgs, times = {}, {}
    import time
    for key, btype, non_color in BAKE_MAPS:
        t0 = time.time()
        img = _new_image(f"{prefix}_{key}", size, non_color)
        node.image = img
        # samples also anti-alias the bake (jittered sub-pixel rays): 1 sample left stair-stepped
        # bevel highlights and ribs in the normal map (AK review renders)
        sc.cycles.samples = ao_samples if btype == "AO" else (8 if btype == "NORMAL" else 4)
        kw = dict(type=btype, use_selected_to_active=True, cage_extrusion=extrusion, margin=margin,
                  use_clear=True, target="IMAGE_TEXTURES")
        if btype == "DIFFUSE":
            kw["pass_filter"] = {"COLOR"}
        if btype == "NORMAL":
            kw["normal_space"] = "TANGENT"
        undo = _metal_to_emission(mats) if btype == "EMIT" else []
        try:
            bpy.ops.object.bake(**kw)
        finally:
            _undo_emission(undo)
        imgs[key] = img
        times[key] = round(time.time() - t0, 1)
    out = {}
    for key in ("base", "normal"):
        p = os.path.join(folder, f"{prefix}_{key}.png")
        imgs[key].filepath_raw = p
        imgs[key].file_format = "PNG"
        imgs[key].save()
        out[key] = p
    px = {k: _pixels(imgs[k]) for k in ("ao", "rough", "metal")}
    orm = np.ones_like(px["ao"])
    orm[..., 0], orm[..., 1], orm[..., 2] = px["ao"][..., 0], px["rough"][..., 0], px["metal"][..., 0]
    oimg = _new_image(f"{prefix}_orm", size, True)
    oimg.pixels.foreach_set(orm.ravel())
    p = os.path.join(folder, f"{prefix}_orm.png")
    oimg.filepath_raw = p
    oimg.file_format = "PNG"
    oimg.save()
    out["orm"] = p
    for k in ("ao", "rough", "metal"):
        bpy.data.images.remove(imgs[k])
    bpy.data.objects.remove(target, do_unlink=True)
    bpy.data.materials.remove(tmat)
    out["stats"] = dict(size=size, device=device, seconds_per_map=times, extrusion_m=round(extrusion, 4), ao_distance_m=round(sc.world.light_settings.distance, 4),
                        base_mean=[round(float(x), 3) for x in _pixels(imgs["base"])[..., :3].reshape(-1, 3).mean(0)],
                        normal_mean=[round(float(x), 3) for x in _pixels(imgs["normal"])[..., :3].reshape(-1, 3).mean(0)])
    return out


def _pixels(img):
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


# ----------------------------------------------------------------------------- material
def _gltf_output_group():
    """Node group the glTF exporter reads the occlusion texture from ("glTF Material Output")."""
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def game_material(name, tex):
    """Principled material from baked maps: base colour, ORM (glTF metallicRoughness + occlusion),
    tangent normal map. Exports to glTF as a standard PBR material."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])

    def img_node(path, non_color, y):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        n.location = (-700, y)
        return n
    base = img_node(tex["base"], False, 300)
    nt.links.new(base.outputs["Color"], b.inputs["Base Color"])
    orm = img_node(tex["orm"], True, 0)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = _gltf_output_group()
    nt.links.new(sep.outputs["Red"], grp.inputs["Occlusion"])
    nrm = img_node(tex["normal"], True, -300)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.space = "TANGENT"
    nm.uv_map = "UVMap"
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    mean = tex.get("stats", {}).get("base_mean", (0.5, 0.5, 0.5))
    m.diffuse_color = (*[float(c) ** 2.2 for c in mean], 1.0)      # Workbench preview colour (linear)
    return m


def assign_single(objs, mat):
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)
        for p in o.data.polygons:
            p.material_index = 0
