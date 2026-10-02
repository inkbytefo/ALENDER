"""
Paint for PROP_AK_Rifle: the four palette materials become instances of the workbench master material
(workbench.bl.master) with the AK texture sets made by texgen.py and the three wear masks.

    parts.after_build(3, objs) -> paint.apply(objs)       S3 DETAIL = painted hero mesh (Cycles / EEVEE)
    S4 bakes these instances into the game atlas through master.BakeRouter (pipeline.stage4).

Material slots stay the four of parts.PALETTE (prop limit), so no builder changes:
    MAT_STEEL_DARK     AK_SteelParkerized  phosphate finish = mostly diffuse dark grey (Metallic Scale 0.4,
                                           a mirror-black metal reads as a hole); bare steel on convex edges,
                                           in chips and scratches; grime in cavities
    MAT_STEEL_BRIGHT   AK_SteelBrushed     bolt carrier + charging handle, anisotropic
    MAT_WOOD_LAMINATE  AK_WoodLaminateA    lacquered laminate = clear coat over the wood; grain runs along
                                           the part (cylindrical projection); lacquer scratches, worn edges
    MAT_POLYMER        AK_PolymerStipple   pistol grip; edges polished smooth by handling
AK_WoodLaminateB and AK_EnamelBlack are in the library too (alternative stock / magazine looks).
The game export has ONE baked material; these instances are the bake source and the render look.
"""
import os

from workbench import pbrlib
from workbench.bl import master

PREFIX = "AK"
_MASKS = None


def _masks():
    d = os.path.join(os.path.dirname(pbrlib.find("AK_SteelParkerized")["dir"]), "AK_WearMasks_1K-PNG")
    return {"Scratch Mask": os.path.join(d, "AK_WearMasks_Scratches.png"),
            "Chip Mask": os.path.join(d, "AK_WearMasks_Chips.png"),
            "Grunge Mask": os.path.join(d, "AK_WearMasks_Grunge.png")}


def instances():
    m = _masks()
    bare_steel = (0.60, 0.60, 0.61, 1.0)
    return {
        "MAT_STEEL_DARK": dict(set="AK_SteelParkerized", tile=0.06, masks=m, mask_tile=0.07, p={
            "Value": 1.7, "Metallic Scale": 0.40, "Roughness Bias": 0.06, "AO Strength": 0.5, "Bump Strength": 0.22, "Bump Distance": 0.0002,
            "Normal Map Strength": 0.3, "Macro Variation": 0.10, "Macro Scale": 7.0,
            "Dirt Amount": 0.14, "Dirt Color": (0.035, 0.030, 0.025, 1.0),
            "Bevel Wear": 1.0, "Bevel Radius": 0.0020, "Chip Amount": 0.05, "Scratch Amount": 0.32,
            "Scratch Roughness": 0.34, "Wear Color": bare_steel, "Wear Roughness": 0.30, "Wear Metallic": 1.0}),
        "MAT_STEEL_BRIGHT": dict(set="AK_SteelBrushed", tile=0.05, masks=m, mask_tile=0.10, p={
            "Anisotropic": 0.5, "Bump Strength": 0.10, "Bump Distance": 0.0002, "Normal Map Strength": 0.4,
            "Macro Variation": 0.04, "Dirt Amount": 0.10, "Dirt Color": (0.05, 0.045, 0.04, 1.0),
            "Scratch Amount": 0.30, "Scratch Roughness": 0.45, "Wear Color": (0.75, 0.75, 0.76, 1.0)}),
        "MAT_WOOD_LAMINATE": dict(set="AK_WoodLaminateA", tile=0.24, projection="CYL_Y", radius=0.036,
                                  masks=m, mask_tile=0.16, p={
            "Tint": (1.0, 0.90, 0.74, 1.0), "Saturation": 0.95, "Value": 0.80, "AO Strength": 0.3, "Coat Weight": 0.85, "Coat Roughness": 0.14,
            "Bump Strength": 0.06, "Bump Distance": 0.0002, "Normal Map Strength": 0.08, "Macro Variation": 0.08,
            "Macro Scale": 5.0, "Dirt Amount": 0.16, "Dirt Color": (0.05, 0.03, 0.02, 1.0),
            "Bevel Wear": 0.30, "Bevel Radius": 0.004, "Chip Amount": 0.10, "Scratch Amount": 0.55,
            "Scratch Roughness": 0.55, "Wear Color": (0.52, 0.34, 0.17, 1.0), "Wear Roughness": 0.62,
            "Wear Metallic": 0.0}),
        "MAT_POLYMER": dict(set="AK_PolymerStipple", tile=0.06, masks=m, mask_tile=0.12, p={
            "Value": 0.95, "AO Strength": 0.8, "Bump Strength": 0.55, "Bump Distance": 0.0004, "Normal Map Strength": 0.8,
            "Macro Variation": 0.05, "Dirt Amount": 0.12, "Dirt Color": (0.06, 0.055, 0.05, 1.0),
            "Bevel Wear": 0.30, "Bevel Radius": 0.003, "Scratch Amount": 0.25, "Scratch Roughness": 0.40,
            "Wear Color": (0.035, 0.035, 0.037, 1.0), "Wear Roughness": 0.30, "Wear Metallic": 0.0}),
    }


def apply(objs):
    """Re-slot the palette materials of objs with the master instances (same names)."""
    master.setup(PREFIX)
    used = master.apply(objs, instances(), lambda ob, slot, old: None)
    bad = master.unwired_normal_maps(list(used))
    print("[PAINT] instances", used, "| unwired normal maps:", bad or "none")
    return used
