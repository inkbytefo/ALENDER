"""
Master material: ONE shader node group, many light-weight material instances (docs/11).

    from workbench.bl import master
    master.setup("TT92")                         # group names MM_TT92_Master / MF_TT92_Projection
    used = master.apply(objs, INSTANCES, resolve)   # resolve(ob, slot, old_material_name) -> instance | None
    router = master.BakeRouter()                 # bake material inputs through the group (game export)

INSTANCES = {"MAT_PAINT_RED": dict(set="TT92_PaintRed", tile=0.5, p={"Coat Weight": 1.0, ...}), ...}
  set = pbrlib texture set, tile = metres per texture repeat, p = master inputs that differ from the defaults.
  optional: projection="CYL_Y" (+ radius, offset): grain runs along the object's Y axis on every face;
            masks={"Scratch Mask" | "Chip Mask" | "Grunge Mask": png path}, mask_tile=metres per repeat.
Wear: Edge Wear (pointiness, per vertex), Bevel Wear (Bevel node, tessellation independent, Cycles only),
Chip Amount / Scratch Amount (mask driven), Dirt Amount (noise + cavity + Grunge Mask); the exposed
material is Wear Color / Wear Roughness / Wear Metallic.

Master features (group inputs, MASTER_INPUTS): tint / saturation / value, baked AO, macro variation,
dirt (noise + cavity), edge wear (Cycles pointiness), roughness and metallic scale / bias, normal map
(Non-Color image -> Normal Map node -> Bump from height -> Principled), clear coat, sheen, anisotropy,
emission. Projection: BOX (tri-planar) in OBJECT space, one repeat = `tile` metres - no UV unwrap needed.
Blender renders only: the glTF exporter cannot read node groups, bake first (BakeRouter).
Extracted from projects/VEH_TT92_Racing_Car/paint.py.
"""
import bpy

from workbench import pbrlib
from workbench.bl import pbr

MASTER = "MM_Master"
PROJECTION = "MF_Projection"


def setup(prefix):
    """name the two node groups after the asset."""
    global MASTER, PROJECTION
    MASTER, PROJECTION = f"MM_{prefix}_Master", f"MF_{prefix}_Projection"
    return MASTER, PROJECTION


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
    # --- wear from mask textures + geometry (all default 0 = off; see `masks` in the instance spec)
    ("Scratch Mask", "NodeSocketFloat", 0.0, (0, 1)),       # white = scratch
    ("Chip Mask", "NodeSocketFloat", 0.0, (0, 1)),          # white = finish chipped off
    ("Grunge Mask", "NodeSocketFloat", 0.0, (0, 1)),        # white = grime
    ("Scratch Amount", "NodeSocketFloat", 0.0, (0, 1)),     # light, shallow: lightens + changes roughness
    ("Scratch Roughness", "NodeSocketFloat", 0.55, (0, 1)), # roughness inside a scratch
    ("Chip Amount", "NodeSocketFloat", 0.0, (0, 1)),        # chips anywhere on the surface -> Wear Color
    ("Bevel Wear", "NodeSocketFloat", 0.0, (0, 1)),         # convex edges found with the Bevel node (Cycles)
    ("Bevel Radius", "NodeSocketFloat", 0.0015, (0, 0.02)),
    ("Wear Roughness", "NodeSocketFloat", 0.30, (0, 1)),    # roughness of the exposed material
    ("Wear Metallic", "NodeSocketFloat", 1.0, (0, 1)),      # 1 = bare metal under paint, 0 = bare wood / plastic
]


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


PROJECTION_CYL = "_Cyl"      # suffix of the cylindrical projection group


