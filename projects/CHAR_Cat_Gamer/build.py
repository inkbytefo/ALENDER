"""Staged build of CHAR_Cat_Gamer:   python wb.py build CHAR_Cat_Gamer [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate CHAR_Cat_Gamer   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
