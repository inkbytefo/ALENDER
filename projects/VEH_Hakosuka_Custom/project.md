# VEH_Hakosuka_Custom

Category: vehicle. Budget: hero_vehicle. Target: realistic game GLB plus studio presentation.
Engine unspecified; no engine-specific acceptance claimed. Maximum 8 materials.

Status: S1 built, gate FAIL. S2-S5 pending.

## Verified dimensions and S1 evidence

The initial intake scale blocker is resolved. Nissan Heritage confirms KPGC10 factory
4330 x 1665 x 1370 mm, wheelbase 2570 mm, front/rear track 1370/1365 mm.
Source: https://www.nissan-global.com/EN/HERITAGE_COLLECTION/skyline_hardtop_2000gt-r.html
The user's 1364 mm rear track differs by 1 mm; use manufacturer 1365 mm.
FACTORY_BLUEPRINT.png saved unchanged. Original real-photo montage remains primary truth.

Blueprint eye-read hub centres (221,280), (665,280): scale 444/2.570 = 172.762646 px/m.
Cross-checks on drawing (not measurements of the modified car):
- Approximate overall span x76..841: 765px = 4.428 m; +2.27% versus factory length.
- Roof y99 to ground y332: 233px = 1.349 m; -1.56% versus factory height.
- Front-view width x911..1201: 290px = 1.679 m; +0.82% versus factory width.
Drawing is approximate, not metrology. Modifications invalidate a stock overall-width target.

Nine approximate photo correspondences fit a 40.386 mm pinhole camera; mean error
12.590 px, max 19.360 px. Calibration remains too approximate for final reconstruction.
Photo contour manually traced and visually inspected in ref/MASK_CHECK.png.
REF_MASK and R01 share the traced contour; R02 is NOT an independent segmentation proof.
The manual contour uncertainty is estimated at 2-4px, not measured. Thresholds unchanged.
Camera fit, trace and source pixels remain editable in calibrate.py and landmarks.py.

Six S1 correction passes completed. Photo R02 IoU/p95 progression:
1: .846 / 41.0px; 2: .908 / 22.0px; 3: .930 / 15.0px;
4: .933 / 14.1px; 5: R02 passed but R01 failed; 6: see report.json, R02 fails.
Changes addressed front body profile, greenhouse rear slope, wheel placement, mirror
height, bumper and lip masses. No acceptance threshold or severity changed.
Stop at the workflow's six-pass cap. S2-S5 NOT BUILT; no game-ready delivery claimed.

Primitive model has solid greenhouse and proxy rims; windows, panel seams, true wheel
spokes, interior, fine lamps and detailed trim are not yet reconstructed. Width 1.9m
includes estimated flares. Only primary front-right photo is gated; other views are
visual references, not multi-view silhouette acceptance.

Library addition: calibrated camera transform/lens and selectable reference crop.
Smoke test ALL PASS including optical-axis reprojection 0.0px. Regression command
could not compare: tests/regress_baseline.json absent. No synthetic baseline created.
Next work: jointly refine camera correspondences and lip/body profiles; inspect all
three original photos before another correction batch. Preserve the current failed gate.

## Identity
Two-door greenhouse, long hood, short deck, four round headlights, split grille,
paired rear lamps, black bolt-on flares, deep-dish rims, low stance, fender mirrors,
chrome bumpers, front lip and raised rear spoiler. Photo overrides all drawings.

## Stage checklist
- [x] Save sources and obtain physical scale.
- [ ] S0: refine camera fit and independently validate mask.
- [ ] S1: pass photo gate.
- [ ] S2: real panel/window/wheel builders and shared UV atlas.
- [ ] S3: detail, smoothing policy and drift checks.
- [ ] S4: bake, LODs, collision, export/reopen and visual checks.
- [ ] S5: clay/studio_dark presentation and clean rebuild.

## User-authorized design variation (2026-09-30)
User permits approximately 15% creative departure from the reference design.
Interpretation: limited secondary design changes, not 15% global scale error or
an automatic numerical silhouette tolerance. Preserve wheelbase, two-door body,
greenhouse and quad-headlight identity. Design freedom: wheel spoke pattern,
front lip section, grille treatment and spoiler detailing. Do not weaken gates.
Each intentional deviation will be recorded separately from unresolved errors.
User also authorized a fresh correction batch after the earlier six-pass report.
