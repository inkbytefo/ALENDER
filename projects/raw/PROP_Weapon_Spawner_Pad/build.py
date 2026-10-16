"""Staged build of PROP_Weapon_Spawner_Pad:   python wb.py build PROP_Weapon_Spawner_Pad [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Weapon_Spawner_Pad   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
