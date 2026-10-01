"""
Silhouette metrics: deterministic numbers instead of "looks aligned" (numpy only, no bpy, no PIL).
Works on the host (wb.py compare / snap) and inside Blender (pipeline gates).

Coordinates are photo pixels (u right, v down); masks are bool arrays indexed [v, u].

    ref = rasterize(L.SILHOUETTE, L.IMAGE_SIZE)       # landmark polygons -> reference mask
    ren = alpha > 0.08                                 # transparent reference-camera render
    m = metrics(ref, ren)    # iou, boundary mean/p95/max px, worst zones with direction
    diff_rgb(ref, ren)       # grey = both, red = photo only (model missing), blue = model only

    snap(gray, poly, radius=6)   # suggest landmark corrections along the strongest nearby edge
    simplify(poly, tol_px)       # Douglas-Peucker (primitive outlines for Stage 1)
"""
import numpy as np


# ----------------------------------------------------------------------------- masks
def dilate(mask, r):
    """Binary dilation with a (2r+1)^2 square (numpy shifts)."""
    m = np.asarray(mask, bool)
    for _ in range(int(r)):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] \
            | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    return m


def close(mask, r):
    """Morphological closing: fills slivers / gaps up to 2r px wide (between adjacent landmark
    polygons), keeps real openings wider than that."""
    return ~dilate(~dilate(mask, r), r)


def rasterize(polys, size, close_px=0):
    """Union of closed polygons [(u, v), ...] (even-odd inside each polygon) -> bool mask (H, W).
    Sampling at pixel centres (u + 0.5, v + 0.5). close_px > 0 closes gaps between adjacent
    polygons (measured outlines never meet exactly - they would score as fake inner edges)."""
    W, H = int(size[0]), int(size[1])
    out = np.zeros((H, W), bool)
    if polys and not isinstance(polys[0][0], (list, tuple)):
        polys = [polys]
    ys = np.arange(H) + 0.5
    for poly in polys:
        p = np.asarray(poly, float)
        if len(p) < 3:
            continue
        a, b = p, np.roll(p, -1, axis=0)
        acc = np.zeros((H, W + 1), np.int32)
        for (x0, y0), (x1, y1) in zip(a, b):
            if y0 == y1:
                continue
            lo, hi = min(y0, y1), max(y0, y1)
            rows = np.nonzero((ys >= lo) & (ys < hi))[0]
            if not len(rows):
                continue
            xs = x0 + (ys[rows] - y0) * (x1 - x0) / (y1 - y0)
            cols = np.clip(np.ceil(xs - 0.5), 0, W).astype(int)
            np.add.at(acc, (rows, cols), 1)
        out |= (np.cumsum(acc, axis=1)[:, :W] % 2).astype(bool)
    return close(out, close_px) if close_px else out


def label(mask):
    """4-connected component labels (numpy only): int array, -1 outside the mask; each component
    is labelled with its smallest flat pixel index. Min-propagation + pointer jumping."""
    mask = np.asarray(mask, bool)
    H, W = mask.shape
    big = H * W
    lab = np.where(mask, np.arange(big).reshape(H, W), big)
    while True:
        m = lab.copy()
        np.minimum(m[1:], lab[:-1], out=m[1:])
        np.minimum(m[:-1], lab[1:], out=m[:-1])
        np.minimum(m[:, 1:], lab[:, :-1], out=m[:, 1:])
        np.minimum(m[:, :-1], lab[:, 1:], out=m[:, :-1])
        m = np.where(mask, m, big)
        flat = np.append(m.ravel(), big)
        for _ in range(4):
            m = np.where(mask, flat[m], big)
            flat = np.append(m.ravel(), big)
        if np.array_equal(m, lab):
            break
        lab = m
    return np.where(mask, lab, -1)


def boundary(mask):
    """Pixels of the mask that touch a non-mask 4-neighbour (image border counts as outside)."""
    m = np.pad(mask, 1)
    inner = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    return mask & ~inner


