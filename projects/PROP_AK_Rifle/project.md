# PROP_AK_Rifle

## Category
prop (hand-held weapon, game asset)

## Objective
Own, licence-clean, game-ready realistic reconstruction of the AKM-pattern rifle in the reference photo
(stamped receiver, laminated wood stock/handguards, polymer pistol grip, ribbed steel 30-rd magazine,
slant muzzle brake). Built 100 % procedurally from our own measurements.

## Licence note (important)
`downloaded_resources/models/ak47blend/AK47.blend` (third-party, licence does NOT allow reuse) was
**studied only** (`wb.py inspect` + a deep read-only analysis, see output/_inspect/AK47/deep/).
No geometry, UVs or textures from it are imported, copied, traced or baked into this asset.
Only generic real-world facts were cross-checked against it (overall length ~0.88 m, part widths).
It is also a different variant (milled AK-47 Type 3 with wooden grip), so it is no shape source.

## Study of the downloaded model (summary)
- 1 object `AK`, 16.3k verts / 15.8k faces (96 % quads), Subsurf L2 in the file -> 501.6k tris
  evaluated: a subdivision *high-poly*, not a game mesh (cage 31.7k tris).
- 96 loose parts in one mesh, symmetric about X=0, real scale 0.888 x 0.071 x 0.263 m, muzzle -Y.
- 1 material, 4K PBR set (base colour, metallic, roughness, normal GL; AO map present but unused),
  texture paths broken (relative to a missing folder). UV: 63 % coverage, ~56 px/cm texel density.
- Widths (for our estimates): receiver 41 mm incl. rails, dust cover 43, lower handguard 41,
  upper handguard 35, stock 44, pistol grip 31, magazine 26.5, gas block 21, front sight 21 mm.

## References
- ref/REAL_REFERENCE.png   primary truth (photo, rotated 90 deg CW from the portrait original
  ref/REF_ORIGINAL_vertical.png)  side: RIGHT (muzzle on image right), 1440x720 px
- ref/REF_MASK.png  photo silhouette, checked by eye (work/ref_mask_check.png):
  `python wb.py mask PROP_AK_Rifle --fill 760,258 745,262 45,408 740,248 815,250`
  (fill points = chrome bolt-carrier glare and butt-plate glare that read as background)
- no cheatsheet.

## Staged pipeline migration (2026-09-29) — reference implementation of docs/01
targets: game (Godot glb) + render. budget key hero_prop. All four stages gate PASS.
Landmarks MEASURED on the photo in v2/v3 (the eye-read v1 values were 3-33 px off, lesson 33):
HG_LOWER_BOT, STOCK_BOT, COVER_TOP (wb.py profile on REF_MASK / 50 % rule), MAG_REAR / MAG_FRONT
(edge rows, arcs least-squares fitted: residual 1.3 / 0.7 px), MAG_FLOOR_LINE (lowest point 851,617).
Added: REAR_SIGHT_POST (missing upright), REAR_SIGHT_BASE bottom 263 -> 268 (no gap in the photo).
Builder fix: FSB_Body is the outline BELOW the ear base (v1 `min()` bug, lesson 37).
Still eye-read: everything else (receiver, grip, controls, barrel radii, gas block, sights).

## Refactor + measurement pass (2026-10-02)
- Code: `parts.py` = builders + registry only, `shapes.py` = geometry helpers (two-edge lofts, domes,
  beads, slant brake), magic numbers moved into `landmarks.py`. Verified with `fingerprint.py`
  (per-object vertex hash of S2/S3): 86/86 objects identical before/after the refactor.
