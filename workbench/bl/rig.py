"""Characters & rigs: skin-modifier blockouts from a joint graph, armatures, auto-weight binding.

Typical character flow (docs/06_CATEGORIES.md#characters):
  1. joints = {"Hips": (0,0,0.95), ...}; bones = [("Spine", "Hips", "Chest"), ...]
  2. body = skin_body("CHR_Body_LOW", joints, edges, radii)          # Stage 1 volume blockout
  3. arm  = armature("CHR_Rig", bones_from_joints(joints, bones))    # humanoid names
  4. bind_auto(body, arm)                                            # ARMATURE_AUTO weights
"""
import bpy
from mathutils import Vector
from workbench.bl.scene import coll


def skin_body(name, collection, joints, edges, radii, mat=None, subsurf=2, apply=False):
    """Skin-modifier volume from a joint graph.
    joints {name: (x,y,z)}, edges [(a, b), ...] by joint name, radii {name: r | (rx, ry)}."""
    names = list(joints)
    idx = {n: i for i, n in enumerate(names)}
    me = bpy.data.meshes.new(name + "_Mesh")
    me.from_pydata([joints[n] for n in names], [(idx[a], idx[b]) for a, b in edges], [])
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = True
    for n, i in idx.items():
        r = radii.get(n, 0.05)
        rr = (r, r) if isinstance(r, (int, float)) else r
        me.skin_vertices[0].data[i].radius = rr
    root = names[0]
    me.skin_vertices[0].data[idx[root]].use_root = True
    if subsurf:
        m = ob.modifiers.new("Subdivision", "SUBSURF")
        m.levels = 1
        m.render_levels = subsurf
    if mat:
        me.materials.append(bpy.data.materials[mat])
    if apply:
        from workbench.bl.mods import apply_all
        apply_all(ob)
        ob.data.uv_layers.new(name="UVMap")
    return ob


def bones_from_joints(joints, chain):
    """chain [(bone, head_joint, tail_joint, parent_bone|None), ...] -> bone specs."""
    return [(b, joints[h], joints[t], p) for (b, h, t, p) in chain]


