"""
FrontRefMap: reference photo taken from the FRONT of a character (project-local; the library RefMap
is a side-view map). Model convention unchanged: +Z up, -Y forward, +X = the character's left, so
image right = +X and the photo plane is X/Z; DEPTH is +Y (away from the camera).

A pinhole camera far away (near-orthographic), pitched down by `pitch`, looking along +Y. The world
origin (ground point under the body) is seen at `anchor_px`.

    P3(u, v, d)   px + chosen world depth Y=d  -> (x, y, z)   exact inverse of the camera
    px(x, y, z)   world -> px
Library builders (mesh.plate, prim.*) only call P3(u, v, depth), so they work unchanged: a "plate"
is extruded along the view depth. cameras.reference_camera uses view = "CALIBRATED".
"""
import math


class FrontRefMap:
    view = "CALIBRATED"
    sign = 1.0
    theta = 0.0

    def __init__(self, scale, anchor_px, pitch=0.0, dist=20.0, image_size=(1080, 720)):
        self.S = float(scale)                  # px per metre at the origin
        self.anchor_px = anchor_px
        self.anchor_yz = (0.0, 0.0)
        self.pitch, self.dist = pitch, float(dist)
        self.image_size = image_size
        W, H = image_size
        self.F = self.S * self.dist            # focal length in px
        c, s = math.cos(pitch), math.sin(pitch)
        self._right, self._up, self._fwd = (1.0, 0.0, 0.0), (0.0, s, c), (0.0, c, -s)
        ra = self._ray(*anchor_px)
        self.cam_loc = tuple(-self.dist * k for k in ra)
        self.cam_rot = (math.pi / 2.0 - pitch, 0.0, 0.0)
        self.lens = 36.0 * self.F / W          # cameras.make: sensor_fit HORIZONTAL, 36 mm
        self.shift_x = self.shift_y = 0.0

    def _ray(self, u, v):
        W, H = self.image_size
        a, b = (u - W / 2.0) / self.F, (H / 2.0 - v) / self.F
        return tuple(a * self._right[i] + b * self._up[i] + self._fwd[i] for i in range(3))

    def P3(self, u, v, d=0.0):
        r = self._ray(u, v)
        t = (d - self.cam_loc[1]) / r[1]
        return tuple(self.cam_loc[i] + t * r[i] for i in range(3))

    def P(self, u, v):
        """px -> (X, Z) on the depth plane Y = 0 (front view: the photo plane is X/Z)."""
        x, _, z = self.P3(u, v, 0.0)
        return (x, z)

    def px(self, x, y, z):
        q = (x - self.cam_loc[0], y - self.cam_loc[1], z - self.cam_loc[2])
        dot = lambda a: sum(q[i] * a[i] for i in range(3))
        zc = dot(self._fwd)
        W, H = self.image_size
        return (W / 2.0 + self.F * dot(self._right) / zc, H / 2.0 - self.F * dot(self._up) / zc)

    def photo_of(self, x, z):
        return self.px(x, 0.0, z)

    def scale_at(self, d=0.0):
        """px per metre for a point at world depth d near the body axis."""
        return self.F / (self.dist + d * math.cos(self.pitch))

    def length_px(self, metres):
        return metres * self.S
