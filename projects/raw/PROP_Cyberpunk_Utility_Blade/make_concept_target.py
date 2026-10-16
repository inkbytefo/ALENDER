"""Regenerate the authored side-view concept target used to frame S1-S3 review cameras.

Run from the repository root: python projects/PROP_Cyberpunk_Utility_Blade/make_concept_target.py
This is generated from landmarks.py, not a photo or an independent reference.
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import landmarks as L

image = Image.new("RGBA", L.IMAGE_SIZE, (28, 31, 35, 255))
draw = ImageDraw.Draw(image)
for polygon in L.SILHOUETTE:
    draw.polygon(polygon, fill=(218, 223, 227, 255))
ref_dir = HERE / "ref"
ref_dir.mkdir(exist_ok=True)
image.save(ref_dir / L.REFERENCE_IMAGE)
