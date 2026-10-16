# 09 — Lessons learned

Format: **what happened → why → rule**, max 3-4 lines. Numbers are permanent (code and docs cite
them); append new lessons at the bottom with the next free number.
Status tag: **[CODE: where]** the fix lives in the library (nothing to remember) ·
**[CHECK: id]** a gate catches it · **[JUDGEMENT]** still needs the agent's attention.
A lesson should end as CODE or CHECK whenever possible (docs/05, workbench/).

| Category | Lessons | Read when |
|----------|---------|-----------|
| Reference & measurement | 2 3 4 5 6 15 20 30 31 32 33 34 35 51 52 | S0, any R01/R02 failure |
| Geometry & topology | 7 8 10 11 12 18 19 24 37 38 50 | S1-S3 builders |
| Validation & process | 1 9 14 16 26 39 | always skim |
| Rendering & presentation | 13 21 22 27 | review renders, S5 |
| Assets, materials, game | 23 25 28 29 36 40 | PBR, imports, S4 |

---

1. **v1 of the motorcycle was a generic café racer** (bulbous tank, invented shapes) and passed
   its own checks. → Checks were technical only, nothing compared it to the photo.
   → *Rule: the reference silhouette is a BLOCKER gate.* **[CHECK: R01/R02]**

2. **Measuring from the full photo is too coarse.** → 1 px there = 2.5 mm; edges blur.
   → *Rule: zoom-crop 3–4× with a labelled grid (`wb.py crop`) — or better, measure (33).* **[JUDGEMENT]**

3. **Store proportions as pixels, not metres.** Pixel landmarks + one RefMap made every later fix a
   one-number change and let later stages inherit earlier ones exactly.
   → *Rule: all silhouettes in `landmarks.py` as px; metres only via `REF.P()`.* **[JUDGEMENT]**

4. **The photo showed the RIGHT side, not the left.** Front on image right = right side.
   → *Rule: decide the side explicitly and write it in the landmarks docstring.* **[JUDGEMENT]**

5. **Rear wheel on a paddock stand → photo pitched 2°.** Unnoticed, every part tilts.
   → *Rule: check known-level points; remove tilt with `pitch_from_two_points`.* **[JUDGEMENT]**

6. **Scale from tyre sizes cross-checked by two independent dimensions** gave confidence to trust
   the photo over the AI cheatsheet. → *Rule: one scale source + two cross-checks, recorded.* **[JUDGEMENT]**

7. **Subdivision on extruded plates made engine blocks and panels vanish.** → Subsurf shrinks flat
   n-gon prisms. → *Rule: hard-surface = bevel + weighted normal only.* **[CHECK: H01 — builders tag
   `wb_builder`, plates/boxes/extrusions with a Subdivision modifier fail]**

8. **Intersection check found 5 real construction errors** the eye missed (gearbox through pivot
   plates, intakes through rails …). → *Rule: CRITICAL_PAIRS per project.* **[CHECK: X01, every stage]**

9. **False intersections exploded after moving origins.** → `BVHTree.FromObject` is local-space.
   **[CODE: validate.intersections builds world-space BVHs]**

10. **Face-centre material assignment stair-steps a paint line.** → *Rule: make the boundary an
    edge loop (boundary-aware ring sampling) + crease + material index.* **[JUDGEMENT]**

11. **Subsurf L2 on dense lofts blew the budget (114k tris).** → subsurf viewport/export L1, render
    L2. **[CHECK: U08 per stage budget from tables.BUDGETS; `top_tris` in report.json]**

12. **Fins barely read** when they only overhung the block by 4 px. → *Rule: repeated details need
    contrast — inset the core so fins stand proud.* **[JUDGEMENT]**

13. **Perspective review cams framed too wide.** **[CODE: cameras.rig_from_bounds, presentation.hero_cameras]**

14. **Old outputs next to new ones confuse reviewers.** **[CODE: the pipeline wipes work/s<N>/ before
    each stage; archive other stale files by hand]**

15. **Cheatsheet ≠ truth.** The AI sheet had plausible but wrong details. → *Rule: photo wins;
    cheatsheet is for decomposition and naming.* **[JUDGEMENT]**

