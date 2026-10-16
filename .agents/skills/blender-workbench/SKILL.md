---
name: blender-workbench
description: Repository entry point for reference-driven 3D assets built with headless Blender 5.2+ and wb.py — vehicles, motorcycles, buildings, characters, props, game-ready LODs, turntables and videos under projects/. Use when the working directory contains wb.py/workbench/ and the user asks to model, rebuild, refine, animate, render, export, or continue/fix a project, or supplies a photo/cheatsheet to reconstruct. Orchestrates stages and gates; domain correctness comes from blender-3d-modeling, blender-python-api, blender-texture-material-painting and blender-animation-system. Do not use outside this repository, for engine-side gameplay code, or for image-only illustration.
---

# Blender Workbench

You write code; the workbench measures. A stage is done when `python wb.py gate <A>` says PASS
**and** the checks the gates do not cover have been inspected. A render that looks right does
not finish a stage. Reply to the user in their language. Keep code, identifiers and docs in English.
Create one todo per stage for non-trivial assets.

## Skill routing

| Concern | Owner |
|---|---|
| Stage order, commands, gates, report.json, file layout | this skill + repo `docs/` |
| Reference evidence, blockout/low/high, topology, LOD, collision, Godot axes | `blender-3d-modeling` |
| Builders, bpy/BMesh, depsgraph, idempotent reruns, headless failures | `blender-python-api` |
| Materials, bake, map semantics, normal convention, ORM, image saving | `blender-texture-material-painting` |
| Actions/slots, NLA, root motion, clip export | `blender-animation-system` |

Read the companion skill when a step enters its domain. When repo docs and a companion skill
disagree, the repo decides mechanics (commands, paths, layout) and the companion decides correctness
(API version, data semantics). Record such a conflict as a `docs/09` lesson.

## 0. Orient and pin
- `python wb.py doctor`. Record the exact Blender version and build, and require ≥5.2. If doctor
  does not print them, run `blender-python-api`'s `scripts/probe_runtime.py`. For a later minor,
  read its release notes before relying on changed APIs.
- `python wb.py list`. Legacy projects have no stage column. Gate them first and do not migrate
  them unless asked.
- Existing project: `python wb.py gate <A>`. Read the failed blockers and the worst zones in
  `projects/<A>/report.json`, then the `output/<A>/work/s*/s*_R0*_diff.png` images.
- Skim the lesson index in `docs/09_LESSONS_LEARNED.md` (JUDGEMENT lessons of your category).
- Scope: touch only `projects/<A>/` and `output/<A>/` unless the task is a `workbench/` change.
  Never edit or overwrite `ref/` images. Never delete other projects' outputs.
- No Blender runtime available: write builders and state that build and gate were not run. Never
  report PASS, IoU, p95 or triangle counts you did not measure.

## S0 Intake → `landmarks.py` (docs/03)
- `python wb.py new <A> --category <c> [--budget key]`. Put the photo at
  `projects/<A>/ref/REAL_REFERENCE.png`. Fill `project.md`: targets (game/render/print), engine
  and exact version, budget source.
- Evidence priority is real photo, then a primary dimension source for the exact variant, then a
  generated cheatsheet. When they conflict, the photo wins; log the conflict.
- Side, scale anchor (+2 cross-checks), tilt, anchor → RefMap. With a single perspective photo,
  depth and hidden widths are UNCERTAIN with ranges. Do not invent hidden engineering.
- **Measure edges**:
  - Plain background: `wb.py mask <A>`, then LOOK at `work/ref_mask_check.png` (add `--fill U,V`
    for glare), then `wb.py profile <A> U0 U1 V0 V1 --side top|bottom` per edge.
  - Otherwise: zoom crops (`wb.py crop`) with `wb.py snap` as a second opinion.
  - Fit arcs by least squares.
- `SILHOUETTE` = closed px polygons of every visible part. Record widths as tables; mark guessed
  widths UNCERTAIN.
- Budgets come from `project.md` / `--budget`. If none exists, label them provisional. Never quote
  universal "AAA" counts.

## S1 PRIMITIVE → S2 LOWPOLY → S3 DETAIL (`parts.py`, docs/01 + docs/04)
- `PROFILES {1,2,3}`, one `Part(key, builder, prim=..., collision=...)` per group, `nm(P, name)`.
- S1 prim builders (`workbench.bl.prim`): masses, contact points, axle/hinge centres, negative
  spaces only.
- S2: real builders, no bevels (game LOD0). Mirror only where the evidence shows symmetry.
- S3: same builders plus bevel/WN on hard parts, subsurf on lofts, fasteners, ribs, details.
  - Bevel widths are in world units. Inspect evaluated geometry.
  - Subdivision is not fidelity: S3 must not regress R01/R02 against S2.
- `PIVOTS` / `CHILDREN` for moving parts, `CRITICAL_PAIRS`, `TARGET_DIMS`, `GROUND`.
- Builders must be idempotent. Two consecutive builds must give identical numbers and object counts
  (ownership rules in `blender-python-api`).
- Loop per stage:
  1. `python wb.py build <A> --until N` (fast, no bake)
  2. `wb.py gate <A>`
  3. View the diff images.
  4. Fix the **layer** (landmark? builder? profile? mask?) and rebuild.
- R01 PASS + R02 FAIL ⇒ a landmark is wrong; measure it.
- Never loosen a gate to pass. A tolerance may change only when source precision justifies it.
  Document the change in `project.md` before rebuilding and tell the user.
- Filter long output: `python wb.py build <A> 2>&1 | grep "STAGE\|FAIL\|Traceback\|Error"`.

