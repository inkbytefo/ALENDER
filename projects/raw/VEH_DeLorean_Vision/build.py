"""Staged build of VEH_DeLorean_Vision:   python wb.py build VEH_DeLorean_Vision [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate VEH_DeLorean_Vision   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline
from production import bake, atlas, copies
pipeline.game.bake = bake
pipeline.uv.atlas = atlas
pipeline.game.copies = copies

pipeline.main(__file__)
