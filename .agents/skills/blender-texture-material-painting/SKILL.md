---
name: blender-texture-material-painting
description: Author, paint, bake, repair, and validate Blender 5.2+ PBR materials and texture sets for game assets, including UV-preserving edits, brush assets, procedural-to-texture baking, tangent normals, and Godot/glTF material export. Use for albedo, roughness, metallic, normal, emission, AO, seam or texture alignment issues, material painting and texture delivery. Pair with blender-python-api for automation; do not trigger for unrelated photo editing, 2D illustration, or mesh-only modeling.
---

# Blender Texture and Material Painting

Produce editable materials and saved texture files that survive a reopen and engine import. Keep physical material intent separate from preview lighting. Respond in the user's language.

## Inspect and preserve

1. Detect exact Blender version with `bpy.app.version_string`/`bpy.app.version` or `blender --version`. Target 5.2+, verifying the installed minor's manual, API and release changes before using operators, brush assets, node sockets or exporter flags. Later releases need separate checks. Use [sources](references/sources.md); do not mistake moving `latest` or `current` links for a version pin.
2. Inspect the mesh, UV sets, images, material nodes, mapping transforms, dimensions, color spaces, packing and external paths. Establish target engine/version/renderer and requested maps, resolution, bit depth, tiling and channel packing. Use project budgets; do not prescribe 4K/8K or one material per part by default.
3. Save a working copy. Preserve original assets and isolate edited datablocks if materials/images are shared. When UVs are locked, snapshot topology and all per-loop UV coordinates and layer settings; make no re-unwrap, island movement, rotation, scaling or repacking. Preserve image resolution and pixel registration when required. Any change that makes the comparison invalid must be disclosed.
4. Determine whether the request is analysis-only, editable material creation, direct image painting, or baking. Use available Blender/image tools to execute the authorized task. Without them, provide a concrete script/workflow and label unexecuted work; never invent paint strokes, bake results or visual checks.

Read [PBR pipeline](references/pbr-pipeline.md) before generating map sets, baking, painting existing UVs, or exporting to Godot.

## Build material intent

Create a material-region table: substance, coating, roughness rationale, metallic state, height scale, opacity, and emission intent. Paint and rust over metal are usually dielectric surface layers; exposed clean metal is metallic. Use intermediate metallic values for coverage/antialiasing or an intentional blend, not as a generic shininess control.

Keep base color free of cast shadows, specular highlights, AO, and directional lighting. Preserve intentional coloration and stains; a photographic dark patch is not automatically a cavity. Do not derive roughness from inverse albedo or invent precise height from color. If source images cannot establish surface geometry or material values, label the inference and use physically plausible conservative detail.

Use a minimal understandable node graph with meaningful node/image names. Resolve sockets by verified names/identifiers, not memorized indices. Keep color textures and numeric data maps correctly interpreted. Use a Normal Map node for tangent-space normals; do not plug RGB normal data directly into the shader normal input. A display transform is not a correction to stored texture values.

## Paint or generate

Select the exact object, UV layer, material and image target explicitly. Confirm texture-paint slots, face masking, backface/occlusion behavior, brush scale/falloff and seam bleed before painting. Start on a small identifiable region and verify the stroke reaches the intended UV island. Preserve labels, material boundaries and existing details outside the request.

Inspect the current brush asset workflow. Do not assume legacy direct brush assignment remains valid in Blender 5.2+. Treat Essentials/library brushes as sources; create a project-owned copy when modifying shared assets, and save the brush asset through the supported workflow if persistence is requested. Confirm by reopening; changing a temporary brush setting is not an installed reusable brush.

For procedural materials, keep real-world texture scale, deterministic seeds where needed and meaningful masks. Avoid uniform noise across unlike substances. For tiling outputs, validate both edge pairs and neighboring tiles for every map. If image generation is used for appearance, validate registration, seams and numeric map semantics; an attractive generated normal map is not proof of a correct tangent field.

## Bake and export

Confirm Cycles/bake support in the runtime, source/target selection, active target image node in each material, UV layer, matching low/high transforms and suitable cage/ray distances. Test representative thin/concave regions first. Freeze low-mesh triangulation and tangent basis before a final normal bake. Bake data separately from illumination; isolate base color from direct/indirect contributions. Keep AO separate unless the requested style intentionally bakes lighting.

Use tangent-space +Y/OpenGL normals for the standard Blender-to-Godot path. A DirectX map needs one deliberate green-channel inversion; never flip merely because a preview looks different. Bake or reconstruct unsupported procedural graphs for glTF; Blender appearance alone does not imply exporter support.

