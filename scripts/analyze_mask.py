from PIL import Image
import numpy as np
import collections

mask = np.asarray(Image.open("projects/PROP_K7_Rifle/ref/REF_MASK.png").convert("L"))
photo = np.asarray(Image.open("projects/PROP_K7_Rifle/ref/REAL_REFERENCE.png").convert("L"))
print("mask size", mask.shape, "mask px count:", int((mask > 127).sum()), "of", mask.size)
ys, xs = np.nonzero(mask > 127)
if len(xs):
    print("mask bbox: u", xs.min(), xs.max(), " v", ys.min(), ys.max())
    col = collections.Counter(int(x // 80) * 80 for x in xs)
    print("mask x-bands:", sorted(col.items()))
    row = collections.Counter(int(y // 80) * 80 for y in ys)
    print("mask y-bands:", sorted(row.items()))
pmin = photo.min(axis=2)
ys2, xs2 = np.nonzero(pmin < 120)
print("photo dark px count:", int((pmin < 120).sum()))
if len(xs2):
    print("photo dark bbox: u", xs2.min(), xs2.max(), " v", ys2.min(), ys2.max())
