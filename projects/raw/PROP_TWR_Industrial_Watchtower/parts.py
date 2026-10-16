"""Procedural, modular steel watchtower builders in metric world coordinates."""
import math

from mathutils import Matrix

import landmarks as L
from workbench import stages
from workbench.stages import Part
from workbench.bl import mesh, mods

C = {
    "paint": "MAT_PAINTED_STEEL",
    "grate": "MAT_GALVANIZED_STEEL",
    "worn": "MAT_WORN_STEP_STEEL",
}

CATEGORY = "building"
TARGET_DIMS = (8.0, 15.1, 7.0)
GROUND = True
PROFILES = {
    1: stages.profile(1, ring=8, stations=4),
    2: stages.profile(2, ring=12, stations=8),
    3: stages.profile(3, ring=16, stations=12),
}
GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25), drop_small_m=0.02)
PALETTE = {
    C["paint"]: ((0.12, 0.18, 0.23), 0.0, 0.5),
    C["grate"]: ((0.16, 0.18, 0.19), 0.85, 0.68),
    C["worn"]: ((0.38, 0.4, 0.41), 1.0, 0.36),
}
UNCERTAIN = [
    "No reference image was supplied; only the 8 x 6 m platform and +6 m deck elevation are source dimensions.",
    "Straight south stair is assumed 1.25 m wide, 32 risers at 0.1875 m, 0.28 m treads, and 8.96 m run.",
    "Guardrail is modeled as 1.0 m high with 0.78 m sheet panels and a centered 1.5 m stair opening.",
    "Beam sections, column spacing, grating pitch, and all structural thicknesses are design assumptions.",
]
CRITICAL_PAIRS = []

def nm(P, name):
    return stages.nm(P, name)


