"""Staged build of PROP_Glock_19:   python wb.py build PROP_Glock_19 [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Glock_19   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
