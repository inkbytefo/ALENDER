"""Project bake adapter: one evaluated source, isolated scene, explicit progress.

The editable hero remains separate. Only transient evaluated copies are joined.
Metallic is disabled for DIFFUSE/COLOR only, so steel albedo does not bake black.
"""
import time
import bpy
from workbench.bl import game

_bake = game.bake

def bake(high, low_objs, folder, size=2048, prefix='T', **kw):
    original_maps = game.BAKE_MAPS
    state = [(o,o.hide_render,o.hide_get()) for o in bpy.data.objects if o.type=='MESH']
    copies=[]
    source=None
    metal=[]
    try:
        # Evaluate one dependency graph snapshot; repeated graph updates after each
        # temporary object caused quadratic preparation cost on detailed vehicles.
        dg=bpy.context.evaluated_depsgraph_get()
        coll=bpy.data.collections['40_S4_GAME']
        for o in high:
            me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
            copy=bpy.data.objects.new('TEMP_Bake_'+o.name,me)
            copy.matrix_world=o.matrix_world.copy();coll.objects.link(copy);copies.append(copy)
        for o,_,_ in state:
            o.hide_render=True
            o.hide_set(True)
        for o in bpy.context.view_layer.objects:o.select_set(False)
        for o in copies:
            o.hide_render=False;o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=copies[0]
        bpy.ops.object.join()
        source=bpy.context.view_layer.objects.active
        source.name='TEMP_EvaluatedBakeSource'
        mats={m for m in source.data.materials if m}
        for m in mats:
            b=game._principled(m)
            if b:metal.append((b.inputs['Metallic'],b.inputs['Metallic'].default_value))
        class Maps:
            def __iter__(self):
                for key,kind,nc in original_maps:
                    if key=='base':
                        for socket,_ in metal:socket.default_value=0
                    t=time.time()
                    print(f'[VISION BAKE] begin {key}: {size}px',flush=True)
                    yield key,kind,nc
                    for socket,value in metal:socket.default_value=value
                    print(f'[VISION BAKE] end {key}: {time.time()-t:.1f}s',flush=True)
        game.BAKE_MAPS=Maps()
        print(f'[VISION BAKE] {len(high)} editable sources consolidated transiently',flush=True)
        kw.setdefault('extrusion',.006)
        kw.setdefault('margin',16)
        result=_bake([source],low_objs,folder,size,prefix=prefix,**kw)
        filter_orm(result['orm'])
        result['stats']['ao_encoding']='3-tap denoise, 6-bit AO in an 8-bit ORM PNG'
        return result
    finally:
        game.BAKE_MAPS=original_maps
        for socket,value in metal:socket.default_value=value
        if source is not None and source.name in bpy.data.objects:
            bpy.data.objects.remove(source,do_unlink=True)
        for o,render,hidden in state:
            if o.name in bpy.data.objects:o.hide_render=render;o.hide_set(hidden)


from workbench.bl import uv
from workbench import stages
import math

_atlas=uv.atlas
_copies=game.copies

def atlas(objs,uv_m=2.0,**kw):
    # Repack the whole atlas with concave island bounds and explicit pixel padding.
    # Smart-project's default packing wasted most of the atlas on thin wheel islands.
    objs=list(objs);_atlas(objs,uv_m=uv_m,**kw)
    for ob in objs:ob.data.uv_layers.active_index=ob.data.uv_layers.find('UV_Bake')
    uv._select_only(objs);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True,scale=True,shape_method='CONCAVE',margin_method='FRACTION',margin=.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    area=tex=0.0
    for ob in objs:
        a,u=uv._areas(ob,'UV_Bake');area+=a;tex+=u
    scale=math.sqrt(area/tex)/uv_m
    for ob in objs:
        bake=ob.data.uv_layers['UV_Bake'];main=ob.data.uv_layers[0]
        for i,d in enumerate(main.data):d.uv=bake.data[i].uv*scale
        ob.data.uv_layers.active_index=0
    return dict(area3d_m2=round(area,4),atlas_coverage=round(tex,3),texel_px_per_m_at_2k=round(2048*math.sqrt(tex/area),1))

def copies(objs,lod,coll,keep_uv='UV_Bake'):
    result=_copies(objs,lod,coll,keep_uv)
    import parts
    for tire in parts.PIVOTS:
        keys=[tire]+[child for child,parent in parts.CHILDREN.items() if parent==tire and child in result]
        members=[result[k] for k in keys if k in result]
        joined=game.merge(members,'TEMP_Merged_'+tire,coll)
        for key in keys:
            ob=result.pop(key,None)
            if ob and ob!=joined:bpy.data.objects.remove(ob,do_unlink=True)
        joined.name=tire+'_LOD'+str(lod)
        result[tire]=joined
    return result


def filter_orm(path):
    # AO's Monte Carlo speckle dominated the PNG size. Preserve roughness/metallic
    # exactly; lightly denoise AO and encode it at 64 levels (<=2/255 quantization).
    import numpy as np
    img=bpy.data.images.load(path,check_existing=True);w,h=img.size
    pix=np.empty(w*h*4,np.float32);img.pixels.foreach_get(pix);pix=pix.reshape(h,w,4)
    a=np.pad(pix[:,:,0],((0,0),(1,1)),mode='edge')
    a=(a[:,:-2]+4*a[:,1:-1]+a[:,2:])/6
    a=np.pad(a,((1,1),(0,0)),mode='edge')
    a=(a[:-2]+4*a[1:-1]+a[2:])/6
    pix[:,:,0]=np.minimum(255,np.round(a*255/4)*4)/255
    img.pixels.foreach_set(pix.ravel());img.filepath_raw=path;img.save()
    # Lossless PNG optimization after encoding. Host Pillow is a workbench dependency.
    import subprocess,shutil
    code='from PIL import Image; import sys; p=sys.argv[1]; im=Image.open(p); out=im.copy(); im.close(); out.save(p,optimize=True,compress_level=9)'
    subprocess.run([shutil.which('python'),'-c',code,path],check=True)
