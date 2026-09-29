"""
STAGE 2 - HIGH POLY / REFINED MODEL  (VEH_Gemini_Motorcycle)
    python wb.py run projects/VEH_Gemini_Motorcycle/stage2.py      (after stage1.py)
Opens <ASSET>_02_COMPLETE_LOW, keeps LOW collections (hidden), rebuilds every part at HIGH LOD
from the same landmarks, adds details, validates, renders, exports GLB, writes report.json.
"""
import os, sys, json, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Matrix

from workbench import paths
from workbench.bl import scene, materials, render, validate, export, mesh
from workbench.bl.fasteners import Fasteners

scene.open_blend(paths.milestone("VEH_Gemini_Motorcycle", "02_COMPLETE_LOW"))
import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)

A = L.ASSET
H = PT.HIGH
WORK = paths.out(A, "work", "stage2")
RENDERS = paths.out(A, "renders")
cams = {n: bpy.data.objects[n] for n in ("ORTHO_RIGHT", "ORTHO_LEFT", "ORTHO_FRONT", "ORTHO_REAR",
                                          "ORTHO_TOP", "CAM_PERSPECTIVE", "CAM_PERSPECTIVE_L")}
ref_cam = bpy.data.objects["CAM_REFERENCE"]


def high():
    return scene.objects_in(scene.HIGH_COLLS)


def review(tag, ortho=True):
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_clay.png"), "CLAY", transparent=True)
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_mat.png"), "MATERIAL", transparent=True)
    if ortho:
        render.review_set(cams, WORK, tag)


# ------------------------------------------------------------------ preserve LOW (hidden, kept)
for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
    scene.set_collection_visible(c, False)
materials.ensure(PT.PALETTE)

# ------------------------------------------------------------------ phase 1-4: primary forms
PT.wheels(H); PT.tank(H); PT.seat(H); PT.frame(H)
scene.save(paths.milestone(A, "03_HIGH_PRIMARY"))
review("h1", ortho=False)

# ------------------------------------------------------------------ phase 5-9: mechanical
PT.brakes(H); PT.engine(H); PT.front(H); PT.rear(H); PT.exhaust(H)
scene.save(paths.milestone(A, "04_HIGH_MECHANICAL"))
review("h2", ortho=False)

# ------------------------------------------------------------------ phase 10: details (instanced)
D = "07_DETAILS"
fs = Fasteners(D)
for sg in (-1, 1):                          # engine side covers (right seen; left mirrored)
    c = Vector(L.P3(*L.ALT_COVER_PX)); r = L.ALT_COVER_R / L.S
    for i in range(10):
        a = 2 * math.pi * i / 10 + 0.2
        fs.place("BOLT_M6", c + Vector((sg * 0.23, math.cos(a) * r * 0.78, math.sin(a) * r * 0.78)), (sg, 0, 0))
    c = Vector(L.P3(*L.SMALL_COVER_PX)); r = L.SMALL_COVER_R / L.S
    for i in range(6):
        a = 2 * math.pi * i / 6
        fs.place("BOLT_M6", c + Vector((sg * 0.222, math.cos(a) * r * 0.72, math.sin(a) * r * 0.72)), (sg, 0, 0))
for sg in (-1, 1):                          # axle nuts, pivot washers
    fs.place("NUT", Vector(L.FRONT_AXLE) + Vector((sg * 0.13, 0, 0)), (sg, 0, 0))
    fs.place("NUT", Vector(L.REAR_AXLE) + Vector((sg * 0.17, 0, 0)), (sg, 0, 0))
    fs.place("WASHER", Vector(L.P3(*L.SWINGARM_PIVOT_PX)) + Vector((sg * 0.175, 0, 0)), (sg, 0, 0))
fork, st = PT.steering()
for sg in (-1, 1):                          # radial caliper bolts
    cp = Vector(L.P3(803, 468))
    for dz in (-0.035, 0.035):
        d = Matrix.Rotation(math.radians(35), 3, "X") @ Vector((0, 0, dz))
        fs.place("BOLT_M10", cp + d + Vector((sg * 0.108, 0, 0)), (sg, 0, 0))
    for off in (fork["len"] - 0.005, fork["len"] - 0.175):   # triple-clamp pinch bolts
        p = fork["axle"] + fork["up"] * off + Vector((sg * (L.FORK_SPACING + 0.04), 0, 0)) + fork["back"] * 0.03
        fs.place("BOLT_M8", p, (sg, 0, 0))
for s, sg in (("L", 1), ("R", -1)):         # chain adjusters
    y, z = L.P(266, 475)
    mesh.box(f"FRAME_Swingarm_ChainAdjuster_{s}", D, (sg * 0.143, y, z), (0.008, 0.03, 0.026), "MAT_METAL_RAW")
up = fork["up"]                              # front brake line, visible on the right side
mc = Vector(L.P3(L.RESERVOIR_R_PX[0], L.RESERVOIR_R_PX[1] + 30, -0.19))
cal = Vector(L.P3(803, 440, -0.095))
mesh.tube("CTRL_BrakeLine_Front_R", D, [mc, mc + Vector((0.05, 0.05, -0.06)),
                                         fork["axle"] + up * 0.45 + Vector((-0.14, -0.02, 0)),
                                         fork["axle"] + up * 0.2 + Vector((-0.13, -0.035, 0)), cal],
          0.0045, 8, "MAT_RUBBER", samples=8)
