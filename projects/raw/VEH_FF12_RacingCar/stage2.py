"""
STAGE 2 - HIGH POLY / REFINED MODEL (VEH_FF12_RacingCar)
    python wb.py run projects/VEH_FF12_RacingCar/stage2.py

Opens <ASSET>_02_COMPLETE_LOW, keeps LOW collections (hidden), rebuilds every part at HIGH LOD
from the same landmarks, adds details, validates, renders, exports GLB, writes report.json.
"""
import os, sys, json, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

from workbench import paths
from workbench.bl import scene, materials, cameras, render, validate, export, mesh

scene.open_blend(paths.milestone("VEH_FF12_RacingCar", "02_COMPLETE_LOW"))
import landmarks as L; importlib.reload(L)
import parts as PT; importlib.reload(PT)

A = L.ASSET
H = PT.HIGH
WORK = paths.out(A, "work", "stage2")
RENDERS = paths.out(A, "renders")
os.makedirs(WORK, exist_ok=True)
os.makedirs(RENDERS, exist_ok=True)

# Preserve LOW (hidden, kept for provenance)
for c in scene.LOW_COLLS + ("08_TEMP", "01_GUIDES"):
    scene.set_collection_visible(c, False)
materials.ensure(PT.PALETTE)


def high():
    return scene.objects_in(scene.HIGH_COLLS)


# ---- Phase 1: Primary forms -------------------------------------------------
PT.wheels(H)
PT.body_shell(H)
scene.save(paths.milestone(A, "03_HIGH_PRIMARY"))

# ---- Phase 2: Mechanical assemblies -----------------------------------------
PT.suspension(H)
PT.cockpit(H)
PT.exhaust(H)
PT.chassis_and_mechanics(H)
scene.save(paths.milestone(A, "04_HIGH_MECHANICAL"))

# ---- Phase 3: Details & Fasteners -------------------------------------------
PT.fasteners(H)
scene.save(paths.milestone(A, "05_FINAL_GEOMETRY"))

# ---- Hierarchy & Pivots -----------------------------------------------------
root = scene.root(A)
for ob in high():
    if ob.type != "MESH":
        continue
    # Set wheel origins on axle pivots
    if "FL" in ob.name or "FR" in ob.name:
        if ob.name.startswith("WHEEL_"):
            y_axle = L.FRONT_AXLE_Y
            x_axle = L.AXLE_FL[0] if "FL" in ob.name else L.AXLE_FR[0]
            scene.set_origin(ob, (x_axle, y_axle, L.AXLE_Z))
    elif "RL" in ob.name or "RR" in ob.name:
        if ob.name.startswith("WHEEL_"):
            y_axle = L.REAR_AXLE_Y
            x_axle = L.AXLE_RL[0] if "RL" in ob.name else L.AXLE_RR[0]
            scene.set_origin(ob, (x_axle, y_axle, L.AXLE_Z))
    elif ob.name.startswith("COCKPIT_Steering_"):
        scene.set_origin(ob, L.STEERING_CENTER)
    else:
        scene.origin_to_bbox_center(ob)
    ob.parent = root

bpy.context.view_layer.update()

# ---- Review Cameras & Setup -------------------------------------------------
objs = validate.mesh_objects(high())
cams = cameras.rig_from_bounds(objs)
ref_cam = bpy.data.objects.get("CAM_REFERENCE")
if ref_cam:
    cams["CAM_REFERENCE"] = ref_cam

# ---- Validation Checks ------------------------------------------------------
stt = validate.stats(objs)
print("[STAGE2] evaluated stats:", {"objects": stt["objects"], "tris": stt["tris"], "dims": stt["dims"]})
print("[STAGE2] top tris:", stt["top_tris"][:8])

chk = validate.Checks()
validate.standard_checks(chk, stt, target_dims=(1.84, 4.11, 0.88),
                         tri_target=(40000, 100000), tri_max=150000, max_materials=8)

