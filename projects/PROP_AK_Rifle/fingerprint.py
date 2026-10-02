"""Geometry fingerprint of the S2/S3 milestones (refactor safety net).
    python wb.py run projects/PROP_AK_Rifle/fingerprint.py -- <out.json>
Per object: evaluated vertex / triangle count and an order-independent hash of the world-space
vertices rounded to 0.01 mm. Two builds with equal fingerprints have identical geometry."""
import hashlib
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import landmarks as L
from workbench import paths, stages
from workbench.bl import scene

out = sys.argv[sys.argv.index("--") + 1]
fp = {}
for st in (2, 3):
    scene.open_blend(paths.milestone(L.ASSET, stages.milestone_tag(st)))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.collections[stages.STAGES[st]["coll"]].all_objects:
        if o.type != "MESH":
            continue
        me = o.evaluated_get(dg).to_mesh()
        vs = sorted(tuple(round(c * 1e5) for c in (o.matrix_world @ v.co)) for v in me.vertices)
        fp[o.name] = [len(vs), sum(len(p.vertices) - 2 for p in me.polygons),
                      hashlib.md5(repr(vs).encode()).hexdigest()[:12],
                      [m.name for m in o.data.materials]]
with open(out, "w") as f:
    json.dump(fp, f, indent=1, sort_keys=True)
print("[FINGERPRINT]", len(fp), "objects ->", out)
