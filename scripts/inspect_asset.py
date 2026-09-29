"""
Inspect a third-party model:  python wb.py inspect <model file> [--render] [--json out.json]
Imports into an empty scene, prints per-object bbox / tris / materials, optionally renders a
clay contact sheet (studio neutral_grey, 4 shots) into output/_inspect/<file stem>/.
"""
import argparse
import json
import os
import sys
import bpy

from workbench import paths
from workbench.bl import scene, assets

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--render", action="store_true")
ap.add_argument("--json", default="")
a = ap.parse_args(argv)

scene.reset()
scene.setup_collections()
objs = assets.import_model(a.model, "05_HIGH_BODY")
rep = assets.inspect(objs)
assets.print_report(rep)
stem = os.path.splitext(os.path.basename(a.model))[0]
out = paths.out("_inspect", stem)
if a.json:
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1, default=str)
if a.render:
    from workbench.bl import presentation as pres
    meshes = [o for o in objs if o.type == "MESH"]
    pres.studio(meshes, "neutral_grey")
    shots = {k: pres.SHOTS[k] for k in ("HERO_FRONT_34", "SIDE", "TOP_34", "FRONT")}
    cams = pres.hero_cameras(meshes, {k: v[:4] + ((960, 540),) for k, v in shots.items()})
    files = pres.render_stills(cams, out, "inspect_", "CYCLES", 32)
    with open(os.path.join(out, "files.txt"), "w") as f:
        f.write("\n".join(files))
    print("[INSPECT] renders in", out)
