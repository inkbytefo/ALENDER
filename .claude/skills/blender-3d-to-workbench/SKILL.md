---
name: blender-3d-to-workbench
description: Reverse-engineer, measure, and reconstruct existing 3D models (GLB, FBX, OBJ, blend) into clean, procedural, reproducible workbench assets (projects/<ASSET>) across stages S1-S5. Use when given an existing 3D model reference or raw asset to rebuild from scratch using pure Python code, exact silhouette masking, landmark pixel matching, and automated gate validation.
---

# Blender 3D Model to Workbench Reconstruction

You take an existing 3D model (GLB, FBX, OBJ, `.blend`) as ground-truth reference and reconstruct it
from scratch as a 100% procedural, reproducible Python workbench asset under `projects/<ASSET>/`.
Never import foreign geometry into the final asset; reverse-engineer its dimensions, silhouettes,
pivots, and materials into code.

## Core Rules
1. **Reconstruct, don't re-mesh**: Foreign 3D models often carry dirty geometry (n-gons, non-manifold
   edges, non-uniform scaling, uncentered pivots). Extract their dimensions and silhouette, but build
   clean procedural geometry from scratch in `parts.py`.
2. **Pixels & Metrics are Truth**: Measure source dimensions with code (`wb.py inspect` / custom script).
   Render orthographic reference views and extract binary masks into `ref/REAL_REFERENCE.png` and
   `ref/REF_MASK.png`.
3. **Automated Gating**: Every stage must PASS `python wb.py gate <ASSET>` with 0 blockers and 0 warnings:
   - Zero n-gons (strictly 0.0%)
   - Zero non-manifold or degenerate elements
   - Exact silhouette match (IoU $\ge 0.85$, boundary p95 $\le 14.0\text{ px}$)
   - Budget compliance (tris, materials, GLB size, draw calls)

---

## Step 0: Source Asset Inspection & Hierarchy Mapping

1. **Inspect Geometry & Bounds**:
   Use a headless inspection script or `python wb.py inspect <model.glb>` to extract:
   - Overall bounding box ($X, Y, Z$ dimensions in metres)
   - Component mesh names, vertex counts, materials
   - Hierarchy and relative transforms
   - Pivots and kinematic ranges (stroke distances, rotation axes)
2. **Scaffold New Asset**:
   ```bash
   python wb.py new <ASSET> --category <prop|vehicle|weapon|etc> [--budget <key>]
   ```
   Fill `projects/<ASSET>/project.md` with target engine, bounding dimensions, and budget constraints.

---

## Step 1: Reference Renders & Silhouette Extraction

1. **Render Orthographic Side View (`ref/REAL_REFERENCE.png`)**:
   Render an orthographic side camera shot of the source model at $1920 \times 1080$ with a neutral
   high-contrast background.
2. **Extract Binary Silhouette Mask (`ref/REF_MASK.png`)**:
   Render the alpha mask of the entire model assembly.
3. **CRITICAL GOTCHA — Hairline Submesh Seams (Lesson 56)**:
   - Multi-part models (e.g. frame, slide, cylinder, accessories) frequently have tiny clearances
     ($0.1\text{ mm}$ gaps). In the rendered mask, these show up as 1 px transparent fracture cracks.
   - The boundary distance transform (`d_rn`) treats hairline cracks as huge internal voids, spiking
     p95 error ($> 100\text{ px}$).
   - **Fix**: Run morphological closing or connected-component hole filling on internal micro-holes
     ($< 1000\text{ px}$) while strictly protecting genuine functional voids (e.g. trigger guard loops,
     windows, chassis pass-throughs $> 10,000\text{ px}$).

---

## Step 2: Pixel Landmarks & Silhouette Definition (`landmarks.py`)

1. **Anchor Coordinates**:
   - Establish `RefMap(side="RIGHT"|"LEFT", scale_px_per_m=..., p_origin=(U, V))` using the primary bounding dimensions.
   - Record key boundary points in integer pixels: muzzle, rear tang, grip base, top of receiver, controls.
2. **Closed Silhouette Polylines (`SILHOUETTE`)**:
   - Define closed 2D pixel polylines for major functional assemblies.
