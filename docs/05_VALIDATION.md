# 05 — Validation: numbers and overlays, not opinions

"Looks good" is not evidence. Every gate is a render you inspected **and** numbers you printed.

## 1. Reference overlay (the most important check)
```python
render.workbench(ref_cam, WORK + "/p9_ref_clay.png", "CLAY", transparent=True)
```
```bash
python wb.py compare <ASSET> output/<ASSET>/work/stage1/p9_ref_clay.png
```
→ `compare_*_edge.png` (cyan model silhouette on the photo, magenta = `landmarks.MARKS`) and
`compare_*_blend.png` (55 % mix). Read it zone by zone; write mismatches as numbers:
"tail top 8 px too low", "fork 3° too steep", not "tail looks off".
Also compose side-by-side material views: `python wb.py sheet out.png ref.png render.png`.

## 2. Orthographic sanity
Render `review_set(cams)`; check front/rear/top for symmetry, width hierarchy (bars > engine >
tank > seat > tail for a bike), impossible depths, floating parts.

## 3. Intersections (automatic, world space)
`validate.intersections(CRITICAL_PAIRS, objs)` with name-prefix pairs that must never touch
(exhaust↔frame, tyre↔swingarm, fork↔tank, engine↔frame, wall↔window glass, limb↔torso…).
Stage 1 gate requires 0 hits. Real hits it found on the case study: gearbox through pivot plates,
intakes through frame rails, downtube through a header, pivot shaft through gearbox.
BVHs must be built in WORLD space (library does it) — local-space trees give false positives
once objects have their own origins.

## 4. Universal checks (`validate.standard_checks`)
| ID | Check | Level |
|----|-------|-------|
| U01 | bbox matches target dims ±2 % | BLOCKER |
| U02 | all scales 1.0 | BLOCKER |
| U03 | lowest point on Z = 0 (±2 mm) | BLOCKER |
| U06 | every mesh has UVs | BLOCKER |
| U07 | no empty material slots | BLOCKER |
| U08 | evaluated tris ≤ max | BLOCKER |
| U09 | tris within target | WARN |
| U10 | material count ≤ limit | WARN |
| U15 | GLB re-import: object + material counts equal | BLOCKER |
| cat. | category checks: wheelbase, rake, door size, height, symmetry (`validate.symmetry_error`) | BLOCKER/WARN |
| X | 0 critical intersections | BLOCKER |

## 5. report.json
`validate.write_report(path, asset, chk, metrics, **extra)` writes summary (PASS/FAIL, counts),
metrics, checks, plus your `assumptions`, `uncertain`, `outputs`, `waivers`, `known_limitations`.
FAIL ⇒ do not call the task done; report the blocker and the proposed fix.

## 6. Iteration rule
Fix the largest visible mismatch first (or several unrelated ones per pass), re-render, compare.
Same blocker twice in a row ⇒ stop and find the layer: landmark wrong? builder bug? API change?
render setting? Write a diagnostic print before changing anything. Max 6 passes, then report.

## 7. Before saying "done"
- clean rebuild from scratch (`python wb.py build <ASSET>`) gives the same numbers (determinism)
- renders exist and were looked at; report PASS; stale outputs from earlier attempts archived
