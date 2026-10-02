# CHAR_Cat_Gamer

> Filled by the agent in S0 INTAKE, BEFORE modelling (docs/01_WORKFLOW.md). Short and factual.

## Category / targets
character            <!-- vehicle | architecture | character | prop | environment | animation -->
budget key: character  (workbench.tables.BUDGETS; change CATEGORY in parts.py if wrong)
targets: game (S4) | render (S3 + S5) | print (P01/P02)   engine: godot | unity | unreal

## Objective
One sentence: what is built, for what use.

## References
- ref/REAL_REFERENCE.png   primary truth (photo)          side: RIGHT|LEFT, size WxH px
- ref/REF_MASK.png         photo silhouette (python wb.py mask CHAR_Cat_Gamer) - checked by eye? yes/no
- ref/MODELING_CHEATSHEET.png  secondary (decomposition / proportions)
- other: ...

## Scale & measurements (docs/03_REFERENCE_ANALYSIS.md)
- scale: ___ px/m, derived from: ___ (known real size)   cross-checks: ___
- photo tilt/pitch: ___ deg (why)
- key dimensions: L ___ x W ___ x H ___ m -> TARGET_DIMS in parts.py
- edges measured with wb.py profile / mask (list which landmarks), read by eye (list which)

## Stage plan
| Stage | content | budget (tris) |
|-------|---------|---------------|
| S1 PRIMITIVE | main masses only | < s1_max |
| S2 LOWPOLY (LOD0) | real forms, no bevels, UV atlas | s2 range |
| S3 DETAIL | bevels, subsurf lofts, fasteners, ribs | < s3_max |
| S4 GAME | bake, LOD1-2, collision per part | auto |

## Part breakdown (registry parts.PARTS)
| Part key | prim builder | real builder | collision | moving? |
|----------|--------------|--------------|-----------|---------|

## Uncertain / hidden areas
- ... (named UNCERTAIN_*, listed in parts.UNCERTAIN)

## Deliverables
output/CHAR_Cat_Gamer/blend/CHAR_Cat_Gamer_S0_SETUP ... _S4_GAME.blend, CHAR_Cat_Gamer.blend (hero S3)
output/CHAR_Cat_Gamer/glb/CHAR_Cat_Gamer_LOD0..2.glb (+ fbx for unreal), CHAR_Cat_Gamer_hero.glb, textures/
output/CHAR_Cat_Gamer/work/s1..s4 (review images), projects/CHAR_Cat_Gamer/report.json (python wb.py gate CHAR_Cat_Gamer)
