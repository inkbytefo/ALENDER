"""
Paint of VEH_Sonnet_Bike: master-material instances (workbench.bl.master) on the S3 DETAIL model.

Claude Sonnet signature aesthetic:
  - Deep metallic terracotta / copper pearlescent bodywork (tank, cowl, chin spoiler)
  - Forged carbon fiber aero components (fenders, huggers, bellypan chin, muffler)
  - Anodized copper / gold inverted suspension stanchions
  - Satin black chassis, engine alloy, brushed billet aluminum controls
  - Amber / terracotta glowing LED DRL halo ring and taillight lightblade
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TT92_SETS = os.path.normpath(os.path.join(HERE, "..", "VEH_TT92_Racing_Car", "material"))
os.environ["WB_PBR_LIBRARY"] = os.pathsep.join(
    [TT92_SETS] + [p for p in os.environ.get("WB_PBR_LIBRARY", "").split(os.pathsep) if p and p != TT92_SETS])

from workbench import stages          # noqa: E402
from workbench.bl import master       # noqa: E402

PREFIX = "Sonnet"

INSTANCES = {
    # bodywork: Sonnet signature metallic terracotta/copper paint + gloss clear coat
    "MAT_PAINT_SONNET": dict(set="TT92_Chrome", tile=0.30, p={
        "Tint": (0.78, 0.26, 0.08, 1.0), "Metallic Scale": 0.80, "Metallic Bias": 0.35, "Coat Weight": 1.0,
        "Coat Roughness": 0.025, "Roughness Scale": 1.4, "Roughness Bias": 0.10, "Bump Strength": 0.02,
        "Bump Distance": 0.0001, "Normal Map Strength": 0.05, "Macro Variation": 0.02, "Dirt Amount": 0.0,
        "AO Strength": 0.2}),
    "MAT_PAINT_BLACK": dict(set="TT92_Chrome", tile=0.30, p={
        "Tint": (0.012, 0.012, 0.014, 1.0), "Metallic Scale": 0.0, "Metallic Bias": 0.10, "Coat Weight": 1.0,
        "Coat Roughness": 0.05, "Roughness Scale": 1.6, "Roughness Bias": 0.14, "Bump Strength": 0.02,
        "Bump Distance": 0.0001, "Normal Map Strength": 0.05, "Macro Variation": 0.02, "Dirt Amount": 0.02,
        "AO Strength": 0.2}),
    # frame, swingarm, rims, clamps, housings: satin black powder coat with worn edges
    "MAT_BLACK_COATED": dict(set="TT92_BlackCoated", tile=0.25, p={
        "Bump Strength": 0.35, "Bump Distance": 0.0004, "Normal Map Strength": 0.4, "Dirt Amount": 0.10,
        "Edge Wear": 0.12, "Value": 0.20, "Wear Color": (0.22, 0.22, 0.23, 1.0)}),
    # engine: anthracite cast alloy, oily dirt in the cavities
    "MAT_ENGINE_CAST": dict(set="TT92_AluminiumCast", tile=0.20, p={
        "Value": 0.13, "Bump Strength": 0.5, "Bump Distance": 0.0007, "Normal Map Strength": 0.6,
        "Dirt Amount": 0.18, "Dirt Color": (0.03, 0.028, 0.025, 1.0), "Edge Wear": 0.18,
        "Wear Color": (0.30, 0.30, 0.31, 1.0), "Macro Variation": 0.08, "Metallic Scale": 0.85}),
    # billet / machined aluminium: carbs, levers, sprockets, pegs, caps
    "MAT_ALUMINIUM": dict(set="TT92_AluminiumCast", tile=0.20, p={
        "Roughness Bias": -0.18, "Bump Strength": 0.15, "Bump Distance": 0.0003, "Normal Map Strength": 0.2,
        "Dirt Amount": 0.12}),
    "MAT_CHROME": dict(set="TT92_Chrome", tile=0.20, p={
        "Bump Strength": 0.04, "Bump Distance": 0.0001, "Normal Map Strength": 0.1, "Macro Variation": 0.0,
        "Dirt Amount": 0.04, "AO Strength": 0.2}),
    # raw stainless headers and collector with heat tint
    "MAT_STAINLESS_HEAT": dict(set="TT92_StainlessHeat", tile=0.30, p={
        "Bump Strength": 0.06, "Bump Distance": 0.0002, "Normal Map Strength": 0.15, "Macro Variation": 0.04,
        "Anisotropic": 0.25}),
    "MAT_STEEL_BRUSHED": dict(set="TT92_SteelBrushed", tile=0.10, p={
        "Anisotropic": 0.5, "Bump Strength": 0.1, "Bump Distance": 0.0002, "Normal Map Strength": 0.5,
        "Macro Variation": 0.0}),
    "MAT_CARBON": dict(set="TT92_CarbonForged", tile=0.12, p={
        "Coat Weight": 1.0, "Coat Roughness": 0.07, "Bump Strength": 0.1, "Bump Distance": 0.0002,
        "Normal Map Strength": 0.2}),
    "MAT_TYRE_RUBBER": dict(set="TT92_TyreRubber", tile=0.30, p={
        "Bump Strength": 0.45, "Bump Distance": 0.0006, "Normal Map Strength": 0.5, "Dirt Amount": 0.06,
        "Value": 0.20, "Dirt Color": (0.06, 0.055, 0.05, 1.0), "Macro Variation": 0.03}),
    "MAT_LEATHER_SEAT": dict(set="Leather009", tile=0.35, p={
        "Bump Strength": 0.45, "Bump Distance": 0.0006, "Normal Map Strength": 0.8, "Sheen Weight": 0.15,
        "Dirt Amount": 0.06}),
    # tail light & DRL halo: vibrant glowing neon
    "MAT_TAILLIGHT": dict(set="TT92_LensAmber", tile=0.20, p={
        "Tint": (1.0, 0.35, 0.05, 1.0), "Value": 4.0, "Coat Weight": 1.0, "Coat Roughness": 0.03,
        "Bump Strength": 0.02, "Normal Map Strength": 0.05, "Macro Variation": 0.0,
        "Emission": (1.0, 0.35, 0.05, 1.0), "Emission Strength": 4.0}),
}

BY_OLD = {
    "MAT_BODY_RED": "MAT_PAINT_SONNET", "MAT_BODY_BLACK": "MAT_PAINT_BLACK", "MAT_SEAT": "MAT_LEATHER_SEAT",
    "MAT_METAL_DARK": "MAT_BLACK_COATED", "MAT_METAL_RAW": "MAT_ALUMINIUM", "MAT_ENGINE": "MAT_ENGINE_CAST",
    "MAT_RUBBER": "MAT_TYRE_RUBBER", "MAT_GLASS": None,
}
OVERRIDES = [
    (r"EXHAUST_(Header|Collector|Muffler_Inlet|Muffler_EndCap|Clamp|PieWeld)", "MAT_STAINLESS_HEAT"),
    (r"EXHAUST_Muffler$|BODY_FrontFender$|FRAME_RearHugger$|FRAME_ChainGuard$|BODY_BellyPan_Chin$|BODY_BellyPan_Winglet|WHEEL_Rear_AeroDisc", "MAT_CARBON"),
    (r"EXHAUST_Spring|SUSP_Fork_Inner|SUSP_Shock_Rear_Body|CTRL_BarEnd|CTRL_Headlight_Projector|SUSP_\w+_Axle|CTRL_SteeringDamper_Rod",
     "MAT_CHROME"),
    (r"BRAKE_\w*Disc(_[LR])?(_Bobbin_\d+)?$|FASTENER_|DRIVE_Chain|ENGINE_OilCooler_Mesh|EXHAUST_Muffler_Mesh", "MAT_STEEL_BRUSHED"),
    (r"BODY_TailLight|CTRL_Headlight_DRL|BODY_TailTidy_Signal", "MAT_TAILLIGHT"),
    (r"CTRL_(Headlight_Housing|SwitchHousing|TFT_Dashboard|Headlight_Flyscreen)|ENGINE_SparkPlug|BODY_TailTidy_|BODY_Tail_Tunnel", "MAT_BLACK_COATED"),
    (r"BODY_FrontFender_Strut|ENGINE_OilCooler_Bracket|CTRL_BarEnd_Mirror_Stem|CTRL_BarEnd_Mirror_Head", "MAT_ALUMINIUM"),
    (r"CTRL_BarEnd_Mirror_Glass", "MAT_CHROME"),
    (r"SUSP_Fork_Outer|SUSP_Shock_Rear_Spring|SUSP_Shock_Rear_Reservoir|CTRL_SteeringDamper_Body|WHEEL_Rear_AeroCap", "MAT_PAINT_SONNET"),
]


def resolve(ob, slot, old):
    base = stages.base_name(ob.name).replace("UNCERTAIN_", "")
    for pat, mat in OVERRIDES:
        if re.match(pat, base):
            return mat
    if old not in BY_OLD:
        raise SystemExit(f"[PAINT] {ob.name} slot {slot}: no rule for material {old}")
    return BY_OLD[old]


def apply(objs):
    master.setup(PREFIX)
    return master.apply(objs, INSTANCES, resolve)
