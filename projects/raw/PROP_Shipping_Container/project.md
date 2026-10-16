# PROP_Shipping_Container

Standard 20ft ISO corrugated steel shipping container (2.4m width x 6.0m length x 2.6m height).

## Category / targets
prop
budget key: large_prop (workbench.tables.BUDGETS)
targets: game (S4) | render (S3 + S5)
engine: godot (GLB LOD0-2 with -convcolonly collision)

## Objective
High-fidelity, reference-accurate, game-ready 3D asset of an industrial corrugated steel shipping container with double locking bar doors on both ends, ISO 1161 corner casting blocks (stackable up to 5.2m), forklift pockets, and PBR metallic-roughness materials in slate blue-grey and rust-orange variants with bottom dirt and wear.

## References
- ref/REAL_REFERENCE.png: 4-view container reference (perspective, side, wireframe)
- ref/REF_FOURPANEL.png: full 4-panel user reference image
- Primary dimensions: ISO 668 1CC (20ft standard container: 6.058m x 2.438m x 2.591m nominal, modeled at exact 6.0m x 2.4m x 2.6m target spec).

## Scale & measurements
- Dimensions: Length 6.000m x Width 2.400m x Height 2.600m
- Corner Castings: ISO 1161 standard (0.178m length x 0.162m width x 0.118m height)
- Forklift Pockets: 2 pockets spaced 2.05m center-to-center, 0.355m x 0.115m clear openings
- Walls: 20 trapezoidal corrugation ribs per side, 0.042m depth, 0.28m pitch
- Doors: Double-leaf doors on BOTH front and rear ends, 4 locking bars per end (8 total), 4 hinges per leaf (16 total), cam keepers and latch handles.

## Stage plan
| Stage | content | budget (tris) |
|-------|---------|---------------|
| S1 PRIMITIVE | main masses, corner posts, rails, door blocks, casting blocks | < 800 |
| S2 LOWPOLY (LOD0) | corrugated walls, ISO corner castings with apertures, double doors on both ends, locking bars, hinges, handles | 1,500 - 8,000 |
| S3 DETAIL | beveled edges, weld beads, gaskets, cam heads, keeper slots, weighted normals | < 25,000 |
| S4 GAME | baked PBR maps (base color, ORM, normal), LOD1 (50%), LOD2 (25%), convex collision | auto |

## Part breakdown (registry parts.PARTS)
| Part key | prim builder | real builder | collision | moving? |
|----------|--------------|--------------|-----------|---------|
| frame | frame_prim | frame | box | no |
| castings | castings_prim | castings | box | no |
| walls | walls_prim | walls | box | no |
| roof | roof_prim | roof | box | no |
| doors_front | doors_front_prim | doors_front | box | yes (hinged) |
| doors_rear | doors_rear_prim | doors_rear | box | yes (hinged) |
| locking_bars | locking_bars_prim | locking_bars | none | yes (rides with doors) |

## Uncertain / hidden areas
- Interior floor planking (container is closed / exterior-focused prop, modeled as sealed floor plate).
