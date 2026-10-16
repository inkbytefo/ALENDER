"""Staged build of PROP_Colt_1911:   python wb.py build PROP_Colt_1911 [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Colt_1911   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
