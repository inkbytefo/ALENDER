"""Edge measurements on ref/REF_MASK.png (host python, no Blender):
    python projects/PROP_AK_Rifle/measure.py cols U0 U1 V0 V1 [step]   top / bottom mask edge per column
    python projects/PROP_AK_Rifle/measure.py rows U0 U1 V0 V1 [step]   left / right mask edge per row
    python projects/PROP_AK_Rifle/measure.py runs  U V0 V1             mask runs down one column
    python projects/PROP_AK_Rifle/measure.py hruns V U0 U1             mask runs along one row
`wb.py profile` covers top/bottom polylines; this adds left/right edges and interior runs (holes,
gaps between parts) that the landmarks of upright parts (grip, front sight, butt) need."""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
M = Image.open(os.path.join(HERE, "ref", "REF_MASK.png")).convert("L")
px = M.load()


def on(u, v):
    return px[u, v] > 127


def runs(vals):
    """[(start, end)] of consecutive True indices (inclusive)."""
    out, s = [], None
    for i, b in enumerate(vals):
        if b and s is None:
            s = i
        if not b and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(vals) - 1))
    return out


mode, a = sys.argv[1], [int(x) for x in sys.argv[2:]]
if mode == "cols":
    u0, u1, v0, v1 = a[:4]
    for u in range(u0, u1 + 1, a[4] if len(a) > 4 else 10):
        r = runs([on(u, v) for v in range(v0, v1 + 1)])
        print(u, "top", v0 + r[0][0] if r else None, "bot", v0 + r[-1][1] if r else None,
              "runs", [(v0 + s, v0 + e) for s, e in r])
elif mode == "rows":
    u0, u1, v0, v1 = a[:4]
    for v in range(v0, v1 + 1, a[4] if len(a) > 4 else 10):
        r = runs([on(u, v) for u in range(u0, u1 + 1)])
        print(v, "left", u0 + r[0][0] if r else None, "right", u0 + r[-1][1] if r else None,
              "runs", [(u0 + s, u0 + e) for s, e in r])
elif mode == "runs":
    u, v0, v1 = a
    print(u, [(v0 + s, v0 + e) for s, e in runs([on(u, v) for v in range(v0, v1 + 1)])])
elif mode == "hruns":
    v, u0, u1 = a
    print(v, [(u0 + s, u0 + e) for s, e in runs([on(u, v) for u in range(u0, u1 + 1)])])
