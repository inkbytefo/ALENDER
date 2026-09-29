"""Full build of PROP_AK_Rifle:   python wb.py build PROP_AK_Rifle"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "stage1.py"), run_name="__main__")
runpy.run_path(os.path.join(HERE, "stage2.py"), run_name="__main__")
