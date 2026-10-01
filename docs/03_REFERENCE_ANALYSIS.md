# 03 — Reference analysis: turning photos into metres

The model is only as good as the numbers you read off the photo. Spend real time here.

## 1. Look properly
```bash
python wb.py grid projects/<A>/ref/REAL_REFERENCE.png            # labelled 20 px grid
python wb.py crop projects/<A>/ref/REAL_REFERENCE.png 140 320 440 630 --scale 3   # zoom a region
```
- Crop **every** region you model (3–4× zoom, labels every 10 px, red line every 50 px).
- Read edges from the zoomed crop, not from the full image. Log the numbers in `landmarks.py`
  with a comment saying what they are.
- Silhouettes: polylines of (u, v) along the top edge and bottom edge of each volume,
  rear → front. Key points: axles, pivots, joints, corners, lamp centres.

## 1b. Measure instead of reading (lessons 33–35)
Eye-read edges on the AK were off by 3–33 px (lacquer highlights taken as edges, arcs guessed).
When the edge is measurable, let code measure it:
```bash
python wb.py mask <A> [--fill U,V ...]              # plain LIGHT background -> ref/REF_MASK.png
#   threshold + flood fill from landmarks.ANCHOR_PX + local 50 % rule on the edge band + small
#   holes filled; --fill forces glare regions (chrome) closed. LOOK at work/ref_mask_check.png.
python wb.py profile <A> U0 U1 V0 V1 --side top|bottom [--step 8] [--tol 1.5]
#   the mask's top/bottom edge in a window -> simplified px polyline to paste into landmarks.py
python wb.py profile <A> ... --photo-thr 150         # same on the raw photo (global 50 % threshold;
#   only for dark objects on white - lit grey metal needs the mask's local rule)
python wb.py snap <A> <LANDMARK> [--radius 6]        # second opinion on any photo: strongest edge
#   along each vertex normal (yellow = suggestion, red = no clear edge) - suggestions, not truth
```
- The **50 % rule**: an edge is where the intensity crosses half-way between object and background.
  Highlights (top of the transition) and haze/shadow (bottom) are both wrong by 2–8 px.
- Circular arcs (magazine spines, wheel arches): sample the edge rows, fit a circle by least squares
  (residual ≤ 2 px) and store centre + radius; record the residual in a comment.
- Write in a comment next to each landmark whether it was measured (command + window) or read.
- `landmarks.SILHOUETTE` = closed polygons of every visible part; gate R01 compares the model with
  their union, gate R02 with `REF_MASK.png`. R01 PASS + R02 FAIL ⇒ the landmark is wrong.

## 2. Which side is visible?
Front on image **right** ⇒ you see the object's **RIGHT** side (−X) ⇒ reference camera at −X,
`RefMap(front_is_right=True)`. Parts seen in the photo live on −X (exhaust, visible covers);
the far side is `UNCERTAIN_` unless symmetry is certain. (Mistake to avoid: assuming "left".)

## 3. Scale (px per metre)
Pick the most reliable known real dimension and **cross-check with two others**:
| Object | Known dimension |
|--------|-----------------|
| motorcycle | tyre ⌀: 120/70-17 ≈ 0.600 m, 180/55-17 ≈ 0.630 m, 190/50-17 ≈ 0.622 m; rim 17" = 0.432 m |
| car | tyre ⌀ 0.60–0.75 m (205/55R16 = 0.632 m), door handle height ≈ 1.0 m |
| building | door 2.0–2.1 m tall, 0.9 m wide; storey 2.8–3.2 m; step 0.17–0.19 m; brick course 75 mm |
| human | height 1.60–1.90 m (default 1.75), head ≈ 1/7.5 of height |
| furniture | table 0.75 m, seat 0.45 m, counter 0.90 m |
Formula: `S = measured_px / real_m`. Tyre diameter: measure top-to-bottom of the tyre (not rim).
Gemini example: rear tyre 250 px / 0.63 m and front 240 px / 0.60 m → 400 px/m; cross-check:
overall length 820 px = 2.05 m, height 418 px = 1.045 m — both matched the cheatsheet.

## 4. Tilt / pitch / perspective
- Objects on stands, slopes, jacks, or a rolled camera are rotated in the photo. Find two points
  whose true height difference you know (e.g. axles: rear-tyre radius − front-tyre radius) and use
  `refmap.pitch_from_two_points(px_front, px_rear, rest_dz, S)` → (theta, true distance).
  Gemini: rear wheel on a paddock stand → 1.98° nose-down; ignoring it would tilt every part.
- Side photos from 5–10 m are near-orthographic; `cameras.reference_camera` uses a long lens at
  7 m, so the X = 0 plane maps exactly and parts at ±0.2 m depth err by a few px only.
- Wide-angle/close photos: measure only near the object's centre plane, prefer the cheatsheet
  orthographic views for proportions, and flag it in `project.md`.

## 5. Anchor and RefMap
Choose one well-defined point (front axle, a foot, a building corner at ground level), measure its
px and define its world (Y, Z). `REF = RefMap(S, anchor_px, anchor_yz, theta, front_is_right)`.
Then `REF.P(u, v)` → (Y, Z), `REF.P3(u, v, x)`, `REF.photo_of(y, z)` → px (for overlays).
Verify immediately with a host-side print: the anchors must round-trip to their pixels.

## 6. Depth (X) — the invisible dimension
A side photo never shows width. Sources in order: second photo (front/top) → cheatsheet
top/front views → standard construction (engine widths, tyre widths, door thickness) →
conservative guess. Keep widths in named constants/tables (`TANK_HALF_WIDTH = [(u, m), ...]`)
so they are easy to correct, and tag guessed parts `UNCERTAIN_`.

## 7. Paint and material boundaries
If the photo shows a hard colour split that follows the surface (e.g. red shell over a black
recessed flank), measure that boundary as its own polyline — it is geometry (edge loop +
crease + material index), not decoration. Logos/decals are not modelled.

## 8. What to write down (in landmarks.py docstring)
side shown · scale & derivation · cross-checks · tilt & why · anchor · uncertain regions.