Confirm target channel packing before creating it. For glTF metallic-roughness, G is roughness and B is metallic; an ORM texture convention uses R for occlusion. Select the correct UV set, channel and linear data interpretation in the destination material. Do not infer arbitrary engine packs from filenames.

Explicitly save dirty external images, then save the blend; alternatively deliberately pack images for a self-contained blend and verify packed state. Deliver external texture files when requested even if packed. Do not export display-transformed data maps as screenshots or rendered previews.

## Verify and hand off

Reopen the blend and reload external images. Check resolution, channels, file paths, color spaces, UV invariance, material assignments and no unsaved image state. Inspect neutral lighting and several grazing/view angles, with each map isolated, then test in the target engine if available. Check seams at mip levels and compressed target settings, mirrored tangents, normal direction, roughness scale, transparency, culling and emission.

Report paths, exact tested versions, map/channel table, normal convention, modifications and constraints preserved, checks executed and unresolved issues. Keep visual preview separate from texture deliverables. Use [eval cases](evals/evals.json) for future skill testing; assertions there are not evidence of passed runtime tests.


# Bundled resources

The resources below belong to this skill. Split them into the indicated relative paths when using a folder-based skill loader.

## File: `references/pbr-pipeline.md`

````markdown
# PBR pipeline decisions

## Data contract

| Map | Meaning | Typical interpretation | Validation |
|---|---|---|---|
| Base color | Surface color/metal reflectance for metallic workflow | sRGB for conventional color images | No cast shadow, AO or reflected highlight |
| Roughness | Microfacet roughness, low smoother/high rougher | Non-Color numeric data | Inspect grazing reflections; never infer directly from luminance |
| Metallic | Dielectric/conductor material coverage | Non-Color numeric data | Coatings/rust separated from exposed metal |
| Tangent normal | Encoded local direction, not height | Non-Color; Normal Map node | +Y for Godot; neutral near (0.5, 0.5, 1), normalization and seams |
| Height | Scalar surface offset | Non-Color numeric data | Document units/range and sufficient precision; no arbitrary albedo emboss |
| AO | Local indirect occlusion | Non-Color numeric data | Separate from color; avoid double-darkening |
| Emission | Emitted color/intensity | Color-managed color image; HDR pipeline when required | Separate intensity convention; no assumption it lights nearby objects automatically |
| ORM | R occlusion, G roughness, B metallic | Non-Color numeric data | Inspect channels independently and target material wiring |

Use these conventional interpretations only when they match the source encoding and project's color management. EXR may contain scene-linear color; do not force all color images to sRGB. Alpha, masks, normal vectors and packed scalars are data. Use lossless outputs for maps when practical; assess target compression separately. Choose bit depth for required precision and memory rather than applying one format universally.

## Existing UV edits

Record UV layers, per-loop coordinates, topology, image dimensions and sampling transforms. Edit the image/material rather than the UV map when the layout is locked. Compare snapshots after work. Preserve padding without painting over another island's valid area. Reject automatic flatten/repack operations under an immutable-UV contract. If mirrored islands prevent asymmetric painting, explain the conflict rather than quietly changing UVs.

Project a reference only after matching camera/lens and confirming scale. Photos contain lighting and occlusions: de-light cautiously and identify uncertain regions. A flat generated image is not automatically a valid mesh texture. Use UV overlays, unique island colors or a numbered checker to verify registration before detailed painting. Preserve corresponding pixel positions across every requested map.

## Normal and height correctness

A tangent normal encodes direction relative to a mesh tangent basis. Recover a plausible height field only where surface structure warrants it; large albedo changes can have zero height. For derived normals, document height amplitude and physical texel scale, normalize the resulting vectors, and use wrap-aware derivatives for tiled maps. Keep a flat surface neutral. Blend multiple normal fields using a normal-aware method, not ordinary RGB averaging.

When diagnosing inverted detail, inspect orientation, UV mirroring, tangent generation, negative object scale and the DirectX/OpenGL convention before editing data. Flip G exactly once only for a known -Y source. A correct normal texture still fails if the bake and export triangulation/tangents differ. Do not change silhouette-critical depth only in a normal map.

## Paint and bake reliability

Use explicit target images and stable paths. Test one island before a full operation. For projection painting, verify occluded/back-facing surfaces were not unintentionally marked. Paint across seams in 3D and inspect in UV view. For bakes, isolate projection from nearby parts as needed, test cage clearance, and measure resulting artifacts before increasing ray distance blindly. Save each successful costly stage.

Size texture dilation/padding from texture resolution, UV separation, mip footprint and compression. There is no universal safe pixel count. Test at small mip levels; downsampling must not mix adjacent unrelated island colors. Compare tiled texture edges numerically where possible, but remember exact pixel equality alone does not guarantee a visually smooth boundary; inspect derivatives/normal continuity and a multi-tile preview.

