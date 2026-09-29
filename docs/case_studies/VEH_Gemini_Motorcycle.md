# Case study — VEH_Gemini_Motorcycle (custom Honda inline-4 street bike)

Source: `projects/VEH_Gemini_Motorcycle/` · rebuild: `python wb.py build VEH_Gemini_Motorcycle`
Result: PASS · LOW 135 objects / 9.8k tris · HIGH 192 objects / 65.5k tris · 8 materials ·
0 critical intersections · GLB round trip 193/193 · reference-camera anchor error 0 px.

## Inputs
- `ref/REAL_REFERENCE.png` 1080×720 side photo (bike on a rear paddock stand, brick wall).
- `ref/MODELING_CHEATSHEET.png` AI-generated sheet (blockout colours, orthos, exploded view,
  ~2050 × 1050 mm, wheelbase ~1400 mm). Used for decomposition only.

## Reference analysis (numbers)
| Item | Value | How |
|------|-------|-----|
| side shown | RIGHT (front on image right) | camera at −X |
| scale | 400 px/m | rear tyre 250 px / 0.63 m, front 240 px / 0.60 m |
| cross-checks | length 820 px = 2.05 m, height 418 px = 1.045 m | matched cheatsheet |
| axles px | front (853,496), rear (276,470) | 3× crops |
| pitch | 1.98° nose-down | rear axle 65 mm higher in photo vs 15 mm at rest |
| wheelbase | 1.444 m | after pitch removal (cheatsheet said ~1.40 — photo wins) |
| rake | 22° | fork line through axle + top clamp (±1°, fork edge hard to read) |
| seat height | 0.80 m | seat top polyline |

## Build sequence and what each gate caught
1. Wheels only → overlay: tyre outlines within 2–3 px of the photo. ✔
2. Full LOW → overlay good on tank/tail/fork/exhaust; orthos plausible. Largest mismatches fixed:
   empty gap under tank (added UNCERTAIN airbox), engine one box (split block/head), reservoir
   stems like antennae, hump too wedge-like, black review background.
3. Intersections (9 hits) → split crankcase vs narrow transmission, intakes converge into airbox,
   shortened uncertain downtube, airbox narrowed, transmission moved off pivot shaft. → 0 hits.
4. HIGH v1 → 114k tris + false intersections + vanished engine plates (subsurf on plates).
   Fixes: world-space BVH, hard-surface policy, subsurf L1/L2. → 65k tris, 0 hits.
5. Visual pass → fins inset/proud, flatter chamfered covers, tighter perspective cams.

## Techniques worth reusing
- Photo tank paint split → **boundary-aware loft** with recessed black flank + creased red lip.
- Fork/steering geometry from rake + one measured point (`parts.steering()`).
- Exhaust headers pushed radially off the front tyre (clearance), converging to a collector.
- Chain loop from two sprocket half-circles; shock spring via `mesh.helix`.
- Fasteners as linked duplicates of 5 family meshes.

## Uncertain (tagged)
`UNCERTAIN_ENGINE_Airbox`, `UNCERTAIN_FRAME_Downtube_L/R`, `UNCERTAIN_FRAME_Crossmember_0/1`,
`UNCERTAIN_ENGINE_Cover_*_L`, `UNCERTAIN_BODY_Tank_FillerCap`, shock mount points, chain side.
