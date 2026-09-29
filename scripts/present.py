"""
Presentation renders for any finished asset (bpy script, run through wb.py):

    python wb.py present <ASSET> [--style studio_dark|studio_light|neutral_grey|clay]
                                 [--engine CYCLES|EEVEE] [--samples 192] [--shots HERO_FRONT_34,SIDE|none]
                                 [--turntable [SECONDS]] [--scale 100] [--blend path.blend]

Opens output/<ASSET>/blend/<ASSET>.blend (the final model), shows only the HIGH collections,
builds the studio (workbench.bl.presentation), renders auto-framed hero shots into
output/<ASSET>/presentation/<style>_<shot>.png, a contact sheet, optional turntable MP4, and saves
output/<ASSET>/blend/<ASSET>_PRESENTATION.blend for GUI inspection. The source .blend is not modified.
"""
import argparse
import os
import sys
import bpy

from workbench import paths
from workbench.bl import scene, presentation as pres

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("asset")
ap.add_argument("--style", default="studio_dark", choices=sorted(pres.STYLES))
ap.add_argument("--engine", default="CYCLES", choices=("CYCLES", "EEVEE"))
ap.add_argument("--samples", type=int, default=0)
ap.add_argument("--shots", default="")
ap.add_argument("--turntable", nargs="?", const=8.0, type=float, default=0.0)
ap.add_argument("--scale", type=int, default=100, help="resolution percentage (50 = quick preview)")
ap.add_argument("--blend", default="")
a = ap.parse_args(argv)

A = a.asset
src = a.blend or paths.out(A, "blend", A + ".blend")
if not os.path.isfile(src):
    sys.exit(f"[PRESENT] missing {src} - build the asset first (python wb.py build {A})")
scene.open_blend(src)

# show only the finished model: HIGH collections (+ anything outside the standard layout)
hide = set(scene.LOW_COLLS) | {"00_REFERENCE", "01_GUIDES", "08_TEMP"}
for c in bpy.data.collections:
    if c.name in hide:
        c.hide_render = c.hide_viewport = True
objs = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("PRES_")
        and o.visible_get() and not o.hide_render
        and not any(c.name in hide for c in o.users_collection)]
print(f"[PRESENT] {A}: {len(objs)} mesh objects, style {a.style}, engine {a.engine}")

st = pres.studio(objs, a.style)
shots = {k: v for k, v in pres.SHOTS.items() if not a.shots or k in a.shots.split(",")}   # --shots none = video only
cams = pres.hero_cameras(objs, shots)
engine = "BLENDER_EEVEE" if a.engine == "EEVEE" else "CYCLES"
samples = a.samples or (192 if engine == "CYCLES" else 64)
bpy.context.scene.render.resolution_percentage = a.scale
out = paths.out(A, "presentation")
scene.save(paths.out(A, "blend", A + "_PRESENTATION.blend"))
pres.setup_engine(engine, samples)
files = []
for n, cam in cams.items():
    bpy.context.scene.camera = cam
    r = tuple(cam["resolution"])
    sfx = "_eevee" if engine == "BLENDER_EEVEE" else ""
    p = pres.still(cam, os.path.join(out, f"{a.style}_{n.lower()}{sfx}.png"),
                   (r[0] * a.scale // 100, r[1] * a.scale // 100))
    files.append(p)
    print("[PRESENT] wrote", p)
if a.turntable:
    mp4 = pres.turntable_video(objs, os.path.join(paths.out(A, "video"), f"{a.style}_turntable.mp4"),
                               seconds=a.turntable, res=(1920 * a.scale // 100, 1080 * a.scale // 100))
    print("[PRESENT] wrote", mp4)
scene.save(paths.out(A, "blend", A + "_PRESENTATION.blend"))
if files and engine == "CYCLES":                 # the contact sheet lists the final (Cycles) stills
    with open(os.path.join(out, f"{a.style}_files.txt"), "w") as f:
        f.write("\n".join(files))
print("[PRESENT] done", len(files), "stills")
