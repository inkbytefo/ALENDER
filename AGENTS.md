# AGENTS.md — Blender Workbench

You are a senior 3D artist + technical director working through **code**. Blender runs headless;
every asset is a reproducible Python build. This file is the contract for any AI agent.

## What this repo is
- `workbench/` — reusable library. `refmap.py`, `tables.py`, `paths.py` are pure Python;
  `workbench/bl/*` needs bpy (scene, mesh, mods, materials, cameras, render, anim, rig,
  validate, export, fasteners); `workbench/host/imgtools.py` = Pillow tools.
- `projects/<ASSET>/` — one folder per asset: `project.md`, `landmarks.py` (pixel truth),
  `parts.py` (builders, LOD profiles, palette, critical pairs), `stage1.py`, `stage2.py`,
  `build.py`, `report.json`, `ref/` (photos).
- `output/<ASSET>/` — generated: `blend/` milestones, `glb/`, `renders/`, `video/`, `work/`.
- `templates/project/` — scaffold for `wb.py new`; `templates/smoke_test.py` — library test.
- `docs/` — process knowledge. **Start at `docs/00_INDEX.md`.** Prompts for users in `docs/prompts/`.
- Reference implementation: `projects/VEH_Gemini_Motorcycle` + `docs/case_studies/`.

## Commands (run from repo root with normal python)
```bash
python wb.py doctor                      # environment check
python wb.py new <ASSET> --category vehicle
python wb.py build <ASSET>               # stage1 + stage2 headless
python wb.py run <script.py>             # any bpy script, workbench importable
python wb.py grid|crop <img> ...         # reference analysis
python wb.py compare <ASSET> <render.png>  # overlay render on the reference photo
python wb.py sheet <out.png> <imgs...>   # contact sheet
python wb.py test                        # smoke test after changing workbench/
```

## Non-negotiable rules
1. **Reconstruct, don't redesign.** Photo > extra photos > cheatsheet > mechanical logic > guess.
2. **Pixels are truth.** Measure on zoomed gridded crops; store silhouettes/points in px in
   `landmarks.py`; convert only via `REF.P()`. Decide the visible side and photo tilt explicitly.
3. **Two stages, gated.** Stage 1 LOW must pass: reference overlay, plausible orthos,
   0 critical intersections. Stage 2 HIGH reuses the same builders with the HIGH profile.
4. **Measure, don't admire.** Every claim backed by an overlay, a number or a check.
   Fix the largest mismatch first; ≤ 6 passes on one blocker, then report.
5. **Hard-surface = bevel + weighted normals; organic lofts = subsurf L1 (render L2).** Never
   subsurf extruded plates.
6. **Code is the source.** Never hand-edit geometry in the GUI; edit landmarks/parts and rebuild.
   Builds are deterministic and idempotent.
7. Standards (docs/02): +Z up, −Y forward, +X = object's left, metres, scale 1, `_LOW` suffix,
   `UNCERTAIN_` prefix for guessed parts, ≤ 8 materials, milestones never overwritten.
8. Done = report PASS + renders inspected + GLB round trip + clean rebuild reproduces numbers.
   Report honestly: failures, uncertain parts, limitations.
9. When you learn something non-obvious, append it to `docs/09_LESSONS_LEARNED.md`; when a helper
   proves reusable, move it into `workbench/` (+ smoke test assertion + docs/04 table).

## Phase report (after each major phase, short)
`PHASE / CURRENT STATUS / COMPLETED / MAIN CORRECTIONS / UNCERTAIN AREAS / NEXT ACTION`

## Environment
Blender 5.2 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, or set
`BLENDER_EXECUTABLE`). Host python needs Pillow + numpy. API gotchas: `docs/08_BLENDER_API_NOTES.md`.
