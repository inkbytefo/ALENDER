---
name: blender-animation-system
description: Build, retarget, repair, bake, and export game animation in Blender 5.2+ using version-verified rigs, IK/FK, action slots, NLA, root motion, and measurable motion quality. Use for character or mechanical rigging, locomotion clips, mocap cleanup, animation libraries, Blender-to-Godot exports, or animation API migrations. Do not use as the primary skill for engine-only AnimationTree gameplay code, static modeling, or rendered video editing.
---

# Blender Animation System

Produce editable source animation and a verified engine-facing result. Treat runtime playback as part of animation quality, not an assumed consequence of export.

## Establish the contract

1. Inspect the file before edits: Blender version/build, units, frame rate including `fps_base`, frame ranges, armatures, rest pose, mesh bindings, actions/slots, NLA, constraints, drivers and linked data. Record source and target skeletons. Never change rest pose, apply armature transforms, or overwrite actions merely to make a retarget look correct.
2. Require Blender >=5.2 for this workflow. Match documentation to the exact installed minor; check release changes and RNA for later versions. Read [sources.md](references/sources.md) for evidence and version boundaries. If the requested API cannot be verified, state the uncertainty and probe it rather than inventing a call.
3. Define clip names, intended speed, loop/one-shot, duration, contact events, in-place/root-motion convention, root bone, facing axis, scale, export format and target engine version. Infer reversible defaults from the project; ask only for blocking artistic or gameplay choices.
4. Choose acceptance thresholds in project units: planted-foot drift, penetration, root displacement, end-pose error and bake deviation. Do not present universal numeric thresholds as industry standards.

## Build and edit

- Separate animator controls/mechanism bones from the export deformation hierarchy. Retain required ancestors/root bones even when exporting deform bones only. Use bone collections rather than legacy armature layers.
- Set bone roll/rest orientations deliberately. Validate weights at joint extremes before polishing clips. Keep an untouched source rig and a separately owned export/bake target when substantial conversion is needed.
- For IK, define chain length, owner/target spaces, pole target and pole angle. Test straight and nearly straight limbs, target reach limits, mirrored sides, and pole-crossing poses. Disable unintended stretch. Measure world-space contact positions on evaluated poses; pose-channel values alone do not prove a planted foot.
- Match FK/IK poses before switching. Avoid dependency cycles and double transforms. For retargeting, map semantics and rest-pose offsets, normalize scale, preserve root/pelvis separation and solve contacts; matching bone names is insufficient.
- Use keyframe insertion when appropriate. For curve edits, resolve the actual assigned `AnimData.action` and `AnimData.action_slot`, then the matching channelbag. Do not use legacy `action.fcurves`, guess slot zero, or edit all users of a shared action unintentionally.
- Treat action slots/layers/strips and NLA tracks/strips as different structures. A helper returning the first channelbag is sufficient only for a verified single relevant strip; traverse the required layers/strips when the task spans multiple bags. Handle missing action, slot or bag explicitly. Consult [workflow.md](references/workflow.md) for migration and bake checks.
- Set deliberate interpolation and rotation modes; inspect overshoot, quaternion discontinuities and Euler flips. Preserve timing in seconds when changing FPS. Keep foot/hand events in a clip manifest if export cannot preserve their authoring representation.

## Bake and deliver

1. Duplicate or create owned bake targets and actions; tag ownership and preserve the original. Evaluate the full rig at the agreed sample rate. Bake visual transforms required by constraints/drivers; unsupported authoring logic is not an engine feature.
2. Compare source and baked world-space poses at contacts, extrema and intermediate frames. Only simplify keys after measuring deviation. Verify scale channels and root motion separately.
3. Select the installed glTF export animation mode explicitly and inspect its RNA options. Confirm exactly which actions/slots/NLA tracks export; a datablock merely existing does not mean it is included. Never rely on old rules that merge all clips by NLA name.
4. Export and reimport into a clean scene; load into the actual target engine if available. Verify clip list, lengths, rest pose, deformation, axes, scale, root track, looping and transition behavior. For Godot, define who consumes root motion so the character is not moved twice.
5. Supply the editable `.blend`, requested exported asset, clip manifest and evidence. Distinguish measured results, visual review, and checks not run. Do not call a system production-ready on the strength of a viewport preview alone.