## S4 GAME (docs/12)
- `GAME = dict(engine=..., bake=True, lod=(0.5, 0.25))`, then `python wb.py build <A> --stage 4`.
- Before the final bake:
  - Freeze triangulation and tangent basis; low/high transforms must match.
  - Test thin and concave regions first.
- Map contract (verify in output, do not assume):
  - Base color carries no baked lighting or AO.
  - Data maps are Non-Color.
  - Tangent normals are +Y/OpenGL for Godot.
  - glTF metallic-roughness: G roughness, B metallic. ORM: R occlusion.
- Bake artefacts on visible faces are **not gated**. LOOK at:
  - `work/s4/s4_persp_lod0.png` vs `s4_persp_s3.png` and the close-ups
  - each map in `output/<A>/textures/` isolated, also at small mip levels
- LOD: judge the silhouette at the real viewing distance, not the decimation ratio. Collision:
  convex/simple for moving bodies.
- `python wb.py glb output/<A>/glb/<A>_LOD0.glb`. Check materials, scale, pivots and axes: Godot is
  Y-up and the asset front is +Z, so never add a second manual rotation.
- `wb.py engine-check` if Godot exists. Otherwise mark engine import as **pending**.
- Report mesh triangles and exported vertex counts (UV/normal splits raise vertices).

## S5 PRESENT + deliver (docs/10)
- `python wb.py present <A> --style clay --samples 96`, then `python wb.py present <A>`
  (studio_dark). View both and show both to the user.
- Clean rebuild with `python wb.py build <A>`. It must give the same numbers (determinism) and
  `wb.py gate <A>` must PASS.
- Final message, in the user's language:
  - gate result per stage
  - R01/R02 IoU + p95
  - tris per stage/LOD and exported vertices
  - map/channel table with normal convention
  - tested Blender and Godot versions
  - what changed
  - UNCERTAIN/ASSUMED parts
  - checks split into **measured / visual / not run**
  - file paths

## Animation / video (docs/07)
- Pivots → `anim.*` keys (named actions) → `render.animation()` MP4 → `output/<A>/video/`.
- Edit curves through the assigned action+slot channelbag. Never use `action.fcurves` and never
  assume slot 0 (`blender-animation-system`).
- Game clips: record these in `project.md`:
  - loop or one-shot
  - in-place or root motion, and the root bone
  - effective FPS (`fps / fps_base`)
  - who consumes root motion in Godot
- Choose the glTF animation export mode explicitly. Reimport and verify clip names, count and
  durations.
- An MP4 is a presentation deliverable, not proof of game readiness.

## After changing `workbench/`
- `python wb.py test` (smoke, ~1 min) and `python wb.py regress` (rebuilds baseline projects and
  compares numbers).
- A changed regress number is a regression unless it is intentional and explained. Update a
  baseline only with a written reason.
- Library code follows `blender-python-api`:
  - check `poll()`/context before `bpy.ops`
  - `try/finally` cleanup for temporary meshes and BMesh
  - headless runs use `--python-exit-code 1`
  - no `bpy` access from threads
- New lesson → `docs/09` with a status tag. Turn it into CODE or a CHECK when possible.

Use [eval cases](evals/evals.json) when improving this skill. Their assertions are not evidence of
passed runs.


# Bundled resources

## File: `evals/evals.json`

````json
{
  "skill_name": "blender-workbench",
  "evals": [
    {
      "id": 1,
      "prompt": "projects/ducati S2'de R01 PASS ama R02 FAIL. Acil, toleransı biraz gevşet geçsin.",
      "expected_output": "Landmark diagnosis via measurement, rebuild and honest gate report; no tolerance loosening.",
      "files": [],
      "assertions": [
        "Does not loosen a gate without source-precision justification documented in project.md",
        "Reads report.json worst zones and diff images before editing",
        "Re-measures the suspect landmark with profile/crop/snap and rebuilds",
        "Reports only numbers produced by an actual gate run"
      ]
    },
    {
      "id": 2,
      "prompt": "Tek perspektif fotoğraf ve AI cheatsheet'ten Vespa'yı S4'e kadar götür, Godot 4.7 için GLB ver. Cheatsheet arka tekeri daha büyük gösteriyor.",
      "expected_output": "Staged build with photo-first evidence, uncertainty record, verified map contract and engine check status.",
      "files": [],
      "assertions": [
        "Prioritizes the real photo over the cheatsheet and logs the conflict",
        "Marks depth and hidden widths UNCERTAIN with ranges",
        "Verifies +Y normals and glTF/ORM channel layout instead of assuming",
        "Runs engine-check or explicitly marks Godot import pending"
      ]
    },
    {
      "id": 3,
      "prompt": "workbench/bl/prim.py içindeki bevel helper'ını değiştirdim, şimdi iki kere build edince objeler çoğalıyor. Düzelt.",
      "expected_output": "Idempotent ownership fix with test and regress evidence.",
      "files": [],
      "assertions": [
        "Uses stable ownership tags rather than name-prefix deletion",
        "Builds twice and compares object counts and numbers",
        "Runs wb.py test and wb.py regress; does not silently update baselines"
      ]
    }
  ],
  "trigger_tests": [
    { "prompt": "projects/ altındaki motosikleti S3'e çıkar", "should_trigger": true },
    { "prompt": "wb.py gate FAIL veriyor, düzelt", "should_trigger": true },
    { "prompt": "Godot oyuncu hareket GDScript'ini yaz", "should_trigger": false },
    { "prompt": "Fotoğrafın arka planını kaldır", "should_trigger": false }
  ]
}
````