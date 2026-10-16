# VEH_Vision_V2 — Independent Stainless GT Concept

## Scope and targets
- Category: `hero_vehicle`; budget: provisional Workbench hero-vehicle budget.
- Targets: game-ready GLB package and presentation renders.
- Engine convention: Godot-compatible glTF; no Godot version/project was provided.
- This is an original fictional vehicle concept, not a reconstruction or copy of a specific production car.
- Source project `VEH_DeLorean_Vision` and its outputs are retained unchanged.

## Design brief
Create a coherent, high-quality retro-futuristic stainless GT coupe using an original silhouette:
a long soft-edged bonnet, raised arched greenhouse, short fastback tail, curved wheel arches, narrow
side glazing, seven-blade alloy wheels, round projector headlamps, and a slim rear light bar.
No brand badges, logos, vehicle-specific signature details, or copied factory proportions are used.
The doors are conventional, closed, and static.

## Evidence and dimensions
- No reference photograph, drawing, or product-specific measurements were supplied or used.
- `landmarks.py` contains authored design coordinates in metres; these are concept targets, not
  measured vehicle facts.
- Target envelope: 2.04 m wide x 4.45 m long x 1.28 m high; wheelbase 2.70 m.
- Origin: midpoint between axles on the ground; +Z up, -Y forward; wheel centres at +/-1.35 m Y.
- The empty `ref/` folder is intentionally left without an invented reference image. R01/R02 photo
  silhouette metrics are not applicable and are not claimed.

## Construction plan
| Part | Construction | S4 collision |
|---|---|---|
| Outer shell | Interpolated cross-section loft with integrated wheel-arch rise | Convex hull |
| Cabin | Separate arched roof-and-pillar loft, with opaque tinted glazing panels | Convex hull |
| Four wheels | Lathed tyres, alloy rims, swept spokes, hub and rotor | One hull per wheel |
| Fascia | Recessed intake, round projectors, thin tail lamp and bumpers | None |
| Side details | Closed-door seams, mirror housings, rocker trim, shoulder line | None |
| Undertray | Simplified hidden floor plate | Box |

## Materials
| Material | Intent | Metallic | Roughness |
|---|---|---:|---:|
| Stainless | Brushed stainless body shell and roof | 0.96 | 0.27 |
| Alloy | Machined wheel faces and fine trim | 0.93 | 0.24 |
| Trim | Dark, non-metallic bumper and seals | 0.00 | 0.38 |
| Glass | Opaque, blue-charcoal tinted glazing for portable baking | 0.00 | 0.17 |
| Rubber | Low-gloss tyre rubber | 0.00 | 0.84 |
| Headlamp | Cool-white projector lens with restrained emission | 0.00 | 0.20 |
| Taillamp | Deep red light strip with restrained emission | 0.00 | 0.24 |
| Amber | Small marker lenses | 0.12 | 0.30 |

The baked game maps use Base Color (sRGB), ORM (R=AO, G=roughness, B=metallic; Non-Color), and
tangent-space normal (+Y/OpenGL; Non-Color). Procedural surface relief is subtle and only added to
the S3 source material.

## Uncertain areas and limitations
- Hidden drivetrain, suspension, structure, and detailed interior are intentionally omitted.
- The glazing is opaque rather than transmissive to keep the baked glTF material predictable.
- Dimensions and body sections are original visual-design choices; they do not describe a real car.
- No Godot project/version is available, so engine import remains pending unless the runtime is found.

## Verification and deliverables
- Run the standard S1-S4 stage gates, then inspect all orthographic and perspective review views.
- Compare S4 LOD0 and distance LODs visually; check exported GLB materials, bounds, collisions, and
  texture channel semantics.
- S5 clay and studio-dark presentation sheets are required and must be visually inspected.
- Source is `parts.py`, `landmarks.py`, and `build.py`; generated output lives under
  `output/VEH_Vision_V2/`.
