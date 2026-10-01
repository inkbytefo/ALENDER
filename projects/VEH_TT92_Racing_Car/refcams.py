"""
Reference camera for VEH_TT92_Racing_Car.

  CAM_REFERENCE  orthographic TOP camera reproducing ref/REAL_REFERENCE.png (front = image top):
                 1 px = 1/S m on the ground plane, image centre = photo centre.
  REF_PHOTO      the photo as an image empty just below the ground, aligned with that camera.

Overlay a render of CAM_REFERENCE on the photo:
    python wb.py compare VEH_TT92_Racing_Car output/VEH_TT92_Racing_Car/work/s4/s4_ref_clay.png
(the nose is a design change and no longer follows the photo; everything behind v 250 does).
"""
import math
import os
import bpy

import landmarks as L
from workbench.bl import cameras
from workbench.bl.scene import coll


def top_camera():
    W, H = L.IMAGE_SIZE
    cam = cameras.make("CAM_REFERENCE", (L.X(W / 2.0), L.Y(H / 2.0), 10.0), (0.0, 0.0, math.pi),
                       ortho_scale=W / L.S, collection="00_REFERENCE")
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


def make_all(here):
    """{tag: (camera, resolution)} of the reference cameras; also places the photo."""
    cams = {"ref": (top_camera(), L.IMAGE_SIZE)}
    top_image(os.path.join(here, "ref", "REAL_REFERENCE.png"))
    return cams
