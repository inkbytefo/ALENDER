# DeLorean Vision — revised brief

The user rejected the reference-matched geometry and explicitly requested original art direction.
This supersedes photographic reconstruction. The previous VEH_DeLorean_DMC12 is retained as an
abandoned version. No source-mask or self-drawn silhouette score is claimed for this concept.

Design: low, wide stainless-steel restomod; flowing quarter panels around circular wheel wells;
one continuous glazed cabin with structural roof and pillars; flush panel joints and integrated
quad headlights; a restrained front splitter, turbine wheels and nine rear engine-cover louvres.
Target dimensions roughly 4.50 x 2.10 x 1.15 m including mirrors; wheelbase 2.63 m.

Stages: S1 masses, S2 engineered solid surfaces and shared UV atlas, S3 small bevels/details,
S4 game LOD/bake/export, S5 clay and dark studio sheets. Geometric hygiene, dimensions,
intersections, budgets, stage drift and exports remain gated. R01/R02 do not apply after the
explicit change of brief. Visual inspection of multiple views is now a primary acceptance check.

Quality priorities: curvature continuity and reflections; no detached window overlays; no
floating fascia/trim; tire-to-arch clearance; clean watertight lowpoly meshes; eight materials.
The asset has closed doors, wheel pivots and a simplified visible cockpit. Hidden drivetrain is not modeled.


## Quality refinement after user critique
The broad lower grille and bulky bright trim were rejected visually. The final direction retains
an angular DeLorean-inspired wedge with restrained fender crown, slim quad lamps, narrow intake,
thin dark glazing seals, turbine alloys and a recessed rear valance. Separate closed door skins
have shallow seats; they are not engineered opening assemblies.

Body longitudinal profiles now use natural cubic splines (continuous second derivatives).
Cross sections use a periodic cubic B-spline; wheel openings are built into a structured quad
strip mesh instead of cylinder booleans. Only the nearly planar front/rear intake recesses use
localized booleans. Body curvature is evaluated through studio reflections and wire review,
not advertised as certified automotive CAD Class-A or an all-quad subdivision control cage.
The cockpit has seats, bolsters, headrests, dashboard, console and steering wheel. Transmission
and thin-wall glass reveal it. Rubber grain, tread channels, metal brushing, wipers, fluted lenses
and hollow exhaust tips supply close details. The shared game atlas is 4096px. The game export keeps the standard single atlas material and uses a tighter 6mm bake cage to
reduce contamination from adjacent trim. The hero retains physical thin-wall glass; the game
atlas uses opaque tinted glazing as an engine-portable approximation.

Research informing this work:
- Autodesk, Continuity G0/G1/G2/G3: https://help.autodesk.com/cloudhelp/2026/ENU/Alias-Video-Tutorials/files/essential-concepts/continuity-g0-g1-g2-g3.html
- Blender, Subdivision Surface and deliberate support loops: https://docs.blender.org/manual/en/3.6/modeling/modifiers/generate/subdivision_surface.html

Validation includes standard gates, a reproducible wire review, S4 against S3 close views,
clay/material sheets, and a second full build with deterministic metric comparison.


Waiver of the generic organic-loft modifier recipe: the automotive body uses explicitly
sampled spline surfaces and structured arch strips rather than a Subdivision modifier over
trimmed fascia topology. It is editable parametric geometry, not a minimal SubD cage. Hard
fittings retain bevel and weighted normals. All geometric gates retain their thresholds.

The game model merges rigid wheel parts, keeping four independent wheel pivots and five
visible meshes. AO is lightly denoised and quantized to 64 levels inside an 8-bit packed ORM
map; roughness, metallic, base color and tangent-normal channels keep their original precision.
S4 uses baked micro-detail, so extreme close views approximate the hero's trim and bevels.


## Completed verification
S1/S2/S3/S4 gates: PASS with zero warnings. Clean full rebuild reproduced every recorded
geometry, hygiene, UV, dimensions and LOD metric exactly (work/clean_rebuild.json).
Triangles: S1 2,764; S2/LOD0 41,900; S3 81,120; LOD1 20,950; LOD2 10,419.
Body topology review: 96.6% quad faces, zero boundary/non-manifold edges. The narrow local
fascia recesses and end caps are triangulated. Five visible game meshes plus six colliders;
4096px maps; the LOD0 package is about 10.24 MiB. Both clay (96 samples) and studio_dark
(192 samples) six-view Cycles sheets were inspected. S4 LOD0/S3 and distant LODs were reviewed.
