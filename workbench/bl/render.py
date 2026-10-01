"""Rendering: fast Workbench review (clay / material / x-ray), EEVEE/Cycles beauty, video.

Blender 5.2: engine ids 'BLENDER_WORKBENCH', 'BLENDER_EEVEE', 'CYCLES'.
Video: image_settings.media_type = 'VIDEO' then file_format = 'FFMPEG' (reset to 'IMAGE' after).
"""
import os
from contextlib import contextmanager

import bpy


def _world(color=(0.32, 0.33, 0.35)):
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new("WORLD_Review")
    sc.world.color = color


def _workbench_shading(mode, xray=False):
    sh = bpy.context.scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "SINGLE" if mode == "CLAY" else "MATERIAL"
    sh.single_color = (0.62, 0.62, 0.62)
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sh.show_shadows = False
    sh.show_object_outline = True
    sh.show_xray = xray
    bpy.context.scene.display.render_aa = "8"


def _still(path, rgba=False):
    im = bpy.context.scene.render.image_settings
    im.media_type = "IMAGE"
    im.file_format = "PNG"
    im.color_mode = "RGBA" if rgba else "RGB"
    bpy.context.scene.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)


def workbench(cam, path, mode="MATERIAL", transparent=False, res=None, xray=False):
    """mode CLAY (single grey) | MATERIAL (viewport colours). transparent -> RGBA (for overlays).
    res=None: the camera's own image size (reference cameras store the photo size in
    cam["wb_image_size"], so overlays can never be stretched - lesson 26), else 1080x720."""
    sc = bpy.context.scene
    if res is None:
        res = tuple(cam["wb_image_size"]) if "wb_image_size" in cam else (1080, 720)
    _world()
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    _workbench_shading(mode, xray)
    _still(path, transparent)


@contextmanager
def only(objs):
    """Render exactly `objs`: every other renderable object is hidden inside the block, restored after."""
    keep = {o.name for o in objs}
    hidden = [o for o in bpy.context.scene.objects
              if o.type in ("MESH", "CURVE", "SURFACE", "META", "FONT") and o.name not in keep and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    was = {o.name: o.hide_render for o in objs}
    for o in objs:
        o.hide_render = False
    try:
        yield
    finally:
        for o in hidden:
            o.hide_render = False
        for o in objs:
            o.hide_render = was[o.name]


def silhouette(cam, objs, path, res=None):
    """Alpha-only render of exactly `objs` from cam -> RGBA PNG (pipeline gates, silhouette.metrics)."""
    with only(objs):
        workbench(cam, path, "CLAY", transparent=True, res=res)
    return path


def read_alpha(path):
    """RGBA PNG -> float alpha array [v, u] (top row first) inside Blender (no PIL needed)."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[::-1, :, 3]


def write_rgb(arr, path):
    """uint8 (H, W, 3) array -> PNG inside Blender (no PIL needed)."""
    import numpy as np
    h, w = arr.shape[:2]
    img = bpy.data.images.new("TMP_write_rgb", w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.asarray(arr, np.float32)[::-1] / 255.0
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save()
    bpy.data.images.remove(img)
    return path


def review_set(cams, folder, tag, modes=("CLAY", "MATERIAL")):
    """Render every camera of a rig dict -> <folder>/<tag>_<CAM>_<mode>.png"""
    for n, cam in cams.items():
        res = (720, 720) if n in ("ORTHO_FRONT", "ORTHO_REAR") else (1080, 720)
        for m in modes:
            workbench(cam, os.path.join(folder, f"{tag}_{n}_{m.lower()}.png"), m, res=res)


def studio_lights(center=(0, 0, 0.5), size=2.0, strength=1.0):
    """3-point area lights (REVIEW_LIGHT_*) for EEVEE / Cycles beauty renders."""
    from mathutils import Vector
    from workbench.bl.cameras import look_at
    from workbench.bl.scene import coll
    c = Vector(center)
    d = size * 2.5
    for name, off, e in (("KEY", (-0.8, -0.8, 0.9), 1.5), ("FILL", (0.9, -0.6, 0.5), 0.6),
                         ("RIM", (0.0, 1.0, 0.8), 1.2)):
        n = "REVIEW_LIGHT_" + name
        ld = bpy.data.lights.get(n) or bpy.data.lights.new(n, "AREA")
        ld.energy = size * size * 150 * e * strength
        ld.size = size * 0.6
        ob = bpy.data.objects.get(n) or bpy.data.objects.new(n, ld)
        if ob.name not in coll("09_PRESENTATION").objects:
            coll("09_PRESENTATION").objects.link(ob)
        ob.location = c + Vector(off) * d
        look_at(ob, c)


def beauty(cam, path, res=(1600, 1000), samples=32, engine="BLENDER_EEVEE", transparent=False,
           world=(0.05, 0.05, 0.055)):
    """Material render with EEVEE (default) or CYCLES. Call studio_lights() first."""
    sc = bpy.context.scene
    _world(world)
    sc.camera = cam
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = samples
    else:
        sc.eevee.taa_render_samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = transparent
    _still(path, transparent)


def animation(cam, path_mp4, frame_start=1, frame_end=120, res=(1280, 720),
              engine="BLENDER_WORKBENCH", mode="MATERIAL", fps=30, samples=16):
    """Render a frame range straight to an H.264 MP4 (Workbench = fast previews)."""
    sc = bpy.context.scene
    if engine == "BLENDER_WORKBENCH":
        _world()
        _workbench_shading(mode)
    elif engine == "BLENDER_EEVEE":
        sc.eevee.taa_render_samples = samples
    sc.render.engine = engine
    sc.camera = cam
    sc.frame_start, sc.frame_end = frame_start, frame_end
    sc.render.fps = fps
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    im = sc.render.image_settings
    im.media_type = "VIDEO"
    im.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = path_mp4
    os.makedirs(os.path.dirname(path_mp4), exist_ok=True)
    bpy.ops.render.render(animation=True)
    im.media_type = "IMAGE"
