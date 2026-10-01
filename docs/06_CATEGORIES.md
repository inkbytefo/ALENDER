# 06 — Category playbooks

Each section: what to measure, part breakdown (primary → secondary → tertiary), typical sizes,
critical intersection pairs, pitfalls. Use together with 01 (process) and 04 (builders).

---
## Motorcycles  (proven: `case_studies/VEH_Gemini_Motorcycle.md`)
**Measure**: both axles, tyre top/bottom, swingarm pivot, fork line (2 points), top clamp,
headlight centre & face, grips, tank top/bottom polylines, seat/tail polylines, engine polygons
(crankcase, cylinder bank as tilted quad, head, covers as circles), exhaust centreline, muffler ends.
**Scale**: tyre sizes (docs/03 table). **Tilt**: paddock stands lift the rear → pitch.
**Breakdown**: wheels (tyre lathe, rim lathe, hub, spokes) → frame (tubes + pivot plates) → tank
(loft) → seat/hump/tail (lofts) → engine (plates + lathe covers + carbs) → front (fork tubes along
rake, clamps, headlight lathe, clip-ons) → rear (swingarm plates, shock + helix spring, chain loop)
→ exhaust (tubes with clearance) → rearsets, calipers, discs → fasteners, fins, lines.
**Typical**: wheelbase 1.35–1.55 m, rake 22–27°, seat 0.78–0.85 m, bars width 0.65–0.80 m,
fork tube spacing ±0.10 m, rear tyre 0.18 m wide, front 0.12 m.
**Pairs**: exhaust↔frame, headers↔front tyre, rear tyre↔swingarm, fork↔tank, bars↔tank,
engine↔frame, shock↔side panel, muffler↔rear tyre, chain↔tyre.
**Pitfalls**: see case study — generic café-racer drift, wrong side, stand pitch, gearbox width.

## Cars
**Measure** (side photo): both wheel centres & tyre ⌀, roof line, belt line (window bottom), sill,
bonnet/boot lines, A/B/C pillar lines, wheel-arch arcs, bumper profiles, lamp outlines.
Front/rear photo: track width, body width, greenhouse tumblehome. Top view if available.
**Breakdown**: wheels ×4 → body shell as `loft_rings` from side silhouette + width tables per station
(or plan-view outline × side outline) → greenhouse/glass → arches (boolean or shaped loft) →
bumpers, lamps (lathe/plates), mirrors, handles → grilles (multi_cyl / extrude_polys), badges skipped.
**Typical**: sedan 4.6×1.85×1.45 m, wheelbase ≈ 58–62 % of length, ground clearance 0.12–0.18 m,
arch gap 2–4 cm around the tyre, glass 4–6 mm.
**Pairs**: tyre↔body (arches), glass↔body frames, bumper↔body. Origin: axle midpoint on ground;
wheels pivot on their axle centres; doors on hinges (−Y edge).
**Pitfalls**: side-photo perspective exaggerates the near wheel — use the far-away long lens rule;
build one symmetric half with `mods.mirror_x` then apply.

## Architecture (buildings, rooms, modular kits)
**Measure**: storey lines, window/door grid (sill, head, jambs), roof pitch & overhang, wall thickness
at openings, stair rise/run, facade setbacks. Scale from doors (2.0–2.1 m) and brick courses.
**Breakdown**: footprint + storey slabs → walls (`box`, 0.25–0.35 m exterior) → openings
(`mods.boolean(apply=True)` with cutters, or build walls around openings) → roof (plates/lofts) →
windows (frame plates + glass) → stairs/rails (box arrays, tube rails) → trim, gutters, details.
**Modular kits**: 1 m grid (0.5 sub-grid), pieces 1/2/4 m wide × 3 m high, pivots on a shared rule
(bottom-left or bottom-centre for the whole kit), edges exactly on grid (±1 mm).
**Pairs**: window glass↔wall, door↔frame, stairs↔slab. Materials by function (plaster, brick,
glass, wood, metal) ≤ 6. Repeating bricks/tiles are texture, not geometry.

## Characters & creatures
**Measure** (front + side photo or turnaround sheet): height, head size, shoulder/hip widths,
joint heights (knee, hip, elbow, wrist), limb thickness at joints.
**Breakdown**: joint graph (`rig.HUMANOID_JOINTS` scaled to height) → `rig.skin_body()` volume
blockout (S1) → proportions check front/side (R01) → refine: separate head/hands, sculpt-like lofts
per limb (`loft_rings` with elliptical sections along bone axes) → clothing as separate meshes →
`rig.armature(HUMANOID_BONES)` → `rig.bind_auto()` → test poses via `rig.pose_key`.
**Typical**: 1.75 m adult, ~7.5 heads, T- or A-pose, facing −Y, origin between the feet.
**Budget**: 15k–40k tris hero; hands ≤ 10 % of budget; quad-dominant where it bends.
**Pitfalls**: realistic faces are out of scope for procedural code — stylise or use a base mesh;
check deformation with 4 test poses (arm up, knee bent, crouch, head turn).

## Props (furniture, weapons, tools, containers)
**Measure**: bbox from a known size; profile for turned parts (lathe), outline for flat parts (plate).
**Breakdown**: primary volume → functional sub-parts (handles, hinges, lids) → bevels → fasteners.
Budget 0.5k–10k. Origin bottom-centre (on the floor) or grip point (hand-held).

## Environments / scenes
Block the layout with boxes on a grid first (S1 PRIMITIVE), camera(s) placed early, then refine hero
assets individually as their own projects and link/append them. Keep ≤ 3 hierarchy levels.
