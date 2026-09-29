"""
Presentation studio: a professional, asset-agnostic stage for reviewing, presenting and rendering
any model (vehicle, building, character, prop). Everything scales from the asset's bounding box,
so the same call works for a 0.3 m bottle and a 30 m building.

    from workbench.bl import presentation as pres
    st = pres.studio(objs, style="studio_dark")          # bowl cyclorama + lights + world + colour
    cams = pres.hero_cameras(objs)                        # auto-framed hero / side / front / rear / top
    pres.render_stills(cams, folder, engine="CYCLES", samples=192)
    pres.turntable_video(objs, path_mp4, seconds=8)       # EEVEE 360 deg orbit

What is in the stage (all objects prefixed PRES_ in collection 09_PRESENTATION, never exported):
  * PRES_Cyclorama  - seamless 360 deg "bowl": flat floor -> cove -> wall. No horizon line from ANY
                      camera angle (turntable-safe). Floor z = -0.5 mm (no z-fighting at the tyres).
  * PRES_Light_*    - KEY softbox (front-3/4 high), TOP light bank (long overhead strip that draws the
                      reflection line along car paint), RIM_L / RIM_R strips (edge separation from
                      the background), FILL (large, dim, camera side), KICKER (low front bounce).
                      Energies scale with distance^2, so exposure is size-independent.
                      Soft boxes use full spread (180 deg): a narrower cone draws a hard-edged pool
                      on the floor that shows up in reverse shots.
  * World           - dim neutral ambient; AgX view transform + contrast look per style.
  * Clay            - style "clay" swaps the ASSET's materials for grey clay via object-linked slots
                      (clay_override(objs, False) restores them); the stage keeps its own floor.
Styles: studio_dark (charcoal glossy floor, car-launch look), studio_light (bright product shot),
        neutral_grey (mid grey, honest material review), clay (neutral stage + grey clay on the asset).
Engines: CYCLES (GPU OptiX/CUDA auto, denoised, finals) or BLENDER_EEVEE (raytraced, fast/video).
"""
import math
import os
import bpy
import bmesh
from mathutils import Vector, Matrix

from workbench.bl.scene import coll
from workbench.bl import cameras

C = "09_PRESENTATION"

STYLES = {
    # floor/wall/world colours, AgX look, exposure (EV), power = global light multiplier
    "studio_dark":  dict(floor=(0.012, 0.012, 0.013), floor_rough=0.42, wall=(0.010, 0.010, 0.011),
                         world=(0.018, 0.019, 0.021), world_strength=1.0,
                         look="AgX - Medium High Contrast", exposure=0.0, power=1.0),
    "studio_light": dict(floor=(0.62, 0.62, 0.63), floor_rough=0.55, wall=(0.70, 0.70, 0.71),
                         world=(0.55, 0.56, 0.58), world_strength=0.6,
                         look="AgX - Base Contrast", exposure=-0.6, power=0.8),
    "neutral_grey": dict(floor=(0.18, 0.18, 0.185), floor_rough=0.5, wall=(0.20, 0.20, 0.205),
                         world=(0.20, 0.21, 0.22), world_strength=0.8,
                         look="AgX - Base Contrast", exposure=0.0, power=0.9),
}
STYLES["clay"] = dict(STYLES["neutral_grey"], clay=True, power=0.8, exposure=-1.0,
                      look="AgX - Medium High Contrast")
EEVEE_EV = 1.0      # EEVEE misses most of the diffuse bounce inside the dark bowl: +1 EV to match Cycles

# light rig: name -> (azimuth deg from front (-Y) towards the RIGHT side (-X), elevation deg,
#                     distance k, size_x k, size_y k, relative irradiance, rgb, spread deg)
LIGHTS = {
    "KEY":    (-35.0, 42.0, 2.2, 1.30, 0.90, 0.75, (1.00, 0.97, 0.93), 180.0),
    "TOP":    (0.0, 90.0, 1.6, 0.35, 1.50, 0.80, (1.00, 1.00, 1.00), 180.0),
    "RIM_L":  (-140.0, 28.0, 2.0, 0.10, 1.30, 1.10, (0.93, 0.96, 1.00), 70.0),
    "RIM_R":  (140.0, 28.0, 2.0, 0.10, 1.30, 1.10, (0.93, 0.96, 1.00), 70.0),
    "FILL":   (70.0, 18.0, 2.6, 1.80, 1.20, 0.22, (0.94, 0.97, 1.00), 180.0),
    "KICKER": (10.0, 4.0, 2.4, 1.40, 0.25, 0.12, (1.00, 0.98, 0.95), 140.0),
}

# lights that must not touch the cyclorama (light linking): the overhead bank would otherwise be
# mirrored by the glossy floor as a hard white rectangle in low / rear shots.
FLOOR_EXCLUDED = ("TOP",)