3. **CRITICAL GOTCHA — 2D Bridging vs 3D Boolean Voiding (Lesson 57)**:
   - To rasterize closed loops (such as trigger guards or structural apertures) in 2D (`landmarks.py`),
     a bridge cut line must connect the outer envelope to the inner hole so PIL draws a single polygon.
   - **Never extrude a bridged 2D polyline in 3D (`parts.py`)**: coincident edges create zero-thickness
     non-manifold faces (`U04 FAIL`).
   - **Rule**: Keep the bridged polyline in `landmarks.py` for 2D validation (`R01`). In `parts.py`,
     extrude a solid volumetric prism and punch the aperture using a clean exact boolean cutter
     (`mesh.boolean_diff`) followed by `mesh.dissolve_degenerate()` and `mesh.triangulate()`.

---

## Step 3: Procedural Builders & Staged Pipeline (`parts.py`)

1. **Stage 1 (Primitive Blockout)**:
   - Use simple primitive stand-ins (`prim="cylinder"`, `prim="box"`, or basic lofts).
   - Anchor bounds strictly to landmark planes (`p_front[1]`, `L.TOP_Z`, `L.HALF_WIDTH`, `z=0.0001`).
   - Run `python wb.py build <ASSET> --stage 1` and `python wb.py gate <ASSET> 1`.
   - Verify `output/<ASSET>/work/s1/s1_r01_diff.png` and `s1_r02_diff.png`.
2. **Stage 2 (Low-Poly Game Geometry)**:
   - Replace primitives with production low-poly meshes.
   - Use clean bevels and arches with controlled segment counts (e.g. 6-segment arch for slide tops).
   - **CRITICAL GOTCHA — Microscopic Grooves & Slivers (Lesson 58)**:
     - Never carve dense parallel boolean slots (e.g. cocking serrations, cooling fins) into curved
       low-poly hulls in S2; they cause coplanar slivers and degenerate triangles (`U16 FAIL`).
     - Keep low-poly hulls continuous and clean; bake micro-grooves into normal maps in S4.
   - **Budget Floor Balancing (Lesson 59)**:
     - If planar components fall below the game triangle budget floor (e.g. minimum 4,000 tris for hero props),
       apply structured quad subdivision (`bmesh.ops.subdivide_edges(cuts=N, use_grid_fill=True)`) to
       tactile areas (checkering, knurling, grip panels) to build clean physical diamond topology.
   - **UV Atlas**:
     - Ensure 100% unwrapped geometry, zero unmapped faces, $\ge 40\%$ coverage, and texel spread $\le 2.5$.
   - Run `python wb.py build <ASSET> --stage 2` and `python wb.py gate <ASSET> 2`.
3. **Stage 3 (High-Poly Detail)**:
   - Apply micro-bevels (`finish_hard(bevel_width=...)`) and weighted normals to all mechanical parts.
   - Export hero GLB (`output/<ASSET>/glb/<ASSET>_hero.glb`).
   - Run `python wb.py build <ASSET> --stage 3` and `python wb.py gate <ASSET> 3`.
4. **Stage 4 (Game Delivery & Baking)**:
   - High-to-low bake in Cycles: BaseColor, Normal (OpenGL tangent space), and ORM (Ambient Occlusion, Roughness, Metallic) at 2048×2048.
   - Generate LOD0, LOD1 (50%), LOD2 (25%) meshes.
   - Add Godot convex collision hulls (`-convcolonly`) with $\le 255\text{ faces}$ per hull.
   - Ensure moving parts are parented with centered pivots in `pivots` dict.
   - Run `python wb.py build <ASSET> --stage 4` and `python wb.py gate <ASSET> 4`.

---

## Step 4: Presentation & Studio Validation (Stage 5)

1. **Render Studio & Turntable**:
   ```bash
   python wb.py present <ASSET> --style clay --turntable 8
   python wb.py present <ASSET> --style studio_dark --turntable 8
   ```
2. **Engine Compatibility Check**:
   ```bash
   python wb.py glb output/<ASSET>/glb/<ASSET>_LOD0.glb
   ```
   Verify 1 draw call, 1 material, correct texture bindings, and Godot axis alignment ($+Z$ up, $-Y$ forward).
3. **Inspect Output Images**:
   Review contact sheets and turntable video in `output/<ASSET>/presentation/`.