- `measure.py`: left/right edges and interior runs on REF_MASK (complements `wb.py profile`).
- Now MEASURED too: GRIP (+ GRIP_BACK / GRIP_FRONT rails), TRIGGER, TRIGGER_GUARD, MAG_CATCH,
  REAR_SIGHT_*, HG_UPPER_TOP, HG_REAR_CAP, HG_FRONT_BAND, HG_RETAINER (new), GAS_TUBE, GAS_BLOCK,
  BAYONET_LUG, BARREL radii, FSB, BRAKE (kinked front cut), STOCK_TOP, MAG_FLOOR_LINE, RECV_BODY bottom
  front, COVER_BOT rear (gap closed). Photo gate R02 at S3: IoU 0.949 -> 0.973, boundary mean
  2.2 -> 1.1 px, p95 6.0 -> 3.6 px, max 40.8 -> 21.1 px.
- Shape: pistol grip is a rounded loft between its measured edges (was a bevelled plate); buttplate
  ribs / trapdoor / screws sit in the slanted butt plane (were offset along the stock axis).
- Still eye-read: receiver top line, safety lever, charging knob, rivet positions, all X widths.
- Known limit: REF_MASK has no hole for the front-sight aperture and the photo may carry a slight
  perspective (dust cover top falls 7 px, bore 3 px towards the muzzle); proportions follow the photo.

## Perspective rectification + manual dimensions (2026-10-02, second pass)
New references (ref/): `AK-47 AKM Technical Drawings, Russian.pdf` = Soviet AKM/AKMS repair manual
1968 (pages extracted to ref/pdf_pages/, factory side section stitched to REF_SECTION_akm_manual.png),
REF_FOURVIEW_ak47_type3.png (top / left / bottom / right of a milled AK-47: widths only),
REF_EXTRA_* (other variants, detail reference only).
- The photo is NOT a parallel side view: comparing 5 longitudinal stations with the factory section
  shows the butt end drawn ~16 % longer / 7 % taller than the muzzle end. `REF` is now a
  `workbench.refmap.ObliqueRefMap` (pinhole, yaw 10.4 deg, 3 m, principal point right of the cropped
  frame; fit residuals <= 2.2 mm). Landmarks stay in px; the model is rectified:
  stock 241 mm (was 255), receiver 259 (262), receiver front -> muzzle 380 (364), overall 0.880 m.
- Thick parts seen obliquely overhang their mid-plane outline; builders subtract
  `REF.thickness_px(u, hw)` at the butt end, the grip edges and the magazine edges.
- Widths from the manual: receiver 32 mm (stock tenon 28), dust cover 35.5 mm (cover mandrel 34),
  magazine body 22.5 mm at the spine tapering to 17.5 mm at the front (mandrel 21 / 16 x 55 mm).
  From the four-view: butt 40 mm, stock mid 35 mm, lower handguard max 40 mm.
- Cross-checks: front sight post tip 48.5 mm above the bore (spec 48.5); sight radius 364 mm
  (spec 378; the rear notch position in the photo is uncertain). Vertical scale uncertainty ~ +-4 %.
- Gates after the change: S1-S4 PASS; photo gate R02 at S3 IoU 0.966, p95 3.2 px, mean 1.3 px.

## Texture painting (2026-10-02, third pass)
- Sources: 9 AI-made images from the user in `mat/` (2 woods, graphite steel, chipped black enamel,
  stippled polymer, brushed steel, 3 grayscale wear masks; albedo only, 1254 px).
- `texgen.py` (host python) -> 6 PBR sets + masks in `downloaded_resources/materials/AK_*_1K-PNG`
  (Color real; Roughness / Metalness / NormalGL+DX / AO / Displacement DERIVED from the albedo).
  Seam ratios after the cross-fade 0.86-1.04 (WoodLaminateA top/bottom 1.6).
- `paint.py`: the 4 palette materials are instances of `workbench.bl.master` (steel dark = phosphate,
  mostly diffuse; steel bright; lacquered wood with cylindrical grain projection; polymer). Wear:
  Bevel-node edge wear, chip / scratch / grunge masks, cavity dirt. Applied in `after_build(3)`.
