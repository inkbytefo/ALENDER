"""Pure-python interpolation helpers used by landmark-driven builders."""


def interp(table, u):
    """Piecewise-linear lookup in [(u, value), ...] sorted by u; clamps at both ends."""
    if u <= table[0][0]:
        return table[0][1]
    for (u0, a), (u1, b) in zip(table, table[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            return a + (b - a) * t
    return table[-1][1]


def polyline_v(poly, u):
    """v of a photo polyline [(u, v), ...] at horizontal position u (first match, clamped)."""
    return interp([(p[0], p[1]) for p in poly], u)


def lin(a, b, n):
    """n evenly spaced values from a to b inclusive."""
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ----------------------------------------------------------------------------- budgets
# Evaluated triangles per stage (modifiers applied) + game delivery budgets, per asset category.
# s1_max: Stage 1 primitives; s2: Stage 2 LOWPOLY = game LOD0 (target range, max);
# s3_max: Stage 3 DETAIL (hero / bake source); lod: LOD1/LOD2 tri ratio of LOD0;
# tex: baked texture size (px); glb_mb: max size of one game LOD0 .glb; mats: material limit.
BUDGETS = {
    "hero_vehicle":       dict(s1_max=3000, s2=(15000, 60000), s2_max=80000, s3_max=150000, lod=(0.5, 0.25), tex=2048, glb_mb=12, mats=8),
    "background_vehicle": dict(s1_max=1500, s2=(4000, 12000), s2_max=20000, s3_max=30000, lod=(0.5, 0.25), tex=1024, glb_mb=4, mats=6),
    "building":           dict(s1_max=2000, s2=(5000, 30000), s2_max=50000, s3_max=100000, lod=(0.5, 0.25), tex=2048, glb_mb=10, mats=8),
    "modular":            dict(s1_max=300, s2=(500, 4000), s2_max=8000, s3_max=15000, lod=(0.5, 0.25), tex=1024, glb_mb=2, mats=4),
    "character":          dict(s1_max=1500, s2=(8000, 30000), s2_max=40000, s3_max=60000, lod=(0.5, 0.25), tex=2048, glb_mb=10, mats=6),
    "hero_prop":          dict(s1_max=1500, s2=(4000, 15000), s2_max=20000, s3_max=60000, lod=(0.5, 0.25), tex=2048, glb_mb=6, mats=4),
    "small_prop":         dict(s1_max=300, s2=(300, 2000), s2_max=3000, s3_max=5000, lod=(0.5, 0.25), tex=512, glb_mb=1, mats=4),
    "large_prop":         dict(s1_max=800, s2=(1500, 8000), s2_max=12000, s3_max=25000, lod=(0.5, 0.25), tex=1024, glb_mb=3, mats=4),
}

# Reference-silhouette gates (landmark polygons vs reference-camera render), per stage.
SILHOUETTE_GATES = {1: dict(iou=0.85, p95=14.0), 2: dict(iou=0.92, p95=6.0), 3: dict(iou=0.92, p95=6.0)}
# Same, against the PHOTO mask (ref/REF_MASK.png): the mask edge itself is uncertain by ~2 px
# (glare, haze) and S2 legitimately omits sub-silhouette details (sling swivels, springs).
# Calibrated on PROP_AK_Rifle (2026-09-29), then frozen.
PHOTO_GATES = {1: dict(iou=0.85, p95=14.0), 2: dict(iou=0.92, p95=8.0), 3: dict(iou=0.93, p95=6.0)}
# Drift between consecutive stages seen from the reference camera (render vs render).
DRIFT_GATES = {2: dict(iou=0.80, p95=16.0, dims=0.04), 3: dict(iou=0.95, p95=4.0, dims=0.015)}

# Game engines: collision naming + preferred export format (docs/12_GAME_READY.md).
ENGINES = {
    "godot":  dict(fmt="glb", col=lambda base, i: f"{base}_{i:02d}-convcolonly"),
    "unity":  dict(fmt="glb", col=lambda base, i: f"{base}_Collider{i:02d}"),
    "unreal": dict(fmt="fbx", col=lambda base, i: f"UCX_{base}_{i:02d}"),
}
