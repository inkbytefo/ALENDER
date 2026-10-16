"""Staged build of PROP_Shipping_Container:   python wb.py build PROP_Shipping_Container [--stage N | --from N | --until N] [--no-bake]
Then:  python wb.py gate PROP_Shipping_Container   (PASS/FAIL per stage, docs/05_VALIDATION.md)"""
from workbench.bl import pipeline

pipeline.main(__file__)