16. **Idempotent builders made iteration cheap** (whole stages in seconds). → *Rule: never
    hand-edit geometry in the GUI; change code/landmarks and rebuild.* **[CHECK: stale-input hash in
    `wb.py gate` — a stage built from older inputs cannot PASS]**

17. **Top-down references need calibrated camera translation and (0,0,180°) rotation.** Camera
    local −Z looks down, local +Y → world −Y (nose). Off-centre framing → solve camera XY without
    tilting the asset. **[CODE: cameras.reference_camera view="TOP"]**

18. **Boolean cutters created empty material slots** (fails U07). **[CODE: mods.boolean gives the
    cutter the target's material and cleans slots after apply]**

19. **Mechanical assemblies inside wheel rims produce false intersections if paired broadly.**
    → *Rule: pair `WHEEL_Tire_`, not `WHEEL_`, against moving parts.* **[JUDGEMENT]**

20. **Colour segmentation of the body edge failed on the shaded side** (dark-red flank, wet floor
    reflections). → *Rule: use `wb.py mask` only on plain backgrounds and LOOK at the overlay;
    otherwise measure lit edges on gamma-brightened crops.* **[JUDGEMENT]**

21. **First studio render was blown out.** **[CODE: workbench.bl.presentation (size-scaled lights,
    visible_camera False)]**

22. **PBR preview balls showed staircase seams** (bmesh UV sphere). → *Rule: test meshes need clean
    UVs and an integer number of texture repeats.* **[JUDGEMENT]**

23. **Imported FBX parts landed at wrong places** (un-parenting, stale bound_box). **[CODE:
    workbench.bl.assets]**

24. **CAD-style FBX (2.5 M tris) would not decimate.** **[CODE: assets.decimate(cad=True)]**

25. **Mean texture colour looked "wrong"** — sRGB pixels vs linear `diffuse_color`. → *Rule:
    linearise sampled colours before using them as material values.* **[JUDGEMENT]**

26. **AK overlay came out 20 % squashed** — review renders defaulted to 1080x720 on a 1440x720
    photo. **[CODE: reference_camera stores cam["wb_image_size"]; render.workbench(res=None) uses it]**

27. **Hand-held prop sank through the presentation floor.** **[CODE: presentation.studio floor at
    min(0, asset min Z)]**

28. **`mesh.box_uv` wrapped UVs with `% 1`**, faces crossing a wrap stretched across the texture.
    **[CODE: box_uv is continuous now; bakes use the S2 atlas from uv.atlas (UV_Bake)]**

29. **Studying a downloaded model with an incompatible licence**: inspect read-only for facts,
    never import, trace or bake from it; record it in project.md. **[JUDGEMENT]**

30. *(was a second "17")* **The AI cheatsheet drew the TT92 car reversed.** → *Rule: decide the
    front from function (steering wheel ahead of seat, exhausts), never from nose shape.* **[JUDGEMENT]**

31. *(was a second "18")* **Top-view-only reference (TT92)**: heights estimated. → *Rule: ortho top
    reference camera; list every height as UNCERTAIN in the report.* **[JUDGEMENT]**

32. *(was a second "19")* **Oblique-photo camera fit with estimated anchors was degenerate** (2
    points of known height → 15 mm lens, 17 px error). → *Rule: fit a camera only with ≥ 4 anchors
    whose 3D positions are known independently of the model.* **[JUDGEMENT]**

33. **Eye-read landmarks were off by 3–33 px on the AK** (handguard bottom on the lacquer highlight
    3–8 px high, magazine spine arc 19 px off, floorplate end 33 px, stock belly 4–7 px) although
    the old model "passed" by eye. Found by R02 on the first pipeline run. → *Rule: measure edges
    (`wb.py mask` + `wb.py profile`, 50 % rule), fit arcs by least squares, keep eye-read values
    only where no edge is measurable and say so in project.md.* **[CHECK: R02; CODE: profile/mask]**

34. **Photo mask thresholds**: a global near-white threshold (235) swallowed 2–5 px of haze/shadow
    (R02 biased "model too small"); a global 50 % threshold (150) dropped lit grey steel. → the edge
    band is re-decided with a LOCAL 50 % rule (mean of neighbouring object and background tones);
    chrome glare that reads as background is filled with `--fill U,V`. **[CODE: imgtools.photo_mask]**

35. **Adjacent landmark polygons never meet exactly** → 1–2 px slivers in the union became fake
    inner edges (boundary p95 31 px on a correct model). **[CODE: silhouette.rasterize(close_px=3)]**

36. **Bake: touching parts steal each other's rays** (carrier inside the receiver, levers on walls)
    → inverted normals on contact faces. Hidden in the assembly, so harmless — but visible faces
    must be checked. → *Rule: compare work/s4 LOD0 and S3 renders; separate or bake-isolate a part if
    a visible face breaks.* **[JUDGEMENT]**

37. **A builder bug survived a "PASS" model**: the AK front-sight block used `min()` instead of the
    outline below the ear base — the block under the barrel was missing, the hood was solid. Humans
    had looked at the overlay; R01/R02 flagged it (red wedge) on the first run. **[CHECK: R01/R02]**

38. **Bevel on short outline edges / thin plates collapses to zero-area faces** (grip corners, a
    0.3 mm lug). → *Rule: simplify outlines (`silhouette.simplify`, ≥ 1 px tolerance) and keep plates
    ≥ 2 px thick where they get a bevel.* **[CHECK: U16 — BLOCKER on S2/S4, WARN on the S3 bake source]**

39. **Stage drift on thin axes is meaningless**: S1 primitives omit a charging handle → X width
    +65 %. **[CODE: D02 compares only axes ≥ 25 % of the longest]**

40. **Bake cost**: five 2048 px Cycles bakes of a 18k-tri source took ~4.7 min. → *Rule: iterate
    S1–S3 with `--until 3`, bake once at the end; `--no-bake` for quick S4 structure checks.* **[JUDGEMENT]**

41. **Three-quarter photo montage cannot use a side-plane RefMap as calibrated truth.**
    SIDE reference_camera fixes azimuth at +/-X; wheel-centre slope includes perspective.
    → Separate source views and calibrate perspective before mapping pixel landmarks into 3D;
    never replace the photographic R02 reference with an AI orthographic drawing. **[JUDGEMENT]**

42. **A factory blueprint can anchor scale without proving a custom car's width/height.**
    Hakosuka drawing wheelbase gives 172.763px/m; drawing length differs from factory by 2.27%.
    Keep stock dimensions separate from modified flares, tyres and ride height. **[JUDGEMENT]**
43. **Three-quarter reference cameras need explicit calibrated pose/lens.**
    Added REF.view=CALIBRATED and selectable photographic crop; smoke test projects an
    off-axis camera target with 0.0px error. Project fitting remains a separate task.
    **[CODE: workbench/bl/cameras.py, pipeline.py; templates/smoke_test.py]**
44. **Orthographic drawings need an orthographic reference camera.** The default side reference camera is
    perspective at 7 m: a 2 m wide car is magnified +16 % at the near wheels and the gate measures
    nonsense. `REF.ortho = True` (landmarks.py) makes `cameras.reference_camera` orthographic.
    Also: a silhouette gate counts HOLES in the model (e.g. the empty centre of a tyre/rim lathe, the gap between
    wheel arch and tyre) as boundary error (p95 70 px) - close them with backing discs / an underbody mass.
    Column-wise top/bottom polygons lose cavities (wing/tail notch, receding nose): trace the mask, not the extremes.
    **[CODE: workbench/bl/cameras.py; VEH_Honda_NSX_Widebody]**
45. **VEH_Honda_NSX_Widebody gates against the AI cheatsheet's side drawing, not the photo** (photo is a front 3/4
    perspective, no camera fit made). This is a deliberate exception to lesson 41; it is only acceptable because no
    other side view exists, and the report must say that R02 is NOT photographic proof. **[JUDGEMENT]**

