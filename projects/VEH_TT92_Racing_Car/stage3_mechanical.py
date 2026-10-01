"""
STAGE 3 - MECHANICAL (HIGH)       python wb.py build VEH_TT92_Racing_Car --stage 3

Opens 03_HIGH_PRIMARY and adds the mechanical groups:
    exhaust            both sides: 4 headers -> collector -> pipe, helical heat wrap
    afterburners       one jet-style outlet on the tail: slotted can, petals, glowing liner
    front_suspension   double wishbones, uprights, spindles, dampers
    rear_suspension    hub carriers, axles, transverse coil-overs, radius rods
    engine             blown V8 in the bay: blocks, cam covers, blower, 4 stacks, belt drive
Milestone: 04_HIGH_MECHANICAL.
"""
import stagelib as SL
from stagelib import PT
from workbench.bl import validate

SL.open_milestone("03_HIGH_PRIMARY")

PT.build_stage(3, PT.HIGH)

inter = validate.intersections(PT.CRITICAL_PAIRS, validate.mesh_objects(SL.high()))
SL.save_milestone("04_HIGH_MECHANICAL")
SL.review(3, "mechanical")
if inter:
    raise SystemExit(f"[STAGE3] FAIL: critical intersections {inter}")
print("[STAGE3] PASS")
