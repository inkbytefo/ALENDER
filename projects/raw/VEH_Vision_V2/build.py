"""Staged build of VEH_Vision_V2:   python wb.py build VEH_Vision_V2 [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate VEH_Vision_V2   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
