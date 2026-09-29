# 11 — PBR materials and third-party assets

Two library layers:
- `workbench/pbrlib.py` (pure python) — finds PBR texture sets on disk and classifies their maps.
- `workbench/bl/pbr.py` (bpy) — builds glTF-exportable Principled BSDF node trees from a set.
- `workbench/bl/assets.py` (bpy) — imports / analyses / fits / merges / decimates downloaded models.

Downloaded files live in `downloaded_resources/` (models/, materials/). `downloaded_resources/models/`
is **git-ignored** (Fab / Sketchfab licences forbid redistributing the raw files); CC0 material sets
(ambientCG, Poly Haven) in `materials/` may be committed — check the licence of anything else. A build that
needs such a file must say so in its `project.md` (source URL, licence, path) and fail with a clear
message when the file is missing.

---
## 1. PBR texture library

### Where sets are found
`pbrlib.library_roots()` = `$WB_PBR_LIBRARY` (os.pathsep-separated) + `library/materials/` +
`downloaded_resources/materials/` (existing ones). Drop an unzipped set folder in either place.

### Recognised naming (case-insensitive, end of the file stem)
| Map | Recognised suffixes |
|-----|---------------------|
| base colour | `Color`, `BaseColor`, `Base_color`, `Albedo`, `Diffuse`, `diff`, `D` (e.g. `bodyD`) |
| roughness | `Roughness`, `rough`, `_rg`, `R` |
| metallic | `Metalness`, `Metallic`, `metal`, `_mt`, `M` |
| normal | `NormalGL` / `Normal_OpenGL` (preferred), `NormalDX` / `Normal_DirectX` (green flipped automatically), `Normal`, `nor`, `_nr`, `N` |
| height | `Displacement`, `Height`, `disp`, `bump` |
| AO | `AmbientOcclusion`, `Mixed_AO`, `occlusion`, `_ao` |
| others | `Opacity`/`Alpha`, `Emissive`/`Emission`, `Specular`, packed `_arm` / `_orm` |
Several sets in one folder (e.g. `Main_*`, `Control_*` from a Substance export) are split by prefix.
The resolution tag (`_2K-PNG`) is removed from the set name: `Leather009_2K-PNG` → `Leather009`.

### Commands
```bash
python wb.py pbr list                       # every set: category, resolution, available maps
python wb.py pbr list --filter Metal
python wb.py pbr preview                    # labelled material balls -> output/_pbr/pbr_preview_grid.png
python wb.py pbr preview --filter Leather --samples 128
```
**Always look at the preview sheet before choosing** — names say nothing about colour or wear
(`Metal041B/053C/056C` are rusty, `Metal058A` polished copper, `Metal058C` patina, `Fabric004` is a
carbon-fibre weave, `Leather037` tan, `Leather009` near black).

---
## 2. Using PBR materials in a build

### In a project palette (preferred)
`materials.ensure(PALETTE)` understands a `pbr` entry; mix freely with plain Principled entries:
```python
PALETTE = {
    "MAT_BODY_RED": ((0.34, 0.012, 0.010), 0.3, 0.36),          # plain paint (no texture)
    "MAT_CARBON":   dict(pbr="Fabric004", tile_m=0.12),          # carbon weave, 12 cm repeat
    "MAT_LEATHER":  dict(pbr="Leather037", tile_m=0.35),         # seat / steering wheel
    "MAT_FLOOR":    dict(pbr="Tiles140", tile_m=1.0, bump=0.2),
}
```
Every builder keeps using the material *name* (`"MAT_CARBON"`), so switching a material between
flat colour and PBR is a one-line palette change and needs no geometry change.

### Direct API
```python
from workbench.bl import pbr
m = pbr.material("MAT_SEAT", "Leather037", tile_m=0.35)       # name or a pbrlib set dict
pbr.assign(ob, m)                                             # all slots (or slot=i)
```
| Parameter | Meaning / default |
|-----------|-------------------|
| `tile_m` | real size of ONE texture repeat in metres (1.0). Wood planks 1–2, leather 0.3–0.5, carbon 0.1–0.15, tiles = tile size × tiles in the image |
| `uv_m` | metres per UV unit of the target mesh. **2.0 for workbench builders** (`mesh.box_uv` = 0.5 UV/m), usually 1.0 for imported models with real-scale UVs. Mapping scale = `uv_m / tile_m` |
| `projection` | `"UV"` (default, glTF-safe) or `"BOX"` (object-space tri-planar, ignores UVs — Blender renders only) |
| `tint` | RGB multiply on the colour map (Blender-only refinement; keep `None` for game assets) |
| `roughness_mul` | scale the roughness map (Blender-only) |
| `metallic` | constant override (e.g. 0.0 for painted metal); otherwise the Metalness map or 0 |
| `normal_strength` | Normal Map node strength (1.0) |
| `bump` | > 0 adds the Displacement map as bump on top of the normal map (Blender-only, 0.1–0.3) |
| `use_ao` | multiply AO into base colour (off by default: engines apply their own AO; breaks glTF texture detection) |