### Refactor check: per-object geometry fingerprint  [STATUS: JUDGEMENT - candidate for `wb.py fingerprint`]
Rewriting a project's build scripts (VEH_TT92_Racing_Car, legacy two-stage -> five stage scripts) must not
move a vertex. Total tris + bbox are too weak to prove that. Dump, before and after, one record per HIGH
object - evaluated vertex count, triangle count, world bbox (4 decimals), material slots, origin - and diff
the two JSON files; 0 differences = identical model. Run it on every derived file too (the cleaned
WORKSPACE blend), since regrouping collections and purging orphans can silently drop objects.

### AI-generated texture inputs: measure before trusting  [STATUS: CODE in projects/VEH_TT92_Racing_Car/texgen.py - candidate for workbench]
AI image tools return "seamless" albedos that are not (edge difference 2-4x the neighbour difference on
structured textures) and "normal maps" that can be a hue-shifted copy of the albedo. Check both with numbers:
seam ratio = mean |edge - opposite edge| / mean |pixel - neighbour| (1.0 = tiles), and for a normal map the
mean colour must be ~(0.5, 0.5, 1.0) AND the picture must not resemble the albedo. Fix seams with an edge
cross-fade that renormalises the detail (plain blending leaves a flat band). Roughness / height / AO derived
from albedo luminance are approximations - say so, and keep normal strength low on smooth paint (0.1-0.2):
at 0.6 a derived normal turned car paint into hammered metal.
Pointiness-based edge wear needs a high threshold (0.62+): thin convex parts are "all edge" and go fully bare.

