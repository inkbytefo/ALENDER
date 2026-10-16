---
name: blender-python-api
description: Write, debug, migrate, and validate Blender 5.2+ Python automation, bpy/BMesh tools, add-ons, batch exporters, and AI-agent Blender scripts with exact-version API checks and safe scene mutations. Use for operator context failures, depsgraph/evaluated geometry, action API migrations, headless jobs, registration/handlers, or repeatable scene generation. Do not use as the primary skill for unrelated Python, purely artistic modeling advice, or engine-side gameplay code.
---

# Blender Python API

Implement repeatable, inspectable scripts that preserve the user's scene. Explain the operation's scope before substantial edits and report the actual verification performed.

## Inspect and pin

1. Read project instructions, existing scripts and tool capabilities. Inspect the current file and connected Blender runtime before assuming object names, selections, modes or available operators. Never delete the default scene as a generic setup step in a user's file.
2. Run the bundled read-only `scripts/probe_runtime.py` inside Blender, or the equivalent limited introspection through the connected Blender tool. It reports version, action helpers, context facilities and optional RNA metadata without creating scene data. See [patterns.md](references/patterns.md) for usage.
3. Target Blender >=5.2. Record exact `bpy.app.version` and build. For later minors consult that minor's API/change log and runtime RNA; “5.2+” is a maintained workflow, not forward compatibility assurance. Fail clearly on unavailable required features. Consult [sources.md](references/sources.md) rather than relying on remembered 3.x/4.x examples.
4. Define preconditions, owned data, expected object/data counts, output path, rerun behavior and recovery. If no Blender runtime exists, provide source and static validation with a reproducible Blender command; never call it runtime-tested.

## Choose the smallest reliable API surface

- Prefer explicit `bpy.data`, RNA and `mathutils` operations for deterministic creation/edits. Link new Objects into the intended collection; creation alone does not place them into the scene.
- Use `bpy.ops` only when its behavior is needed. Verify `poll()`, mode, active/selected objects and editor requirements. Supply a consistent `bpy.context.temp_override(...)`; do not pass obsolete context dictionaries as positional overrides. A background process has no arbitrary UI area to override.
- Treat object transforms, parent transforms, local/world coordinates and units separately. Do not apply transforms across rigs, shape keys or shared meshes without understanding consequences.
- Use BMesh according to ownership: object-mode standalone BMesh needs explicit writeback and `free()` in `finally`; Edit Mode uses Blender's edit BMesh and `update_edit_mesh`, and must not free that borrowed mesh. Read [patterns.md](references/patterns.md) before mesh edits.
- Evaluate modifiers/constraints through a current depsgraph. Temporary evaluated meshes require cleanup on the evaluated object; copy ordinary numeric values needed later. Do not keep RNA references across deletion, undo, file load or invalidating updates.
- Resolve action+slot channelbags for animation. Do not use legacy `action.fcurves` or assume slot zero. Delegate animation semantics to `blender-animation-system` when applicable.
- Inspect node/socket identifiers and RNA enums in the target runtime; do not use remembered numeric socket indices or silently substitute a different feature. In 5.2 Geometry Nodes modifier inputs/outputs moved to proper RNA under `modifier.properties`; do not reuse legacy `modifier["identifier"]` assignments. Read the migration note in [patterns.md](references/patterns.md).

## Make mutations recoverable

1. Tag script-owned datablocks with a stable namespace/identifier. On rerun update or replace only owned data. Name matching alone is insufficient proof of ownership. Detect shared meshes/materials/actions and linked-library data before writes.
2. Prepare changes in isolated owned datablocks where practical. Validate before replacing existing links. Keep a mutation ledger and clean up only new owned data on failure; undo is not a universal transaction API for background scripts.
3. Use `try/finally` for temporary meshes, BMeshes and context restoration. Restore mode/selection/frame only when the referenced data still exists. Surface exceptions with operation and object context; never `except: pass` or print success after a partial failure.
4. Save only to an explicit task output after validation. Preserve the input file and avoid broad orphan purges. For batch processing, use separate processes/files and a per-file result manifest; a failed item must have an explicit failure state.
5. Do not access `bpy` from background threads. Use separate external processes for independent work; pass serialized data and perform Blender changes through supported main-thread execution. Persistent background Python threads can destabilize Blender even when their purpose seems unrelated.

