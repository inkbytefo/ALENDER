import sys
sys.path.insert(0, ".")
import json
from pathlib import Path
from PIL import Image
import numpy as np
from workbench.silhouette import simplify

ref_dir = Path("projects/PROP_Colt_1911/ref")
parts = [
    "FRAME_POLY",
    "SLIDE_POLY",
    "HAMMER_POLY",
    "TRIGGER_POLY",
    "SIGHT_FRONT_POLY",
    "SIGHT_REAR_POLY",
]

result = {}

for p in parts:
    mask_file = ref_dir / f"MASK_{p}.png"
    if not mask_file.exists():
        continue
    im = Image.open(mask_file).convert("L")
    arr = np.array(im) > 30

    start_rows, start_cols = np.where(arr)
    if len(start_rows) == 0:
        continue

    start_row = start_rows[0]
    start_col = start_cols[np.where(start_rows == start_row)[0][0]]

    directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    contour = []
    curr = (start_row, start_col)
    dir_idx = 0

    max_steps = 15000
    step = 0
    while step < max_steps:
        contour.append((float(curr[1]), float(curr[0])))
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

    simp = simplify(contour + [contour[0]], 3.0)
    result[p] = [[round(u, 1), round(v, 1)] for u, v in simp]
    print(f"{p}: {len(contour)} raw -> {len(simp)} simplified points.")
    mask_file.unlink()

out_json = ref_dir / "ACCURATE_PART_POLYS.json"
with open(out_json, "w") as f:
    json.dump(result, f, indent=2)

print(f"Successfully saved {out_json}")
