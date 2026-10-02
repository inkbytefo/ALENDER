"""
Texture set generator for PROP_AK_Rifle (host python: numpy + Pillow, no Blender).
    python projects/PROP_AK_Rifle/texgen.py [SetName ...]

Turns the AI-made albedo images in projects/PROP_AK_Rifle/mat/ into complete PBR sets in the shared
library, named like the downloaded ambientCG sets so workbench.pbrlib finds them:
    downloaded_resources/materials/AK_<Name>_1K-PNG/AK_<Name>_1K-PNG_{Color,Roughness,Metalness,
                                                    NormalGL,NormalDX,AmbientOcclusion,Displacement}.png
and the three wear masks as AK_WearMasks_1K-PNG/AK_WearMasks_{Scratches,Chips,Grunge}.png.

Map conventions (Blender Principled BSDF / glTF):
    Roughness     0 = black = mirror smooth      1 = white = fully rough
    Metalness     0 = black = dielectric         1 = white = bare metal
    Displacement  0 = black = low                1 = white = high
    AO            0 = black = occluded           1 = white = open
    NormalGL      +Y (green) up, as Blender and glTF expect; NormalDX = green channel inverted
    Color         sRGB; every other map is linear (Non-Color)

What is REAL and what is DERIVED:
    Color        the AI albedo, made seamless (10 % edge cross-fade, contrast preserved), 1024 px
    Displacement DERIVED: high-passed luminance of the albedo
    NormalGL     DERIVED from the height map (central differences on the periodic image)
    Roughness    DERIVED: base value + luminance-driven variation (numbers per material in SPECS)
    Metalness    constant, or DERIVED from bright paint chips (EnamelBlack: bare steel shows through)
    AO           DERIVED: cavities of the height map
Luminance-derived relief is an approximation, so normal strengths are kept low.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mat")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "downloaded_resources", "materials"))
SIZE = 1024                 # sources are 1254 px: the nearest power of two without inventing detail
FADE = 0.10                 # fraction of the image cross-faded to make it tile

# rough = (base, amplitude, sign): sign +1 brighter albedo = rougher, -1 darker = rougher
SPECS = {
    # lacquered laminate: the lacquer is the clear coat of the master material, this is the wood under it
    "WoodLaminateA": dict(src="Kızıl Sedir Ahşap Doku", metal=0.0, rough=(0.42, 0.10, -1), height=+1, normal=0.35,
                          ao=0.25),
    "WoodLaminateB": dict(src="Kızıl Tonlarda Ahşap Dokusunun Yakın Planı", metal=0.0, rough=(0.42, 0.08, -1),
                          height=+1, normal=0.30, ao=0.25),
    # dark gunmetal: phosphate + black oxide over steel. Source mean sRGB 0.26 = linear 0.055 (a dark metal F0)
    "SteelParkerized": dict(src="Koyu Grafit Metal Dokusu", metal=1.0, rough=(0.50, 0.10, -1), height=+1,
                            normal=0.45, ao=0.30, desat=0.85),
    # black baked enamel on stamped sheet (magazine): bright chips = bare steel -> metalness map
    "EnamelBlack": dict(src="Koyu Çizikli Siyah Metal Doku", metal="chips", rough=(0.40, 0.10, +1), height=-1,
                        normal=0.40, ao=0.30, gain=0.80, desat=0.70),
    "PolymerStipple": dict(src="Koyu Kömür Rengi İnce Granüllü Doku", metal=0.0, rough=(0.62, 0.08, -1), height=+1,
                           normal=1.00, ao=0.55, gain=0.75, desat=0.90),
    "SteelBrushed": dict(src="Yatay Çizgili Fırçalanmış Çelik Doku", metal=1.0, rough=(0.30, 0.10, -1), height=+1,
                         normal=0.50, ao=0.15, flatten=0.08, gain=0.92),
}
MASKS = {"Scratches": "Siyah Beyaz Çizik Grunge Dokusu", "Chips": "Siyah Zeminde Beyaz Grunge Dokusalg",
         "Grunge": "Kesintisiz Gri Grunge Doku"}


# ------------------------------------------------------------------ image I/O (0..1 floats, row 0 = top)
def load(name):
    return np.asarray(Image.open(os.path.join(SRC, name + ".png")).convert("RGB"), dtype=np.float64) / 255.0


def save(arr, path):
    a = np.clip(arr, 0.0, 1.0)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, axis=2)
    Image.fromarray((a * 255.0 + 0.5).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ numpy helpers
def blur(a, sigma):
    """gaussian blur with PERIODIC borders (FFT) - valid on tiling images."""
    if sigma <= 0:
        return a
    h, w = a.shape[:2]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (np.fft.fftfreq(w)[None, :] ** 2 + np.fft.fftfreq(h)[:, None] ** 2))
    if a.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    return np.stack([np.real(np.fft.ifft2(np.fft.fft2(a[..., c]) * g)) for c in range(a.shape[2])], axis=2)


def blur_np(a, sigma):
    """small separable gaussian with edge clamping (for the non-periodic bands in seamless())."""
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = a
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode="edge")
        acc = np.zeros_like(out)
        for i, kv in enumerate(k):
            sl = [slice(None)] * out.ndim
            sl[axis] = slice(i, i + out.shape[axis])
            acc += kv * p[tuple(sl)]
        out = acc
    return out


def resize(a, n):
    im = Image.fromarray((np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8))
    return np.asarray(im.resize((n, n), Image.LANCZOS), dtype=np.float64) / 255.0


def seamless(a, frac=FADE):
    """make an image tile: cross-fade the first `frac` of each axis with the wrapped end, then crop.
    The detail (image - local mean) is renormalised so the faded band does not go flat."""
    for axis in (0, 1):
        a = np.moveaxis(a, axis, 0)
        n = a.shape[0]
        w = max(2, int(n * frac))
        t = np.linspace(0.0, 1.0, w)
        t = (t * t * (3 - 2 * t))[:, None, None]
        head, tail = a[:w], a[n - w:]
        mh, mt = blur_np(head, 6.0), blur_np(tail, 6.0)
        band = t * mh + (1 - t) * mt + (t * (head - mh) + (1 - t) * (tail - mt)) / np.sqrt(t * t + (1 - t) * (1 - t))
        a = np.moveaxis(np.concatenate([band, a[w:n - w]], axis=0), 0, axis)
    return a


def luminance(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def seam_ratio(a):
    """edge-to-edge difference relative to the normal neighbour difference (1.0 = perfectly seamless)."""
    lr = np.abs(a[:, 0] - a[:, -1]).mean() / max(1e-9, np.abs(a[:, 1:] - a[:, :-1]).mean())
    tb = np.abs(a[0] - a[-1]).mean() / max(1e-9, np.abs(a[1:] - a[:-1]).mean())
    return round(float(lr), 2), round(float(tb), 2)


def height_from(color, sign):
    lum = luminance(color)
    hp = blur(lum - blur(lum, 0.06 * lum.shape[0]), 0.7)       # drop the lighting / stain low frequencies
    return np.clip(0.5 + 0.5 * sign * hp / max(1e-6, 3.0 * hp.std()), 0.0, 1.0)


def normal_from(height, strength):
    """OpenGL tangent normal. Image rows run DOWN here, so +Y (up) is -row."""
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
    gy = (np.roll(height, 1, 0) - np.roll(height, -1, 0)) * 0.5
    n = np.stack([-gx * strength * 6.0, -gy * strength * 6.0, np.ones_like(height)], axis=2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def ao_from(height, strength):
    cav = blur(height, 5.0) - height                            # > 0 inside pits
    return np.clip(1.0 - strength * np.clip(cav * 6.0, 0.0, 1.0), 0.0, 1.0)


# ------------------------------------------------------------------ main
def build(name, sp):
    tag = f"AK_{name}_1K-PNG"
    d = os.path.join(OUT, tag)
    os.makedirs(d, exist_ok=True)

    def path(kind):
        return os.path.join(d, f"{tag}_{kind}.png")
    raw = load(sp["src"])
    before = seam_ratio(raw)
    col = resize(seamless(raw), SIZE)
    after = seam_ratio(col)
    if "flatten" in sp:                                         # remove lighting baked into the albedo
        col = np.clip(col - blur(col, sp["flatten"] * SIZE) + col.reshape(-1, 3).mean(0), 0.0, 1.0)
    lum = luminance(col)
    z = np.clip((lum - lum.mean()) / max(1e-6, 3.0 * lum.std()), -1.0, 1.0)
    height = height_from(col, sp["height"])
    base, amp, sgn = sp["rough"]
    rough = np.clip(base + amp * sgn * z, 0.02, 1.0)
    albedo = col
    if "desat" in sp:
        albedo = lum[..., None] * sp["desat"] + albedo * (1 - sp["desat"])
    if "gain" in sp:
        albedo = albedo * sp["gain"]
    if sp["metal"] == "chips":                                  # bright flakes = bare steel under the paint
        hi = lum - blur(lum, 12.0)
        metal = np.clip((hi - 3.0 * hi.std()) / max(1e-6, 2.0 * hi.std()), 0.0, 1.0)
        metal = blur(metal, 0.6)
        rough = np.clip(rough * (1 - metal) + 0.34 * metal, 0.02, 1.0)
        albedo = albedo * (1 - metal[..., None]) + np.array([0.56, 0.57, 0.58]) * metal[..., None]
    else:
        metal = np.full((SIZE, SIZE), float(sp["metal"]))
    nrm = normal_from(height, sp["normal"])
    ndx = nrm.copy()
    ndx[..., 1] = 1.0 - ndx[..., 1]
    save(albedo, path("Color"))
    save(rough, path("Roughness"))
    save(metal, path("Metalness"))
    save(nrm, path("NormalGL"))
    save(ndx, path("NormalDX"))
    save(ao_from(height, sp["ao"]), path("AmbientOcclusion"))
    save(height, path("Displacement"))
    Image.fromarray((np.clip(albedo, 0, 1) * 255).astype(np.uint8)).resize((256, 256)).save(
        os.path.join(d, f"AK_{name}.png"))                        # preview thumbnail, like the downloaded sets
    info = dict(set=tag, source=sp["src"] + ".png", seam_before=before, seam_after=after,
                metal_mean=round(float(metal.mean()), 3), roughness_mean=round(float(rough.mean()), 3),
                roughness_range=[round(float(rough.min()), 3), round(float(rough.max()), 3)],
                albedo_mean_srgb=[round(float(v), 3) for v in albedo.reshape(-1, 3).mean(0)],
                normal_mean=[round(float(v), 3) for v in nrm.reshape(-1, 3).mean(0)])
    print("[TEXGEN]", json.dumps(info, ensure_ascii=False))
    return info


def build_masks():
    d = os.path.join(OUT, "AK_WearMasks_1K-PNG")
    os.makedirs(d, exist_ok=True)
    out = []
    for kind, src in MASKS.items():
        raw = load(src)
        m = luminance(resize(seamless(raw), SIZE))
        lo, hi = np.percentile(m, 2), np.percentile(m, 99.5)
        m = np.clip((m - lo) / max(1e-6, hi - lo), 0.0, 1.0)     # full 0..1 range: 0 = untouched, 1 = worn
        save(m, os.path.join(d, f"AK_WearMasks_{kind}.png"))
        info = dict(mask=kind, source=src + ".png", seam_before=seam_ratio(raw), seam_after=seam_ratio(m[..., None]),
                    coverage=round(float((m > 0.5).mean()), 3), mean=round(float(m.mean()), 3))
        print("[TEXGEN]", json.dumps(info, ensure_ascii=False))
        out.append(info)
    return out


if __name__ == "__main__":
    only = sys.argv[1:]
    report = [build(n, sp) for n, sp in SPECS.items() if not only or n in only]
    if not only or "masks" in only:
        report += build_masks()
    with open(os.path.join(OUT, "AK_texgen_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print("[TEXGEN] sets:", len(report))
