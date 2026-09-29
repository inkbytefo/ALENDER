# 08 — Blender 5.2 API notes (verified on 5.2.1 LTS, Windows)

Don't guess API names — probe with a 10-line script (`python wb.py run probe.py`) and print
`[p.identifier for p in X.bl_rna.properties]` or enum items.

| Topic | Fact |
|-------|------|
| Run headless | `blender --background --factory-startup --python-exit-code 1 --python s.py` (wb.py does it). `--factory-startup` skips user add-ons (their logs pollute output) |
| Engines | `BLENDER_WORKBENCH`, `BLENDER_EEVEE` (not `_NEXT`), `CYCLES` |
| Video | `image_settings.media_type = "VIDEO"`, then `file_format = "FFMPEG"`; reset `media_type="IMAGE"` for stills |
| Materials | `Material.use_nodes = True` prints a deprecation warning (removal in 6.0) but is still required; Principled inputs: `"Base Color"`, `"Emission Color"`, `"Emission Strength"`, `"Alpha"` |
| Auto smooth | `mesh.use_auto_smooth` is gone (4.1+). Set `bm` edge `.smooth` flags by angle (mesh.finish does) or use Weighted Normal modifier |
| Crease | edge crease = float attribute `crease_edge`; in bmesh `bm.edges.layers.float.new("crease_edge")` |
| Workbench colours | Workbench MATERIAL mode uses `material.diffuse_color`, not the node tree — set both (materials.ensure does) |
| BVH overlap | `BVHTree.FromObject` is in LOCAL space; build from world-space verts (`FromPolygons`) to compare objects with different origins |
| Evaluated mesh | `ob.evaluated_get(depsgraph).to_mesh()` … always `to_mesh_clear()` |
| Apply modifiers without ops | `bpy.data.meshes.new_from_object(ob.evaluated_get(dg))` then swap `ob.data` (mods.apply_all) |
| Armature | edit bones need `bpy.ops.object.mode_set(mode="EDIT")` with the armature active — works in background; `parent_set(type="ARMATURE_AUTO")` works too |
| Skin modifier | `mesh.skin_vertices[0].data[i].radius = (rx, ry)`, mark one `use_root` |
| Actions | 4.4+/5.x use layered actions: fcurves live in `action.layers[].strips[].channelbags[].fcurves` (anim._fcurves handles both) |
| Camera euler | look +X `(90°, roll, −90°)`, look −X `(90°, roll, 90°)`; roll is the middle (Y) component in XYZ order |
| Image empty | `empty_display_type="IMAGE"`, `ob.data = image`, `empty_display_size` = width in m, offset (−0.5, −0.5) centres it |
| glTF | `export_scene.gltf(export_format="GLB", export_yup=True, export_apply=True, use_selection=True)`; import with `import_scene.gltf` |
| Save | `wm.save_as_mainfile(filepath=…, check_existing=False)` writes `.blend1` backups next to it — harmless |
| webp | Pillow reads webp; convert references to PNG for Blender image empties and tools |
