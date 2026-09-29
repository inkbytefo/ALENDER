# __ASSET__

> Filled by the agent BEFORE modelling (docs/01_WORKFLOW.md step 1). Keep it short and factual.

## Category
__CATEGORY__            <!-- vehicle | architecture | character | prop | environment | animation -->

## Objective
One sentence: what is built, for what use (game asset, render, animation, print...).

## References
- ref/REAL_REFERENCE.png   primary truth (photo)          side: RIGHT|LEFT, size WxH px
- ref/MODELING_CHEATSHEET.png  secondary (decomposition / proportions)
- other: ...

## Scale & measurements (from docs/03_REFERENCE_ANALYSIS.md)
- scale: ___ px/m, derived from: ___ (known real size)   cross-checks: ___
- photo tilt/pitch: ___ deg (why)
- key dimensions: L ___ x W ___ x H ___ m, other: ___

## Style / budget
STYLE=realistic_game | stylized_lowpoly | scifi_industrial
Stage 1 LOW: < ___ tris   Stage 2 HIGH: ___ - ___ tris   materials <= ___

## Part breakdown (primary -> secondary -> tertiary)
| Part | builder | approx size | LOD notes |
|------|---------|-------------|-----------|

## Uncertain / hidden areas
- ... (will be named UNCERTAIN_*)

## Deliverables
output/__ASSET__/blend/__ASSET___00_SETUP ... _05_FINAL_GEOMETRY, __ASSET__.blend
output/__ASSET__/glb/__ASSET__.glb, output/__ASSET__/renders/, projects/__ASSET__/report.json
