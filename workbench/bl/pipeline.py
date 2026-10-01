"""
Stage runner (docs/01_WORKFLOW.md). A project's build.py is only:

    from workbench.bl import pipeline
    pipeline.main(__file__)

    python wb.py build <ASSET> [--stage N | --from N | --until N] [--no-bake] [--force]

Every stage opens the previous milestone, rebuilds ITS collection from the same builders
(parts.PARTS) with its profile (parts.PROFILES[stage]), measures itself and writes its section of
report.json. A failed stage stops the run (--force continues). Gates: python wb.py gate <ASSET>.

  S1 PRIMITIVE  silhouette R01/R02, dims U01, intersections X01, naming N01, budget U08
  S2 LOWPOLY    + UV atlas, hygiene U04/U05/U11 as BLOCKER, U09 range, U13/U14, drift D01/D02
  S3 DETAIL     + smoothing policy H01, drift vs S2, pivots, hero .blend/.glb, U15
  S4 GAME       bake S3 -> S2 atlas, LOD1-2, collision, exports, G01-G06, M01, U15

parts.py contract: PALETTE, PROFILES {1,2,3}, PARTS [stages.Part], CATEGORY (tables.BUDGETS),
optional CRITICAL_PAIRS, TARGET_DIMS (x, y, z | None), GROUND (lowest point at Z=0, default True),
PIVOTS {base: fn -> xyz}, CHILDREN {child_base: parent_base}, GAME dict(engine, bake, tex, lod,
drop_small_m, uv_m), GATES {check_id: severity override}, guide_points(), after_build(stage, objs).
landmarks.py: ASSET, REF, IMAGE_SIZE, ANCHORS, SILHOUETTE [px polygons], optional PART_OUTLINES.
"""
import importlib
import json
import os
import shutil
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

from workbench import gate, paths, silhouette, stages, tables
from workbench.bl import scene, materials, cameras, render, validate, export, uv, game


# ----------------------------------------------------------------------------- context
class Ctx:
    def __init__(self, build_file, argv):
        self.here = os.path.dirname(os.path.abspath(build_file))
        if self.here not in sys.path:
            sys.path.insert(0, self.here)
        self.L = importlib.reload(importlib.import_module("landmarks"))
        self.PT = importlib.reload(importlib.import_module("parts"))
        self.A = self.L.ASSET
        self.argv = argv
        self.force = "--force" in argv
        self.photo = os.path.join(self.here, "ref", getattr(self.L, "REFERENCE_IMAGE", "REAL_REFERENCE.png"))
        self.mask = os.path.join(self.here, "ref", "REF_MASK.png")
        self.report_path = os.path.join(self.here, "report.json")
        self.hash = gate.inputs_hash(self.here)
        self.budget = tables.BUDGETS[getattr(self.PT, "CATEGORY", "large_prop")]
        self.GAME = dict(engine="godot", bake=True, tex=None, lod=None, drop_small_m=0.02, uv_m=2.0)
        self.GAME.update(getattr(self.PT, "GAME", {}))
        if "--no-bake" in argv:
            self.GAME["bake"] = False
        self.gates = getattr(self.PT, "GATES", {})

    def work(self, s, clean=False):
        d = os.path.join(paths.OUTPUT, self.A, "work", f"s{s}")
        if clean and os.path.isdir(d):
            shutil.rmtree(d)                     # lesson 14: no stale review images
        os.makedirs(d, exist_ok=True)
        return d

    def milestone(self, s):
        return paths.milestone(self.A, stages.milestone_tag(s))

    def sev(self, cid, default):
        return self.gates.get(cid, default)


def log(s, *msg):
    print(f"[STAGE{s}]", *msg, flush=True)


# ----------------------------------------------------------------------------- build
def stage_objects(s):
    return [o for o in scene.coll(stages.STAGES[s]["coll"]).all_objects if o.type == "MESH"]


