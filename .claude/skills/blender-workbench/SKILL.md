---
name: blender-workbench
description: Reference-driven 3D modelling, animation and rendering with headless Blender in this repository (vehicles, motorcycles, cars, buildings, characters, props, turntables, videos). Use whenever the user asks to model, rebuild, refine, animate, render or export a 3D asset here, gives a photo/cheatsheet of an object to reconstruct, or asks to continue/fix an existing project under projects/.
---

# Blender Workbench skill

Checklist form of `docs/01_WORKFLOW.md`. Read `AGENTS.md` once per session, then work the list.
Create a todo per numbered step for non-trivial assets.

## 0. Orient (2 min)
- `python wb.py doctor`; `python wb.py list`.
- Skim `docs/09_LESSONS_LEARNED.md` (always) and the category section of `docs/06_CATEGORIES.md`.
- Existing project? Read its `project.md`, `report.json`, latest `output/<A>/work/*` overlays first.

## 1. Intake
- `python wb.py new <ASSET> --category <c>`; photos → `projects/<A>/ref/REAL_REFERENCE.png`
  (+ `MODELING_CHEATSHEET.png`), convert webp→png. Fill `project.md`.

## 2. Reference analysis → `landmarks.py` (docs/03)
- `wb.py grid` + `wb.py crop` every region at 3–4×; **view the crops** and read pixel edges.
- Visible side (front right ⇒ right side ⇒ camera −X). Scale from known size + 2 cross-checks.
  Tilt via `pitch_from_two_points`. RefMap anchor. Silhouettes/points in px. Widths as tables.
- Sanity-print a few `REF.P()` values on the host (length, height, known points).

## 3. Stage 1 LOW (`stage1.py`, `parts.py` with `LOW`)
- Setup: reset, collections, palette, `reference_camera` (error < 2 px), rig, guides → `_00_SETUP`.
- Global proportions only → `_01_GLOBAL_BLOCKOUT` → overlay (`wb.py compare`) → must match.
- All primary/secondary masses → review renders → overlay + orthos → fix top mismatches.
- `validate.intersections(CRITICAL_PAIRS)` → 0 hits. Save `_02_COMPLETE_LOW`. Phase report.

## 4. Stage 2 HIGH (`stage2.py`, same builders with `HIGH`)
- Primary → `_03_HIGH_PRIMARY`; mechanical → `_04_HIGH_MECHANICAL`; details (instanced
  fasteners, fins, holes, lines) → `_05_FINAL_GEOMETRY`.
- Hard parts: `finish_hard` (bevel+WN). Organic lofts: `finish_organic` (subsurf L1/L2).
- Origins: pivots for moving parts, bbox centre otherwise; parent all to the asset root.

## 5. Validate & deliver (docs/05)
- `validate.stats` (check `top_tris`), `standard_checks` + category checks + intersections,
  renders (ref cam clay/material, orthos, perspectives, wire), `export.glb` + `roundtrip`,
  `write_report`. View the final overlay + review sheet yourself.
- Clean rebuild `python wb.py build <A>` → same numbers. Remove stale outputs.
- Final message: result, key numbers, what changed, uncertain parts, limitations, file paths.
- New lesson? Append to `docs/09_LESSONS_LEARNED.md`. Reusable helper? Promote to `workbench/`,
  add a smoke-test assertion, `python wb.py test`.

## Animation / video
`docs/07`: pivots → `anim.*` keys (named actions, linear for mechanics) → `render.animation()` MP4
(Workbench preview, EEVEE final) → `output/<A>/video/`.
