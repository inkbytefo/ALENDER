# 09 — Lessons learned (append new ones at the bottom, keep each to 3 lines)

Format: **what happened → why → rule**.

1. **v1 of the motorcycle was a generic café racer** (bulbous tank, invented shapes) and passed
   its own checks. → Checks were technical only (UVs, scale), nothing compared it to the photo.
   → *Rule: the reference overlay is a BLOCKER gate. No overlay, no "done".*

2. **Measuring from the full photo is too coarse.** → 1 px there = 2.5 mm; edges blur.
   → *Rule: zoom-crop every region 3–4× with a labelled grid (`wb.py crop`) before writing landmarks.*

3. **Store proportions as pixels, not metres.** Pixel landmarks + one RefMap made every later fix a
   one-number change and let Stage 2 inherit Stage 1 exactly (identical tri counts after refactor).
   → *Rule: all silhouettes in `landmarks.py` as px; metres only via `REF.P()`.*

4. **The photo showed the RIGHT side, not the left.** Front on image right = right side.
   → *Rule: decide the side explicitly and write it in the landmarks docstring.*

5. **Rear wheel on a paddock stand → photo pitched 2°.** Unnoticed, every part tilts.
   → *Rule: check whether known-level points are level; remove tilt with `pitch_from_two_points`.*

6. **Scale from tyre sizes cross-checked by two independent dimensions** (length, height) caught
   no error but gave confidence to trust the photo over the AI cheatsheet.
   → *Rule: one scale source + two cross-checks, recorded.*

7. **Subdivision on extruded plates made engine blocks and panels vanish** in Stage 2.
   → Subsurf shrinks flat n-gon prisms. → *Rule: hard-surface = bevel + weighted normal only;
   subsurf only on lofts (`mods.finish_hard` / `finish_organic`).*

8. **Intersection check found 5 real construction errors** the eye missed (gearbox through pivot
   plates, intakes through rails, downtube through header, pivot shaft through gearbox).
   → *Rule: define CRITICAL_PAIRS per project; 0 hits is a Stage 1 gate.*

9. **False intersections exploded after moving origins** in Stage 2. → `BVHTree.FromObject` is
   local-space. → *Rule: build BVHs from world-space vertices (library does).*

10. **Face-centre material assignment stair-steps a paint line.** → *Rule: make the boundary an
    edge loop (boundary-aware ring sampling) + crease + material index; recess for a real lip.*

11. **Subsurf L2 on dense lofts blew the budget (114k tris).** → *Rule: subsurf viewport/export L1,
    render L2; check `validate.stats()["top_tris"]` to find the offenders.*

12. **Fins barely read** when they only overhung the block by 4 px. → *Rule: repeated details need
    contrast — inset the core so fins stand proud; leave the real interruption (block/head joint).*

13. **Perspective review cams framed too wide** made judgement hard. → *Rule: `rig_from_bounds`
    or size cams to the asset; review renders must fill the frame.*

14. **Old outputs next to new ones confuse reviewers** (v1 renders sat beside v2).
    → *Rule: each asset owns `output/<ASSET>/`; archive or delete stale attempts before delivering.*

15. **Cheatsheet ≠ truth.** The AI-generated sheet had plausible but wrong details (fenders,
    radiator, shock position). → *Rule: photo wins; cheatsheet is for decomposition and naming.*

16. **Idempotent builders made iteration cheap**: rebuild whole stages in ~1–2 min, compare, fix.
    → *Rule: never hand-edit geometry in the GUI; change code/landmarks and rebuild.*

17. **Top-down references need calibrated camera translation and (0,0,180°) rotation.** → Camera
    local -Z views downward while local +Y points to -Y world (nose) and +X points to -X (driver right).
    Off-center photo framing requires solving camera XY position without tilting the asset.

18. **Boolean cutters create empty material slots on evaluated meshes if unassigned.** → Applying
    boolean modifiers without a material generates an unassigned face slot (fails check U07).
    → *Rule: always assign material to cutters and pop extraneous slots after apply_all().*

19. **Mechanical assemblies inside wheel rims produce false intersections if paired broadly.**
    Uprights, hubs, and calipers deliberately sit inside the rim cavity.
    → *Rule: define critical moving clearance pairs as WHEEL_Tire_ rather than WHEEL_.*

17. **The AI cheatsheet drew the TT92 car reversed** (pointed tail labelled "nose", cockpit at the
    wrong end). → It guessed direction from shape. → *Rule: decide the front from function in the
    photo (steering wheel ahead of seat, engine louvres/headers, exhaust exit), never from nose shape.*

18. **Top-view-only reference (TT92)**: plan (X/Y) came from the photo with an orthographic top
    reference camera; heights had to be estimated. → *Rule: for a top photo use an ortho top cam
    (`refcams.top_camera` in the TT92 project) and list every height as an estimate in the report.*

19. **Oblique-photo camera fit with estimated anchors was degenerate** (only 2 points of known height;
    LM converged to a 15 mm lens, 17 px error, useless overlay). → *Rule: fit a camera only with ≥ 4
    anchors whose 3D positions are KNOWN independently of the model; otherwise use the photo qualitatively.*

20. **Colour segmentation of the body edge failed on the shaded side** (dark-red flank, reflections on
    the wet floor). → *Rule: measure the lit edge on gamma-brightened crops, verify the centre line at
    3+ stations (nose, cockpit, tail, wheel pairs) and mirror.*

21. **First studio render was blown out** (white floor, pink paint) and the rim softboxes showed up
    as white cards in the rear shot. → Area-light power must scale with distance² and lights must be
    `visible_camera = False`. → *Rule: present with `workbench.bl.presentation` (tuned, size-scaled);
    check one preview sheet (`--scale 50 --samples 48`) before paying for finals.*

22. **PBR preview balls showed flat colour and diagonal "staircase" seams** — the bmesh UV sphere
    (`create_uvsphere(calc_uvs=True)`) has broken seam UVs, and non-integer repeats break at the seam.
    → *Rule: preview/test meshes need clean UVs and an integer number of texture repeats.*

23. **Imported FBX parts landed at wrong places**: un-parenting a parent changes its children's world
    matrix, and `bound_box` stays stale until the depsgraph updates (also inside hidden collections).
    → *Rule: capture all world matrices before un-parenting, `view_layer.update()` after baking,
    process imports in a visible collection (`workbench.bl.assets` does this).*

24. **CAD-style FBX (2.5 M tris) would not decimate**: split vertices + n-gons + open boundaries stall
    collapse and extreme ratios throw spikes. → *Rule: `assets.decimate(ob, n, cad=True)` (weld 2e-3,
    dissolve degenerate, multi-pass); budget honestly — some downloads are render-only references.*

25. **Mean texture colour looked "wrong" (0.32 for a 0.6 pixel)** — it was right: image pixels are
    sRGB-encoded, `diffuse_color` is linear. → *Rule: linearise sampled colours before using them
    as material values.*
