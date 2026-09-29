# VEH_Gemini_Motorcycle

## Category
vehicle (motorcycle)

## Objective
Reference-accurate reconstruction of the custom Honda inline-4 street bike ("X-AXIS HONDA X")
as an editable high-poly source asset (game-ready GLB, renders). Reference implementation of the workbench.

## References
- ref/REAL_REFERENCE.png — 1080×720 side photo, bike's RIGHT side, rear wheel on a paddock stand
- ref/MODELING_CHEATSHEET.png — AI-generated sheet (decomposition only; wrong in details)

## Scale & measurements
- 400 px/m from tyres 120/70-17 (240 px) and 180/55-17 (250 px)
- cross-checks: length 820 px = 2.05 m, height 418 px = 1.045 m
- pitch 1.98° nose-down (stand) removed; wheelbase 1.444 m; rake 22°; seat 0.80 m

## Style / budget
STYLE=realistic_game · LOW < 15k tris (9.8k) · HIGH 40k–100k (65.5k) · 8 materials

## Part breakdown
wheels (tyre/rim/hub/spokes lathes) · brakes (drilled discs, calipers) · frame (tube rails, pivot
plates, head tube) · tank (boundary-aware loft with black knee recess) · seat, hump, tail (lofts),
tail light, side panels · engine (crankcase, transmission, block, head, cam cover, fins, covers,
carbs, intakes, airbox, sump) · front (USD fork, clamps, stem, headlight, clip-ons, grips,
levers, reservoirs) · rear (swingarm, brace, pivot, monoshock + helix spring, sprockets, chain,
rearsets) · exhaust (4 headers with tyre clearance, collector, muffler) · details (fasteners,
chain adjusters, brake line)

## Uncertain / hidden
airbox, downtube, tail crossmembers, left-side engine covers, filler cap, shock mounts, chain side

## Deliverables
output/VEH_Gemini_Motorcycle/blend (00…05, STAGE_01_LOW, final), glb/, renders/, report.json