def points(mask, max_points=20000):
    """(N, 2) float array of (u, v) pixel centres of True pixels (strided if too many)."""
    v, u = np.nonzero(mask)
    pts = np.stack([u + 0.5, v + 0.5], axis=1).astype(np.float32)
    if len(pts) > max_points:
        pts = pts[:: int(np.ceil(len(pts) / max_points))]
    return pts


def nearest(a, b, chunk=1024):
    """Distance from every point of a (N, 2) to the nearest point of b (M, 2)."""
    if not len(a):
        return np.zeros(0, np.float32)
    if not len(b):
        return np.full(len(a), np.inf, np.float32)
    out = np.empty(len(a), np.float32)
    for i in range(0, len(a), chunk):
        d = a[i:i + chunk, None, :] - b[None, :, :]
        out[i:i + chunk] = np.sqrt((d * d).sum(-1).min(1))
    return out


# ----------------------------------------------------------------------------- metrics
def metrics(ref, ren, grid=(8, 4), worst=5):
    """Compare a reference mask with a render mask.
    Returns iou, area ratio, symmetric boundary distance (mean / p95 / max px) and the `worst`
    grid cells (over the union bbox) with their signed error: + = model too large, - = too small."""
    ref, ren = np.asarray(ref, bool), np.asarray(ren, bool)
    inter, union = int((ref & ren).sum()), int((ref | ren).sum())
    out = dict(iou=round(inter / union, 4) if union else 0.0,
               area_ratio=round(int(ren.sum()) / max(1, int(ref.sum())), 4))
    rb, nb = points(boundary(ref)), points(boundary(ren))
    d_rn, d_nr = nearest(rb, nb), nearest(nb, rb)
    d = np.concatenate([d_rn, d_nr])
    if not len(d) or not np.isfinite(d).all():
        out.update(b_mean=float("inf"), b_p95=float("inf"), b_max=float("inf"), zones=[])
        return out
    out.update(b_mean=round(float(d.mean()), 2), b_p95=round(float(np.percentile(d, 95)), 2),
               b_max=round(float(d.max()), 2))
    # signed errors: ref-boundary points covered by the render -> model sticks out (+);
    # render-boundary points outside the photo silhouette -> model sticks out (+)
    s_r = np.where(ren[rb[:, 1].astype(int), rb[:, 0].astype(int)], 1.0, -1.0) * d_rn
    s_n = np.where(ref[nb[:, 1].astype(int), nb[:, 0].astype(int)], -1.0, 1.0) * d_nr
    pts = np.concatenate([rb, nb])
    sgn = np.concatenate([s_r, s_n])
    vv, uu = np.nonzero(ref | ren)
    u0, u1, v0, v1 = uu.min(), uu.max() + 1, vv.min(), vv.max() + 1
    gu, gv = grid
    cells = []
    for i in range(gu):
        for j in range(gv):
            a0, a1 = u0 + (u1 - u0) * i / gu, u0 + (u1 - u0) * (i + 1) / gu
            b0, b1 = v0 + (v1 - v0) * j / gv, v0 + (v1 - v0) * (j + 1) / gv
            sel = (pts[:, 0] >= a0) & (pts[:, 0] < a1) & (pts[:, 1] >= b0) & (pts[:, 1] < b1)
            if sel.sum() < 5:
                continue
            e = sgn[sel]
            mean_abs = float(np.abs(e).mean())
            cells.append(dict(box=[int(a0), int(b0), int(a1), int(b1)], mean_px=round(mean_abs, 1),
                              max_px=round(float(np.abs(e).max()), 1), signed_px=round(float(e.mean()), 1),
                              hint="model too large" if e.mean() > 0.5 else
                                   "model too small" if e.mean() < -0.5 else "mixed"))
    cells.sort(key=lambda c: -c["mean_px"])
    out["zones"] = cells[:worst]
    return out


def gate(m, iou_min, p95_max):
    """(ok, detail) for a metrics() dict against thresholds."""
    ok = m["iou"] >= iou_min and m["b_p95"] <= p95_max
    return ok, "iou %.3f (min %.2f), boundary p95 %.1f px (max %.1f), mean %.1f, max %.1f" % (
        m["iou"], iou_min, m["b_p95"], p95_max, m["b_mean"], m["b_max"])


