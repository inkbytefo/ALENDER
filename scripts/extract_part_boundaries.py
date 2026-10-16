import bpy
import mathutils
from pathlib import Path
import json

src_glb = Path("projects/PROP_Colt_1911/ref/SOURCE_M1911A1.glb").resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src_glb))

S = 2048.0 / 0.28
def world_to_uv(x, z):
    u = 1024.0 + (x - 0.065) * S
    v = 768.0 - (z - 0.025) * S
    return u, v

# Extract 2D boundary of an object using convex hull or projected boundary
import sys
sys.path.insert(0, ".")
from workbench.silhouette import simplify

parts_to_extract = ["Frame_LOW", "Slide_LOW", "Hammer_LOW", "Trigger_LOW"]

for name in parts_to_extract:
    obj = bpy.data.objects.get(name)
    if not obj:
        continue
    mw = obj.matrix_world
    pts = [world_to_uv((mw @ v.co).x, (mw @ v.co).z) for v in obj.data.vertices]
    # Compute 2D convex hull of pts
    # Or find boundary edges (edges with 1 face or silhouette edges from +Y)
    print(f"{name}: {len(pts)} vertices")

    # Let's find silhouette edges when viewed from -Y towards +Y:
    # An edge is a silhouette edge if its faces have dot products with view vector (0, 1, 0) of opposite signs!
    # Here view is ortho along Y (+Y direction). Face normal Ny:
    # A face is front-facing if Ny < 0, back-facing if Ny > 0.
    # An edge between front and back face is on the silhouette!
    sil_edges = []
    me = obj.data
    me.calc_normals()
    for e in me.edges:
        linked_faces = [f for f in me.polygons if e.index in f.edge_keys or (e.vertices[0] in f.vertices and e.vertices[1] in f.vertices)]
        if len(linked_faces) == 1:
            sil_edges.append(e)
        elif len(linked_faces) >= 2:
            n1 = (mw.to_3x3() @ linked_faces[0].normal).y
            n2 = (mw.to_3x3() @ linked_faces[1].normal).y
            if (n1 * n2) <= 0:
                sil_edges.append(e)

    print(f"  {len(sil_edges)} silhouette edges found.")
