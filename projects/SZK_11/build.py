"""Full build of SZK_11:   python wb.py build SZK_11"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "stage1.py"), run_name="__main__")
runpy.run_path(os.path.join(HERE, "stage2.py"), run_name="__main__")
