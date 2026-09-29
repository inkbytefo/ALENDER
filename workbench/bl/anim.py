"""Animation helpers: keyframes, linear/cyclic curves, turntables, camera orbits, wheel spin.

Rules (docs/07_ANIMATION_AND_VIDEO.md): 30 fps default, one Action per clip named like
'idle-loop' / 'door_open', loop clips end on the start pose, bake before glTF export.
"""
import math
import bpy
from mathutils import Vector
from workbench.bl.scene import coll, empty


def key(ob, frame, loc=None, rot=None, scale=None):
    """Insert keys at frame for whichever channels are given (rot in radians, XYZ euler)."""
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        ob.scale = scale
        ob.keyframe_insert("scale", frame=frame)


def _fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):                    # legacy actions
        return list(act.fcurves)
    out = []                                       # layered actions (Blender 4.4+ / 5.x)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def set_interpolation(ob, mode="LINEAR"):
    """LINEAR for mechanical motion / turntables, BEZIER (default) for organic motion."""
    for fc in _fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = mode


def name_action(ob, name, fake_user=True):
    if ob.animation_data and ob.animation_data.action:
        ob.animation_data.action.name = name
        ob.animation_data.action.use_fake_user = fake_user


def turntable(target_center=(0, 0, 0.5), radius=4.0, height=1.2, frames=(1, 240), lens=50,
              name="CAM_TURNTABLE"):
    """Camera orbiting 360 deg around target_center (pivot empty rotates, linear)."""
    from workbench.bl.cameras import make
    c = Vector(target_center)
    pivot = empty("TURNTABLE_PIVOT", c, "09_PRESENTATION", "PLAIN_AXES", 0.2)
    cam = make(name, (0, 0, 0), (0, 0, 0), lens=lens)
    cam.parent = pivot
    cam.location = (0.0, -radius, height)
    d = Vector((0.0, radius, -height + 0.0))
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    key(pivot, frames[0], rot=(0, 0, 0))
    key(pivot, frames[1] + 1, rot=(0, 0, 2 * math.pi))
    set_interpolation(pivot, "LINEAR")
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = frames
    return cam, pivot


def spin(ob, axis="X", turns=1.0, frames=(1, 120), name=None):
    """Constant spin about a local axis (wheels, fans, propellers). Origin must be the pivot."""
    i = "XYZ".index(axis)
    r0 = list(ob.rotation_euler)
    r1 = list(r0)
    r1[i] += 2 * math.pi * turns
    key(ob, frames[0], rot=r0)
    key(ob, frames[1], rot=r1)
    set_interpolation(ob, "LINEAR")
    if name:
        name_action(ob, name)


def move(ob, frames_locs, interpolation="BEZIER", name=None):
    """Keyframe a path: frames_locs = [(frame, (x,y,z)), ...]."""
    for f, p in frames_locs:
        key(ob, f, loc=p)
    set_interpolation(ob, interpolation)
    if name:
        name_action(ob, name)
