"""
Stage gates on the host (pure python): is a stage really done?  python wb.py gate <ASSET> [N]

A stage passes only if ALL of these hold (the agent cannot talk its way past them):
  * report.json has that stage and every earlier one with result PASS
  * every stage was built from the CURRENT inputs (hash of the project's *.py files)
  * the stage milestone .blend exists
"""
import glob
import hashlib
import json
import os

from workbench import paths, stages


def inputs_hash(project_dir):
    """sha1 of every *.py in the project folder (landmarks, parts, hooks) - build.py excluded."""
    h = hashlib.sha1()
    for p in sorted(glob.glob(os.path.join(project_dir, "*.py"))):
        if os.path.basename(p) == "build.py":
            continue
        h.update(os.path.basename(p).encode())
        with open(p, "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:12]


def load_report(asset):
    p = os.path.join(paths.project_dir(asset), "report.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def is_pipeline(asset):
    """True for projects on the staged pipeline (build.py calls workbench.bl.pipeline)."""
    b = os.path.join(paths.project_dir(asset), "build.py")
    return os.path.isfile(b) and "pipeline" in open(b, encoding="utf-8").read()


def evaluate(asset, upto=None):
    """[(stage, ok, reason, failed_blockers)] for stages 1..upto (default: highest in the report)."""
    rep = load_report(asset) or {}
    st = rep.get("stages", {})
    if upto is None:
        upto = max([int(k) for k in st] or [1])
    cur = inputs_hash(paths.project_dir(asset))
    rows = []
    for s in range(1, upto + 1):
        sec = st.get(str(s))
        if sec is None:
            rows.append((s, False, "not built", []))
            continue
        failed = [f"{c['id']} {c['detail']}" for c in sec.get("checks", [])
                  if c["severity"] == "BLOCKER" and c["result"] == "FAIL"]
        reasons = []
        if sec["summary"]["result"] != "PASS":
            reasons.append(f"{len(failed)} blocker(s) failed")
        if sec.get("inputs_hash") != cur:
            reasons.append("STALE: landmarks/parts changed since this stage was built")
        ms = os.path.join(paths.OUTPUT, asset, "blend", f"{asset}_{stages.milestone_tag(s)}.blend")
        if not os.path.isfile(ms):
            reasons.append("milestone missing: " + os.path.relpath(ms, paths.ROOT))
        rows.append((s, not reasons, "; ".join(reasons) or "PASS", failed))
    return rows


def print_rows(asset, rows):
    names = {k: v["key"] for k, v in stages.STAGES.items()}
    for s, ok, why, failed in rows:
        print(f"  S{s} {names.get(s, '?'):10} {'PASS' if ok else 'FAIL'}  {'' if ok else why}")
        for f in failed[:10]:
            print(f"        - {f}")
    return all(ok for _, ok, _, _ in rows)
