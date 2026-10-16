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

## Finish steps (2026-10-01) - run after `python wb.py build VEH_Gemini_Motorcycle` (S1-S3 gated)
```bash
python wb.py run projects/VEH_Gemini_Motorcycle/finish_paint.py       # master material + 12 instances on S3 DETAIL
python wb.py run projects/VEH_Gemini_Motorcycle/finish_workspace.py   # clean GUI file ..._WORKSPACE.blend
python wb.py run projects/VEH_Gemini_Motorcycle/finish_game.py        # Godot package (TEX=512 for a quick test)
python wb.py present VEH_Gemini_Motorcycle --style studio_dark
```
| file | role |
|------|------|
| `paint.py` | `INSTANCES` (12 master-material instances), `BY_OLD` (flat material -> instance), `OVERRIDES` (by part name) |
| `finish_paint.py` | applies the paint to the hero blend, checks (all slots painted, normal maps wired), Cycles review renders |
| `finish_workspace.py` | `..._WORKSPACE.blend`: final model only, collections by function, README inside |
| `finish_game.py` | `output/.../godot/`: GLB + FBX, one 4K texture set, ORM + Standard `.tres`, re-import check |
| `GODOT.md` | import guide copied into the package |

Paint (photo): gloss candy red tank, gloss black bodywork, satin black frame / rims / fork, anthracite cast
engine, raw heat-tinted stainless headers, carbon muffler, brushed steel discs and fasteners, chrome fork
tubes, dark leather seat, glowing tail light; glass stays a plain transparent material.
Texture sets come from `projects/VEH_TT92_Racing_Car/material` (AI albedos, derived maps - see its README)
and the shared library; the red / black paint use the clean chrome set with a tint.
Numbers: 249 parts, 70,972 tris; game package 4 meshes (Body, Wheel_Front, Wheel_Rear, Glass) + hull,
atlas 661-674 px/m at 4K (coverage 38 %). Tested in Godot 4.7.2 (`GODOTTESTING/testingarea/test_gemini.tscn`).
Not done: tank "HONDA X" graphic, tyre tread, the S4 GAME stage of the pipeline (LODs) - `finish_game.py`
replaces it for the painted model. Model geometry was reviewed and left unchanged.

