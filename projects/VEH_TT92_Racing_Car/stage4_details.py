"""
STAGE 4 - DETAILS + DELIVERY (HIGH)   python wb.py build VEH_TT92_Racing_Car --stage 4

Opens 04_HIGH_MECHANICAL and finishes the model:
    cockpit         steering wheel, seat, dash, rim lip, cowl pad
    body_details    filler caps, air filter, bonnet louvres
    panel_lines     bonnet / cowl / tail seams, engine bay lip
    front_details   eyes with twin lamps, fender mirrors, chin spoiler, cream stripes
    fasteners       rivets and bolts
then pivots + hierarchy (everything under the VEH_TT92_Racing_Car root), validation, review
renders, GLB export with round-trip check and projects/VEH_TT92_Racing_Car/report.json.

Outputs: 05_FINAL_GEOMETRY, VEH_TT92_Racing_Car.blend (pipeline file: LOW + HIGH, used by
`wb.py present`), glb/VEH_TT92_Racing_Car.glb, renders/*.png.
"""
import os
import json
import bpy

import stagelib as SL
from stagelib import L, PT, A
from workbench import paths
from workbench.bl import scene, render, validate, export, cameras

SL.open_milestone("04_HIGH_MECHANICAL")

PT.build_stage(4, PT.HIGH)

# ---------------------------------------------------------------- pivots + hierarchy
root = scene.root(A)
PT.set_pivots(SL.high())
for ob in SL.high():
    ob.parent = root

# ---------------------------------------------------------------- validation
bpy.context.view_layer.update()
objs = validate.mesh_objects(SL.high())
st = validate.stats(objs)
print("[STAGE4] top tris:", st["top_tris"][:10])
chk = validate.Checks()
validate.standard_checks(chk, st, tri_target=(40000, 100000), tri_max=120000, max_materials=8)
chk.add("V01", "BLOCKER", abs(L.WHEELBASE - 2.128) < 0.01, f"wheelbase {L.WHEELBASE:.3f} m (665 px / 312.5)")
chk.add("V02", "WARN", abs(st["dims"][0] - 1.82) < 0.04,
        f"overall width {st['dims'][0]:.3f} m (photo 570 px = 1.82 m)")
inter = validate.intersections(PT.CRITICAL_PAIRS, objs)
chk.add("V03", "BLOCKER", not inter, f"critical intersections: {inter}")
sym = validate.symmetry_error(bpy.data.objects["BODY_Shell"])
chk.add("V04", "WARN", sym < 0.003, f"body symmetry error {sym * 1000:.1f} mm")
print("[STAGE4] result", chk.result(), "tris", st["tris"], "dims", tuple(round(d, 3) for d in st["dims"]))

SL.save_milestone("05_FINAL_GEOMETRY")

# ---------------------------------------------------------------- review renders
SL.review(4, "final")
cams = cameras.rig_from_bounds(objs)
for n, cam in dict(cams, CAM_REFERENCE=bpy.data.objects["CAM_REFERENCE"]).items():
    res = L.IMAGE_SIZE if n == "CAM_REFERENCE" else \
        ((900, 720) if n in ("ORTHO_FRONT", "ORTHO_REAR") else (1280, 720))
    render.workbench(cam, os.path.join(SL.RENDERS, f"clay_{n.lower()}.png"), "CLAY", res=res)
    render.workbench(cam, os.path.join(SL.RENDERS, f"mat_{n.lower()}.png"), "MATERIAL", res=res)
render.studio_lights(center=(0, 0, 0.4), size=2.5)
render.beauty(cams["CAM_PERSPECTIVE"], os.path.join(SL.RENDERS, "beauty_perspective.png"), res=(1600, 1000))
render.beauty(cams["CAM_PERSPECTIVE_L"], os.path.join(SL.RENDERS, "beauty_perspective_l.png"), res=(1600, 1000))
scene.save(paths.out(A, "blend", A + ".blend"))

# ---------------------------------------------------------------- export + round trip
uncertain = sorted(o.name for o in SL.high() if o.name.startswith("UNCERTAIN"))
glb_path = paths.out(A, "glb", A + ".glb")
n_exp = len(SL.high()) + 1
export.glb([root] + SL.high(), glb_path)
ok, detail = export.roundtrip(glb_path, n_exp, len(PT.PALETTE))     # destroys the scene (saved above)
chk.add("U15", "BLOCKER", ok, detail)

stage1 = json.load(open(os.path.join(SL.work(1), "stats.json")))
validate.write_report(
    os.path.join(SL.HERE, "report.json"), A, chk,
    metrics={"tris_high": st["tris"], "tris_low": stage1["tris"], "materials": len(PT.PALETTE),
             "bbox_m": [round(d, 3) for d in st["dims"]], "objects_high": st["objects"],
             "wheelbase_m": round(L.WHEELBASE, 4), "scale_px_per_m": L.S,
             "track_front_m": round(2 * L.TRACK_HALF_F, 3), "track_rear_m": round(2 * L.TRACK_HALF_R, 3),
             "tyre_dia_m": [round(2 * L.R_TYRE_F, 3), round(2 * L.R_TYRE_R, 3)]},
    category="vehicle", style="realistic_game", stage1=stage1,
    assumptions=[
        "Top photo: front = image top. Model -Y forward, +Z up, +X = car left; origin midway between "
        "the axles on the ground. Scale 312.5 px/m from the rear tyre 225 px = 0.72 m.",
        "Plan view behind v 250 px (wheels, body width, cockpit, exhaust, rear suspension) is measured "
        "on the photo. No side photo exists: every height is a design estimate.",
        "Design changes agreed with the user (not in the photo): wedge nose with chrome mouth, eyes, "
        "fender mirrors, chin spoiler, stripes; engine bay with a blown V8; exhaust mirrored to both "
        "sides; bonnet/cowl/tail panel lines. Removed: side fins, side louvre panels, tail blade, "
        "canards, door lines.",
        "Body HIGH: loft -> subsurf L1 baked -> booleans (cockpit, bay, mouth) -> weighted normals.",
    ],
    uncertain=uncertain + ["all heights (no side photo)", "ENG_* proportions (engine not visible in any photo)",
                           "EXHAUST_* height", "tyre widths"],
    waivers=["Rule 5 organic lofts subsurf live: BODY_Shell subsurf is baked before the booleans.",
             "Rule 1 reconstruct-don't-redesign: the front end and engine are user-requested redesigns."],
    outputs={"blend": f"output/{A}/blend/{A}.blend", "workspace": f"output/{A}/blend/{A}_WORKSPACE.blend",
             "glb": f"output/{A}/glb/{A}.glb", "renders": f"output/{A}/renders/"})
print("[STAGE4] final", chk.result())
if chk.result() != "PASS":
    raise SystemExit("[STAGE4] FAIL")