def build(ctx, s):
    """Run every part builder with the stage profile; tag, suffix and collect what they made."""
    P = ctx.PT.PROFILES[s]
    coll = stages.STAGES[s]["coll"]
    for o in list(scene.coll(coll).all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for part in ctx.PT.PARTS:
        fn = part.builder(s)
        if fn is None:
            continue
        fn(P)
        # everything this part made: mesh objects without a wb_part tag (earlier stages are tagged)
        for o in [o for o in bpy.data.objects if o.type == "MESH" and "wb_part" not in o]:
            if o.name.startswith("TEMP_"):
                continue
            if not o.name.endswith(P["suffix"]):
                o.name = stages.nm(P, o.name)
            if coll not in [c.name for c in o.users_collection]:
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                scene.coll(coll).objects.link(o)
            o["wb_part"] = part.key
            o["wb_stage"] = s
    for o in [o for o in bpy.data.objects if o.name.startswith("TEMP_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    objs = stage_objects(s)
    if hasattr(ctx.PT, "after_build"):
        ctx.PT.after_build(s, objs)
        objs = stage_objects(s)
    log(s, f"built {len(objs)} objects from {len(ctx.PT.PARTS)} parts")
    return objs


# ----------------------------------------------------------------------------- images in Blender
def _photo_rgb(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return (a.reshape(h, w, 4)[::-1, :, :3] * 255).astype(np.uint8)


def _sil_metrics(ctx, s, chk, cid, ref_mask, ren_mask, tag, photo, severity, thresholds):
    m = silhouette.metrics(ref_mask, ren_mask)
    ok, detail = silhouette.gate(m, thresholds["iou"], thresholds["p95"])
    worst = "; ".join(f"{z['hint']} {z['signed_px']:+.0f}px @u{z['box'][0]}-{z['box'][2]} v{z['box'][1]}-{z['box'][3]}"
                      for z in m["zones"][:3])
    chk.add(cid, ctx.sev(cid, severity), ok, detail + (f" | worst: {worst}" if worst else ""))
    render.write_rgb(silhouette.diff_rgb(ref_mask, ren_mask, photo), os.path.join(ctx.work(s), f"s{s}_{cid}_{tag}_diff.png"))
    return m


# ----------------------------------------------------------------------------- evaluate
def evaluate(ctx, s, objs, extra_metrics=None, extra_checks=None):
    """Numbers for one stage -> report.json section. Returns 'PASS' | 'FAIL'."""
    L, PT, B = ctx.L, ctx.PT, ctx.budget
    work = ctx.work(s)
    chk = validate.Checks()
    st = validate.stats(objs)
    metrics = dict(objects=st["objects"], tris=st["tris"], dims=[round(d, 4) for d in st["dims"]],
                   bbox_min=[round(d, 4) for d in st["bbox_min"]], top_tris=st["top_tris"][:10],
                   materials=st["materials_used"])
    # --- universal
    td = getattr(PT, "TARGET_DIMS", None)
    if td:
        tol = 0.03 if s == 1 else 0.02
        d = st["dims"]
        ok = all(abs(d[i] - t) / t <= tol for i, t in enumerate(td) if t)
        chk.add("U01", "BLOCKER", ok, "bbox %.3f x %.3f x %.3f m vs target %s (+-%d%%)" % (*d, td, tol * 100))
    chk.add("U02", "BLOCKER", not st["bad_scale"], st["bad_scale"] or "all scales 1.0")
    if getattr(PT, "GROUND", True):
        chk.add("U03", "BLOCKER", abs(st["bbox_min"][2]) < 0.002, "lowest z = %.4f" % st["bbox_min"][2])
    if s >= 2:
        chk.add("U06", "BLOCKER", not st["no_uv"], st["no_uv"] or "all meshes have UVs")
    chk.add("U07", "BLOCKER", not st["empty_slots"], st["empty_slots"] or "no empty material slots")
    tmax = {1: B["s1_max"], 2: B["s2_max"], 3: B["s3_max"]}[s]
    chk.add("U08", ctx.sev("U08", "BLOCKER"), st["tris"] <= tmax, f"{st['tris']} tris (S{s} max {tmax})")
    if s == 2:
        lo, hi = B["s2"]
        chk.add("U09", "WARN", lo <= st["tris"] <= hi, f"{st['tris']} tris (LOD0 target {lo}-{hi})")
    chk.add("U10", "BLOCKER", len(st["materials_used"]) <= B["mats"], f"{len(st['materials_used'])} materials (max {B['mats']})")
    hy = validate.hygiene(objs)
    validate.hygiene_checks(chk, hy, blocker=s >= 2, degenerate_blocker=s == 2)
    metrics["hygiene"] = hy["total"]
    validate.policy_checks(chk, objs, stages.STAGES[s]["suffix"])
    hits = validate.intersections(getattr(PT, "CRITICAL_PAIRS", []), objs)
    chk.add("X01", ctx.sev("X01", "BLOCKER"), not hits, hits[:8] or "0 critical intersections")
    # --- reference silhouettes
    ref_cam = bpy.data.objects.get("CAM_REFERENCE")
    if ref_cam is not None:
        size = tuple(ref_cam["wb_image_size"])
        sil_path = render.silhouette(ref_cam, objs, os.path.join(work, f"s{s}_silhouette.png"))
        ren = render.read_alpha(sil_path) > 0.5
        photo = _photo_rgb(ctx.photo) if os.path.isfile(ctx.photo) else None
        g = tables.SILHOUETTE_GATES[s]
        if getattr(L, "SILHOUETTE", None):
            ref = silhouette.rasterize(L.SILHOUETTE, size, close_px=3)
            metrics["R01"] = _sil_metrics(ctx, s, chk, "R01", ref, ren, "landmarks", photo, "BLOCKER", g)
        if os.path.isfile(ctx.mask):
            pm = _photo_rgb(ctx.mask)[..., 0] > 127
            metrics["R02"] = _sil_metrics(ctx, s, chk, "R02", pm, ren, "photo", photo, "BLOCKER",
                                          tables.PHOTO_GATES[s])
        outlines = getattr(L, "PART_OUTLINES", {})
        if outlines:
            per = {}
            for key, poly in outlines.items():
                sel = [o for o in objs if stages.base_name(o.name).startswith(key)]
                if not sel:
                    per[key] = "no objects"
                    continue
                pth = render.silhouette(ref_cam, sel, os.path.join(work, f"s{s}_part_{key}.png"))
                m = silhouette.metrics(silhouette.rasterize([poly], size), render.read_alpha(pth) > 0.5)
                per[key] = dict(iou=m["iou"], b_p95=m["b_p95"], zones=m["zones"][:2])
            bad = {k: v for k, v in per.items() if not isinstance(v, dict) or v["iou"] < g["iou"] or v["b_p95"] > g["p95"]}
            chk.add("R03", ctx.sev("R03", "WARN"), not bad,
                    ", ".join(f"{k}: iou {v['iou']:.2f} p95 {v['b_p95']:.0f}px" if isinstance(v, dict) else f"{k}: {v}"
                              for k, v in bad.items()) or f"{len(per)} part outlines within iou {g['iou']} / p95 {g['p95']} px")
            metrics["R03"] = per
        prev = os.path.join(paths.OUTPUT, ctx.A, "work", f"s{s - 1}", f"s{s - 1}_silhouette.png")
        if s >= 2 and s - 1 in (1, 2) and os.path.isfile(prev):
            dg = tables.DRIFT_GATES[s]
            pm = render.read_alpha(prev) > 0.5
            metrics["D01"] = _sil_metrics(ctx, s, chk, "D01", pm, ren, f"vs_s{s - 1}", photo, "BLOCKER", dg)
        render.workbench(ref_cam, os.path.join(work, f"s{s}_ref_clay.png"), "CLAY", transparent=True)
        render.workbench(ref_cam, os.path.join(work, f"s{s}_ref_mat.png"), "MATERIAL", transparent=True)
    prev_rep = (load_report(ctx).get("stages", {}).get(str(s - 1)) or {}) if s >= 2 else {}
    if prev_rep.get("metrics", {}).get("dims"):
        pd = prev_rep["metrics"]["dims"]
        # thin axes (< 25 % of the longest) are dominated by small protrusions (handles, mirrors)
        # that a coarser stage legitimately omits -> only the main axes must stay put
        axes = [i for i in range(3) if pd[i] >= 0.25 * max(pd)]
        rel = max(abs(st["dims"][i] - pd[i]) / pd[i] for i in axes)
        lim = tables.DRIFT_GATES[s]["dims"]
        chk.add("D02", "BLOCKER", rel <= lim, f"bbox change vs S{s - 1} on axes {''.join('XYZ'[i] for i in axes)}: "
                f"{rel:.1%} (max {lim:.1%})")
    for fn in extra_checks or []:
        fn(chk, metrics)
    metrics.update(extra_metrics or {})
    cams = cameras.rig_from_bounds(objs)
    render.review_set({k: v for k, v in cams.items() if k != "CAM_PERSPECTIVE_L"}, work, f"s{s}", modes=("CLAY",))
    return write_stage(ctx, s, chk, metrics)


def load_report(ctx):
    if os.path.isfile(ctx.report_path):
        with open(ctx.report_path, encoding="utf-8") as f:
            r = json.load(f)
        if "stages" in r:
            return r
    return dict(asset=ctx.A, pipeline="stages-v1", stages={})


def write_stage(ctx, s, chk, metrics):
    rep = load_report(ctx)
    rep["blender"] = bpy.app.version_string
    rep["stages"][str(s)] = dict(stage=stages.STAGES[s]["key"], summary=chk.summary(), inputs_hash=ctx.hash,
                                 time=time.strftime("%Y-%m-%d %H:%M:%S"), metrics=metrics, checks=chk.items)
    for k in [k for k in rep["stages"] if int(k) > s and rep["stages"][k].get("inputs_hash") != ctx.hash]:
        rep["stages"][k]["summary"]["result"] = "STALE"
    res = {k: v["summary"]["result"] for k, v in sorted(rep["stages"].items())}
    rep["summary"] = dict(result="PASS" if res and all(r == "PASS" for r in res.values()) else "FAIL",
                          stages=res, blockers_failed=sum(v["summary"]["blockers_failed"] for v in rep["stages"].values()))
    m = {k: rep["stages"][k]["metrics"].get("tris") for k in rep["stages"]}
    rep["metrics"] = dict(tris_s1=m.get("1"), tris_low=m.get("2"), tris_high=m.get("3"),
                          dims=metrics.get("dims"), game=rep["stages"].get("4", {}).get("metrics", {}).get("lod_tris"))
    for k in ("assumptions", "uncertain", "known_limitations", "licence"):
        if hasattr(ctx.PT, k.upper()):
            rep[k] = getattr(ctx.PT, k.upper())
    with open(ctx.report_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, default=str)
    r = chk.result()
    log(s, f"GATE {r}  ({chk.summary()['blockers_failed']} blockers, {chk.summary()['warnings']} warnings)")
    return r


# ----------------------------------------------------------------------------- stages
def stage1(ctx):
    L, PT = ctx.L, ctx.PT
    scene.reset()
    scene.setup_collections(stages.COLLECTIONS)
    materials.ensure(PT.PALETTE)
    if os.path.isfile(ctx.photo) and getattr(L, "ANCHORS", None):
        cam = cameras.reference_camera(L.REF, L.ANCHORS)
        cameras.reference_image(L.REF, ctx.photo, cam)
        bpy.context.scene.camera = cam
        log(1, "reference camera anchor error px:", cam["anchor_reprojection_error_px"])
    if hasattr(PT, "guide_points"):
        scene.guides(PT.guide_points())
    scene.save(paths.milestone(ctx.A, "S0_SETUP"))
    ctx.work(1, clean=True)
    objs = build(ctx, 1)
    scene.save(ctx.milestone(1))
    return evaluate(ctx, 1, objs)


def _open(ctx, s):
    src = ctx.milestone(s - 1)
    if not os.path.isfile(src):
        raise SystemExit(f"[STAGE{s}] needs {src} - run the earlier stage first")
    scene.open_blend(src)
    materials.ensure(ctx.PT.PALETTE)
    for k in range(1, s):
        scene.set_collection_visible(stages.STAGES[k]["coll"], False)
    for c in ("01_GUIDES", "08_TEMP"):
        scene.set_collection_visible(c, False)
    ctx.work(s, clean=True)


def _uv_checks(objs, layer="UV_Bake"):
    def fn(chk, metrics):
        ov = uv.overlap(objs, layer)
        td = uv.texel_density(objs, layer)
        chk.add("U13", "BLOCKER", ov["overlap"] <= 0.005 and ov["outside"] <= 0.001,
                f"{layer}: overlap {ov['overlap']:.2%}, outside 0-1 {ov['outside']:.2%}, coverage {ov['coverage']:.0%}")
        chk.add("U14", "WARN", td["spread"] <= 2.5,
                f"texel density {td['min']}-{td['max']} px/m at 2k (spread {td['spread']}, max 2.5)")
        metrics["uv_overlap"], metrics["texel"] = ov, dict(min=td["min"], max=td["max"], spread=td["spread"])
    return fn


def stage2(ctx):
    _open(ctx, 2)
    objs = build(ctx, 2)
    info = uv.atlas(objs, uv_m=ctx.GAME["uv_m"])
    log(2, "uv atlas", info)
    scene.save(ctx.milestone(2))
    return evaluate(ctx, 2, objs, extra_metrics=dict(uv=info), extra_checks=[_uv_checks(objs)])


def _hierarchy(ctx, objs_by_base, root):
    """Pivots (origins) + parenting: CHILDREN ride with their parent, everything else on the root."""
    PT = ctx.PT
    game.set_pivots(objs_by_base, getattr(PT, "PIVOTS", {}))
    ch = getattr(PT, "CHILDREN", {})
    for b, ob in objs_by_base.items():
        par = objs_by_base.get(ch.get(b)) if ch.get(b) else None
        scene.parent_keep([ob], par or root)


def stage3(ctx):
    _open(ctx, 3)
    objs = build(ctx, 3)
    root = scene.root(ctx.A)
    _hierarchy(ctx, {stages.base_name(o.name): o for o in objs}, root)
    scene.save(ctx.milestone(3))
    hero = paths.out(ctx.A, "blend", ctx.A + ".blend")
    res = evaluate(ctx, 3, objs)
    scene.save(hero)
    glb = paths.out(ctx.A, "glb", ctx.A + "_hero.glb")
    export.glb([root] + objs, glb)
    nmat = len({m for o in objs for m in o.data.materials if m})
    ok, detail = export.roundtrip(glb, len(objs) + 1, nmat)
    _append_check(ctx, 3, "U15", "BLOCKER", ok, "hero glb: " + detail)
    return load_report(ctx)["stages"]["3"]["summary"]["result"]


def _append_check(ctx, s, cid, sev, ok, detail):
    rep = load_report(ctx)
    sec = rep["stages"][str(s)]
    sec["checks"].append(dict(id=cid, severity=sev, result="PASS" if ok else "FAIL", detail=str(detail)))
    print(f"   [{sev}] {cid}: {'PASS' if ok else 'FAIL'} - {detail}")
    chk = validate.Checks()
    chk.items = sec["checks"]
    sec["summary"] = chk.summary()
    res = {k: v["summary"]["result"] for k, v in sorted(rep["stages"].items())}
    rep["summary"].update(result="PASS" if all(r == "PASS" for r in res.values()) else "FAIL", stages=res)
    with open(ctx.report_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, default=str)


def stage4(ctx):
    from workbench import glbinfo
    A, PT, G, B = ctx.A, ctx.PT, ctx.GAME, ctx.budget
    _open(ctx, 4)
    for k in (2, 3):                                     # bake needs the sources selectable
        scene.set_collection_visible(stages.STAGES[k]["coll"], True)
    coll, ccoll = stages.STAGES[4]["coll"], stages.COLL_COLLISION
    for c in (coll, ccoll):
        for o in list(scene.coll(c).all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
    lp, hp = stage_objects(2), stage_objects(3)
    root = scene.root(A)
    pivots, children = getattr(PT, "PIVOTS", {}), getattr(PT, "CHILDREN", {})
    movers = set(pivots) | set(children)
    lod0 = game.copies(lp, 0, coll)
    game.set_pivots(lod0, pivots)
    tex, metrics = None, {}
    size = G["tex"] or B["tex"]
    if G["bake"]:
        t0 = time.time()
        tex = game.bake(hp, list(lod0.values()), paths.out(A, "textures"), size, prefix=f"T_{A}")
        metrics["bake"] = dict(tex["stats"], seconds=round(time.time() - t0, 1))
        log(4, "bake", metrics["bake"])
        game.assign_single(lod0.values(), game.game_material(f"MAT_{A}_Baked", tex))
    for k in (2, 3):
        scene.set_collection_visible(stages.STAGES[k]["coll"], False)
    static = [o for b, o in lod0.items() if b not in movers]
    body = game.merge(static, f"{A}_Body_LOD0", coll)
    for o in static:
        bpy.data.objects.remove(o, do_unlink=True)
    levels = {0: dict({"__body__": body}, **{b: o for b, o in lod0.items() if b in movers})}
    ratios = G["lod"] or B["lod"]
    for n, r in enumerate(ratios, start=1):
        lvl = {}
        for b, ob in levels[0].items():
            if n == len(ratios) and b != "__body__" and game.diag(ob) < G["drop_small_m"]:
                continue                                  # tiny movers vanish at the last LOD
            lvl[b] = game.lod_copy(ob, r, f"{A}_Body_LOD{n}" if b == "__body__" else f"{b}_LOD{n}", coll)
        levels[n] = lvl
    for lvl in levels.values():
        for b, ob in lvl.items():
            par = lvl.get(children.get(b)) if children.get(b) else None
            scene.parent_keep([ob], par or root)
    groups = {p.key: [o for o in lp if o.get("wb_part") == p.key] for p in PT.PARTS}
    cols = game.collision(groups, {p.key: p.collision for p in PT.PARTS}, G["engine"], body.name, ccoll)
    scene.parent_keep([c for _, c, _ in cols], root)
    _review_game(ctx, levels, hp)
    scene.save(ctx.milestone(4))
    # --- exports
    files = {}
    for n, lvl in levels.items():
        objs_n = list(lvl.values()) + ([c for _, c, _ in cols] if n == 0 else [])
        files[n] = export.glb([root] + objs_n, paths.out(A, "glb", f"{A}_LOD{n}.glb"))
    if tables.ENGINES[G["engine"]]["fmt"] == "fbx":
        export.fbx([root] + list(levels[0].values()) + [c for _, c, _ in cols], paths.out(A, "fbx", f"{A}_LOD0.fbx"))
    # --- checks
    chk = validate.Checks()
    ltris = {n: sum(game.tris(o) for o in lvl.values()) for n, lvl in levels.items()}
    metrics["lod_tris"] = ltris
    # +20 %, plus the 4-tri floor per object that collapse decimation cannot go below
    ok = all(ltris[n] <= ltris[0] * r * 1.2 + 4 * len(levels[n]) for n, r in enumerate(ratios, start=1))
    chk.add("G01", "BLOCKER", ok, "LOD tris " + " / ".join(f"{ltris[n]}" for n in sorted(ltris)) +
            f" (targets x{' x'.join(str(r) for r in ratios)} +20%)")
    need = [p.key for p in PT.PARTS if p.collision not in (None, "none") and groups[p.key]]
    got = {k: f for k, _, f in cols}
    chk.add("G02", "BLOCKER", set(need) <= set(got) and all(f <= 255 for f in got.values()),
            f"{len(cols)} colliders ({G['engine']} naming), faces {sorted(got.values())} (max 255); missing {sorted(set(need) - set(got))}")
    if tex:
        nm = tex["stats"]["normal_mean"]
        sane = abs(nm[0] - 0.5) < 0.12 and abs(nm[1] - 0.5) < 0.12 and nm[2] > 0.7
        sizes = {k: bpy.data.images.load(tex[k], check_existing=True).size[:] for k in ("base", "orm", "normal")}
        chk.add("G03", "BLOCKER", sane and all(sz == (size, size) for sz in sizes.values()),
                f"textures {sizes} (want {size}), normal mean {nm} (tangent ~0.5/0.5/1)")
        metrics["textures"] = {k: os.path.relpath(tex[k], paths.ROOT) for k in ("base", "orm", "normal")}
    mb = os.path.getsize(files[0]) / 1e6
    chk.add("G04", "BLOCKER", mb <= B["glb_mb"], f"LOD0 glb {mb:.2f} MB (max {B['glb_mb']} MB)")
    info = glbinfo.read(files[0])
    col_tris = sum(game.tris(c) for _, c, _ in cols)
    want_m = 1 if tex else None
    okg = info["tris"] == ltris[0] + col_tris and (want_m is None or info["materials"] == want_m) and \
        (not tex or len(info["images"]) == 3)
    chk.add("G05", "BLOCKER", okg, f"glb: {info['meshes']} meshes, {info['tris']} tris (expect {ltris[0] + col_tris}), "
            f"{info['materials']} materials, images {info['images']}")
    metrics["glb"] = {n: dict(glbinfo.read(p), node_names=None) for n, p in files.items()}
    names = [o.name for lvl in levels.values() for o in lvl.values()]
    bad = [n for n in names if not stages.NAME_RE.match(n) or not n.split("_")[-1].startswith("LOD")]
    chk.add("G06", "BLOCKER", not bad, bad[:6] or f"{len(names)} game objects named *_LOD<n>")
    game_objs = list(levels[0].values())
    _uv_checks(game_objs, "UVMap")(chk, metrics)
    hy = validate.hygiene(game_objs)
    validate.hygiene_checks(chk, hy, blocker=True)
    metrics["hygiene"] = hy["total"]
    moved = []
    for b, fn in pivots.items():
        ob = levels[0].get(b)
        if ob is None:
            moved.append(f"{b}: missing")
            continue
        d = (ob.matrix_world.translation - Vector(fn())).length
        par = ob.parent.name if ob.parent else None
        want = levels[0][children[b]].name if b in children and children[b] in levels[0] else root.name
        if d > 1e-4 or par != want:
            moved.append(f"{b}: pivot off {d * 1000:.2f} mm, parent {par} (want {want})")
    if pivots:
        chk.add("M01", "BLOCKER", not moved, moved or f"{len(pivots)} moving parts on their pivots, parented")
    st = validate.stats(game_objs)
    metrics.update(objects=st["objects"], tris=ltris[0], dims=[round(d, 4) for d in st["dims"]],
                   files={n: os.path.relpath(p, paths.ROOT) for n, p in files.items()}, engine=G["engine"])
    write_stage(ctx, 4, chk, metrics)
    n_obj = 1 + len(levels[0]) + len(cols)
    ok, detail = export.roundtrip(files[0], n_obj, 1 if tex else len(st["materials_used"]))
    _append_check(ctx, 4, "U15", "BLOCKER", ok, "LOD0 glb: " + detail)
    return load_report(ctx)["stages"]["4"]["summary"]["result"]


def _review_game(ctx, levels, hp):
    """EEVEE renders of every LOD with the baked material + the S3 DETAIL mesh from the same cameras:
    work/s4/s4_<view>_lod<n>.png and s4_<view>_s3.png. LOOK at them - the gates cannot see bake
    artefacts on visible faces."""
    work = ctx.work(4)
    objs0 = list(levels[0].values())
    mn, mx = cameras.world_bounds(objs0)
    c, size = (mn + mx) / 2, (mx - mn).length
    cams = {"persp": cameras.rig_from_bounds(objs0)["CAM_PERSPECTIVE"]}
    close = cameras.make("CAM_S4_CLOSE", c + Vector((-0.28, -0.22, 0.10)) * size, (0, 0, 0), lens=60)
    cams["close"] = cameras.look_at(close, c + Vector((0.0, 0.08, 0.02)) * size)
    render.studio_lights(tuple(c), size)
    scene.set_collection_visible(stages.STAGES[3]["coll"], True)
    shots = [(f"lod{n}", list(lvl.values())) for n, lvl in levels.items()] + [("s3", hp)]
    for view, cam in cams.items():
        for tag, objs in shots:
            with render.only(objs):
                render.beauty(cam, os.path.join(work, f"s4_{view}_{tag}.png"), (1280, 720), 32)
    scene.set_collection_visible(stages.STAGES[3]["coll"], False)
    log(4, "review renders ->", os.path.relpath(work, paths.ROOT))


RUN = {1: stage1, 2: stage2, 3: stage3, 4: stage4}


def main(build_file):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ctx = Ctx(build_file, argv)
    todo = stages.parse_stage_args(argv, getattr(ctx.PT, "STAGES", (1, 2, 3, 4)))
    print(f"[PIPELINE] {ctx.A}: stages {todo}  inputs {ctx.hash}", flush=True)
    for s in todo:
        t0 = time.time()
        res = RUN[s](ctx)
        log(s, f"{stages.STAGES[s]['key']} -> {res}  ({time.time() - t0:.0f}s)")
        if res != "PASS" and not ctx.force:
            log(s, "stopping: fix the failed blockers (python wb.py gate %s) or rerun with --force" % ctx.A)
            break
