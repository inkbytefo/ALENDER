"""
Image tools used during reference analysis and review (run with normal python, needs Pillow).

  crop(src, out, box, scale)          gridded zoom crop: labels every 10 px, red line every 50 px
  grid(src, out, step)                whole image with a labelled grid
  overlay(ref, render, prefix, marks) render (RGBA, from the reference camera) over the photo:
                                      <prefix>_blend.png (55% mix) + <prefix>_edge.png (cyan outline)
  sheet(paths, out, cols, width)      contact sheet of several images
  photo_mask(src, out, seed, thr)     object mask of a photo on a plain light background (threshold +
                                      flood fill from a seed pixel on the object, small holes filled)
  snap_sheet(src, poly, out, ...)     landmark polyline + suggested edge corrections drawn on a crop
"""
import os
from PIL import Image, ImageDraw, ImageFilter


def crop(src, out, box, scale=4):
    x0, y0, x1, y1 = box
    im = Image.open(src).convert("RGB")
    c = im.crop((x0, y0, x1, y1))
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    for x in range(x0 - x0 % 10 + 10, x1, 10):
        X = (x - x0) * scale
        d.line([(X, 0), (X, c.height)], fill=(255, 0, 0) if x % 50 == 0 else (0, 200, 0), width=1)
        d.text((X + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(y0 - y0 % 10 + 10, y1, 10):
        Y = (y - y0) * scale
        d.line([(0, Y), (c.width, Y)], fill=(255, 0, 0) if y % 50 == 0 else (0, 200, 0), width=1)
        d.text((2, Y + 2), str(y), fill=(0, 255, 255))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    c.save(out)
    return out


def grid(src, out, step=20):
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    for x in range(0, im.width, step):
        d.line([(x, 0), (x, im.height)], fill=(0, 255, 0), width=1)
        d.text((x + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(0, im.height, step):
        d.line([(0, y), (im.width, y)], fill=(0, 255, 0), width=1)
        d.text((2, y + 2), str(y), fill=(0, 255, 255))
    im.save(out)
    return out


def overlay(ref_path, render_path, prefix, marks=()):
    """marks: [(u, v), ...] measured landmarks drawn as magenta crosses. Returns covered px."""
    import numpy as np
    ref = Image.open(ref_path).convert("RGB")
    ren = Image.open(render_path).convert("RGBA").resize(ref.size)
    a = np.asarray(ren)[..., 3] > 20
    mask = Image.fromarray((a * 255).astype("uint8"))
    Image.composite(Image.blend(ref, ren.convert("RGB"), 0.55), ref, mask).save(prefix + "_blend.png")
    edge = np.asarray(mask.filter(ImageFilter.FIND_EDGES)) > 0
    e = np.asarray(ref).copy()
    e[edge] = (0, 255, 255)
    img = Image.fromarray(e)
    d = ImageDraw.Draw(img)
    for (u, v) in marks:
        d.line([(u - 6, v), (u + 6, v)], fill=(255, 0, 255), width=2)
        d.line([(u, v - 6), (u, v + 6)], fill=(255, 0, 255), width=2)
    img.save(prefix + "_edge.png")
    return int(a.sum())


def sheet(paths, out, cols=2, width=1440, bg=(205, 205, 208)):
    ims = []
    for p in paths:
        im = Image.open(p)
        if im.mode == "RGBA":
            b = Image.new("RGBA", im.size, bg + (255,))
            b.alpha_composite(im)
            im = b
        ims.append(im.convert("RGB"))
    cw = width // cols
    cells = [im.resize((cw, int(im.height * cw / im.width))) for im in ims]
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    H = sum(max(c.height for c in r) for r in rows)
    W = Image.new("RGB", (width, H), bg)
    y = 0
    for r in rows:
        for i, c in enumerate(r):
            W.paste(c, (i * cw, y))
        y += max(c.height for c in r)
    W.save(out)
    return out


def _box(a, r):
    """Sum over a (2r+1)^2 window (integral image)."""
    import numpy as np
    c = np.pad(a, ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    return c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]


def _half_max_edge(obj, dark, band):
    """Re-decide the outer `band` px of a rough object mask with a local 50 % threshold."""
    import numpy as np
    from workbench.silhouette import dilate
    inner = ~dilate(~obj, band)
    outer = dilate(obj, band) & ~obj
    r = 2 * band
    n_in, n_out = _box(inner.astype(np.float32), r), _box(outer.astype(np.float32), r)
    t_in = _box(dark * inner, r) / np.maximum(n_in, 1)
    t_out = _box(dark * outer, r) / np.maximum(n_out, 1)
    thr = np.where((n_in > 0) & (n_out > 0), (t_in + t_out) / 2, 255.0)
    ring = obj & ~inner
    return inner | (ring & (dark < thr))


def photo_mask(src, out, seed, thr=235, sat=40, max_hole=400, fill=(), band=6):
    """Deterministic silhouette of an object photographed on a plain LIGHT background (no ML):
    foreground = darker than thr in any channel or saturated (max-min > sat); keep only the region
    connected to `seed` (a pixel on the object, e.g. landmarks.ANCHOR_PX); fill enclosed holes smaller
    than max_hole px (glare), keep real openings (trigger guards, windows). ALWAYS look at the result
    before using it as ref/REF_MASK.png - shaded / reflective edges can still fail (lesson 20).
    fill=[(u, v), ...] forces the enclosed regions containing those pixels to be filled (chrome glare
    that reads as background, e.g. a bolt carrier seen through an ejection port).
    band > 0: local 50 % rule on the outer `band` px of the rough mask - a pixel stays object only if
    its darkest channel is below the mean of the local object tone and the local background tone,
    so soft shadows / haze (lesson 20) and grey metal are both judged against their own neighbours."""
    import numpy as np
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.int16)
    fg = (im.min(axis=2) < thr) | ((im.max(axis=2) - im.min(axis=2)) > sat)
    lab = Image.fromarray((fg * 255).astype("uint8")).copy()   # own buffer: floodfill writes in place
    sx, sy = int(seed[0]), int(seed[1])
    if not fg[sy, sx]:
        raise ValueError(f"seed {seed} is background (value {im[sy, sx].tolist()}) - pick a pixel on the object")
    ImageDraw.floodfill(lab, (sx, sy), 128)
    obj = np.asarray(lab) == 128
    if band:
        obj = _half_max_edge(obj, im.min(axis=2).astype(np.float32), band)
        lab = Image.fromarray((obj * 255).astype("uint8")).copy()
        ImageDraw.floodfill(lab, (sx, sy), 128)
        obj = np.asarray(lab) == 128
    from workbench.silhouette import label
    H, W = obj.shape
    comp = Image.fromarray(np.where(obj, 0, 255).astype("uint8")).copy()
    for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1), (W // 2, 0), (W // 2, H - 1), (0, H // 2), (W - 1, H // 2)):
        if comp.getpixel((x, y)) == 255:
            ImageDraw.floodfill(comp, (x, y), 100)            # true background, connected to the border
    bg = label(np.asarray(comp) == 255)                       # enclosed holes only (small -> fast)
    ids, counts = np.unique(bg[bg >= 0], return_counts=True)
    forced = {int(bg[int(v), int(u)]) for u, v in fill if bg[int(v), int(u)] >= 0}
    small = [i for i, n in zip(ids, counts) if n <= max_hole or i in forced]
    kept = sum(1 for i, n in zip(ids, counts) if n > max_hole and i not in forced)
    filled = len(small)
    c = np.where(obj | np.isin(bg, small), 0, 255)
    mask = (c == 0)
    Image.fromarray((mask * 255).astype("uint8")).save(out)
    return dict(path=out, pixels=int(mask.sum()), holes_filled=filled, openings_kept=kept)


def snap_sheet(src, poly, out, sug, box=None, scale=3):
    """Draw a landmark polyline (cyan) and snap() suggestions (yellow arrows) on a zoomed crop."""
    im = Image.open(src).convert("RGB")
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    x0, y0, x1, y1 = box or (int(min(us)) - 20, int(min(vs)) - 20, int(max(us)) + 20, int(max(vs)) + 20)
    x0, y0 = max(0, x0), max(0, y0)
    c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST)
    d = ImageDraw.Draw(c)
    P = lambda u, v: ((u - x0) * scale, (v - y0) * scale)
    d.line([P(u, v) for u, v in poly] + [P(*poly[0])], fill=(0, 255, 255), width=1)
    for s in sug:
        a = P(s["u"], s["v"])
        b = P(s["u"] + s["du"], s["v"] + s["dv"])
        col = (255, 220, 0) if s["ok"] else (255, 60, 60)
        d.line([a, b], fill=col, width=2)
        d.ellipse([b[0] - 3, b[1] - 3, b[0] + 3, b[1] + 3], outline=col)
        d.text((a[0] + 4, a[1] - 12), str(s["i"]), fill=(255, 0, 255))
    c.save(out)
    return out
