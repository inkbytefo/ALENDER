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
