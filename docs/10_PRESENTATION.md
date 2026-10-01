# 10 — Presentation studio (review, showcase, final renders)

One reusable, professionally lit stage for **every** asset: vehicles, buildings, characters, props.
Use it whenever a model is shown to a human — design review, client presentation, portfolio,
turntable video. It is built by code (`workbench/bl/presentation.py`) and scales itself from the
asset's bounding box, so a 0.3 m bottle and a 30 m building get the same look.

> Review renders for *measuring* (overlays, orthos, Workbench clay) stay in `render.py`/`cameras.py`.
> The presentation studio is for *judging and showing* the finished form. Never use it to hide
> modelling errors — lighting that flatters is not a gate.

## One command
```bash
python wb.py present <ASSET>                                   # studio_dark, Cycles GPU, 6 hero shots + sheet
python wb.py present <ASSET> --style clay --samples 128        # shape review in grey clay
python wb.py present <ASSET> --style studio_light              # bright product shot
python wb.py present <ASSET> --engine EEVEE --shots none --turntable 8   # 8 s 360° MP4
python wb.py present <ASSET> --scale 50 --samples 48           # quick preview (half res)
python wb.py present <ASSET> --shots HERO_FRONT_34,SIDE        # chosen shots only
```
Input: `output/<ASSET>/blend/<ASSET>.blend` (the final model, not modified).
Output: `output/<ASSET>/presentation/<style>_<shot>.png`, `<style>_sheet.png`,
`output/<ASSET>/video/<style>_turntable.mp4`, `output/<ASSET>/blend/<ASSET>_PRESENTATION.blend`
(open it in the GUI to inspect the stage). Only the finished model is shown (S3 DETAIL, or HIGH
in legacy projects); S1/S2/S4 stage collections, collision, guides, reference and temp are hidden.

## What the stage contains
| Element | Design | Why |
|---------|--------|-----|
| `PRES_Cyclorama` | 360° seamless bowl: floor r = 3L → quarter-circle cove r = 1.4L → wall 4L high (L = largest asset dimension). Floor material slightly glossy, wall matte. Floor at z = −0.5 mm. | No horizon line from ANY angle (turntable-safe), soft reflections anchor the object, no z-fighting at contact points. |
| `PRES_Light_KEY` | big softbox front-3/4 high (az −35°, el 42°) | main form-defining light, soft shadow under the object |
| `PRES_Light_TOP` | long overhead light bank along the asset | draws the long highlight along paint / hard surfaces (car-studio look) |
| `PRES_Light_RIM_L / RIM_R` | tall strips behind left/right | separates the silhouette from a dark background |
| `PRES_Light_FILL` | large dim panel on the camera side | opens shadows without flattening |
| `PRES_Light_KICKER` | low front strip | lifts lower bodywork, tyre sidewalls, feet |
| World | dim neutral ambient | keeps blacks clean |
| Colour | AgX view transform + per-style look/exposure | filmic highlight roll-off, no clipped paint |

All lights are area lights, **invisible to the camera** (they still light and reflect), and their
power scales with distance², so exposure is identical for small and large assets.
Everything is prefixed `PRES_`, lives in `09_PRESENTATION`, and is never exported to GLB.

## Styles
| Style | Look | Use for |
|-------|------|---------|
| `studio_dark` (default) | charcoal glossy floor, rim-lit, "car launch" | hero images, vehicles, products with paint/metal |
| `studio_light` | bright grey cyc, soft | catalogue / product shots, light-coloured assets |
| `neutral_grey` | mid grey, low contrast | honest material review |
| `clay` | neutral grey stage + grey clay on the asset | **shape review**: proportions, silhouettes, bevels, surface flow — no material can hide anything |

## Shots (auto-framed)
`HERO_FRONT_34` (70 mm, low 3/4 front) · `HERO_REAR_34` · `SIDE` (105 mm, near-orthographic
profile) · `FRONT` (85 mm) · `TOP_34` (55 mm, high 3/4) · `LOW_DRAMA` (35 mm, near the ground).
Azimuth 0° = front (−Y), +90° = the asset's right side (−X), matching docs/02 axes.
`presentation.frame()` moves each camera along its view axis and sets lens shift from the real
perspective projection of the evaluated vertices, so the object fills the frame with a fixed
margin — no hand-placed cameras, identical framing after every rebuild.

## Engines
- **Cycles** (finals): GPU picked automatically (OptiX > CUDA > HIP > oneAPI > Metal, CPU fallback),
  adaptive sampling, OptiX/OIDN denoise, indirect clamp 8, caustics off. 192–256 samples for
  finals, 48–64 for previews. RTX 3060: ~4 s per 960×540 still at 64 samples.
- **EEVEE** (previews, turntables): raytracing + shadows on, exposure +1 EV (`EEVEE_EV`) to match
  Cycles (EEVEE misses most diffuse bounce inside the dark bowl). Contact shadows are softer —
  judge grounding in Cycles.

## Library use (inside any bpy script)
```python
from workbench.bl import presentation as pres
objs = validate.mesh_objects(scene.objects_in(scene.HIGH_COLLS))
pres.studio(objs, "studio_dark")                       # stage, lights, world, colour management
cams = pres.hero_cameras(objs)                         # or {name: (az, el, lens, margin, (w, h))}
pres.render_stills(cams, paths.out(A, "presentation"), "final_", "CYCLES", 256)
pres.turntable_video(objs, paths.out(A, "video", "turntable.mp4"), seconds=8)
pres.clay_override(objs, False)                        # restore the asset's materials after style 'clay'
```
Custom look: edit `STYLES` / `LIGHTS` / `SHOTS` dicts (copy them in the project if only one asset
needs a variation — keep the library defaults stable).

## Checklist for AI agents (end of every modelling job)
1. Final gate passed (docs/05) — presentation never replaces validation.
2. `python wb.py present <ASSET> --style clay --samples 96` → **look at the sheet**: silhouettes,
   bevel highlights, surface pinches, floating parts (check contact shadows), interpenetrations.
3. `python wb.py present <ASSET>` (studio_dark, finals) → look at the sheet again for material
   problems (flat paint, wrong metalness, black tyres reading grey).
4. Optional: `--engine EEVEE --shots none --turntable 8` for a video.
5. Put the sheet in the final message; mention render engine, samples and time.

## Pitfalls
- A light pointing into the lens appears as a white card → lights are `visible_camera = False`.
- Clay is applied with object-linked material slots on the asset only; the cyclorama keeps its
  grey floor so the clay form reads against it. `clay_override(objs, False)` restores materials.
- Very flat assets (rugs, decals) have small L in Z; the stage uses max(X, Y, Z) so it still works.
- Assets not built with the standard collections: `present.py` falls back to all visible meshes.