def _box(P, name, center, size, material, bevel=0.002, rot=None):
    ob = mesh.box(nm(P, name), P["coll"], center, size, material, rot=rot)
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def _boxes(P, name, specs, material, bevel=0.0015):
    """Build disjoint box modules into one mesh, keeping each module editable in source."""
    vertices, faces = [], []
    face_template = (
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    )
    for center, size in specs:
        cx, cy, cz = center
        sx, sy, sz = (value * 0.5 for value in size)
        base = len(vertices)
        vertices.extend((
            (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
            (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
            (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
            (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
        ))
        faces.extend(tuple(base + i for i in face) for face in face_template)
    ob = mesh.from_pydata(nm(P, name), P["coll"], vertices, faces, material, smooth=False)
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def _column(P, key, x, y):
    out = []
    if P["stage"] == 1:
        out.append(_box(P, f"COL_{key}", (x, y, 3.0), (0.34, 0.34, 6.0), C["paint"], 0.0))
    else:
        out.extend((
            _box(P, f"COL_{key}_FlangeA", (x, y - 0.135, 3.0), (0.36, 0.07, 5.9), C["paint"]),
            _box(P, f"COL_{key}_FlangeB", (x, y + 0.135, 3.0), (0.36, 0.07, 5.9), C["paint"]),
            _box(P, f"COL_{key}_Web", (x, y, 3.0), (0.07, 0.20, 5.9), C["paint"]),
            _box(P, f"COL_{key}_Foot", (x, y, 0.06), (0.50, 0.50, 0.12), C["paint"]),
            _box(P, f"COL_{key}_Cap", (x, y, 5.90), (0.46, 0.46, 0.08), C["paint"]),
        ))
        if P["detail"]:
            bolts = []
            for dx in (-0.16, 0.16):
                for dy in (-0.16, 0.16):
                    bolts.append(((x + dx, y + dy, 0.12), (x + dx, y + dy, 0.145), 0.018))
            out.append(mesh.multi_cyl(nm(P, f"FASTENER_{key}_FootBolts"), P["coll"],
                                      bolts, segs=8, mat=C["worn"]))
    return out


_COLUMN_POSITIONS = (
    ("SW", -3.65, -2.65),
    ("SE", 3.65, -2.65),
    ("NW", -3.65, 2.65),
    ("NE", 3.65, 2.65),
)


def _column_part(key, x, y):
    def low(P):
        return _column(P, key, x, y)

    def prim(P):
        return low(P)

    return Part(f"column_{key.lower()}", low, prim=prim, collision="box")


def _beams(P):
    if P["stage"] == 1:
        specs = [
            ((0, -2.75, 5.78), (7.6, 0.30, 0.30)),
            ((0, 2.75, 5.78), (7.6, 0.30, 0.30)),
            ((-3.65, 0, 5.78), (0.30, 5.2, 0.30)),
            ((3.65, 0, 5.78), (0.30, 5.2, 0.30)),
        ]
    else:
        specs = [
            ((0, -2.75, 5.78), (7.6, 0.30, 0.34)),
            ((0, 2.75, 5.78), (7.6, 0.30, 0.34)),
            ((-3.65, 0, 5.78), (0.30, 5.2, 0.34)),
            ((3.65, 0, 5.78), (0.30, 5.2, 0.34)),
        ]
        for i in range(1, 6):
            y = -2.0 + i * 0.8
            specs.append(((0, y, 5.78), (7.0, 0.12, 0.22)))
    return [_box(P, "BEAM_Perimeter", *specs[0], C["paint"])] + [
        _box(P, f"BEAM_Module_{i:02d}", center, size, C["paint"])
        for i, (center, size) in enumerate(specs[1:], 1)
    ]


def _beams_prim(P):
    return _beams(P)


def _deck_prim(P):
    return [_box(P, "DECK_Blockout", (0, 0, 5.96), (8.0, 6.0, 0.08), C["grate"], 0.0)]


def _deck(P):
    if P["stage"] == 1:
        return _deck_prim(P)
    longitudinal, cross = [], []
    for i in range(60):
        y = -2.95 + 0.1 * i
        longitudinal.append(((0, y, 5.972), (8.0, 0.025, 0.012)))
    for i in range(80):
        x = -3.95 + 0.1 * i
        cross.append(((x, 0, 5.988), (0.025, 6.0, 0.012)))
    return [
        _boxes(P, "DECK_Grate_Longitudinal", longitudinal, C["grate"]),
        _boxes(P, "DECK_Grate_Cross", cross, C["grate"]),
    ]


def _guardrail_specs():
    panels, posts, rails = [], [], []
    panel_z, panel_h = 6.39, 0.78

    def panel_run(start, end, fixed, axis):
        count = max(1, math.ceil(end - start))
        step = (end - start) / count
        for i in range(count):
            a, b = start + i * step, start + (i + 1) * step
            center, width = (a + b) * 0.5, b - a - 0.02
            if axis == "x":
                panels.append(((center, fixed, panel_z), (width, 0.025, panel_h)))
                post_x = min(max(a, -3.97), 3.97)
                post_y = fixed + (0.04 if fixed < 0 else -0.04)
                posts.append(((post_x, post_y, 6.5), (0.06, 0.06, 1.0)))
            else:
                panels.append(((fixed, center, panel_z), (0.025, width, panel_h)))
                post_x = fixed + (0.03 if fixed < 0 else -0.03)
                post_y = min(max(a, -2.97), 2.97)
                posts.append(((post_x, post_y, 6.5), (0.06, 0.06, 1.0)))

    panel_run(-4.0, 4.0, 2.98, "x")
    panel_run(-4.0, -0.75, -2.98, "x")
    panel_run(0.75, 4.0, -2.98, "x")
    panel_run(-3.0, 3.0, -3.96, "y")
    panel_run(-3.0, 3.0, 3.96, "y")
    rails.extend((
        ((0, 2.965, 6.965), (8.0, 0.07, 0.07)),
        ((-3.965, 0, 6.965), (0.07, 6.0, 0.07)),
        ((3.965, 0, 6.965), (0.07, 6.0, 0.07)),
        ((-2.375, -2.965, 6.965), (3.25, 0.07, 0.07)),
        ((2.375, -2.965, 6.965), (3.25, 0.07, 0.07)),
    ))
    return panels, posts, rails


def _guardrails(P):
    if P["stage"] == 1:
        return [
            _box(P, "RAIL_North_Blockout", (0, 2.98, 6.5), (8.0, 0.04, 1.0), C["paint"], 0.0),
            _box(P, "RAIL_West_Blockout", (-3.98, 0, 6.5), (0.04, 6.0, 1.0), C["paint"], 0.0),
            _box(P, "RAIL_East_Blockout", (3.98, 0, 6.5), (0.04, 6.0, 1.0), C["paint"], 0.0),
            _box(P, "RAIL_South_Left_Blockout", (-2.35, -2.98, 6.5), (3.3, 0.04, 1.0), C["paint"], 0.0),
            _box(P, "RAIL_South_Right_Blockout", (2.35, -2.98, 6.5), (3.3, 0.04, 1.0), C["paint"], 0.0),
        ]
    panels, posts, rails = _guardrail_specs()
    return [
        _boxes(P, "RAIL_Sheet_Modules", panels, C["paint"]),
        _boxes(P, "RAIL_Post_Modules", posts, C["paint"]),
    ] + [
        _box(P, f"RAIL_Top_Module_{i:02d}", center, size, C["paint"])
        for i, (center, size) in enumerate(rails, 1)
    ]


def _stairs_prim(P):
    front, back = L.STAIR_Y_START - 0.14, L.STAIR_Y_END
    side = ((front, 0.0), (back, L.DECK_Z), (back, 0.0))
    fa = [(-0.65, y, z) for y, z in side]
    fb = [(0.65, y, z) for y, z in side]
    return [mesh.extrude_polys(nm(P, "STAIR_Ramp_Blockout"), P["coll"], [(fa, fb)], C["grate"])]


def _stairs(P):
    if P["stage"] == 1:
        return _stairs_prim(P)
    rise = L.DECK_Z / L.STAIR_COUNT
    treads, nosings, bolts = [], [], []
    for i in range(L.STAIR_COUNT):
        y = L.STAIR_Y_START + (i + 0.5) * L.STAIR_TREAD
        top = (i + 1) * rise
        z = top - L.STAIR_THICKNESS * 0.5
        treads.append(((0, y, z), (L.STAIR_WIDTH, L.STAIR_TREAD, L.STAIR_THICKNESS)))
        nosings.append(((0, y - L.STAIR_TREAD * 0.38, top + 0.003),
                        (L.STAIR_WIDTH, 0.03, 0.006)))
        if P["detail"]:
            for x in (-0.52, 0.52):
                bolts.append(((x, y - L.STAIR_TREAD * 0.38, top + 0.006),
                              (x, y - L.STAIR_TREAD * 0.38, top + 0.02), 0.012))
    theta = math.atan2(L.DECK_Z, L.STAIR_RUN)
    center_y = (L.STAIR_Y_START + L.STAIR_Y_END) * 0.5
    center_z = L.DECK_Z * 0.5 + 0.15
    out = [
        _boxes(P, "STAIR_Treads", treads, C["grate"]),
        _boxes(P, "STAIR_Worn_Nosings", nosings, C["worn"]),
        _box(P, "STAIR_Stringer_Left", (-0.69, center_y, center_z),
             (0.14, math.hypot(L.STAIR_RUN, L.DECK_Z), 0.24), C["paint"], rot=Matrix.Rotation(theta, 3, "X")),
        _box(P, "STAIR_Stringer_Right", (0.69, center_y, center_z),
             (0.14, math.hypot(L.STAIR_RUN, L.DECK_Z), 0.24), C["paint"], rot=Matrix.Rotation(theta, 3, "X")),
        _box(P, "STAIR_Footing", (0, L.STAIR_Y_START - 0.04, 0.06),
             (L.STAIR_WIDTH + 0.2, 0.20, 0.12), C["paint"]),
    ]
    if bolts:
        out.append(mesh.multi_cyl(nm(P, "FASTENER_STAIR_TreadBolts"), P["coll"],
                                  bolts, segs=8, mat=C["worn"]))
    return out


def _stair_rails_prim(P):
    theta = math.atan2(L.DECK_Z, L.STAIR_RUN)
    center_y = (L.STAIR_Y_START + L.STAIR_Y_END) * 0.5
    center_z = L.DECK_Z * 0.5 + 1.0 - 0.0332
    return [
        _box(P, "STAIR_RAIL_Left_Blockout", (-0.80, center_y, center_z),
             (0.08, math.hypot(L.STAIR_RUN, L.DECK_Z), 0.08), C["paint"], rot=Matrix.Rotation(theta, 3, "X")),
        _box(P, "STAIR_RAIL_Right_Blockout", (0.80, center_y, center_z),
             (0.08, math.hypot(L.STAIR_RUN, L.DECK_Z), 0.08), C["paint"], rot=Matrix.Rotation(theta, 3, "X")),
    ]


def _stair_rails(P):
    theta = math.atan2(L.DECK_Z, L.STAIR_RUN)
    length = math.hypot(L.STAIR_RUN, L.DECK_Z)
    center_y = (L.STAIR_Y_START + L.STAIR_Y_END) * 0.5
    top_center = (0, center_y, L.DECK_Z * 0.5 + 1.0 - 0.0291)
    mid_center = (0, center_y, L.DECK_Z * 0.5 + 0.5 - 0.0187)
    rot = Matrix.Rotation(theta, 3, "X")
    rails = []
    posts = []
    for x in (-0.80, 0.80):
        rails.extend((
            _box(P, f"STAIR_RAIL_Top_{'L' if x < 0 else 'R'}", (x, top_center[1], top_center[2]),
                 (0.07, length, 0.07), C["paint"], rot=rot),
            _box(P, f"STAIR_RAIL_Mid_{'L' if x < 0 else 'R'}", (x, mid_center[1], mid_center[2]),
                 (0.045, length, 0.045), C["paint"], rot=rot),
        ))
        for i in range(17):
            step = min(i * 2, L.STAIR_COUNT - 1)
            y = L.STAIR_Y_START + (step + 0.5) * L.STAIR_TREAD
            step_top = (step + 1) * L.DECK_Z / L.STAIR_COUNT
            posts.append(((x, y, step_top + 0.5), (0.045, 0.045, 1.0)))
    rails.append(_boxes(P, "STAIR_RAIL_Posts", posts, C["paint"]))
    return rails


PARTS = [
    *(_column_part(key, x, y) for key, x, y in _COLUMN_POSITIONS),
    Part("beams", _beams, prim=_beams_prim, collision="none"),
    Part("deck", _deck, prim=_deck_prim, collision="box"),
    Part("guardrails", _guardrails, prim=_guardrails, collision="none"),
    Part("stairs", _stairs, prim=_stairs_prim, collision="hull"),
    Part("stair_rails", _stair_rails, prim=_stair_rails_prim, collision="none"),
]
