# __ASSET__

> Filled by the agent in S0 INTAKE, BEFORE modelling (docs/01_WORKFLOW.md). Short and factual.

## Category / targets
__CATEGORY__            <!-- vehicle | architecture | character | prop | environment | animation -->
budget key: __BUDGET__  (workbench.tables.BUDGETS; change CATEGORY in parts.py if wrong)
targets: game (S4) | render (S3 + S5) | print (P01/P02)   engine: godot | unity | unreal

## Objective
One sentence: what is built, for what use.

## References
- ref/REAL_REFERENCE.png   primary truth (photo)          side: RIGHT|LEFT, size WxH px
- ref/REF_MASK.png         photo silhouette (python wb.py mask __ASSET__) - checked by eye? yes/no
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
output/__ASSET__/blend/__ASSET___S0_SETUP ... _S4_GAME.blend, __ASSET__.blend (hero S3)
output/__ASSET__/glb/__ASSET___LOD0..2.glb (+ fbx for unreal), __ASSET___hero.glb, textures/
output/__ASSET__/work/s1..s4 (review images), projects/__ASSET__/report.json (python wb.py gate __ASSET__)
