# 01 — Workflow: reference-driven, two-stage, measured

Goal: **reconstruction, not re-design.** A flat-grey render from the reference camera must lay
on top of the photo. A simple accurate model beats a detailed wrong one.

```
 intake ─► reference analysis ─► landmarks.py ─► STAGE 1 LOW ─► GATE ─► STAGE 2 HIGH ─► final gate ─► deliver
                (numbers)          (px truth)      blockout      │         refine          │
                                                    ▲            │           ▲             │
                                                    └─ correct ◄─┘           └─ correct ◄──┘
```

## 0. Intake (5 min)
- `python wb.py new <ASSET> --category <c>` → `projects/<ASSET>/` from `templates/project`.
- Copy photos to `projects/<ASSET>/ref/` (`REAL_REFERENCE.png` = primary, `MODELING_CHEATSHEET.png` = secondary).
  Convert webp/jpg to png (Pillow). Record image size.
- Fill `project.md`: category, objective, style, budget, part breakdown, uncertain areas.
- Source priority: **photo > extra photos > cheatsheet > mechanical logic > conservative guess.**
  The cheatsheet is AI-generated and often wrong in details (it drew the prior failed model's
  style); use it for decomposition and naming, never to override the photo.

## 1. Reference analysis → numbers (docs/03)
- Grid the photo, zoom-crop every region (`wb.py grid`, `wb.py crop`) and *read* pixels.
- Decide the side shown (front on image right ⇒ you see the object's RIGHT side ⇒ camera at −X).
- Derive scale from a known real size (tyre, door, human height…), cross-check with 2 others.
- Detect tilt (stands, slopes, camera roll) and remove it in the RefMap.
- Write every silhouette/point in **pixels** into `landmarks.py`. Metres come from `REF.P()`.

## 2. Scene setup (stage1.py, top)
`scene.reset()` → `setup_collections()` → `materials.ensure(PALETTE)` →
`cameras.reference_camera(REF, anchors)` (check `anchor_reprojection_error_px` < 2) →
`reference_image()` → `review_rig()` → `scene.guides(points)` → save `_00_SETUP`.

## 3. STAGE 1 — LOW blockout (phases in order)
1. **Global proportions only**: main volumes that define the footprint (wheels / floor plan /
   body height / skeleton). Save `_01_GLOBAL_BLOCKOUT`, overlay → must match before continuing.
2. Structure (frame / walls / spine), 3. dominant body volume (tank, hull, torso, roof),
4. secondary volumes, 5. mechanical masses, 6. front/rear assemblies, 7. routing (pipes, cables),
8. secondary parts that change the silhouette.
Rules: primitives, separate objects, no bevels/bolts/fins, `_LOW` suffix (automatic via `nm()`).

### Stage 1 gate (all must be true)
- overlay edge (`wb.py compare`) sits on the photo edges for every major part (±5 px)
- orthographic views plausible: symmetry, widths, nothing impossible in top/front
- **0 critical intersections** (`validate.intersections(CRITICAL_PAIRS)`)
- recognisable in flat grey
Save `_02_COMPLETE_LOW` and `_STAGE_01_LOW`. Never start Stage 2 before this passes.

## 4. STAGE 2 — HIGH refine
Re-run the *same builders* with the HIGH LOD profile (denser sections, subsurf on organic parts,
bevel + weighted normals on hard parts). Proportions cannot drift because both stages read
`landmarks.py`. Order: primary forms (`_03_HIGH_PRIMARY`) → mechanical (`_04_HIGH_MECHANICAL`)
→ details: instanced fasteners, fins, holes, clamps, lines (`_05_FINAL_GEOMETRY`).
LOW collections stay in the file, hidden.

## 5. Correction loop (both stages)
```
observe (render ref cam + orthos) → measure (overlay, bbox, intersections, tri counts)
→ list mismatches → fix the LARGEST one (or top 3-5 unrelated ones) → re-render → repeat
```
Priority: global proportion > silhouette > placement > major curvature > thickness > secondary > detail.
Stop after 6 iterations on the same blocker → analyse the layer (landmark? builder? API? render?).

## 6. Final gate & delivery
`validate.standard_checks` + category checks + intersections + GLB round trip (U15) →
`report.json`. Renders: reference cam (clay+material), 5 orthos, 2 perspectives, wire.
Presentation (docs/10): `python wb.py present <ASSET> --style clay` (shape review — look at the
sheet) then `python wb.py present <ASSET>` (finals, studio_dark).
Deliver: milestones in `output/<ASSET>/blend/`, `<ASSET>.glb`, renders, presentation sheet, report.
Report honestly: result, numbers, uncertain parts, known limitations.

## Phase report format (after each major phase, keep it short)
```
PHASE: / CURRENT STATUS: / COMPLETED: / MAIN CORRECTIONS: / UNCERTAIN AREAS: / NEXT ACTION:
```

## Autonomy
Proceed without asking after every step. Ask only when references contradict each other,
a major component is invisible *and* important, tooling fails, or an action would destroy
significant work.
