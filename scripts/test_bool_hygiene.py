import sys
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")
import bpy
import bmesh
import json
import landmarks as L
from workbench.bl import mesh, materials, validate

palette = {
    "MAT_GUN_STEEL": ((0.08, 0.085, 0.09), 0.8, 0.35),
}
bpy.ops.wm.read_factory_settings(use_empty=True)
materials.ensure(palette)
mesh.set_ref(L.REF)

polys = json.load(open('projects/PROP_Colt_1911/ref/ACCURATE_PART_POLYS.json'))
fp = polys['FRAME_POLY']

th = [
    (974.0, 606.0), (1017.0, 607.0), (1057.0, 615.0), (1083.0, 631.0),
    (1106.0, 663.0), (1112.0, 703.0), (1103.0, 739.0), (1074.0, 776.0),
    (1042.0, 794.0), (998.0, 800.0), (938.0, 799.0), (900.0, 759.0),
    (888.0, 733.0), (884.0, 697.0), (887.0, 676.0), (899.0, 648.0),
    (938.0, 608.0), (974.0, 606.0)
]

ob = mesh.plate("FRAME_Main", "Collection", fp, -0.01125, 0.01125, "MAT_GUN_STEEL")
ob_cutter = mesh.plate("CUTTER", "Collection", th, -0.05, 0.05, "MAT_GUN_STEEL")

mod = ob.modifiers.new("CutTrigger", 'BOOLEAN')
mod.object = ob_cutter
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_apply(modifier="CutTrigger")
bpy.data.objects.remove(ob_cutter, do_unlink=True)

# Triangulate
me = ob.data
bm = bmesh.new()
bm.from_mesh(me)
ngons = [f for f in bm.faces if len(f.verts) > 4]
bmesh.ops.triangulate(bm, faces=ngons)
bm.to_mesh(me)
me.update()
bm.free()

hy = validate.hygiene([ob])
print(f"Tris: {sum(len(p.vertices) - 2 for p in me.polygons)}")
print(f"Hygiene: {hy['total']}")
