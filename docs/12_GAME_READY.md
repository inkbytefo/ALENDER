# 12 — Game-ready delivery (Stage 4)

S4 turns S2 LOWPOLY (the shipping LOD0 topology) and S3 DETAIL (bake source) into an engine
package. It is automatic; the agent configures it in `parts.py` and reviews the result.

```python
GAME = dict(engine="godot",      # godot | unity | unreal  (collision naming + fbx for unreal)
            bake=True,           # False: keep the S2 multi-material palette, no textures
            tex=2048,            # default tables.BUDGETS[CATEGORY]["tex"]
            lod=(0.5, 0.25),     # LOD1 / LOD2 tri ratios of LOD0
            drop_small_m=0.02,   # moving parts smaller than this vanish at the last LOD
            uv_m=2.0)            # metres per unit of the tiling UVMap (PBR palettes, docs/11)
PIVOTS = {"MAG_Body": lambda: L.P3(778, 331)}        # moving parts: origin on the joint
CHILDREN = {"MAG_Floorplate": "MAG_Body"}            # rides with its parent
PARTS = [Part("magazine", magazine, prim=magazine_prim, collision="hull"), ...]   # hull | box | none
```

## What the pipeline does
1. **UV atlas (S2)** — `uv.atlas()`: one multi-object smart-project atlas → `UV_Bake` (0-1, bakes)
   and `UVMap` (same islands at `uv_m` m/unit, tiling PBR). Gates U13 (overlap / outside) and U14
   (texel density spread).
2. **LOD0 copies** — evaluated S2 meshes (`<base>_LOD0`), only the atlas kept (renamed `UVMap`).
3. **Pivots** — `PIVOTS` origins, bbox centre for the rest (docs/02).
4. **Bake** (`game.bake`, Cycles selected-to-active, GPU when available): DIFFUSE colour → base
   (sRGB), NORMAL tangent (OpenGL +Y) → normal, AO + ROUGHNESS + metallic (EMIT trick) → packed
   **ORM** (R = AO, G = roughness, B = metallic, glTF convention). Cage extrusion ≈ 0.6 % of the
   asset size, AO distance ≈ 8 %.
5. **Material** — `game.game_material`: Principled + textures + "glTF Material Output" group, so
   the glTF exporter writes baseColor, metallicRoughness, occlusion and normal textures.
6. **Merge / hierarchy** — static parts → `<A>_Body_LOD0`; moving parts stay separate, parented
   by `CHILDREN`, everything under the asset root empty.
7. **LOD1-2** — collapse decimation of each LOD0 object (`game.lod_copy`); tiny movers dropped at
   the last LOD.
8. **Collision** — one convex hull (or box) per Part group from the S2 meshes, ≤ 250 faces,
   named for the engine (below), collection `41_S4_COLLISION`, exported with LOD0 only.
9. **Exports** — `glb/<A>_LOD0|1|2.glb` (+ `fbx/<A>_LOD0.fbx` for unreal), textures in
   `output/<A>/textures/`. Checks G01–G06, U13/U14, hygiene on the game meshes, M01, U15.
10. **Review renders** — `work/s4/s4_{persp,close}_{lod0,lod1,lod2,s3}.png` (EEVEE). Compare LOD0
    with S3 side by side: the bake must reproduce bevels, ribs and rivets; broken islands show as
    dark / inverted patches.

## Engine naming
| engine | collision object | notes |
|--------|------------------|-------|
| godot | `<Body>_00-convcolonly` | glTF import hint → ConvexPolygonShape3D, mesh hidden |
| unity | `<Body>_Collider00` | add MeshCollider (convex) on import (name filter) |
| unreal | `UCX_<Body>_00` | FBX import picks UCX_ hulls; exported to `fbx/` |

## Engine-side check
`python wb.py glb <file>` reads the glb like an engine (`workbench.glbinfo`: nodes, meshes, tris,
materials, embedded image sizes) — used by gate G05. `python wb.py engine-check <file>` adds a
headless Godot 4 import (`scripts/godot_import_check.gd`) when `$GODOT_EXECUTABLE` is set
(not verified in this repo yet — Godot is not installed here).

## Known limits / lessons
- Selected-to-active rays can hit a **neighbouring** high-poly part where parts touch (carrier
  inside the receiver, levers on walls). Those faces are hidden in the assembly, so the artefact is
  invisible — but check the close-up render; if a visible face is wrong, separate the parts more or
  bake that part on its own (lesson 36).
- The bake takes minutes at 2048 px (GPU); iterate with `--no-bake` / `--until 3` and bake last.
- LOD decimation keeps UVs approximately; very aggressive ratios smear textures — keep ≥ 0.2.
- Bone-driven characters (skins) are not covered by S4 yet: export rigs via docs/07.
