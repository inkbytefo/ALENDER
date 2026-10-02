"""
RefMap: maps pixels of a (side-view) reference photo to world metres and back.

Model convention: +Z up, -Y forward, X = width (+X = object's LEFT side).
A side photo gives the Y/Z plane; X (depth) always comes from widths you choose.

    ref = RefMap(scale=400, anchor_px=(853, 496), anchor_yz=(-0.722, 0.300),
                 theta=0.0346, front_is_right=True)
    y, z = ref.P(620, 241)          # pixel -> metres
    x, y, z = ref.P3(620, 241, 0.1) # with a chosen depth
    u, v = ref.photo_of(y, z)       # metres -> pixel (overlay checks)

theta (radians) removes a known in-plane tilt of the photo (e.g. a bike on a paddock
stand is pitched nose-down). Positive theta = photo rotated clockwise vs. rest pose.
See docs/03_REFERENCE_ANALYSIS.md for how to measure scale, anchor and theta.
"""
import math


class RefMap:
    def __init__(self, scale, anchor_px, anchor_yz, theta=0.0, front_is_right=True,
                 image_size=(1080, 720)):
        self.S = float(scale)
        self.anchor_px = anchor_px
        self.anchor_yz = anchor_yz
        self.theta = theta
        self.sign = 1.0 if front_is_right else -1.0   # image-right = -Y when front is right
        self.image_size = image_size
        self._c, self._s = math.cos(theta), math.sin(theta)

    def _rest_local(self, u, v):
        xp = (u - self.anchor_px[0]) / self.S
        zp = (self.anchor_px[1] - v) / self.S
        return xp * self._c - zp * self._s, xp * self._s + zp * self._c

    def P(self, u, v):
        """photo px -> (Y, Z) metres, pitch removed."""
        xr, zr = self._rest_local(u, v)
        return (self.anchor_yz[0] - self.sign * xr, self.anchor_yz[1] + zr)

    def P3(self, u, v, x=0.0):
        y, z = self.P(u, v)
        return (x, y, z)

    def photo_of(self, y, z):
        """(Y, Z) metres -> photo px."""
        xr = -(y - self.anchor_yz[0]) * self.sign
        zr = z - self.anchor_yz[1]
        xp = xr * self._c + zr * self._s
        zp = -xr * self._s + zr * self._c
        return (self.anchor_px[0] + xp * self.S, self.anchor_px[1] - zp * self.S)

    def length_px(self, metres):
        return metres * self.S


def pitch_from_two_points(px_a, px_b, rest_dz, scale):
    """Tilt of the photo given two points whose true height difference at rest is rest_dz
    (b minus a, metres). px_a must be the point nearer the image RIGHT (e.g. front axle when
    the front faces right), px_b the other one (rear axle). Returns (theta, true_distance_m)."""
    dxp = (px_b[0] - px_a[0]) / scale
    dzp = (px_a[1] - px_b[1]) / scale
    dist = math.hypot(dxp, dzp)
    ang_photo = math.atan2(dzp, -dxp)
    ang_rest = math.asin(rest_dz / dist)
    return ang_photo - ang_rest, dist * math.cos(ang_rest)


