# VEH_TT92_Racing_Car

Red front-engined single-seater: photo-measured plan (wheels, body width, cockpit, exhaust, rear
suspension) with a user-directed redesign of the front end, engine and details.
Category `vehicle`, style `realistic_game`.

## Files
| file | role |
|------|------|
| `landmarks.py` | every number: `[PHOTO]` = measured in px on the top photo, `[DESIGN]` = chosen |
| `parts.py` | geometry recipes, one builder per part group; `STAGES` maps builders to stages |
| `stagelib.py` | shared helpers of the stage scripts (milestones, review renders) |
| `stage1_blockout.py` | LOW blockout of every part, proportions + collision check |
| `stage2_body.py` | HIGH primary forms: wheels, body shell + boolean cuts, nose mouth |
| `stage3_mechanical.py` | HIGH exhaust (both sides), tail nozzle, suspension, blown V8 |
| `stage4_details.py` | HIGH cockpit, details, front end, fasteners; pivots, checks, renders, GLB, report |
| `stage5_workspace.py` | clean GUI file `..._WORKSPACE.blend` |
| `build.py` | runs the stages (`--stage N`, `--from N`, `--until N`) |
| `refcams.py` | orthographic top reference camera + photo |
| `ref/` | `REAL_REFERENCE.png` (top photo, truth for the plan), `REF_OBLIQUE.png`, cheatsheet, analysis crops |
| `report.json` | checks + metrics of the last stage 4 run |

## Build
```bash
python wb.py build VEH_TT92_Racing_Car                # stages 1-5
python wb.py build VEH_TT92_Racing_Car --stage 5      # only the workspace file
python wb.py build VEH_TT92_Racing_Car --from 2       # stage 2 to the end
python wb.py present VEH_TT92_Racing_Car --style clay # studio sheets (also studio_dark)
```
The project is NOT on the gated S1-S4 pipeline (`wb.py gate` reports it as legacy): the nose is a
design change, so a silhouette gate against the top photo would be meaningless there. The checks
live in `stage4_details.py` (U02-U15, V01-V04).

## Outputs (`output/VEH_TT92_Racing_Car/`)
- `blend/..._WORKSPACE.blend` - **the file to work in**: final model only, collections Body / Front /
  Cockpit / Engine / Exhaust / Suspension / Wheels / Fasteners (+ Reference, Studio), one root
  empty, wheel pivots on the axles, live bevel modifiers, README text block.
- `blend/VEH_TT92_Racing_Car.blend` - pipeline file (LOW + HIGH), source of `present` and of stage 5.
- `blend/..._00_SETUP ... _05_FINAL_GEOMETRY.blend` - one milestone per build step.
- `glb/VEH_TT92_Racing_Car.glb`, `renders/`, `presentation/`, `work/s1..s4/` (review renders).

## Reference numbers (last build)
HIGH 98,604 tris (target 40k-100k), LOW 17,058 tris, 252 mesh objects, 8 materials,
bbox 1.802 x 3.380 x 0.836 m, wheelbase 2.128 m, track F 1.32 / R 1.43 m, tyres 0.59 / 0.72 m.
A rebuild must reproduce these exactly.

## Scale and axes
Scale 312.5 px/m from the rear tyre (225 px = 0.72 m); cross-checks: rear track 447 px = 1.43 m,
wheelbase 665 px = 2.13 m. +X = car left, -Y = front, +Z up, origin midway between the axles on
the ground. Top photo: front = image top (the AI cheatsheet shows the car reversed; photo wins).

## The design as built
- **Body**: loft of superellipse sections; three boolean cuts (cockpit, engine bay, nose mouth);
  low tapered wedge nose (tip 0.38 x 0.22 m); the tail tapers to a round face (radius 0.14 m).
- **Front** ("old JDM wedge", inspired by a Honda RA300 nose, a riveted hot rod and slim sport-bike
  eyes - inspiration, not copies): wide flat mouth with chrome lip, five chrome slats and an emblem;
  slanted smoked eyes with two round lamps each; red bullet fender mirrors on chrome stalks; dark
  chin spoiler; twin cream stripes from the nose to the engine bay; riveted bonnet seams.
- **Engine**: blown 60-degree V8 in an open bay (blocks, cam covers, Roots blower, four velocity
  stacks, crank-to-blower belt). Invented: no photo shows the engine.
- **Exhaust**: four headers per side into a wrapped side pipe, mirrored left/right. Behind the rear
  axle both pipes sweep inwards and enter the **tail nozzle** (`NOZZLE_*`, rocket-thruster reference):
  stepped dark collar sleeved over the tail end, bronze heat ring, chrome bell, dark core, six ribs,
  two inlet sleeves. No glow: an emissive ring would need a 9th material (limit is 8).
- **Rest**: wire wheels with knock-off spinners, double-wishbone front, transverse coil-over rear,
  leather cockpit, bonnet louvres, filler caps, air filter.

## Uncertain / limits
- No side photo: every height is a design estimate (`BODY_ZTOP/ZBOT`, exhaust, suspension).
- The nose (v < 250 px) and the tail (v > 950 px) no longer follow the top photo - intended.
- Right front suspension is mirrored from the left (`UNCERTAIN_SUSP_Front_*`).
- Faint shading marks remain around the nose mouth (boolean on the subdivided shell).
- Paint is a plain material; tyres have no tread.

## History (2026-09-29 .. 2026-10-01)
1. Reconstruction from the top photo (two-stage legacy build).
2. Engine bay + V8, exhaust mirrored, panel lines, first nose redesign (fangs, claws, scoop).
3. Front v2 "white hot rod" box nose - rejected. Front v3 "old JDM wedge" - kept.
4. Removed on request: side fins, side louvre panels, tail blade, canards, door lines + handles.
5. Flame relief as geometry tried and reverted - planned later as a normal map.
6. Project rewritten into five stage scripts + clean workspace file; geometry verified identical
   (per-object fingerprint: 239 objects, 0 differences).
7. Rear redesign: pointed tail replaced by a round tail face with a rocket-style nozzle; side pipes
   routed into the nozzle collar; rear radius rods re-anchored on the new tail.
