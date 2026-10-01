# 04 — Modelling toolkit (library map + techniques)

All geometry is procedural (bmesh) and idempotent: calling a builder again replaces the object.
Import inside Blender scripts:
```python
from workbench import paths, tables, stages, silhouette   # pure python (host + Blender)
from workbench.stages import Part
from workbench.refmap import RefMap
from workbench.bl import scene, mesh, mods, prim, materials, cameras, render, anim, rig, validate, export
from workbench.bl import uv, game, pipeline              # S2 atlas, S4 game package, stage runner
from workbench.bl.fasteners import Fasteners
```

## Which builder for which shape
| Shape | Builder | Examples |
|-------|---------|----------|
| outline seen from the side, constant thickness | `mesh.plate(name, coll, poly_px, x0, x1, mat)` | side panels, swingarm, engine block/head, brackets, gear plates, window frames |
| rounded body following a side silhouette | `mesh.loft_px(name, coll, stations, n, mat)` | fuel tank, seat, tail, fuselage, car cabin, boat hull, bottle side |
| custom cross-sections | `mesh.loft_rings(name, coll, rings)` | paint-line-aware tank, tapered limbs, ducts |
| revolved profile | `mesh.lathe(name, coll, center, [(r, axial)], segs, mat, axis=)` | tyres, rims, discs, lamps, pistons, vases, columns |
| pipe / rail / cable along points | `mesh.tube(name, coll, pts, r or [r..], segs, mat)` | frames, exhaust, handrails, cables; `mesh.helix()` → springs |
| straight rod / cone | `mesh.cyl(name, coll, p0, p1, r, segs, mat, r1=)` | axles, fork tubes, legs, bolts |
| block | `mesh.box(name, coll, center, size, mat, rot=)` | housings, calipers, furniture, walls |
| many tiny repeats in ONE object | `mesh.multi_cyl`, `mesh.extrude_polys` | drill holes, studs, fins, louvres |
| identical hardware | `Fasteners(coll).place(kind, loc, normal)` / `.ring(...)` | bolts, nuts, washers (linked duplicates) |
| organic volume from a joint graph | `rig.skin_body(name, coll, joints, edges, radii)` | character blockout, creatures, trees, cables |
| openings | `mods.boolean(obj, cutter, apply=True)` | doors/windows in walls, holes in plates (cutter material + slot cleanup automatic) |

### Stage 1 primitives (`workbench.bl.prim`)
| Shape | Builder |
|-------|---------|
| bounding rectangle of a px outline, across X | `prim.box_px(name, coll, poly_or_bounds, hw, mat)` |
| px outline simplified to its corners (Douglas-Peucker) | `prim.plate_px(name, coll, poly, hw, mat, tol=6)` |
| cylinder between two px points (radius m) | `prim.cyl_px(name, coll, a_px, b_px, r, segs=8, mat)` |
| wheel / disc along X at a px centre | `prim.wheel_px(name, coll, center_px, r_px, hw)` |
| crude stand-ins of finished parts (migration) | `prim.from_objects(objs, name_fn, coll, "bbox"|"hull")` |

Photo-driven builders read pixels through the active RefMap: `mesh.set_ref(L.REF)` once in parts.py.
Loft stations: `(u, v_top, v_bot, half_width_m, e_top, e_bot, widest)`; build them from landmark
polylines with `tables.polyline_v(poly, u)` and a width table `tables.interp(table, u)`.
Superellipse exponents: 2 = ellipse, 2.5 = soft crown, 4–7 = boxy; `widest` = fraction of height
(from the bottom) where the section is widest.

## Stage profiles + part registry (one builder, every stage)
```python
PROFILES = {1: stages.profile(1, ring=8), 2: stages.profile(2, ring=16), 3: stages.profile(3, ring=32)}
PARTS = [Part("receiver", receiver, prim=receiver_prim, collision="hull"), ...]
def receiver(P):                              # P["stage"], P["coll"], P["bevel"], P["detail"], P["subsurf"], knobs
    return [hard(mesh.plate(stages.nm(P, "RECV_Body"), P["coll"], L.RECV_BODY, -hw, hw, STEEL), P)]
```
`stages.profile(n, **knobs)` sets `bevel/detail/subsurf` True from S3 and points the legacy
`C_PRIMARY/C_SECONDARY/C_MECH/C_DETAIL` keys at the stage collection. The pipeline runs every
Part's builder for the stage, tags new objects (`wb_part`, `wb_stage`), adds the stage suffix to
names that lack it and removes `TEMP_*` leftovers. `Part.prim` defaults to the real builder with
the coarse S1 profile; `Part.high` defaults to the real builder with the S3 profile.

## Smoothing policy (critical)
- **Hard-surface** (plates, boxes, brackets, engine parts): `mods.finish_hard(ob, bevel_w)` =
  bevel (angle-limited) + weighted normals. **Never subsurf a plate** — it shrinks to a blob or vanishes.
- **Organic** (lofts: tanks, seats, bodies, characters): `mods.finish_organic(ob)` = subsurf
  viewport/export L1, render L2.
