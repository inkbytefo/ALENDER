"""
Paint system for VEH_TT92_Racing_Car: ONE master material, 14 instances.

    MM_TT92_Master       node group = the shader logic, written once
    MF_TT92_Projection   node group = tri-planar coordinates in metres (no UV unwrap needed)
    MAT_*                material instances: master group + a texture set + a few numbers (INSTANCES)

Why a master material: every surface of the car gets the same, tested feature set and the look is
tuned with a handful of exposed parameters per instance instead of 14 hand-built node trees.

Master features (all exposed as group inputs, see MASTER_INPUTS):
  * base colour: tint / saturation / value, baked AO multiply
  * macro variation: large object-space noise modulates value and roughness, hides the tiling
  * dirt: noise + cavity (AO) mask blends a dirt colour in and roughens it
  * edge wear (Cycles: Geometry > Pointiness): bare metal on convex edges
  * roughness scale / bias, metallic scale / bias
  * relief: NormalGL texture (Non-Color) -> Normal Map node -> Bump (height map) -> Principled Normal
  * clear coat over the textured base (car paint, lacquered wood, carbon, lens), sheen (cloth,
    leather), anisotropy (brushed metal), emission (afterburner liner)
Projection: textures are sampled with BOX (tri-planar) projection in OBJECT space, scaled so one
repeat = `tile` metres. That needs no UVs and has no seams on the curved shell. The tangent-space
normal map is sampled through the same projection: its tangent frame comes from the mesh UVs
(box UVs of the builders), which matches the projection planes; the height-driven Bump on top is
projection independent. Per instance: "Normal Map Strength" and "Bump Strength".
Limit: this node setup is for Blender renders (Cycles / EEVEE). The glTF exporter cannot read
custom node groups; the GLB of stage 4 keeps the plain modelling materials.

Textures: material/TT92_<Set>_1K-PNG (made by texgen.py) + the shared library (docs/11).
"""
import os
import re
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIAL_DIR = os.path.join(HERE, "material")
os.environ["WB_PBR_LIBRARY"] = os.pathsep.join(
    [MATERIAL_DIR] + [p for p in os.environ.get("WB_PBR_LIBRARY", "").split(os.pathsep) if p and p != MATERIAL_DIR])

from workbench import pbrlib          # noqa: E402  (after the library path is set)
from workbench.bl import pbr          # noqa: E402

MASTER = "MM_TT92_Master"
PROJECTION = "MF_TT92_Projection"

# name, socket type, default, (min, max)
MASTER_INPUTS = [
    ("Color", "NodeSocketColor", (0.5, 0.5, 0.5, 1.0), None),
    ("Roughness", "NodeSocketFloat", 0.5, (0, 1)),
    ("Metallic", "NodeSocketFloat", 0.0, (0, 1)),
    ("AO", "NodeSocketFloat", 1.0, (0, 1)),
    ("Height", "NodeSocketFloat", 0.5, (0, 1)),
    ("Normal Map", "NodeSocketColor", (0.5, 0.5, 1.0, 1.0), None),
    ("Emission", "NodeSocketColor", (0.0, 0.0, 0.0, 1.0), None),
    ("Tint", "NodeSocketColor", (1.0, 1.0, 1.0, 1.0), None),
    ("Saturation", "NodeSocketFloat", 1.0, (0, 2)),
    ("Value", "NodeSocketFloat", 1.0, (0, 2)),
    ("AO Strength", "NodeSocketFloat", 0.6, (0, 1)),
    ("Roughness Scale", "NodeSocketFloat", 1.0, (0, 2)),
    ("Roughness Bias", "NodeSocketFloat", 0.0, (-1, 1)),
    ("Metallic Scale", "NodeSocketFloat", 1.0, (0, 1)),
    ("Metallic Bias", "NodeSocketFloat", 0.0, (0, 1)),
    ("Bump Strength", "NodeSocketFloat", 0.3, (0, 1)),
    ("Bump Distance", "NodeSocketFloat", 0.0005, (0, 0.01)),
    ("Normal Map Strength", "NodeSocketFloat", 0.35, (0, 2)),
    ("Macro Variation", "NodeSocketFloat", 0.05, (0, 0.5)),
    ("Macro Scale", "NodeSocketFloat", 2.5, (0.1, 20)),
    ("Dirt Amount", "NodeSocketFloat", 0.0, (0, 1)),
    ("Dirt Color", "NodeSocketColor", (0.09, 0.075, 0.06, 1.0), None),
    ("Edge Wear", "NodeSocketFloat", 0.0, (0, 1)),
    ("Wear Color", "NodeSocketColor", (0.55, 0.55, 0.57, 1.0), None),
    ("Coat Weight", "NodeSocketFloat", 0.0, (0, 1)),
    ("Coat Roughness", "NodeSocketFloat", 0.08, (0, 1)),
    ("Sheen Weight", "NodeSocketFloat", 0.0, (0, 1)),
    ("Anisotropic", "NodeSocketFloat", 0.0, (0, 1)),
    ("Emission Strength", "NodeSocketFloat", 0.0, (0, 100)),
]