## Add-on and automation lifecycle

Register classes/properties in dependency order and unregister in reverse. Remove only this tool's handlers, timers, keymaps and subscriptions; handle reload without duplicates. Use persistent handlers only when survival across file loads is intentional, and re-resolve IDs after a load. Avoid scene mutation from render/frame handlers while other Blender threads read that data. Keep long jobs cancellable and progress observable without pretending a timer grants thread safety.

## Verify and return

Test an isolated fixture, then a representative project copy. For generated content run twice and verify no duplicates or unrelated changes. Check expected counts, links, transforms and exported files; test relevant invalid input and context failures. For add-ons exercise register/unregister/re-register and file reload. Use `--python-exit-code 1` in headless validation so exceptions fail the process. Reopen requested saved artifacts where feasible.

Return the script/add-on, invocation, supported tested version, changed data scope and concise test evidence. State which checks were static, mocked, live Blender or engine round-trip. Use `evals/evals.json` for skill evaluation; do not treat the presence of cases as passing them.


# Bundled resources

The resources below belong to this skill. Split them into the indicated relative paths when using a folder-based skill loader.

## File: `references/patterns.md`

````markdown
# Practical runtime and ownership patterns

## Probe commands

Run without modifying an existing scene:

```bash
blender --background --factory-startup --python-exit-code 1 --python /absolute/path/to/scripts/probe_runtime.py -- --require-min 5.2 --rna-type Object
```

Use `--operator export_scene.gltf` to print the installed operator's property identifiers and enum choices. A missing operator/type is an error. The probe prints JSON between `BLENDER_PROBE_BEGIN` and `BLENDER_PROBE_END`; Blender may print additional startup text. No report file or `.blend` is written. `python3 probe_runtime.py --help` works without Blender. Normal execution outside Blender fails explicitly.

For a project-specific read-only check, launch a copy of the file with auto-execution disabled when its embedded scripts are untrusted. The bundled probe does not require access to file contents or secrets and does not list object names.

## Evaluated geometry

```python
dg = bpy.context.evaluated_depsgraph_get()
evaluated = obj.evaluated_get(dg)
mesh = evaluated.to_mesh()
try:
    points = [tuple(evaluated.matrix_world @ v.co) for v in mesh.vertices]
finally:
    evaluated.to_mesh_clear()
```

Use evaluated world transforms for evaluated geometry. Never link this temporary mesh to a persistent object. Request all data layers only when necessary and pass the required depsgraph. Resolve a fresh evaluation after changes; stale evaluated references are not a cache contract.

## Two distinct BMesh paths

Standalone, Object Mode:

```python
bm = bmesh.new()
try:
    bm.from_mesh(mesh)
    # Modify owned/local data, validate geometry and selection invariants.
    bm.to_mesh(mesh)
    mesh.update()
finally:
    bm.free()
```

Edit Mode:

```python
bm = bmesh.from_edit_mesh(mesh)
# Modify the borrowed BMesh; do not free it.
bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
```

Set `destructive` according to topology changes. Validate mesh ownership and current mode before choosing a path; do not run both approaches on the same live Edit Mode mesh.

## Mutation ledger

Track newly created IDs and changes to existing links separately. Store recovery values before edits and commit the intended replacement only after validation. On failure undo known edits in reverse and remove only IDs created by this operation, accounting for users. Preserve diagnostics if recovery itself fails. Do not claim a full transaction when third-party operators have unknown side effects.

For an owned generated collection, use an ID property such as `my_tool.owner = tool_id`, not a broad prefix-only deletion rule. Inspect shared users before replacing its meshes/actions. Duplicate only those data which must diverge; preserve linked instances deliberately.

## Headless failure signals

Use deterministic exit status, operation names and artifact paths. Catch an exception only to add context or perform cleanup, then re-raise. Handle per-file errors in a batch supervisor with a manifest and a nonzero overall exit if any required item fails. Do not save incomplete output over the source during exception handling.

