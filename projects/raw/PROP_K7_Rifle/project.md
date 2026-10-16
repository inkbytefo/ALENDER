# PROP_K7_Rifle — K-7 Rook

## Category / targets
prop (FPS hero weapon)  
Budget key: `hero_prop` (`workbench.tables.BUDGETS`)  
Targets: editable Blender source, game-ready Godot GLB, and studio presentation.

## Art direction
An original, clean-sided K-7 with a purposeful hybrid silhouette: compact angular receiver,
tapered M-LOK handguard, full-length top rail, open raised iron sights, softly curved 30-round
magazine, ergonomic grip, and a light skeletonized collapsible stock. Matte graphite anodized
metal contrasts with charcoal polymer; bright steel is reserved for the carrier, sight edges, and
small wear accents. No borrowed logos or markings.

The K-7 is an authored game-art concept, not a reconstruction of a real firearm or a functional
engineering specification. The existing `REAL_REFERENCE.png` and its crops remain unchanged as
historical context; they do not define the new proportions.

## Design scale and orientation
- Side-view design canvas: 1536 × 720 px; muzzle on image-left, viewed from the object's left.
- RefMap: 1500 px/m; bore-origin anchor `(750, 350)` at world `(0, 0, 0)`; no photo tilt.
- Authored muzzle-to-butt length: 0.904 m. This is a project target, not a manufacturer dimension.
- Widths: deliberately stylized game-art estimates; main receiver half-width 28 mm, handguard
  half-width 36 mm, stock half-width 26 mm.
- Axis conventions: +Z up, −Y forward (muzzle), +X object's left. Hand-held origin at bore axis.
- `K7_DESIGN_REFERENCE.png` is the authored orthographic side-view guide;
  `REF_MASK.png` is generated from the design landmarks for silhouette checks.

## Stages and provisional budget
| Stage | Content | Triangle budget |
|---|---|---:|
| S1 PRIMITIVE | Major component silhouettes, lengths, width, raised sights | < 1,500 |
| S2 LOWPOLY | Clean game mesh, separated sub-parts, UV atlas | 4,000–15,000 target |
| S3 DETAIL | Readable chamfers, rail teeth, M-LOK details, grip/mag ribs, wear accents | < 60,000 |
| S4 GAME | 2048 bake, LOD0–2, component collision, Godot GLB | Workbench profile |
| S5 PRESENT | Inspected clay and studio-dark presentation renders | — |

## Component registry
| Part | Contents | Collision / pivot |
|---|---|---|
| Receiver | Receiver shell, ejection-port/carrier face, full-length Picatinny rail | Hull |
| Barrel | Barrel, stepped muzzle device, gas collar | Hull |
| Handguard | Tapered shell, side rails, M-LOK inset details | Hull |
| Magazine | Curved polymer body, ribs, floorplate | Hull; removable pivot |
| Grip | Ergonomic polymer grip and texture ribs | Hull |
| Controls | Trigger, guard, selector, separate charging handle and knob | No collision; handle pivot |
| Stock | Buffer tube, skeletonized shell, cheek riser, buttplate | Hull |
| Sights | Raised front post and open rear aperture | No collision; leaf pivots |

## PBR intent
| Material | Intent | Metallic | Roughness |
|---|---|---:|---:|
| `MAT_RECEIVER` | Matte black anodized aluminum | 0.88 | 0.48 |
| `MAT_POLYMER` | Dark charcoal polymer | 0.00 | 0.72 |
| `MAT_STEEL` | Dark steel controls and rails | 0.82 | 0.40 |
| `MAT_WEAR` | Restrained exposed steel on handled edges | 0.95 | 0.32 |

S4 produces the project bake maps using the Workbench metallic-roughness pipeline. Godot uses
glTF metallic-roughness channels; tangent normals are expected to use +Y/OpenGL convention.

## Assumptions and limits
- Hidden faces, internal mechanisms, exact ammunition dimensions, and mechanical clearances are
  intentionally not specified; this is visual game art only.
- Side profile and widths are authored choices; the retained generated image is not treated as
  measured evidence.
- The sights are shown raised and aligned for an FPS view; hinge mechanics are simplified.
- Engine round-trip must be marked pending if Godot is unavailable during the build.

## Deliverables
`output/PROP_K7_Rifle/blend/` stage milestones and hero blend;  
`output/PROP_K7_Rifle/glb/` LOD0–2 and hero GLBs;  
`output/PROP_K7_Rifle/textures/` baked base/ORM/normal textures;  
`output/PROP_K7_Rifle/work/s1..s4/` stage reviews and gate diffs;  
`output/PROP_K7_Rifle/presentation/` clay and studio-dark sheets.
