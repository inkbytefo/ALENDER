"""Staged build of __ASSET__:   python wb.py build __ASSET__ [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate __ASSET__   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
