# Headless Godot 4 import check of a .glb (python wb.py engine-check <file.glb>, needs $GODOT_EXECUTABLE).
#   godot --headless --script scripts/godot_import_check.gd -- <abs path to .glb>
# Prints GODOT_IMPORT_OK with mesh / collision / material counts, exit 1 on failure.
# NOTE: written for Godot 4.x runtime GLTFDocument; not verified in this repo yet (Godot not installed).
extends SceneTree

var meshes := 0
var tris := 0
var colliders := 0
var materials := {}


func _walk(n: Node) -> void:
	if n is MeshInstance3D and n.mesh:
		meshes += 1
		for s in n.mesh.get_surface_count():
			var arr = n.mesh.surface_get_arrays(s)
			var idx = arr[Mesh.ARRAY_INDEX]
			tris += (idx.size() if idx else arr[Mesh.ARRAY_VERTEX].size()) / 3
			var m = n.mesh.surface_get_material(s)
			if m:
				materials[m.resource_name] = true
	if n.name.ends_with("-convcolonly") or n.name.ends_with("-colonly") or n is CollisionShape3D:
		colliders += 1
	for c in n.get_children():
		_walk(c)


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		print("usage: -- <file.glb>")
		quit(1)
		return
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(args[0], state)
	if err != OK:
		print("GODOT_IMPORT_FAIL error ", err)
		quit(1)
		return
	var root := doc.generate_scene(state)
	_walk(root)
	print("GODOT_IMPORT_OK meshes=%d tris=%d colliders=%d materials=%d" % [meshes, tris, colliders, materials.size()])
	quit(0 if meshes > 0 else 1)
