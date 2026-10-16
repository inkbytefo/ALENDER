# PROP_Cyberpunk_Utility_Blade

## Category / targets
- Category: prop; budget key: `small_prop`
- Targets: S1 primitive, S2 low-poly, S3 detailed hero, S4 game-ready GLB, S5 studio presentation
- Engine export profile: Godot/glTF (engine-side import is pending unless Godot is available)
- Style: original compact cyberpunk utility tool; hard-surface, restrained neon accent
- Source: deterministic procedural Python in this project; no external geometry or textures

## Objective
Create an original compact, hand-held utility blade prop with a faceted metal blade, guarded grip,
warm polymer scales, and narrow cyan visual inlays. This is a fictional design concept, not a
reconstruction of a specific existing product or asset.

## Original concept assumptions and measurements
- Overall target dimensions: **0.030 m X thickness × 0.240 m Y length × 0.053 m Z height**.
- Axes: Blender +Z up, -Y forward (blade tip), +X object's left.
- Origin: grip-origin at the hand-held center reference station; not a world-grounded prop.
- Concept scale map: 1600 design-pixels/m; side-view target extents u=80..464 = 0.240 m.
- Side silhouette is authored in `landmarks.py` solely as an original concept target to make R01
  measurable. It is not photographic evidence. No photo, mask, or measured source scale exists.
- Side profile designed proportions: grip approx. 0.10 m; exposed blade approx. 0.14 m.
- Stage target dimensions above are assumed concept values; U01 checks the procedural model against
  these declared targets, not against a real-world object.

## References / evidence
- No reference photo or external design reference is used.
- `ref/CONCEPT_TARGET.png` is generated from `landmarks.py` only to establish render framing; it
  is a visualization of the same authored target, not an independent source.
- R01 compares geometry to the authored concept silhouette.
- R02 photo-mask comparison is not applicable: no photo/mask is present.
- External raw asset folder: license/permission proof was not established; it is explicitly excluded.
  No files from it were inspected, read, imported, measured, traced, or used.

## Stage plan
| Stage | Content | Budget |
|---|---|---:|
| S1 PRIMITIVE | Simplified blade, handle, guard and grip masses | ≤ 300 tris |
| S2 LOWPOLY | Faceted plates, grip scales, inlays and UV atlas | 300–2,000 target; 3,000 max |
| S3 DETAIL | Bevels and small grip fasteners; hero/bake source | ≤ 5,000 tris |
| S4 GAME | 512 px baked maps, LOD0–2, convex part colliders, GLB | small_prop profile |
| S5 PRESENT | Clay and studio-dark sheets | visual deliverable |

## Part breakdown
| Part key | Primary group | Collision | Notes |
|---|---|---|---|
| blade | BLADE_Main | hull | Flat faceted silhouette; two cyan side channels |
| frame | FRAME_Handle, FRAME_Guard | hull | Compact grip shell and short finger guard |
| grip | GRIP_Scale_R/L | hull | Contrasting scales, insets and cosmetic fasteners |

## Uncertain / intentionally omitted
- Every dimension, outline, color, and proportion is a design assumption rather than a measurement.
- Cross-section, actual hand fit, ergonomics, edge profile and material specification are unverified.
- Internal lock, deployment mechanism, pivot, and functional blade geometry are intentionally omitted.
- The hidden blade-root/guard junction is an intentional overlap, treated as a tang seated in the
  guard; `CRITICAL_PAIRS` checks blade-to-grip clearance instead.
- No claim is made that this is a functional or safe real-world tool; it is a fictional visual prop.

## Validation notes
- `TARGET_DIMS` are declared concept targets; dimensional gates verify builder consistency only.
- `GROUND=False` because this is hand-held and the grip-origin is the chosen origin.
- Silhouette/pixel results are synthetic concept conformance, not reference accuracy.
- No shared workbench or documentation code is needed or changed for this asset.

## Deliverables
Generated files belong only under `output/PROP_Cyberpunk_Utility_Blade/`. Source belongs only
under `projects/PROP_Cyberpunk_Utility_Blade/`.
