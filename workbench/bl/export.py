"""glTF / FBX export and the U15 round-trip check (re-import, compare counts)."""
import os
import bpy


def glb(objs, path, animations=False, skins=False):
    """Export exactly `objs` (include the root empty) to .glb, +Y up, modifiers applied."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_yup=True, export_apply=True,
                              use_selection=True, export_cameras=False, export_lights=False,
                              export_animations=animations, export_skins=skins)
    print("[GLB]", path)
    return path


def fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True,
                             axis_forward="-Y", axis_up="Z")
    return path


def roundtrip(path, expected_objects, expected_materials):
    """DESTROYS the current scene: loads an empty one and imports the glb. Save first!
    Returns (ok, detail)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    n = len(bpy.data.objects)
    m = len([x for x in bpy.data.materials if x.users])
    ok = n == expected_objects and m == expected_materials
    return ok, f"exported {expected_objects} objs / reimported {n}; materials {m}/{expected_materials}"