def diff_rgb(ref, ren, photo=None):
    """uint8 (H, W, 3): grey = both, red = photo only (model missing), blue = model only (extra).
    With a photo (H, W, 3 uint8) the colours are blended over a darkened copy of it."""
    H, W = ref.shape
    base = (np.asarray(photo, np.float32) * 0.45) if photo is not None else np.full((H, W, 3), 30.0, np.float32)
    img = base.copy()
    both, r_only, n_only = ref & ren, ref & ~ren, ren & ~ref
    img[both] = img[both] * 0.5 + np.array([150, 150, 150]) * 0.5
    img[r_only] = np.array([235, 40, 40])
    img[n_only] = np.array([40, 110, 255])
    img[boundary(ref)] = np.array([255, 230, 0])
    return np.clip(img, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- polylines
def edge_profile(mask, us, v0, v1, side="bottom"):
    """Measured edge of a mask along columns: for each u the last (side='bottom') or first
    (side='top') mask pixel between v0 and v1 -> [(u, v), ...] (None where the column is empty).
    With ref/REF_MASK.png this turns 'read the pixel on a crop' into a measurement."""
    m = np.asarray(mask, bool)
    out = []
    for u in us:
        col = np.nonzero(m[int(v0):int(v1), int(round(u))])[0]
        if not len(col):
            out.append((u, None))
            continue
        v = (col[-1] + 1.0) if side == "bottom" else float(col[0])
        out.append((u, v0 + v))
    return out


def simplify(poly, tol):
    """Douglas-Peucker simplification of an open polyline [(u, v), ...] with tolerance in px.
    For a closed polygon pass it with the first point repeated at the end."""
    p = np.asarray(poly, float)
    if len(p) < 3:
        return [tuple(x) for x in p]
    keep = np.zeros(len(p), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(p) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = p[i], p[j]
        ab = b - a
        L = np.hypot(*ab)
        seg = p[i + 1:j]
        if not len(seg):
            continue
        if L == 0:
            dist = np.hypot(*(seg - a).T)
        else:
            dist = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return [tuple(float(c) for c in x) for x in p[keep]]


def snap(gray, poly, radius=6, closed=True, min_strength=12.0):
    """Suggest corrections for measured landmark points: for every vertex search +-radius px along
    the polyline normal for the strongest intensity edge (|dI/dn|). Returns a list of dicts
    {i, u, v, du, dv, shift, strength, ok}; ok = an edge stronger than min_strength was found.
    Suggestions only: the agent reviews them on a crop before editing landmarks.py."""
    g = np.asarray(gray, np.float32)
    H, W = g.shape
    gy, gx = np.gradient(g)
    p = np.asarray(poly, float)
    n = len(p)
    out = []
    for i in range(n):
        prv = p[i - 1] if (closed or i > 0) else p[i]
        nxt = p[(i + 1) % n] if (closed or i < n - 1) else p[i]
        t = nxt - prv
        L = np.hypot(*t)
        if L == 0:
            continue
        nrm = np.array([-t[1], t[0]]) / L
        best = (0.0, 0.0)
        for s in np.arange(-radius, radius + 0.01, 0.5):
            u, v = p[i] + nrm * s
            iu, iv = int(round(u)), int(round(v))
            if not (0 <= iu < W and 0 <= iv < H):
                continue
            val = abs(gx[iv, iu] * nrm[0] + gy[iv, iu] * nrm[1])
            if val > best[0] or (val == best[0] and abs(s) < abs(best[1])):
                best = (val, s)
        du, dv = nrm * best[1]
        out.append(dict(i=i, u=float(p[i][0]), v=float(p[i][1]), du=round(float(du), 1),
                        dv=round(float(dv), 1), shift=round(float(best[1]), 1),
                        strength=round(float(best[0]), 1), ok=bool(best[0] >= min_strength)))
    return out