chk.add("V01", "BLOCKER", abs(L.WHEELBASE - 2.56) < 0.01, f"wheelbase {L.WHEELBASE:.3f} m")
inter = validate.intersections(PT.CRITICAL_PAIRS, objs)
chk.add("V02", "BLOCKER", not inter, f"critical intersections: {inter}")

# ---- Milestone & Main Blend Save -------------------------------------------
main_blend = paths.out(A, "blend", A + ".blend")
scene.save(main_blend)

# ---- Renders: Reference camera + 5 Orthos + 2 Perspectives + Wire ----------
if ref_cam:
    render.workbench(ref_cam, os.path.join(RENDERS, "clay_cam_reference.png"), "CLAY", transparent=True, res=L.IMAGE_SIZE)
    render.workbench(ref_cam, os.path.join(RENDERS, "mat_cam_reference.png"), "MATERIAL", transparent=True, res=L.IMAGE_SIZE)

for n in ("ORTHO_LEFT", "ORTHO_RIGHT", "ORTHO_FRONT", "ORTHO_REAR", "ORTHO_TOP",
          "CAM_PERSPECTIVE", "CAM_PERSPECTIVE_L"):
    if n in cams:
        cam = cams[n]
        res = (1080, 720) if "FRONT" not in n and "REAR" not in n else (720, 720)
        render.workbench(cam, os.path.join(RENDERS, f"clay_{n.lower()}.png"), "CLAY", res=res)
        render.workbench(cam, os.path.join(RENDERS, f"mat_{n.lower()}.png"), "MATERIAL", res=res)

# Wireframe render from right side ortho
if "ORTHO_RIGHT" in cams:
    render.workbench(cams["ORTHO_RIGHT"], os.path.join(RENDERS, "wire_ortho_right.png"), "CLAY", xray=True)

# ---- Export GLB & Round-Trip Validation ------------------------------------
UNCERTAIN = sorted(o.name for o in high() if o.name.startswith("UNCERTAIN"))
glb_path = paths.out(A, "glb", A + ".glb")
n_exp = len(high()) + 1
export.glb([root] + high(), glb_path)
ok, detail = export.roundtrip(glb_path, n_exp, len(PT.PALETTE))
chk.add("U15", "BLOCKER", ok, detail)

# ---- Report JSON -----------------------------------------------------------
stage1_stats = {}
s1_json = paths.out(A, "work", "stage1", "stats.json")
if os.path.isfile(s1_json):
    stage1_stats = json.load(open(s1_json, encoding="utf-8"))

validate.write_report(
    os.path.join(HERE, "report.json"), A, chk,
    metrics={
        "tris_high": stt["tris"],
        "tris_low": stage1_stats.get("tris", 0),
        "materials": len(PT.PALETTE),
        "bbox_m": [round(d, 3) for d in stt["dims"]],
        "objects_high": stt["objects"],
        "wheelbase_m": round(L.WHEELBASE, 4),
        "track_width_m": round(L.TRACK_WIDTH, 4),
    },
    category="vehicle",
    style="realistic_game",
    stage1=stage1_stats,
    assumptions=[
        "Reference photo is top-down view (681x1265 px) showing exact wheelbase (2.56 m) and track width (1.46 m).",
        "Modern wide Yokohama Advan tires mounted on vintage wire spoke knock-off wheels.",
        "External exhaust header runner exits right hood louvers and routes along the right flank to a megaphone tip.",
        "Internal spaceframe and engine block modeled conservatively under UNCERTAIN_ prefix.",
    ],
    uncertain=UNCERTAIN + ["Internal chassis mounting gussets", "Cockpit pedal box"],
    outputs={
        "blend": f"output/{A}/blend/{A}.blend",
        "glb": f"output/{A}/glb/{A}.glb",
        "renders": f"output/{A}/renders/",
    }
)

print(f"[STAGE2] FINAL RESULT: {chk.result()}")
