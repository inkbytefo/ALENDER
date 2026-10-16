from PIL import Image
import numpy as np
import collections

im = np.asarray(Image.open("output/PROP_K7_Rifle/work/s1/s1_R02_photo_diff.png").convert("RGB")).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
red = (r > 150) & (g < 100) & (b < 100)      # model only
blue = (b > 150) & (r < 100) & (g < 100)     # photo only

for name, mask in (("RED model-only", red), ("BLUE photo-only", blue)):
    ys, xs = np.nonzero(mask)
    print(name, "count:", int(mask.sum()))
    if len(xs):
        col = collections.Counter(int(x // 40) * 40 for x in xs)
        row = collections.Counter(int(y // 40) * 40 for y in ys)
        print("  x-bands:", sorted(col.items()))
        print("  y-bands:", sorted(row.items()))
