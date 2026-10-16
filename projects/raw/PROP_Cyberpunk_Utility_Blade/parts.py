"""Procedural builders for the original compact cyberpunk utility-blade concept."""
import math

import landmarks as L
from workbench import stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "small_prop"
TARGET_DIMS = (0.030, 0.240, 0.053)  # X thickness, Y overall, Z height; concept targets
GROUND = False                       # hand-held prop; grip-origin is at (0, 0, 0)
PROFILES = {
    1: stages.profile(1, ring=8, stations=4),
    2: stages.profile(2, ring=12, stations=8),
    3: stages.profile(3, ring=16, stations=12),
}
GAME = dict(engine="godot", bake=True, tex=512, lod=(0.5, 0.25), drop_small_m=0.002,
            image_format="JPEG", image_quality=92)

PALETTE = {
    "MAT_BLADE": ((0.42, 0.49, 0.53), 0.92, 0.28),
    "MAT_FRAME": ((0.045, 0.055, 0.067), 0.78, 0.4),
    "MAT_GRIP": ((0.42, 0.105, 0.038), 0.08, 0.48),
    "MAT_ACCENT": ((0.015, 0.48, 0.62), 0.25, 0.3),
}
BLADE, FRAME, GRIP, ACCENT = "MAT_BLADE", "MAT_FRAME", "MAT_GRIP", "MAT_ACCENT"

# The proportions, hidden cross-sections, color blocking and internal construction are
# original concept decisions (not photo evidence); see project.md for explicit uncertainty.
UNCERTAIN = [
    "UNCERTAIN_all dimensions and proportions are original concept targets, not measured evidence",
    "UNCERTAIN_depth/thickness and hand fit are assumed; no orthographic end view exists",
    "UNCERTAIN_internal mechanism, lock, pivot and blade deployment are intentionally not modeled",
    "UNCERTAIN_material palette and accent placement are original stylistic choices",
]
# Blade-to-guard overlap is an intentional, hidden tang/guard junction; keep it out of
# forbidden pairs. The blade-to-grip gap is a genuine clearance and is checked at every stage.
CRITICAL_PAIRS = [
    ("BLADE_Main", "GRIP_Scales"),
]


def nm(P, name):
    return stages.nm(P, name)


def _plate(P, name, outline, x0, x1, material, bevel=0.001):
    ob = mesh.plate(nm(P, name), P["coll"], outline, x0, x1, material)
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


def _primitive(P, name, outline, half_width, material):
    return [prim.plate_px(nm(P, name), P["coll"], outline, half_width, material, tol=3.0)]


def blade_prim(P):
    return _primitive(P, "BLADE_Main", L.BLADE_OUTLINE, 0.006, BLADE)


def blade(P):
    out = [_plate(P, "BLADE_Main", L.BLADE_OUTLINE, -0.006, 0.006, BLADE, 0.0012)]
    # The narrow contrasting channel is a surface inlay, not a sharpened/functional edge.
    if P["stage"] >= 2:
        for side in (-1, 1):
            if side < 0:
                x0, x1 = -0.0068, -0.0061
            else:
                x0, x1 = 0.0061, 0.0068
            out.append(_plate(P, "BLADE_Channel_" + ("R" if side < 0 else "L"),
                              L.BLADE_CHANNEL, x0, x1, ACCENT, 0.00025))
    return out


def frame_prim(P):
    return (_primitive(P, "FRAME_Handle", L.HANDLE_OUTLINE, 0.009, FRAME)
            + _primitive(P, "FRAME_Guard", L.GUARD_OUTLINE, 0.015, FRAME))


def frame(P):
    out = [
        _plate(P, "FRAME_Handle", L.HANDLE_OUTLINE, -0.009, 0.009, FRAME, 0.0015),
        _plate(P, "FRAME_Guard", L.GUARD_OUTLINE, -0.015, 0.015, FRAME, 0.001),
    ]
    return out


def grip_prim(P):
    return _primitive(P, "GRIP_Scales", L.SCALE_OUTLINE, 0.0105, GRIP)


def grip(P):
    out = []
    # Thin raised scales on both faces, set just outside the handle shell.
    out.extend([
        _plate(P, "GRIP_Scale_R", L.SCALE_OUTLINE, -0.0110, -0.0091, GRIP, 0.0007),
        _plate(P, "GRIP_Scale_L", L.SCALE_OUTLINE, 0.0091, 0.0110, GRIP, 0.0007),
    ])
    if P["detail"]:
        for side, tag in ((-1, "R"), (1, "L")):
            if side < 0:
                x0, x1 = -0.0115, -0.01105
            else:
                x0, x1 = 0.01105, 0.0115
            out.append(_plate(P, "GRIP_Inset_" + tag, L.HANDLE_INSET, x0, x1,
                              ACCENT, 0.00015))
            # Two small non-functional fastener heads per grip scale.
            for j, (u, v) in enumerate(((124, 316), (204, 324)), 1):
                y, z = L.P(u, v)
                out.append(mesh.cyl(nm(P, f"FASTENER_Grip_{tag}_{j:02d}"),
                                    P["coll"], (side * 0.0111, y, z),
                                    (side * 0.0117, y, z), 0.00125, 8, FRAME))
    return out


PARTS = [
    Part("blade", blade, prim=blade_prim, collision="hull"),
    Part("frame", frame, prim=frame_prim, collision="hull"),
    Part("grip", grip, prim=grip_prim, collision="hull"),
]
PIVOTS = {}
CHILDREN = {}


def guide_points():
    return {"GRIP_ORIGIN": L.P3(*L.ANCHOR_PX, 0.0)}
