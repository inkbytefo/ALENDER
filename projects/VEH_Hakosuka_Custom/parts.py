"""Reproducible Hakosuka part builders. Blueprint pixels control longitudinal shape.
Photographic widths/tyres/ride height remain estimates until silhouette calibration passes.
"""
import math
import landmarks as L
from workbench import stages, tables
from workbench.stages import Part
from workbench.bl import mesh, mods
mesh.set_ref(L.BLUEPRINT_REF)
CATEGORY='hero_vehicle'
TARGET_DIMS=(None,4.33,None)
GROUND=True
PROFILES={1:stages.profile(1,ring=12),2:stages.profile(2,ring=32),3:stages.profile(3,ring=48)}
GAME=dict(engine='godot',bake=True,lod=(.5,.25))
PALETTE={'MAT_BODY':((.58,.59,.58),.65,.24),'MAT_TRIM':'plastic_black','MAT_TIRE':'rubber',
'MAT_CHROME':'chrome','MAT_GLASS':((.065,.09,.105),.3,.16),
'MAT_RED':((.5,.01,.012),.1,.2),'MAT_LAMP':((.83,.8,.58),.1,.2),'MAT_AMBER':((.8,.38,.04),.1,.2)}
UNCERTAIN=['UNCERTAIN_Underbody','UNCERTAIN_Interior','UNCERTAIN_WheelDimensions','UNCERTAIN_BodyWidths']
CRITICAL_PAIRS=[('WHEEL_Tire','BODY_Shell')]
PIVOTS={}
CHILDREN={}
def nm(P,n):return stages.nm(P,n.replace('_-1','_R'))
def hard(o,P,w=.004):return mods.finish_hard(o,w,enabled=P['bevel'])
def box(P,n,uv,hw,dv,du,mat='MAT_BODY'):
 y,z=L.P(*uv)
 return hard(mesh.box(nm(P,n),P['coll'],(0,y,z),(hw*2,du/L.S,dv/L.S),mat),P)
def body(P):
 us=sorted(set([u for u,*_ in L.BODY_STATIONS]+[c+t for c in L.WHEEL_U for t in [-65,-60,-50,-35,0,35,50,60,65]]))
 rings=[]
 for u in us:
  if not 88<=u<=829:continue
  vt=tables.interp([(a,b) for a,b,c,d in L.BODY_STATIONS],u)
  vb=tables.interp([(a,c) for a,b,c,d in L.BODY_STATIONS],u)
  hw=tables.interp([(a,d) for a,b,c,d in L.BODY_STATIONS],u)
  y,zt=L.P(u,vt); _,zb=L.P(u,vb)
  for c in L.WHEEL_U:
   dy=(u-c)/L.S
   if abs(dy)<.365:zb=max(zb,.300+math.sqrt(max(0,.365**2-dy**2)))
  zb=min(zb,zt-.04)
  rings.append([(-hw*.94,y,zt),(-hw,y,zt-.075),(-hw*.97,y,zb),(-hw*.72,y,zb-.01),
   (hw*.72,y,zb-.01),(hw*.97,y,zb),(hw,y,zt-.075),(hw*.94,y,zt)])
 return [hard(mesh.loft_rings(nm(P,'BODY_Shell'),P['coll'],rings,'MAT_BODY'),P)]
def cabin(P):
 rings=[]
 for u,v,hw in L.ROOF:
  y,z=L.P(u,v); bottom=L.P(u,181)[1]
  rings.append([(-.74,y,bottom),(-hw,y,z-.025),(-hw*.8,y,z),(hw*.8,y,z),(hw,y,z-.025),(.74,y,bottom)])
 ob=mesh.loft_rings(nm(P,'CABIN_Greenhouse'),P['coll'],rings,'MAT_BODY')
 return [hard(ob,P)] + (glazing(P) if P['stage']>=2 else [])