## Validation focus

Review start/stop, left/right turn, loop boundary, FK/IK switch, contact release, and transition blends. For in-place clips compare contacts after applying intended actor motion; world-space drift in a stationary preview can be expected. For traveling clips exclude intentional root displacement when comparing loop poses. Follow the structured cases in `evals/evals.json` when evaluating this skill.


# Bundled resources

The resources below belong to this skill. Split them into the indicated relative paths when using a folder-based skill loader.

## File: `references/sources.md`

````markdown
# Sources and evidence boundaries

Research date: 2026-10-01. Use pinned Blender 5.2 documentation, then the installed runtime's exact minor. These references establish API behavior, not a guarantee that a particular rig or exporter configuration was tested. Several page fetches were blocked; indexed official documentation excerpts were available. Do not claim full-page inspection for those sources.

- https://docs.blender.org/api/5.2/bpy_extras.anim_utils.html — Verified indexed signatures for action/slot channelbag lookup, ensure helper, and bake helpers. The lookup returns the first matching bag, not every layer/strip.
- https://developer.blender.org/docs/release_notes/5.0/python_api/ — Official migration reference for action channelbags; indexed result confirms helper approach. Inspect complete release notes when performing migrations.
- https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/ — Historical introduction and deprecated legacy action-curve access; do not copy pre-5.0 compatibility code as the current API.
- https://docs.blender.org/manual/es/5.2/addons/scene_gltf2.html — Retrieved indexed 5.2 manual export details: action association, slots, explicit animation modes and supported animated data. The localized page includes English technical text; check the equivalent language/version at task time.
- https://docs.blender.org/api/5.2/bpy.ops.export_scene.html — Official version-pinned exporter operator reference. Inspect available enums/defaults before invoking export.
- https://docs.blender.org/manual/sl/5.2/animation/constraints/tracking/ik_solver.html — Retrieved indexed IK chain, pole and evaluation notes; inspect constraints in the actual rig.
- https://docs.blender.org/api/5.2/bpy.types.KinematicConstraint.html — Version-pinned IK RNA reference.
- https://docs.blender.org/manual/en/5.2/index.html — Versioned manual entry point.

Rest-pose preservation, contact/loop measurement, rig separation and engine round-trip gates are workflow recommendations synthesized for game production. They are not promises of automatic retarget fidelity or official universal error budgets. Godot runtime code belongs in the Godot coding skill and requires its own version-matched API verification.
````

## File: `references/workflow.md`

````markdown
# Animation operations and acceptance

## Modern action inspection

Use the target runtime documentation before mutation. This read-only pattern locates the first relevant bag for one assigned action/slot; it is not an all-layers walker:

```python
from bpy_extras import anim_utils
ad = obj.animation_data
bag = anim_utils.action_get_channelbag_for_slot(
    ad.action if ad else None,
    ad.action_slot if ad else None,
)
curves = tuple(bag.fcurves) if bag else ()
```

The 5.2 helper explicitly accepts `None` for action or slot and returns `None`; missing animation data is therefore a valid read-only result.

For a shared action, identify all slot users before changing curves. Duplicate the intended source action only when the edit should be isolated; reassign the correct compatible slot. Validate all paths against their target ID, including shape-key data rather than assuming every path belongs to an Object. For a newly created clip prefer ordinary ID/keyframe workflows unless low-level curve construction is necessary. Query `action_ensure_channelbag_for_slot` only after explicitly creating/assigning the intended action and slot; an inspection pass must never ensure/create data.

## Retarget/bake sequence

