# PROP_TWR_Industrial_Watchtower (TWR)

## Category / targets
- Category: architecture; budget key: `building` (provisional workbench budget).
- Targets: game (S4) and presentation (S5); Godot-compatible GLB.
- Objective: modular industrial steel watchtower with an elevated grated platform, crouch-cover
  sheet guardrails, clear underpass, and a south-facing stair with a ramp-compatible convex collider.

## References and evidence
- No reference photograph, drawing, or target Godot project was supplied.
- Confirmed dimensions from the request: platform footprint 8 x 6 m; walking surface at +6 m;
  guardrail top at +7 m (1.0 m above the deck).
- World axes follow `docs/02_STANDARDS.md`: +Z up, south access on -Y, origin at ground-floor centre.
- There is no photo-derived RefMap, silhouette, or R01/R02 comparison. Dimensions are checked by U01.

## Assumed structural layout
- Four H-section columns at X = +/-3.65 m and Y = +/-2.65 m; perimeter beams and joists carry the
  platform. The underpass remains open apart from the corner supports.
- Steel grating uses a 100 mm nominal pitch and 25 mm bars.
- Guardrail is 1.0 m high overall, with 0.78 m solid sheet panels and a 1.5 m centered opening at
  the south stair head.
- Straight stair width 1.25 m, 32 risers at 0.1875 m, 280 mm treads, and 8.96 m horizontal run.
  It extends south beyond the tower platform; its overall low-mesh bounding box is 8 x 15.1 x 7 m.
- Tread noses are exposed, brighter steel against darker galvanized treads to represent worn edges.
- Section sizes, post spacing, stair dimensions, materials, and all unseen construction details are
  reasonable game-asset assumptions, not source facts.

## Modular part breakdown
| Part | Construction | S4 collision |
|---|---|---|
| Four independent H-section columns | Flanges, web, foot and cap plates | One box per column |
| Perimeter beams and joists | Separate steel beam modules | None |
| Platform deck | Two-layer open grating bars | Box, as the walkable platform surface |
| Guardrails | Sheet panels, posts, and top rails; south stair opening | None |
| Stair flight | 32 discrete treads, stringers, nosings | Convex hull approximates a smooth ramp |
| Stair handrails | Sloped top/mid rails with regular posts | None |

## Stage plan
| Stage | Content | Budget |
|---|---|---|
| S1 PRIMITIVE | Main frame, deck mass, guard panels, stair ramp mass | building S1 max 2k tris |
| S2 LOWPOLY | Modular structural geometry; game LOD0 source | building S2 max 50k tris |
| S3 DETAIL | 2 mm hard-surface bevels, foot bolts, worn tread noses | building S3 max 100k tris |
| S4 GAME | 2048 baked material set, LOD1/2, walkable platform and ramp collider, GLB | building budget |
| S5 PRESENT | Clay and studio-dark presentation sheets | visual inspection |

## Material intent
| Material | Substance | Metallic | Roughness |
|---|---|---:|---:|
| Painted steel | Blue-grey industrial coating (dielectric paint layer) | 0.0 | 0.50 |
| Galvanized steel | Dark steel grating and stair treads | 0.85 | 0.68 |
| Worn step steel | Exposed bright steel at tread noses and fasteners | 1.0 | 0.36 |

The finish is intentionally material-blockout level rather than a sourced weathering texture; no
paint chips, rust distribution, or baked lighting are claimed.

## Deliverables and validation
- Source builders: `parts.py`, `landmarks.py`, `build.py`.
- Outputs: `output/PROP_TWR_Industrial_Watchtower/` stage blends, GLBs, textures, work reviews,
  and presentation renders.
- Measured checks: target dimensions, mesh hygiene, stage drift, game LOD/collision/export checks.
- Visual checks: stage review renders and the S5 clay / studio-dark sheets.
- Not applicable without a reference: photo mask, calibrated silhouette IoU, and reference-pixel p95.
