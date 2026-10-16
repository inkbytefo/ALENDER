"""Staged build of PROP_Cyberpunk_Utility_Blade:   python wb.py build PROP_Cyberpunk_Utility_Blade [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Cyberpunk_Utility_Blade   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
