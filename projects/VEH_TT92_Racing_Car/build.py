"""
Build VEH_TT92_Racing_Car.

    python wb.py build VEH_TT92_Racing_Car                 all stages 1-5
    python wb.py build VEH_TT92_Racing_Car --stage 4       one stage (needs the milestone before it)
    python wb.py build VEH_TT92_Racing_Car --from 2        stage 2 to the end
    python wb.py build VEH_TT92_Racing_Car --until 3       stage 1 to 3

    1 stage1_blockout.py    LOW blockout of every part            -> 02_COMPLETE_LOW
    2 stage2_body.py        wheels, body shell + cuts, nose mouth  -> 03_HIGH_PRIMARY
    3 stage3_mechanical.py  exhaust, suspension, engine            -> 04_HIGH_MECHANICAL
    4 stage4_details.py     cockpit, details, front, fasteners, checks, renders, GLB, report
    5 stage5_workspace.py   clean GUI file                         -> _WORKSPACE.blend
"""
import os
import sys
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = {1: "stage1_blockout.py", 2: "stage2_body.py", 3: "stage3_mechanical.py",
          4: "stage4_details.py", 5: "stage5_workspace.py"}

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag):
    return int(args[args.index(flag) + 1]) if flag in args else None


first, last = min(STAGES), max(STAGES)
if opt("--stage") is not None:
    first = last = opt("--stage")
if opt("--from") is not None:
    first = opt("--from")
if opt("--until") is not None:
    last = opt("--until")

for n in range(first, last + 1):
    print(f"[BUILD] ===== stage {n}: {STAGES[n]}")
    runpy.run_path(os.path.join(HERE, STAGES[n]), run_name="__main__")
print(f"[BUILD] stages {first}..{last} done")
