"""Staged build of VEH_Honda_NSX_Widebody:   python wb.py build VEH_Honda_NSX_Widebody [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate VEH_Honda_NSX_Widebody   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
