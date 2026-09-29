# VEH_FF12_RacingCar

> Reference-driven 3D reconstruction of FF12 retro-modern racing car (Alfa Romeo 158/159 inspired GP racer with modern aero and Yokohama Advan wide tires).

## Category
vehicle

## Objective
Accurate, editable, reference-faithful 3D reconstruction of the FF12 retro-modern formula racing car for game engine / realistic render use. Single source of truth is the reference photo set; clean idempotent Python build in Blender Workbench.

## References
- `ref/REAL_REFERENCE.png` / `ref/REF_TOP.png` — primary truth: top-down photograph (681x1265 px) showing exact wheelbase, track width, tire positions, cockpit, louvers, fin, exhaust.
- `ref/REF_OBLIQUE.png` — secondary photo: 3/4 front oblique perspective (631x1121 px) showing surface heights, front splitter, suspension, rake, wheels, cockpit depth.
- `ref/MODELING_CHEATSHEET.png` — tertiary reference: AI cheatsheet for decomposition, naming, cross-sections, and baseline dimensions.
- `ref/REF_SIDE_ORTHO.png` & `ref/REF_FRONT_ORTHO.png` — orthographic cross-checks.

## Scale & measurements
- Scale: 241.4 px/m on top photo, derived from wheelbase = 2.56 m (618 px in photo).
- Cross-check 1: Overall length = 3.80 m (to body tail: 915 px / 241.4 = 3.79 m, matches cheatsheet within 10 mm). Total with fin & diffuser = 4.21 m.
- Cross-check 2: Tire outer diameter = 0.72 m (174 px in photo / 241.4 = 0.721 m).
- Key dimensions:
  - Wheelbase: 2.56 m (Front axle Y = -1.28 m, Rear axle Y = +1.28 m)
  - Track width: 1.46 m (Wheel centers X = ±0.73 m)
  - Overall width: 1.78 m across wide tires (tire width 0.32 m)
  - Ground clearance: 0.12 m
  - Body max height: 0.78 m (cowl / windscreen top 0.86 m)
  - Cockpit opening: 0.80 m length (v = 510 to 675 px)
- Coordinate convention: +Z up, -Y forward (nose), +X = car's LEFT side. Root origin at (0, 0, 0) midway between axles on the ground plane.

## Style / budget
- STYLE: `realistic_game`
- Stage 1 LOW: < 15,000 tris
- Stage 2 HIGH: 40,000 – 100,000 tris (evaluated)
- Materials: 8 (MAT_BODY_RED, MAT_CARBON, MAT_RUBBER, MAT_METAL_CHROME, MAT_METAL_DARK, MAT_EXHAUST, MAT_LEATHER_BROWN, MAT_GLASS)

## Part breakdown (primary -> secondary -> tertiary)
| Part | builder | approx size | LOD notes |
|------|---------|-------------|-----------|
| WHEEL_Tire_[FL,FR,RL,RR] | lathe_circle / tyre_profile | ⌀ 0.72 m × 0.32 m | LOW 20-seg lathe; HIGH 72-seg with Yokohama Advan tread & sidewalls |
| WHEEL_Rim_Hub_[FL,FR,RL,RR] | lathe + wire array + knockoff | 18" rim ⌀ 0.46 m | Wire spokes + center-lock 2-eared spinner |
| SUSP_Wishbones_[F,R] | tube arrays + uprights | tubes ⌀ 25 mm | Double A-arms, pushrods, hubs, brake discs |
| SUSP_Coilover_[F,R] | cylinder + helix spring | ⌀ 50 mm × 0.22 m | Red coil spring over damper body |
| BODY_Nose_Cone | loft_rings / cone | L 0.62 m | Yellow-tipped bullet nose with mesh grille |
| BODY_Front_Splitter | plate + endplates | 1.10 m × 0.40 m | Carbon fiber front wing with strakes and tie rods |
| BODY_Hood_Engine | loft_rings | L 1.25 m × W 0.58 m | Long torpedo cowl with dual louver vent rows |
| BODY_Side_Canards_[L,R] | plates / lofts | L 0.55 m × W 0.20 m | Mid-body side aero dive planes |
| BODY_Cockpit_Surround | loft_rings with cutout | L 0.85 m × W 0.58 m | Deep cockpit recess with molded leather padding |
| BODY_Cockpit_Windscreen | curved sheet | W 0.42 m × H 0.14 m | Vintage curved aero windscreen |
| COCKPIT_Seat | lofted bucket + cushions | L 0.65 m × W 0.44 m | Vintage leather bucket seat with 4-point harness |
| COCKPIT_Steering_Wheel | torus rim + 3 spokes + column | ⌀ 0.36 m | Wood rim, polished aluminium 3-spoke wheel |
| COCKPIT_Controls | cylinders / boxes | gauges, shifter | Shifter gate, dashboard dials, pedals |
| BODY_Rear_Tail | loft_rings | L 1.35 m tapering | Pointed cigar tail with dual fuel caps and rear diffuser |
| BODY_Dorsal_Fin | thin tapered plate | L 1.05 m × H 0.22 m | Central vertical stability fin |
| EXHAUST_Assembly | continuous tube + wrap + tip | L 2.10 m × ⌀ 75 mm | Right flank header runner with heat wrap and blued tip |

## Uncertain / hidden areas
- UNCERTAIN_FRAME_Chassis: internal spaceframe underneath the cigar body.
- UNCERTAIN_ENGINE_Block: engine block inside the louvers (visible only through vents).
- UNCERTAIN_Diff_Gearbox: rear transaxle between rear suspension wishbones.

## Deliverables
- `output/VEH_FF12_RacingCar/blend/` milestones 00_SETUP to 05_FINAL_GEOMETRY + `VEH_FF12_RacingCar.blend`
- `output/VEH_FF12_RacingCar/glb/VEH_FF12_RacingCar.glb`
- `output/VEH_FF12_RacingCar/renders/` (clay + material reference, 5 orthos, 2 perspectives, wireframe)
- `projects/VEH_FF12_RacingCar/report.json`
