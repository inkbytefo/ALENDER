"""
STAGE 2 - HIGH / GAME-READY for PROP_AK_Rifle      python wb.py run projects/PROP_AK_Rifle/stage2.py
Opens _02_COMPLETE_LOW, hides (keeps) LOW, rebuilds HIGH from the same landmarks, unwraps one shared
UV atlas, sets animation pivots, validates, renders, exports GLB (parts) + GLB (game: static merged)
and writes report.json.
"""
import os, sys, json, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import bmesh
from mathutils import Vector

from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, export

scene.open_blend(paths.milestone("PROP_AK_Rifle", "02_COMPLETE_LOW"))
import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)
A = L.ASSET
WORK = paths.out(A, "work", "stage2")
H = PT.HIGH
UV_M = 2.0                      # metres per UV unit in UVMap (workbench convention, tiling PBR)
MOVING = ("MAG_Body", "MAG_Floorplate", "MAG_Ribs", "MAG_LipPlates", "MAG_LugFront", "MAG_LugRear", "CTRL_Trigger_Blade", "CTRL_Safety_Lever",
          "CTRL_Safety_Pivot", "CTRL_MagCatch", "CTRL_Charging_Handle", "CTRL_Charging_Carrier")


def unwrap(objs):
    """One shared smart-project atlas for all parts (consistent texel density) -> UV_Bake (0-1),
    and UVMap = the same islands scaled to UV_M metres per unit (tiling textures)."""
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.004, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    a3 = auv = 0.0
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data)
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            a3 += f.calc_area()
            us = [l[uv].uv for l in f.loops]
            auv += abs(sum(us[i].x * us[(i + 1) % len(us)].y - us[(i + 1) % len(us)].x * us[i].y
                           for i in range(len(us)))) / 2
        bm.free()
    k = math.sqrt(a3 / auv) / UV_M
    for o in objs:
        me = o.data
        bake = me.uv_layers.get("UV_Bake") or me.uv_layers.new(name="UV_Bake")
        main = me.uv_layers[0]
        for i, d in enumerate(main.data):
            bake.data[i].uv = d.uv.copy()
            d.uv = d.uv * k
        me.uv_layers.active_index = 0
    return dict(area3d_m2=round(a3, 4), atlas_coverage=round(auv, 3),
                texel_px_per_m_at_4k=round(4096 * math.sqrt(auv / a3), 1))


def merged_game_mesh(objs, name, root):
    """Static parts joined into ONE evaluated mesh (modifiers applied), materials kept as slots."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for o in objs:
        eo = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(eo, depsgraph=dg)
        me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = remap[f.material_index] if remap else 0
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    scene.coll("08_TEMP").objects.link(ob)
    ob.parent = root
    return ob


# ---------------------------------------------------------------------------- build
for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
    scene.set_collection_visible(c, False)
materials.ensure(PT.PALETTE)
PT.receiver(H); PT.barrel(H); PT.woodwork(H); PT.buttstock(H); PT.grip(H); PT.magazine(H)
scene.save(paths.milestone(A, "03_HIGH_PRIMARY"))
PT.controls(H)
scene.save(paths.milestone(A, "04_HIGH_MECHANICAL"))
PT.details(H)

high = [o for o in scene.objects_in(scene.HIGH_COLLS) if o.type == "MESH"]
uvinfo = unwrap(high)
print("[STAGE2] uv", uvinfo)

root = scene.root(A)
for ob in high:
    piv = PT.PIVOTS.get(ob.name)
    scene.set_origin(ob, piv() if piv else sum((ob.matrix_world @ Vector(c) for c in ob.bound_box), Vector()) / 8)
    ob.parent = root
# carrier and floorplate/ribs ride with their drivers
for child, par in (("CTRL_Charging_Carrier", "CTRL_Charging_Handle"), ("MAG_Floorplate", "MAG_Body"),
                   ("MAG_Ribs", "MAG_Body"), ("MAG_LipPlates", "MAG_Body"), ("MAG_LugFront", "MAG_Body"), ("MAG_LugRear", "MAG_Body"), ("CTRL_Safety_Pivot", "CTRL_Safety_Lever")):
    scene.parent_keep([bpy.data.objects[child]], bpy.data.objects[par])
scene.save(paths.milestone(A, "05_FINAL_GEOMETRY"))

# ---------------------------------------------------------------------------- review renders
cams = cameras.rig_from_bounds(high)
ref_cam = bpy.data.objects.get("CAM_REFERENCE")
render.workbench(ref_cam, os.path.join(WORK, "high_ref_clay.png"), "CLAY", transparent=True, res=L.IMAGE_SIZE)
render.workbench(ref_cam, os.path.join(WORK, "high_ref_mat.png"), "MATERIAL", transparent=True, res=L.IMAGE_SIZE)
render.review_set(cams, paths.out(A, "renders"), "final")

# ---------------------------------------------------------------------------- validation
st = validate.stats(high)
chk = validate.Checks()
d = st["dims"]
chk.add("U01", "BLOCKER", abs(d[1] - 0.880) / 0.880 < 0.02, "length %.4f m (target 0.880)" % d[1])
chk.add("U02", "BLOCKER", not st["bad_scale"], st["bad_scale"] or "all scales 1.0")
chk.add("U06", "BLOCKER", not st["no_uv"], st["no_uv"] or "all meshes have UVs (UVMap + UV_Bake)")
chk.add("U07", "BLOCKER", not st["empty_slots"], st["empty_slots"] or "no empty material slots")
chk.add("U08", "BLOCKER", st["tris"] <= 60000, f"{st['tris']} tris (max 60000)")
chk.add("U09", "WARN", 12000 <= st["tris"] <= 45000, f"{st['tris']} tris (target 12000-45000)")
chk.add("U10", "BLOCKER", len(st["materials_used"]) <= 4, f"{len(st['materials_used'])} materials")
hits = validate.intersections(PT.CRITICAL_PAIRS, high)
chk.add("X01", "BLOCKER", not hits, hits or "0 critical intersections")
chk.add("P01", "BLOCKER", all(bpy.data.objects[n].parent for n in MOVING), "moving parts parented, pivots set")
scene.save(paths.out(A, "blend", A + ".blend"))

# ---------------------------------------------------------------------------- export
glb = paths.out(A, "glb", A + ".glb")
export.glb([root] + high, glb)
static = [o for o in high if o.name not in MOVING]
body = merged_game_mesh(static, A + "_Body", root)
movers = [bpy.data.objects[n] for n in MOVING]
glb_game = paths.out(A, "glb", A + "_game.glb")
game_tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
export.glb([root, body] + movers, glb_game)
print("[STAGE2] game body tris", game_tris)
nmat = len({m for o in high for m in o.data.materials if m})
metrics = {"tris_high": st["tris"], "dims": st["dims"], "objects": st["objects"], "uv": uvinfo,
           "top_tris": st["top_tris"][:10], "game_glb": {"body_tris": game_tris, "moving_parts": list(MOVING)}}
ok, detail = export.roundtrip(glb, len(high) + 1, nmat)
chk.add("U15", "BLOCKER", ok, detail)
validate.write_report(os.path.join(HERE, "report.json"), A, chk, metrics=metrics,
                      licence="own procedural build; downloaded AK47.blend studied only, nothing reused")
