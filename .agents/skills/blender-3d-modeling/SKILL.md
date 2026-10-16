---
name: blender-3d-modeling
description: Build, correct, retopologize, and validate reference-faithful 3D assets in Blender 5.2+ through primitive blockout, low-poly and high-poly stages, UV/bake preparation, LODs, collision, and Godot/glTF export. Use for photo-to-model tasks, hard-surface or organic modeling, silhouette/proportion fixes, game-ready meshes, and non-destructive mesh workflows. Pair with blender-python-api for automation and texture or animation skills for those domains; do not trigger for image-only illustrations or unrelated 3D theory.
---

# Blender 3D Modeling

Produce editable geometry whose fidelity and game suitability can be inspected. Reply in the user's language; keep code and technical identifiers consistent with the project.

## Establish the contract

1. Inspect supplied photos, drawings, existing scene, and project instructions. Treat real photos as primary evidence; a generated cheatsheet is a secondary interpretation. Preserve specific asymmetries, orientation, accessories, and proportions. Do not redesign without a request.
2. Detect Blender with `bpy.app.version_string` and `bpy.app.version` through available Blender tools, or `blender --version`. Record exact runtime and target engine/exporter. Target Blender 5.2+, but verify each later minor release separately. Do not silently upgrade or use development documentation as stable API evidence. Read [sources](references/sources.md) to resolve relevant official documentation and release changes before scripting.
3. Establish deliverables, target views/camera distance, animated versus rigid use, real-world units, existing material/UV constraints, and hardware constraints. Derive polygon, texture, draw-call, and LOD budgets from the project; if unavailable, label provisional assumptions instead of declaring universal AAA budgets.
4. Save a working copy/checkpoint. Inventory original objects, collections, meshes, modifiers, shape keys, materials, and external assets. Operate only on the asset scope; never clear the user's scene for convenience.

If Blender tools are available, perform and inspect the work. If access is absent, produce an executable plan/script with stated untested sections; do not claim to have modeled, rendered, or exported anything. For automation, use the companion `blender-python-api` skill when available.

## Measure before detailing

Create a concise evidence table: landmark/part, dimension or ratio, units, source, confidence, and uncertainty. Research real dimensions from manufacturer drawings or other primary sources for the exact variant. A similar model is not exact evidence.

Choose a verified anchor dimension and world axes; document origin and ground plane. Use orthographic references only when genuinely orthographic. Match camera perspective before comparing a perspective photo with a render; never measure depth or absolute size from a single uncalibrated view as fact. Mark occluded parts `ASSUMED` or `UNCERTAIN`, giving ranges where useful. Preserve ambiguity rather than inventing hidden engineering.

Read [production gates](references/production-gates.md) for stage checks and quantitative comparisons.

## Build in reversible stages

**Stage 0 — reference setup.** Set units, reference planes/cameras, anchor dimensions and semantic part names. Separate reference, blockout, low, high, and export collections only as needed. Keep references out of export.

**Stage 1 — primitive blockout.** Use boxes, cylinders, wedges, curves, and simple volumes. Establish major masses, contact points, wheel/hinge/axle centers, negative spaces, and overall silhouette. Compare front/side/top views plus the reference-matched camera. Fix proportion errors before subdivisions or fine details. Continue autonomously through gates unless the user requested approval between stages.

**Stage 2 — low-poly form.** Build purposeful topology around silhouette, shading boundaries, and deformation. Keep rigid movable parts separate with useful pivots. Use Mirror only where evidence supports symmetry. Keep modifier order deliberate; inspect evaluated geometry, not only the control cage. Make bevel widths meaningful in world units. Do not use smooth shading to hide missing form.

**Stage 3 — high-poly source.** Duplicate or branch the approved forms while retaining the low mesh. Add physically justified thickness, curvature, seams, and surface detail through bevel/subdivision/sculpting as appropriate. Subdivision alone is not a fidelity improvement. For organics, preserve landmarks and deformation needs; remeshing a sculpt does not automatically produce animation-ready topology. Check that support loops and booleans do not produce pinching or unintended intersections.

**Stage 4 — production low and bake.** Update/retopologize low mesh against the final high source. Check normals, intentional boundaries, degenerate/duplicate faces, intersections, material slots, and transforms. Preserve locked UVs exactly; otherwise unwrap for required texel density and bake isolation. Lock export triangulation and normal/tangent decisions before tangent normal baking. Use explicit high-to-low selection, active low object, target image, cage/ray distance, and padding. Verify a small representative bake before committing the full asset. Use `blender-texture-material-painting` for maps/materials.

**Stage 5 — export and engine check.** Retain editable source, export only intended objects, and avoid applying modifiers destructively to the master. Use a verified exporter preset matching the target. Validate glTF material compatibility; procedural Blender shaders need baking or engine reconstruction. Create collision and LODs only to the project's needs. Test one export/import loop before batch processing.

## Validate and deliver

