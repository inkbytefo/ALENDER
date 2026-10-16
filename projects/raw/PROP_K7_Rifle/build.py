"""Staged build of PROP_K7_Rifle:   python wb.py build PROP_K7_Rifle [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_K7_Rifle   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
