# CLAUDE.md

@AGENTS.md

## Claude-specific notes
- For any modelling / animation / rendering task in this repo, use the project skill
  `blender-workbench` (`.claude/skills/blender-workbench/SKILL.md`); it is the checklist version of
  docs/01.
- **Look at your renders.** After every render step, open the PNGs (Read tool) — overlay
  `compare_*_edge.png` first, then orthos and a perspective. Describe mismatches in numbers.
- Blender MCP tools (if connected) are for *observing* a live GUI session (screenshots, object
  summaries). Production always goes through `python wb.py build/run` so results stay reproducible.
- Long builds: run `wb.py build` and filter output, e.g.
  `python wb.py build X 2>&1 | grep "STAGE\|BLOCKER\|WARN\|Traceback\|Error"`.
- Deleting user files: prefer the Windows Recycle Bin (PowerShell
  `Microsoft.VisualBasic.FileIO.FileSystem.DeleteDirectory(..., 'SendToRecycleBin')`).
- The user writes Turkish; answer in Turkish, keep code/docs/commits in English.
