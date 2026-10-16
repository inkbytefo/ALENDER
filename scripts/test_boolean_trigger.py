import sys
import bpy
import bmesh
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")

import landmarks as L
from workbench.bl import mesh, materials

palette = {
    "MAT_GUN_STEEL": ((0.08, 0.085, 0.09), 0.8, 0.35),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
materials.ensure(palette)
mesh.set_ref(L.REF)

coll = "Collection"

# Create frame
ob_frame = mesh.plate("FRAME_Main_PRIM", coll, L.FRAME_POLY, -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")

# Trigger hole poly
TRIGGER_HOLE_POLY = [
    (974.0, 606.0), (1017.0, 607.0), (1057.0, 615.0), (1083.0, 631.0),
    (1106.0, 663.0), (1112.0, 703.0), (1103.0, 739.0), (1074.0, 776.0),
    (1042.0, 794.0), (998.0, 800.0), (938.0, 799.0), (900.0, 759.0),
    (888.0, 733.0), (884.0, 697.0), (887.0, 676.0), (899.0, 648.0),
    (938.0, 608.0), (974.0, 606.0)
]

ob_cutter = mesh.plate("CUTTER", coll, TRIGGER_HOLE_POLY, -0.05, 0.05, "MAT_GUN_STEEL")

# Boolean cut
mod = ob_frame.modifiers.new("CutTrigger", 'BOOLEAN')
mod.object = ob_cutter
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'

bpy.context.view_layer.objects.active = ob_frame
bpy.ops.object.modifier_apply(modifier="CutTrigger")

bpy.data.objects.remove(ob_cutter, do_unlink=True)

# Triangulate n-gons
me = ob_frame.data
bm = bmesh.new()
bm.from_mesh(me)
ngons = [f for f in bm.faces if len(f.verts) > 4]
if ngons:
    bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(me)
    me.update()
bm.free()

tris = sum(len(p.vertices) - 2 for p in me.polygons)
print(f"Cut frame successfully! Tris: {tris}")
