"""Reproducible body topology review; diagnostics are observations, not Class-A certification."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
from workbench.bl import presentation as pres,scene
ROOT=Path(__file__).resolve().parents[2]
A='VEH_DeLorean_Vision';OUT=ROOT/'output'/A/'work'/'topology';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output'/A/'blend'/f'{A}_S2_LOWPOLY.blend'))
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_LP')]
for c in ['10_S1_PRIMITIVE','20_S2_LOWPOLY','30_S3_DETAIL','40_S4_GAME']:
    if c in bpy.data.collections:scene.set_collection_visible(c,c=='20_S2_LOWPOLY')
for o in bpy.data.objects:
    if o.type=='MESH':o.hide_render=o not in objs
body=bpy.data.objects['BODY_Main_LP'];bm=bmesh.new();bm.from_mesh(body.data)
ratios=[];visible=[]
for f in bm.faces:
    lengths=[e.calc_length() for e in f.edges]
    ratio=max(lengths)/max(min(lengths),1e-12);ratios.append(ratio)
    c=f.calc_center_median()
    if c.z>.48 and abs(c.y)<2.10 and len(f.verts)==4:visible.append(ratio)
report={'body_faces':len(bm.faces),'body_quad_percent':round(100*sum(len(f.verts)==4 for f in bm.faces)/len(bm.faces),2),
        'body_boundary_edges':sum(e.is_boundary for e in bm.edges),'body_non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
        'visible_quad_aspect_p95':round(float(np.percentile(visible,95)),2),'visible_quads_aspect_over20':sum(r>20 for r in visible),
        'note':'Aspect ratio compares longest/shortest edge, not CAD curvature continuity. End caps and the localized intake use triangles.'}
bm.free();(OUT/'topology.json').write_text(json.dumps(report,indent=2));print('[TOPOLOGY]',report)
# Explicit quad-edge geometry avoids shader wireframes that show triangulation.
m=bpy.data.materials.new('AUDIT_QuadEdges');m.diffuse_color=(.004,.008,.012,1);m.use_nodes=True
b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.004,.008,.012,1);b.inputs['Roughness'].default_value=.7
for o in objs:
    if o.name.startswith(('BODY_','DOOR_Skin')):
        o.data.materials.append(m);w=o.modifiers.new('AUDIT_QuadWire','WIREFRAME');w.thickness=.001;w.use_replace=False;w.material_offset=len(o.data.materials)-1
pres.studio(objs,'clay');cams=pres.hero_cameras(objs,{'WIRE_FRONT':(35,23,65,.07,(1600,900)),'WIRE_SIDE':(90,12,85,.07,(1600,900))})
# Clay override would recolor the wire too: restore and set steel to flat clay.
pres.clay_override(objs,False)
for name in ['MAT_STEEL','MAT_ALLOY']:
    b=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.42,.45,.48,1);b.inputs['Metallic'].default_value=0;b.inputs['Roughness'].default_value=.65
pres.render_stills(cams,str(OUT),'','CYCLES',64)
