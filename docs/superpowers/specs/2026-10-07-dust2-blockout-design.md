# Dust2 1:1 blockout — design brief

## Goal

Create a reproducible Blender blockout of the current Counter-Strike 2 Dust2 map at 1:1 scale. The first deliverable covers the playable layout and its characteristic spatial feel: ground levels, ramps, corridors, doorways, walls, cover masses, and the main sightlines. It is a blockout, not a detailed architectural or material reconstruction.

## Reference and measurement

1. Treat the current CS2 Dust2 map as the target version, as confirmed by the user.
2. First inspect whether the local CS2 installation exposes the official compiled map geometry or map source in a form that can be read. If available, use it as the primary dimensional source and record the extraction/conversion method.
3. If no usable local map data is available, use a measured top-down radar/map image plus published dimensions as cross-checks. Do not present inferred geometry as exact; mark uncertain dimensions and elevations in the project files.
4. Use the published bomb plant bounds (A about 6.9 × 7.3 m; B about 9.7 × 9.3 m) only as independent checks, not as a substitute for the whole-map source.
5. Record coordinate orientation, scale conversion, and all source/version choices in `project.md` and the measurement data. Model dimensions in metres with Blender unit scale 1.

## Modeling approach

- Add a new map project under `projects/` using the existing Workbench staged pipeline.
- Keep the build deterministic and idempotent; source code is authoritative.
- Organize geometry into named areas and functional parts: T spawn, Long A and pit, mid and doors, short/catwalk, A site and CT routes, upper/lower tunnels, B site, and connectors.
- Build sequentially by functional group and elevation, checking the saved scene after each group. Prefer clean boxes, extruded plan profiles, and simple ramps; preserve openings and walkable connections.
- Name speculative elements with `UNCERTAIN_`. The first pass contains only blockout masses and simple neutral materials.

## Validation and deliverables

- Deliver the S1 primitive blockout as a Blender scene, source Python project, and a top-down plus three-quarter review render.
- Validate overall footprint and elevations against the selected map source; validate site bounds and a small set of documented route distances as independent checks.
- Compare the top-down blockout against the radar/map plan and inspect the major play-space sightlines in the three-quarter render.
- Run the applicable Workbench gate and report its result honestly. If generic silhouette gates do not represent a level blockout, add project-specific numeric checks rather than relaxing shared thresholds.
- Do not proceed to surface detailing, materials, lighting polish, or S2/S3 until the user reviews the blockout.

## Limits

“Exact” means matching the selected CS2 version's measured playable geometry and scale. Where the official map data cannot be read locally, the result is a measured reconstruction with explicitly documented uncertainty, not a claim of byte-for-byte geometry recovery. Non-playable skybox and decorative props are out of scope for S1.

## Self-review

- Scope is limited to the current CS2 version and S1 blockout; later finish work is explicitly deferred.
- The primary-reference fallback is stated, and derived measurements cannot silently become exact claims.
- Validation includes map-specific checks without changing shared Workbench gate thresholds.
- No TODO placeholders or conflicting scale/orientation requirements remain.

## Reference links reviewed

- [Dust 2 CS2 routes and published site dimensions](https://csbepro.com/counter-strike-2/dust-2/)
- [Dust2 top-down overview](https://strategywiki.org/wiki/File:Css_de_dust2_overview_general.png)
- [Source 2 map export overview](https://s2v.app/ValveResourceFormat/guides/exporting-maps.html)
