"""Staged build of CHAR_Tactical_Mannequin:   python wb.py build CHAR_Tactical_Mannequin [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate CHAR_Tactical_Mannequin   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
