"""Pixel source geometry and separately calibrated photographic reference.
Blueprint points eye-read from user-supplied orthographic drawing. Photo outline
hand-traced; boundary uncertainty 2-4 px. No generated-sheet silhouette used.
"""
import json
from pathlib import Path
from workbench.refmap import RefMap
ASSET = 'VEH_Hakosuka_Custom'
IMAGE_SIZE = (963, 440)
REFERENCE_IMAGE = 'REF_FRONT.png'
# Blueprint front/rear hubs (221,280), (665,280); 444px / 2.570m.
S = 444 / 2.570
BLUEPRINT_REF = RefMap(S, (221,280), (-1.285,0.300), front_is_right=False, image_size=(1280,906))
P, P3 = BLUEPRINT_REF.P, BLUEPRINT_REF.P3
# Body section stations: blueprint u, top v, bottom v, estimated half width m.
BODY_STATIONS = [(88,191,287,.80),(130,181,294,.80),(221,178,302,.80),
 (325,170,304,.80),(400,179,303,.80),(540,180,302,.80),
 (665,179,300,.80),(790,187,291,.78),(813,196,284,.73)]
ROOF = [(332,179,.73),(411,103,.61),(460,99,.62),(545,100,.65),(574,110,.63),(620,132,.68),(661,172,.74)]
WHEEL_U = (221,665)
WHEEL_V = 280
WHEEL_R_PX = 52
BODY_OUTLINE = [(u,v) for u,v,_,_ in BODY_STATIONS]+[(u,b) for u,_,b,_ in reversed(BODY_STATIONS)]
# Front-right photograph crop coordinates. Exterior contour includes mirrors/wheels.
PHOTO_OUTLINE = [(101,198),(107,161),(121,145),(122,133),(146,130),(165,108),(186,70),
 (205,50),(237,39),(274,30),(297,26),(351,24),(430,27),(494,33),(537,43),
 (554,58),(578,85),(605,121),(639,135),(762,145),(766,134),(763,120),
 (770,116),(783,121),(796,134),(800,146),(796,158),(843,169),(875,179),
 (883,189),(886,224),(886,259),(883,284),(871,300),(839,319),(843,341),
 (850,360),(834,370),(768,380),(685,388),(606,395),(549,398),(531,393),
 (503,376),(446,376),(428,391),(401,403),(372,409),(343,402),(326,387),
 (312,366),(302,330),(176,288),(164,300),(142,302),(126,295),(116,278),
 (110,249),(109,221),(101,211)]
SILHOUETTE = [PHOTO_OUTLINE]
PART_OUTLINES = {}
# Approximate world correspondences derived from blueprint + uncertain widths.
CALIBRATION_ANCHORS = [
 ((-.82,-1.285,.300),(363,307)), ((-.82,1.285,.300),(138,234)),
 ((-.65,-2.00,.69),(521,236)), ((.65,-2.00,.69),(860,222)),
 ((-.72,-.642,.884),(306,130)), ((.72,-.642,.884),(607,126)),
 ((-.61,-.185,1.325),(298,36)), ((.61,-.185,1.325),(536,49)),
 ((-.61,.66,1.325),(217,54)),
]
REF = RefMap(S, (221,280), (-1.285,.300), front_is_right=False, image_size=IMAGE_SIZE)
REF.view = 'CALIBRATED'
cp = Path(__file__).with_name('camera_fit.json')
if cp.exists():
    fit = json.loads(cp.read_text())
    REF.cam_loc, REF.cam_rot, REF.lens = fit['location'],fit['rotation_euler'],fit['lens_mm']
ANCHORS = CALIBRATION_ANCHORS
MARKS = [px for _,px in ANCHORS]
