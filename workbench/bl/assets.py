"""
Third-party model import + analysis (FBX / glTF / GLB / OBJ / USD / .blend).

    objs = assets.import_model(path, collection="08_TEMP")        # returns the new objects
    rep = assets.inspect(objs)                                     # dims, tris, materials, parts
    assets.print_report(rep)
    part = assets.join(objs_subset, "SUSP_Front_DW_L")             # merge a sub-assembly
    assets.normalise(objs, up="Z", forward="-Y", scale=0.01)       # bring to workbench axes/units

    assets.decimate(ob, 6000, cad=True)                            # game budget (CAD exports: cad=True)

Rules (docs/11_ASSETS_AND_PBR.md):
  * imported geometry is never the source of truth for proportions - landmarks are. Imported parts
    are fitted to landmark hardpoints (fit_to / place_between) and named with the project's scheme.
  * transforms are applied (scale 1, rotation 0) before the part joins a build, so validation and
    GLB export behave like procedural parts.
  * record origin + licence of every imported file in the project's project.md.
"""
import os
import bpy
from mathutils import Vector, Matrix

from workbench.bl.scene import coll

IMPORTERS = {
    ".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
    ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
    ".usd": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".usdc": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".usdz": lambda p: bpy.ops.wm.usd_import(filepath=p),
    ".stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
}


def _append_blend(path, name_filter=None):
    """append every object (or those whose name contains name_filter) from a .blend."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if not name_filter or name_filter in n]
    out = []
    for ob in dst.objects:
        if ob is not None:
            bpy.context.scene.collection.objects.link(ob)
            out.append(ob)
    return out


def import_model(path, collection="08_TEMP", prefix="", name_filter=None):
    """Import a model file; move the new objects into `collection`; optional name prefix.
    Returns the list of new objects (meshes, empties, armatures...)."""
    path = os.path.abspath(path)
    ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext == ".blend":
        _append_blend(path, name_filter)
    elif ext in IMPORTERS:
        IMPORTERS[ext](path)
    else:
        raise ValueError(f"unsupported model format: {ext}")
    new = [o for o in bpy.data.objects if o not in before]
    c = coll(collection)
    for o in new:
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        c.objects.link(o)
        if prefix and not o.name.startswith(prefix):
            o.name = prefix + o.name
    bpy.context.view_layer.update()
    return new


def world_bbox(objs):
    mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def inspect(objs):
    """per-object and overall summary (world bbox, tris, materials, hierarchy)."""
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for o in objs:
        r = dict(name=o.name, type=o.type, parent=o.parent.name if o.parent else None,
                 scale=tuple(round(s, 4) for s in o.scale))
        if o.type == "MESH":
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            r["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
            r["verts"] = len(me.vertices)
            eo.to_mesh_clear()
            mn, mx = world_bbox([o])
            r["center"] = tuple(round(v, 4) for v in (mn + mx) / 2)
            r["size"] = tuple(round(v, 4) for v in mx - mn)
            r["materials"] = [m.name for m in o.data.materials if m]
        rows.append(r)
    mn, mx = world_bbox(objs)
    mats = sorted({m for r in rows for m in r.get("materials", [])})
    return dict(objects=rows, count=len(objs), meshes=sum(1 for r in rows if r["type"] == "MESH"),
                tris=sum(r.get("tris", 0) for r in rows), bbox_min=tuple(mn), bbox_max=tuple(mx),
                size=tuple(mx - mn), materials=mats)


def print_report(rep, limit=200):
    print(f"[ASSET] {rep['count']} objects, {rep['meshes']} meshes, {rep['tris']} tris, "
          f"size {tuple(round(v, 3) for v in rep['size'])}, materials {rep['materials']}")
    for r in sorted(rep["objects"], key=lambda r: r["name"])[:limit]:
        if r["type"] == "MESH":
            print(f"   {r['name']:44} tris {r['tris']:7}  c {r['center']}  s {r['size']}  {r['materials']}")
        else:
            print(f"   {r['name']:44} {r['type']}  parent {r['parent']}")


def apply_transforms(objs):
    """bake object transforms into mesh data (scale 1, rotation 0, location 0); clears parents."""
    # capture ALL world matrices first: un-parenting a parent changes its children's world matrix
    mws = {o.name: o.matrix_world.copy() for o in objs}
    for o in objs:
        o.parent = None
    for o in objs:
        if o.type != "MESH":
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(mws[o.name])
        o.matrix_world = Matrix.Identity(4)
        o.data.update()
    bpy.context.view_layer.update()          # refresh bound_box (stale until the depsgraph runs)
    return objs


def normalise(objs, scale=1.0, rotate=None):
    """uniform scale and optional rotation (Matrix 3x3/4x4) about the world origin, baked."""
    apply_transforms(objs)
    m = Matrix.Scale(scale, 4)
    if rotate is not None:
        m = rotate.to_4x4() @ m
    for o in objs:
        if o.type == "MESH":
            o.data.transform(m)
            o.data.update()
    bpy.context.view_layer.update()
    return objs


def transform(objs, mat):
    """bake an arbitrary 4x4 world transform into the meshes."""
    for o in objs:
        if o.type == "MESH":
            o.data.transform(mat)
            o.data.update()
    bpy.context.view_layer.update()
    return objs


def fit_to(objs, target_min, target_max, axes="XYZ", uniform=True):
    """scale+move objs so their world bbox matches the target box on the given axes
    (uniform=True keeps proportions, using the mean ratio of the requested axes)."""
    apply_transforms(objs)
    mn, mx = world_bbox(objs)
    tmn, tmx = Vector(target_min), Vector(target_max)
    idx = ["XYZ".index(a) for a in axes]
    ratios = [(tmx[i] - tmn[i]) / max(1e-9, mx[i] - mn[i]) for i in idx]
    s = [1.0, 1.0, 1.0]
    for i, r in zip(idx, ratios):
        s[i] = sum(ratios) / len(ratios) if uniform else r
    if uniform:
        s = [s[idx[0]]] * 3
    c0 = (mn + mx) / 2
    c1 = (tmn + tmx) / 2
    for i in range(3):
        if i not in idx:
            c1[i] = c0[i]
    m = Matrix.Translation(c1) @ Matrix.Diagonal((*s, 1.0)) @ Matrix.Translation(-c0)
    return transform(objs, m)


def join(objs, name, collection=None, material=None):
    """merge mesh objects into ONE object named `name` (context-free, via bmesh)."""
    import bmesh
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        return None
    bm = bmesh.new()
    mats = []
    for o in meshes:
        tmp = o.data.copy()
        tmp.transform(o.matrix_world)
        remap = {}
        for i, m in enumerate(tmp.materials):
            if m is not None and m not in mats:
                mats.append(m)
            remap[i] = mats.index(m) if m is not None else 0
        off = len(bm.faces)
        bm.from_mesh(tmp)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[off:]:
            f.material_index = remap.get(f.material_index, 0)
        bpy.data.meshes.remove(tmp)
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    for m in ([bpy.data.materials[material]] if material else mats):
        me.materials.append(m)
    if material:
        for p in me.polygons:
            p.material_index = 0
    ob = bpy.data.objects.new(name, me)
    coll(collection or meshes[0].users_collection[0].name).objects.link(ob)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    return ob


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def merge_by_distance(ob, rel=2e-5):
    """weld split vertices (CAD / FBX exports store one vertex per face corner). rel = fraction of
    the bbox diagonal. Without this, collapse decimation stalls and throws long spikes."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mn, mx = world_bbox([ob])
    d = max(1e-6, (mx - mn).length * rel)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=d)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return len(ob.data.vertices)


