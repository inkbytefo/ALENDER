"""Full reproducible build: Stage 1 LOW -> gate -> Stage 2 HIGH.
    python wb.py build VEH_Gemini_Motorcycle
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "stage1.py"), run_name="__main__")
runpy.run_path(os.path.join(HERE, "stage2.py"), run_name="__main__")
