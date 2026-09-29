"""
STAGE 2 - HIGH POLY / REFINED for VEH_TT92_Racing_Car
    python wb.py run projects/VEH_TT92_Racing_Car/stage2.py      (after stage1.py)
Opens _02_COMPLETE_LOW, keeps LOW collections (hidden), rebuilds every part at HIGH LOD from the
same landmarks, adds details, validates, renders, exports GLB, writes report.json.
"""
import os, sys, json, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

from workbench import paths
from workbench.bl import scene, materials, render, validate, export, cameras
from workbench.bl.fasteners import Fasteners

A = "VEH_TT92_Racing_Car"
scene.open_blend(paths.milestone(A, "02_COMPLETE_LOW"))
import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)

H = PT.HIGH
WORK = paths.out(A, "work", "stage2")
RENDERS = paths.out(A, "renders")
ref_cam = bpy.data.objects["CAM_REFERENCE"]
REF_RES = L.IMAGE_SIZE


def high():
    return scene.objects_in(scene.HIGH_COLLS)


def review(tag):
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_clay.png"), "CLAY", transparent=True, res=REF_RES)
    render.workbench(ref_cam, os.path.join(WORK, f"{tag}_ref_mat.png"), "MATERIAL", transparent=True, res=REF_RES)


# ------------------------------------------------------------------ preserve LOW (hidden, kept)
for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
    scene.set_collection_visible(c, False)
materials.ensure(PT.PALETTE)

# ------------------------------------------------------------------ primary forms
PT.wheels(H); PT.body(H); PT.nose(H); PT.fins(H); PT.tail_blade(H)
scene.save(paths.milestone(A, "03_HIGH_PRIMARY"))
review("h1")

# ------------------------------------------------------------------ mechanical
PT.exhaust(H); PT.front_suspension(H); PT.rear_suspension(H); PT.canards(H)
scene.save(paths.milestone(A, "04_HIGH_MECHANICAL"))
review("h2")

# ------------------------------------------------------------------ details
PT.cockpit(H); PT.body_details(H)
D = "07_DETAILS"
fs = Fasteners(D, mat="MAT_CHROME")
bvh = PT.body_bvh()


def on_body(x, y, kind):
    hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)), 5.0)
    if hit[0] is not None:
        fs.place(kind, hit[0] - hit[1] * 0.001, hit[1])


# rivets: rear deck arc behind the cockpit and along both cockpit flanks (photo)
for i in range(15):
    a = math.pi * i / 14
    on_body(0.24 * math.cos(a), L.Y(L.COCKPIT_V[1]) + 0.04 + 0.05 * math.sin(a), "BOLT_M5")
for sg in (-1, 1):
    for i in range(10):
        v = L.COCKPIT_V[0] + 30 + (L.COCKPIT_V[1] - L.COCKPIT_V[0] - 60) * i / 9
        on_body(sg * (L.open_hw(v) + 0.035), L.Y(v), "BOLT_M5")
# bonnet strap bolts at the cowl joint (v 520) and the nose seam (v 205)
for v in (205, 520):
    for sg in (-1, 1):
        for f in (0.35, 0.7):
            on_body(sg * f * L.body_hw(v), L.Y(v), "BOLT_M6")
bpy.context.view_layer.update()

# ------------------------------------------------------------------ origins + hierarchy
root = scene.root(A)
shared = {m.data.name for m in high() if m.name.startswith("FASTENER_") and m.data.users > 1}
for ob in high():
    if ob.type != "MESH" or ob.data.name in shared:
        continue
    wheel = None
    for tag, (x, v, R, W) in PT.WHEELS.items():
        pos, side = tag.split("_")
        if ob.name.startswith((f"WHEEL_{pos}_", f"BRAKE_Drum_{tag}")) and ob.name.endswith("_" + side) \
                or ob.name == f"BRAKE_Drum_{tag}":
            wheel = (x, L.Y(v), R)
    if wheel:
        scene.set_origin(ob, wheel)                         # rotating parts pivot on their axle
    elif ob.name.startswith("COCKPIT_Steering"):
        scene.set_origin(ob, (L.X(L.STEER_WHEEL_PX[0]), L.Y(L.STEER_WHEEL_PX[1]), L.STEER_WHEEL_Z))
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
validate.standard_checks(chk, stt, tri_target=(40000, 100000), tri_max=120000, max_materials=8)
chk.add("V01", "BLOCKER", abs(L.WHEELBASE - 2.128) < 0.01, f"wheelbase {L.WHEELBASE:.3f} m (665 px / 312.5)")
tw = stt["dims"][0]
chk.add("V02", "WARN", abs(tw - 1.82) < 0.04, f"overall width {tw:.3f} m (photo 570 px = 1.82 m)")
inter = validate.intersections(PT.CRITICAL_PAIRS, objs)
chk.add("V03", "BLOCKER", not inter, f"critical intersections: {inter}")
body_ob = bpy.data.objects["BODY_Shell"]
sym = validate.symmetry_error(body_ob)
chk.add("V04", "WARN", sym < 0.003, f"body symmetry error {sym * 1000:.1f} mm")
print("[STAGE2] result", chk.result(), "tris", stt["tris"], "dims", tuple(round(d, 3) for d in stt["dims"]))

