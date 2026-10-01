# 01 — Workflow: reference-driven, staged, gated by numbers

Goal: **reconstruction, not re-design.** The agent writes code; the workbench measures. A stage is
done when `python wb.py gate <ASSET>` says PASS — not when a render "looks right".

```
 S0 INTAKE ─► S1 PRIMITIVE ─► S2 LOWPOLY ─► S3 DETAIL ─► S4 GAME ─► S5 PRESENT
 landmarks     masses          LOD0 base     hero +       bake, LODs,   studio
 (px truth)    *_PRIM          *_LP + UVs    bake source  collision,    renders
                                             *_HP         export
      every stage: build ─► measure (report.json) ─► gate ─► fix largest mismatch ─► rebuild
```

One builder per part (`parts.PARTS`) reads `landmarks.py` at every stage; only the stage profile
changes. Proportions cannot drift between stages, and a landmark fix is a fix everywhere.

| Stage | Collection / suffix | Content | Gate (BLOCKERs, docs/05) |
|-------|---------------------|---------|--------------------------|
| S0 INTAKE | — | photos, scale, side, tilt, landmarks (px), `ref/REF_MASK.png`, project.md | — (agent checklist) |
| S1 PRIMITIVE | `10_S1_PRIMITIVE` `_PRIM` | boxes, cylinders, simplified outlines; pivots/hierarchy planned | R01/R02 silhouette (loose), U01 dims ±3 %, X01, N01, U08 |
| S2 LOWPOLY | `20_S2_LOWPOLY` `_LP` | real forms, clean topology, NO bevels, shared UV atlas = **game LOD0** | + R01/R02 strict, D01/D02 drift vs S1, U04/U05/U11/U16 hygiene, U06, U09, U13/U14 UVs |
| S3 DETAIL | `30_S3_DETAIL` `_HP` | bevels + weighted normals, subsurf on lofts, fasteners, ribs = **hero + bake source** | + H01 policy, D01/D02 drift vs S2 (tight), U15 hero glb |
| S4 GAME | `40_S4_GAME` `_LODn`, `41_S4_COLLISION` | bake S3→S2 (base/ORM/normal), LOD1-2, collision per part, glb/fbx | G01–G06, U13/U14, hygiene, M01 pivots, U15 |
| S5 PRESENT | studio | `python wb.py present <ASSET>` (clay + studio_dark) | sheets inspected by the agent |

## Commands
```bash
python wb.py new <ASSET> --category prop            # scaffold (staged template)
python wb.py mask <ASSET> [--fill U,V ...]          # S0: photo silhouette (plain background) -> LOOK at it
python wb.py profile <ASSET> U0 U1 V0 V1 --side top # S0: measure an edge instead of reading it
python wb.py build <ASSET>                          # all stages, stops at the first failed gate
python wb.py build <ASSET> --stage 2 | --from 3 | --until 2 [--no-bake] [--force]
python wb.py gate <ASSET> [N]                       # PASS/FAIL + failed blockers, exit code
python wb.py present <ASSET> --style clay           # S5
python wb.py regress                                # after touching workbench/
```

## S0 — Intake (no geometry)
- `wb.py new`, photos → `projects/<A>/ref/REAL_REFERENCE.png` (+ cheatsheet), fill `project.md`
  (targets: game / render / print, engine, budget key).
- Source priority: **photo > extra photos > cheatsheet > mechanical logic > conservative guess.**
- Side, scale (+2 cross-checks), tilt, RefMap anchor (docs/03).
- **Measure, don't read**: plain background → `wb.py mask` (check the magenta overlay!) then
  `wb.py profile` for every silhouette edge; otherwise zoom crops + `wb.py snap` as a second opinion.
  Record which landmarks are measured and which are eye-read in `project.md`.
- `landmarks.py`: px polylines, `SILHOUETTE` (union = reference for R01), widths as tables.

## S1 — Primitive
Masses only: every Part gets a `prim=` builder (`workbench.bl.prim`: `box_px`, `plate_px`,
`cyl_px`, `wheel_px`) or falls back to its real builder with the coarse S1 profile.
Plan pivots / hierarchy now (PIVOTS, CHILDREN). Gate R01 checks the landmark silhouette with
loose thresholds; a failing S1 means wrong landmarks or scale — fix those, not the geometry.

## S2 — Lowpoly (game LOD0)
The real builders with `PROFILES[2]`: enough segments for the silhouette, no bevels/rivets/ribs
(they are baked from S3). The pipeline unwraps one shared atlas (`UV_Bake` 0-1 + tiling `UVMap`).
This is the mesh that ships; hygiene failures here are BLOCKERs.

## S3 — Detail
Same builders with `PROFILES[3]`: hard-surface = bevel + weighted normals, organic lofts =
subsurf (L1 viewport/export, L2 render), fasteners, ribs, holes. Drift vs S2 must stay tiny
(D01 p95 ≤ 4 px) — details may not move silhouettes. Pivots + parenting set here (hero `.blend`).

## S4 — Game
Automatic (`parts.GAME`): evaluated LOD0 copies, pivots, bake S3→LOD0 atlas (Cycles, per map:
base, normal, AO, roughness, metallic → base / ORM / normal PNG), single glTF-ready material,
static parts merged into `<A>_Body_LODn`, moving parts separate, LOD1/LOD2 by collapse,
convex-hull/box collision per Part (engine naming), exports, structural glb check, round trip.
**Look at `work/s4/s4_*_lod0.png` vs `s4_*_s3.png`** — bake artefacts on visible faces are not gated.

## Correction loop (every stage)
```
build → gate → read the WORST zones in report.json (hint + px + box) and the *_diff.png
→ decide the layer: landmark wrong? builder bug? profile too coarse? mask wrong?
→ fix the largest mismatch (or 3-5 unrelated ones) → rebuild that stage → repeat
```
Priority: global proportion > silhouette > placement > curvature > thickness > detail.
Same blocker twice → write a diagnostic (probe script, `cluster` of errors) before changing code.
Max 6 passes on one blocker, then report. Never loosen a gate to pass it; if a threshold is
wrong for a category, change it in `workbench/tables.py` with a reason (and `wb.py regress`).

## Phase report (after each stage, short)
```
PHASE: / CURRENT STATUS (gate) / COMPLETED / MAIN CORRECTIONS (numbers) / UNCERTAIN AREAS / NEXT ACTION
```

## Autonomy
Proceed stage by stage without asking. Ask only when references contradict each other, a major
component is invisible *and* important, tooling fails, or an action would destroy work.

## Legacy projects
Projects with `stage1.py`/`stage2.py` (Gemini, FF12, TT92, NSX) still build with `wb.py build`
(two stages, LOW/HIGH collections); `wb.py gate` does not apply to them. Migrate a legacy project
when you next touch it: convert `LOW/HIGH` dicts to `PROFILES`, `build_all` to `PARTS`, `nm()` to
`stages.nm`, add `SILHOUETTE`, replace `stage1.py/stage2.py` by the 3-line `build.py`
(reference migration: `projects/PROP_AK_Rifle`).
