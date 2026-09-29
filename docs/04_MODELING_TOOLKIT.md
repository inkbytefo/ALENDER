# 04 — Modelling toolkit (library map + techniques)

All geometry is procedural (bmesh) and idempotent: calling a builder again replaces the object.
Import inside Blender scripts:
```python
from workbench import paths, tables                      # pure python
from workbench.refmap import RefMap
from workbench.bl import scene, mesh, mods, materials, cameras, render, anim, rig, validate, export
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
| openings | `mods.boolean(obj, cutter, apply=True)` | doors/windows in walls, holes in plates |

Photo-driven builders read pixels through the active RefMap: `mesh.set_ref(L.REF)` once in parts.py.
Loft stations: `(u, v_top, v_bot, half_width_m, e_top, e_bot, widest)`; build them from landmark
polylines with `tables.polyline_v(poly, u)` and a width table `tables.interp(table, u)`.
Superellipse exponents: 2 = ellipse, 2.5 = soft crown, 4–7 = boxy; `widest` = fraction of height
(from the bottom) where the section is widest.

## LOD profiles (one builder, two stages)
`parts.py` defines `LOW` and `HIGH` dicts (segments, stations, loft ring count, bevel on/off,
target collections). Every builder takes `lod`. Stage 2 = same function with `HIGH` ⇒ geometry
refines while proportions stay locked to landmarks. Name LOW objects via `nm(lod, name)` (adds `_LOW`).

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
- `cameras.review_rig(center, length, width)` / `rig_from_bounds(objs)` — 5 orthos + 2 perspectives.
- `render.workbench(cam, path, "CLAY"|"MATERIAL", transparent=True)` — fast review; transparent
  RGBA for overlays. `render.review_set(cams, folder, tag)` renders the whole rig.
- `render.studio_lights()` + `render.beauty(cam, path, engine="BLENDER_EEVEE"|"CYCLES")`.
- Video: `anim.turntable()` + `render.animation(cam, "x.mp4", 1, 240)` (docs/07).

## Host tools (normal python)
`python wb.py grid|crop|compare|sheet` — see `wb.py -h`.

## Extending the library
Add a builder only after it worked in a project; keep it context-free (bmesh/bpy.data), end in
`mesh.finish()`, document it in the table above, add one assertion to `templates/smoke_test.py`,
run `python wb.py test`.