### What the node tree looks like
`UV → Mapping → Image Textures` · Colour (sRGB) → Base Color · Roughness / Metalness (Non-Color) →
sockets · NormalGL → Normal Map (DirectX maps get the green channel inverted) → [Bump] → Normal ·
Opacity → Alpha · Emission → Emission Color. The material's `diffuse_color` is set to the mean
texture colour (linearised) so Workbench review renders (clay / material overlays) keep the right
colours. Custom props `pbr_set`, `pbr_tile_m` record the source for reports.

### glTF / game-engine rules
- Direct image → socket links export as glTF textures (baseColor, metallicRoughness — the exporter
  packs roughness + metalness, normal, emissive, alpha). Mapping scale exports as
  `KHR_texture_transform`.
- Blender-only (dropped or approximated on export): `tint`, `roughness_mul`, `BOX` projection, bump,
  AO multiply. Use them for presentation renders, not for game deliverables.
- 2K sets × several materials grow the GLB fast (each map is embedded). For game assets resize to
  1K or pack an atlas; record texture sizes in the report.
- UVs decide everything: seams show where UVs are discontinuous. Procedural workbench meshes get
  box UVs (seams at 90° edges — fine for hard surfaces); organic lofts may need `projection="BOX"`
  for renders or a proper unwrap for game use.
- Material budget (≤ 8 per vehicle) counts PBR materials like any other.

### Checklist
1. `python wb.py pbr preview --filter <kind>` → pick by eye.
2. Put it in the palette with a realistic `tile_m` (and `uv_m` if the mesh is not workbench-built).
3. Render a close-up (`python wb.py present <ASSET> --shots HERO_FRONT_34`) and check texel scale,
   seams and normal direction (bumps must look raised, not dented — if inverted, the map is DX).
4. Workbench review renders still work (mean colour), overlays unaffected.

---
## 3. Third-party models (FBX / glTF / GLB / OBJ / USD / STL / .blend)

### Analyse first
```bash
python wb.py inspect downloaded_resources/models/<x>/source/model.fbx            # table
python wb.py inspect <file> --render     # + clay contact sheet in output/_inspect/<stem>/sheet.png
```
The table lists every object with world centre, size, tris and materials. Read it for: units
(real scale or ×100 / ×2?), axes (which way is forward / up), duplicated modules, tri budget.

### Library API
```python
from workbench.bl import assets
objs = assets.import_model(path, "08_TEMP")           # new objects only, moved to the collection
assets.apply_transforms(objs)                         # bake parents/rotation/scale (scale 1 rule)
assets.transform(objs, Matrix)                        # bake any fit matrix (scale about a hardpoint, move)
assets.fit_to(objs, tmin, tmax, axes="XYZ")           # fit a bbox (uniform by default)
ob = assets.join(parts, "SUSP_Front_Arms", coll)      # merge by role, materials kept
ob = assets.split(src, "WHEEL_Front_Tire_L", keep)    # faces where keep(face, world_centre) is True
assets.decimate(ob, 6000, cad=True)                   # weld -> [cad clean] -> multi-pass collapse
assets.inspect(objs); assets.print_report(rep); assets.delete(objs)
```
Rules:
- Landmarks stay the source of truth: imported parts are **fitted to** landmark hardpoints (axle
  centres, mounting points), never the other way round.
- Bake transforms, then rename by the project scheme (`GROUP_Part_L`), map materials onto the
  project palette (≤ 8), give moving parts their pivot (wheel = hub).
- Keep the import inside a *visible* collection while processing (hidden collections are not
  evaluated; `bound_box` stays stale).
- Record source, licence and every modification in `project.md`.

### Decimating CAD-style exports (lesson from the double-wishbone test)
CAD / engineering FBX files (one vertex per face corner, huge n-gons, open boundaries, non-manifold
edges) **do not decimate well**: collapse stalls (75k → 56k at ratio 0.1) and extreme single-pass
ratios throw spikes. What helps, measured on the suspension arms:
| Pre-process | tris after weld | after collapse 0.1 |
|-------------|-----------------|--------------------|
| weld 2e-5 of bbox diagonal | 75,636 | 56,458 |
| weld 5e-4 | 41,660 | 24,811 |
| weld 2e-3 + triangulate + dissolve degenerate | 13,804 | 10,621 |
So: use `assets.decimate(ob, target, cad=True)` (weld 2e-3 + dissolve degenerate + multi-pass
collapse), and budget honestly — a 2.5 M-tri CAD asset is a *reference* or a
render-only prop, not a game asset, unless it is retopologised.