# material instance: texture set, tile (metres per repeat), master parameters that differ from the defaults
INSTANCES = {
    "MAT_PAINT_RED": dict(set="TT92_PaintRed", tile=0.50, p={
        "Coat Weight": 1.0, "Coat Roughness": 0.05, "Metallic Bias": 0.25, "Bump Strength": 0.05,
        "Bump Distance": 0.0002, "Macro Variation": 0.06, "Dirt Amount": 0.10,
        "Saturation": 1.08, "Value": 0.92, "Normal Map Strength": 0.12}),
    "MAT_PAINT_CREAM": dict(set="TT92_PaintCream", tile=0.25, p={
        "Coat Weight": 0.7, "Coat Roughness": 0.12, "Bump Strength": 0.2, "Bump Distance": 0.0003,
        "Dirt Amount": 0.08, "Normal Map Strength": 0.2}),
    "MAT_CHROME": dict(set="TT92_Chrome", tile=0.20, p={
        "Bump Strength": 0.04, "Bump Distance": 0.0001, "Macro Variation": 0.0, "Dirt Amount": 0.04,
        "AO Strength": 0.2, "Normal Map Strength": 0.1}),
    "MAT_ALUMINIUM_CAST": dict(set="TT92_AluminiumCast", tile=0.25, p={
        "Bump Strength": 0.55, "Bump Distance": 0.0008, "Dirt Amount": 0.30, "Macro Variation": 0.08, "Normal Map Strength": 0.6}),
    "MAT_BLACK_COATED": dict(set="TT92_BlackCoated", tile=0.25, p={
        "Bump Strength": 0.4, "Bump Distance": 0.0004, "Dirt Amount": 0.10, "Edge Wear": 0.25, "Normal Map Strength": 0.4}),
    "MAT_STAINLESS_HEAT": dict(set="TT92_StainlessHeat", tile=0.30, p={
        "Bump Strength": 0.06, "Bump Distance": 0.0002, "Macro Variation": 0.04, "Anisotropic": 0.25, "Normal Map Strength": 0.15}),
    "MAT_EXHAUST_WRAP": dict(set="TT92_ExhaustWrap", tile=0.10, p={
        "Bump Strength": 0.85, "Bump Distance": 0.0015, "Sheen Weight": 0.3, "AO Strength": 0.9,
        "Dirt Amount": 0.15, "Normal Map Strength": 1.0}),
    "MAT_TYRE_RUBBER": dict(set="TT92_TyreRubber", tile=0.30, p={
        "Bump Strength": 0.45, "Bump Distance": 0.0006, "Dirt Amount": 0.06, "Value": 0.32,
        "Dirt Color": (0.10, 0.09, 0.08, 1.0), "Macro Variation": 0.03, "Normal Map Strength": 0.5}),
    "MAT_LEATHER_SEAT": dict(set="Leather037", tile=0.35, p={
        "Bump Strength": 0.45, "Bump Distance": 0.0006, "Sheen Weight": 0.15, "Dirt Amount": 0.10,
        "Roughness Bias": 0.05, "Normal Map Strength": 0.8}),
    "MAT_WOOD_WHEEL": dict(set="TT92_WoodMahogany", tile=0.30, p={
        "Coat Weight": 0.9, "Coat Roughness": 0.10, "Bump Strength": 0.1, "Bump Distance": 0.0002, "Normal Map Strength": 0.2}),
    "MAT_SMOKED_LENS": dict(set="TT92_LensAmber", tile=0.20, p={
        "Coat Weight": 1.0, "Coat Roughness": 0.03, "Bump Strength": 0.02, "Macro Variation": 0.0, "Normal Map Strength": 0.05}),
    "MAT_CARBON": dict(set="TT92_CarbonForged", tile=0.12, p={
        "Coat Weight": 1.0, "Coat Roughness": 0.07, "Bump Strength": 0.1, "Bump Distance": 0.0002, "Normal Map Strength": 0.2}),
    "MAT_AB_GLOW": dict(set="TT92_AfterburnerPlasma", tile=0.30, p={
        "Emission Strength": 6.0, "Macro Variation": 0.0, "Bump Strength": 0.0, "Normal Map Strength": 0.0}),
    "MAT_STEEL_BRUSHED": dict(set="TT92_SteelBrushed", tile=0.10, p={
        "Anisotropic": 0.6, "Bump Strength": 0.12, "Bump Distance": 0.0002, "Macro Variation": 0.0, "Normal Map Strength": 0.6}),
}

