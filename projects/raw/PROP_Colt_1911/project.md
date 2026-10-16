# PROP_Colt_1911

Colt M1911-A1 semi-automatic service pistol (.45 ACP).
Low-poly, game-ready PBR hero asset rebuilt procedurally from original reference geometry.

## Category / targets
hero_prop
budget key: hero_prop (workbench.tables.BUDGETS)
targets: game (S4) | render (S3 + S5) | engine: godot

## Objective
Reconstruct a game-ready, mechanically faithful Colt M1911-A1 pistol with zero n-gons, accurate proportions, crisp hard-surface bevels, and baked PBR materials for FPS viewmodels.

## References
- ref/REAL_REFERENCE.png: primary truth (left side orthographic render, 2048x1536 px)
- ref/REF_MASK.png: ground-truth binary silhouette mask
- ref/SOURCE_M1911A1.glb: reference 3D model
- ref/PARTS_GEOMETRY.json: measured bounding boxes and sub-assembly dimensions

## Scale & measurements
- scale: 7314.2857 px/m, derived from 0.28m camera orthographic span at 2048 px
- photo tilt: 0.0 deg (pure orthographic alignment)
- key dimensions: Width 0.0303m (X) x Length 0.2351m (Y) x Height 0.1463m (Z)
- lowest Z: 0.0000 m (magazine floorplate and bottom edge seated on ground)

## Stage plan
| Stage | content | budget (tris) |
|---|---|---|
| S1 PRIMITIVE | Main slide cylinder/box, frame grip block, barrel, sights | < 1,500 |
| S2 LOWPOLY (LOD0) | Clean quad/tri topology, no bevels, modular levers, UV unwrap | 4,000 - 15,000 |
| S3 DETAIL | Micro-bevels, slide serrations, knurled/checkered grips, chamber hood | < 60,000 |
| S4 GAME | 2048 PBR bake, LOD1 (50%), LOD2 (25%), convex collision hulls | < 6 MB GLB |

## Part breakdown (registry parts.PARTS)
| Part key | prim builder | real builder | collision | moving? |
|---|---|---|---|---|
| `slide` | `slide_prim` | `slide` | box | yes (cycles back on -Y) |
| `frame` | `frame_prim` | `frame` | convcol | base frame |
| `barrel` | `barrel_prim` | `barrel` | capsule | tilts slightly |
| `grip_panels` | `grip_panels_prim` | `grip_panels` | box | attached to frame |
| `controls` | `controls_prim` | `controls` | box | trigger & hammer pivots |
| `sights` | `sights_prim` | `sights` | box | attached to slide |
| `magazine` | `magazine_prim` | `magazine` | box | ejects down -Z |

## Deliverables
- `output/PROP_Colt_1911/glb/PROP_Colt_1911_LOD0.glb` (game asset)
- `output/PROP_Colt_1911/glb/PROP_Colt_1911_hero.glb` (master highpoly)
- `output/PROP_Colt_1911/presentation/` (clay + dark studio renders)