### Baking a node-group master material for an engine  [STATUS: CODE in projects/VEH_TT92_Racing_Car/stage7_game.py - candidate for workbench.bl.game]
When every material instance shares ONE master node group, bake material inputs by rewiring the group once:
group output <- Emission(<socket feeding Base Color / Roughness / Metallic / Emission>) and bake type EMIT.
One relink serves all instances, metals do not bake black (a DIFFUSE colour pass of a metallic BSDF is black),
and the result is lighting-free. Restore the BSDF link for the NORMAL and AO passes. Triangulate the game mesh
BEFORE baking so the engine's tangents match. Helical / very long thin parts (heat-wrap strands) unwrap into
metre-long UV strips that wreck the atlas scale: drop or simplify them in the game mesh. A clear coat does not
export - fold part of it into the baked roughness and say so.


46. **A downscaled AI sheet and its floor shadow corrupted the DeLorean intake.** Old axle
    landmarks implied a 5.147m car from a 4.213m label; the mask included the entire shadow.
    Preserve the native attachment, verify axle centers on labelled crops, and inspect the mask.
    The user chose drawn side proportions over conflicting labels; R02 therefore proves sheet
    fidelity, not photographic or stock-dimension accuracy. **[JUDGEMENT; reproducible boundary
    analysis in projects/VEH_DeLorean_DMC12/prepare_reference.py]**

47. **A passing side silhouette concealed poor three-dimensional design.** The first DeLorean
    had detached-looking overlays, crude slab bumpers and inconsistent surface flow despite
    96.8% silhouette overlap. After the user changed the brief to an original restomod, a
    continuous curved shell and integrated cabin replaced the silhouette-first construction.
    Inspect clay and specular front/rear/side views before accepting any hero asset; a gate
    measures its specified property, not overall artistic quality. **[JUDGEMENT]**

- **[CODE] A "side photo" can hide 10-16 % perspective** (AK: rifle leaning away from the camera; butt
  16 % longer than the muzzle end, yet every gate passed because gates compare against the same photo).
  Symptoms: scale cross-checks disagree by 5-10 %, parallel real edges converge. Fix: fit
  `refmap.ObliqueRefMap` (yaw + focal) to >= 4 stations of an orthographic source and keep landmarks in px.
- **[JUDGEMENT] Stations only give the in-plane homography; the camera position comes from parallax.**
  Parts that are NOT thickened in the photo are seen square-on, visible end faces give the obliquity
  elsewhere. Then subtract `REF.thickness_px(u, hw)` from silhouette edges that face along the long axis,
  or thick parts are counted twice (R02 "model too large" on one side of every thick part).
