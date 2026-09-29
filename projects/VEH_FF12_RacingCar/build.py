"""Full build of VEH_FF12_RacingCar:   python wb.py build VEH_FF12_RacingCar"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "stage1.py"), run_name="__main__")
runpy.run_path(os.path.join(HERE, "stage2.py"), run_name="__main__")
