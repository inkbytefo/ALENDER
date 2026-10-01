---
name: blender-workbench
description: Reference-driven 3D modelling, animation and rendering with headless Blender in this repository (vehicles, motorcycles, cars, buildings, characters, props, game-ready assets, turntables, videos). Use whenever the user asks to model, rebuild, refine, animate, render or export a 3D asset here, gives a photo/cheatsheet of an object to reconstruct, or asks to continue/fix an existing project under projects/.
---

# Blender Workbench skill — the single entry point

You write code; the workbench measures. **A stage is done when `python wb.py gate <A>` says
PASS**, not when a render looks right. Read docs only when a step below points to them.
Create one todo per stage for non-trivial assets.

## 0. Orient (2 min)
- `python wb.py doctor`; `python wb.py list` (legacy projects show no stage column).
- Existing project: `python wb.py gate <A>` → read the failed blockers and the worst zones in
  `projects/<A>/report.json`, then the `output/<A>/work/s*/s*_R0*_diff.png` images.
- Skim the lesson index table in `docs/09_LESSONS_LEARNED.md` (JUDGEMENT lessons of your category).

## S0 Intake → `landmarks.py` (docs/03)
- `python wb.py new <A> --category <c> [--budget key]`; photo → `projects/<A>/ref/REAL_REFERENCE.png`.
  Fill `project.md` (targets game/render/print, engine, budget).
- Side, scale (+2 cross-checks), tilt, anchor → RefMap.
- **Measure edges**: plain background → `wb.py mask <A>` (LOOK at `work/ref_mask_check.png`, add
  `--fill U,V` for glare) → `wb.py profile <A> U0 U1 V0 V1 --side top|bottom` per edge. Otherwise
  zoom crops (`wb.py crop`) + `wb.py snap` as a second opinion. Fit arcs by least squares.
- `SILHOUETTE` = closed px polygons of every visible part. Widths as tables, guessed → UNCERTAIN.

## S1 PRIMITIVE → S2 LOWPOLY → S3 DETAIL (`parts.py`, docs/01 + docs/04)
- `PROFILES {1,2,3}`, one `Part(key, builder, prim=..., collision=...)` per group, `nm(P, name)`.
- S1 prim builders (`workbench.bl.prim`): masses only. S2: real builders, no bevels (game LOD0).
  S3: same builders + bevel/WN on hard parts, subsurf on lofts, fasteners, ribs, details.
- `PIVOTS` / `CHILDREN` for moving parts, `CRITICAL_PAIRS`, `TARGET_DIMS`, `GROUND`.
- Loop per stage: `python wb.py build <A> --until N` (fast, no bake) → `wb.py gate <A>` →
  view the diff images → fix the **layer** (landmark? builder? profile? mask?) → rebuild.
  R01 PASS + R02 FAIL ⇒ a landmark is wrong: measure it. Never loosen a gate to pass.
- Filter long output: `python wb.py build <A> 2>&1 | grep "STAGE\|FAIL\|Traceback\|Error"`.

## S4 GAME (docs/12)
- `GAME = dict(engine=..., bake=True, lod=(0.5, 0.25))`; `python wb.py build <A> --stage 4`.
- LOOK at `work/s4/s4_persp_lod0.png` vs `s4_persp_s3.png` and the close-ups (bake artefacts
  on visible faces are not gated), the textures in `output/<A>/textures/`.
- `python wb.py glb output/<A>/glb/<A>_LOD0.glb` (engine view); `wb.py engine-check` if Godot exists.

## S5 PRESENT + deliver (docs/10)
- `python wb.py present <A> --style clay --samples 96` → view the sheet; `python wb.py present <A>`
  (studio_dark) → view; show both to the user.
- Clean rebuild `python wb.py build <A>` → same numbers; `wb.py gate <A>` PASS.
- Final message (Turkish to the user): gate result per stage, key numbers (R01/R02 IoU + p95, tris
  per stage/LOD, bake), what changed, uncertain parts, limitations, file paths.

## After changing `workbench/`
`python wb.py test` (smoke, ~1 min) and `python wb.py regress` (rebuilds baseline projects,
compares numbers). New lesson → `docs/09` with a status tag; turn it into CODE or a CHECK if you can.

## Animation / video
`docs/07`: pivots → `anim.*` keys (named actions) → `render.animation()` MP4 → `output/<A>/video/`.
