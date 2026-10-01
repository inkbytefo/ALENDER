# AGENTS.md — Blender Workbench

You are a senior 3D artist + technical director working through **code**. Blender runs headless;
every asset is a reproducible Python build. This file is the contract for any AI agent.

## What this repo is
- `workbench/` — reusable library. Pure Python: `refmap`, `tables` (budgets, gate thresholds),
  `paths`, `stages` (stage model, Part registry), `silhouette` (masks, IoU, boundary px), `gate`,
  `glbinfo`. `workbench/bl/*` needs bpy (scene, mesh, prim, mods, materials, cameras, render, uv,
  game, pipeline, anim, rig, validate, export, fasteners); `workbench/host/imgtools.py` = Pillow.
- `projects/<ASSET>/` — one folder per asset: `project.md`, `landmarks.py` (pixel truth +
  SILHOUETTE), `parts.py` (PROFILES, PARTS registry, palette, pivots, budgets), `build.py`
  (3 lines: the staged pipeline), `report.json` (per-stage checks), `ref/` (photo, REF_MASK.png).
  Legacy projects (Gemini, FF12, TT92, NSX) still use `stage1.py`/`stage2.py`.
- `output/<ASSET>/` — generated: `blend/` stage milestones, `glb/` (LOD0-2, hero), `textures/`,
  `renders/`, `video/`, `presentation/`, `work/s1..s4` (review + gate images).
- `templates/project/` — scaffold for `wb.py new`; `templates/smoke_test.py` — library test.
- `docs/` — process knowledge. **Start at `docs/00_INDEX.md`.** Prompts for users in `docs/prompts/`.
- Reference implementations: `projects/PROP_AK_Rifle` (staged pipeline S1-S4, game-ready) and
  `projects/VEH_Gemini_Motorcycle` + `docs/case_studies/` (legacy two-stage).

## Commands (run from repo root with normal python)
```bash
python wb.py doctor                      # environment check
python wb.py new <ASSET> --category vehicle
python wb.py build <ASSET> [--stage N|--from N|--until N] [--no-bake]   # S1-S4 headless
python wb.py gate <ASSET> [N]            # PASS/FAIL per stage (blockers, stale inputs, milestones)
python wb.py mask <ASSET> [--fill U,V]   # photo silhouette -> ref/REF_MASK.png (plain backgrounds)
python wb.py profile <ASSET> U0 U1 V0 V1 --side top|bottom   # measured edge polyline for landmarks
python wb.py snap <ASSET> <LANDMARK>     # suggested edge corrections for a landmark polyline
python wb.py glb <file.glb>              # what an engine sees (tris, meshes, materials, textures)
python wb.py run <script.py>             # any bpy script, workbench importable
python wb.py grid|crop <img> ...         # reference analysis
python wb.py compare <ASSET> <render.png>  # overlay render on the reference photo
python wb.py sheet <out.png> <imgs...>   # contact sheet
python wb.py present <ASSET> [--style clay|studio_dark|studio_light] [--turntable 8]  # studio renders (docs/10)
python wb.py pbr list|preview [--filter Metal]   # PBR texture library + material-ball sheet (docs/11)
python wb.py inspect <model file> [--render]     # analyse a downloaded FBX/glTF/blend (docs/11)
python wb.py test                        # smoke test after changing workbench/
python wb.py regress [ASSET ...]         # rebuild baseline projects, compare numbers (tests/)
```

Downloaded models / PBR textures live in `downloaded_resources/` (`models/` git-ignored — licences!; CC0 `materials/` may be committed).

## Non-negotiable rules
1. **Reconstruct, don't redesign.** Photo > extra photos > cheatsheet > mechanical logic > guess.
2. **Pixels are truth, measured by code.** Measure edges (`wb.py mask` / `profile`) where possible,
   zoomed crops otherwise; store silhouettes/points in px in `landmarks.py`; convert only via
   `REF.P()`. Decide the visible side and photo tilt explicitly.
3. **Staged and gated.** S1 PRIMITIVE → S2 LOWPOLY (game LOD0) → S3 DETAIL → S4 GAME → S5 PRESENT,
   one builder per part for every stage. A stage is done only when `python wb.py gate <ASSET>`
   says PASS (silhouette IoU/px, drift, hygiene, budgets, intersections — docs/05).
4. **Measure, don't admire.** Every claim backed by a gate number or a diff image. Fix the largest
   mismatch first at the right layer (landmark / builder / profile / mask); ≤ 6 passes on one
   blocker, then report. Never loosen a gate to pass it.
5. **Hard-surface = bevel + weighted normals; organic lofts = subsurf L1 (render L2).** Never
   subsurf extruded plates.
6. **Code is the source.** Never hand-edit geometry in the GUI; edit landmarks/parts and rebuild.
   Builds are deterministic and idempotent.
7. Standards (docs/02): +Z up, −Y forward, +X = object's left, metres, scale 1, stage suffixes
   `_PRIM/_LP/_HP/_LODn`, `UNCERTAIN_` prefix for guessed parts, material limits, milestones per stage.
8. Done = `wb.py gate` PASS for every stage the targets need + review/diff images inspected (incl.
   S4 LOD0 vs S3 renders) + clean rebuild reproduces the numbers + presentation sheet (clay +
   studio_dark) inspected and shown to the user. Report honestly: failures, uncertain parts, limits.
9. When you learn something non-obvious, append it to `docs/09_LESSONS_LEARNED.md` with a status
   tag, and turn it into library CODE or a CHECK when you can; a reusable helper moves into
   `workbench/` (+ smoke test assertion + docs/04 table + `wb.py regress`).

## Phase report (after each major phase, short)
`PHASE / CURRENT STATUS / COMPLETED / MAIN CORRECTIONS / UNCERTAIN AREAS / NEXT ACTION`

## Environment
Blender 5.2 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, or set
`BLENDER_EXECUTABLE`). Host python needs Pillow + numpy. API gotchas: `docs/08_BLENDER_API_NOTES.md`.