- **[JUDGEMENT] Scanned PDFs without a PDF library:** pages are usually embedded JPEGs; a 15-line
  pure-python `/DCTDecode` stream extractor is enough (see ref/pdf_pages of PROP_AK_Rifle).


48. **Watertight boolean wheel cuts are not an editable automotive surface cage.** The
    DeLorean Vision refinement uses explicit circular-arch lower boundaries and ruled quad
    strips, merges redundant nearby stations, and keeps localized boolean recesses on the
    almost planar fascias. Longitudinal natural cubic splines and periodic B-spline cross
    sections improve reflection flow, but polygon geometry is not a CAD Class-A certificate.
    Inspect both wire edges and studio reflections; report aspect-ratio observations rather
    than claiming an all-quad cage. **[CODE: projects/VEH_DeLorean_Vision/parts.py and
    review_topology.py; JUDGEMENT]**

49. **A single atlas can pass gates while adjacent trim contaminates glazing.** A 29.5mm
    selected-to-active cage projected fine rail geometry into the windshield. This project
    tightens the cage to 6mm, uses 4K maps and repacks concave UV islands. The hero retains
    thin-wall transmissive glass; the portable one-material game atlas approximates it with
    opaque tinted glazing. Review S4 close-ups separately; changing the material count would
    violate the current one-material export contract. Merge rigid wheel children before
    baking/export to retain four pivots with five visible game meshes. **[CODE:
    projects/VEH_DeLorean_Vision/production.py; candidate project hooks for a future library API]**

- **[CODE: master] Edge wear from Geometry > Pointiness is per vertex**; on bevelled plates every corner
  is convex, so flat faces flood or show nothing. `Bevel Wear` uses the Cycles Bevel node
  (1 - N.N_bevel, convex only) and is tessellation independent. Chip / scratch / grunge masks are
  optional master inputs (`masks=` in the instance spec).
- **[CODE: master] Grain textures need `projection="CYL_Y"`**: BOX projection turns the grain 90 deg on
  the top / bottom faces of a stock. U along the part, V = atan2 around it, seam on the belly.
- **[JUDGEMENT] A dark finish with Metallic 1 renders as a black hole** in a studio (nothing to
  reflect). Phosphate / parkerized steel is mostly diffuse: Metallic Scale ~0.4 + bare-metal wear.
- **[CODE: pipeline/export] Painted atlases triple the glb** (3 x 6 MB PNG at 2K): keep PNG masters,
  embed JPEG (`GAME image_format="JPEG"`). `materials.ensure` must skip master instances when a later
  stage re-opens the file.

50. **Slanted crowns / diagonal cuts on primitives break S1 silhouettes.** A straight cylinder
    stand-in for the 45° angled plasma saber emitter shroud left a +38 px overshoot at the tip
    (R01/R02 FAIL). → Primitives with large angled faces cannot use a blunt bounding cylinder.
    → *Rule: omit prim= and let the real builder run under S1 profile (ring=8..12) whenever a
    part has prominent planar chamfers or angled lips; this guarantees zero silhouette drift (D01 iou=0.999).*
    **[JUDGEMENT / CODE: projects/PROP_Plasma_Saber/parts.py]**

51. **Open skeletal cages create hollow voids in 2D silhouette renders.** A crystal chamber
    with 3-4 perimeter struts and a narrow inner floating core let transparent background show
    through between the struts and the core (R01/R02 "model too small -15 px").
    → Transparent gaps inside the outer envelope are counted as background by render.silhouette.
    → *Rule: ensure the transparent/sapphire sleeve fills up to the inner face of perimeter
    struts, or orient structural struts to cover silhouette extrema (e.g. 90° and 270° in side view).*
    **[JUDGEMENT: projects/PROP_Plasma_Saber/parts.py]**

52. **Inverted step directions on shaft cooling fins corrupt silhouette matching.** When defining
    landmarks for stepped shafts with radial fins, drawing the polyline step inward instead of outward
    creates localized 15 px boundary errors.
    → *Rule: inspect silhouette diff columns with a 5-line numpy slice probe to locate internal
    voids vs outer boundary discrepancies before adjusting builder geometry.*
    **[JUDGEMENT]**
