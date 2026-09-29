"""
Image tools used during reference analysis and review (run with normal python, needs Pillow).

  crop(src, out, box, scale)          gridded zoom crop: labels every 10 px, red line every 50 px
  grid(src, out, step)                whole image with a labelled grid
  overlay(ref, render, prefix, marks) render (RGBA, from the reference camera) over the photo:
                                      <prefix>_blend.png (55% mix) + <prefix>_edge.png (cyan outline)
  sheet(paths, out, cols, width)      contact sheet of several images
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
