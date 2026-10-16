"""Staged build of PROP_AK_Rifle:   python wb.py build PROP_AK_Rifle [--stage N|--from N|--until N]"""
from workbench.bl import pipeline

pipeline.main(__file__)
