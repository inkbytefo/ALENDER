"""Measured native side-view pixels. LEFT side, front left, zero roll.
Source is the user-approved AI sheet, not a photograph. Scale from approximate
4.213m length; cross-checks: 1.136m height, 2.496m wheelbase (printed 2.410m),
0.597/0.581m tires (printed .590/.663m). Shape takes priority per user.
"""
import json
from pathlib import Path
from workbench.refmap import RefMap
ASSET='VEH_DeLorean_DMC12'
IMAGE_SIZE=(525,163)
S=508/4.213
ANCHOR_PX=(114.,112.)
ANCHOR_YZ=(-150.5/S,36/S)
THETA=0.
REF=RefMap(S,ANCHOR_PX,ANCHOR_YZ,THETA,front_is_right=False,image_size=IMAGE_SIZE)
REF.ortho=True
P,P3,photo_of=REF.P,REF.P3,REF.photo_of
ANCHORS=[(P3(114,112,.795),(114,112)),(P3(415,113,.794),(415,113))]
MARKS=[(114,112),(415,113)]
WHEEL_U=(114.,415.)
WHEEL_V=(112.,113.)
TIRE_R_PX=(36.,35.)
RIM_R_PX=(25.8,25.5)
TIRE_W=(.195,.235)
TRACK_X=(.795,.794)
# Fenders, hood and rear deck read on 3x crop; arch cutouts use measured arcs.
BODY_TOP=[(9,84),(16,71),(40,65),(114,55),(151,50),(178,62),
          (197,71),(316,70),(348,66),(379,56),(415,54),(449,57),(486,43),(506,48),(516,81)]
BODY_BOTTOM=[(9,102),(25,113),(70,122),(160,119),(370,118),(456,126),(506,111),(516,98)]
BODY_HALF_W=[(9,.78),(40,.88),(114,.928),(180,.90),(330,.90),(415,.928),(486,.88),(516,.83)]
ROOF_TOP=[(158,49),(184,40),(220,25),(253,13),(269,11),(330,11),(369,17),(428,29),(486,42)]
CABIN_HW=[(158,.79),(220,.70),(253,.62),(330,.62),(369,.70),(428,.79),(486,.86)]
CABIN_BASE=74.
WINDOW_SIDE=[(193,47),(255,19),(323,19),(329,23),(329,48),(324,52),(205,53)]
WINDOW_QUARTER=[(351,20),(429,35),(470,43),(470,48),(355,48)]
DOOR_SEAM=[(176,51),(184,116),(311,116),(346,65),(346,14)]
HOOD_EDGE=[(20,71),(62,66),(115,59),(155,54)]
ARCH_R=(44.,44.)
_data=json.loads((Path(__file__).parent/'measurements.json').read_text())
SILHOUETTE=[_data['top']+_data['bottom'][1:]]
PART_OUTLINES={}