# camera presets: name -> (azimuth deg, elevation deg, lens mm, margin, resolution)
SHOTS = {
    "HERO_FRONT_34": (38.0, 9.0, 70.0, 0.07, (1920, 1080)),
    "HERO_REAR_34":  (-148.0, 13.0, 70.0, 0.07, (1920, 1080)),
    "SIDE":          (90.0, 2.0, 105.0, 0.06, (1920, 1080)),
    "FRONT":         (0.0, 6.0, 85.0, 0.09, (1920, 1080)),
    "TOP_34":        (-30.0, 38.0, 55.0, 0.07, (1920, 1080)),
    "LOW_DRAMA":     (25.0, 2.5, 35.0, 0.05, (1920, 1080)),
}


# ----------------------------------------------------------------------------- helpers
def direction(az_deg, el_deg):
    """unit vector from the asset towards the viewer. az 0 = front (-Y), +90 = right side (-X)."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def asset_points(objs, max_pts=6000):
    """world-space evaluated vertices (subsampled) of the asset meshes - used for tight framing."""
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type not in ("MESH", "FONT", "CURVE"):
            continue
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        n = len(me.vertices)
        step = max(1, n // max(1, max_pts // max(1, len(objs))))
        mw = o.matrix_world
        pts += [mw @ me.vertices[i].co for i in range(0, n, step)]
        eo.to_mesh_clear()
    return pts


def bounds(objs):
    pts = asset_points(objs, 3000)
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def _clear():
    for ob in [o for o in bpy.data.objects if o.name.startswith("PRES_")]:
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)


def _material(name, rgb, rough, metallic=0.0, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    m.diffuse_color = (*rgb, 1.0)
    m.roughness = rough
    return m


# ----------------------------------------------------------------------------- stage parts
def cyclorama(center, L, floor_rgb, floor_rough, wall_rgb, segs=96):
    """360 deg seamless bowl: flat floor radius 3L, quarter-circle cove radius 1.4L, wall 4L high.
    Floor vertex colours are not used; a second material on the wall/cove keeps the floor
    reflective and the wall matte (reads as infinite background)."""
    R0, rc, Hw = 3.0 * L, 1.4 * L, 4.0 * L
    prof = [(0.0, 0.0)]
    prof += [(R0 * t, 0.0) for t in (0.25, 0.5, 0.75, 1.0)]
    prof += [(R0 + rc * math.sin(math.pi / 2 * i / 10), rc * (1 - math.cos(math.pi / 2 * i / 10)))
             for i in range(1, 11)]
    prof += [(R0 + rc, rc + (Hw - rc) * t) for t in (0.33, 0.66, 1.0)]
    bm = bmesh.new()
    cx, cy = center.x, center.y
    center_v = bm.verts.new((cx, cy, -0.0005))
    rings = []
    for (r, z) in prof[1:]:
        rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * k / segs),
                                    cy + r * math.sin(2 * math.pi * k / segs), z - 0.0005))
                      for k in range(segs)])
    for k in range(segs):
        bm.faces.new((center_v, rings[0][k], rings[0][(k + 1) % segs]))
    for i in range(len(rings) - 1):
        for k in range(segs):
            f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % segs], rings[i][(k + 1) % segs]))
            f.material_index = 0 if i < 3 else 1
    for f in bm.faces:
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:                      # normals must point UP / inwards (towards the asset)
        if (f.calc_center_median() - Vector((cx, cy, Hw))).dot(f.normal) > 0:
            f.normal_flip()
    me = bpy.data.meshes.new("PRES_Cyclorama_Mesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("PRES_Cyclorama", me)
    coll(C).objects.link(ob)
    me.materials.append(_material("PRES_MAT_Floor", floor_rgb, floor_rough, spec=0.35))
    me.materials.append(_material("PRES_MAT_Wall", wall_rgb, 0.9, spec=0.2))
    ob["presentation"] = True
    return ob


def light(name, target, az, el, dist, size_x, size_y, irradiance, rgb, spread):
    """area light looking at target; power scales with distance^2 (size-independent exposure)."""
    d = direction(az, el)
    ld = bpy.data.lights.new("PRES_Light_" + name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size_x, size_y
    ld.color = rgb
    ld.energy = irradiance * 5.0 * dist * dist
    if hasattr(ld, "spread"):
        ld.spread = math.radians(spread)
    ob = bpy.data.objects.new("PRES_Light_" + name, ld)
    ob.visible_camera = False                 # softboxes light + reflect, never appear as white cards
    coll(C).objects.link(ob)
    ob.location = Vector(target) + d * dist
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
    if el > 80:                               # overhead bank: long axis along the asset (Y)
        ob.rotation_euler = (0.0, 0.0, 0.0)
    return ob


def exclude_from_floor(light_obs, cyc):
    """light linking: these lights light the asset but not the cyclorama (Cycles + EEVEE)."""
    if not light_obs:
        return
    lc = bpy.data.collections.get("PRES_LightLink_NoFloor") or bpy.data.collections.new("PRES_LightLink_NoFloor")
    for o in list(lc.objects):
        lc.objects.unlink(o)
    lc.objects.link(cyc)
    for lo in light_obs:
        lo.light_linking.receiver_collection = lc
    for e in lc.collection_objects:
        e.light_linking.link_state = "EXCLUDE"


def colour_management(look, exposure=0.0):
    vs = bpy.context.scene.view_settings
    vs.view_transform = "AgX"
    try:
        vs.look = look
    except TypeError:
        vs.look = "None"
    vs.exposure = exposure
    vs.gamma = 1.0
    bpy.context.scene["pres_eevee_ev"] = False


def world(rgb, strength):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("PRES_World") or bpy.data.worlds.new("PRES_World")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*rgb, 1.0)
    bg.inputs["Strength"].default_value = strength
    w.color = rgb
    sc.world = w
    return w


def clay_override(objs, enable=True, rgb=(0.40, 0.40, 0.41)):
    """grey clay on the ASSET only (object-linked material slots, reversible): shape review against
    the style's own floor, so the object keeps contrast with the stage."""
    m = _material("PRES_MAT_Clay", rgb, 0.5, spec=0.4) if enable else None
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if enable:
                slot.link = "OBJECT"
                slot.material = m
            else:
                slot.material = None
                slot.link = "DATA"
    return m


