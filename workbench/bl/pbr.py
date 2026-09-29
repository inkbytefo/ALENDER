"""
PBR materials from texture sets (workbench.pbrlib) - glTF-exportable Principled BSDF node trees.

    from workbench.bl import pbr
    m = pbr.material("MAT_SEAT_LEATHER", "Leather009", tile_m=0.4)           # by set name
    m = pbr.material("MAT_FRAME", "Metal041B", tile_m=0.5, tint=(0.4, 0.4, 0.42))
    pbr.assign(ob, m)                                                         # replace all slots
    # or in a project palette (materials.ensure understands it):
    PALETTE = {"MAT_SEAT": dict(pbr="Leather009", tile_m=0.4), "MAT_BODY": "paint_gloss", ...}

Node layout (left -> right):
  UV (or Object for projection="BOX") -> Mapping(scale) -> Image Textures
  Color (sRGB) [-> tint multiply]            -> Base Color
  Roughness (Non-Color) [-> Math multiply]   -> Roughness
  Metalness (Non-Color) or constant          -> Metallic
  NormalGL (or NormalDX with green flipped)  -> Normal Map -> [Bump(Displacement)] -> Normal
  Opacity -> Alpha ; Emission -> Emission Color
glTF: Base Color / Roughness / Metallic / Normal Map / Emission / Alpha export as textures when the
image node feeds the socket directly (tint, roughness_mul, BOX projection and bump are Blender-only
refinements - the exporter falls back to the raw texture or factor). Keep tint=None for game assets.

Texture scale: `tile_m` = real size of one texture repeat in metres. `uv_m` = metres per UV unit
of the target mesh: 2.0 for workbench builders (mesh.box_uv uses 0.5 UV/m), 1.0 for most imported
models with real-world UVs. Mapping scale = uv_m / tile_m.
Workbench (viewport / review renders) uses material.diffuse_color: set to the texture's mean colour.
"""
import os
import bpy

from workbench import pbrlib

_MEAN_CACHE = {}