def wheels(P):
 obs=[]
 for i,u in enumerate(L.WHEEL_U):
  y,z=L.P(u,280)
  for sign in (-1,1):
   side='R' if sign<0 else 'L';name=f'{i}_{side}';x=sign*.76
   profile=[(.212,-.115),(.273,-.115),(.300,-.08),(.300,.08),(.273,.115),(.212,.115)]
   obs.append(mesh.lathe(nm(P,'WHEEL_Tire_'+name),P['coll'],(x,y,.300),profile,P['ring'],'MAT_TIRE'))
   obs.append(mesh.lathe(nm(P,'WHEEL_Rim_'+name),P['coll'],(x,y,.300),[(.187,-.105),(.20,-.105),(.218,-.12),(.228,-.11),(.223,.11),(.205,.12),(.187,.09)],P['ring'],'MAT_CHROME'))
   if P['stage']>=2:
    face=x+sign*.115
    for k in range(8):
     a=2*math.pi*k/8
     verts=[]
     for xx in (face-sign*.025,face):
      for r,t in ((.06,-.12),(.193,-.075),(.193,.075),(.06,.12)):
       verts.append((xx,y+r*math.cos(a+t),.300+r*math.sin(a+t)))
     obs.append(hard(mesh.from_pydata(nm(P,f'WHEEL_Spoke_{name}_{k}'),P['coll'],verts,
      [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'MAT_CHROME'),P,.002))
 return obs

def flares(P):
 obs=[];n=12 if P['stage']==1 else 28
 for i,u in enumerate(L.WHEEL_U):
  cy,cz=L.P(u,280)
  for sign in (-1,1):
   rings=[]
   for j in range(n+1):
    a=-.12+(math.pi+.24)*j/n
    row=[]
    for r,x in [(.337,.80),(.347,.95),(.40,.91),(.423,.80)]:
     row.append((sign*x,cy+r*math.cos(a),.300+r*math.sin(a)))
    rings.append(row)
   obs.append(hard(mesh.loft_rings(nm(P,f'FLARE_{i}_{sign}'),P['coll'],rings,'MAT_TRIM'),P))
 return obs
def trim(P):
 obs=[box(P,'BUMPER_Front',(82,252),.76,12,10,'MAT_CHROME'),box(P,'BUMPER_Rear',(816,268),.78,15,15,'MAT_CHROME'),
 box(P,'GRILLE_Front',(86,213),.735,42,4,'MAT_TRIM'),front_lip(P),
 box(P,'SPOILER_Blade',(785,180),.76,7,43)]
 for s in (-1,1):
  y,z=L.P(780,193)
  obs.append(mesh.box(nm(P,f'SPOILER_Mount_{s}'),P['coll'],(s*.5,y,z),(.045,.15,.15),'MAT_BODY'))
  y,z=L.P(170,175)
  obs.append(mesh.cyl(nm(P,f'MIRROR_Stem_{s}'),P['coll'],(s*.67,y,z),(s*.75,y,z+.035),.022,8,'MAT_TRIM'))
  obs.append(mesh.box(nm(P,f'MIRROR_Housing_{s}'),P['coll'],(s*.75,y,z+.048),(.12,.10,.07),'MAT_TRIM'))
 return obs
def front_lip(P):
 """A swept front air dam with returned corners; intentional secondary design variation."""
 rings=[]
 for x,u,vt,vb in [(-.76,113,266,286),(-.65,88,272,293),(-.40,76,275,297),
                   (0,74,275,297),(.40,76,275,297),(.65,88,272,293),(.76,113,266,286)]:
  y,zt=L.P(u,vt);_,zb=L.P(u,vb)
  rings.append([(x,y,zt),(x,y-.028,zb),(x,y+.005,zb),(x,y+.022,zt)])
 return hard(mesh.loft_rings(nm(P,'LIP_Front'),P['coll'],rings,'MAT_BODY'),P,.003)

def lamps(P):
 obs=[]
 for s in (-1,1):
  for j,x in enumerate((.48,.66)):
   y,z=L.P(84,212)
   obs.append(mesh.cyl(nm(P,f'LAMP_Front_{s}_{j}'),P['coll'],(s*x,y-.018,z),(s*x,y-.04,z),.085,P['ring'],'MAT_LAMP'))
   if P['stage']>=2:
    obs.append(mesh.lathe(nm(P,f'LAMP_Bezel_{s}_{j}'),P['coll'],(s*x,y-.035,z),[(.085,-.012),(.095,-.012),(.098,.003),(.085,.007)],P['ring'],'MAT_CHROME',axis='Y'))
  y,z=L.P(835,225)
  obs.append(mesh.box(nm(P,f'LAMP_Rear_{s}'),P['coll'],(s*.55,y,z),(.32,.035,.14),'MAT_RED'))
 return obs
def floor(P):return [box(P,'UNCERTAIN_Underbody',(450,300),.45,12,580,'MAT_TRIM')]
def glazing(P):
 """Separate dark glass slabs follow the measured greenhouse, not arbitrary rectangles."""
 obs=[]
 def point(u,v,sign):
  vt=tables.interp([(a,b) for a,b,c in L.ROOF],u)
  hw=tables.interp([(a,c) for a,b,c in L.ROOF],u)
  t=max(0,min(1,(181-v)/(181-vt))) if vt!=181 else 0
  x=sign*(.74+(hw-.74)*t+.004)
  return L.P3(u,v,x)
 for sign in (-1,1):
  for name,poly in [('Door',[(345,175),(421,114),(504,110),(504,175)]),
                    ('Quarter',[(516,111),(558,116),(613,155),(614,170),(516,175)])]:
   a=[point(u,v,sign) for u,v in poly];b=[(x+sign*.005,y,z) for x,y,z in a]
   obs.append(mesh.extrude_polys(nm(P,f'GLASS_{name}_{sign}'),P['coll'],[(a,b)],'MAT_GLASS'))
 # Front/rear panes: between roof stations. Offset out of the solid cabin proxy.
 for name,ua,ub,va,vb,wa,wb,dy in [('Windshield',341,404,178,112,.682,.575,-.006),
                                  ('Rear',580,649,119,169,.586,.673,.006)]:
  a=[L.P3(ua,va,-wa),L.P3(ua,va,wa),L.P3(ub,vb,wb),L.P3(ub,vb,-wb)]
  a=[(x,y+dy,z+.006) for x,y,z in a];b=[(x,y+dy,z) for x,y,z in a]
  obs.append(mesh.extrude_polys(nm(P,'GLASS_'+name),P['coll'],[(a,b)],'MAT_GLASS'))
 return obs

def detailing(P):
 if P['stage']==1:return []
 obs=[]
 for sign in (-1,1):
  # Door seam, sill trim and handles remain independently editable.
  poly=[(337,183),(337,272),(349,296),(534,295),(541,182)]
  pts=[L.P3(u,v,sign*.802) for u,v in poly]
  obs.append(mesh.tube(nm(P,f'TRIM_DoorSeam_{sign}'),P['coll'],pts,.0022,6,'MAT_TRIM'))
  y,z=L.P(515,197)
  obs.append(hard(mesh.box(nm(P,f'TRIM_Handle_{sign}'),P['coll'],(sign*.813,y,z),(.022,.11,.022),'MAT_CHROME'),P,.002))
  y,z=L.P(596,143)
  obs.append(mesh.cyl(nm(P,f'TRIM_CPillar_{sign}'),P['coll'],(sign*.66,y,z),(sign*.684,y,z),.037,20,'MAT_CHROME'))
  y,z=L.P(170,175)
  obs.append(mesh.lathe(nm(P,f'MIRROR_Rounded_{sign}'),P['coll'],(sign*.75,y,z+.048),[(.012,-.065),(.04,-.03),(.045,.025),(.014,.06)],16,'MAT_TRIM',closed=False,axis='X'))
 # Split grille inserts and central chrome divider.
 for sign in (-1,1):
  y,z=L.P(84,212)
  obs.append(mesh.box(nm(P,f'GRILLE_Insert_{sign}'),P['coll'],(sign*.185,y-.025,z),(.335,.018,.16),'MAT_TRIM'))
  for k in range(4):
   obs.append(mesh.box(nm(P,f'GRILLE_Slat_{sign}_{k}'),P['coll'],(sign*.185,y-.037,z-.065+k*.04),(.325,.008,.006),'MAT_CHROME'))
 y,z=L.P(84,212)
 obs.append(mesh.box(nm(P,'GRILLE_Divider'),P['coll'],(0,y-.04,z),(.018,.015,.19),'MAT_CHROME'))
 return obs

PARTS=[Part('body',body,collision='hull'),Part('cabin',cabin,collision='hull'),Part('wheels',wheels,collision='hull'),Part('flares',flares,collision='hull'),Part('trim',trim,collision='hull'),Part('lamps',lamps,collision='box'),Part('underbody',floor,collision='box'),Part('details',detailing,collision='none')]
def guide_points():return {'FRONT_AXLE':(0,-1.285,.300),'REAR_AXLE':(0,1.285,.300)}
