import sys
sys.path.insert(0, ".")
import numpy as np
from PIL import Image
from pathlib import Path
from workbench.silhouette import simplify

mask_path = Path("projects/PROP_Colt_1911/ref/REF_MASK.png")
im = Image.open(mask_path).convert("L")
arr = np.array(im) > 128

# Find outer contours using cv2 or marching squares/simple boundary scan
import cv2
contours, hierarchy = cv2.findContours((arr * 255).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

print(f"Found {len(contours)} contours.")
main_contour = max(contours, key=cv2.contourArea)
poly = [(float(pt[0][0]), float(pt[0][1])) for pt in main_contour]

print(f"Raw contour points: {len(poly)}")
simplified_poly = simplify(poly, tol_px=4.0)
print(f"Simplified contour points (tol=4.0px): {len(simplified_poly)}")

# Print polyline code
print("\n# Copy into landmarks.py:")
print("BODY_OUTLINE = [")
for u, v in simplified_poly:
    print(f"    ({round(u, 1)}, {round(v, 1)}),")
print("]")
