"""
Texture set generator for VEH_TT92_Racing_Car      python wb.py run projects/VEH_TT92_Racing_Car/texgen.py

Turns the AI-made albedo images in material/_source/ into complete PBR sets:
    material/TT92_<Name>_1K-PNG/TT92_<Name>_{Color,Roughness,Metalness,NormalGL,AmbientOcclusion,
                                              Displacement[,Emission]}.png
(names recognised by workbench.pbrlib, docs/11). Runs inside Blender (bpy image I/O + numpy).

What is REAL and what is DERIVED - be honest when judging the result:
  Color        the AI albedo, made seamless (10 % edge cross-fade, contrast preserved), 1024 px
  NormalGL     supplied by the user for SteelBrushed and ExhaustWrap (re-centred + renormalised);
               everywhere else DERIVED from the height map (Sobel on a periodic image)
  Displacement DERIVED: high-passed luminance of the albedo (dark = low unless SPEC says otherwise)
  Roughness    DERIVED: base value + luminance-driven variation, per-material numbers in SPECS
  Metalness    constant per material (0 or 1) - these surfaces are not mixed metal/dielectric
  AO           DERIVED: cavities of the height map
A luminance-derived height is an approximation: it reads paint chips, pores and weave correctly,
but it cannot know real depth. Strengths are therefore kept low (see `normal` in SPECS).
"""
import os
import sys
import json
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "material", "_source")
OUT = os.path.join(HERE, "material")
SIZE = 1024                 # sources are 1254 px: 1024 is the nearest power of two without inventing detail
FADE = 0.10                 # fraction of the image cross-faded to make it tile

# name: dict(src, [normal_src], metal, rough=(base, amplitude, sign), height=sign, normal=strength,
#            ao=strength, [gain], [desat], [color=const], [emission], [flatten=blur fraction])
#   rough sign +1: brighter albedo = rougher, -1: darker = rougher
SPECS = {
    "PaintRed":        dict(src="paint_red_aged", metal=0.0, rough=(0.34, 0.10, +1), height=+1, normal=0.5, ao=0.35),
    "PaintCream":      dict(src="paint_cream_aged", metal=0.0, rough=(0.42, 0.10, -1), height=+1, normal=0.7, ao=0.45),
    "Chrome":          dict(src="chrome_worn_grey", metal=1.0, rough=(0.10, 0.09, +1), height=+1, normal=0.2, ao=0.15,
                            color=(0.86, 0.87, 0.89), color_var=0.03),
    "AluminiumCast":   dict(src="aluminium_cast", metal=1.0, rough=(0.52, 0.12, -1), height=+1, normal=1.4, ao=0.6,
                            gain=1.18, desat=0.6),
    "BlackCoated":     dict(src="black_coated", metal=0.0, rough=(0.55, 0.10, +1), height=+1, normal=1.1, ao=0.5,
                            desat=0.7),
    "StainlessHeat":   dict(src="stainless_heat_tint", metal=1.0, rough=(0.32, 0.14, -1), height=+1, normal=0.6, ao=0.3),
    "ExhaustWrap":     dict(src="exhaust_wrap_jute", normal_src="exhaust_wrap_jute_normal", metal=0.0,
                            rough=(0.90, 0.06, -1), height=+1, normal=1.0, ao=0.8),
    "TyreRubber":      dict(src="tyre_rubber_worn", metal=0.0, rough=(0.84, 0.08, +1), height=+1, normal=1.0, ao=0.5,
                            gain=0.55, desat=0.8),
    "WoodMahogany":    dict(src="wood_mahogany", metal=0.0, rough=(0.34, 0.08, +1), height=+1, normal=0.5, ao=0.3),
    "LensAmber":       dict(src="lens_amber_smoked", metal=0.0, rough=(0.08, 0.05, +1), height=+1, normal=0.15, ao=0.1),
    "CarbonForged":    dict(src="carbon_forged", metal=0.0, rough=(0.28, 0.10, -1), height=+1, normal=0.5, ao=0.3),
    "SteelBrushed":    dict(src="steel_brushed", normal_src="steel_brushed_normal", metal=1.0,
                            rough=(0.36, 0.10, -1), height=+1, normal=1.0, ao=0.2, flatten=0.08),
    "AfterburnerPlasma": dict(src="afterburner_plasma", metal=0.0, rough=(0.5, 0.0, +1), height=+1, normal=0.0,
                              ao=0.0, emission=True, gain=0.06),
}


# ------------------------------------------------------------------ image I/O (bpy, raw 0..1 values)
def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[..., :3].astype(np.float64)        # row 0 = image bottom


def save(arr, path):
    a = np.clip(arr, 0.0, 1.0)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, axis=2)
    h, w = a.shape[:2]
    img = bpy.data.images.new("texgen_tmp", w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = a
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


# ------------------------------------------------------------------ numpy helpers
def blur(a, sigma):
    """gaussian blur with PERIODIC borders (FFT) - valid on tiling images."""
    if sigma <= 0:
        return a
    h, w = a.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    if a.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    return np.stack([np.real(np.fft.ifft2(np.fft.fft2(a[..., c]) * g)) for c in range(a.shape[2])], axis=2)


def resize(a, n):
    """bilinear resample to n x n (sources are only ~10 % larger, no aliasing risk)."""
    h, w = a.shape[:2]
    ys = (np.arange(n) + 0.5) * h / n - 0.5
    xs = (np.arange(n) + 0.5) * w / n - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 1); y1 = np.clip(y0 + 1, 0, h - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 1); x1 = np.clip(x0 + 1, 0, w - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None, None]
    fx = np.clip(xs - x0, 0, 1)[None, :, None]
    a = a if a.ndim == 3 else a[..., None]
    top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx
    bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
    return top * (1 - fy) + bot * fy


