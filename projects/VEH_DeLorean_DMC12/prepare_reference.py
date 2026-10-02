"""Reproduce native-resolution crops and measured boundary; exclude floor shadow."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, binary_erosion

HERE = Path(__file__).resolve().parent
REF = HERE / 'ref'
WORK = HERE.parents[1] / 'output' / HERE.name / 'work'
# Inspected pixel windows on the 3x labelled original crop.
TOP_SEEDS = [(9,84),(16,71),(40,65),(110,56),(160,49),(184,40),(220,25),
             (253,13),(269,11),(330,11),(369,17),(428,29),(486,42),(506,48),(516,81)]
BOTTOM_SEEDS = [(516,81),(516,98),(506,112),(462,127),(450,127),
                (442,136),(430,145),(415,148),(400,145),(386,137),(377,128),
                (160,131),(148,138),(133,145),(114,148),(97,144),(82,135),
                (76,130),(15,132),(9,130),(20,123),(25,113),(11,105),(8,101),(8,85)]

def measure(seeds, gray):
    """Strongest smoothed normal gradient within +/-2 px of inspected seed.
    Narrow guarded windows avoid chrome highlights and floor shadows.
    """
    gy,gx = np.gradient(gaussian_filter(gray,.65)); out=[]
    for i,(u,v) in enumerate(seeds):
        a=np.array(seeds[max(0,i-1)],float); b=np.array(seeds[min(len(seeds)-1,i+1)],float)
        t=b-a; n=np.array([-t[1],t[0]]); n/=max(np.linalg.norm(n),1)
        candidates=[]
        for d in np.linspace(-2,2,17):
            p=np.array([u,v])+n*d; x,y=np.rint(p).astype(int)
            if 0<=x<gray.shape[1] and 0<=y<gray.shape[0]:
                candidates.append((abs(gx[y,x]*n[0]+gy[y,x]*n[1])-.6*abs(d),p))
        p=max(candidates,key=lambda q:q[0])[1]
        out.append(tuple(round(float(c),2) for c in p))
    return out

def main():
    src=Image.open(REF/'SOURCE_ATTACHMENT.png').convert('RGB')
    src.save(REF/'MODELING_CHEATSHEET.png')
    im=src.crop((515,72,1040,235)); im.save(REF/'REAL_REFERENCE.png')
    for name,box in [('REF_FRONT',(550,532,790,660)),('REF_REAR',(884,530,1125,661)),
                     ('REF_TOP',(1233,531,1640,711)),('REF_SIDE_BLUEPRINT',(54,534,506,662))]:
        src.crop(box).save(REF/(name+'.png'))
    gray=np.asarray(im,dtype=float).mean(axis=2)
    top=measure(TOP_SEEDS,gray); bot=measure(BOTTOM_SEEDS,gray)
    mask=Image.new('L',im.size); ImageDraw.Draw(mask).polygon(top+bot[1:],fill=255)
    mask.save(REF/'REF_MASK.png')
    a=np.asarray(im).copy(); m=np.asarray(mask)>0; a[m^binary_erosion(m)]=(255,0,255)
    WORK.mkdir(parents=True,exist_ok=True)
    Image.fromarray(a).resize((1575,489)).save(WORK/'ref_mask_check.png')
    data=dict(source_size=src.size,crop=[515,72,1040,235],top=top,bottom=bot,
              method='inspected seeds + normal-gradient search +/-2px; floor shadow excluded',
              scale=508/4.213,wheelbase_m=301/(508/4.213),height_m=137/(508/4.213),
              front_tire_m=72/(508/4.213),rear_tire_m=70/(508/4.213))
    (HERE/'measurements.json').write_text(json.dumps(data,indent=2))
    print(json.dumps({k:v for k,v in data.items() if k not in ('top','bottom')},indent=2))

if __name__=='__main__': main()
