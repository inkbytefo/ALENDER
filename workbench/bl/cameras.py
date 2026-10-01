"""Cameras: reference-photo match camera, orthographic review rig, perspective views.

Rotation conventions (verified in Blender 5.2):
  looking +X  = euler (90deg, roll, -90deg)      looking -X = (90, roll, 90)
  looking +Y  = (90, 0, 0)                        looking -Y = (90, 0, 180)
  top view with front (-Y) on image right = (0, 0, -90)
"""
import math
import bpy
from mathutils import Vector
from workbench.bl.scene import coll

R90 = math.radians(90.0)


def make(name, loc, rot, ortho_scale=None, lens=50.0, collection="09_PRESENTATION"):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    if ortho_scale:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho_scale
    else:
        cd.type = "PERSP"
        cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cd.clip_end = 200.0
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
        coll(collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def reference_camera(ref, anchors, res=None, distance=7.0, name="CAM_REFERENCE"):
    """Perspective camera reproducing a side or top reference photo.
    ref: RefMap; anchors: [((x,y,z) world, (u,v) px), ...] (>= 2, e.g. both axles).
    A long lens at `distance` keeps perspective mild; the roll sign is chosen by reprojection
    error, stored in cam['anchor_reprojection_error_px'] (expect < 2 px)."""
    from bpy_extras.object_utils import world_to_camera_view
    W, H = res or ref.image_size
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = W, H
    cam_size = (int(W), int(H))

    if getattr(ref, "view", "SIDE") in ("TOP", "CALIBRATED"):
        lens = getattr(ref, "lens", 36.0 * distance / (W / ref.S))
        loc = getattr(ref, "cam_loc", (0.0, 0.0, distance))
        rot = getattr(ref, "cam_rot", (0.0, 0.0, math.radians(180.0)))
        cam = make(name, loc, rot, lens=lens, collection="00_REFERENCE")
        cam["wb_image_size"] = cam_size
        bpy.context.view_layer.update()
        err = 0.0
        for p, px in anchors:
            c = world_to_camera_view(sc, cam, Vector(p))
            err += math.hypot(c.x * W - px[0], (1 - c.y) * H - px[1])
        cam["anchor_reprojection_error_px"] = round(err / max(1, len(anchors)), 2)
        return cam

    ortho = getattr(ref, "ortho", False)               # landmarks: REF.ortho = True for orthographic drawings
    lens = 36.0 * distance / (W / ref.S)
    cy, cz = ref.P(W / 2.0, H / 2.0)
    side = -1.0 if ref.sign > 0 else 1.0          # front on image right -> camera at -X
    yaw = -R90 if side < 0 else R90
    cam = make(name, (side * distance, cy, cz), (R90, 0.0, yaw), lens=lens, collection="00_REFERENCE",
               ortho_scale=(W / ref.S) if ortho else None)
    cam["wb_image_size"] = cam_size
    best = None
    for sgn in (1, -1):
        cam.rotation_euler = (R90, sgn * ref.theta, yaw)
        bpy.context.view_layer.update()
        err = 0.0
        for p, px in anchors:
            c = world_to_camera_view(sc, cam, Vector(p))
            err += math.hypot(c.x * W - px[0], (1 - c.y) * H - px[1])
        if best is None or err < best[0]:
            best = (err, sgn)
    cam.rotation_euler = (R90, best[1] * ref.theta, yaw)
    bpy.context.view_layer.update()
    cam["anchor_reprojection_error_px"] = round(best[0] / max(1, len(anchors)), 2)
    return cam


def reference_image(ref, path, cam, name="REF_PHOTO", depth=0.6):
    """Viewport-only image empty aligned with the reference camera (GUI inspection)."""
    img = bpy.data.images.load(path, check_existing=True)
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    ob.empty_display_type = "IMAGE"
    ob.data = img
    ob.empty_display_size = ref.image_size[0] / ref.S
    ob.empty_image_offset = (-0.5, -0.5)
    if getattr(ref, "view", "SIDE") == "CALIBRATED":
        # A viewport image plane at a chosen camera-space distance. It does not
        # assert a physical depth for any photographed part.
        ob.empty_display_size = 36.0 * depth / cam.data.lens
        ob.location = cam.matrix_world @ Vector((0.0, 0.0, -depth))
    elif getattr(ref, "view", "SIDE") == "TOP":
        ob.location = (cam.location.x, cam.location.y, -depth)
    else:
        cy, cz = ref.P(ref.image_size[0] / 2.0, ref.image_size[1] / 2.0)
        ob.location = (depth if ref.sign > 0 else -depth, cy, cz)
    ob.rotation_euler = cam.rotation_euler.copy()
    ob.empty_image_side = "FRONT"
    ob.hide_render = True
    if ob.name not in coll("00_REFERENCE").objects:
        coll("00_REFERENCE").objects.link(ob)
    return ob


def review_rig(center=(0, 0, 0.55), length=2.4, width=1.3, dist=6.0, persp=True):
    """ORTHO_LEFT/RIGHT/FRONT/REAR/TOP + CAM_PERSPECTIVE / CAM_PERSPECTIVE_L.
    length = ortho scale of side/top views, width = ortho scale of front/rear views.
    Make them ~15% larger than the asset (or use rig_from_bounds)."""
    cx, cy, cz = center
    specs = {
        "ORTHO_LEFT":  ((cx + dist, cy, cz), (R90, 0, R90), length),
        "ORTHO_RIGHT": ((cx - dist, cy, cz), (R90, 0, -R90), length),
        "ORTHO_FRONT": ((cx, cy - dist, cz), (R90, 0, 0), width),
        "ORTHO_REAR":  ((cx, cy + dist, cz), (R90, 0, math.radians(180)), width),
        "ORTHO_TOP":   ((cx, cy, cz + dist), (0, 0, -R90), length),
    }
    cams = {n: make(n, loc, rot, ortho_scale=s) for n, (loc, rot, s) in specs.items()}
    if persp:
        k = length / 2.4
        cams["CAM_PERSPECTIVE"] = look_at(
            make("CAM_PERSPECTIVE", (cx - 2.45 * k, cy - 2.2 * k, cz + 0.7 * k), (0, 0, 0), lens=50),
            (cx, cy + 0.05 * k, cz - 0.05))
        cams["CAM_PERSPECTIVE_L"] = look_at(
            make("CAM_PERSPECTIVE_L", (cx + 2.35 * k, cy + 2.15 * k, cz + 0.7 * k), (0, 0, 0), lens=50),
            (cx, cy, cz - 0.05))
    return cams


def world_bounds(objs):
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def rig_from_bounds(objs, margin=1.15):
    """review_rig sized from the combined world bbox of objs."""
    mn, mx = world_bounds(objs)
    d = mx - mn
    c = (mn + mx) / 2
    return review_rig((c.x, c.y, c.z), max(d.y, d.z) * margin, max(d.x, d.z) * margin)
