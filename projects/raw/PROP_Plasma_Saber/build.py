"""Staged build of PROP_Plasma_Saber:   python wb.py build PROP_Plasma_Saber [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Plasma_Saber   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
