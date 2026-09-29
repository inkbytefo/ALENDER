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
- no cheatsheet.

## Scale & measurements
- scale: 1598 px/m from overall length 1406 px (butt-plate heel u=26 -> brake tip u=1432) = 0.880 m
  (AKM with slant brake, fixed stock).
- cross-checks: sight radius 566 px -> 0.354 m @1598 (spec 0.378 m, -6 %: rear notch position
  uncertain); gas tube 30 px = 19 mm (plausible 19-20 mm); barrel 20 px = 12.5 mm (blown-out white
  background erodes thin dark edges -> reads small). Photo scale uncertainty ~ +-6 %.
- photo tilt: 0 deg (barrel centre line v=295 at u=1110..1340 is level).
- origin: bore axis above the trigger (px 572,295) = (0,0,0); muzzle -Y, +X = rifle's left.
- key dimensions: L 0.880 x W ~0.07 (charging handle) x H ~0.255 m (rear sight top -> magazine heel).

## Style / budget
STYLE=realistic_game (first/third-person hero weapon)
Stage 1 LOW: < 6k tris   Stage 2 HIGH: 20k - 45k tris   materials <= 4
(MAT_STEEL_DARK, MAT_STEEL_BRIGHT (bolt carrier), MAT_WOOD_LAMINATE, MAT_POLYMER)

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
output/PROP_AK_Rifle/blend/PROP_AK_Rifle_00_SETUP ... _05_FINAL_GEOMETRY, PROP_AK_Rifle.blend
output/PROP_AK_Rifle/glb/PROP_AK_Rifle.glb, output/PROP_AK_Rifle/renders/, projects/PROP_AK_Rifle/report.json
