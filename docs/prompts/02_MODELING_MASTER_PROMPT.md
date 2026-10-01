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

PROCESS (details in docs; start at .claude/skills/blender-workbench/SKILL.md):
S0 Reference analysis (docs/03): decide the visible side; scale from the known size + 2
   cross-checks; remove photo tilt; MEASURE edges (`wb.py mask`, `wb.py profile`) instead of reading
   them, crops + `wb.py snap` otherwise; all silhouettes/points as PIXELS in landmarks.py
   (+ SILHOUETTE). Report the numbers before modelling.
S1 PRIMITIVE: masses from primitives (workbench.bl.prim) for every Part.
S2 LOWPOLY: the real builders, no bevels = game LOD0 with a shared UV atlas.
S3 DETAIL: the same builders with the S3 profile: bevel + weighted normals on hard parts (never
   subsurf plates), subsurf L1/L2 on lofts, fasteners, ribs, holes. Proportions must not drift.
S4 GAME [if game target]: bake S3 -> S2, LOD1-2, collision, [engine] export (docs/12).
After every stage: `python wb.py gate [ASSET]` must PASS; read the worst zones and diff images,
fix the right layer (landmark / builder / profile), rebuild. Numbers, not adjectives.
S5: presentation renders (`python wb.py present [ASSET]`, clay + studio_dark, docs/10), clean
   rebuild gives identical numbers, honest report.

BUDGET: parts.CATEGORY = [hero_vehicle | hero_prop | character | ...] (tables.BUDGETS), <= [8] materials.
DELIVERABLES: output/[ASSET]/blend S0..S4 milestones + [ASSET].blend, glb/[ASSET]_LOD0..2.glb +
[ASSET]_hero.glb, textures/, work/s1..s4 review images, projects/[ASSET]/report.json (all stages PASS).
[OPTIONAL ANIMATION: e.g. "8 s turntable MP4 + wheel spin loop" — docs/07]

REPORTING: after each major phase give PHASE / STATUS / COMPLETED / MAIN CORRECTIONS / UNCERTAIN /
NEXT (short). Work autonomously; ask me only if references contradict each other, an important
component is invisible, or tooling fails. At the end: show the overlay and a review sheet, list
uncertain parts and known limitations honestly, and add any new lesson to docs/09_LESSONS_LEARNED.md.
```

## Short version (when the agent already knows the repo)

```text
New project [ASSET] ([CATEGORY]). Photo + cheatsheet attached. Known size: [..].
Follow AGENTS.md / docs/01_WORKFLOW.md: measured px landmarks → S1 PRIMITIVE → S2 LOWPOLY →
S3 DETAIL → S4 GAME, each gated by `python wb.py gate` → presentation, report. Preserve: [..]. Don't invent: [..].
```
