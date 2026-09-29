# 02 — Modelling master prompt (photo + cheatsheet → 3D model)

Give this to the coding agent in this repository (Claude Code or any agent that reads AGENTS.md).
Attach the photo(s) and the cheatsheet, fill `[...]`. The agent's detailed procedures live in
`docs/`; this prompt sets goals, priorities and the definition of done.

```text
PROJECT: [ASSET_NAME, e.g. VEH_Honda_CB750]   CATEGORY: [vehicle | architecture | character | prop]
TARGET USE: [game asset (engine) | product render | animation | 3D print]   STYLE: [realistic_game]

You are working in the Blender Workbench repository. Read AGENTS.md and docs/00_INDEX.md first,
then follow docs/01_WORKFLOW.md exactly. Save the attached images as
projects/[ASSET]/ref/REAL_REFERENCE.png (primary truth) and ref/MODELING_CHEATSHEET.png (secondary).
[Extra photos: ref/REF_FRONT.png, ref/REF_TOP.png ...]

GOAL: an accurate, editable reconstruction of THIS [OBJECT] — not a redesign, not a generic
[OBJECT TYPE]. With no materials, a flat-grey render from the reference camera must lie on top of
the photo, and the model must stay recognisable from every orthographic view.

KNOWN FACTS: [real sizes you know, e.g. "tyres 120/70-17 front, 180/55-17 rear", "door 2.1 m",
"person is 1.80 m", "overall length about 4.5 m"]. [Anything the photo hides but you know.]

SOURCE PRIORITY: photo > extra photos > cheatsheet > mechanical/structural logic > conservative
guess. The cheatsheet is AI-generated: use it for decomposition, naming and widths, never to
override what the photo shows. Tag every guessed/hidden part with the UNCERTAIN_ prefix.

MUST PRESERVE: [list the identity-defining features, e.g. "tank silhouette with black recessed
knee panel, slim upswept tail, 4-into-1 exhaust routing, fork rake, wheel sizes"].
DO NOT: redesign, add parts not visible (fairings, fenders, decorations), hide errors with
materials, micro-detail before primary forms are validated, merge everything into one mesh.

PROCESS (details in docs):
1. Reference analysis (docs/03): gridded zoom crops of every region; decide the visible side;
   scale from the known size + 2 cross-checks; remove photo tilt; write all silhouettes and key
   points as PIXELS in landmarks.py. Report the numbers before modelling.
2. STAGE 1 LOW blockout (stage1.py): global proportions first (save _01_GLOBAL_BLOCKOUT and
   overlay-check), then structure, main volumes, mechanics, assemblies, routing, secondary parts.
   Gate: overlay edges on the photo, plausible orthos, 0 critical intersections, recognisable in grey.
3. STAGE 2 HIGH (stage2.py): same builders with the HIGH profile; hard-surface = bevel + weighted
   normals (never subsurf plates), organic = subsurf L1/L2; details last (instanced fasteners,
   fins, holes, lines). Proportions must not drift.
4. Correction loop after every major phase: render reference cam + orthos, measure, fix the largest
   mismatch(es), re-render. Numbers, not adjectives.
5. Final: validation checks + report.json, presentation renders (`python wb.py present <ASSET>`,
   clay + studio_dark, docs/10), renders (reference cam clay/material, 5 orthos,
   2 perspectives, wire), GLB export with round-trip check, clean rebuild gives identical numbers.

BUDGET: Stage 1 < [15k] tris, Stage 2 [40k–100k] tris evaluated, ≤ [8] materials.
DELIVERABLES: output/[ASSET]/blend milestones 00…05 + [ASSET].blend, output/[ASSET]/glb/[ASSET].glb,
output/[ASSET]/renders/, projects/[ASSET]/report.json.
[OPTIONAL ANIMATION: e.g. "8 s turntable MP4 + wheel spin loop" — docs/07]

REPORTING: after each major phase give PHASE / STATUS / COMPLETED / MAIN CORRECTIONS / UNCERTAIN /
NEXT (short). Work autonomously; ask me only if references contradict each other, an important
component is invisible, or tooling fails. At the end: show the overlay and a review sheet, list
uncertain parts and known limitations honestly, and add any new lesson to docs/09_LESSONS_LEARNED.md.
```

## Short version (when the agent already knows the repo)

```text
New project [ASSET] ([CATEGORY]). Photo + cheatsheet attached. Known size: [..].
Follow AGENTS.md / docs/01_WORKFLOW.md: landmarks in px → Stage 1 LOW with overlay + intersection
gate → Stage 2 HIGH → validation, renders, GLB, report. Preserve: [..]. Don't invent: [..].
```
