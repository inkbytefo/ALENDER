"""Original restomod design: metres, no photographic fit (user changed brief)."""
from workbench.refmap import RefMap
ASSET='VEH_DeLorean_Vision'
IMAGE_SIZE=(1200,500)
REF=RefMap(250,(600,400),(0,0),front_is_right=False,image_size=IMAGE_SIZE)
REF.ortho=True
P,P3=REF.P,REF.P3
ANCHORS=[]
SILHOUETTE=[]
WHEELS=[(-1.31,.337,.265,.855),(1.32,.347,.305,.87)]
# y, half width, hood/deck center height, shoulder height
BODY=[(-2.22,.84,.599,.599),(-2.16,.92,.620,.630),(-1.98,.96,.645,.675),
      (-1.65,.974,.680,.748),(-1.31,.982,.706,.778),(-.94,.957,.725,.754),
      (-.65,.938,.735,.754),(0,.934,.740,.755),(.65,.950,.746,.769),
      (1.0,.981,.746,.793),(1.32,1.002,.744,.803),(1.75,.983,.728,.762),
      (2.12,.939,.704,.717),(2.22,.872,.674,.681)]
# y, roof center height, roof half-width, lower half-width, base height
CABIN=[(-.94,.735,.792,.80,.713),(-.83,.786,.763,.825,.722),
       (-.45,.987,.681,.83,.735),(-.13,1.129,.624,.833,.741),
       (-.07,1.15,.618,.834,.743),(.50,1.148,.623,.845,.75),
       (.68,1.13,.642,.849,.755),(1.12,.963,.736,.863,.761),
       (1.64,.77,.856,.871,.751),(1.73,.752,.86,.865,.73)]
