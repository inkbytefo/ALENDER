"""Reproduce intake crops and provenance; host Python, no geometry."""
import hashlib
import json
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
REF = HERE / "ref"
RECTS = {
    "REF_REAR.png": (0, 0, 963, 399),
    "REF_FRONT.png": (0, 399, 963, 839),
    "REF_FRONT_ALT.png": (0, 839, 963, 1200),
}
def main():
    with Image.open(REF / "REAL_REFERENCE.png") as source:
        assert source.size == (963, 1200)
        for name, rect in RECTS.items():
            source.crop(rect).save(REF / name)
    evidence = {"status": "S1_GATE_FAILED", "stages_passed": [], "sources": {}}
    for name in ("REAL_REFERENCE.png", "MODELING_CHEATSHEET.png", "FACTORY_BLUEPRINT.png"):
        path = REF / name
        with Image.open(path) as im:
            size = list(im.size)
        evidence["sources"][name] = {"size_px": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    evidence["crop_rects_xyxy"] = RECTS
    evidence["factory_dimensions_mm"] = {"length": 4330, "width": 1665, "height": 1370, "wheelbase": 2570, "track_front": 1370, "track_rear": 1365}
    evidence["blockers"] = ["S1 R02 p95 exceeds 14px; six correction passes exhausted", "Camera fit mean error 12.59px", "Photo mask manually traced, not independently segmented"]
    (HERE / "intake_report.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
if __name__ == "__main__":
    main()
