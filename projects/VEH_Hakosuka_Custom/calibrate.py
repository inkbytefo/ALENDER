"""Fit a pinhole camera to explicit approximate photo/blueprint correspondences."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
import landmarks as L
xyz=np.array([a for a,b in L.CALIBRATION_ANCHORS]); pix=np.array([b for a,b in L.CALIBRATION_ANCHORS])
loc=np.array([-5.,-7.,2.4]); forward=np.array([0,0,.65])-loc; forward/=np.linalg.norm(forward)
right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
rot=Rotation.from_matrix(np.column_stack([right,up,-forward])).as_rotvec()
def project(p):
    q=(xyz-p[:3])@Rotation.from_rotvec(p[3:6]).as_matrix()
    return np.column_stack([481.5+p[6]*q[:,0]/-q[:,2],220-p[6]*q[:,1]/-q[:,2]])
p0=np.r_[loc,rot,1200.]
fit=least_squares(lambda p:(project(p)-pix).ravel(),p0,max_nfev=4000,
 bounds=([-30,-40,.3,-7,-7,-7,300],[ -.5,-.5,15,7,7,7,8000]))
errors=np.linalg.norm(project(fit.x)-pix,axis=1)
data=dict(location=fit.x[:3].tolist(),rotation_euler=Rotation.from_rotvec(fit.x[3:6]).as_euler('xyz').tolist(),lens_mm=float(fit.x[6]*36/963),errors_px=errors.tolist(),mean_px=float(errors.mean()),max_px=float(errors.max()),status='approximate fit; independently traced silhouette still required')
(HERE/'camera_fit.json').write_text(json.dumps(data,indent=2))
im=Image.open(HERE/'ref/REF_FRONT.png').convert('RGB'); d=ImageDraw.Draw(im)
for i,((u,v),(a,b)) in enumerate(zip(pix,project(fit.x))):
 d.ellipse((u-4,v-4,u+4,v+4),outline='lime',width=2); d.line((u,v,a,b),fill='yellow',width=2);d.text((a+4,b),str(i),fill='red')
im.save(HERE/'ref/CAMERA_ANCHOR_CHECK.png')
mask=Image.new('L',L.IMAGE_SIZE); ImageDraw.Draw(mask).polygon(L.PHOTO_OUTLINE,fill=255);mask.save(HERE/'ref/REF_MASK.png')
over=Image.open(HERE/'ref/REF_FRONT.png').convert('RGB');ImageDraw.Draw(over).line(L.PHOTO_OUTLINE+[L.PHOTO_OUTLINE[0]],fill='magenta',width=2);over.save(HERE/'ref/MASK_CHECK.png')
print(json.dumps(data,indent=2))