Reopen the saved blend and inspect export in the destination engine when available. Check dimensions, axes, pivots, material assignments, normal shading, culling, collision, LOD transitions, and animation compatibility if relevant. Report both mesh triangles and evaluated/exported counts; UV/material/normal splits can increase exported vertices.

Provide artifact paths, exact tested versions, measured fidelity results, remaining assumptions, stage reached, and checks actually run. Separate observed results from proposed verification. A polished render alone does not establish game readiness. Use [eval cases](evals/evals.json) when improving this skill; do not treat their assertions as already passed.


# Bundled resources

The resources below belong to this skill. Split them into the indicated relative paths when using a folder-based skill loader.

## File: `references/production-gates.md`

````markdown
# Production gates

## Reference fidelity

Maintain a landmark table such as overall dimensions, axle spacing, wheel radii, top-of-body height, and silhouette extrema. Store source/confidence separately from the measured model value. For verified target distance d and model distance m, report absolute error |m-d| in scene units and relative error |m-d|/d when d is nonzero. Set acceptance tolerances from source precision and the task; do not invent them after measuring.

For calibrated aligned silhouette masks, calculate intersection-over-union and optionally boundary distance; report resolution, camera, crop, and occlusion treatment. A good IoU can conceal small important parts. Compare key landmarks and negative spaces separately. For perspective photos, fit camera and lens before evaluating geometry; a single image leaves depth ambiguous. Uncalibrated renders support qualitative assessment only.

## Geometry

Check evaluated bounding boxes in world space, scale sign, loose/zero-area geometry, duplicate faces, winding, intentional versus accidental open borders, self-intersections, and visible shading. Do not require every asset to be watertight: leaves, garments, and open shells may intentionally have boundaries. Rigid hard-surface meshes need not be all quads; deformation/subdivision needs determine topology. Inspect wireframe during bending for animated forms. Keep export triangulation deterministic and consistent with the normal bake.

Avoid arbitrary merge-by-distance thresholds; use the asset scale and protect close parallel surfaces. Inspect modifier interactions around seams. Keep a snapshot before remeshing, destructive booleans, UV changes, or applying modifiers. Reject a repair that changes the approved silhouette more than the original defect.

## UV and bake

For locked UV work, snapshot layer names, active/render layer, per-loop UVs and mesh topology before editing, then compare after. A topology change invalidates loop-index comparison; treat it as a separate change requiring an explicit mapping or avoid it. Do not repack, normalize, rotate, or scale islands merely to improve appearance. If layout defects prevent the requested result, report the localized conflict and propose options.

For new UVs, inspect checker distortion, texel density, overlapping islands and seam placement. Deliberate mirrored/stacked UVs are acceptable only for compatible content and baking. Keep lightmap UVs separate when the engine requires unique non-overlapping charts. Size dilation against mip levels, texture size, UV gaps and compression; inspect seams in the engine at distance.

Bake with matched low/high transforms. Test cage intersections around thin or concave parts, cross-object projection and incorrect smoothing. Isolate intersecting pieces or bake by matched groups when appropriate. Freeze the triangulation and shading basis used for the final bake. Never claim a normal map can repair missing silhouette geometry.

## Godot handoff

Read the exact target Godot minor's import docs. Godot uses Y-up; its camera forward is -Z while an oriented asset's conventional front is +Z. Blender's corresponding asset front is -Y. Do not add a second manual rotation after exporter axis conversion. Test an asymmetric orientation marker and a known metric dimension.

Explicit glTF/GLB exports are useful reproducible handoffs; direct blend import is viable only when its Blender dependency and exporter settings are controlled. Inspect imported materials and double-sidedness, normals/tangents, pivots, origin, collision and scale. Place runtime lighting in-engine. Prefer convex/simple collision for moving bodies; choose static concave collision only where the target physics rules allow it. Inspect LOD silhouette and material continuity at actual viewing distances rather than accepting decimation percentage as a quality test.

## Minimal handoff record

- Source blend and exported scene paths; exact Blender/exporter/Godot versions.
- Units, axes, origin, real versus assumed dimensions.
- Triangle/vertex counts before and after export, material count, texture sizes, LODs/collision if requested.
- Before/after orthographic and matched-camera comparisons.
- Checks run, measured errors, remaining defects and their gameplay impact.
````

## File: `references/sources.md`

````markdown
# Official sources and version policy

Research date: 2026-10-01. These are primary documentation sources, not a promise that every runtime/API has been exercised. Blender manual search results identified 5.2 LTS. Several direct Blender page fetches returned HTTP 402; the entries marked indexed were verified through official-domain search excerpts, not full-page retrieval. Fetch the matching runtime's page before relying on an exact operator/property signature. `/latest`, `/current` and Godot `/stable` are moving selectors; inspect their actual version and select the installed minor. Never copy a development-only signature into stable code.