def build_projection_cyl():
    """Vector for long round parts (stocks, handguards): U runs along the object's Y axis, V around it
    (atan2(X, Z) * Radius, seam on the -Z side), both in units of Tile. Use with FLAT image projection:
    a grain texture then runs along the part on every face, which BOX projection cannot do."""
    nt, gi, go = _group(PROJECTION + PROJECTION_CYL, [("Tile", "NodeSocketFloat", 0.25, (0.001, 10)),
                                                      ("Radius", "NodeSocketFloat", 0.03, (0.001, 1)),
                                                      ("Offset", "NodeSocketFloat", 0.0, (-10, 10))],
                        [("Vector", "NodeSocketVector")])
    b = _B(nt)
    tc = b.node("ShaderNodeTexCoord")
    sep = b.node("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ang = b.math("ARCTAN2", sep.outputs["X"], sep.outputs["Z"])
    inv = b.math("DIVIDE", 1.0, gi.outputs["Tile"])
    u = b.math("ADD", b.math("MULTIPLY", sep.outputs["Y"], inv), gi.outputs["Offset"])
    v = b.math("MULTIPLY", b.math("MULTIPLY", ang, gi.outputs["Radius"]), inv)
    comb = b.node("ShaderNodeCombineXYZ")
    nt.links.new(u, comb.inputs["X"]); nt.links.new(v, comb.inputs["Y"])
    nt.links.new(comb.outputs[0], go.inputs["Vector"])
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
    dirt = b.math("ADD", dirt, b.math("MULTIPLY", I["Dirt Amount"], I["Grunge Mask"]), clamp=True)
    edge = b.math("MULTIPLY", I["Edge Wear"],
                  b.math("MULTIPLY", b.ramp(geo.outputs["Pointiness"], 0.62, 0.78),
                         b.ramp(dnoise, 0.30, 0.65)), clamp=True)
    # Bevel-node edge mask: independent of the tessellation (pointiness is per vertex and floods flat
    # n-gons whose corners are all convex). 1 - N.N_bevel > 0 near an edge; pointiness > 0.5 keeps the
    # convex ones only (creases between touching parts stay painted).
    bev = b.node("ShaderNodeBevel", samples=6)
    nt.links.new(I["Bevel Radius"], bev.inputs["Radius"])
    dot = b.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    nt.links.new(bev.outputs["Normal"], dot.inputs[0]); nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    near_edge = b.ramp(b.math("SUBTRACT", 1.0, dot.outputs["Value"]), 0.015, 0.12)
    convex = b.ramp(geo.outputs["Pointiness"], 0.50, 0.53)
    breakup = b.math("MAXIMUM", b.ramp(dnoise, 0.35, 0.70), I["Chip Mask"])
    bevel_wear = b.math("MULTIPLY", I["Bevel Wear"], b.math("MULTIPLY", b.math("MULTIPLY", near_edge, convex), breakup))
    chips = b.math("MULTIPLY", I["Chip Amount"], I["Chip Mask"])
    edge = b.math("MAXIMUM", edge, b.math("MAXIMUM", bevel_wear, chips), clamp=True)
    scratch = b.math("MULTIPLY", I["Scratch Amount"], I["Scratch Mask"], clamp=True)

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
    col = b.mix(b.math("MULTIPLY", scratch, 0.45), col, I["Wear Color"])
    col = b.mix(edge, col, I["Wear Color"])

    # ---- roughness / metallic
    rough = b.math("ADD", b.math("MULTIPLY", I["Roughness"], I["Roughness Scale"]), I["Roughness Bias"])
    rough = b.math("ADD", rough, b.math("MULTIPLY", macro_s, b.math("MULTIPLY", I["Macro Variation"], 0.6)))
    rough = b.lerp(dirt, rough, 0.85)
    rough = b.lerp(scratch, rough, I["Scratch Roughness"])
    rough = b.lerp(edge, rough, I["Wear Roughness"])
    rough = b.math("MAXIMUM", b.math("MINIMUM", rough, 1.0), 0.02)
    metal = b.math("ADD", b.math("MULTIPLY", I["Metallic"], I["Metallic Scale"]), I["Metallic Bias"], clamp=True)
    metal = b.lerp(dirt, metal, 0.0)
    metal = b.lerp(edge, metal, I["Wear Metallic"])

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
        raise SystemExit(f"[MASTER] texture set '{spec['set']}' missing: {e} "
                         f"(library roots: {pbrlib.library_roots()})")
    mp = ts["maps"]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = bpy.data.node_groups[MASTER]
    g.location = (350, 0); g.width = 260; g.label = "MASTER"
    nt.links.new(g.outputs["BSDF"], out.inputs["Surface"])
    cyl = spec.get("projection") == "CYL_Y"
    pr = nt.nodes.new("ShaderNodeGroup")
    pr.node_tree = bpy.data.node_groups[PROJECTION + (PROJECTION_CYL if cyl else "")]
    pr.location = (-700, 0); pr.label = "PROJECTION"
    pr.inputs["Tile"].default_value = spec["tile"]
    if cyl:
        pr.inputs["Radius"].default_value = spec.get("radius", 0.03)
        pr.inputs["Offset"].default_value = spec.get("offset", 0.0)
    y = 500
    for kind, inp, is_color in MAPS:
        if kind == "normal_gl" and kind not in mp and "normal" in mp:
            kind = "normal"                                   # unknown handedness -> treated as OpenGL
        if kind not in mp:
            continue
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(mp[kind], check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if is_color else "Non-Color"
        t.projection = "FLAT" if cyl else "BOX"
        t.projection_blend = 0.25
        t.label = inp
        t.location = (-350, y)
        y -= 280
        nt.links.new(pr.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], g.inputs[inp])
    # wear masks: {"Scratch Mask" | "Chip Mask" | "Grunge Mask": image path}, box-projected at mask_tile
    if spec.get("masks"):
        mp_ = nt.nodes.new("ShaderNodeGroup"); mp_.node_tree = bpy.data.node_groups[PROJECTION]
        mp_.location = (-700, -900); mp_.label = "MASK PROJECTION"
        mp_.inputs["Tile"].default_value = spec.get("mask_tile", 0.15)
        for inp, path in spec["masks"].items():
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(path, check_existing=True)
            t.image.colorspace_settings.name = "Non-Color"
            t.projection, t.projection_blend, t.label = "BOX", 0.25, inp
            t.location = (-350, y)
            y -= 280
            nt.links.new(mp_.outputs["Vector"], t.inputs["Vector"])
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


def build_groups():
    build_projection()
    build_projection_cyl()
    build_master()


def apply(objs, instances, resolve):
    """Build groups + instances and re-slot the mesh objects.
    resolve(ob, slot_index, old_material_name) -> instance name, or None to keep that slot.
    Returns {instance name: number of slots using it}."""
    build_groups()
    mats = {n: make_instance(n, s) for n, s in instances.items()}
    used, done = {}, set()
    for ob in objs:
        if ob.type != "MESH":
            continue
        fresh = ob.data.name not in done                      # instanced meshes: re-slot once
        done.add(ob.data.name)
        for i, slot in enumerate(ob.material_slots):
            old = slot.material.name if slot.material else None
            new = old if old in mats else resolve(ob, i, old)
            if new is None:
                continue
            used[new] = used.get(new, 0) + 1
            if fresh and old != new:
                ob.data.materials[i] = mats[new]
    return used


def unwired_normal_maps(names):
    """instances whose normal map is not a Non-Color image wired into the master."""
    bad = []
    for name in names:
        nt = bpy.data.materials[name].node_tree
        t = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.label == "Normal Map"), None)
        if not (t and t.image and t.image.colorspace_settings.name == "Non-Color" and t.outputs["Color"].links):
            bad.append(name)
    return bad