## Export check

Use official exporter-supported node patterns and exact release docs. Connected Blender nodes may be baked/repacked, ignored or reduced by an exporter. Inspect the exported file/material rather than relying on source-node appearance. For engine-ready procedural material requests, deliver editable source and baked engine maps or an explicit engine shader implementation, depending on scope.

In Godot, use the project's selected renderer and known test lighting. Check material multiplicative color factors, normal-import settings, channel selectors, UV channel, repeat/filtering, alpha mode and backface culling. Light, tone mapping and renderer differences make identical previews unlikely; compare map semantics before compensating texture values. Count surfaces/materials and texture memory where the budget matters.

## Handoff schema

For each output record: path, image width/height, format/bit depth, channel meanings, source color encoding, Blender color-space setting, normal convention if applicable, physical scale, UV set and target material slot. Record whether images are external or packed. Include exact versions and only the checks actually executed; leave unavailable engine validation explicitly pending.
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

| Painting source | Access evidence | Applicable use |
|---|---|---|
| https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/introduction.html | Indexed as 5.2 LTS; direct fetch blocked | Texture-paint workflow |
| https://docs.blender.org/manual/es/latest/sculpt_paint/texture_paint/introduction.html | Official 5.2 indexed detailed excerpt | External images need explicit save; deliberately packed images differ |
| https://docs.blender.org/manual/en/latest/sculpt_paint/brush/brush_management.html | Indexed as 5.2 LTS | Brush asset persistence and ownership; verify operators locally |
| https://docs.blender.org/manual/en/latest/editors/image/image_settings.html | Indexed as 5.2 LTS | Color versus numeric image interpretation |
| https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html | Indexed as 5.2 LTS | Metallic/roughness material interpretation |
````

## File: `evals/evals.json`

````json
{
  "skill_name": "blender-texture-material-painting",
  "evals": [
    {
      "id": 1,
      "prompt": "Blender 5.2 mevcut silah UV haritamı değiştirme. Boyalı çelikte pas ve çıplak metal ayrımını düzelt; albedo, roughness, metallic, OpenGL normal ve Godot ORM çıkar. Çözünürlük ve piksel konumları aynı kalsın.",
      "expected_output": "UV-locked material-region workflow with registered PBR maps and verified ORM mapping.",
      "files": [],
      "assertions": [
        "Snapshots and verifies UVs and image dimensions without repacking",
        "Paint/rust treated dielectric and exposed metal metallic",
        "Does not derive roughness merely by inverting albedo",
        "Uses +Y normals and explicit R AO G roughness B metallic packing"
      ]
    },
    {
      "id": 2,
      "prompt": "Texture Paint ile yaptığım çizikler Blender'ı kapatınca kayboluyor. Essentials brush'ını da değiştirdim ama ayarı dönüyor. Projeyi kaydetmiştim; bunları kalıcı yap.",
      "expected_output": "Inspects image save/pack state and brush ownership separately, saves actual resources, reopens for verification.",
      "files": [],
      "assertions": [
        "Distinguishes blend save from external image save",
        "Checks external versus packed image persistence",
        "Does not overwrite shared Essentials asset; creates owned asset if needed",
        "Verifies actual version brush workflow rather than assumes legacy assignment"
      ]
    },
    {
      "id": 3,
      "prompt": "Bu albedo fotoğrafından birebir fiziksel normal çıkar, ışık gölgeler aynı kalsın. Şu an green flipped DirectX normal de var. Blender 5.2 ve Godot'ta aynı materyal görünsün; engine test erişimin yok.",
      "expected_output": "Separates uncertain height reconstruction from albedo appearance and avoids double inversion/unverified engine claims.",
      "files": [],
      "assertions": [
        "Does not claim exact surface height can be recovered from one albedo",
        "Keeps illumination out of PBR base color and no blind luminance emboss",
        "Checks existing normal convention before exactly one conversion",
        "States engine validation unavailable and gives concrete pending checks"
      ]
    }
  ],
  "trigger_tests": [
    {
      "prompt": "Blender UV'lerime dokunmadan roughness ve normal seamlerini düzelt",
      "should_trigger": true
    },
    {
      "prompt": "Procedural Blender materyalini Godot için bake et",
      "should_trigger": true
    },
    {
      "prompt": "Fotoğrafın arka planını kaldır",
      "should_trigger": false
    },
    {
      "prompt": "Sadece araç geometrisinin wheelbase ölçüsünü değiştir",
      "should_trigger": false
    }
  ]
}
````
