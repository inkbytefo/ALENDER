# VEH_TT92_Racing_Car

## Category
vehicle

## Objective
Accurate, editable game-asset reconstruction (realistic_game) of the red front-engined
"TT92 / #4" retro single-seater racing car shown in the photos — not a generic vintage racer.

## References
- ref/REAL_REFERENCE.png   primary truth: near-orthographic TOP view, 681x1265 px, front = image TOP
- ref/REF_OBLIQUE.png      secondary photo: high oblique from the car's front-RIGHT, 631x1121 px
- ref/MODELING_CHEATSHEET.png  AI sheet, 1672x941 px (decomposition, heights, sections only)

**Reference conflict (resolved by source priority, photo wins):** the cheatsheet treats the pointed
end as the NOSE and puts the cockpit near the blunt end. The photos show the opposite: the steering
wheel is ahead of the seat towards the blunt end, the engine louvres + exhaust headers are at the
blunt end, the exhaust runs rearwards to the pointed end. So: blunt louvred end = FRONT, pointed
end = TAIL (1950s front-engined GP layout). The cheatsheet side view is therefore used only for
global heights (0.78 m body, 0.12 m clearance), never for the position of cockpit/headrest.

There is no side photo. Plan view (X/Y) comes from the top photo; heights (Z) are estimated from
the cheatsheet numbers + mechanical logic and checked against the oblique photo (fitted camera).

## Scale & measurements (docs/03)
- scale: 312.5 px/m from the rear tyre diameter 225 px = 0.72 m (cheatsheet "tire diameter 0.72 m",
  typical vintage-GP rear cover 0.70-0.75 m)
- cross-checks: rear track 447 px = 1.43 m vs cheatsheet 1.46 m (-2 %); wheelbase 665 px = 2.13 m
  vs 250F-class front-engined GP cars 2.2-2.3 m (-5 %); cheatsheet length 3.80 m vs 3.30 m body
  (the AI sheet stretches overhangs; photo wins)
- photo tilt: none needed (top view); camera slightly off-centre -> body centre-line drifts
  341-350 px (±3 cm); model is built symmetric about u = 345
- key dimensions (measured): WB 2.13 m, track F 1.32 / R 1.43 m, body 3.30 m (+ tail blade 0.17 m),
  body max width 0.64 m, overall width 1.82 m, tyre dia F 0.59 / R 0.72 m

## Style / budget
STYLE=realistic_game
Stage 1 LOW: < 15k tris   Stage 2 HIGH: 40k - 100k tris   materials <= 8

## Part breakdown (primary -> secondary -> tertiary)
| Part | builder | approx size | LOD notes |
|------|---------|-------------|-----------|
| wheels x4 (tyre, wire rim, spinner) | lathe + tubes | F 0.59, R 0.72 m | spokes HIGH only |
| body shell with cockpit opening | custom loft_rings (open-top rings) | 3.3 x 0.64 x 0.66 m | subsurf HIGH |
| nose grille (ribbed carbon) | lathe/loft | 0.2 m | ribs HIGH |
| side fins L/R | extruded plan outline | 0.3 x 0.14 m | bevel |
| bonnet louvres, side louvre panel | extrude_polys | | HIGH |
| front suspension (wishbones, uprights, brake drums) | tubes/cyl | | |
| rear suspension (transverse coil-overs, links, radius rods) | tubes/helix | | |
| exhaust (right): headers -> wrapped pipe -> tip | tube | r 0.03 m | wrap helix HIGH |
| cockpit: tub, seat, steering wheel, padded rim | loft/lathe/tube | | |
| tail blade, fuel caps, air filter, canards | plates/lathe | | UNCERTAIN where hidden |

## Uncertain / hidden areas
- all heights (no side photo) -> body height profile, fin height, suspension heights
- right front suspension (hidden under carbon/shadow) mirrored from left
- underside, engine, gearbox (hidden) -> not modelled beyond the floor
- carbon canards at the nose, tail blade height

## Deliverables
output/VEH_TT92_Racing_Car/blend/VEH_TT92_Racing_Car_00_SETUP ... _05_FINAL_GEOMETRY, VEH_TT92_Racing_Car.blend
output/VEH_TT92_Racing_Car/glb/VEH_TT92_Racing_Car.glb, output/VEH_TT92_Racing_Car/renders/, projects/VEH_TT92_Racing_Car/report.json