def decimate(ob, target_tris, planar_first=False, weld_rel=2e-5, cad=False):
    """reduce a mesh to about target_tris (weld -> [cad clean] -> [planar] -> collapse, baked).
    Collapse runs in up to 3 passes (a single extreme ratio produces spikes / stalls).
    cad=True for CAD/engineering exports: weld 2e-3 of the bbox diagonal + dissolve degenerate
    faces first (measured: 75k -> 14k before collapse; docs/11)."""
    import bmesh
    from workbench.bl import mods
    if cad:
        weld_rel = max(weld_rel, 2e-3)
    if weld_rel:
        merge_by_distance(ob, weld_rel)
    if cad:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
        bm.to_mesh(ob.data)
        bm.free()
    t = tris(ob)
    if t <= target_tris:
        return t
    if planar_first:
        m = ob.modifiers.new("DecimatePlanar", "DECIMATE")
        m.decimate_type = "DISSOLVE"
        m.angle_limit = 0.0175          # 1 deg
        mods.apply_all(ob)
        t = tris(ob)
    for _ in range(3):
        if t <= target_tris * 1.1:
            break
        ratio = max(0.08, target_tris / t)            # at most ~12x per pass
        m = ob.modifiers.new("Decimate", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = ratio
        m.use_collapse_triangulate = True
        mods.apply_all(ob)
        t = tris(ob)
    return t


def split(ob, name, keep, collection=None):
    """copy of ob containing only the faces for which keep(poly, world_center) is True."""
    import bmesh
    me = ob.data.copy()
    me.transform(ob.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    drop = [f for f in bm.faces if not keep(f, f.calc_center_median())]
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    nm = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(nm)
    bm.free()
    for m in ob.data.materials:
        nm.materials.append(m)
    o = bpy.data.objects.new(name, nm)
    coll(collection or ob.users_collection[0].name).objects.link(o)
    return o


def delete(objs):
    for o in list(objs):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and getattr(data, "users", 1) == 0 and isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