def seamless(a, frac=FADE, keep_contrast=True):
    """make an image tile: cross-fade the first `frac` of each axis with the wrapped end, then crop.
    keep_contrast: the detail (image - local mean) is renormalised so the faded band does not go flat."""
    for axis in (0, 1):
        a = np.moveaxis(a, axis, 0)
        n = a.shape[0]
        w = max(2, int(n * frac))
        t = np.linspace(0.0, 1.0, w)
        t = (t * t * (3 - 2 * t))[:, None, None]
        head, tail = a[:w], a[n - w:]
        if keep_contrast:
            mh = blur_np(head, 6.0)
            mt = blur_np(tail, 6.0)
            mean = t * mh + (1 - t) * mt
            dev = (t * (head - mh) + (1 - t) * (tail - mt)) / np.sqrt(t * t + (1 - t) * (1 - t))
            band = mean + dev
        else:
            band = t * head + (1 - t) * tail
        a = np.concatenate([band, a[w:n - w]], axis=0)
        a = np.moveaxis(a, 0, axis)
    return a


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


def luminance(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def seam_ratio(a):
    """edge-to-edge difference relative to the normal neighbour difference (1.0 = perfectly seamless)."""
    lr = np.abs(a[:, 0] - a[:, -1]).mean() / max(1e-9, np.abs(a[:, 1:] - a[:, :-1]).mean())
    tb = np.abs(a[0] - a[-1]).mean() / max(1e-9, np.abs(a[1:] - a[:-1]).mean())
    return round(float(lr), 2), round(float(tb), 2)


def height_from(color, sign):
    lum = luminance(color)
    hp = lum - blur(lum, 0.06 * lum.shape[0])                  # drop the lighting / stain low frequencies
    hp = blur(hp, 0.7)
    return np.clip(0.5 + 0.5 * sign * hp / max(1e-6, 3.0 * hp.std()), 0.0, 1.0)


def normal_from(height, strength):
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5     # rows go UP -> OpenGL green
    s = strength * 6.0
    n = np.stack([-gx * s, -gy * s, np.ones_like(height)], axis=2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def fix_normal(nmap, strength):
    """supplied normal map -> unit vectors with zero mean tilt (AI maps carry a constant bias)."""
    v = nmap * 2.0 - 1.0
    v[..., 0] -= v[..., 0].mean()
    v[..., 1] -= v[..., 1].mean()
    v[..., 0] *= strength
    v[..., 1] *= strength
    v[..., 2] = np.sqrt(np.clip(1.0 - v[..., 0] ** 2 - v[..., 1] ** 2, 0.05, 1.0))
    v /= np.linalg.norm(v, axis=2, keepdims=True)
    return v * 0.5 + 0.5


def ao_from(height, strength):
    cav = blur(height, 5.0) - height                            # > 0 inside pits
    return np.clip(1.0 - strength * np.clip(cav * 6.0, 0.0, 1.0), 0.0, 1.0)


# ------------------------------------------------------------------ main
def build(name, sp):
    d = os.path.join(OUT, f"TT92_{name}_1K-PNG")
    os.makedirs(d, exist_ok=True)

    def path(kind):
        return os.path.join(d, f"TT92_{name}_{kind}.png")

    raw = load(os.path.join(SRC, sp["src"] + ".png"))
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
    if "normal_src" in sp:
        nraw = load(os.path.join(SRC, sp["normal_src"] + ".png"))
        nrm = fix_normal(resize(seamless(nraw, keep_contrast=False), SIZE), sp["normal"])
        nsrc = "supplied"
    else:
        nrm = normal_from(height, sp["normal"])
        nsrc = "derived"
    ao = ao_from(height, sp["ao"])

    albedo = col
    if "desat" in sp:
        albedo = lum[..., None] * sp["desat"] + albedo * (1 - sp["desat"])
    if "gain" in sp:
        albedo = albedo * sp["gain"]
    if "color" in sp:                                           # metal with a known reflectance colour
        albedo = np.array(sp["color"])[None, None, :] * (1.0 + sp.get("color_var", 0.0) * z[..., None])
    if sp.get("emission"):
        save(col, path("Emission"))
    save(albedo, path("Color"))
    save(rough, path("Roughness"))
    save(np.full((SIZE, SIZE), sp["metal"]), path("Metalness"))
    save(nrm, path("NormalGL"))
    save(ao, path("AmbientOcclusion"))
    save(height, path("Displacement"))
    info = dict(set=f"TT92_{name}", source=sp["src"] + ".png", seam_before=before, seam_after=after,
                normal=nsrc, metallic=sp["metal"], roughness_mean=round(float(rough.mean()), 3),
                roughness_range=[round(float(rough.min()), 3), round(float(rough.max()), 3)],
                albedo_mean=[round(float(v), 3) for v in albedo.reshape(-1, 3).mean(0)])
    print("[TEXGEN]", json.dumps(info))
    return info


only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
report = [build(n, sp) for n, sp in SPECS.items() if not only or n in only]
with open(os.path.join(OUT, "texgen_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print("[TEXGEN] sets:", len(report))