1. Snapshot source rig, root motion and rest transforms. Resolve bone semantic mapping and unmatched bones.
2. Test one neutral pose, one deep bend and one contact pose before bulk conversion.
3. Retarget orientation in the proper parent/rest spaces; fit limb scale with contact constraints rather than arbitrary bone scaling.
4. Bake evaluated deformation onto an export skeleton or isolated actions. Preserve frame/subframe timing; record effective FPS = `fps / fps_base`.
5. Sample original and baked world matrices before clearing conversion constraints. Do not strip constraints from the only editable rig.
6. Validate contact segments, pelvis height, weapon/hand attachments and root yaw; inspect at slow playback and real speed.

## Clip manifest

Record per clip: source, license/provenance if supplied, action/slot targets, frame start/end, effective FPS, duration convention, loop, intended speed, displacement/yaw, root bone, contact/event times, bake step and export mode. Do not guess licenses from download availability.

For a loop sampled from frame 1 through 31 at 30 FPS, distinguish the 1-second endpoint interval from 31 stored samples. Decide whether the duplicate endpoint is retained by the exporter/engine; test actual playback rather than truncating every clip blindly.

## Measured acceptance

- Foot slip: for each plant interval report maximum world-space displacement after the intended actor trajectory is applied. Separate heel/toe roll from sole sliding.
- Loop error: compare corresponding joint rotations and root-relative poses at endpoints; inspect derivatives to catch velocity snaps even when poses coincide.
- Bake error: report maximum position/orientation difference on selected joints across sample times, plus the sample coverage.
- Engine round trip: expected versus actual clip names/count, duration, root path, unit scale and deform count. Check transition pairs with relevant gameplay speeds.

Thresholds are project decisions. If no character, runtime or target engine is available, deliver a reproducible verification recipe and mark those checks not run.
````

## File: `evals/evals.json`

````json
{
  "skill_name": "blender-animation-system",
  "evals": [
    {
      "id": 1,
      "prompt": "Blender 5.2 rigimde walk ve run aynı Action içindeki farklı slotları kullanıyor. Sadece karakter B yürüyüşündeki bilek eğrilerini düzelt; A karakterine dokunma.",
      "expected_output": "Isolated slot-aware edit and verification report.",
      "files": [],
      "assertions": [
        "Inspects assigned action and slot and shared users",
        "Does not use action.fcurves or slot zero by assumption",
        "Modifies only intended target and verifies other character unchanged"
      ]
    },
    {
      "id": 2,
      "prompt": "Bu mocap koşu klibini farklı boydaki karaktere retarget et. Godot için 30 FPS, root motionlu ve ayak kayması az olsun; kaynak rig kalsın.",
      "expected_output": "Retargeted editable source, baked export and measured contact/root report.",
      "files": [],
      "assertions": [
        "Establishes rest pose mapping, units, effective FPS and root convention",
        "Preserves source and validates baked evaluated poses",
        "Measures contacts after actor trajectory and explicitly checks target-engine import or labels it unrun"
      ]
    },
    {
      "id": 3,
      "prompt": "Blender 5.2 animasyon kitaplığındaki idle, turn ve jump GLB exportta eksik çıkıyor. Tüm klipleri doğru isim ve süreyle düzelt.",
      "expected_output": "Explicit animation-mode diagnosis, clip manifest and round-trip evidence.",
      "files": [],
      "assertions": [
        "Checks action association/slots/NLA before export",
        "Verifies installed exporter options instead of old NLA name-merging assumptions",
        "Checks actual clip count duration and root track after reimport"
      ]
    }
  ]
}
````

## File: `evals/trigger-evals.json`

````json
[
  {
    "query": "Blender animasyonumun IK pole flip sorununu çöz",
    "should_trigger": true
  },
  {
    "query": "Blender 5.2 action slot export hatasını düzelt",
    "should_trigger": true
  },
  {
    "query": "Godot AnimationTree state machine kodu yaz; Blender kullanmayacağız",
    "should_trigger": false
  },
  {
    "query": "Bu arabayı statik low poly modelle",
    "should_trigger": false
  }
]
````
