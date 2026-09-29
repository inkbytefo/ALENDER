"""Instanced fastener families: one shared mesh, many linked-duplicate objects."""
import bpy
import bmesh
from mathutils import Vector
from workbench.bl.scene import coll

FAMILIES = {  # name: (head radius, head height) metres
    "BOLT_M5": (0.0040, 0.0035), "BOLT_M6": (0.0050, 0.0040), "BOLT_M8": (0.0065, 0.0050),
    "BOLT_M10": (0.0080, 0.0060), "NUT": (0.0120, 0.0090), "WASHER": (0.0100, 0.0015),
}


def family_mesh(name, r_head=None, h_head=None):
    """Hex head mesh, origin on the bearing face, axis +Z. Created once, reused."""
    me = bpy.data.meshes.get(name)
    if me:
        return me
    r_head, h_head = (r_head, h_head) if r_head else FAMILIES[name]
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r_head, radius2=r_head * 0.93,
                          depth=h_head)
    bmesh.ops.translate(bm, vec=Vector((0, 0, h_head / 2)), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.new(name="UVMap")
    return me


class Fasteners:
    """fs = Fasteners("07_DETAILS"); fs.place("BOLT_M6", loc, normal)  -> FASTENER_BOLT_M6_001"""

    def __init__(self, collection, mat="MAT_METAL_RAW"):
        self.collection, self.mat, self.k = collection, mat, 0

    def place(self, kind, loc, normal):
        me = family_mesh(kind)
        if not me.materials:
            me.materials.append(bpy.data.materials[self.mat])
        self.k += 1
        ob = bpy.data.objects.new(f"FASTENER_{kind}_{self.k:03d}", me)
        ob.location = loc
        ob.rotation_euler = Vector(normal).to_track_quat("Z", "Y").to_euler()
        coll(self.collection).objects.link(ob)
        return ob

    def ring(self, kind, center, normal, radius, count, phase=0.0):
        """bolt circle on a cover: center, face normal, pitch radius."""
        import math
        from workbench.bl.mesh import frame_for
        n1, n2 = frame_for(normal)
        return [self.place(kind, Vector(center) + radius * (math.cos(phase + 2 * math.pi * i / count) * n1
                                                            + math.sin(phase + 2 * math.pi * i / count) * n2),
                           normal) for i in range(count)]

    @staticmethod
    def shared_mesh_names():
        return set(FAMILIES)