## Blender 5.2 Geometry Nodes migration

The official 5.2 release notes replace modifier custom-property input access with `modifier.properties.inputs.<identifier>.value`, attribute configuration via the input's `.type`/`.attribute_name`, and output names via `modifier.properties.outputs.<identifier>.attribute_name`. Resolve actual identifiers from the runtime rather than treating the literal word `identifier` as a property name. Compare and Random Value socket identifiers also changed. Inspect the actual modifier's dynamic RNA and verify evaluation; merely writing a legacy custom property can appear successful without controlling the intended socket.
````

## File: `references/sources.md`

````markdown
# Sources and API evidence

Research date: 2026-10-01. Baseline: Blender 5.2 documentation. Exact installed patches and later minors must be probed. Official indexed excerpts were retrieved; several direct opens failed. This is source-grounded guidance, not a claim that Blender was present for runtime tests.

- https://docs.blender.org/api/5.2/info_gotcha.html — Official gotchas entry point, including modes, operators, threading and data lifetime.
- https://docs.blender.org/api/5.2/bpy.types.Context.html — Indexed 5.2 signature confirms keyword `temp_override` with window/screen/area/region context.
- https://docs.blender.org/api/current/bpy.types.Object.html?highlight=ray — Retrieved temporary-mesh ownership and `to_mesh_clear()` contract. Resolve `current` to the installed minor before changing production scripts.
- https://docs.blender.org/api/5.2/bmesh.types.html — Retrieved BMesh ownership (`is_wrapped`), lifetime and mesh conversion documentation.
- https://docs.blender.org/api/main/bmesh.html — Retrieved standalone versus Edit Mode patterns. `main` is development evidence only; verify installed 5.2 module signatures before implementation.
- https://docs.blender.org/api/5.0/info_gotchas_threading.html — Official threading warning and separate-process alternative; cross-check the same gotcha in the installed version.
- https://docs.blender.org/api/5.2/bpy.app.handlers.html — Retrieved persistent-handler lifecycle and concurrent data mutation warning.
- https://docs.blender.org/api/5.2/bpy_extras.anim_utils.html — Retrieved modern action-slot helpers; first-bag lookup is not an exhaustive traversal.
- https://developer.blender.org/docs/release_notes/5.2/python_api/ — Retrieved official 5.2 Geometry Nodes RNA migration details and changed socket identifiers; this source supersedes broad compatibility-roadmap examples.
- https://developer.blender.org/docs/release_notes/5.0/python_api/ — Official breaking-change reference for migration. Read exact release notes for every minor crossed.
- https://docs.blender.org/api/5.2/bpy.ops.export_scene.html — Version-pinned exporter options; introspect the installed operator to avoid enum/default assumptions.

Stable ownership tags, explicit outputs, mutation ledgers, idempotence and failure manifests are engineering recommendations in this skill. They do not create a built-in Blender transaction facility. Source checks cannot substitute for runtime/context tests.
````

## File: `scripts/probe_runtime.py`

````python
#!/usr/bin/env python3
"""Read-only Blender capability probe. Does not write files or modify scene data."""
import argparse
import json
import re
import sys


def parse_version(value):
    if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
        raise argparse.ArgumentTypeError("Use MAJOR.MINOR or MAJOR.MINOR.PATCH")
    parts = tuple(map(int, value.split(".")))
    return parts + (0,) * (3 - len(parts))


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-min", type=parse_version, default=(5, 2, 0))
    parser.add_argument("--rna-type", help="Optional bpy.types identifier to inspect")
    parser.add_argument("--operator", help="Optional category.operator to inspect")
    return parser.parse_args(argv)


def describe_rna(rna):
    result = []
    for prop in rna.properties:
        item = {"identifier": prop.identifier, "type": prop.type,
                "readonly": prop.is_readonly}
        if prop.type == 'ENUM':
            item["enum_identifiers"] = [v.identifier for v in prop.enum_items]
        result.append(item)
    return result