# object name (regex, first match wins) -> material instance. BODY_Shell is handled separately (2 slots).
ASSIGN = [
    (r"BODY_Stripes", "MAT_PAINT_CREAM"),
    (r"BODY_Eye_", "MAT_SMOKED_LENS"),
    (r"BODY_(EyeTrim|EyeLamp|MirrorStalk|MirrorGlass|FillerCap)", "MAT_CHROME"),
    (r"NOSE_", "MAT_CHROME"),
    (r"AERO_ChinSpoiler", "MAT_CARBON"),
    (r"BODY_PanelLines", "MAT_BLACK_COATED"),
    (r"BODY_|ENGINE_AirFilter|COCKPIT_RimLip", "MAT_PAINT_RED"),
    (r"WHEEL_\w+_Tire_", "MAT_TYRE_RUBBER"),
    (r"WHEEL_\w+_(Hub|Spinner)_", "MAT_CHROME"),
    (r"WHEEL_|BRAKE_", "MAT_BLACK_COATED"),
    (r"(UNCERTAIN_)?SUSP_\w*(Damper_|HubCarrier)", "MAT_BLACK_COATED"),
    (r"SUSP_Rear_Spring", "MAT_PAINT_RED"),
    (r"(UNCERTAIN_)?SUSP_", "MAT_CHROME"),
    (r"ENG_(OilPan|Crankcase|TimingCover|Bellhousing|Bank|Intake)", "MAT_ALUMINIUM_CAST"),
    (r"ENG_\w*Pulley", "MAT_BLACK_COATED"),
    (r"ENG_Belt", "MAT_TYRE_RUBBER"),
    (r"ENG_Port", "MAT_STAINLESS_HEAT"),
    (r"ENG_", "MAT_CHROME"),
    (r"EXHAUST_Wrap", "MAT_EXHAUST_WRAP"),
    (r"EXHAUST_AB_Can", "MAT_CHROME"),
    (r"EXHAUST_AB_PetalsOuter", "MAT_CARBON"),
    (r"EXHAUST_AB_PetalsInner", "MAT_STAINLESS_HEAT"),
    (r"EXHAUST_AB_Glow", "MAT_AB_GLOW"),
    (r"EXHAUST_AB_", "MAT_BLACK_COATED"),
    (r"EXHAUST_", "MAT_STAINLESS_HEAT"),
    (r"COCKPIT_(Seat|CowlPad)", "MAT_LEATHER_SEAT"),
    (r"COCKPIT_SteeringWheel", "MAT_WOOD_WHEEL"),
    (r"COCKPIT_SteeringSpokes", "MAT_CHROME"),
    (r"COCKPIT_", "MAT_BLACK_COATED"),
    (r"FASTENER_", "MAT_STEEL_BRUSHED"),
]
SHELL_SLOTS = ("MAT_PAINT_RED", "MAT_BLACK_COATED")         # BODY_Shell: skin, cut interiors