scene.save(paths.milestone(A, "05_FINAL_GEOMETRY"))
review("h3")
cams = cameras.rig_from_bounds(objs)
for n, cam in dict(cams, CAM_REFERENCE=ref_cam).items():
    res = REF_RES if n == "CAM_REFERENCE" else ((900, 720) if n in ("ORTHO_FRONT", "ORTHO_REAR") else (1280, 720))
    render.workbench(cam, os.path.join(RENDERS, f"clay_{n.lower()}.png"), "CLAY", res=res)
    render.workbench(cam, os.path.join(RENDERS, f"mat_{n.lower()}.png"), "MATERIAL", res=res)
render.workbench(cams["ORTHO_RIGHT"], os.path.join(RENDERS, "wire_ortho_right.png"), "CLAY", xray=True,
                 res=(1280, 720))
# beauty perspective (EEVEE)
render.studio_lights(center=(0, 0, 0.4), size=2.5)
render.beauty(cams["CAM_PERSPECTIVE"], os.path.join(RENDERS, "beauty_perspective.png"), res=(1600, 1000))
render.beauty(cams["CAM_PERSPECTIVE_L"], os.path.join(RENDERS, "beauty_perspective_l.png"), res=(1600, 1000))
scene.save(paths.out(A, "blend", A + ".blend"))

# ------------------------------------------------------------------ export + round trip (U15)
UNCERTAIN = sorted(o.name for o in high() if o.name.startswith("UNCERTAIN"))
glb_path = paths.out(A, "glb", A + ".glb")
n_exp = len(high()) + 1
export.glb([root] + high(), glb_path)
ok, detail = export.roundtrip(glb_path, n_exp, len(PT.PALETTE))     # destroys the scene (saved above)
chk.add("U15", "BLOCKER", ok, detail)

stage1 = json.load(open(paths.out(A, "work", "stage1", "stats.json")))
validate.write_report(
    os.path.join(HERE, "report.json"), A, chk,
    metrics={"tris_high": stt["tris"], "tris_low": stage1["tris"], "materials": len(PT.PALETTE),
             "bbox_m": [round(d, 3) for d in stt["dims"]], "objects_high": stt["objects"],
             "wheelbase_m": round(L.WHEELBASE, 4), "scale_px_per_m": L.S,
             "track_front_m": round(2 * L.TRACK_HALF_F, 3), "track_rear_m": round(2 * L.TRACK_HALF_R, 3),
             "tyre_dia_m": [round(2 * L.R_TYRE_F, 3), round(2 * L.R_TYRE_R, 3)]},
    category="vehicle", style="realistic_game", stage1=stage1,
    assumptions=[
        "Primary photo is a TOP view: front = image top (steering wheel ahead of seat, louvres and "
        "exhaust headers at the blunt end). The AI cheatsheet shows the car reversed; photo wins.",
        "Model -Y forward, +Z up, +X = car left; origin midway between the axles on the ground.",
        "Scale 312.5 px/m from rear tyre 225 px = 0.72 m; rear track 1.43 m vs cheatsheet 1.46 m.",
        "No side photo: all heights (body profile, fin, exhaust, suspension) are estimates from the "
        "cheatsheet numbers (0.78 m body, 0.12 m clearance) and front-engined GP car logic.",
        "Body built symmetric about u = 345 px; photo centre line drifts 342-347 px (perspective).",
        "Body HIGH: loft -> subsurf L1 baked -> cockpit boolean -> weighted normals (subsurf before "
        "the boolean, not live, to keep the cockpit cut crisp).",
    ],
    uncertain=UNCERTAIN + ["all heights (no side photo)", "BODY_SideLouvrePanel_L height",
                           "AERO_SideFin_* height/dihedral", "EXHAUST_* height", "tyre widths"],
    waivers=["Rule 5 organic lofts subsurf live: BODY_Shell subsurf is baked before the cockpit boolean."],
    outputs={"blend": f"output/{A}/blend/{A}.blend", "glb": f"output/{A}/glb/{A}.glb",
             "renders": f"output/{A}/renders/"})
print("[STAGE2] final", chk.result())
