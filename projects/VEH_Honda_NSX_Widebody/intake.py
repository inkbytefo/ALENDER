"""Reproduce the side-blueprint crop + mask from ref/MODELING_CHEATSHEET.png (panel 4, 'DIMENSIONS').
The only orthographic side drawing available; the photo is a front 3/4 perspective (not gate-able
without a camera fit). Host python only."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = Path(__file__).resolve().parent
REF = HERE / "ref"
BOX = (90, 345, 600, 484)          # sheet px: x0,y0,x1,y1 (y1 = ground line)
UP = 4
def main():
    sheet = Image.open(REF / "MODELING_CHEATSHEET.png").convert("RGB")
    c = sheet.crop(BOX)
    a = np.asarray(c).astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / (mx + 1e-6)
    m = (sat > 0.30) | (mx < 0.5)
    m = ndi.binary_opening(m, np.ones((3, 3)))
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    m = ndi.binary_fill_holes(ndi.binary_closing(m, np.ones((3, 3))))
    m = ndi.binary_opening(m, np.ones((5, 5)))
    big = c.resize((c.width * UP, c.height * UP), Image.LANCZOS)
    big.save(REF / "REF_SIDE_BLUEPRINT.png")
    mm = Image.fromarray((m * 255).astype(np.uint8)).resize(big.size, Image.BILINEAR)
    mm = Image.fromarray(((np.asarray(mm) > 127) * 255).astype(np.uint8))
    mm.save(REF / "REF_MASK.png")
    ys, xs = np.nonzero(np.asarray(mm) > 0)
    print("size", big.size, "bbox", xs.min(), xs.max(), ys.min(), ys.max())
    ov = np.asarray(big).copy()
    edge = np.asarray(mm) > 0
    edge = edge ^ ndi.binary_erosion(edge, iterations=2)
    ov[edge] = (255, 0, 255)
    Image.fromarray(ov).save(REF / "MASK_CHECK.png")
if __name__ == "__main__":
    main()
