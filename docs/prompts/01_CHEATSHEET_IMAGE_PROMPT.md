# 01 — Cheatsheet image prompt (for image-generation AIs)

Attach the real photo(s). Fill the `[...]` fields. Use **A** for one sheet, or better **B + C (+ D)**
as separate generations (image models keep alignment and scale much better on focused sheets).

Why these panels: the modelling agent measures proportions from the real photo, but a side photo
cannot show **width, cross-sections, hidden sides and part boundaries**. The sheet must supply
exactly that, drawn orthographically, aligned and at one scale.

---
## A — All-in-one modelling cheatsheet

```text
Create a professional 3D-modelling reference sheet ("cheatsheet") of the EXACT [OBJECT TYPE]
shown in the attached photo: [SHORT DESCRIPTION, e.g. "custom Honda inline-4 street bike,
red/black tank, black frame, stainless 4-into-1 exhaust"].

FIDELITY RULES (most important):
- Reproduce THIS specific object, not a generic one. Keep every proportion, shape, part and colour
  of the photo. Do not redesign, beautify, modernise or add parts that are not visible.
- Hidden areas: infer conservatively and mark them with a dashed outline and the word "ASSUMED".
- Keep the same side orientation as the photo in the side view ([FRONT FACES RIGHT/LEFT]).

LAYOUT: clean landscape sheet, 16:9, light neutral grey background, thin dark panel borders,
numbered panel titles in bold sans-serif, legible labels, no watermark, no perspective in
orthographic panels, no depth-of-field, no dramatic lighting.

PANELS:
1. REFERENCE — the original photo, unchanged.
2. PRIMITIVE BLOCKOUT (side view) — the object rebuilt from simple primitives (boxes, cylinders,
   wedges, tubes), each major group in a flat distinct colour with a colour legend
   ([LIST GROUPS, e.g. body/tank, seat/tail, frame, engine, wheels, exhaust, suspension, other]).
3. ORTHOGRAPHIC VIEWS — LEFT, RIGHT, FRONT, REAR, TOP, all TRUE orthographic, neutral grey clay,
   SAME SCALE, aligned on a common ground line (front/rear views aligned in height with the side
   views, top view aligned in length with the side view). Thin horizontal guide lines across views
   at key heights ([e.g. axle, seat, tank top, bar height]).
4. DIMENSIONS — side view with dimension lines: overall length, overall height, [KEY DIMENSIONS,
   e.g. wheelbase, seat height, ground clearance, wheel diameter]; front view with overall width and
   [KEY WIDTHS]. Include a scale bar in metres and a 10 cm grid behind the side view.
   Known real size to respect: [e.g. "front tyre 120/70-17, rear 180/55-17", "door 2.1 m", "person 1.75 m"].
5. CROSS-SECTIONS — [4-6] section cuts through the main body at marked stations on the side view
   (e.g. S1…S6), each drawn as a flat 2D outline showing true width and height.
6. COMPONENT BREAKDOWN — exploded view: every major component separated along its assembly axis,
   same style, short labels.
7. DETAIL CLOSE-UPS — [4-6] close-ups of details that define the character
   ([e.g. tank edge, headlight bracket, swingarm, shock mount, exhaust joint, brake]).
8. WIREFRAME / TOPOLOGY REFERENCE — clean quad-dominant wireframe of the side view.
9. MATERIALS — swatches with names: [e.g. gloss red paint, satin black, raw steel, brushed
   stainless, rubber, black anodised aluminium, clear glass].
10. MODELLING NOTES — 8-10 short numbered notes: construction order, symmetry, which parts are
   separate meshes, where edges are sharp vs soft, what is assumed.

STYLE: technical, precise, industrial-design presentation board; consistent line weights;
all views of the same object at the same scale; text in English.
```

---
## B — Orthographic sheet only (most useful for accuracy)

```text
Using the attached photo, draw the EXACT same [OBJECT] as a strict orthographic drawing set
(no perspective): SIDE ([FRONT FACING RIGHT/LEFT], matching the photo), FRONT, REAR, TOP.
All views: same scale, neutral grey clay shading with thin dark outlines, white background,
aligned on one ground line; front/rear views level with the side view; top view directly above
the side view with matching length. Horizontal guide lines at [KEY HEIGHTS]. Vertical guide
lines at [KEY STATIONS]. 10 cm grid, scale bar in metres, overall length/width/height dimension
lines. Known size: [REAL DIMENSION]. Do not change any proportion, do not add parts; hidden or
uncertain regions dashed and labelled "ASSUMED".
```

## C — Width & cross-section sheet (answers "how wide is it?")

```text
For the EXACT [OBJECT] in the attached photo, create a technical sheet with:
(1) a side view with [6-8] numbered vertical section lines through [MAIN VOLUMES, e.g. tank,
seat, engine, tail]; (2) for each section, the true cross-section outline (width × height) drawn
flat, same scale, with width values; (3) a top view showing the plan outline and widths of
[e.g. handlebars, tank, seat, engine, tyres, footpegs]; (4) a front view with width hierarchy.
Neutral grey technical style, white background, metres, scale bar, legible labels, no redesign.
```

## D — Detail close-ups sheet

```text
From the attached photo of the [OBJECT], create a grid of [6-9] close-up orthographic studies of:
[LIST DETAILS]. For each: side and front mini-views, simple shading, part name, approximate size
in millimetres, material name. Faithful to the photo; label assumptions "ASSUMED".
```

---
## Category panel swaps (replace panel 2/4/5/7 content)

| Category | Groups for blockout legend | Key dimensions | Sections / details |
|----------|---------------------------|----------------|--------------------|
| Motorcycle | tank, seat/tail, frame, engine, wheels, exhaust, suspension, controls | length, height, wheelbase, seat height, tyre sizes, rake | sections through tank/seat/engine; details: tank edge, headlight, swingarm, shock, exhaust joint, brake |
| Car | body shell, greenhouse/glass, wheels, lights, bumpers, trim | L/W/H, wheelbase, track, ground clearance, tyre size | 6 body sections, plan outline, arch shapes, lamp close-ups |
| Building | walls, roof, openings, stairs, trim, ground | storey height, total height, footprint, door/window sizes, roof pitch | floor plan, elevation of each facade, wall section, window/door details |
| Character | head, torso, arms, legs, hands, feet, clothing, hair | height, head height, shoulder/hip width, joint heights | turnaround front/side/back in T-pose, head front/side, hand, foot |
| Prop | body, handles, lids, hinges, fasteners | L/W/H | profile of turned parts, section of hollow parts, mechanism close-ups |

Tips: if the generator mangles text, drop text and keep the grid + scale bar; if views drift,
generate B alone first. Always save the result as `projects/<ASSET>/ref/MODELING_CHEATSHEET.png`.
