# PROP_Plasma_Saber

## Category / targets
- Category: `prop` (hand-held sci-fi energy weapon, hero game asset)
- Budget key: `hero_prop` (workbench.tables.BUDGETS: S1 < 1.5k, S2 = 4k-15k, S3 < 60k, textures 2048, materials <= 4)
- Target use: `game asset (engine)` (Godot / Unity / Unreal) + `product render`
- Style: `realistic_game` / `scifi_industrial`

## Objective
High-detail, realistic, original and copyright-safe tactical plasma saber / laser sword hilt (Vanguard Arc-Cutter).
Original industrial sci-fi aesthetic avoiding trademarked film elements, featuring clean quad-dominant geometry,
exact mechanical decomposition, functional ergonomic layout, baked game-ready LODs (LOD0-2) with collision and glTF export.

## References
- `ref/REAL_REFERENCE.png` — primary truth: high-resolution orthographic right-side technical reference view (1280x720).
- `ref/REF_MASK.png` — reference silhouette mask (1280x720, verified clean).

## Scale & measurements (docs/03_REFERENCE_ANALYSIS.md)
- Scale: `2500.0 px/m` (2.5 px/mm), derived from overall hilt length 750 px = 0.300 m (300 mm).
- Cross-checks:
  - Main grip tube diameter: 87.5 px = 35.0 mm (standard ergonomic combat grip).
  - Clamp collars diameter: 100 px = 40.0 mm.
  - Emitter shroud diameter: 105 px = 42.0 mm.
  - Switch module height: 115 px from bottom to top = 46.0 mm.
  - Crystal chamber length: 80 px = 32.0 mm.
- Tilt / pitch: 0.0 deg (central bore axis at v=360 px is horizontal).
- Origin (0,0,0): Central weapon axis at geometric center of hilt (px 640.0, 360.0). -Y forward, +Z up, +X object's left.
- Key dimensions: Length 0.300 m x Width 0.042 m x Height 0.046 m -> TARGET_DIMS = (None, 0.300, None).
- Edges measured with `wb.py mask` & `create_reference.py`:
  - `EMITTER_SHROUD`, `EMITTER_COILS`, `CHASSIS_UPPER`
  - `CRYSTAL_CHAMBER`, `CTRL_SWITCHBOX`, `CHASSIS_MID`
  - `GRIP_BODY`, `GRIP_RIBS`, `CHASSIS_LOWER`, `POMMEL_CAP`, `POMMEL_DRING`

## Stage plan
| Stage | Content | Budget (tris) |
|-------|---------|---------------|
| S1 PRIMITIVE | Main masses only (cylinders, blockouts, simplified bounds) | < 1,500 |
| S2 LOWPOLY (LOD0) | Real builders, clean topology, no bevels, shared UV atlas | 4,000 - 15,000 |
| S3 DETAIL | Hard-surface bevel + weighted normals, serrations, cooling fins, crystal facet detail | < 60,000 |
| S4 GAME | Bake S3 -> S2 atlas (base, ORM, normal), LOD1-2, collision hulls | auto |
| S5 PRESENT | Studio presentation renders (clay + studio_dark) | — |

## Part breakdown (registry parts.PARTS)
| Part key | Prim builder | Real builder | Collision | Moving? |
|----------|--------------|--------------|-----------|---------|
| `emitter` | `emitter_prim` | `emitter` | hull | Static |
| `chassis_upper` | `chassis_upper_prim` | `chassis_upper` | hull | Static |
| `crystal_chamber`| `crystal_chamber_prim`| `crystal_chamber`| hull | Static |
| `switch_module` | `switch_module_prim` | `switch_module` | box | Rocker switch / controls |
| `grip` | `grip_prim` | `grip` | hull | Static |
| `chassis_lower` | `chassis_lower_prim` | `chassis_lower` | hull | Static |
| `pommel` | `pommel_prim` | `pommel` | hull | D-ring loop pivots |

## Uncertain / hidden areas
- Width across X: symmetrical cylindrical and milled chassis, depth matches Z radius.
- Internal plasma crystal mounting gimbal: internal mechanical detail, visible through sapphire chamber window.

## Deliverables
- `output/PROP_Plasma_Saber/blend/PROP_Plasma_Saber_S0_SETUP.blend` ... `_S4_GAME.blend`, `PROP_Plasma_Saber.blend` (hero S3)
- `output/PROP_Plasma_Saber/glb/PROP_Plasma_Saber_LOD0..2.glb`, `PROP_Plasma_Saber_hero.glb`, `textures/`
- `output/PROP_Plasma_Saber/work/s1..s4` (review images, silhouettes, diffs)
- `projects/PROP_Plasma_Saber/report.json` (all stage checks PASS)
