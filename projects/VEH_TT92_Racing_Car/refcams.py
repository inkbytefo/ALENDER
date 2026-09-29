"""
Reference cameras for VEH_TT92_Racing_Car.

  CAM_REFERENCE  orthographic TOP camera reproducing ref/REAL_REFERENCE.png (front = image top):
                 1 px = 1/S m on the ground plane, image centre = photo centre.
  CAM_OBLIQUE    perspective camera fitted to ref/REF_OBLIQUE.png from OBLIQUE_ANCHORS
                 (landmarks.py) by Levenberg-Marquardt on the reprojection error (if anchors exist).
"""
import math
import os
import bpy
import numpy as np
from mathutils import Vector, Euler

import landmarks as L
from workbench.bl import cameras
from workbench.bl.scene import coll


def top_camera():
    W, H = L.IMAGE_SIZE
    cx, cy = L.X(W / 2.0), L.Y(H / 2.0)
    cam = cameras.make("CAM_REFERENCE", (cx, cy, 10.0), (0.0, 0.0, math.pi), ortho_scale=W / L.S,
                       collection="00_REFERENCE")
    cam.data.clip_end = 30.0
    return cam


def top_image(path):
    img = bpy.data.images.load(path, check_existing=True)
    ob = bpy.data.objects.get("REF_PHOTO") or bpy.data.objects.new("REF_PHOTO", None)
    ob.empty_display_type = "IMAGE"
    ob.data = img
    W, H = L.IMAGE_SIZE
    ob.empty_display_size = max(W, H) / L.S
    ob.empty_image_offset = (-0.5, -0.5)
    ob.location = (L.X(W / 2.0), L.Y(H / 2.0), -0.002)
    ob.rotation_euler = (0.0, 0.0, math.pi)
    ob.hide_render = True
    if ob.name not in coll("00_REFERENCE").objects:
        coll("00_REFERENCE").objects.link(ob)
    return ob


# ------------------------------------------------------------------ oblique camera fit
def _project(params, pts, W, H):
    """params = loc(3), euler(3), lens(1); returns Nx2 pixel coords (numpy)."""
    loc = Vector(params[:3])
    R = Euler(params[3:6], "XYZ").to_matrix()
    Rt = np.array(R).T
    P = (np.asarray(pts) - np.array(loc)) @ Rt.T          # camera space (x right, y up, -z fwd)
    f = params[6] / 36.0 * W                               # sensor 36 mm horizontal
    u = W / 2 + f * P[:, 0] / -P[:, 2]
    v = H / 2 - f * P[:, 1] / -P[:, 2]
    return np.stack([u, v], 1)


def _depth_ok(params, pts):
    loc = np.array(params[:3])
    R = np.array(Euler(params[3:6], "XYZ").to_matrix())
    return bool(((np.asarray(pts) - loc) @ R)[:, 2].max() < -0.2)


def fit_oblique(anchors, W, H, x0):
    pts = [a[0] for a in anchors]
    px = np.array([a[1] for a in anchors], float)
    p = np.array(x0, float)
    lam = 1e-2

    def res(q):
        return (_project(q, pts, W, H) - px).ravel()
    r = res(p)
    for it in range(400):
        J = np.zeros((r.size, p.size))
        for j in range(p.size):
            d = np.zeros(p.size)
            d[j] = 1e-5 if j < 6 else 1e-3
            J[:, j] = (res(p + d) - r) / d[j]
        A = J.T @ J
        g = J.T @ r
        step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
        r2 = res(p + step)
        if (r2 ** 2).sum() < (r ** 2).sum():
            p, r, lam = p + step, r2, lam * 0.4
            if np.abs(step).max() < 1e-7:
                break
        else:
            lam *= 4.0
    err = np.sqrt((r.reshape(-1, 2) ** 2).sum(1))
    return p, err


def _starts(target=(0.0, 0.0, 0.3)):
    """multi-start initial guesses: positions around the car, looking at it, 12 rolls, 3 lenses."""
    from mathutils import Matrix
    t = Vector(target)
    for ang in range(0, 360, 30):
        for dist, h in ((3.0, 2.5), (4.5, 3.5), (6.0, 5.0)):
            loc = t + Vector((dist * math.cos(math.radians(ang)), dist * math.sin(math.radians(ang)), h))
            q = (t - loc).to_track_quat("-Z", "Y")
            for roll in range(0, 360, 30):
                R = q.to_matrix() @ Matrix.Rotation(math.radians(roll), 3, "Z")
                e = R.to_euler("XYZ")
                for lens in (35.0, 60.0):
                    yield [loc.x, loc.y, loc.z, e.x, e.y, e.z, lens]


def oblique_camera():
    anchors = getattr(L, "OBLIQUE_ANCHORS", None)
    if not anchors:
        return None
    W, H = L.OBLIQUE_SIZE
    ranked = sorted(((np.sqrt(((_project(np.array(x0), np.array([a[0] for a in anchors]), W, H)
                                 - np.array([a[1] for a in anchors], float)) ** 2).sum(1)).mean(), x0)
                     for x0 in _starts() if _depth_ok(x0, [a[0] for a in anchors])),
                    key=lambda c: c[0] if np.isfinite(c[0]) else 1e9)[:25]
    p, err = None, None
    for _, x0 in ranked:
        q, e = fit_oblique(anchors, W, H, x0)
        # camera must look at the car from above (points in front of it)
        if np.isfinite(e).all() and _depth_ok(q, [a[0] for a in anchors]) and (err is None or e.mean() < err.mean()):
            p, err = q, e
    cam = cameras.make("CAM_OBLIQUE", tuple(p[:3]), tuple(p[3:6]), lens=float(p[6]), collection="00_REFERENCE")
    cam["fit_error_px_mean"] = float(err.mean())
    cam["fit_error_px_max"] = float(err.max())
    print("[REFCAM] oblique fit: loc %s rot %s lens %.1f  err mean %.1f max %.1f px" %
          (np.round(p[:3], 3), np.round(np.degrees(p[3:6]), 1), p[6], err.mean(), err.max()))
    for (w, px), e in zip(anchors, err):
        print("   anchor", w, px, "err %.1f" % e)
    return cam


def make_all(here):
    cams = {"ref": (top_camera(), L.IMAGE_SIZE)}
    top_image(os.path.join(here, "ref", "REAL_REFERENCE.png"))
    ob = oblique_camera()
    if ob:
        cams["obl"] = (ob, L.OBLIQUE_SIZE)
    return cams
