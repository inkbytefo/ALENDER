"""Folder conventions. Every asset lives in projects/<ASSET>/ and writes to output/<ASSET>/."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS = os.path.join(ROOT, "projects")
OUTPUT = os.path.join(ROOT, "output")
TEMPLATES = os.path.join(ROOT, "templates")


def project_dir(asset):
    direct = os.path.join(PROJECTS, asset)
    if os.path.isdir(direct):
        return direct
    for ws in ("raw", "gameready"):
        candidate = os.path.join(PROJECTS, ws, asset)
        if os.path.isdir(candidate):
            return candidate
    return direct


def clean_asset_name(asset):
    return os.path.basename(asset.rstrip("/\\"))


def out(asset, kind="", *parts):
    """output/<asset>/<kind>/...  kind in {blend, glb, renders, video, work}; creates the folder."""
    a_name = clean_asset_name(asset)
    d = os.path.join(OUTPUT, a_name, kind) if kind else os.path.join(OUTPUT, a_name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *parts) if parts else d


def milestone(asset, tag):
    """output/<asset>/blend/<asset>_<tag>.blend  e.g. tag='00_SETUP', '02_COMPLETE_LOW'."""
    a_name = clean_asset_name(asset)
    return out(a_name, "blend", f"{a_name}_{tag}.blend")
