#!/usr/bin/env python3
"""
wb.py - Blender Workbench command line (run from the repository root with normal python).

  python wb.py doctor                          check Blender / Pillow / folders
  python wb.py new  <ASSET> [--category C] [--budget B]   scaffold projects/<ASSET>/ (staged pipeline)
  python wb.py build <ASSET> [--stage N|--from N|--until N] [--no-bake] [--force]
                                               run projects/<ASSET>/build.py headless (stages S1-S4)
  python wb.py gate <ASSET> [N]                PASS/FAIL of stages 1..N from report.json (exit code)
  python wb.py mask <ASSET> [--seed U V] [--thr 235] [--max-hole 400] [--fill U,V ...]
                                               photo silhouette on a plain light background -> ref/REF_MASK.png
  python wb.py snap <ASSET> <LANDMARK> [--radius 6] [--open]   suggest edge corrections for a px polyline
  python wb.py profile <ASSET> U0 U1 V0 V1 [--side top|bottom] [--step 10] [--tol 1.5] [--photo-thr 150]
                                               measured edge polyline from ref/REF_MASK.png (paste into landmarks)
  python wb.py glb <file.glb>                  structural check of a glb (tris, meshes, materials, images)
  python wb.py engine-check <file.glb>         glb check + Godot headless import if $GODOT_EXECUTABLE is set
  python wb.py regress [ASSET ...] [--update] [--no-build]    rebuild + compare metrics with the baseline
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


BUDGET_OF = {"vehicle": "hero_vehicle", "architecture": "building", "character": "character",
             "prop": "large_prop", "environment": "modular", "animation": "large_prop"}


def cmd_new(a):
    src = os.path.join(ROOT, "templates", "project")
    dst = os.path.join(ROOT, "projects", a.asset)
    if os.path.exists(dst):
        sys.exit(f"exists: {dst}")
    shutil.copytree(src, dst)
    for p in glob.glob(os.path.join(dst, "**", "*.*"), recursive=True):
        if p.endswith((".py", ".md")):
            t = open(p, encoding="utf-8").read().replace("__ASSET__", a.asset).replace("__CATEGORY__", a.category)
            t = t.replace("__BUDGET__", a.budget or BUDGET_OF.get(a.category, "large_prop"))
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
            if "stages" in r:
                res += "  " + " ".join(f"S{k}:{v}" for k, v in r["summary"].get("stages", {}).items())
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


def _landmarks(asset):
    pdir = os.path.join(ROOT, "projects", asset)
    sys.path.insert(0, pdir)
    import landmarks
    return pdir, landmarks


def cmd_mask(a):
    from PIL import Image
    from workbench.host import imgtools as T
    pdir, L = _landmarks(a.asset)
    seed = a.seed or getattr(L, "ANCHOR_PX")
    fill = [tuple(float(x) for x in f.split(",")) for f in a.fill]
    photo = os.path.join(pdir, "ref", "REAL_REFERENCE.png")
    out = os.path.join(pdir, "ref", "REF_MASK.png")
    r = T.photo_mask(photo, out, seed, a.thr, a.sat, a.max_hole, fill)
    prev = os.path.join(ROOT, "output", a.asset, "work", "ref_mask_check.png")
    os.makedirs(os.path.dirname(prev), exist_ok=True)
    ph = Image.open(photo).convert("RGB")
    tint = Image.new("RGB", ph.size, (255, 0, 255))
    Image.composite(Image.blend(ph, tint, 0.45), ph, Image.open(out).convert("L")).save(prev)
    print(f"[wb] {r}")
    print(f"[wb] LOOK at {os.path.relpath(prev, ROOT)} (magenta = mask) before trusting REF_MASK.png")


def cmd_snap(a):
    import numpy as np
    from PIL import Image
    from workbench import silhouette
    from workbench.host import imgtools as T
    pdir, L = _landmarks(a.asset)
    poly = getattr(L, a.landmark)
    photo = os.path.join(pdir, "ref", "REAL_REFERENCE.png")
    gray = np.asarray(Image.open(photo).convert("L"), np.float32)
    sug = silhouette.snap(gray, poly, a.radius, closed=not a.open)
    print(f"  {'i':>3} {'u':>7} {'v':>7} {'du':>5} {'dv':>5} {'edge':>6}  suggestion")
    for g in sug:
        if not g["ok"]:
            tip = "no clear edge - check by eye"
        elif abs(g["shift"]) < 1:
            tip = "keep"
        else:
            tip = f"-> ({g['u'] + g['du']:.0f}, {g['v'] + g['dv']:.0f})"
        print(f"  {g['i']:>3} {g['u']:>7.1f} {g['v']:>7.1f} {g['du']:>5.1f} {g['dv']:>5.1f} {g['strength']:>6.1f}  {tip}")
    out = os.path.join(ROOT, "output", a.asset, "work", f"snap_{a.landmark}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("[wb] sheet:", T.snap_sheet(photo, poly, out, sug), "(cyan = landmark, yellow = suggested edge)")


def cmd_profile(a):
    import numpy as np
    from PIL import Image
    from workbench import silhouette
    pdir, L = _landmarks(a.asset)
    mp = os.path.join(pdir, "ref", "REF_MASK.png")
    if a.photo_thr:        # 50 % rule: edge = where the darkest channel crosses mid-way object <-> background
        img = np.asarray(Image.open(os.path.join(pdir, "ref", "REAL_REFERENCE.png")).convert("RGB"))
        mask = img.min(axis=2) < a.photo_thr
    elif os.path.isfile(mp):
        mask = np.asarray(Image.open(mp).convert("L")) > 127
    else:
        sys.exit(f"[wb] no {mp}: run python wb.py mask {a.asset} first, or pass --photo-thr")
    n = max(2, int(round((a.u1 - a.u0) / a.step)) + 1)
    us = [a.u0 + (a.u1 - a.u0) * i / (n - 1) for i in range(n)]
    pts = silhouette.edge_profile(mask, us, a.v0, a.v1, a.side)
    miss = [round(u) for u, v in pts if v is None]
    pts = [(round(u), v) for u, v in pts if v is not None]
    simp = silhouette.simplify(pts, a.tol) if len(pts) > 2 else pts
    print(f"# {a.side} edge of {'photo min-channel < %d' % a.photo_thr if a.photo_thr else 'REF_MASK'}, u {a.u0:.0f}-{a.u1:.0f}, v window {a.v0:.0f}-{a.v1:.0f}, "
          f"simplified to {a.tol} px ({len(pts)} -> {len(simp)} points)" + (f"; empty columns {miss}" if miss else ""))
    print("[" + ", ".join(f"({u:.0f}, {v:.0f})" for u, v in simp) + "]")


def cmd_godot(glb):
    exe = os.environ.get("GODOT_EXECUTABLE") or shutil.which("godot")
    if not exe:
        print("[wb] engine-check: Godot not found (set GODOT_EXECUTABLE) - structural glb check only")
        return 0
    gd = os.path.join(ROOT, "scripts", "godot_import_check.gd")
    r = subprocess.run([exe, "--headless", "--script", gd, "--", os.path.abspath(glb)],
                       capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-2000:])
    return r.returncode


def _flat_metrics(rep):
    """Numbers compared by the regression test (legacy and staged reports)."""
    out = {"result": rep["summary"]["result"]}
    m = rep.get("metrics", {})
    for k in ("tris_low", "tris_high", "tris_s1"):
        if m.get(k) is not None:
            out[k] = m[k]
    if m.get("dims"):
        out["dims"] = [round(x, 3) for x in m["dims"]]
    for k, sec in rep.get("stages", {}).items():
        sm = sec.get("metrics", {})
        out[f"s{k}_tris"] = sm.get("tris")
        for key in ("R01", "R02"):
            if isinstance(sm.get(key), dict):
                out[f"s{k}_{key}_iou"] = sm[key]["iou"]
        if sm.get("lod_tris"):
            out[f"s{k}_lod_tris"] = {str(n): t for n, t in sm["lod_tris"].items()}
    return out


def _close(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b if isinstance(b, int) and isinstance(a, int) else abs(a - b) <= max(0.002, 0.005 * abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    return a == b


def cmd_regress(a):
    """Clean rebuild of projects + comparison of their numbers with tests/regress_baseline.json.
    Run after changing workbench/ (a library change must not silently change old assets)."""
    base_p = os.path.join(ROOT, "tests", "regress_baseline.json")
    base = json.load(open(base_p, encoding="utf-8")) if os.path.isfile(base_p) else {}
    assets = a.assets or sorted(base)
    if not assets:
        sys.exit("[regress] no baseline yet: python wb.py regress <ASSET ...> --update")
    fails, now = [], {}
    for asset in assets:
        if not a.no_build:
            print(f"[regress] building {asset} ...", flush=True)
            if run_script(os.path.join(ROOT, "projects", asset, "build.py"), ["--force"]) != 0:
                fails.append(f"{asset}: build crashed")
                continue
        rep = json.load(open(os.path.join(ROOT, "projects", asset, "report.json"), encoding="utf-8"))
        now[asset] = _flat_metrics(rep)
        if asset in base and not a.update:
            for k in sorted(set(base[asset]) | set(now[asset])):
                if not _close(now[asset].get(k), base[asset].get(k)):
                    fails.append(f"{asset}.{k}: {base[asset].get(k)} -> {now[asset].get(k)}")
    if a.update:
        base.update(now)
        os.makedirs(os.path.dirname(base_p), exist_ok=True)
        json.dump(base, open(base_p, "w", encoding="utf-8"), indent=1, sort_keys=True)
        print(f"[regress] baseline updated: {', '.join(now)}")
        return 0
    for f in fails:
        print("[regress] DIFF", f)
    print(f"[regress] {len(assets)} assets: {'PASS' if not fails else str(len(fails)) + ' differences'}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new"); p.add_argument("asset"); p.add_argument("--category", default="prop")
    p.add_argument("--budget", help="key of workbench.tables.BUDGETS (default from --category)")
    p = sp.add_parser("build"); p.add_argument("asset"); p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sp.add_parser("gate"); p.add_argument("asset"); p.add_argument("stage", nargs="?", type=int)
    p = sp.add_parser("mask"); p.add_argument("asset"); p.add_argument("--seed", nargs=2, type=float)
    p.add_argument("--thr", type=int, default=235); p.add_argument("--sat", type=int, default=40)
    p.add_argument("--max-hole", type=int, default=400); p.add_argument("--fill", nargs="*", default=[])
    p = sp.add_parser("snap"); p.add_argument("asset"); p.add_argument("landmark")
    p.add_argument("--radius", type=float, default=6); p.add_argument("--open", action="store_true")
    p = sp.add_parser("profile"); p.add_argument("asset")
    for k in ("u0", "u1", "v0", "v1"):
        p.add_argument(k, type=float)
    p.add_argument("--side", default="bottom", choices=("top", "bottom")); p.add_argument("--step", type=float, default=10)
    p.add_argument("--tol", type=float, default=1.5); p.add_argument("--photo-thr", type=int)
    p = sp.add_parser("glb"); p.add_argument("file")
    p = sp.add_parser("engine-check"); p.add_argument("file")
    p = sp.add_parser("regress"); p.add_argument("assets", nargs="*"); p.add_argument("--update", action="store_true")
    p.add_argument("--no-build", action="store_true")
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
        from workbench import gate
        rest = [x for x in a.rest if x != "--"]
        if rest and not gate.is_pipeline(a.asset):
            print("[wb] note: legacy project (stage1.py/stage2.py) - stage flags are ignored")
        rc = run_script(os.path.join(ROOT, "projects", a.asset, "build.py"), rest)
        if rc == 0 and gate.is_pipeline(a.asset):
            gate.print_rows(a.asset, gate.evaluate(a.asset))
        sys.exit(rc)
    elif a.cmd == "gate":
        from workbench import gate
        if not gate.is_pipeline(a.asset):
            sys.exit(f"[wb] {a.asset} is a legacy project (no staged pipeline) - see its report.json")
        ok = gate.print_rows(a.asset, gate.evaluate(a.asset, a.stage))
        print(f"[wb] gate {a.asset} S1..S{a.stage or 'last'}: {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)
    elif a.cmd == "mask":
        cmd_mask(a)
    elif a.cmd == "snap":
        cmd_snap(a)
    elif a.cmd == "profile":
        cmd_profile(a)
    elif a.cmd in ("glb", "engine-check"):
        from workbench import glbinfo
        info = glbinfo.read(a.file)
        names = info.pop("node_names")
        print(json.dumps(info, indent=1))
        print("nodes:", ", ".join(names[:40]) + (" ..." if len(names) > 40 else ""))
        if a.cmd == "engine-check":
            sys.exit(cmd_godot(a.file))
    elif a.cmd == "regress":
        sys.exit(cmd_regress(a))
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
