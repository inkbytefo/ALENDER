# VEH_Honda_NSX_Widebody

Category: vehicle. Budget: hero_vehicle. Target: game asset (Godot GLB, LOD0-2 + hero) + studio presentation.
Subject: red widebody Honda NSX (NA1-style) with GT wing, deep-dish black wheels, front splitter.

## Sources (priority photo > cheatsheet)
- `ref/REAL_REFERENCE.png` 1080x1350 front 3/4 perspective photo (identity, widths, details). Perspective => NOT
  usable as an orthographic gate image without a camera fit (not done).
- `ref/MODELING_CHEATSHEET.png` AI sheet. Panel 4 side drawing cropped 4x -> `ref/REF_SIDE_BLUEPRINT.png`
  (`intake.py` reproduces crop + `REF_MASK.png` by colour segmentation). R01/R02 gate against this drawing
  with an ORTHOGRAPHIC reference camera (new `REF.ortho = True` flag in `workbench/bl/cameras.py`).

## Scale and known facts
- Wheelbase 2.53 m = 1157 px between measured axle centres -> 457.3 px/m. Axle height 0.31 m.
- Sheet text claims L 4.40 / H 1.15 / W 2.00 (arches) / body 1.82 / track 1.68. The drawn car measures
  4.27 x 1.06 m at the wheelbase scale: the drawing was followed (it is what the silhouette is), widths from the
  sheet. Model bbox 2.00 x 4.26 x 1.06 m. Mismatch vs the sheet text: length -3 %, height -8 %.

## Result
S1 PASS, S2 PASS, S3 PASS, S4 PASS (`python wb.py gate VEH_Honda_NSX_Widebody`). Numbers in report.json.
Silhouette IoU ~0.98 on the side drawing for every stage.

## Uncertain / limitations
- UNCERTAIN_BodyWidths: all X widths (side drawing cannot show them): body 1.83, arches 2.0, cabin belt 1.6, roof 1.04.
- UNCERTAIN_Underbody, UNCERTAIN_Interior (2 seat blocks + dash), UNCERTAIN_Exhaust, UNCERTAIN_WingEndplates (width).
- Photo is only checked visually (not by gate); front fascia, hood pop-ups and lamps are simplified blocks.
- Body is one lofted shell (superellipse sections): no panel gaps/door cut-outs beyond a seam tube; glass is
  opaque dark; no real interior; wing cross-section is flat plate.
- Wheel hole in side silhouette is closed by a backing disc (WHEEL_Dish) - gate counts holes.
- Bake artefacts (S4): slight jagged highlights on curved panels (AO/normal bake at 2k).

## Library change made
`workbench/bl/cameras.py` `reference_camera`: honours `REF.ortho` (orthographic reference camera for drawings;
a perspective camera at 7 m distorted a 2 m wide car by 16 %). Smoke test not re-run yet.