def studio(objs, style="studio_dark", light_scale=1.0, hide_review_lights=True):
    """Build (idempotently) the whole stage around objs. Returns a dict with the pieces."""
    s = STYLES[style]
    _clear()
    coll(C)
    mn, mx = bounds(objs)
    ctr = (mn + mx) / 2
    size = mx - mn
    L = max(size.x, size.y, size.z)
    tgt = Vector((ctr.x, ctr.y, mn.z + 0.45 * size.z))
    cyc = cyclorama(Vector((ctr.x, ctr.y, 0.0)), L, s["floor"], s["floor_rough"], s["wall"])
    lights = {}
    for n, (az, el, dk, sxk, syk, irr, rgb, spread) in LIGHTS.items():
        lights[n] = light(n, tgt, az, el, dk * L, sxk * L, syk * L, irr * s["power"] * light_scale, rgb, spread)
    exclude_from_floor([lights[n] for n in FLOOR_EXCLUDED if n in lights], cyc)
    if hide_review_lights:
        for o in bpy.data.objects:
            if o.name.startswith("REVIEW_LIGHT_"):
                o.hide_render = True
    world(s["world"], s["world_strength"])
    colour_management(s["look"], s["exposure"])
    if s.get("clay"):
        clay_override(objs, True)
    return dict(cyclorama=cyc, lights=lights, center=ctr, target=tgt, size=size, L=L, style=style)


