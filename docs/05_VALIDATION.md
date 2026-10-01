# 05 — Validation: numbers the agent cannot argue with

"Looks good" is not evidence. Every stage writes its checks into `report.json`
(`stages.<N>.checks`) and `python wb.py gate <ASSET> [N]` turns them into PASS/FAIL (exit code).
A stage passes only if all its BLOCKERs pass, it was built from the **current** inputs (hash of the
project's `*.py`) and its milestone exists. Edit a landmark → every stage is STALE until rebuilt.

## 1. Reference silhouette (the most important check) — R01 / R02 / R03
The pipeline renders the stage from `CAM_REFERENCE` (alpha only, photo size) and compares masks
(`workbench.silhouette.metrics`): **IoU** and the symmetric **boundary distance** (mean / p95 / max
px) plus the worst grid zones with direction (`model too large +7px @u728-904 v310-412`).

| ID | reference mask | S1 | S2 | S3 |
|----|----------------|----|----|----|
| R01 | union of `landmarks.SILHOUETTE` polygons (closing 3 px: adjacent outlines never meet exactly) | IoU ≥ .85, p95 ≤ 14 | ≥ .92, ≤ 6 | ≥ .92, ≤ 6 |
| R02 | `ref/REF_MASK.png` (photo truth, `wb.py mask`) | ≥ .85, ≤ 14 | ≥ .92, ≤ 8 | ≥ .93, ≤ 6 |
| R03 | `landmarks.PART_OUTLINES` per part (WARN) | same as R01 | | |

Thresholds live in `workbench/tables.py` (`SILHOUETTE_GATES`, `PHOTO_GATES`, calibrated on
PROP_AK_Rifle). Output images: `work/s<N>/s<N>_R0x_*_diff.png` — grey = both, **red = photo only
(model missing)**, **blue = model only (extra)**, yellow = reference edge. R01 tests how well the
builders realise the landmarks; R02 tests the landmarks themselves against the photo. R01 PASS +
R02 FAIL ⇒ a landmark is wrong → measure it (`wb.py profile`), don't nudge geometry.

Host-side the same numbers: `python wb.py compare <ASSET> <render.png>` (overlay + edge images).

## 2. Stage drift — D01 / D02
D01: silhouette of stage N vs stage N−1 (S2 vs S1: IoU ≥ .80, p95 ≤ 16; S3 vs S2: ≥ .95, ≤ 4).
D02: bbox change on the main axes (axes ≥ 25 % of the longest; thin axes are dominated by
handles/mirrors a primitive may omit): S2 ≤ 4 %, S3 ≤ 1.5 %.

## 3. Intersections — X01
`validate.intersections(CRITICAL_PAIRS, objs)` with name-prefix pairs that must never touch
(exhaust↔frame, tyre↔swingarm, magazine↔grip, wall↔window glass …). Stage suffixes are stripped,
so the same pairs work at every stage. World-space BVHs (lesson 9). 0 hits at every stage.

## 4. Universal checks — U01–U16
| ID | Check | S1 | S2 | S3 | S4 |
|----|-------|----|----|----|----|
| U01 | bbox matches `TARGET_DIMS` (±3 % S1, ±2 % later) | B | B | B | |
| U02 | all scales 1.0 | B | B | B | |
| U03 | lowest point Z = 0 ±2 mm (`GROUND = False` for hand-held props) | B | B | B | |
| U04 | 0 non-manifold edges (open edges reported) | W | B | B | B |
| U05 | 0 flipped (inconsistent winding) / inverted (negative volume) | W | B | B | B |
| U06 | every mesh has UVs | | B | B | |
| U07 | no empty material slots | B | B | B | |
| U08 | tris ≤ stage max (`tables.BUDGETS[CATEGORY]`) | B | B | B | |
| U09 | tris within LOD0 target range | | W | | |
| U10 | materials ≤ category limit | B | B | B | |
| U11 | 0 loose verts / edges | W | B | B | B |
| U12 | n-gon ratio ≤ 5 % | W | W | W | W |
| U13 | bake UVs: overlap ≤ 0.5 %, outside 0-1 ≤ 0.1 % | | B | | B |
| U14 | texel density spread ≤ 2.5 | | W | | W |
| U15 | glb round trip: object + material counts equal | | | B | B |
| U16 | 0 degenerate faces / edges (zero-area bevel collapses are WARN on the S3 bake source) | W | B | W | B |

## 5. Policy, game, mechanics, print
| ID | Check | Level |
|----|-------|-------|
| N01 | names `GROUP_Part…` + stage suffix, no `.001`/spaces | BLOCKER |
| H01 | no Subdivision on hard-surface builders (plate, box, extrude — tagged `wb_builder`) | BLOCKER |
| M01 | moving parts: origin on `PIVOTS` point (<0.1 mm), parent per `CHILDREN` | BLOCKER (S4) |
| G01 | LOD tris ≤ ratio × LOD0 + 20 % | BLOCKER |
| G02 | a collider for every Part with `collision != "none"`, ≤ 255 faces each | BLOCKER |
| G03 | baked textures exist at the budget size; tangent normal mean ≈ (0.5, 0.5, >0.7) | BLOCKER |
| G04 | LOD0 glb ≤ `glb_mb` | BLOCKER |
| G05 | glb as the engine sees it (`workbench.glbinfo`): tris, 1 material, 3 images | BLOCKER |
| G06 | game objects named `*_LOD<n>` | BLOCKER |
| P01/P02 | watertight / min wall thickness (`validate.print_checks`, print targets only) | BLOCKER |

Per-project severity overrides: `parts.GATES = {"R03": "BLOCKER"}` — never to hide a failure;
record the reason in project.md.

## 6. report.json
```
summary: result PASS|FAIL, stages {1: PASS, 2: PASS, ...}, blockers_failed
stages.<N>: stage, summary, inputs_hash, time, metrics (tris, dims, hygiene, R01/R02/D01 with zones,
            uv, bake, lod_tris, glb ...), checks [...]
metrics: tris_s1, tris_low (S2), tris_high (S3), dims, game (LOD tris)
uncertain, licence ... (from parts.py)
```

## 7. Iteration rule
Fix the largest mismatch first (the worst zone), rebuild the stage, re-gate. Same blocker twice
⇒ find the layer (landmark? builder bug? profile? mask? API?) with a probe before changing code.
Max 6 passes, then report.

## 8. Before saying "done"
- `python wb.py gate <ASSET>` PASS for every stage the targets need
- review renders LOOKED at: `work/s*/s*_R0*_diff.png`, orthos, `work/s4/s4_*_lod0.png` vs `_s3.png`
- clean rebuild (`python wb.py build <ASSET>`) reproduces the numbers; `wb.py regress` if the
  library changed
- presentation sheets (clay + studio_dark) inspected and shown to the user
