# Dust2 Blockout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and validate a reproducible S1 Blender blockout of current CS2 Dust2 at 1:1 scale.

**Architecture:** A Workbench `architecture` project will hold a map-specific top-down reference transform and measured layout data. Its staged builders will create separately named play-space masses from the source measurements, with Blender-native boxes and simple extruded profiles; project-specific checks will validate footprint, elevation, site bounds, and route distances.

**Tech Stack:** Python 3, Blender 5.2 Python API (`bpy`, `bmesh`, `mathutils`), existing Blender Workbench staged pipeline and gate.

**Spec:** `docs/superpowers/specs/2026-10-07-dust2-blockout-design.md`

## Global Constraints

- Target the current Counter-Strike 2 Dust2 version.
- Use metres with Blender unit scale 1.
- S1 includes playable layout masses, ground levels, ramps, corridors, doorways, cover masses, and major sightlines; no surface-detail pass.
- Prefer local official map geometry as the primary dimensional source; if unavailable, use a measured top-down reference with explicit uncertainty.
- Keep code deterministic and idempotent; code is authoritative.
- Do not weaken shared Workbench gate thresholds.
- Stop after S1 for user review.

## Review Focus

- Local map data may be absent or in a format current tools cannot export: verify source availability first and use the approved measured-reference fallback.
- A radar image is symbolic and not metric: calibrate scale from the independent published A/B site bounds and cross-check documented route lengths.
- Top-down projection can hide elevation errors: add separate elevation and ramp endpoint checks.
- Large connecting geometry may leave unintended gaps or overlaps: check corridor connectivity and critical intersections from map-specific geometry.
- Default Workbench reference helpers assume side views: implement and inspect a top-down reference transform/camera for the project, without changing shared thresholds.

---

### Task 1: Establish the map measurement source

**Files:**
- Create: `projects/MAP_Dust2/project.md` (via Workbench scaffold)
- Create: `projects/MAP_Dust2/mapdata.py`
- Create: `projects/MAP_Dust2/ref/` with the selected reference image and source notes

**Interfaces:**
- Produces `mapdata.py` constants in metres: `AREAS`, `ROUTES`, `ELEVATIONS`, `SITES`, and `SOURCE_INFO`.
- Each area entry has a stable name, plan polygon or centerline/width, floor elevation, and confidence/source tag.

- [ ] Inspect common local CS2 install locations for the current map package and available Source 2 map export tools. Record the version/path and whether geometry export is possible.
- [ ] If readable local map geometry exists, export/read only the map geometry needed to measure playable floor plan, elevations, site bounds, and route centerlines; retain source notes and conversion factors.
- [ ] If local geometry is unavailable, save a clear top-down map reference and derive mapdata from it, calibrated against A and B published site bounds; mark eye-read values `UNCERTAIN_` and record the limitation.
- [ ] Add a host-side measurement report to `project.md` with world bounds, source coordinate conversion, A/B site dimensions, and at least three route distance cross-checks.

### Task 2: Scaffold a top-down Workbench project

**Files:**
- Create: `projects/MAP_Dust2/build.py`
- Create: `projects/MAP_Dust2/landmarks.py`
- Create: `projects/MAP_Dust2/parts.py`
- Modify: `projects/MAP_Dust2/project.md`

**Interfaces:**
- `landmarks.py` exposes `ASSET = "MAP_Dust2"`, top-down `REF`, `IMAGE_SIZE`, `ANCHORS`, `SILHOUETTE`, and map coordinate helpers.
- `parts.py` exposes the Workbench contract (`CATEGORY`, `PROFILES`, `PARTS`, `TARGET_DIMS`, `GROUND`, `PALETTE`, `CRITICAL_PAIRS`, `UNCERTAIN`) plus map-specific extra checks.
- `build.py` remains the standard three-line Workbench pipeline entry point.

- [ ] Scaffold `MAP_Dust2` with category `architecture`; fill the project objective, source/version, map coordinate orientation, scale, stage scope, and uncertainty sections.
- [ ] Replace the side-photo transform with a project-local top-down reference transform that maps plan-image coordinates onto world X/Y and configure a top-down review camera through the supported `REF.view="TOP"` contract.
- [ ] Define the top-down reference silhouette from the playable bounds and keep Z for real elevation; verify anchors reproject within 2 px in Blender.
- [ ] Set overall target dimensions and material/budget limits from measured map bounds, not guessed defaults.

### Task 3: Build the S1 blockout in readable passes

**Files:**
- Modify: `projects/MAP_Dust2/mapdata.py`
- Modify: `projects/MAP_Dust2/parts.py`

**Interfaces:**
- Each `Part` builder consumes a stage profile and mapdata; it creates only its named stage-suffixed mesh objects in the assigned Workbench collection.
- Stable part groups: `SPAWN_T`, `LONG_A`, `MID`, `SHORT_A`, `SITE_A`, `CT_ROUTES`, `TUNNELS`, `SITE_B`, and `CONNECTORS`.

- [ ] Build the ground/ramp and corridor volumes first, preserving measured walkable widths, wall openings, and floor elevations; keep each functional area in a separate `Part` builder.
- [ ] Build the two sites, doors, cover masses, and connecting walls in a second pass using simple boxes/extruded polygons; tag guessed geometry with `UNCERTAIN_` names.
- [ ] Run `python wb.py build MAP_Dust2 --until 1 --no-bake`; confirm deterministic object naming, unit scale, and stage collection placement.
- [ ] Fix the largest footprint or elevation mismatch from the generated top-down and three-quarter review images before continuing.

### Task 4: Add map-specific checks and review the blockout

**Files:**
- Modify: `projects/MAP_Dust2/parts.py`
- Modify: `projects/MAP_Dust2/project.md`

**Interfaces:**
- `parts.py` extra-check callback appends normal Workbench check records with stable ids `M10`–`M14`.
- Metrics record measured `bounds_m`, `site_dims_m`, `route_lengths_m`, `elevation_range_m`, and `uncertain_parts` in `report.json`.

- [ ] Add `M10` footprint/bounds check (within 1% of selected source bounds), `M11` A/B site dimensions (within 3% of selected source values), `M12` documented route-length checks (within 3%), `M13` required connector continuity, and `M14` elevation/ramp endpoint checks (within 0.05 m of selected source values).
- [ ] Run `python wb.py build MAP_Dust2 --until 1 --no-bake` and `python wb.py gate MAP_Dust2 1`; inspect the diff/review images and every failed blocker.
- [ ] Correct measured input or builder placement, never shared thresholds; rebuild until the applicable S1 gate passes or report the specific source limitation.
- [ ] Save and show the top-down and three-quarter blockout review images, summarize source confidence and uncertain regions, and stop for the user's S1 review.

## Plan self-review

- Spec coverage: current CS2 target, local-source-first measurement, measured fallback, uncertainty labels, sequential blockout, 1:1 dimensions, map-specific validation, gate, renders, and S1-only stop are each assigned to a task.
- Step scan: each step has a concrete file/output or command-based check.
- Type consistency: mapdata constants use metres; Workbench callbacks consume its map groups and append checks/metrics.
- Review focus: local-source absence, symbolic radar scale, hidden vertical information, connectivity, and top-down camera assumptions have owning checks/tasks.
- Proportion: four tasks map to four independently reviewable outcomes; no later detailing/game export is included.
