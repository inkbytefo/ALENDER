"""Folder conventions. Every asset lives in projects/<ASSET>/ and writes to output/<ASSET>/."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS = os.path.join(ROOT, "projects")
OUTPUT = os.path.join(ROOT, "output")
TEMPLATES = os.path.join(ROOT, "templates")


def project_dir(asset):
    return os.path.join(PROJECTS, asset)


def out(asset, kind="", *parts):
    """output/<asset>/<kind>/...  kind in {blend, glb, renders, video, work}; creates the folder."""
    d = os.path.join(OUTPUT, asset, kind) if kind else os.path.join(OUTPUT, asset)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *parts) if parts else d


def milestone(asset, tag):
    """output/<asset>/blend/<asset>_<tag>.blend  e.g. tag='00_SETUP', '02_COMPLETE_LOW'."""
    return out(asset, "blend", f"{asset}_{tag}.blend")
