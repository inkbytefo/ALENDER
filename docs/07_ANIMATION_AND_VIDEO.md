# 07 — Animation and video

## Principles
- 30 fps default. One Action per clip: `idle-loop`, `walk-loop`, `door_open`, `wheel_spin-loop`
  (`-loop`/`-cycle` suffix = loop in Godot). `anim.name_action(ob, name)` sets fake user.
- Loops end on the start pose. Mechanical motion LINEAR (`anim.set_interpolation(ob, "LINEAR")`),
  organic motion BEZIER with anticipation / follow-through / ease.
- Pivots first: an object only rotates correctly if its origin is the pivot (wheel = axle,
  door = hinge, steering = steering axis). Set origins in Stage 2 (`scene.set_origin`).
- Bake constraints/IK before glTF export; export with `export.glb(objs, path, animations=True, skins=True)`.

## Library
```python
anim.key(ob, frame, loc=..., rot=..., scale=...)       # raw keys
anim.spin(wheel, "X", turns=3, frames=(1, 90), name="wheel_spin-loop")
anim.move(ob, [(1, p0), (60, p1)], "BEZIER", name="drive_in")
cam, pivot = anim.turntable(center, radius, height, frames=(1, 240))   # 360° orbit, linear
rig.pose_key(arm, frame, {"LeftUpperArm": (0, -1.0, 0)})             # pose keys on bones
```

## Video
```python
render.animation(cam, paths.out(A, "video", "turntable.mp4"), 1, 240, (1920, 1080),
                 engine="BLENDER_WORKBENCH" | "BLENDER_EEVEE" | "CYCLES", mode="MATERIAL")
```
- Blender 5.x: `image_settings.media_type = "VIDEO"` + `file_format = "FFMPEG"`, H.264 MP4.
- Previews with Workbench (seconds), finals with EEVEE (`studio_lights()` first). Cycles only for
  stills or short shots — time scales with samples × frames.
- Review: render a contact sheet of every Nth frame (render stills at those frames + `wb.py sheet`)
  and check first/last frame equality for loops.

## Typical deliverables
- product turntable (8 s, 240 frames), wheel spin loop, door/hood open clips, walk/idle cycles,
  camera fly-through for architecture (keyframed camera path with `anim.move` + `cameras.look_at`
  via a Track To constraint if needed).
