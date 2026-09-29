# Docs index — read this first

Blender Workbench = headless Blender + a Python library (`workbench/`) + a proven process for
building **reference-accurate** 3D assets (vehicles, buildings, characters, props), animations
and videos. Everything is code: `projects/<ASSET>/*.py` is the source, `.blend/.glb` are outputs.

## Reading order for a new task

| Step | Read | Why |
|------|------|-----|
| 1 | `01_WORKFLOW.md` | the two-stage loop, phases, gates, milestones — non-negotiable |
| 2 | `09_LESSONS_LEARNED.md` | mistakes already paid for; skim every time |
| 3 | `03_REFERENCE_ANALYSIS.md` | how to turn photos into metres (scale, side, tilt, landmarks) |
| 4 | `06_CATEGORIES.md` (your section) | part breakdown + pitfalls per asset type |
| 5 | `04_MODELING_TOOLKIT.md` | which builder for which shape; library API |
| 6 | `02_STANDARDS.md` | axes, units, naming, collections, budgets, materials |
| 7 | `05_VALIDATION.md` | overlays, intersection pairs, checks, report.json |
| as needed | `07_ANIMATION_AND_VIDEO.md`, `08_BLENDER_API_NOTES.md` | anim/video; Blender 5.x gotchas |
| example | `case_studies/VEH_Gemini_Motorcycle.md` | a complete worked project with real numbers |

## Prompts for the user (and for image / coding AIs)

`prompts/` — master prompts: build a modelling cheatsheet with an image generator, start a
modelling job from photo + cheatsheet, category packs, iteration / fix prompts.

## Priority when documents disagree

1. the user's explicit request  2. the reference photo  3. `project.md` of the asset
4. category section (`06`)  5. `02_STANDARDS.md`  6. everything else.
Knowingly breaking a rule → write it under `waivers` in `report.json` with the reason.
