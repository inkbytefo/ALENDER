"""
PBR texture-set library (pure python, no bpy): finds texture sets on disk and classifies their maps.

    from workbench import pbrlib
    sets = pbrlib.scan()                         # every set under the library roots
    s = pbrlib.find("Leather009")                # one set (exact name, else unique substring)
    s["maps"]["base_color"], s["maps"]["normal_gl"], ...

Recognised naming (case-insensitive, last token(s) of the file stem):
  ambientCG / Poly Haven : *_Color  *_Roughness  *_Metalness  *_NormalGL  *_NormalDX  *_Displacement
                           *_AmbientOcclusion  *_Opacity  *_Emission   (+ _diff/_rough/_nor_gl/_disp/_arm)
  Substance / Fab exports: *_Base_color *_BaseColor *_Albedo *_Diffuse *_Metallic *_Normal_DirectX
                           *_Normal_OpenGL *_Normal *_Height *_Mixed_AO *_AO *_Emissive
  short suffixes         : *D *M *R *N *S (Diffuse/Metal/Rough/Normal/Specular) when nothing else matches
One folder may hold several sets (e.g. Main_*, Control_*): files are grouped by the stem prefix.

Library roots: $WB_PBR_LIBRARY (os.pathsep separated) + <repo>/library/materials +
<repo>/downloaded_resources/materials (whichever exist). docs/11_ASSETS_AND_PBR.md.
"""
import os
import re

from workbench.paths import ROOT

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".tga", ".webp", ".bmp")

# map kind -> regex on the END of the lower-case stem (longest / most specific first)
_PATTERNS = [
    ("normal_gl", r"(normal[_\-]?gl|normal[_\-]?opengl|nor[_\-]?gl|normalgl)"),
    ("normal_dx", r"(normal[_\-]?dx|normal[_\-]?directx|nor[_\-]?dx|normaldx)"),
    ("ao", r"(ambient[_\-]?occlusion|mixed[_\-]?ao|occlusion|_ao)"),
    ("base_color", r"(base[_\-]?colou?r|albedo|diffuse|diff|colou?r|basecolor)"),
    ("roughness", r"(roughness|rough|rgh|_rg)"),
    ("metallic", r"(metalness|metallic|metal|mtl|_mt)"),
    ("displacement", r"(displacement|height|disp|bump)"),
    ("opacity", r"(opacity|alpha|transparency|mask)"),
    ("emission", r"(emissive|emission|emit)"),
    ("specular", r"(specular|spec)"),
    ("arm", r"(_arm|_orm)"),                       # packed AO / Rough / Metal
    ("normal", r"(normal|nor|nrm|_nr)"),               # unknown handedness -> treated as OpenGL
]
_SHORT = {"d": "base_color", "m": "metallic", "r": "roughness", "n": "normal", "s": "specular"}
_RES = re.compile(r"(\d+k)", re.I)


def library_roots():
    roots = [p for p in os.environ.get("WB_PBR_LIBRARY", "").split(os.pathsep) if p]
    roots += [os.path.join(ROOT, "library", "materials"), os.path.join(ROOT, "downloaded_resources", "materials")]
    return [r for r in roots if os.path.isdir(r)]


def library_root():
    r = library_roots()
    return r[0] if r else os.path.join(ROOT, "downloaded_resources", "materials")


def classify(stem):
    """(kind, prefix) for an image stem, or (None, stem)."""
    s = stem.lower()
    for kind, pat in _PATTERNS:
        m = re.search(r"[_\-\s\.]?" + pat + r"(@.*)?$", s)
        if m:
            return kind, stem[:m.start()].rstrip("_- .")
    if len(stem) > 2 and stem[-1] in "DMRNS" and stem[-2].islower():     # 'scooter_bodyD' style
        return _SHORT[stem[-1].lower()], stem[:-1]
    return None, stem


def _category(name):
    m = re.match(r"([A-Za-z]+)", name)
    return m.group(1) if m else "misc"


def scan(roots=None):
    """list of texture sets: dict(name, dir, category, resolution, maps{kind: path})."""
    if isinstance(roots, str):
        roots = [roots]
    sets = {}
    for root in roots or library_roots():
        for d, _, files in os.walk(root):
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext.lower() not in IMAGE_EXT:
                    continue
                kind, prefix = classify(stem)
                if kind is None:
                    continue
                key = (d, prefix.lower())
                s = sets.setdefault(key, dict(name=prefix or os.path.basename(d), dir=d, maps={}))
                s["maps"].setdefault(kind, os.path.join(d, f))
    out = []
    for s in sets.values():
        if "base_color" not in s["maps"] and "normal_gl" not in s["maps"] and "normal" not in s["maps"]:
            continue                                   # not a usable material (e.g. lone AO bake)
        name = re.sub(r"[_\-]\d+k[_\-]?(png|jpg|exr)?$", "", s["name"], flags=re.I)
        s["name"] = name
        s["category"] = _category(name)
        r = _RES.search(os.path.basename(s["dir"]) + " " + s["name"])
        s["resolution"] = r.group(1).upper() if r else "?"
        out.append(s)
    return sorted(out, key=lambda s: s["name"].lower())


def find(name, roots=None):
    """set by exact name (case-insensitive), else the unique set containing `name`."""
    sets = scan(roots)
    low = name.lower()
    exact = [s for s in sets if s["name"].lower() == low]
    if exact:
        return exact[0]
    part = [s for s in sets if low in s["name"].lower()]
    if len(part) == 1:
        return part[0]
    raise KeyError(f"PBR set '{name}': {'ambiguous ' + str([s['name'] for s in part]) if part else 'not found'}"
                   f" in {roots or library_roots()}")