# ----------------------------------------------------------------------------- cameras
def frame(cam, pts, target, margin=0.07, res=(1920, 1080), iters=12):
    """move cam along its view axis + set lens shift so pts fill the frame with `margin` on the
    tightest side (perspective-correct, uses the real projection)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    aspect = res[1] / res[0]
    cam.data.shift_x = cam.data.shift_y = 0.0
    for _ in range(iters):
        bpy.context.view_layer.update()
        ps = [world_to_camera_view(sc, cam, p) for p in pts]
        xs, ys = [p.x for p in ps], [p.y for p in ps]
        ex, ey = max(xs) - min(xs), max(ys) - min(ys)
        need = max(ex / (1 - 2 * margin), ey / (1 - 2 * margin))
        view = (cam.location - Vector(target))
        cam.location = Vector(target) + view * need
        cam.data.shift_x += ((min(xs) + max(xs)) / 2 - 0.5)
        cam.data.shift_y += ((min(ys) + max(ys)) / 2 - 0.5) * aspect
        if abs(need - 1) < 0.002:
            break
    return cam


def shot(name, objs_pts, target, az, el, lens, margin=0.07, res=(1920, 1080), L=4.0):
    d = direction(az, el)
    cam = cameras.make("PRES_CAM_" + name, Vector(target) + d * L * 3, (0, 0, 0), lens=lens, collection=C)
    cam.data.clip_start = 0.01 * L
    cam.data.clip_end = 60.0 * L
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    frame(cam, objs_pts, target, margin, res)
    cam["resolution"] = list(res)
    return cam


def hero_cameras(objs, shots=None):
    """auto-framed presentation cameras (SHOTS presets). Returns {name: camera}."""
    pts = asset_points(objs)
    mn, mx = bounds(objs)
    size = mx - mn
    tgt = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.4 * size.z))
    L = max(size)
    out = {}
    for n, (az, el, lens, margin, res) in (SHOTS if shots is None else shots).items():
        out[n] = shot(n, pts, tgt, az, el, lens, margin, res, L)
    return out


# ----------------------------------------------------------------------------- rendering
def use_gpu():
    """Cycles on the best GPU (OptiX > CUDA > HIP > oneAPI > Metal); CPU fallback. Returns device."""
    sc = bpy.context.scene
    try:
        cp = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        sc.cycles.device = "CPU"
        return "CPU"
    for t in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            cp.compute_device_type = t
        except TypeError:
            continue
        cp.get_devices()
        gpus = [d for d in cp.devices if d.type == t]
        if gpus:
            for d in cp.devices:
                d.use = d.type == t
            sc.cycles.device = "GPU"
            return t
    sc.cycles.device = "CPU"
    return "CPU"


def setup_engine(engine="CYCLES", samples=192):
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.film_transparent = False
    if engine == "CYCLES":
        if sc.get("pres_eevee_ev"):
            sc.view_settings.exposure -= EEVEE_EV
            sc["pres_eevee_ev"] = False
        dev = use_gpu()
        c = sc.cycles
        c.samples = samples
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.01
        c.use_denoising = True
        c.denoiser = "OPTIX" if dev == "OPTIX" else "OPENIMAGEDENOISE"
        c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 10, 4, 6
        c.transmission_bounces, c.transparent_max_bounces = 8, 16
        c.caustics_reflective = c.caustics_refractive = False
        c.sample_clamp_indirect = 8.0
        c.blur_glossy = 0.5
        return dev
    if not sc.get("pres_eevee_ev"):
        sc.view_settings.exposure += EEVEE_EV
        sc["pres_eevee_ev"] = True
    e = sc.eevee
    e.taa_render_samples = samples
    for k, v in (("use_raytracing", True), ("use_shadows", True), ("use_fast_gi", True),
                 ("shadow_ray_count", 2), ("shadow_step_count", 8)):
        if hasattr(e, k):
            setattr(e, k, v)
    return "EEVEE"


def still(cam, path, res=None):
    sc = bpy.context.scene
    sc.camera = cam
    r = res or tuple(cam.get("resolution", (1920, 1080)))
    sc.render.resolution_x, sc.render.resolution_y = r
    sc.render.resolution_percentage = 100
    im = sc.render.image_settings
    im.media_type = "IMAGE"
    im.file_format = "PNG"
    im.color_mode = "RGB"
    im.color_depth = "8"
    sc.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return path


def render_stills(cams, folder, tag="", engine="CYCLES", samples=192, res=None):
    """render every camera -> <folder>/<tag><NAME>.png ; returns the paths."""
    setup_engine(engine, samples)
    return [still(cam, os.path.join(folder, f"{tag}{n.lower()}.png"), res) for n, cam in cams.items()]


def turntable_video(objs, path_mp4, seconds=8, fps=30, el=12.0, lens=60.0, res=(1920, 1080),
                    engine="BLENDER_EEVEE", samples=32):
    """360 deg orbit around the asset (camera moves, studio + lights stay: reflections travel over
    the paint like in a real studio). Linear, loops seamlessly."""
    from workbench.bl import anim
    from workbench.bl.scene import empty
    pts = asset_points(objs)
    mn, mx = bounds(objs)
    size = mx - mn
    tgt = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.4 * size.z))
    # frame for the worst case (the diagonal) then fix the radius for the whole orbit
    cam = shot("TURNTABLE", pts, tgt, 45.0, el, lens, 0.06, res, max(size))
    radius_vec = cam.location - tgt
    sx, sy = cam.data.shift_x, cam.data.shift_y
    pivot = bpy.data.objects.get("PRES_TurntablePivot") or empty("PRES_TurntablePivot", tgt, C, "PLAIN_AXES", 0.2)
    pivot.location = tgt
    pivot.rotation_euler = (0, 0, 0)
    pivot.animation_data_clear()
    mw = cam.matrix_world.copy()
    cam.parent = pivot
    cam.matrix_parent_inverse = pivot.matrix_world.inverted()
    cam.matrix_world = mw
    cam.data.shift_x, cam.data.shift_y = 0.0, sy
    n = int(seconds * fps)
    anim.key(pivot, 1, rot=(0, 0, 0))
    anim.key(pivot, n + 1, rot=(0, 0, 2 * math.pi))
    anim.set_interpolation(pivot, "LINEAR")
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, n
    sc.render.fps = fps
    setup_engine(engine, samples)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
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
    return path_mp4
