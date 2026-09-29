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
