import sys
sys.path.insert(0, ".")
import numpy as np
from PIL import Image
from pathlib import Path
from workbench.silhouette import simplify

mask_path = Path("projects/PROP_Colt_1911/ref/REF_MASK.png")
im = Image.open(mask_path).convert("L")
arr = np.array(im) > 128

# Moore-Neighbor tracing or simple grid walk
# Find the first pixel
start_row, start_col = np.where(arr)[0][0], np.where(arr)[1][np.where(arr)[0] == np.where(arr)[0][0]][0]

# Simple 8-direction boundary tracer
directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

contour = []
curr = (start_row, start_col)
dir_idx = 0
visited = set()

# Safe boundary walk
max_steps = 20000
step = 0
while step < max_steps:
    contour.append((float(curr[1]), float(curr[0]))) # (u, v)
    visited.add(curr)
    found_next = False
    for i in range(8):
        check_dir = (dir_idx + 6 + i) % 8
        dr, dc = directions[check_dir]
        nr, nc = curr[0] + dr, curr[1] + dc
        if 0 <= nr < arr.shape[0] and 0 <= nc < arr.shape[1] and arr[nr, nc]:
            curr = (nr, nc)
            dir_idx = check_dir
            found_next = True
            break
    if not found_next or (curr == (start_row, start_col) and step > 10):
        break
    step += 1

print(f"Traced boundary: {len(contour)} points.")
poly_simple = simplify(contour + [contour[0]], 3.5)
print(f"Simplified boundary: {len(poly_simple)} points.")

# Save to landmarks snippet
with open("projects/PROP_Colt_1911/ref/CONTOUR.json", "w") as f:
    import json
    json.dump([[round(u, 1), round(v, 1)] for u, v in poly_simple], f)

print("Saved CONTOUR.json successfully.")
