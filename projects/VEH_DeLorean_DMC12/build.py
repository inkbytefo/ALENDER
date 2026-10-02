"""Staged build of VEH_DeLorean_DMC12:   python wb.py build VEH_DeLorean_DMC12 [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate VEH_DeLorean_DMC12   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