- Bevel hierarchy: large structures 5–12 mm, medium parts 3–6 mm, small parts 1–3 mm.
- `mesh.finish()` already marks sharp edges by angle (default 40°); raise `sharp_angle` for
  smooth lofts (tank uses 75°).

## Techniques proven on the case study
- **Boundary-aware loft**: to make a crisp paint/panel line, sample each cross-section so one ring
  vertex lies exactly on the measured boundary (bisection on the superellipse), add a second vertex
  1.5 px below and scale everything below it inward (recess). Crease both edge loops (attribute
  `crease_edge`), set `material_index` per face band. Result: continuous lip, no stair-steps.
  See `tank_ring()` in `projects/VEH_Gemini_Motorcycle/parts.py`.
- **Fins / repeated plates**: one profile interpolated along the tilted block edges, all fins in
  one object via bmesh; inset the core so fins stand proud; leave a gap at the block/head joint.
- **Clearance-aware routing**: push pipe points radially away from a wheel until distance ≥
  radius + clearance (exhaust headers vs. front tyre).
- **Convergent parts**: intakes/pipes interpolate their X from spread positions to a collector.
- **Split mass by function** to avoid impossible overlaps: full-width crankcase + narrow
  transmission between frame plates (found by the intersection check, not by eye).
- **Instancing**: fastener families share one mesh; hundreds of bolts cost one mesh.
- **Drilled discs**: dark flush plugs (one merged object) read as holes without booleans.

## Cameras & renders
- `cameras.reference_camera(REF, anchors)` — reproduces the photo; anchors reproject < 2 px.
  For fitted three-quarter views, `REF.view="CALIBRATED"` uses explicit `cam_loc`,
  `cam_rot` (XYZ Euler radians) and `lens` (mm). Calibration is project-owned;
  its measured reprojection error is not automatically a passing acceptance check.
  `landmarks.REFERENCE_IMAGE` optionally selects a crop inside `ref/`, preserving the original montage.
- `cameras.review_rig(center, length, width)` / `rig_from_bounds(objs)` — 5 orthos + 2 perspectives.
- `render.workbench(cam, path, "CLAY"|"MATERIAL", transparent=True)` — fast review; transparent
  RGBA for overlays. `render.review_set(cams, folder, tag)` renders the whole rig.
- `render.studio_lights()` + `render.beauty(cam, path, engine="BLENDER_EEVEE"|"CYCLES")`.
- Video: `anim.turntable()` + `render.animation(cam, "x.mp4", 1, 240)` (docs/07).
- **Presentation studio** (docs/10): `presentation.studio(objs, style)` (360° cyclorama, 6-light
  rig, AgX) + `hero_cameras(objs)` (auto-framed) + `render_stills` / `turntable_video`;
  CLI `python wb.py present <ASSET>`.

## Pipeline modules
| Module | Role |
|--------|------|
| `workbench.stages` | stage table, `profile`, `nm`, `base_name`, `Part`, collections (pure python) |
| `workbench.silhouette` | `rasterize` (+closing), `metrics` (IoU, boundary px, worst zones), `diff_rgb`, `simplify`, `snap`, `edge_profile`, `label` (numpy) |
| `workbench.gate` | `inputs_hash`, `evaluate` → `wb.py gate` (pure python) |
| `workbench.glbinfo` | read a .glb like an engine: nodes, meshes, tris, materials, image sizes (pure python) |
| `workbench.bl.pipeline` | stage runner (`main(__file__)`), per-stage checks → report.json |
| `workbench.bl.uv` | `atlas` (UV_Bake + tiling UVMap), `texel_density`, `overlap` |
| `workbench.bl.game` | `copies`, `set_pivots`, `merge`, `lod_copy`, `collision`, `bake`, `game_material` |
| `workbench.bl.validate` | `stats`, `intersections`, `hygiene` (+`hygiene_checks` U04/U05/U11/U12/U16), `policy_checks` (N01/H01), `print_checks` (P01/P02) |
| `workbench.bl.render` | `workbench` (res from the reference camera), `silhouette`, `only(objs)`, `read_alpha`, `write_rgb`, `beauty`, `animation` |

## Host tools (normal python)
`python wb.py grid|crop|compare|sheet|mask|profile|snap|glb` — see `wb.py -h` and docs/03.

## PBR materials & imported models (docs/11)
- `pbrlib.scan()/find(name)` — texture-set library (`downloaded_resources/materials`, `library/materials`,
  `$WB_PBR_LIBRARY`); `wb.py pbr list|preview` (labelled material-ball sheet).
- `pbr.material(name, set, tile_m, uv_m=2.0)` or palette entry `dict(pbr=..., tile_m=...)` in
  `materials.ensure`; workbench meshes: `uv_m=2.0`.
- `assets.import_model / apply_transforms / transform / fit_to / join / split / decimate(cad=True) /
  inspect`; `wb.py inspect <file> [--render]`.

## Extending the library
Add a builder only after it worked in a project; keep it context-free (bmesh/bpy.data), end in
`mesh.finish()`, document it in the table above, add one assertion to `templates/smoke_test.py`,
run `python wb.py test`.
