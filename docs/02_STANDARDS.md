# 02 — Standards

## Units, axes, origin
- 1 Blender unit = 1 m, metric scene (`scene.reset()` sets it).
- **+Z up, −Y forward, X = width, +X = the object's LEFT side.** Never change mid-project.
- glTF export converts to +Y up automatically (`export_yup=True`).
- Root: one empty named exactly like the asset at world origin, ground at Z = 0.
  Vehicles: root midway between axles. Buildings: ground-floor centre. Characters: between the feet.
- Object origins: rotating parts on their pivot (wheel → axle, door → hinge, steering → steering
  axis, bone-driven → joint); everything else at its bbox centre. Scale always (1,1,1).
- Hierarchy depth ≤ 3 (root → group → part). Cameras/lights are never exported.

## Folders
```
projects/<ASSET>/   project.md  landmarks.py  parts.py  stage1.py  stage2.py  build.py  report.json  ref/
output/<ASSET>/     blend/<ASSET>_00_SETUP … _05_FINAL_GEOMETRY.blend, <ASSET>.blend
                    glb/<ASSET>.glb   renders/   video/   work/stage1|stage2 (review images)
```
Milestones: `00_SETUP, 01_GLOBAL_BLOCKOUT, 02_COMPLETE_LOW, STAGE_01_LOW, 03_HIGH_PRIMARY,
04_HIGH_MECHANICAL, 05_FINAL_GEOMETRY` via `paths.milestone(asset, tag)`. Never overwrite the only
good state — milestones are separate files.

## Collections
`00_REFERENCE 01_GUIDES 02_LOW_PRIMARY 03_LOW_SECONDARY 04_LOW_MECHANICAL 05_HIGH_BODY
06_HIGH_MECHANICAL 07_DETAILS 08_TEMP 09_PRESENTATION` (`scene.setup_collections()`).

## Naming
- Assets: `VEH_ ENV_ ARCH_ CHR_ PROP_ ANIM_` + PascalCase (`VEH_Gemini_Motorcycle`).
- Parts: `GROUP_Part[_Detail][_L|_R|_FL|_RR]` — e.g. `BODY_Tank`, `FRAME_Swingarm_L`,
  `ENGINE_Cover_Main_R`, `WHEEL_Front_Tire`, `CTRL_Grip_L`, `ARCH_Wall_North`, `CHR_Body`.
- Stage 1 objects: `_LOW` suffix. Guessed / hidden geometry: `UNCERTAIN_` prefix.
- Fasteners: `FASTENER_<FAMILY>_###` sharing meshes `BOLT_M6/M8/M10`, `NUT`, `WASHER`.
- Materials: `MAT_<PURPOSE>` (`MAT_BODY_RED`, `MAT_RUBBER`). Guides: `GUIDE_*`. Temp: `TEMP_*`.
- No `Cube.001`, no spaces.

## Budgets (triangles, evaluated = modifiers applied)
| Asset | Stage 1 LOW | Stage 2 HIGH target | max |
|-------|-------------|---------------------|-----|
| hero vehicle (car/moto) | 5k–15k | 40k–100k | 150k |
| background vehicle | 2k–5k | 8k–20k | 30k |
| building exterior | 2k–10k | 15k–60k | 100k |
| modular wall/floor piece | <1k | 2k–8k | 15k |
| character | 2k–6k | 15k–40k | 60k |
| small / large prop | <1k / <3k | 0.5k–2.5k / 3k–10k | 5k / 25k |
Subsurf: viewport/export level 1, render level 2 — keeps GLB inside budget.

## Materials
- Principled BSDF only, values not procedural nodes (glTF-safe). Palette in `parts.PALETTE`,
  presets in `workbench.bl.materials.PRESETS`, or image-based PBR sets via
  `dict(pbr="Leather037", tile_m=0.35)` (docs/11; UV projection, no tint/bump for game assets).
- ≤ 8 per vehicle, ≤ 6 per character, ≤ 4 per prop. No empty slots, no unused materials.
- Metallic binary: metals ≥ 0.7, dielectrics 0. Base colour 0.04–0.9 (no pure black/white).
- Paint splits that are visible in the reference are real geometry/material boundaries
  (see tank recess in the case study), decals/logos are textures (not modelled).

## Style profiles (set in project.md)
- `realistic_game` (default): real proportions, 1–3 mm bevels on visible edges, moderate detail.
- `stylized_lowpoly`: big simple forms, flat colours, ≤ 6 colours, lower half of budget.
- `scifi_industrial`: 70/20/10 primary/secondary/tertiary, chamfers everywhere, hazard accents.
Style never overrides proportion or function (wheels are round, doors fit humans).