bpy.context.view_layer.update()

# ------------------------------------------------------------------ origins + hierarchy
root = scene.root(A)
shared = {m.data.name for m in high() if m.name.startswith("FASTENER_") and m.data.users > 1}
for ob in high():
    if ob.type != "MESH" or ob.data.name in shared:
        continue
    if ob.name.startswith(("WHEEL_Front", "BRAKE_Front_Disc", "SUSP_Front_Axle")):
        scene.set_origin(ob, L.FRONT_AXLE)                    # rotating parts pivot on the axle
    elif ob.name.startswith(("WHEEL_Rear", "BRAKE_Rear_Disc", "SUSP_Rear_Axle", "DRIVE_Sprocket_Rear")):
        scene.set_origin(ob, L.REAR_AXLE)
    elif ob.name.startswith(("SUSP_Fork", "SUSP_TopClamp", "SUSP_BottomClamp", "SUSP_SteeringStem",
                             "CTRL_Headlight", "CTRL_ClipOn", "CTRL_Handlebar", "CTRL_Grip")):
        scene.set_origin(ob, st["bottom"])                    # steering assembly on the steering axis
    else:
        scene.origin_to_bbox_center(ob)
for ob in high():
    ob.parent = root

# ------------------------------------------------------------------ validation
bpy.context.view_layer.update()
objs = validate.mesh_objects(high())
stt = validate.stats(objs)
print("[STAGE2] top tris:", stt["top_tris"][:10])
chk = validate.Checks()
validate.standard_checks(chk, stt, target_dims=(None, 2.05, 1.045), tri_target=(40000, 100000),
                         tri_max=150000, max_materials=8)
chk.add("V01", "BLOCKER", abs(L.WHEELBASE - 1.444) < 0.01, f"wheelbase {L.WHEELBASE:.3f} m")
inter = validate.intersections(PT.CRITICAL_PAIRS, objs)
chk.add("V02", "BLOCKER", not inter, f"critical intersections: {inter}")
print("[STAGE2] result", chk.result(), "tris", stt["tris"], "dims", tuple(round(d, 3) for d in stt["dims"]))

scene.save(paths.milestone(A, "05_FINAL_GEOMETRY"))
review("h3")
for n, cam in dict(cams, CAM_REFERENCE=ref_cam).items():
    res = (720, 720) if n in ("ORTHO_FRONT", "ORTHO_REAR") else (1080, 720)
    render.workbench(cam, os.path.join(RENDERS, f"clay_{n.lower()}.png"), "CLAY", res=res)
    render.workbench(cam, os.path.join(RENDERS, f"mat_{n.lower()}.png"), "MATERIAL", res=res)
render.workbench(cams["ORTHO_RIGHT"], os.path.join(RENDERS, "wire_ortho_right.png"), "CLAY", xray=True)
scene.save(paths.out(A, "blend", A + ".blend"))

# ------------------------------------------------------------------ export + round trip (U15)
UNCERTAIN = sorted(o.name for o in high() if o.name.startswith("UNCERTAIN"))
glb_path = paths.out(A, "glb", A + ".glb")
n_exp = len(high()) + 1
export.glb([root] + high(), glb_path)
ok, detail = export.roundtrip(glb_path, n_exp, len(PT.PALETTE))       # destroys the scene (saved above)
chk.add("U15", "BLOCKER", ok, detail)

stage1 = json.load(open(paths.out(A, "work", "stage1", "stats.json")))
validate.write_report(
    os.path.join(HERE, "report.json"), A, chk,
    metrics={"tris_high": stt["tris"], "tris_low": stage1["tris"], "materials": len(PT.PALETTE),
             "bbox_m": [round(d, 3) for d in stt["dims"]], "objects_high": stt["objects"],
             "wheelbase_m": round(L.WHEELBASE, 4), "photo_pitch_deg": round(math.degrees(L.THETA), 3),
             "rake_deg": L.RAKE_DEG},
    category="vehicle", style="realistic_game", stage1=stage1,
    assumptions=[
        "Photo shows the bike's RIGHT side; model -Y forward, +Z up, root at axle midpoint on ground.",
        "Scale 400 px/m from tyre sizes 180/55-17 & 120/70-17; matches cheatsheet length/height.",
        "Rear wheel on paddock stand in photo: 1.98 deg nose-down pitch removed; model at rest.",
        "Engine interpreted as air-cooled Honda inline-4; widths from standard construction.",
    ],
    uncertain=UNCERTAIN + ["SUSP_Shock_Rear_* mount points", "left (+X) side: chain run, covers"],
    outputs={"blend": f"output/{A}/blend/{A}.blend", "glb": f"output/{A}/glb/{A}.glb",
             "renders": f"output/{A}/renders/"})
print("[STAGE2] final", chk.result())
