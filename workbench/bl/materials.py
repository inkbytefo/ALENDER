"""Principled materials from compact palettes. glTF-safe (no procedural nodes).

A palette is {NAME: (rgb, metallic, roughness)} or {NAME: dict(rgb=..., metallic=..., roughness=...,
alpha=..., emission=(r,g,b), emission_strength=...)}. Keep <= 8 per vehicle, <= 4 per prop.
"""
import bpy

# Ready-made presets; copy into a project palette under project-specific names.
PRESETS = {
    "paint_gloss":   ((0.72, 0.04, 0.03), 0.6, 0.25),
    "paint_satin":   ((0.045, 0.045, 0.05), 0.0, 0.45),
    "metal_dark":    ((0.06, 0.06, 0.065), 0.9, 0.45),
    "metal_raw":     ((0.62, 0.63, 0.65), 1.0, 0.30),
    "chrome":        ((0.8, 0.8, 0.8), 1.0, 0.08),
    "aluminium":     ((0.7, 0.72, 0.75), 1.0, 0.35),
    "rubber":        ((0.045, 0.045, 0.045), 0.0, 0.90),
    "plastic_black": ((0.05, 0.05, 0.055), 0.0, 0.50),
    "exhaust_steel": ((0.55, 0.52, 0.48), 1.0, 0.35),
    "glass":         dict(rgb=(0.85, 0.87, 0.9), metallic=0.0, roughness=0.05, alpha=0.35),
    "leather":       ((0.06, 0.045, 0.04), 0.0, 0.55),
    "fabric":        ((0.25, 0.25, 0.27), 0.0, 0.85),
    "wood":          ((0.35, 0.22, 0.12), 0.0, 0.65),
    "concrete":      ((0.45, 0.45, 0.44), 0.0, 0.85),
    "brick":         ((0.45, 0.2, 0.14), 0.0, 0.9),
    "plaster":       ((0.78, 0.76, 0.72), 0.0, 0.8),
    "skin":          ((0.62, 0.45, 0.36), 0.0, 0.5),
    "hair_dark":     ((0.05, 0.035, 0.025), 0.0, 0.45),
    "emissive_warm": dict(rgb=(1.0, 0.85, 0.6), metallic=0.0, roughness=0.3,
                          emission=(1.0, 0.85, 0.6), emission_strength=5.0),
    "clay":          ((0.62, 0.62, 0.62), 0.0, 0.6),
}


def _norm(spec):
    if isinstance(spec, dict):
        return spec
    rgb, met, rough = spec
    return dict(rgb=rgb, metallic=met, roughness=rough)


def ensure(palette):
    """Create/update every material of the palette. Returns {name: Material}."""
    out = {}
    for name, spec in palette.items():
        s = _norm(PRESETS[spec] if isinstance(spec, str) else spec)
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True                       # deprecated in 5.x (warning only), still needed
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*s["rgb"], 1.0)
        b.inputs["Metallic"].default_value = s.get("metallic", 0.0)
        b.inputs["Roughness"].default_value = s.get("roughness", 0.5)
        if "alpha" in s:
            b.inputs["Alpha"].default_value = s["alpha"]
        if "emission" in s:
            b.inputs["Emission Color"].default_value = (*s["emission"], 1.0)
            b.inputs["Emission Strength"].default_value = s.get("emission_strength", 3.0)
        m.diffuse_color = (*s["rgb"], s.get("alpha", 1.0))   # Workbench MATERIAL colour
        m.metallic = s.get("metallic", 0.0)
        m.roughness = s.get("roughness", 0.5)
        out[name] = m
    return out


def assign_by_face(ob, mat_names, face_to_index):
    """Multi-material mesh: append materials and set per-face index via callback(poly)->int."""
    for n in mat_names:
        if n not in [m.name for m in ob.data.materials if m]:
            ob.data.materials.append(bpy.data.materials[n])
    for p in ob.data.polygons:
        p.material_index = face_to_index(p)
