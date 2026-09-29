"""Scene, collections, save/open, origins and hierarchy."""
import os
import bpy
from mathutils import Vector, Matrix

# Standard collection layout (docs/02_STANDARDS.md). LOW = Stage 1, HIGH = Stage 2.
COLLECTIONS = ["00_REFERENCE", "01_GUIDES", "02_LOW_PRIMARY", "03_LOW_SECONDARY",
               "04_LOW_MECHANICAL", "05_HIGH_BODY", "06_HIGH_MECHANICAL", "07_DETAILS",
               "08_TEMP", "09_PRESENTATION"]
LOW_COLLS = ("02_LOW_PRIMARY", "03_LOW_SECONDARY", "04_LOW_MECHANICAL")
HIGH_COLLS = ("05_HIGH_BODY", "06_HIGH_MECHANICAL", "07_DETAILS")


def reset(fps=30):
    """Empty factory scene, metric units, 1 BU = 1 m."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = "METERS"
    sc.render.fps = fps
    return sc


def open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)


def save(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
    print("[SAVE]", path)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def setup_collections(names=COLLECTIONS):
    for n in names:
        coll(n)


def set_collection_visible(name, visible):
    c = coll(name)
    c.hide_render = not visible
    c.hide_viewport = not visible


def objects_in(colls):
    return [o for c in colls for o in coll(c).all_objects]


def empty(name, loc=(0, 0, 0), collection="01_GUIDES", kind="PLAIN_AXES", size=0.05):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    ob.location = loc
    coll(collection).objects.link(ob)
    return ob


def guides(points, collection="01_GUIDES", size=0.03):
    """points {NAME: (x,y,z)} -> sphere empties GUIDE_<NAME> (the skeleton of the model)."""
    return {n: empty("GUIDE_" + n, p, collection, "SPHERE", size) for n, p in points.items()}


def set_origin(ob, pt):
    """Move object origin to world point pt without moving geometry (single-user meshes only)."""
    pt = Vector(pt)
    ob.data.transform(Matrix.Translation(-(pt - ob.matrix_world.translation)))
    ob.matrix_world = Matrix.Translation(pt)


def origin_to_bbox_center(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    set_origin(ob, sum(bb, Vector()) / 8.0)


def root(name, collection="09_PRESENTATION"):
    """Single asset root empty (docs/02: hierarchy root = asset name, at world origin)."""
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    if ob.name not in coll(collection).objects:
        coll(collection).objects.link(ob)
    ob.empty_display_type = "ARROWS"
    ob.empty_display_size = 0.3
    return ob


def parent_keep(obs, parent):
    for ob in obs:
        mw = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
        ob.matrix_world = mw
