"""Staged build of PROP_TWR_Industrial_Watchtower:   python wb.py build PROP_TWR_Industrial_Watchtower [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_TWR_Industrial_Watchtower   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