def _image(path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def mean_value(path, channels=3):
    """mean pixel value of an image (sampled) - for Workbench colours / constant fallbacks."""
    if path in _MEAN_CACHE:
        return _MEAN_CACHE[path]
    import numpy as np
    img = bpy.data.images.load(path, check_existing=True)
    arr = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(arr)                       # fast bulk read (2K image ~ 0.1 s)
    rgba = arr.reshape(-1, 4)[::97]
    v = tuple(float(x) for x in rgba[:, :3].mean(0))
    _MEAN_CACHE[path] = v
    return v


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, texset, tile_m=1.0, uv_m=2.0, projection="UV", tint=None, roughness_mul=1.0,
             metallic=None, normal_strength=1.0, bump=0.0, use_ao=False, box_blend=0.25,
             emission_strength=1.0):
    """Create/replace material `name` from a texture set (dict from pbrlib or a set name)."""
    s = pbrlib.find(texset) if isinstance(texset, str) else texset
    mp = s["maps"]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, Lk = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled"); bsdf.location = (550, 0)
    Lk.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-1100, 0)
    mapn = N.new("ShaderNodeMapping"); mapn.location = (-900, 0)
    sc = (uv_m / tile_m) if projection == "UV" else (1.0 / tile_m)
    mapn.inputs["Scale"].default_value = (sc, sc, sc)
    Lk.new(tc.outputs["UV" if projection == "UV" else "Object"], mapn.inputs["Vector"])

    def tex(kind, non_color, y):
        t = N.new("ShaderNodeTexImage")
        t.image = _image(mp[kind], non_color)
        t.location = (-600, y)
        t.label = kind
        if projection == "BOX":
            t.projection = "BOX"
            t.projection_blend = box_blend
        Lk.new(mapn.outputs["Vector"], t.inputs["Vector"])
        return t

    # base colour (+ optional tint / AO multiply)
    if "base_color" in mp:
        t = tex("base_color", False, 400)
        col = t.outputs["Color"]
        if use_ao and "ao" in mp:
            ao = tex("ao", True, 650)
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
            mx.location = (-250, 500); mx.inputs["Factor"].default_value = 1.0
            Lk.new(col, mx.inputs["A"]); Lk.new(ao.outputs["Color"], mx.inputs["B"])
            col = mx.outputs["Result"]
        if tint is not None:
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
            mx.location = (-50, 400); mx.inputs["Factor"].default_value = 1.0
            mx.inputs["B"].default_value = (*tint, 1.0)
            Lk.new(col, mx.inputs["A"])
            col = mx.outputs["Result"]
        Lk.new(col, bsdf.inputs["Base Color"])
    elif tint is not None:
        bsdf.inputs["Base Color"].default_value = (*tint, 1.0)
    # roughness
    if "roughness" in mp:
        t = tex("roughness", True, 100)
        r = t.outputs["Color"]
        if abs(roughness_mul - 1.0) > 1e-6:
            mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.use_clamp = True
            mm.location = (-250, 100); mm.inputs[1].default_value = roughness_mul
            Lk.new(r, mm.inputs[0]); r = mm.outputs["Value"]
        Lk.new(r, bsdf.inputs["Roughness"])
    # metallic
    if metallic is not None:
        bsdf.inputs["Metallic"].default_value = metallic
    elif "metallic" in mp:
        t = tex("metallic", True, -150)
        Lk.new(t.outputs["Color"], bsdf.inputs["Metallic"])
    # normal (OpenGL preferred; DirectX -> flip green)
    nkind = "normal_gl" if "normal_gl" in mp else ("normal" if "normal" in mp else
                                                  ("normal_dx" if "normal_dx" in mp else None))
    nrm_out = None
    if nkind:
        t = tex(nkind, True, -400)
        c = t.outputs["Color"]
        if nkind == "normal_dx":
            sep = N.new("ShaderNodeSeparateColor"); sep.location = (-350, -450)
            inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.location = (-200, -450)
            inv.inputs[0].default_value = 1.0
            comb = N.new("ShaderNodeCombineColor"); comb.location = (-60, -450)
            Lk.new(c, sep.inputs["Color"])
            Lk.new(sep.outputs["Red"], comb.inputs["Red"])
            Lk.new(sep.outputs["Green"], inv.inputs[1]); Lk.new(inv.outputs["Value"], comb.inputs["Green"])
            Lk.new(sep.outputs["Blue"], comb.inputs["Blue"])
            c = comb.outputs["Color"]
        nm = N.new("ShaderNodeNormalMap"); nm.location = (150, -400)
        nm.inputs["Strength"].default_value = normal_strength
        Lk.new(c, nm.inputs["Color"])
        nrm_out = nm.outputs["Normal"]
    if bump > 0 and "displacement" in mp:
        t = tex("displacement", True, -700)
        b = N.new("ShaderNodeBump"); b.location = (350, -600)
        b.inputs["Strength"].default_value = bump
        Lk.new(t.outputs["Color"], b.inputs["Height"])
        if nrm_out is not None:
            Lk.new(nrm_out, b.inputs["Normal"])
        nrm_out = b.outputs["Normal"]
    if nrm_out is not None:
        Lk.new(nrm_out, bsdf.inputs["Normal"])
    if "opacity" in mp:
        t = tex("opacity", True, -950)
        Lk.new(t.outputs["Color"], bsdf.inputs["Alpha"])
    if "emission" in mp:
        t = tex("emission", False, -1200)
        Lk.new(t.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    # Workbench / viewport colour = mean texture colour (linear) x tint
    if "base_color" in mp:
        mc = [_srgb_to_linear(v) for v in mean_value(mp["base_color"])]
    else:
        mc = [0.5, 0.5, 0.5]
    if tint is not None:
        mc = [a * b for a, b in zip(mc, tint)]
    m.diffuse_color = (*mc, 1.0)
    m.roughness = min(1.0, (mean_value(mp["roughness"])[0] if "roughness" in mp else 0.5) * roughness_mul)
    m.metallic = metallic if metallic is not None else (mean_value(mp["metallic"])[0] if "metallic" in mp else 0.0)
    m["pbr_set"] = s["name"]
    m["pbr_tile_m"] = tile_m
    return m


def assign(ob, mat, slot=None):
    """put mat in every slot (slot=None) or one slot index."""
    me = ob.data
    if slot is None:
        me.materials.clear()
        me.materials.append(mat)
        for p in me.polygons:
            p.material_index = 0
    else:
        me.materials[slot] = mat
    return ob


def texture_sets_used(materials):
    """{material name: pbr set name} for reports."""
    return {m.name: m.get("pbr_set") for m in materials if m and m.get("pbr_set")}