# ============================================================================ node helpers
def _sock(sockets, ident):
    return next(s for s in sockets if s.identifier == ident)


class _B:
    """tiny node-tree builder: values may be sockets or constants."""

    def __init__(self, nt):
        self.nt, self.x = nt, -1600

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        self.x += 40
        n.location = (self.x, -40 * (len(self.nt.nodes) % 12))
        return n

    def put(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.nt.links.new(val, sock)
        else:
            sock.default_value = val

    def math(self, op, a, b=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.put(n.inputs[0], a)
        if b is not None:
            self.put(n.inputs[1], b)
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.put(_sock(n.inputs, "Factor_Float"), fac)
        self.put(_sock(n.inputs, "A_Color"), a)
        self.put(_sock(n.inputs, "B_Color"), b)
        return _sock(n.outputs, "Result_Color")

    def lerp(self, fac, a, b):
        n = self.node("ShaderNodeMix", data_type="FLOAT")
        self.put(_sock(n.inputs, "Factor_Float"), fac)
        self.put(_sock(n.inputs, "A_Float"), a)
        self.put(_sock(n.inputs, "B_Float"), b)
        return _sock(n.outputs, "Result_Float")

    def ramp(self, value, lo, hi):
        """smooth 0..1 mask between lo and hi."""
        n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        self.put(n.inputs["Value"], value)
        n.inputs["From Min"].default_value = lo
        n.inputs["From Max"].default_value = hi
        return n.outputs["Result"]

    def noise(self, vector, scale, detail=4.0):
        n = self.node("ShaderNodeTexNoise", noise_dimensions="3D")
        self.nt.links.new(vector, n.inputs["Vector"])
        self.put(n.inputs["Scale"], scale)
        n.inputs["Detail"].default_value = detail
        return n.outputs["Fac"], n.outputs["Color"]


def _group(name, inputs, outputs):
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    nt = bpy.data.node_groups.new(name, "ShaderNodeTree")
    for nm, typ, default, rng in inputs:
        s = nt.interface.new_socket(name=nm, in_out="INPUT", socket_type=typ)
        if default is not None:
            s.default_value = default
        if rng and typ == "NodeSocketFloat":
            s.min_value, s.max_value = rng
    for nm, typ in outputs:
        nt.interface.new_socket(name=nm, in_out="OUTPUT", socket_type=typ)
    gi = nt.nodes.new("NodeGroupInput"); gi.location = (-1900, 0)
    go = nt.nodes.new("NodeGroupOutput"); go.location = (900, 0)
    return nt, gi, go


# ============================================================================ the two node groups
def build_projection():
    """Vector = object position / Tile (+ a slow noise offset that breaks up the repetition)."""
    nt, gi, go = _group(PROJECTION, [("Tile", "NodeSocketFloat", 0.25, (0.001, 10)),
                                     ("Distortion", "NodeSocketFloat", 0.02, (0, 1))],
                        [("Vector", "NodeSocketVector")])
    b = _B(nt)
    tc = b.node("ShaderNodeTexCoord")
    _, ncol = b.noise(tc.outputs["Object"], 1.3, detail=2.0)
    off = b.node("ShaderNodeVectorMath", operation="SUBTRACT")
    nt.links.new(ncol, off.inputs[0]); off.inputs[1].default_value = (0.5, 0.5, 0.5)
    sc = b.node("ShaderNodeVectorMath", operation="SCALE")
    nt.links.new(off.outputs[0], sc.inputs[0]); nt.links.new(gi.outputs["Distortion"], sc.inputs["Scale"])
    add = b.node("ShaderNodeVectorMath", operation="ADD")
    nt.links.new(tc.outputs["Object"], add.inputs[0]); nt.links.new(sc.outputs[0], add.inputs[1])
    inv = b.math("DIVIDE", 1.0, gi.outputs["Tile"])
    out = b.node("ShaderNodeVectorMath", operation="SCALE")
    nt.links.new(add.outputs[0], out.inputs[0]); nt.links.new(inv, out.inputs["Scale"])
    nt.links.new(out.outputs[0], go.inputs["Vector"])
    return nt


def build_master():
    nt, gi, go = _group(MASTER, MASTER_INPUTS, [("BSDF", "NodeSocketShader")])
    b = _B(nt)
    I = gi.outputs
    tc = b.node("ShaderNodeTexCoord")
    geo = b.node("ShaderNodeNewGeometry")

    # ---- masks
    macro, _ = b.noise(tc.outputs["Object"], I["Macro Scale"], detail=3.0)            # 0..1, large blotches
    macro_s = b.math("MULTIPLY", b.math("SUBTRACT", macro, 0.5), 2.0)                 # -1..1
    dnoise, _ = b.noise(tc.outputs["Object"], 9.0, detail=6.0)
    cavity = b.math("SUBTRACT", 1.0, I["AO"])                                         # 1 in pits
    dirt = b.math("MULTIPLY", I["Dirt Amount"],
                  b.math("ADD", b.ramp(dnoise, 0.42, 0.72), b.math("MULTIPLY", cavity, 2.0), clamp=True),
                  clamp=True)
    edge = b.math("MULTIPLY", I["Edge Wear"],
                  b.math("MULTIPLY", b.ramp(geo.outputs["Pointiness"], 0.62, 0.78),
                         b.ramp(dnoise, 0.30, 0.65)), clamp=True)

    # ---- base colour
    hsv = b.node("ShaderNodeHueSaturation")
    nt.links.new(I["Color"], hsv.inputs["Color"])
    nt.links.new(I["Saturation"], hsv.inputs["Saturation"])
    nt.links.new(b.math("MULTIPLY", I["Value"],
                        b.math("ADD", 1.0, b.math("MULTIPLY", macro_s, I["Macro Variation"]))),
                 hsv.inputs["Value"])
    col = b.mix(1.0, hsv.outputs["Color"], I["Tint"], "MULTIPLY")
    ao_col = b.node("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(I["AO"], ao_col.inputs[k])
    col = b.mix(I["AO Strength"], col, ao_col.outputs["Color"], "MULTIPLY")
    col = b.mix(dirt, col, I["Dirt Color"])
    col = b.mix(edge, col, I["Wear Color"])

    # ---- roughness / metallic
    rough = b.math("ADD", b.math("MULTIPLY", I["Roughness"], I["Roughness Scale"]), I["Roughness Bias"])
    rough = b.math("ADD", rough, b.math("MULTIPLY", macro_s, b.math("MULTIPLY", I["Macro Variation"], 0.6)))
    rough = b.lerp(dirt, rough, 0.85)
    rough = b.lerp(edge, rough, 0.30)
    rough = b.math("MAXIMUM", b.math("MINIMUM", rough, 1.0), 0.02)
    metal = b.math("ADD", b.math("MULTIPLY", I["Metallic"], I["Metallic Scale"]), I["Metallic Bias"], clamp=True)
    metal = b.lerp(dirt, metal, 0.0)
    metal = b.lerp(edge, metal, 1.0)

    # ---- relief: optional tangent normal map, then bump from the height map
    nmap = b.node("ShaderNodeNormalMap")
    nt.links.new(I["Normal Map"], nmap.inputs["Color"])
    nt.links.new(I["Normal Map Strength"], nmap.inputs["Strength"])
    bump = b.node("ShaderNodeBump")
    nt.links.new(I["Height"], bump.inputs["Height"])
    nt.links.new(I["Bump Strength"], bump.inputs["Strength"])
    nt.links.new(I["Bump Distance"], bump.inputs["Distance"])
    nt.links.new(nmap.outputs["Normal"], bump.inputs["Normal"])

    # ---- shader
    bsdf = b.node("ShaderNodeBsdfPrincipled")
    bsdf.location = (500, 0)
    L = nt.links.new
    L(col, bsdf.inputs["Base Color"])
    L(rough, bsdf.inputs["Roughness"])
    L(metal, bsdf.inputs["Metallic"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    L(I["Coat Weight"], bsdf.inputs["Coat Weight"])
    L(I["Coat Roughness"], bsdf.inputs["Coat Roughness"])        # coat normal stays the smooth surface
    L(I["Sheen Weight"], bsdf.inputs["Sheen Weight"])
    L(I["Anisotropic"], bsdf.inputs["Anisotropic"])
    L(I["Emission"], bsdf.inputs["Emission Color"])
    L(I["Emission Strength"], bsdf.inputs["Emission Strength"])
    L(bsdf.outputs["BSDF"], go.inputs["BSDF"])
    return nt


# ============================================================================ instances
MAPS = [  # pbrlib kind, master input, colour data?, image-node output used
    ("base_color", "Color", True), ("roughness", "Roughness", False), ("metallic", "Metallic", False),
    ("ao", "AO", False), ("displacement", "Height", False), ("emission", "Emission", True),
    ("normal_gl", "Normal Map", False),      # Non-Color image -> Normal Map node (Color) inside the master
]


def make_instance(name, spec):
    try:
        ts = pbrlib.find(spec["set"])
    except KeyError as e:
        raise SystemExit(f"[PAINT] texture set '{spec['set']}' missing: {e}\n"
                         f"        run: python wb.py run projects/VEH_TT92_Racing_Car/texgen.py")
    mp = ts["maps"]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = bpy.data.node_groups[MASTER]
    g.location = (350, 0); g.width = 260; g.label = "MASTER"
    nt.links.new(g.outputs["BSDF"], out.inputs["Surface"])
    pr = nt.nodes.new("ShaderNodeGroup"); pr.node_tree = bpy.data.node_groups[PROJECTION]
    pr.location = (-700, 0); pr.label = "PROJECTION"
    pr.inputs["Tile"].default_value = spec["tile"]
    y = 500
    for kind, inp, is_color in MAPS:
        if kind == "normal_gl" and kind not in mp and "normal" in mp:
            kind = "normal"                                   # unknown handedness -> treated as OpenGL
        if kind not in mp:
            continue
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(mp[kind], check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if is_color else "Non-Color"
        t.projection = "BOX"
        t.projection_blend = 0.25
        t.label = inp
        t.location = (-350, y)
        y -= 280
        nt.links.new(pr.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], g.inputs[inp])
    for k, v in spec.get("p", {}).items():
        g.inputs[k].default_value = v
    # solid-view colour / fallbacks
    if "base_color" in mp:
        mc = [pbr._srgb_to_linear(c) for c in pbr.mean_value(mp["base_color"])]
        m.diffuse_color = (*mc, 1.0)
    m.roughness = pbr.mean_value(mp["roughness"])[0] if "roughness" in mp else 0.5
    m.metallic = pbr.mean_value(mp["metallic"])[0] if "metallic" in mp else 0.0
    m["pbr_set"] = ts["name"]
    m["pbr_tile_m"] = spec["tile"]
    m["master"] = MASTER
    return m


def material_for(name):
    for pat, mat in ASSIGN:
        if re.match(pat, name):
            return mat
    return None


def apply(objs):
    """build the groups + instances and assign them to the mesh objects. Returns {material: n objects}."""
    build_projection()
    build_master()
    mats = {n: make_instance(n, s) for n, s in INSTANCES.items()}
    used, unmatched, done = {}, [], set()
    for ob in objs:
        if ob.type != "MESH":
            continue
        if ob.name == "BODY_Shell":
            for i, mn in enumerate(SHELL_SLOTS):
                ob.data.materials[i] = mats[mn]
                used[mn] = used.get(mn, 0) + 1
            continue
        mn = material_for(ob.name)
        if mn is None:
            unmatched.append(ob.name)
            continue
        used[mn] = used.get(mn, 0) + 1
        if ob.data.name in done:                              # instanced mesh (fasteners)
            continue
        done.add(ob.data.name)
        ob.data.materials.clear()
        ob.data.materials.append(mats[mn])
        for p in ob.data.polygons:
            p.material_index = 0
    if unmatched:
        raise SystemExit(f"[PAINT] objects without a material rule: {unmatched}")
    for m in list(bpy.data.materials):                        # the flat modelling materials are done
        if m.users == 0 and m.name not in mats:
            bpy.data.materials.remove(m)
    return used