def armature(name, bone_specs, collection="06_HIGH_MECHANICAL", show_in_front=True):
    """bone_specs [(name, head, tail, parent|None), ...]. Needs EDIT mode (works headless)."""
    arm = bpy.data.armatures.new(name + "_Data")
    ob = bpy.data.objects.new(name, arm)
    coll(collection).objects.link(ob)
    ob.show_in_front = show_in_front
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for (bn, h, t, p) in bone_specs:
        b = arm.edit_bones.new(bn)
        b.head, b.tail = Vector(h), Vector(t)
        eb[bn] = b
    for (bn, h, t, p) in bone_specs:
        if p:
            eb[bn].parent = eb[p]
            eb[bn].use_connect = (eb[p].tail - eb[bn].head).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def bind_auto(mesh_ob, arm_ob):
    """Parent with automatic weights (ARMATURE_AUTO). Mesh must be applied (no skin modifier)."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh_ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    res = bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    return res, [g.name for g in mesh_ob.vertex_groups]


def pose_key(arm_ob, frame, rotations):
    """rotations {bone: (x,y,z) euler radians} -> keyframes on pose bones."""
    for bn, r in rotations.items():
        pb = arm_ob.pose.bones[bn]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = r
        pb.keyframe_insert("rotation_euler", frame=frame)


HUMANOID_JOINTS = {   # 1.75 m adult, T-pose, facing -Y. Scale with height/1.75.
    "Hips": (0, 0, 0.95), "Spine": (0, 0, 1.08), "Chest": (0, 0, 1.25), "Neck": (0, 0, 1.47),
    "Head": (0, 0, 1.58), "HeadTop": (0, 0, 1.75),
    "L_Shoulder": (0.19, 0, 1.43), "L_Elbow": (0.47, 0, 1.43), "L_Wrist": (0.72, 0, 1.43), "L_Hand": (0.82, 0, 1.43),
    "R_Shoulder": (-0.19, 0, 1.43), "R_Elbow": (-0.47, 0, 1.43), "R_Wrist": (-0.72, 0, 1.43), "R_Hand": (-0.82, 0, 1.43),
    "L_Hip": (0.1, 0, 0.92), "L_Knee": (0.1, 0.01, 0.5), "L_Ankle": (0.1, 0.03, 0.08), "L_Toe": (0.1, -0.12, 0.02),
    "R_Hip": (-0.1, 0, 0.92), "R_Knee": (-0.1, 0.01, 0.5), "R_Ankle": (-0.1, 0.03, 0.08), "R_Toe": (-0.1, -0.12, 0.02),
}
HUMANOID_EDGES = [("Hips", "Spine"), ("Spine", "Chest"), ("Chest", "Neck"), ("Neck", "Head"), ("Head", "HeadTop"),
                  ("Chest", "L_Shoulder"), ("L_Shoulder", "L_Elbow"), ("L_Elbow", "L_Wrist"), ("L_Wrist", "L_Hand"),
                  ("Chest", "R_Shoulder"), ("R_Shoulder", "R_Elbow"), ("R_Elbow", "R_Wrist"), ("R_Wrist", "R_Hand"),
                  ("Hips", "L_Hip"), ("L_Hip", "L_Knee"), ("L_Knee", "L_Ankle"), ("L_Ankle", "L_Toe"),
                  ("Hips", "R_Hip"), ("R_Hip", "R_Knee"), ("R_Knee", "R_Ankle"), ("R_Ankle", "R_Toe")]
HUMANOID_RADII = {"Hips": (0.16, 0.11), "Spine": (0.14, 0.1), "Chest": (0.17, 0.11), "Neck": 0.055, "Head": 0.1,
                  "HeadTop": 0.08, "L_Shoulder": 0.06, "R_Shoulder": 0.06, "L_Elbow": 0.045, "R_Elbow": 0.045,
                  "L_Wrist": 0.035, "R_Wrist": 0.035, "L_Hand": 0.04, "R_Hand": 0.04, "L_Hip": 0.085, "R_Hip": 0.085,
                  "L_Knee": 0.06, "R_Knee": 0.06, "L_Ankle": 0.045, "R_Ankle": 0.045, "L_Toe": 0.04, "R_Toe": 0.04}
# Godot-style humanoid bone names
HUMANOID_BONES = [
    ("Hips", "Hips", "Spine", None), ("Spine", "Spine", "Chest", "Hips"), ("Chest", "Chest", "Neck", "Spine"),
    ("Neck", "Neck", "Head", "Chest"), ("Head", "Head", "HeadTop", "Neck"),
    ("LeftUpperArm", "L_Shoulder", "L_Elbow", "Chest"), ("LeftLowerArm", "L_Elbow", "L_Wrist", "LeftUpperArm"),
    ("LeftHand", "L_Wrist", "L_Hand", "LeftLowerArm"),
    ("RightUpperArm", "R_Shoulder", "R_Elbow", "Chest"), ("RightLowerArm", "R_Elbow", "R_Wrist", "RightUpperArm"),
    ("RightHand", "R_Wrist", "R_Hand", "RightLowerArm"),
    ("LeftUpperLeg", "L_Hip", "L_Knee", "Hips"), ("LeftLowerLeg", "L_Knee", "L_Ankle", "LeftUpperLeg"),
    ("LeftFoot", "L_Ankle", "L_Toe", "LeftLowerLeg"),
    ("RightUpperLeg", "R_Hip", "R_Knee", "Hips"), ("RightLowerLeg", "R_Knee", "R_Ankle", "RightUpperLeg"),
    ("RightFoot", "R_Ankle", "R_Toe", "RightLowerLeg"),
]
