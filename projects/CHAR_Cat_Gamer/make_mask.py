"""
Photo silhouette for CHAR_Cat_Gamer -> ref/REF_MASK.png (+ work/ref_mask_check.png overlay).

`wb.py mask` needs a plain LIGHT background; this photo has a dark red glow, so the rule is
project-specific (deterministic numpy, no ML):
  fur        blue channel high (the red/orange glow has almost no blue)
  headphones strong red inside the two cup windows / the band window (background there is dark)
  vest       black like the background -> closed by hole filling + the hand-traced VEST windows
Run:  python projects/CHAR_Cat_Gamer/make_mask.py        LOOK at the overlay afterwards.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, ROOT]

B_THR = 36                    # fur: blue above this
RED_BOXES = [                 # (u0, v0, u1, v1, R threshold): headphone cups / band
    (255, 170, 400, 445, 120),
    (735, 270, 825, 500, 120),
    (480, 95, 720, 175, 110),
]
DARK_POLYS = []               # filled from landmarks (black vest / band underside touching the background)


def big_components(m, min_px=4000):
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    keep, cur = [], 0
    for sy, sx in zip(*np.nonzero(m)):
        if lab[sy, sx]:
            continue
        cur += 1
        n, q = 0, deque([(sy, sx)])
        lab[sy, sx] = cur
        while q:
            y, x = q.popleft()
            n += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = cur
                    q.append((yy, xx))
        if n >= min_px:
            keep.append(cur)
    return np.isin(lab, keep)


def fill_holes(m):
    h, w = m.shape
    out = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        q.append((0, x)); q.append((h - 1, x))
    for y in range(h):
        q.append((y, 0)); q.append((y, w - 1))
    while q:
        y, x = q.popleft()
        if 0 <= y < h and 0 <= x < w and not out[y, x] and not m[y, x]:
            out[y, x] = True
            q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    return ~out


def shift_or(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def main():
    import landmarks as L
    im = Image.open(os.path.join(HERE, "ref", "REAL_REFERENCE.png")).convert("RGB")
    a = np.asarray(im).astype(np.int32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (B > B_THR) & (B > 0.3 * R)                               # glow / rim light has R >> B
    for (u0, v0, u1, v1, thr) in RED_BOXES:
        box = np.zeros_like(m)
        box[v0:v1, u0:u1] = True
        m |= box & (R > thr) & (R - G > 60)
    dark = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(dark)
    for poly in getattr(L, "MASK_DARK_POLYS", DARK_POLYS):
        d.polygon([tuple(p) for p in poly], fill=255)
    m |= np.asarray(dark) > 0
    excl = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(excl)
    for poly in getattr(L, "MASK_EXCLUDE_POLYS", []):
        d.polygon([tuple(p) for p in poly], fill=255)
    m &= ~(np.asarray(excl) > 0)
    m[int(getattr(L, "MASK_FLOOR_V", 1335)):, :] = False          # floor reflection
    m = ~shift_or(~shift_or(m, 5), 5)                              # closing r=5 (fur gaps, thin stripes)
    m = shift_or(~shift_or(~m, 2), 2)                              # opening r=2 (whiskers, sparks, fur wisps)
    m = fill_holes(big_components(m))
    Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(HERE, "ref", "REF_MASK.png"))
    chk = a.copy()
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    chk[~m] = (chk[~m] * 0.45 + np.array([0, 90, 140])).clip(0, 255)
    chk[shift_or(edge, 1)] = (255, 0, 255)
    out = os.path.join(ROOT, "output", "CHAR_Cat_Gamer", "work")
    os.makedirs(out, exist_ok=True)
    Image.fromarray(chk.astype(np.uint8)).save(os.path.join(out, "ref_mask_check.png"))
    ys, xs = np.nonzero(m)
    print("mask px", int(m.sum()), "bbox u", xs.min(), xs.max(), "v", ys.min(), ys.max())


if __name__ == "__main__":
    main()
