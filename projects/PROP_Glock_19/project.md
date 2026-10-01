# PROP_Glock_19

## Category / targets
- Category: `prop` (hand-held weapon, hero game asset)
- Budget key: `hero_prop` (workbench.tables.BUDGETS: S1 < 1.5k, S2 = 4k-15k, S3 < 60k, textures 2048, materials <= 4)
- Target use: `game asset (engine)` (Godot / Unity / Unreal) + `product render`
- Style: `realistic_game`

## Objective
Accurate, editable, procedural reconstruction of the Glock 19 Gen 4 9x19mm compact semi-automatic pistol
from the reference photo and orthographic modeling cheatsheet. Clean quad topology, exact mechanical decomposition,
baked game-ready LODs (LOD0-2) with collision and glTF export.

## References
- `ref/REAL_REFERENCE.png` — primary truth: high-resolution orthographic right-side reference view (1280x720).
- `ref/REF_MASK.png` — photo silhouette (generated via `python wb.py mask PROP_Glock_19`, verified clean).
- `ref/MODELING_CHEATSHEET.png` — secondary reference: 10-panel Glock 19 Gen 4 cheatsheet (orthographics, exploded breakdown, cross-sections, topology overlay, detail closeups, swatches).
- `ref/REF_PHOTO_RAW.png` — raw photograph of Glock 19 Gen 4 from cheatsheet Panel 1.

## Scale & measurements (docs/03_REFERENCE_ANALYSIS.md)
- Scale: `5000.0 px/m` (5.0 px/mm), derived from overall length 922 px = 0.1844 m (~185 mm official spec).
- Cross-checks:
  - Overall height: 630 px = 126.0 mm (Glock 19 official spec: 128 mm with standard magazine, -1.5%).
  - Slide length: 864 px = 172.8 mm (Glock 19 official spec: 174 mm, -0.7%).
  - Slide height: 140 px = 28.0 mm (Glock 19 official spec: 28 mm, exact match).
  - Bore diameter: 9.0 mm (45 px).
  - Outer barrel diameter: 14.5 mm (72.5 px).
- Tilt / pitch: 0.0 deg (bore axis at v=160 px is level).
- Origin (0,0,0): Bore axis at breech face / trigger plane (px 537.0, 160.0). -Y forward, +Z up, +X object's left.
- Key dimensions: Length 0.185 m x Width 0.032 m x Height 0.128 m -> TARGET_DIMS = (0.032, 0.185, 0.128).
- Edges measured with `wb.py mask` & `wb.py profile`:
  - `SLIDE_OUTLINE`, `SLIDE_TOP`, `SLIDE_BOT`
  - `FRAME_DUST_COVER`, `FRAME_GUARD`, `GRIP_BACKSTRAP`, `GRIP_FRONTSTRAP`
  - `CTRL_TRIGGER`, `MAG_FLOORPLATE`, `SIGHT_REAR`, `SIGHT_FRONT`

## Stage plan
| Stage | Content | Budget (tris) |
|-------|---------|---------------|
| S1 PRIMITIVE | Main masses only (boxes, cylinders, blockouts) | < 1,500 |
| S2 LOWPOLY (LOD0) | Real builders, clean topology, no bevels, shared UV atlas | 4,000 - 15,000 |
| S3 DETAIL | Hard-surface bevel + weighted normals, serrations, pins, fasteners | < 60,000 |
| S4 GAME | Bake S3 -> S2 atlas (base, ORM, normal), LOD1-2, collision hulls | auto |
| S5 PRESENT | Studio presentation renders (clay + studio_dark) | — |

## Part breakdown (registry parts.PARTS)
| Part key | Prim builder | Real builder | Collision | Moving? |
|----------|--------------|--------------|-----------|---------|
| `slide` | `slide_prim` | `slide` | box | Slide cycles along -Y |
| `barrel` | `barrel_prim` | `barrel` | hull | Locks into slide / tilts |
| `sights` | `sights_prim` | `sights` | box | Fixed to slide |
| `recoil` | `recoil_prim` | `recoil` | cyl | Telescopes |
| `frame` | `frame_prim` | `frame` | hull | Static |
| `trigger` | `trigger_prim` | `trigger` | box | Rotates on trigger pin |
| `controls` | `controls_prim` | `controls` | box | Slide stop, takedown, pins |
| `magazine` | `mag_prim` | `magazine` | hull | Detachable |

## Uncertain / hidden areas
- Widths across X: estimated from official Glock technical specifications (slide 25.5 mm, frame 27 mm, grip 30 mm, palm swell 32 mm).
- Left side (+X) controls: slide stop lever and magazine release button modeled on +X according to Glock 19 Gen 4 architecture.
- Striker assembly and internal firing pin channel: simplified (covered by rear slide plate).

## Deliverables
- `output/PROP_Glock_19/blend/PROP_Glock_19_S0_SETUP.blend` ... `_S4_GAME.blend`, `PROP_Glock_19.blend` (hero S3)
- `output/PROP_Glock_19/glb/PROP_Glock_19_LOD0..2.glb`, `PROP_Glock_19_hero.glb`, `textures/`
- `output/PROP_Glock_19/work/s1..s4` (review images, silhouettes, diffs)
- `projects/PROP_Glock_19/report.json` (all stage checks PASS)
