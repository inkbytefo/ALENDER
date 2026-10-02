# VEH_DeLorean_DMC12

## Objective and authority
Editable reconstruction of the DeLorean DMC-12 concept in the attached AI modeling sheet.
The user explicitly chose: match the sheet side-view shape; printed dimensions are approximate.
There is no independent real photograph. REAL_REFERENCE.png is an unscaled crop of panel f,
not a photo. SOURCE_ATTACHMENT.png preserves the original 1672x941 attachment.
Existing unrelated workspace edits are preserved.

## Targets
Vehicle, hero_vehicle budget, game S4 and hero renders S3/S5. Godot glTF convention from
the existing scaffold; no engine-specific runtime testing promised. Maximum 8 materials.

## S0 measurements
Source crop: (515,72)-(1040,235), 525x163 native pixels. Left side visible; front faces left.
Scale: 508 px / approximate 4.213 m = 120.579159744 px/m. Front axle (114,112), rear (415,113).
Anchor front axle: Y=-1.248142717 m, Z=0.298559055 m. Zero in-plane roll; orthographic camera.
Cross-checks: wheelbase 2.4963 m vs printed 2.410 m (+3.58%); height 1.1362 m vs 1.140 m
(-0.33%); front tire .5971 m vs .590 m (+1.21%); rear tire .5805 m vs .663 m (-12.44%).
Shape priority means the rear tire is intentionally NOT enlarged to the printed size.
Width 1.856 m and tracks 1.590/1.588 m are approximate depth assumptions, not verified facts.

prepare_reference.py measures strong normal gradients within inspected +/-2 px edge windows.
Mask overlay inspected at 3x. Floor shadow excluded. Thin rear antenna is below primary
outline resolution and added only as S3 detail. Roof/fender/belt/window outlines read on the
labelled 3x crop; measured whole silhouette retained in measurements.json and landmarks.py.

## Plan / phase checklist
- [x] S0: preserve source, crop, inspect measured mask, record scale conflicts and user choice
- [ ] S1: primitive masses, gate PASS, inspect silhouette diffs and orthographic views
- [ ] S2: actual hard-surface wedge, wheel arches, turbine rims, UV atlas, gate PASS
- [ ] S3: bevel and weighted normals, seams, lamps/louvres, inspect hero, gate PASS
- [ ] S4: bake, LODs, collision, pivot hierarchy, game exports, gate PASS, compare S3/LOD0
- [ ] S5: inspect clay and studio_dark sheets; clean rebuild reproduces gate metrics

## Registry
body, cabin, hood, glass, bumpers, splitter, skirts, diffuser, louvres, mirrors,
trim, lamps, wheels, underbody. Each stage uses the same builders with a stage profile:
S1 low-segment coarse wheels/no spokes or small details; S2 clean unbeveled solids;
S3 bevel + weighted normals. Wedge bodywork is hard surface and never subdivided.
Wheel tire objects pivot at axles; rim, hub, recess, spokes and lugs parent to each tire.
Static closed gull-wing door seams; no opening animation or exposed door interior.

## Uncertainty and limitations
UNCERTAIN_Underbody, UNCERTAIN_Interior, UNCERTAIN_BodyWidths,
UNCERTAIN_RearEngineBay, UNCERTAIN_DoorHingeDepth. Opaque tinted glazing hides an
unmodeled cockpit; no hidden engine or suspension invented. Bilateral symmetry assumed.
No badges/logos or license plate text. Fidelity is to a concept sheet, not a surveyed stock car.

## Deliverables
output/VEH_DeLorean_DMC12/blend: S0-S4 milestones, final editable blend, presentation blend.
output/VEH_DeLorean_DMC12/glb: hero and LOD0-2; textures: baked base/ORM/normal.
output/VEH_DeLorean_DMC12/work/s1-s4: reviewed overlays, diffs and orthographic renders.
projects/VEH_DeLorean_DMC12/report.json: stage gates and limitations.
