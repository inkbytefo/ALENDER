# 03 — Prompt packs (fill-in, per category + iteration)

Each pack goes AFTER the master prompt (02) or alone when the agent knows the repo.

## A. Car
```text
Project VEH_[Make_Model] (vehicle/car). Attached: side photo [+ front/rear/top]. Known: tyre
[205/55R16], length ≈ [4.6] m. Measure wheel centres, roof line, belt line, sill, bonnet/boot lines,
A/B/C pillars, arch arcs, bumper profiles, lamp outlines. Body shell as a loft from the side
silhouette + width tables per station (mirror X), greenhouse and glass separate, wheels pivot on
axles, doors hinged. Preserve: [roof curve, DLO shape, grille, lamps]. Critical pairs: tyre↔body,
glass↔frames. Budget HIGH 40k–80k, ≤ 8 materials. Deliver per docs/01.
```

## B. Motorcycle
```text
Project VEH_[Model] (vehicle/motorcycle). Attached: side photo + cheatsheet. Known tyres
[120/70-17, 180/55-17]. Check for paddock-stand pitch. Measure axles, pivot, fork line, top clamp,
tank/seat/tail polylines, engine polygons, exhaust centreline, headlight. Follow
docs/case_studies/VEH_Gemini_Motorcycle.md as the reference implementation (reuse its parts.py
patterns). Preserve: [tank shape, tail, exhaust routing]. Budget HIGH 40k–100k.
```

## C. Building / architecture
```text
Project ARCH_[Name] (architecture, [single building | modular kit]). Attached: facade photo(s)
[+ plan sketch]. Known: door height 2.1 m [or storey 3.0 m]. Measure storey lines, opening grid
(sills, heads, jambs), roof pitch and overhang, setbacks. Walls 0.3 m exterior with real openings
(booleans applied or built around openings), roof separate, windows = frame + glass, stairs to
code (rise 0.17–0.19, run 0.26–0.30). Modular kit: 1 m grid, shared pivot rule, edges on grid ±1 mm.
Repeating brick/tile = texture, not geometry. Budget [15k–60k]. Deliver per docs/01.
```

## D. Character
```text
Project CHR_[Name] (character). Attached: front + side reference [or turnaround sheet]. Height
[1.75] m, style [realistic_game | stylized]. S1: joint graph scaled to height →
rig.skin_body blockout, gate R01 on front/side silhouette & joint heights. S2/S3: refined
body/head/hands, clothing as separate meshes, humanoid armature (rig.HUMANOID_BONES), auto weights,
4 test poses rendered (arm up, knee bent, crouch, head turn). T-pose, facing −Y, origin between
feet. Budget 15k–40k, ≤ 6 materials. Faces stylised unless a base mesh is provided.
```

## E. Prop
```text
Project PROP_[Name] (prop). Attached: photo(s). Known size: [..]. Turned parts via lathe profile,
flat parts via photo-outline plates, hollow parts with real wall thickness. Origin bottom-centre
[or grip point]. Budget [0.5k–10k], ≤ 4 materials. Deliver per docs/01 (single stage allowed for
very simple props, but still overlay-check).
```

## F. Correction pass (paste with a screenshot or overlay)
```text
Correction pass on [ASSET]. Render the reference camera (clay, transparent) and run
`python wb.py compare [ASSET] <render>`. List the 5 largest mismatches with numbers (px or mm)
ranked by visual impact (proportion > silhouette > placement > curvature > thickness > detail).
Fix them in landmarks.py / parts.py only (never hand-edit geometry), rebuild, re-compare, and show
before/after. Also: [SPECIFIC ISSUE I SEE, e.g. "tail is too thick", "roof pitch too flat"].
```

## G. Continue / resume in a new chat
```text
Continue project [ASSET] in this repo. Read AGENTS.md, docs/09_LESSONS_LEARNED.md,
projects/[ASSET]/project.md and report.json, look at output/[ASSET]/renders/ and the latest
work/ overlays, then tell me the current stage, open issues and your next 3 actions before acting.
```

## H. Animation / video
```text
For [ASSET], create [8 s product turntable at 1920×1080 / wheel spin loop / door open clip /
walk cycle / camera fly-through]. Follow docs/07: pivots correct first, 30 fps, named actions,
linear for mechanical motion, loops end on the start pose. Preview MP4 with Workbench, final with
EEVEE + studio lights, save to output/[ASSET]/video/. Export GLB with animations if requested.
```

## I. New reference → cheatsheet in one go (for the user)
Use `01_CHEATSHEET_IMAGE_PROMPT.md` variant B first (orthographic), then C (widths/sections).
