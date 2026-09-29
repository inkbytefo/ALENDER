"""Non-destructive modifier helpers + the hard-surface / organic smoothing policy.

Policy (learned the hard way, docs/09_LESSONS_LEARNED.md):
  * hard-surface parts built as extruded plates/boxes -> bevel + weighted normal, NEVER subsurf
    (subsurf shrinks plates into blobs or makes them vanish).
  * organic lofts (seats, tanks, bodies, characters) -> subsurf, viewport/export L1, render L2.
"""
import math
import bpy


def subsurf(ob, levels=1, render=2):
    m = ob.modifiers.new("Subdivision", "SUBSURF")
    m.levels = levels
    m.render_levels = render
    return m


def bevel(ob, width=0.003, segments=2, angle=35.0):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    return m


def weighted_normal(ob):
    m = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    m.keep_sharp = True
    return m


def mirror_x(ob, clip=True):
    m = ob.modifiers.new("Mirror", "MIRROR")
    m.use_axis[0] = True
    m.use_clip = clip
    return m


def solidify(ob, thickness=0.003, offset=-1.0):
    m = ob.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness = thickness
    m.offset = offset
    return m


def array(ob, count, offset=(1, 0, 0), relative=True):
    m = ob.modifiers.new("Array", "ARRAY")
    m.count = count
    m.use_relative_offset = relative
    m.use_constant_offset = not relative
    if relative:
        m.relative_offset_displace = offset
    else:
        m.constant_offset_displace = offset
    return m


def boolean(ob, cutter, op="DIFFERENCE", apply=False, hide_cutter=True):
    """Boolean with a cutter object (windows, doors, holes). apply=True bakes it."""
    m = ob.modifiers.new("Boolean_" + cutter.name, "BOOLEAN")
    m.operation = op
    m.object = cutter
    m.solver = "EXACT"
    if hide_cutter:
        cutter.hide_render = True
        cutter.display_type = "WIRE"
    if apply:
        apply_all(ob)
    return m


def apply_all(ob):
    """Bake every modifier into the mesh without bpy.ops (context-free)."""
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = new
    if old.users == 0:
        bpy.data.meshes.remove(old)


def finish_hard(ob, bevel_w=0.003, enabled=True):
    """hard-surface finishing: bevel + weighted normals (no subdivision)."""
    if enabled and bevel_w:
        bevel(ob, bevel_w)
        weighted_normal(ob)
    return ob


def finish_organic(ob, render_levels=2):
    subsurf(ob, 1, render_levels)
    return ob
