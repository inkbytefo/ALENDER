"""
STAGE 5 - CLEAN WORKSPACE         python wb.py build VEH_TT92_Racing_Car --stage 5

Opens the pipeline file VEH_TT92_Racing_Car.blend (never modified) and writes
    output/VEH_TT92_Racing_Car/blend/VEH_TT92_Racing_Car_WORKSPACE.blend
- the file to open in the Blender GUI and work in:
    * only the final HIGH model (blockout, cutters, guides removed), geometry untouched
    * collections by function: Body, Front, Cockpit, Engine, Exhaust, Suspension, Wheels,
      Fasteners (+ Reference with the top photo, Studio with lights and cameras)
    * everything parented to the VEH_TT92_Racing_Car root; wheels pivot on their axles
    * bevel / weighted-normal modifiers left LIVE so parts stay editable
    * reference photo packed, orphan data purged, README text block inside the file
Hand edits made in this file are NOT picked up by the build: change landmarks.py / parts.py for
anything that must survive a rebuild.
"""
import bpy

import stagelib as SL
from stagelib import L, A
from workbench import paths
from workbench.bl import scene

SRC = paths.out(A, "blend", A + ".blend")
DST = paths.out(A, "blend", A + "_WORKSPACE.blend")

# collection <- object name prefixes (first match wins)
GROUPS = [
    ("Wheels", ("WHEEL_", "BRAKE_")),
    ("Suspension", ("SUSP_", "UNCERTAIN_SUSP_")),
    ("Exhaust", ("EXHAUST_",)),
    ("Engine", ("ENG_", "ENGINE_")),
    ("Cockpit", ("COCKPIT_",)),
    ("Fasteners", ("FASTENER_",)),
    ("Front", ("NOSE_", "AERO_", "BODY_Eye", "BODY_Mirror", "BODY_Stripes")),
    ("Body", ("BODY_",)),
]
COLOR_TAGS = {"Body": "COLOR_01", "Front": "COLOR_02", "Cockpit": "COLOR_03", "Engine": "COLOR_04",
              "Exhaust": "COLOR_02", "Suspension": "COLOR_05", "Wheels": "COLOR_06", "Fasteners": "COLOR_08"}

README = f"""{A} - WORKSPACE
====================================
Final design: front-engined single seater, old-JDM wedge nose, blown V8 in an open bay,
twin wrapped exhausts feeding one jet-style afterburner on the round tail. Units: metres. +X = car left, -Y = front, +Z up.
Origin = centre line, midway between the axles, on the ground.

Outliner
  {A}                 everything is parented to the root empty of the same name
    Body               shell, louvres, filler caps, panel lines, bay lip
    Front              nose mouth (ring, slats, emblem), eyes + lamps, mirrors, chin spoiler, stripes
    Cockpit            steering wheel, seat, dash, rim lip, cowl pad
    Engine             ENG_* blown V8 (+ air filter)
    Exhaust            EXHAUST_*_L / _R headers, pipe, heat wrap; EXHAUST_AB_* tail afterburner
    Suspension         SUSP_Front_* / SUSP_Rear_*
    Wheels             WHEEL_<Front|Rear>_<part>_<L|R>, BRAKE_Drum_*  (origins on the axles: rotate on X)
    Fasteners          FASTENER_* rivets / bolts (instanced meshes)
  Reference            top photo + ortho reference camera (hidden; numpad 0 with CAM_REFERENCE)
  Studio               3 area lights, perspective + ortho review cameras

Materials (8): MAT_BODY_RED, MAT_STRIPE (stripes + heat wrap), MAT_CHROME, MAT_METAL_DARK,
MAT_EXHAUST, MAT_GLOW (emissive afterburner liner), MAT_RUBBER, MAT_LEATHER.  BODY_Shell uses two slots: red skin + dark cut interiors.

Modifiers: Bevel + WeightedNormal are live on the hard-surface parts. BODY_Shell is baked
(subsurf + booleans applied).

This file is generated. To change the car permanently edit the project and rebuild:
  projects/{A}/landmarks.py   numbers (sizes, positions)
  projects/{A}/parts.py       geometry recipes
  python wb.py build {A}            all stages
  python wb.py build {A} --stage 5  only this workspace file
"""

scene.open_blend(SRC)
sc = bpy.context.scene

# ---------------------------------------------------------------- drop everything that is not the final model
for cname in scene.LOW_COLLS + ("01_GUIDES", "08_TEMP"):
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
    elif ob.type == "MESH":
        for name, prefixes in GROUPS:
            if ob.name.startswith(prefixes):
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
sc.name = "TT92"
sc.camera = bpy.data.objects.get("CAM_PERSPECTIVE")
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.film_transparent = False
sc.frame_set(1)
for img in bpy.data.images:                                  # self-contained file
    if img.filepath and not img.packed_file and img.source == "FILE":
        img.pack()
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
print("[STAGE5] workspace:", len(meshes), "meshes,", tris, "tris,", len(bpy.data.materials), "materials")
for name, c in groups.items():
    print(f"[STAGE5]   {name:<11}{len(c.objects):>4} objects")
print("[STAGE5] collections:", sorted(c.name for c in bpy.data.collections))
scene.save(DST)
print("[STAGE5] PASS")
