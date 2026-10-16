import bpy
import mathutils
import os
from pathlib import Path

pistols_dir = Path("AssetM\u0131grat\u0131onFromPublictoUS/RawAssets/Weapons_Firearms/Pistols")

models = [
    ("colt-m1911-a1-game-ready-rigged", pistols_dir / "colt-m1911-a1-game-ready-rigged/source/M1911A1.glb"),
    ("pistol-9mm-semi-auto (Glock 19)", pistols_dir / "pistol-9mm-semi-auto/source/G19_Hitansh3D.fbx"),
    ("pistol-with-engravings (Colt M1911 Engraved)", pistols_dir / "pistol-with-engravings/source/colt low polyfbx.fbx"),
    ("9mm-pistol (Browning/Walther style)", pistols_dir / "9mm-pistol/source/9mmPistol.fbx"),
    ("pistol-9mm (Hi-Point/Standard)", pistols_dir / "pistol-9mm/source/HIpistol.fbx"),
    ("animated-pistol (Beretta with Arms)", pistols_dir / "animated-pistol/source/arms@beretta.fbx"),
    ("fps-pistol-animated (Arms + Pistol)", pistols_dir / "fps-pistol-animated/source/arms@bpPistol.fbx"),
    ("fps-pistol-animations (Arms + Pistol)", pistols_dir / "fps-pistol-animations/source/Armpist.fbx"),
]

print("\n" + "=" * 80)
print("PISTOL ASSETS INSPECTION REPORT (BLENDER)")
print("=" * 80)

for name, path in models:
    if not path.exists():
        print(f"[MISSING] {name}: {path}")
        continue

    # Reset scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import
    ext = path.suffix.lower()
    try:
        if ext in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=str(path))
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
        elif ext == ".obj":
            bpy.ops.wm.obj_import(filepath=str(path))
    except Exception as e:
        print(f"[ERROR importing {name}]: {e}")
        continue

    # Analyze objects
    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    armature_objs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    
    total_tris = 0
    total_verts = 0
    total_faces = 0
    
    # Calculate bounding box of all mesh objects
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    obj_details = []
    for obj in mesh_objs:
        me = obj.data
        verts = len(me.vertices)
        faces = len(me.polygons)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        total_tris += tris
        total_verts += verts
        total_faces += faces
        obj_details.append((obj.name, tris, verts))

        # bbox
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ mathutils.Vector(corner)
            min_x = min(min_x, world_co.x)
            max_x = max(max_x, world_co.x)
            min_y = min(min_y, world_co.y)
            max_y = max(max_y, world_co.y)
            min_z = min(min_z, world_co.z)
            max_z = max(max_z, world_co.z)

    dim_x = max_x - min_x if min_x != float('inf') else 0
    dim_y = max_y - min_y if min_y != float('inf') else 0
    dim_z = max_z - min_z if min_z != float('inf') else 0

    materials = [mat.name for mat in bpy.data.materials]

    print(f"\n--- {name} ---")
    print(f"  File: {path.name} ({path.stat().st_size / 1024:.1f} KB)")
    print(f"  Mesh objects: {len(mesh_objs)} | Armatures: {len(armature_objs)}")
    print(f"  Total Tris: {total_tris:,} | Vertices: {total_verts:,} | Polygons: {total_faces:,}")
    print(f"  Dimensions: {dim_x:.3f}m x {dim_y:.3f}m x {dim_z:.3f}m")
    print(f"  Materials ({len(materials)}): {materials[:6]}")
    print(f"  Objects Breakdown (first 8):")
    for oname, otris, overts in obj_details[:8]:
        print(f"    - {oname}: {otris:,} tris, {overts:,} verts")

print("\n" + "=" * 80)
