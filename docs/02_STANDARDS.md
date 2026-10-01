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
projects/<ASSET>/   project.md  landmarks.py  parts.py  build.py  report.json  ref/ (REAL_REFERENCE.png, REF_MASK.png)
output/<ASSET>/     blend/<ASSET>_S0_SETUP|S1_PRIMITIVE|S2_LOWPOLY|S3_DETAIL|S4_GAME.blend, <ASSET>.blend (hero S3)
                    glb/<ASSET>_LOD0..2.glb, <ASSET>_hero.glb   fbx/ (unreal)   textures/ (T_<ASSET>_base|orm|normal.png)
                    renders/   video/   presentation/   work/s1..s4 (review + gate images)
```
Milestones: one per stage via `paths.milestone(asset, stages.milestone_tag(n))`; each stage opens the
previous one, so a stage can be rebuilt alone (`wb.py build A --stage 3`). Never overwrite the only
good state. Legacy projects keep `00_SETUP … 05_FINAL_GEOMETRY`.

## Collections
`00_REFERENCE 01_GUIDES 10_S1_PRIMITIVE 20_S2_LOWPOLY 30_S3_DETAIL 40_S4_GAME 41_S4_COLLISION
08_TEMP 09_PRESENTATION` (`stages.COLLECTIONS`). Earlier stages stay in the file, hidden.
Legacy: `02_LOW_* … 07_DETAILS` (`scene.COLLECTIONS`).

## Naming
- Assets: `VEH_ ENV_ ARCH_ CHR_ PROP_ ANIM_` + PascalCase (`VEH_Gemini_Motorcycle`).
- Parts: `GROUP_Part[_Detail][_L|_R|_FL|_RR]` — e.g. `BODY_Tank`, `FRAME_Swingarm_L`,
  `ENGINE_Cover_Main_R`, `WHEEL_Front_Tire`, `CTRL_Grip_L`, `ARCH_Wall_North`, `CHR_Body`.
- Stage suffix (added by `stages.nm(P, name)` / the pipeline): `_PRIM` (S1), `_LP` (S2), `_HP` (S3),
  `_LOD0.._LOD2` (S4 game objects); static game parts merge into `<ASSET>_Body_LODn`.
  Bake matching and intersection pairs use the base name (`stages.base_name`). Legacy: `_LOW`.
- Collision: engine naming (docs/12): `…-convcolonly` (Godot), `UCX_…` (Unreal), `…_Collider` (Unity).
- Guessed / hidden geometry: `UNCERTAIN_` prefix. Temp: `TEMP_*` (removed by the pipeline).
- Fasteners: `FASTENER_<FAMILY>_###` sharing meshes `BOLT_M6/M8/M10`, `NUT`, `WASHER`.
- Materials: `MAT_<PURPOSE>`; baked game material `MAT_<ASSET>_Baked`. Textures `T_<ASSET>_<map>`.
- No `Cube.001`, no spaces (gate N01).

## Budgets (evaluated triangles = modifiers applied) — `workbench/tables.py` BUDGETS
| key (`parts.CATEGORY`) | S1 max | S2 = LOD0 target | S2 max | S3 max | tex | LOD0 glb |
|------------------------|--------|------------------|--------|--------|-----|----------|
| hero_vehicle | 3k | 15k–60k | 80k | 150k | 2048 | 12 MB |
| background_vehicle | 1.5k | 4k–12k | 20k | 30k | 1024 | 4 MB |
| building | 2k | 5k–30k | 50k | 100k | 2048 | 10 MB |
| modular (wall/floor kit) | 0.3k | 0.5k–4k | 8k | 15k | 1024 | 2 MB |
| character | 1.5k | 8k–30k | 40k | 60k | 2048 | 10 MB |
| hero_prop (FPS weapon …) | 1.5k | 4k–15k | 20k | 60k | 2048 | 6 MB |
| small_prop / large_prop | 0.3k / 0.8k | 0.3k–2k / 1.5k–8k | 3k / 12k | 5k / 25k | 512 / 1024 | 1 / 3 MB |
LOD1 / LOD2 = 50 % / 25 % of LOD0 by default. Subsurf on S3: viewport/export level 1, render level 2.

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