- S4 bakes the instances through `master.BakeRouter`: 2048 atlas base / ORM / normal (PNG masters in
  output/PROP_AK_Rifle/textures, ~5.9 MB each); the glb embeds JPEG q92 -> LOD0 3.9 MB.
- Unused but in the library: AK_WoodLaminateB, AK_EnamelBlack (alternative stock / magazine looks).
- Limits: relief maps are luminance-derived approximations; the S3 hero glb carries no textures (node
  groups do not export) - the textured deliverable is the LOD glb; no decals / markings yet.

## Scale & measurements
- (superseded by the rectification above) first pass: scale 1598 px/m from overall length 1406 px (butt-plate heel u=26 -> brake tip u=1432) = 0.880 m
  (AKM with slant brake, fixed stock).
- cross-checks: sight radius 566 px -> 0.354 m @1598 (spec 0.378 m, -6 %: rear notch position
  uncertain); gas tube 30 px = 19 mm (plausible 19-20 mm); barrel 20 px = 12.5 mm (blown-out white
  background erodes thin dark edges -> reads small). Photo scale uncertainty ~ +-6 %.
- photo tilt: 0 deg (barrel centre line v=295 at u=1110..1340 is level).
- origin: bore axis above the trigger (px 572,295) = (0,0,0); muzzle -Y, +X = rifle's left.
- key dimensions: L 0.880 x W ~0.07 (charging handle) x H ~0.255 m (rear sight top -> magazine heel).

## Style / budget
STYLE=realistic_game (first/third-person hero weapon), CATEGORY hero_prop (tables.BUDGETS)
S1 PRIMITIVE < 1.5k   S2 LOWPOLY = LOD0 4k-15k   S3 DETAIL < 60k   materials <= 4
(MAT_STEEL_DARK, MAT_STEEL_BRIGHT (bolt carrier), MAT_WOOD_LAMINATE, MAT_POLYMER)
S4: one baked material MAT_PROP_AK_Rifle_Baked (2048 base / ORM / normal), LOD1 50 %, LOD2 25 %,
convex hulls per part (receiver, barrel, woodwork, buttstock, grip, magazine), Godot naming.

## Part breakdown (primary -> secondary -> tertiary)
| Part | builder | approx size | LOD notes |
|------|---------|-------------|-----------|
| RECV_Body / DustCover / RearSight | plate + two-edge loft | 262 x 32 x 45 mm | bevel+WN |
| BARREL / GasBlock / GasTube / FSB / Brake | lathe + plates | 0.55 m | FSB hole = boolean |
| WOOD_Stock | two-edge loft (slanted butt) | 254 x 44 x 100 mm | subsurf L1 |
| WOOD_Handguard_Lower / Upper | loft | 150 x 40 mm | subsurf L1 |
| GRIP_Pistol | plate + big bevel | 110 x 31 mm | |
| MAG_Body / Ribs / Floorplate | two-edge curved loft + tubes | 180 x 27 mm | |
| CTRL_Trigger / Guard / Safety / MagCatch / ChargingHandle | plates, cyl | small | |
| FASTENER rivets / pins | instanced domes | 3-5 mm | |

## Uncertain / hidden areas
- all widths (X) are estimates (photo is a pure side view): real-world AKM knowledge.
- left side (+X) is not visible: built symmetric except the right-side controls.
- magazine top inside the receiver, internal action: not modelled.
- the rear sight leaf / slider detail is simplified.

## Deliverables
output/PROP_AK_Rifle/blend/PROP_AK_Rifle_S0_SETUP ... _S4_GAME.blend, PROP_AK_Rifle.blend (hero S3)
output/PROP_AK_Rifle/glb/PROP_AK_Rifle_LOD0..2.glb (game), PROP_AK_Rifle_hero.glb (S3), textures/
output/PROP_AK_Rifle/work/s1..s4 (gate + review images), projects/PROP_AK_Rifle/report.json
(older files PROP_AK_Rifle.glb / _game.glb / renders/ are from the legacy two-stage build)
