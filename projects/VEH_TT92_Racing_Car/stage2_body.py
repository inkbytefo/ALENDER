"""
STAGE 2 - PRIMARY FORMS (HIGH)    python wb.py build VEH_TT92_Racing_Car --stage 2

Opens 02_COMPLETE_LOW, hides the blockout and builds the big shapes at the HIGH profile:
    wheels   tyres, rims, hubs, laced wire spokes, knock-off spinners, brake drums
    body     shell loft (subsurf baked) + boolean cuts: cockpit, engine bay, nose mouth
    nose     chrome lip, five chrome slats, emblem
Milestone: 03_HIGH_PRIMARY.
"""
import stagelib as SL
from stagelib import PT
from workbench.bl import materials

SL.open_milestone("02_COMPLETE_LOW")
SL.hide_low()
materials.ensure(PT.PALETTE)

PT.build_stage(2, PT.HIGH)

SL.save_milestone("03_HIGH_PRIMARY")
SL.review(2, "primary")
print("[STAGE2] PASS")
