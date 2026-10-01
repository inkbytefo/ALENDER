"""Staged build of VEH_Hakosuka_Custom:   python wb.py build VEH_Hakosuka_Custom [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate VEH_Hakosuka_Custom   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
