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
| `stage3_mechanical.py` | HIGH exhaust (both sides), tail afterburner, suspension, blown V8 |
| `stage4_details.py` | HIGH cockpit, details, front end, fasteners; pivots, checks, renders, GLB, report |
| `stage5_paint.py` | replaces the flat materials of the HIGH model with the master-material instances; Cycles review renders |
| `stage6_workspace.py` | clean GUI file `..._WORKSPACE.blend` |
| `stage7_game.py` | Godot package: 7 merged game meshes, UV atlases, 4K bakes, GLB + FBX, `.tres` materials, re-import check |
| `GODOT.md` | import guide copied into the package as `README_GODOT.md` |
| `paint.py` | master material `MM_TT92_Master` + `INSTANCES` (14 materials: set, tile, parameters) + `ASSIGN` (object -> material) |
| `texgen.py` | builds the PBR sets in `material/` from the AI albedos in `material/_source/` |
| `material/` | texture sets `TT92_<Set>_1K-PNG/` + `README.md` (what is real / derived) |
| `MATERIALS.md` | material plan: part -> material map and the AI prompts used for the albedos |
| `build.py` | runs the stages (`--stage N`, `--from N`, `--until N`) |
| `refcams.py` | orthographic top reference camera + photo |
| `ref/` | `REAL_REFERENCE.png` (top photo, truth for the plan), `REF_OBLIQUE.png`, cheatsheet, analysis crops |
| `report.json` | checks + metrics of the last stage 4 run |

## Build
```bash
python wb.py build VEH_TT92_Racing_Car                # stages 1-7
python wb.py build VEH_TT92_Racing_Car --stage 7      # only the Godot package (~4 min; TT92_TEX=512 for a quick test)
python wb.py build VEH_TT92_Racing_Car --from 5       # repaint + workspace file (after editing paint.py)
python wb.py run projects/VEH_TT92_Racing_Car/texgen.py   # regenerate the texture sets
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
- `godot/` - **engine package**: `VEH_TT92_Racing_Car.glb` / `.fbx`, `textures/` (2 sets x 4096 px: BaseColor,
  Normal, ORM + separate Roughness / Metallic / AO, Emission), `materials/*.tres` (ORMMaterial3D and
  StandardMaterial3D per set), `README_GODOT.md`, `export_report.json`. 80,736 tris in 7 meshes + 1 hull.
- `glb/VEH_TT92_Racing_Car.glb` (stage 4, flat modelling materials - superseded by `godot/` for engines), `renders/`, `presentation/`, `work/s1..s4/` (review renders).

## Reference numbers (last build)
HIGH 96,736 tris (target 40k-100k), LOW 16,798 tris, 250 mesh objects, 8 flat modelling materials (GLB) / 14 painted instances (blend),
bbox 1.802 x 3.341 x 0.836 m, wheelbase 2.128 m, track F 1.32 / R 1.43 m, tyres 0.59 / 0.72 m.
A rebuild must reproduce these exactly.

## Scale and axes
Scale 312.5 px/m from the rear tyre (225 px = 0.72 m); cross-checks: rear track 447 px = 1.43 m,
wheelbase 665 px = 2.13 m. +X = car left, -Y = front, +Z up, origin midway between the axles on
the ground. Top photo: front = image top (the AI cheatsheet shows the car reversed; photo wins).

## The design as built
- **Body**: loft of superellipse sections; three boolean cuts (cockpit, engine bay, nose mouth);
  low tapered wedge nose (tip 0.38 x 0.22 m); the tail tapers to a round face (radius 0.14 m, tail at v 1090).
- **Front** ("old JDM wedge", inspired by a Honda RA300 nose, a riveted hot rod and slim sport-bike
  eyes - inspiration, not copies): wide flat mouth with chrome lip, five chrome slats and an emblem;
  slanted smoked eyes with two round lamps each; red bullet fender mirrors on chrome stalks; dark
  chin spoiler; twin cream stripes from the nose to the engine bay; riveted bonnet seams.
- **Engine**: blown 60-degree V8 in an open bay (blocks, cam covers, Roots blower, four velocity
  stacks, crank-to-blower belt). Invented: no photo shows the engine.
- **Exhaust**: four headers per side into a wrapped side pipe, mirrored left/right. Behind the rear
  axle both pipes sweep inwards and enter ONE jet-style **afterburner** on the round tail face
  (`EXHAUST_AB_*`: chrome can with heat slots + band rings, two rings of converging petals, glowing
  liner (`MAT_GLOW`, emissive), flame-holder cone and teeth). Short: 0.12 m of petals behind the can.
- **Rest**: wire wheels with knock-off spinners, double-wishbone front, transverse coil-over rear,
  leather cockpit, bonnet louvres, filler caps, air filter.

## Uncertain / limits
- No side photo: every height is a design estimate (`BODY_ZTOP/ZBOT`, exhaust, suspension).
- The nose (v < 250 px) and the tail (v > 950 px) no longer follow the top photo - intended.
- Right front suspension is mirrored from the left (`UNCERTAIN_SUSP_Front_*`).
- Faint shading marks remain around the nose mouth (boolean on the subdivided shell).
- Paint: 14 PBR instances of one master material. Only the albedos (and 2 normal maps) are authored;
  roughness, height, AO and 11 normal maps are DERIVED from the albedo (material/README.md). The seat
  leather uses the library set Leather037 (no albedo was supplied). 14 materials exceed the 8-material
  budget of docs/02 - accepted for the render deliverable; the GLB keeps the 8 flat materials.
- Tyres have no tread pattern or sidewall lettering.

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
8. Exhaust redesign from jet / supercar / welded-pipe references: twin afterburners tried, then one centred
   afterburner on the tail; afterburner and body shortened (tail v 1110 -> 1090, petals 0.25 -> 0.12 m).
9. Painting: AI albedos -> 13 seamless 1K PBR sets (texgen.py), master material + 14 instances with
   tri-planar projection and wired normal maps (paint.py, stage 5); workspace moved to stage 6.
10. Game export for Godot 4.x (stage 7): merged meshes, automatic UV atlases (Body 1018-1077 px/m, Mech
    537-565 px/m at 4K), Cycles bakes of the master material, GLB + FBX verified by re-import in Blender
    (not inside Godot - not installed). Mech atlas coverage is only 32 % (many small islands).
