import sys
sys.path.insert(0, ".")
sys.path.insert(0, "projects/PROP_Colt_1911")
import bpy
import bmesh
import landmarks as L
from workbench.bl import mesh, materials, validate

palette = {"MAT_WOOD_GRIP": ((0.28, 0.16, 0.09), 0.0, 0.65)}
bpy.ops.wm.read_factory_settings(use_empty=True)
materials.ensure(palette)
mesh.set_ref(L.REF)

ob = mesh.plate("GRIP_Panels_L_LP", "Collection", L.GRIP_PANEL_POLY,
                L.FRAME_HALF_WIDTH, L.GRIP_HALF_WIDTH, "MAT_WOOD_GRIP")
me = ob.data
bm = bmesh.new()
bm.from_mesh(me)

# Find outer face
outer = [f for f in bm.faces if f.normal.x > 0.9]
if outer:
    # Subdivide outer face
    res = bmesh.ops.subdivide_edges(bm, edges=[e for f in outer for e in f.edges], cuts=5, use_grid_fill=True)
    # Triangulate
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)

bm.to_mesh(me)
me.update()
bm.free()

print(f"Grip tris: {sum(len(p.vertices) - 2 for p in me.polygons)}")
hy = validate.hygiene([ob])
print(f"Hygiene: {hy['total']}")