class BakeRouter:
    """Bake material INPUTS of every instance at once: the master group's output is switched to an
    Emission of the socket that feeds Base Color / Roughness / Metallic / Emission (bake type EMIT);
    route(None) restores the real BSDF (NORMAL / AO bakes). close() removes the helper nodes.
    A clear coat cannot be exported: `coat_to_roughness` of it is folded into the baked roughness.
    The emission colour is baked only where an instance has Emission Strength > 0."""

    def __init__(self, coat_to_roughness=0.75):
        g = self.g = bpy.data.node_groups[MASTER]
        self.out = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
        self.bsdf = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED")
        self.emit = g.nodes.new("ShaderNodeEmission")
        s = {k: self.bsdf.inputs[n].links[0].from_socket for k, n in
             (("base", "Base Color"), ("rough", "Roughness"), ("metal", "Metallic"), ("emission", "Emission Color"),
              ("coat", "Coat Weight"), ("coat_rough", "Coat Roughness"), ("estrength", "Emission Strength"))}
        k = g.nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = coat_to_roughness
        g.links.new(s["coat"], k.inputs[0])
        r = g.nodes.new("ShaderNodeMix")
        r.data_type = "FLOAT"
        g.links.new(k.outputs[0], _sock(r.inputs, "Factor_Float"))
        g.links.new(s["rough"], _sock(r.inputs, "A_Float"))
        g.links.new(s["coat_rough"], _sock(r.inputs, "B_Float"))
        s["rough"] = _sock(r.outputs, "Result_Float")
        on = g.nodes.new("ShaderNodeMath")
        on.operation = "GREATER_THAN"
        on.inputs[1].default_value = 0.0
        g.links.new(s["estrength"], on.inputs[0])
        em = g.nodes.new("ShaderNodeMix")
        em.data_type = "RGBA"
        em.blend_type = "MULTIPLY"
        _sock(em.inputs, "Factor_Float").default_value = 1.0
        g.links.new(s["emission"], _sock(em.inputs, "A_Color"))
        g.links.new(on.outputs[0], _sock(em.inputs, "B_Color"))
        s["emission"] = _sock(em.outputs, "Result_Color")
        self.src, self._tmp = s, [self.emit, k, r, on, em]

    def route(self, key):
        g = self.g
        for l in list(self.out.inputs[0].links):
            g.links.remove(l)
        if key is None:
            g.links.new(self.bsdf.outputs[0], self.out.inputs[0])
            return
        for l in list(self.emit.inputs["Color"].links):
            g.links.remove(l)
        g.links.new(self.src[key], self.emit.inputs["Color"])
        g.links.new(self.emit.outputs[0], self.out.inputs[0])

    def close(self):
        self.route(None)
        for n in self._tmp:
            self.g.nodes.remove(n)
