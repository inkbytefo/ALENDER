"""
WORKSPACE file of VEH_Gemini_Motorcycle    python wb.py run projects/VEH_Gemini_Motorcycle/finish_workspace.py

Run after finish_paint.py. Opens the painted hero file (not modified) and writes
    output/VEH_Gemini_Motorcycle/blend/VEH_Gemini_Motorcycle_WORKSPACE.blend
- the clean file to open in the Blender GUI: only the final S3 DETAIL model, collections by function,
the pivot hierarchy of the build (wheel parts ride with the tyres), live bevel / weighted-normal
modifiers, master material MM_Gemini_Master + its instances, textures by relative path, README inside.
Hand edits in that file are not picked up by the build: change landmarks.py / parts.py / paint.py.
"""
import os
import sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from workbench import paths
from workbench.bl import scene

A = "VEH_Gemini_Motorcycle"
SRC = paths.out(A, "blend", A + ".blend")
DST = paths.out(A, "blend", A + "_WORKSPACE.blend")

GROUPS = [
    ("Wheels", ("WHEEL_", "BRAKE_")),
    ("Suspension", ("SUSP_",)),
    ("Exhaust", ("EXHAUST_",)),
    ("Engine", ("ENGINE_", "INTAKE_")),
    ("Drive", ("DRIVE_",)),
    ("Frame", ("FRAME_",)),
    ("Controls", ("CTRL_",)),
    ("Fasteners", ("FASTENER_",)),
    ("Body", ("BODY_",)),
]
COLOR_TAGS = {"Body": "COLOR_01", "Frame": "COLOR_05", "Controls": "COLOR_03", "Engine": "COLOR_04",
              "Exhaust": "COLOR_02", "Suspension": "COLOR_05", "Wheels": "COLOR_06", "Drive": "COLOR_07",
              "Fasteners": "COLOR_08"}

README = f"""{A} - WORKSPACE
====================================
Custom inline-4 street bike reconstructed from one side photo (bike's right side = -X).
Units: metres. +X = bike left, -Y = front, +Z up. Origin on the ground under the bike.

Outliner
  {A}            everything hangs under the root empty of the same name
    Body, Frame, Engine (+ intake), Exhaust, Suspension, Wheels (+ brakes), Drive, Controls, Fasteners
    object names end in _HP (stage 3 detail meshes)
  Reference        side photo + reference camera (hidden)
  Studio           lights and review cameras

Materials: ONE master node group MM_Gemini_Master + instances MAT_* (texture set + a few numbers each);
MAT_GLASS (headlight lens, reservoirs) is a plain transparent material.
Tune a surface: select the object > Shader Editor > the MASTER node's inputs.
Tri-planar projection (MF_Gemini_Projection, Tile = metres per repeat): no UV unwrap needed.
Textures: projects/VEH_TT92_Racing_Car/material and downloaded_resources/materials (relative paths).

This file is generated. To change the bike permanently:
  projects/{A}/landmarks.py, parts.py     geometry   -> python wb.py build {A}
  projects/{A}/paint.py                   materials  -> python wb.py run projects/{A}/finish_paint.py
  then python wb.py run projects/{A}/finish_workspace.py
"""

scene.open_blend(SRC)
sc = bpy.context.scene

# ---------------------------------------------------------------- drop everything that is not the final model
for cname in ("10_S1_PRIMITIVE", "20_S2_LOWPOLY", "40_S4_GAME", "41_S4_COLLISION", "01_GUIDES", "08_TEMP"):
    c = bpy.data.collections.get(cname)
    if c:
        for ob in list(c.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)

# ---------------------------------------------------------------- new collection tree
def new_coll(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


def move(ob, target):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    target.objects.link(ob)


car = new_coll(A, sc.collection)
groups = {name: new_coll(name, car) for name, _ in GROUPS}
for name, tag in COLOR_TAGS.items():
    groups[name].color_tag = tag
reference = new_coll("Reference", sc.collection)
studio = new_coll("Studio", sc.collection)

unsorted = []
for ob in list(bpy.data.objects):
    if ob.name == A:                                         # root empty
        move(ob, car)
    elif ob.type == "EMPTY":                                 # leftover guide empties
        bpy.data.objects.remove(ob, do_unlink=True)
    elif ob.type == "MESH":
        for name, prefixes in GROUPS:
            if ob.name.replace("UNCERTAIN_", "").startswith(prefixes):
                move(ob, groups[name])
                break
        else:
            unsorted.append(ob.name)
            move(ob, car)
    elif ob.name in ("REF_PHOTO", "CAM_REFERENCE"):
        move(ob, reference)
    else:                                                    # lights, review cameras
        move(ob, studio)
assert not unsorted, f"objects without a group: {unsorted}"

for c in list(bpy.data.collections):                         # the old numbered pipeline collections
    if c not in [car, reference, studio] + list(groups.values()):
        bpy.data.collections.remove(c)

# ---------------------------------------------------------------- scene state
root = bpy.data.objects[A]
for ob in bpy.data.objects:
    ob.hide_viewport = False
    ob.hide_set(False)
    ob.select_set(False)
    if ob.type == "MESH":
        ob.hide_render = False
        ob.display_type = "TEXTURED"
bpy.context.view_layer.objects.active = root
layer = bpy.context.view_layer.layer_collection
layer.children["Reference"].hide_viewport = True             # photo out of the way, one click to show
reference.hide_render = True
sc.name = "Gemini"
sc.camera = bpy.data.objects.get("CAM_PERSPECTIVE")
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.film_transparent = False
sc.frame_set(1)
ref = bpy.data.images.get("REAL_REFERENCE.png")              # small: pack it; the PBR sets stay on disk
if ref and not ref.packed_file:
    ref.pack()
txt = bpy.data.texts.get("README") or bpy.data.texts.new("README")
txt.clear()
txt.write(README)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# ---------------------------------------------------------------- summary + save
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
dg = bpy.context.evaluated_depsgraph_get()
tris = 0
for ob in meshes:
    me = ob.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    ob.evaluated_get(dg).to_mesh_clear()
print("[WORKSPACE] workspace:", len(meshes), "meshes,", tris, "tris,", len(bpy.data.materials), "materials")
for name, c in groups.items():
    print(f"[WORKSPACE]   {name:<11}{len(c.objects):>4} objects")
print("[WORKSPACE] collections:", sorted(c.name for c in bpy.data.collections))
scene.save(DST)
bpy.ops.file.make_paths_relative()                           # textures: //..\..\..\projects\...\material
scene.save(DST)
print("[WORKSPACE] PASS")
