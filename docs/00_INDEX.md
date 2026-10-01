# Docs index — read this first

Blender Workbench = headless Blender + a Python library (`workbench/`) + a staged, gated process
for building **reference-accurate, game-ready** 3D assets (vehicles, buildings, characters, props),
animations and videos. Everything is code: `projects/<ASSET>/*.py` is the source, `.blend/.glb`
are outputs, `report.json` + `python wb.py gate` decide what is done.

**Agents: start with `.claude/skills/blender-workbench/SKILL.md`** (the checklist) and open the
documents below only when a step points to them.

| Doc | Open when |
|-----|-----------|
| `01_WORKFLOW.md` | the stage model S0–S5, commands, correction loop, legacy migration |
| `09_LESSONS_LEARNED.md` | index table at the top — skim your category's JUDGEMENT lessons |
| `03_REFERENCE_ANALYSIS.md` | S0: scale, side, tilt, measuring edges (mask / profile / snap) |
| `06_CATEGORIES.md` | part breakdown + pitfalls per asset type |
| `04_MODELING_TOOLKIT.md` | which builder for which shape, stage profiles, Part registry, module map |
| `02_STANDARDS.md` | axes, units, naming + stage suffixes, collections, budgets, materials |
| `05_VALIDATION.md` | every check id, thresholds, report.json, gate rules |
| `12_GAME_READY.md` | S4: atlas, bake, LODs, collision, engine naming, exports |
| `07_ANIMATION_AND_VIDEO.md`, `08_BLENDER_API_NOTES.md` | anim/video; Blender 5.x gotchas |
| `11_ASSETS_AND_PBR.md` | PBR texture sets in palettes, importing / fitting downloaded models |
| `10_PRESENTATION.md` | S5 studio renders, turntable |
| `case_studies/VEH_Gemini_Motorcycle.md` | a complete (legacy two-stage) project with real numbers |
| `projects/PROP_AK_Rifle` | the reference implementation of the staged pipeline (S1–S4 PASS) |

## Prompts for the user (and for image / coding AIs)
`prompts/` — master prompts: modelling cheatsheet with an image generator, starting a modelling
job from photo + cheatsheet, category packs, iteration / fix prompts.

## Priority when documents disagree
1. the user's explicit request  2. the reference photo  3. `project.md` of the asset
4. category section (`06`)  5. `02_STANDARDS.md`  6. everything else.
Knowingly breaking a rule → `parts.GATES` override or a `waivers` note with the reason.
