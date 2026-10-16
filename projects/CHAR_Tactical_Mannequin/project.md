# CHAR_Tactical_Mannequin

## Category / targets
character
budget key: character  (workbench.tables.BUDGETS: S1 < 1500, S2 8000-30000, max 40000, S3 < 60000, mats: 6)
targets: game (S4) | render (S3 + S5)   engine: godot (glTF 2.0 / GLB)

## Objective
Modular stylized-tactical 3D humanoid combat mannequin for an FPS game, inspired by high-end tactical crash-test dummies and modern combat robotics in A-pose. Fully rigid segmented body parts with zero cloth simulation, spherical ball joints at all major kinematic articulation points, high-contrast two-tone palette with dark charcoal matte under-suit and electric cobalt blue armor plates, and distinct 70m silhouette readability.

## Mode & Reference
- Mode: Original-design mode (per `blender-workbench-modeler.agent.md`).
- Inspiration: Electronic pop-up shooting range target dummy aesthetic (zone designations HEAD, TORSO, LIMBS, bevelled armor plates, rear telemetry/scoring unit with antenna and LED display).
- Reference camera / silhouette gates: Waived in original-design mode; geometry defined via exact parametric world-space coordinates in `landmarks.py` and `shapes.py`.

## Scale & measurements
- Scale: 1 unit = 1.0 metre.
- Key dimensions: W 1.325 m (A-pose arm span) x D 0.315 m (chest plate to back telemetry pack) x H 1.840 m (boot sole to helmet apex).
- Ground alignment: Lowest Z = 0.0000 m (boot soles).
- Proportions: 7.8 heads tall heroic tactical humanoid.

## Stage plan
| Stage | content | budget (tris) | result |
|-------|---------|---------------|--------|
| S1 PRIMITIVE | main masses, joint boxes, torso blocks | < 1500 | 528 tris (PASS) |
| S2 LOWPOLY (LOD0) | procedural capsules, armor plates, boots, helmet shell, wrap-around visor | 8000 - 30000 | 9,072 tris (PASS) |
| S3 DETAIL | beveled plate edges, tech pack antenna rod, weighted normals, hero assets | < 60000 | 9,072 tris (PASS) |
| S4 GAME | LOD0-2 glb (9072 / 4536 / 2267 tris), 5 Godot convex colliders, 14 joint pivots | auto | PASS |

## Part breakdown (registry parts.PARTS)
| Part key | prim builder | real builder | collision | moving? |
|----------|--------------|--------------|-----------|---------|
| head | `head_prim` | `head_mesh` (helmet shell, inner skull, visor, neck collar, neck ball) | box | Yes (Neck pivot: `(0, 0, 1.53)`) |
| torso | `torso_prim` | `torso_mesh` (core box, chest plate, back plate, mid plate, tech pack, antenna, waist ball, pelvis) | box | Yes (Waist pivot: `(0, 0, 1.15)`) |
| arms | `arms_prim` | `arms_mesh` (shoulder ball, pauldron plate, upper arm capsule, bicep plate, elbow ball, elbow guard, forearm capsule, bracer plate, wrist ball, robotic hand) | hull | Yes (Shoulders, elbows, wrists) |
| legs | `legs_prim` | `legs_mesh` (hip ball, thigh capsule, thigh plate, knee ball, knee cap, shin capsule, shin guard, ankle ball) | hull | Yes (Hips, knees, ankles) |
| boots | `boots_prim` | `boots_mesh` (lugged tactical combat boot chassis, tread sole, composite steel toe cap) | box | No (rigid to foot) |

## Joint Pivots (PIVOTS registry)
- `HEAD_NeckJoint`: `(0.0, 0.0, 1.53)`
- `TORSO_WaistJoint`: `(0.0, 0.0, 1.15)`
- `ARM_ShoulderJoint_L/R`: `(±0.25, 0.0, 1.45)`
- `ARM_ElbowJoint_L/R`: `(±0.43, 0.01, 1.20)`
- `ARM_WristJoint_L/R`: `(±0.57, -0.03, 0.94)`
- `LEG_HipJoint_L/R`: `(±0.125, 0.0, 0.94)`
- `LEG_KneeJoint_L/R`: `(±0.15, -0.01, 0.52)`
- `LEG_AnkleJoint_L/R`: `(±0.17, 0.0, 0.18)`

## Deliverables
- Milestone scenes: `output/CHAR_Tactical_Mannequin/blend/CHAR_Tactical_Mannequin_S0_SETUP.blend` ... `_S4_GAME.blend`
- Hero Blend & GLB: `output/CHAR_Tactical_Mannequin/blend/CHAR_Tactical_Mannequin.blend`, `output/CHAR_Tactical_Mannequin/glb/CHAR_Tactical_Mannequin_hero.glb`
- Game GLBs: `output/CHAR_Tactical_Mannequin/glb/CHAR_Tactical_Mannequin_LOD0.glb`, `_LOD1.glb`, `_LOD2.glb`
- Presentation renders: `output/CHAR_Tactical_Mannequin/presentation/clay_sheet.png`, `studio_dark_sheet.png`
- Quality gate report: `projects/CHAR_Tactical_Mannequin/report.json`
