#!/usr/bin/env python3
"""
wb.py - Blender Workbench command line (run from the repository root with normal python).

  python wb.py doctor                          check Blender / Pillow / folders
  python wb.py new  <ASSET> [--category C]     scaffold projects/<ASSET>/ from templates/project
  python wb.py build <ASSET>                   run projects/<ASSET>/build.py headless
  python wb.py run  <script.py> [-- args]      run any bpy script headless (workbench importable)
  python wb.py list                            projects + last report result
  python wb.py grid <img> [--step 20]          labelled grid copy of an image  (-> *_grid.png)
  python wb.py crop <img> x0 y0 x1 y1 [--scale 4] [--out path]   zoomed gridded crop
  python wb.py compare <ASSET> <render.png> [--ref path]          overlay render on reference photo
  python wb.py sheet <out.png> <img> [<img> ...] [--cols 2]       contact sheet
  python wb.py present <ASSET> [--style S] [--engine CYCLES|EEVEE] [--turntable [SEC]] [--scale 50]
                                               studio presentation renders (docs/10_PRESENTATION.md)
  python wb.py inspect <model> [--render]      import + analyse a third-party model (docs/11)
  python wb.py pbr [list|preview] [--filter X] PBR texture library index / material-ball sheet (docs/11)
  python wb.py test                            smoke test of the whole library (renders + video + glb)

Blender is found via $BLENDER_EXECUTABLE, standard install folders, or PATH.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def find_blender():
    env = os.environ.get("BLENDER_EXECUTABLE")
    if env and os.path.isfile(env):
        return env
    pats = [r"C:\Program Files\Blender Foundation\Blender *\blender.exe",
            "/Applications/Blender.app/Contents/MacOS/Blender", "/usr/bin/blender", "/snap/bin/blender"]
    found = sorted((p for pat in pats for p in glob.glob(pat)), reverse=True)
    if found:
        return found[0]
    w = shutil.which("blender")
    if w:
        return w
    sys.exit("Blender not found: set BLENDER_EXECUTABLE to blender(.exe)")


def run_script(script, args=()):
    script = os.path.abspath(script)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([ROOT, os.path.dirname(script)] +
                                        ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [find_blender(), "--background", "--factory-startup", "--python-use-system-env",
           "--python-exit-code", "1", "--python", script]
    if args:
        cmd += ["--"] + list(args)
    print("[wb] blender:", cmd[0])
    print("[wb] script :", os.path.relpath(script, ROOT))
    return subprocess.run(cmd, env=env).returncode


def cmd_new(a):
    src = os.path.join(ROOT, "templates", "project")
    dst = os.path.join(ROOT, "projects", a.asset)
    if os.path.exists(dst):
        sys.exit(f"exists: {dst}")
    shutil.copytree(src, dst)
    for p in glob.glob(os.path.join(dst, "**", "*.*"), recursive=True):
        if p.endswith((".py", ".md")):
            t = open(p, encoding="utf-8").read().replace("__ASSET__", a.asset).replace("__CATEGORY__", a.category)
            open(p, "w", encoding="utf-8").write(t)
    os.makedirs(os.path.join(dst, "ref"), exist_ok=True)
    print(f"[wb] created projects/{a.asset}/  -> put photos in ref/, fill project.md, measure landmarks.py")


def cmd_list(a):
    for d in sorted(glob.glob(os.path.join(ROOT, "projects", "*", ""))):
        name = os.path.basename(os.path.dirname(d))
        rep = os.path.join(d, "report.json")
        res = "-"
        if os.path.isfile(rep):
            r = json.load(open(rep, encoding="utf-8"))
            m = r.get("metrics", {})
            res = f"{r['summary']['result']:5} tris={m.get('tris_high', m.get('tris', '?'))}"
        print(f"  {name:32} {res}")


def cmd_doctor(a):
    print("root   :", ROOT)
    print("blender:", find_blender())
    try:
        import PIL, numpy
        print("pillow :", PIL.__version__, "numpy:", numpy.__version__)
    except ImportError as e:
        print("MISSING host dependency:", e, "->  pip install pillow numpy")
    for d in ("workbench", "projects", "templates", "docs", "output"):
        print(f"{d:8}:", "ok" if os.path.isdir(os.path.join(ROOT, d)) else "MISSING")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new"); p.add_argument("asset"); p.add_argument("--category", default="prop")
    p = sp.add_parser("build"); p.add_argument("asset")
    p = sp.add_parser("run"); p.add_argument("script"); p.add_argument("rest", nargs=argparse.REMAINDER)
    sp.add_parser("list"); sp.add_parser("doctor"); sp.add_parser("test")
    p = sp.add_parser("present"); p.add_argument("asset"); p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sp.add_parser("inspect"); p.add_argument("model"); p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sp.add_parser("pbr"); p.add_argument("action", nargs="?", default="list", choices=("list", "preview"))
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sp.add_parser("grid"); p.add_argument("img"); p.add_argument("--step", type=int, default=20)
    p = sp.add_parser("crop"); p.add_argument("img"); p.add_argument("box", nargs=4, type=int)
    p.add_argument("--scale", type=int, default=4); p.add_argument("--out")
    p = sp.add_parser("compare"); p.add_argument("asset"); p.add_argument("render"); p.add_argument("--ref")
    p = sp.add_parser("sheet"); p.add_argument("out"); p.add_argument("imgs", nargs="+")
    p.add_argument("--cols", type=int, default=2)
    a = ap.parse_args()

    if a.cmd == "new":
        cmd_new(a)
    elif a.cmd == "build":
        sys.exit(run_script(os.path.join(ROOT, "projects", a.asset, "build.py")))
    elif a.cmd == "run":
        rest = [x for x in a.rest if x != "--"]
        sys.exit(run_script(a.script, rest))
    elif a.cmd == "list":
        cmd_list(a)
    elif a.cmd == "doctor":
        cmd_doctor(a)
    elif a.cmd == "present":
        rest = [x for x in a.rest if x != "--"]
        rc = run_script(os.path.join(ROOT, "scripts", "present.py"), [a.asset] + rest)
        style = rest[rest.index("--style") + 1] if "--style" in rest else "studio_dark"
        lst = os.path.join(ROOT, "output", a.asset, "presentation", f"{style}_files.txt")
        if rc == 0 and os.path.isfile(lst):
            from workbench.host import imgtools as T
            imgs = [l.strip() for l in open(lst) if l.strip()]
            print("[wb] sheet:", T.sheet(imgs, os.path.join(os.path.dirname(lst), f"{style}_sheet.png"), 2, 1920))
        sys.exit(rc)
    elif a.cmd == "inspect":
        rest = [x for x in a.rest if x != "--"]
        rc = run_script(os.path.join(ROOT, "scripts", "inspect_asset.py"), [os.path.abspath(a.model)] + rest)
        lst = os.path.join(ROOT, "output", "_inspect", os.path.splitext(os.path.basename(a.model))[0], "files.txt")
        if rc == 0 and "--render" in rest and os.path.isfile(lst):
            from workbench.host import imgtools as T
            imgs = [l.strip() for l in open(lst) if l.strip()]
            print("[wb] sheet:", T.sheet(imgs, os.path.join(os.path.dirname(lst), "sheet.png"), 2, 1920))
        sys.exit(rc)
    elif a.cmd == "pbr":
        rest = [x for x in a.rest if x != "--"]
        if a.action == "list":
            from workbench import pbrlib
            flt = rest[rest.index("--filter") + 1] if "--filter" in rest else ""
            for s in pbrlib.scan(pbrlib.library_root()):
                if flt.lower() in s["name"].lower():
                    print(f"  {s['name']:28} {s['category']:10} {s['resolution']:4} maps: {', '.join(sorted(s['maps']))}")
            sys.exit(0)
        rc = run_script(os.path.join(ROOT, "scripts", "pbr_preview.py"), rest)
        sys.exit(rc)
    elif a.cmd == "test":
        sys.exit(run_script(os.path.join(ROOT, "templates", "smoke_test.py")))
    else:
        from workbench.host import imgtools as T
        if a.cmd == "grid":
            out = os.path.splitext(a.img)[0] + "_grid.png"
            print(T.grid(a.img, out, a.step))
        elif a.cmd == "crop":
            out = a.out or os.path.splitext(a.img)[0] + "_crop_%d_%d_%d_%d.png" % tuple(a.box)
            print(T.crop(a.img, out, a.box, a.scale))
        elif a.cmd == "sheet":
            print(T.sheet(a.imgs, a.out, a.cols))
        elif a.cmd == "compare":
            pdir = os.path.join(ROOT, "projects", a.asset)
            ref = a.ref or os.path.join(pdir, "ref", "REAL_REFERENCE.png")
            sys.path.insert(0, pdir)
            marks = []
            try:
                import landmarks
                marks = getattr(landmarks, "MARKS", [])
            except ImportError:
                pass
            prefix = os.path.join(ROOT, "output", a.asset, "work", "compare_" +
                                  os.path.splitext(os.path.basename(a.render))[0])
            os.makedirs(os.path.dirname(prefix), exist_ok=True)
            n = T.overlay(ref, a.render, prefix, marks)
            print(f"[wb] {prefix}_edge.png / _blend.png  (covered px {n})")


if __name__ == "__main__":
    main()
