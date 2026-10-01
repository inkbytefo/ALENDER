# 09 — Lessons learned

Format: **what happened → why → rule**, max 3-4 lines. Numbers are permanent (code and docs cite
them); append new lessons at the bottom with the next free number.
Status tag: **[CODE: where]** the fix lives in the library (nothing to remember) ·
**[CHECK: id]** a gate catches it · **[JUDGEMENT]** still needs the agent's attention.
A lesson should end as CODE or CHECK whenever possible (docs/05, workbench/).

| Category | Lessons | Read when |
|----------|---------|-----------|
| Reference & measurement | 2 3 4 5 6 15 20 30 31 32 33 34 35 | S0, any R01/R02 failure |
| Geometry & topology | 7 8 10 11 12 18 19 24 37 38 | S1-S3 builders |
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