class ObliqueRefMap(RefMap):
    """Side photo taken with the object plane NOT parallel to the sensor (object leaning away, phone
    held near one end): a pinhole camera yawed by `yaw` about the image-vertical axis, `dist` metres
    from the plane point seen at the principal point (image centre by default). P() / photo_of() are the exact plane homography,
    so landmarks stay in pixels and the model comes out rectified (true proportions).

        ref = ObliqueRefMap(image_size=(1440, 720), f_px=3254.6, yaw=0.170, dist=2.0, roll=0.0,
                            anchor_px=(572, 295), anchor_yz=(0, 0), front_is_right=True)

    yaw > 0: the image-right end is farther from the camera (drawn smaller in the photo).
    roll: in-plane rotation of the photo (radians, same sign convention as RefMap.theta).
    Fit f_px / yaw from stations of a true orthographic source (factory drawing, known lengths);
    only yaw/f and the overall scale are observable, so `dist` is a free choice (2 m default).
    The matching Blender camera comes from cameras.reference_camera (view = "CALIBRATED")."""

    view = "CALIBRATED"

    def __init__(self, image_size, f_px, yaw, dist=2.0, roll=0.0, anchor_px=(0.0, 0.0),
                 anchor_yz=(0.0, 0.0), front_is_right=True, principal=None):
        self.image_size = image_size
        self.f, self.yaw, self.dist, self.roll = float(f_px), yaw, float(dist), roll
        self.sign = 1.0 if front_is_right else -1.0
        self.theta = 0.0
        self.anchor_px, self.anchor_yz = anchor_px, anchor_yz
        self._cy, self._sy = math.cos(yaw), math.sin(yaw)
        self._cr, self._sr = math.cos(roll), math.sin(roll)
        # principal point (px): the image centre unless the photo is a crop of a larger frame. It does
        # not change the in-plane mapping family, only which faces of thick parts the camera sees.
        self.u0, self.v0 = principal or (image_size[0] / 2.0, image_size[1] / 2.0)
        w = float(max(image_size))                     # lens shift in Blender units (fraction of the sensor width)
        self.shift_x = -(self.u0 - image_size[0] / 2.0) / w
        self.shift_y = (self.v0 - image_size[1] / 2.0) / w
        pa, qa = self._plane(*anchor_px)
        self.Y0 = anchor_yz[0] + self.sign * pa        # world (Y, Z) of the plane point at the image centre
        self.Z0 = anchor_yz[1] - qa
        self.S = self.f / self.dist                    # px per metre at the image centre
        side = -1.0 if self.sign > 0 else 1.0          # front on image right -> camera at -X
        self.lens = 36.0 * self.f / max(image_size)
        self.cam_loc = (side * self.dist * self._cy, self.Y0 + self.sign * self.dist * self._sy, self.Z0)
        self.cam_rot = (math.pi / 2.0, -roll, math.atan2(side * self._cy, -self.sign * self._sy))

    def _plane(self, u, v):
        """px -> plane coordinates (p towards image right, q up) relative to the image-centre point."""
        du, dv = u - self.u0, v - self.v0
        a, b = du * self._cr + dv * self._sr, -du * self._sr + dv * self._cr       # undo the roll
        p = a * self.dist / (self.f * self._cy - a * self._sy)
        return p, -b * (self.dist + p * self._sy) / self.f

    def P(self, u, v):
        p, q = self._plane(u, v)
        return (self.Y0 - self.sign * p, self.Z0 + q)

    def photo_of(self, y, z):
        p, q = -(y - self.Y0) * self.sign, z - self.Z0
        depth = self.dist + p * self._sy
        a, b = self.f * p * self._cy / depth, -self.f * q / depth
        return (self.u0 + a * self._cr - b * self._sr, self.v0 + a * self._sr + b * self._cr)

    def scale_at(self, u, v=None):
        """local px per metre (perpendicular to the long axis) at a pixel."""
        p, _ = self._plane(u, self.v0 if v is None else v)
        return self.f / (self.dist + p * self._sy)

    def length_px(self, metres, u=None):
        return metres * (self.S if u is None else self.scale_at(u))

    def obliquity(self, u):
        """angle (rad) between the view ray at photo column u and the plane normal; 0 = square-on,
        < 0 = the part is seen from its image-left side. A part of half width hw shows
        hw * tan|obliquity| of its end faces, so its silhouette is that much longer at both ends."""
        return self.yaw + math.atan((u - self.u0) / self.f)

    def thickness_px(self, u, hw):
        """px by which the silhouette of a part of half width hw (m) overhangs its mid-plane outline
        at column u, on each end that faces along the image-right axis."""
        return hw * abs(math.tan(self.obliquity(u))) * self.scale_at(u)