def probe(bpy, args):
    version = tuple(bpy.app.version)
    if version < args.require_min:
        raise RuntimeError(f"Blender {version} is below required {args.require_min}")
    from bpy_extras import anim_utils
    report = {
        "blender_version": list(version),
        "version_string": bpy.app.version_string,
        "build_hash": bpy.app.build_hash.decode("utf-8", errors="replace"),
        "background": bpy.app.background,
        "python_version": list(sys.version_info[:3]),
        "context_mode": bpy.context.mode,
        "temp_override": hasattr(bpy.context, "temp_override"),
        "action_slot_rna": "action_slot" in bpy.types.AnimData.bl_rna.properties,
        "animation_helpers": {name: hasattr(anim_utils, name) for name in (
            "action_get_channelbag_for_slot", "action_ensure_channelbag_for_slot",
            "animdata_get_channelbag_for_assigned_slot")},
    }
    if args.rna_type:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", args.rna_type):
            raise ValueError("Invalid RNA type identifier")
        cls = getattr(bpy.types, args.rna_type, None)
        if cls is None or not hasattr(cls, "bl_rna"):
            raise ValueError(f"Unknown RNA type: {args.rna_type}")
        report["rna_type"] = {"name": args.rna_type, "properties": describe_rna(cls.bl_rna)}
    if args.operator:
        if not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", args.operator):
            raise ValueError("Operator must be category.operator")
        category, name = args.operator.split(".")
        operator = getattr(getattr(bpy.ops, category), name)
        # Reading RNA does not call the operator or change context.
        report["operator"] = {"name": args.operator,
                              "properties": describe_rna(operator.get_rna_type())}
    return report


def main(argv=None):
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = arguments(argv)
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError("Run this probe inside Blender; only --help works in ordinary Python") from exc
    print("BLENDER_PROBE_BEGIN")
    print(json.dumps(probe(bpy, args), indent=2, sort_keys=True))
    print("BLENDER_PROBE_END")


if __name__ == "__main__":
    main()
````

## File: `evals/evals.json`

````json
{
  "skill_name": "blender-python-api",
  "evals": [
    {
      "id": 1,
      "prompt": "Blender 5.2 headless çalışan bu procedural sahne scriptini iki kez çalıştırınca kopyalar oluşturuyor. Diğer objeleri bozmadan idempotent yap.",
      "expected_output": "Owned-data updates with repeat-run verification and input preservation.",
      "files": [],
      "assertions": [
        "Inspects exact runtime and scene scope",
        "Uses stable ownership tags not broad name-based deletion",
        "Runs twice on copy or clearly labels missing Blender runtime; failures are explicit"
      ]
    },
    {
      "id": 2,
      "prompt": "MCP Blender scriptim Edit Mode mesh değiştirince çökmeye başladı; modifier sonrası dünya koordinatlarını JSON almak istiyorum.",
      "expected_output": "Mode-appropriate BMesh and evaluated-geometry implementation.",
      "files": [],
      "assertions": [
        "Differentiates borrowed edit BMesh from standalone BMesh",
        "Uses evaluated transform and to_mesh_clear in finally",
        "Does not retain removed/evaluated RNA references or access bpy from worker threads"
      ]
    },
    {
      "id": 3,
      "prompt": "Blender 5.2 eklentimde yüklemeden sonra handler iki kez çalışıyor, ayrıca glTF export enum hatası alıyorum. Düzelt ve lifecycle testini ver.",
      "expected_output": "Scoped handler lifecycle and runtime-inspected exporter options.",
      "files": [],
      "assertions": [
        "Removes only owned handlers and makes register/unregister/re-register repeatable",
        "Uses persistence only deliberately and re-resolves IDs after load",
        "Probes RNA options and separates static checks from live runtime results"
      ]
    }
  ]
}
````

## File: `evals/trigger-evals.json`

````json
[
  {
    "query": "Blender headless bpy operator poll hatasını düzelt",
    "should_trigger": true
  },
  {
    "query": "5.2 addonumu register unregister uyumlu yap",
    "should_trigger": true
  },
  {
    "query": "Pandas ile CSV analizi yap",
    "should_trigger": false
  },
  {
    "query": "Hiç kod yazmadan karakter yürüyüşüne sanatsal eleştiri ver",
    "should_trigger": false
  }
]
````