| Source | Access evidence | Applicable use |
|---|---|---|
| https://developer.blender.org/docs/release_notes/5.2/python_api/ | Official indexed result; direct fetch blocked | 5.2 migration; Geometry Nodes modifier input properties changed to RNA, so verify the exact runtime API |
| https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html | Indexed as 5.2 LTS; direct fetch blocked | Export-supported material patterns and glTF constraints; resolve installed-version equivalent |
| https://docs.blender.org/manual/ko/5.2/addons/scene_gltf2.html | Official 5.2 indexed detailed excerpt | Confirms roughness G, metallic B and Non-Color input; use equivalent English 5.2 page if accessible |
| https://docs.blender.org/manual/en/latest/render/cycles/baking.html | Indexed as 5.2 LTS; direct fetch blocked | Baking target/cage/margin concepts; confirm exact bake settings locally |
| https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/model_export_considerations.html | Full page read | Asset/camera axes distinction, triangulation, transforms and engine lighting; pin engine minor |
| https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html | Full page read | Godot material behavior, +Y/OpenGL normals, ORM and renderer differences; pin engine minor |
| https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html | Specification retrieved | Normative glTF 2.0 data conventions; extensions need separate capability checks |

Skill-specific workflows, fidelity gates and test scenarios are engineering synthesis. They are not direct quotations or guarantees of a measured performance budget.

| Modeling source | Access evidence | Applicable use |
|---|---|---|
| https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/mirror.html | Indexed as 5.2 LTS | Mirror origin/local axes |
| https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html | Indexed as 5.2 LTS | Subdivision workflow |
| https://docs.blender.org/manual/en/latest/modeling/modifiers/introduction.html | Indexed as 5.2 LTS | Modifier evaluation order |
| https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html | Indexed as 5.2 LTS under Remeshing | Remeshing limits; not proof of animation-ready edge flow |
| https://developer.blender.org/docs/release_notes/5.2/modeling/ | Official indexed page | Modeling/UV release-specific changes; read before using changed functionality |
````

## File: `evals/evals.json`

````json
{
  "skill_name": "blender-3d-modeling",
  "evals": [
    {
      "id": 1,
      "prompt": "Blender 5.2.2 kullanıyorum. Ekli tek perspektif motosiklet fotoğrafı ve AI cheatsheet ile birebir blockout, sonra low-poly ve high-poly oluştur. Tek doğrulanmış ölçü dingil mesafesi 1420 mm. Cheatsheet arka tekeri daha büyük gösteriyor. Ek parça tasarlama.",
      "expected_output": "Measured staged workflow or actual scene if tools/input assets exist; photo prioritization and uncertainty record.",
      "files": [],
      "assertions": [
        "Requests/uses supplied references without inventing unseen files or scene results",
        "Uses 1420 mm anchor and marks unobservable width/depth as uncertain",
        "Prioritizes real photo when cheatsheet conflicts",
        "Preserves separate editable stages and checks silhouette before detailing"
      ]
    },
    {
      "id": 2,
      "prompt": "Bu existing .blend içindeki sadece crate_LOD0 objesinin shading hatasını düzelt ve Godot 4.7 projesine GLB hazırla. UV'ler kesinlikle değişmeyecek, sahnedeki diğer objeler de aynı kalsın. Triangle budget proje dosyasında.",
      "expected_output": "Scoped mesh correction with UV snapshot, evidence-led triangulation/export and target import test when available.",
      "files": [],
      "assertions": [
        "Inspects project budget instead of inventing a AAA count",
        "Does not clear scene or modify unrelated objects",
        "Verifies UV invariance including loop/topology relationship",
        "Uses deterministic triangulation and reports target import as run or pending"
      ]
    },
    {
      "id": 3,
      "prompt": "Elimde yalnız ön görünüş var. Aracın arka tarafını kesin ölçülerle tamamla; modeli 200 bin poligona çıkarınca AAA olacaktır. Blender 5.3 dev kullanıyorum ama 5.2 runtime'a teslim edeceğim.",
      "expected_output": "Corrects false precision and polygon-count premise; version-compatible staged implementation.",
      "files": [],
      "assertions": [
        "Does not claim hidden dimensions are known",
        "Explains AAA quality is not guaranteed by polygon count",
        "Pins 5.2 delivery compatibility and avoids unverified dev API",
        "Offers conservative rear assumptions and useful measurable fidelity gates"
      ]
    }
  ],
  "trigger_tests": [
    {
      "prompt": "Blender'da fotoğraftaki motoru primitive blockout'tan low/high modele dönüştür",
      "should_trigger": true
    },
    {
      "prompt": "Bu assetin silhouette hatalarını ve topology'sini düzelt",
      "should_trigger": true
    },
    {
      "prompt": "Bana sadece beyaz zeminde motosiklet resmi çiz",
      "should_trigger": false
    },
    {
      "prompt": "Godot oyuncu hareket GDScript'ini yaz",
      "should_trigger": false
    }
  ]
}
````
