"""DeLorean Vision: continuous automotive surfaces, original art direction."""
import math
from functools import lru_cache
import bpy
import bmesh
from mathutils import Vector,Matrix
import landmarks as L
from workbench import stages,tables
from workbench.stages import Part
from workbench.bl import mesh,mods,materials
CATEGORY='hero_vehicle'
TARGET_DIMS=(None,4.50,1.16)
GROUND=True
PROFILES={1:stages.profile(1,ny=18,cross=1,wseg=16,spokes=0),
          2:stages.profile(2,ny=78,cross=3,wseg=64,spokes=20),
          3:stages.profile(3,ny=78,cross=3,wseg=64,spokes=20)}
GAME=dict(engine='godot',bake=True,tex=4096,lod=(.5,.25))
PALETTE={'MAT_STEEL':((.46,.49,.52),.92,.29),'MAT_BLACK':((.018,.022,.027),.05,.38),
 'MAT_RUBBER':((.012,.014,.018),0,.73),'MAT_ALLOY':((.51,.54,.57),.90,.21),
 'MAT_GLASS':((.18,.25,.28),0,.075),'MAT_WHITE':dict(rgb=(.74,.83,.94),metallic=.18,roughness=.15,emission=(.55,.70,1),emission_strength=.4),
 'MAT_RED':dict(rgb=(.47,.006,.012),metallic=.1,roughness=.22,emission=(.5,.003,.007),emission_strength=.35),
 'MAT_AMBER':((.9,.23,.025),.35,.27)}
CRITICAL_PAIRS=[('WHEEL_Tire','BODY_Main')]
UNCERTAIN=['UNCERTAIN_Undertray','UNCERTAIN_HiddenMechanicals']
ASSUMPTIONS=['User explicitly requested original vision and abandoned image matching','Static closed-door exterior restomod','Godot glTF conventions retained']
KNOWN_LIMITATIONS=['Original concept, not an accurate reconstruction of a production DMC-12','Simplified cockpit; no hidden drivetrain or opening doors','Doors remain closed; wheels have rotation pivots']
PIVOTS={}; CHILDREN={}
def nm(P,n):return stages.nm(P,n)
def hard(o,P,w=.002):
    ext=[max(v.co[k] for v in o.data.vertices)-min(v.co[k] for v in o.data.vertices) for k in range(3)]
    return mods.finish_hard(o,min(w,min(ext)*.22),enabled=P['bevel'])
def box(P,n,c,s,mat='MAT_BLACK',w=.002,rot=None):return hard(mesh.box(nm(P,n),P['coll'],c,s,mat,rot=rot),P,w)
def surface(P,n,a,b,mat='MAT_STEEL',w=.001):return hard(mesh.extrude_polys(nm(P,n),P['coll'],[(a,b)],mat),P,w)
def tube(P,n,points,r=.004,mat='MAT_BLACK',seg=8):
    # Round seams and seals already have curved sections; avoid microscopic bevel degenerates.
    ob=mesh.tube(nm(P,n),P['coll'],points,r,4 if P['stage']==1 else seg,mat,smooth_path=False)
    if P['bevel']:mods.weighted_normal(ob)
    return ob

@lru_cache(maxsize=32)
def body_spline(col):
    rows=L.BODY;n=len(rows);h=[rows[i+1][0]-rows[i][0] for i in range(n-1)]
    lo=[0.0]*n;di=[1.0]*n;up=[0.0]*n;rhs=[0.0]*n
    for i in range(1,n-1):
        lo[i]=h[i-1];di[i]=2*(h[i-1]+h[i]);up[i]=h[i]
        rhs[i]=6*((rows[i+1][col]-rows[i][col])/h[i]-(rows[i][col]-rows[i-1][col])/h[i-1])
    for i in range(1,n):
        q=lo[i]/di[i-1];di[i]-=q*up[i-1];rhs[i]-=q*rhs[i-1]
    m=[0.0]*n;m[-1]=rhs[-1]/di[-1]
    for i in range(n-2,-1,-1):m[i]=(rhs[i]-up[i]*m[i+1])/di[i]
    return m

def interp(rows,y,col):
    # Cubic Hermite, derivative from adjacent stations; no arbitrary control-point offsets.
    if y<=rows[0][0]:return rows[0][col]
    if y>=rows[-1][0]:return rows[-1][col]
    for i in range(len(rows)-1):
        a,b=rows[i],rows[i+1]
        if a[0]<=y<=b[0]:
            if rows is L.BODY:
                h=b[0]-a[0];u=(b[0]-y)/h;v=(y-a[0])/h;m=body_spline(col)
                return u*a[col]+v*b[col]+((u**3-u)*m[i]+(v**3-v)*m[i+1])*h*h/6
            prev=rows[max(0,i-1)]; nex=rows[min(len(rows)-1,i+2)]
            d=b[0]-a[0]; t=(y-a[0])/d
            m0=(b[col]-prev[col])/(b[0]-prev[0]); m1=(nex[col]-a[col])/(nex[0]-a[0])
            return (2*t**3-3*t*t+1)*a[col]+(t**3-2*t*t+t)*d*m0+(-2*t**3+3*t*t)*b[col]+(t**3-t*t)*d*m1

def body_section(y):
    w=interp(L.BODY,y,1); top=interp(L.BODY,y,2); sh=interp(L.BODY,y,3); rise=sh-top
    return [(0,top),(.45*w,top+.1*rise),(.74*w,top+.62*rise),(.91*w,sh-.008),
            (.976*w,sh-.010),(w,sh-.045),(1.002*w,min(.58,sh-.074)),(.997*w,.43),
            (.98*w,.285),(.94*w,.235),(.80*w,.211),(0,.211)]

def catloop(points,sub):
    out=[]; n=len(points)
    for i in range(n):
        p0=Vector(points[(i-1)%n]);p1=Vector(points[i]);p2=Vector(points[(i+1)%n]);p3=Vector(points[(i+2)%n])
        for j in range(sub):
            t=j/sub
            # Periodic uniform cubic B-spline: continuous second derivatives across spans.
            out.append(tuple((p0*(1-t)**3+p1*(3*t**3-6*t*t+4)+p2*(-3*t**3+3*t*t+3*t+1)+p3*t**3)/6))
    return out

def side_x(y,z):
    pp=body_section(y)
    for (x0,z0),(x1,z1) in zip(pp[4:],pp[5:]):
        if z1<=z<=z0:return x0+(x1-x0)*(z0-z)/max(z0-z1,1e-6)
    return pp[5][0]

def arch_z(y,prim=False):
    z=.211
    for cy,r,_,_ in L.WHEELS:
        rad=r+(.066 if prim else .037)
        if abs(y-cy)<rad:
            z=max(z,r+math.sqrt(max(0,rad*rad-(y-cy)**2)))
    return z

def section_skin(y,sub,steps=6):
    # Top and shoulder retain their designed spline. The lower side is an explicit
    # ruled quad patch ending at a circular arch: no boolean-generated slivers.
    half=body_section(y); sec=half+[(-x,z) for x,z in half[-2:0:-1]]
    sec[6]=(sec[6][0],sec[5][1]-.030)
    top=catloop(sec,sub)[:5*sub+1]
    x0,z0=top[-1]; bottom=arch_z(y,steps==2)
    if steps==2 and z0<bottom+.018:top[-1]=(x0,bottom+.018);z0=bottom+.018
    side=[]
    for k in range(1,steps+1):
        t=k/steps; z=z0*(1-t)+bottom*t
        x=side_x(y,z)
        side.append((x,z))
    edge=side[-1][0]
    return top+side+[(edge-.014,bottom),(.65,bottom),(.65,.190),(0,.190)]

def body(P):
    ys=set(r[0] for r in L.BODY)
    ny=3 if P['stage']==1 else 72
    ys.update(L.BODY[0][0]+(L.BODY[-1][0]-L.BODY[0][0])*i/(ny-1) for i in range(ny))
    for cy,r,_,_ in L.WHEELS:
        rad=r+(.066 if P['stage']==1 else .037); a=math.asin((.211-r)/rad)
        n=4 if P['stage']==1 else 36
        ys.update(cy+rad*math.cos(a+(math.pi-2*a)*i/n) for i in range(n+1))
    if P['stage']>1:ys.update([-.766,-.746,-.726,.786,.806,.826])
    ys=sorted(ys)
    if P['stage']>1:
        forced={-.766,-.746,-.726,.786,.806,.826,L.BODY[0][0],L.BODY[-1][0]}
        ys=[y for y in ys if y in forced or all(abs(y-f)>.008 for f in forced)]
        reduced=[]
        for y in ys:
            if not reduced or y-reduced[-1]>.008:reduced.append(y)
        ys=reduced
    sub=1 if P['stage']==1 else 3
    rings=[]; original=[]
    for y in ys:
        half=section_skin(y,sub,2 if P['stage']==1 else 6);sec=half+[(-x,z) for x,z in half[-2:0:-1]]
        original.append([(x,y,z) for x,z in sec])
        ring=[]
        for j,(x,z) in enumerate(sec):
            if P['stage']>1 and -.76<y<.82 and abs(x)<.74 and z>.58:
                wx=max(0,min(1,(.74-abs(x))/.14));wy=max(0,min(1,(y+.76)/.15,(.82-y)/.15))
                z-=.30*wx*wy
            # Recess only the door seat. The separate metal skin bridges this region;
            # the 2mm edge clearance exposes the recessed black gasket underneath.
            if P['stage']>1 and -.746<=y<=.806 and .27<z<body_section(y)[5][1]+.0001 and abs(x)>.86:
                x-=math.copysign(.0015,x)
            ring.append((x,y,z))
        rings.append(ring)
    ob=mesh.loft_rings(nm(P,'BODY_Main'),P['coll'],rings,'MAT_STEEL',sharp_angle=50)
    # The only boolean is the small front intake on the almost planar fascia.
    cut=mesh.box('TEMP_Intake',P['coll'],(0,-2.19,.302),(1.50,.30,.082),'MAT_STEEL')
    mods.bevel(cut,.023,segments=3 if P['stage']>1 else 1);mods.apply_all(cut)
    mods.boolean(ob,cut,apply=True);bpy.data.objects.remove(cut,do_unlink=True)
    cut=mesh.box('TEMP_RearValance',P['coll'],(0,2.20,.290),(1.60,.30,.15),'MAT_STEEL')
    mods.bevel(cut,.018,segments=3 if P['stage']>1 else 1);mods.apply_all(cut)
    mods.boolean(ob,cut,apply=True);bpy.data.objects.remove(cut,do_unlink=True)
    ob.data.materials.append(bpy.data.materials['MAT_BLACK'])
    for f in ob.data.polygons:
        c=f.center
        if abs(c.x)<.86 and abs(f.normal.x)>.8 and any(abs(c.y-y)<r+.04 for y,r,w,t in L.WHEELS):f.material_index=1
    hard(ob,P,.002)
    out=[ob]
    if P['stage']>1:
        for sign,label in [(1,'L'),(-1,'R')]:
            rr=[]
            for k in range(25):
                y=-.744+1.548*k/24
                ztop=body_section(y)[5][1]-.003;zbot=.264
                rr.append([(sign*side_x(y,zbot+(ztop-zbot)*i/6),y,zbot+(ztop-zbot)*i/6) for i in range(7)])
            verts=[v for row in rr for v in row];faces=[]
            for k in range(24):
                for i in range(6):faces.append((k*7+i,(k+1)*7+i,(k+1)*7+i+1,k*7+i+1))
            panel=mesh.from_pydata(nm(P,'DOOR_Skin_'+label),P['coll'],verts,faces,'MAT_STEEL',sharp_angle=60)
            mods.solidify(panel,.006);mods.apply_all(panel);hard(panel,P,.001)
            out.append(panel)
    return out

def cabin_values(y):return tuple(interp(L.CABIN,y,i) for i in range(1,5))
def cabin_section(y):
    z,w,bw,bz=cabin_values(y); h=z-bz
    return [(0,z+.003),(.72*w,z),(.97*w,z-.009),(w+.04*(bw-w),z-.032*h),
            (bw-.10*(bw-w),bz+.23*h),(bw,bz),(bw*.94,bz-.035),(0,bz-.035)]

def greenhouse(P):
    ys=sorted(set([r[0] for r in L.CABIN]+[L.CABIN[0][0]+(L.CABIN[-1][0]-L.CABIN[0][0])*i/(12 if P['stage']==1 else 48) for i in range(13 if P['stage']==1 else 49)]+[-.10,.650,.66,.680]))
    if P['stage']==1:ys=[r[0] for r in L.CABIN]
    rings=[]
    for y in ys:
        half=cabin_section(y); sec=half+[(-x,z) for x,z in half[-2:0:-1]]
        rings.append([(x,y,z) for x,z in sec])
    ob=mesh.loft_rings(nm(P,'CABIN_Structure'),P['coll'],rings,'MAT_GLASS',sharp_angle=48)
    ob.data.materials.append(bpy.data.materials['MAT_STEEL'])
    for f in ob.data.polygons:
        x,y,z=f.center; zt,wt,wb,zb=cabin_values(y)
        roof=(-.10<y<.66 and z>zt-.010)
        sill=z<zb+.027
        pillar=.650<y<.680
        rear=y>1.62
        if roof or sill or pillar or rear:f.material_index=1
    return [hard(ob,P,.0015)]

def cabin_x(y,z):
    sec=cabin_section(y)
    for (x0,z0),(x1,z1) in zip(sec[2:5],sec[3:6]):
        if z1<=z<=z0:return x0+(x1-x0)*(z0-z)/max(z0-z1,1e-8)
    return cabin_values(y)[2]

def frames(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        # Rail follows the very same cabin surface; no offset floating glass panels.
        pts=[]
        for i in range(24 if P['stage']>1 else 8):
            y=-.87+2.52*i/(23 if P['stage']>1 else 7); z,w,bw,bz=cabin_values(y)
            pts.append((sign*w,y,z-.006))
        out.append(tube(P,'CABIN_RoofRail_'+side,pts,.006,'MAT_BLACK'))
        pts=[]
        for i in range(18 if P['stage']>1 else 6):
            y=-.84+2.46*i/(17 if P['stage']>1 else 5);z,w,bw,bz=cabin_values(y)
            pts.append((sign*bw,y,bz+.013))
        out.append(tube(P,'CABIN_WindowSill_'+side,pts,.006,'MAT_BLACK'))
    for label,y in [('Cowl',-.84),('Header',-.10)]:
        z,w,bw,bz=cabin_values(y)
        out.append(tube(P,'CABIN_'+label,[(x,y,z+.006) for x in [-w,-w*.65,0,w*.65,w]],.006,'MAT_BLACK'))
    if P['stage']>1:
        for sign,side in [(1,'L'),(-1,'R')]:
            out.append(tube(P,'DOOR_RoofSeam_'+side,[(sign*.052,y,cabin_values(y)[0]+.007) for y in [-.08,.2,.5,.64]],.0016))
            y=.665;z,w,bw,bz=cabin_values(y)
            out.append(tube(P,'CABIN_Bpillar_'+side,[(sign*bw,y,bz+.03),(sign*(w+.07),y,z-.15),(sign*w,y,z-.02)],.009,'MAT_BLACK'))
    return out

def side_details(P):
    if P['stage']==1:
        return [box(P,'MIRROR_Housing_'+side,(sign*.999,-.585,.824),(.166,.115,.071),'MAT_STEEL') for sign,side in [(1,'L'),(-1,'R')]]
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        # Actual closed door skins and recessed seats are built with BODY_Main.
        # Belt inserts follow the waist, with front/rear pieces ending before the arch.
        for label,ya,yb in [('Center',-.90,.91),('Front',-2.14,-1.73),('Rear',1.76,2.16)]:
            pts=[(sign*(side_x(y,.535)+.002),y,.535) for y in [ya+(yb-ya)*k/16 for k in range(17)]]
            out.append(tube(P,'TRIM_Waist'+label+'_'+side,pts,.008))
        x=sign*(side_x(.59,.691)+.004)
        out.append(box(P,'DOOR_FlushHandle_'+side,(x,.59,.691),(.009,.112,.019),'MAT_BLACK',.003))
        # Sculpted mirror stem and tapered capsule at the A-pillar foot.
        out.append(tube(P,'MIRROR_Stem_'+side,[(sign*.823,-.62,.785),(sign*.927,-.58,.81),(sign*.969,-.58,.817)],.016,'MAT_BLACK'))
        out.append(box(P,'MIRROR_Housing_'+side,(sign*.999,-.585,.824),(.166,.115,.071),'MAT_STEEL',.015))
        out.append(box(P,'MIRROR_Glass_'+side,(sign*1.005,-.522,.824),(.132,.007,.045),'MAT_ALLOY',.005))
    return out

def fascia(P):
    out=[]
    # A slim flush black lamp mask between steel brow and lower bumper.
    out.append(box(P,'FRONT_LampMask',(0,-2.226,.533),(1.704,.017,.105),'MAT_BLACK',.025))
    out.append(box(P,'FRONT_LowerIntake',(0,-2.044,.302),(1.47,.013,.074),'MAT_BLACK',.003))
    out.append(box(P,'FRONT_BumperBlade',(0,-2.227,.427),(1.80,.050,.082),'MAT_STEEL',.012))
    out.append(box(P,'REAR_LightMask',(0,2.225,.572),(1.72,.018,.108),'MAT_BLACK',.021))
    out.append(box(P,'REAR_BumperBlade',(0,2.217,.427),(1.80,.055,.082),'MAT_BLACK',.019))
    for sign,side in [(1,'L'),(-1,'R')]:
        for j,x in enumerate([.475,.711]):
            out.append(box(P,'LIGHT_HeadHousing'+str(j)+'_'+side,(sign*x,-2.238,.533),(.212,.015,.083),'MAT_ALLOY',.01))
            out.append(box(P,'LIGHT_HeadLens'+str(j)+'_'+side,(sign*x,-2.247,.533),(.187,.007,.064),'MAT_WHITE',.008))
        for j,z in enumerate([.547,.589]):
            out.append(box(P,'LIGHT_Tail'+str(j)+'_'+side,(sign*.515,2.239,z),(.58,.008,.020),'MAT_RED',.005))
        out.append(box(P,'LIGHT_TurnRear_'+side,(sign*.84,2.238,.568),(.053,.008,.067),'MAT_AMBER',.005))
        out.append(box(P,'LIGHT_TurnFront_'+side,(sign*.734,-2.257,.425),(.12,.009,.014),'MAT_AMBER',.003))
        if P['stage']>1:
            for j in range(12):
                out.append(box(P,'LIGHT_TailDivider'+str(j)+'_'+side,(sign*(.24+j*.049),2.245,.568),(.004,.005,.073),'MAT_BLACK',.0007))
    if P['stage']>1:
        for j in range(15):
            out.append(box(P,'FRONT_IntakeFin'+str(j),(-.65+j*.093,-2.14,.302),(.008,.16,.064),'MAT_BLACK',.001))
    return out

def aero(P):
    out=[]
    # Thin plan-shaped splitter, not a full-height plough.
    poly=[(-.94,-1.91,.193),(-.98,-2.08,.193),(-.94,-2.255,.193),(-.76,-2.27,.193),
          (.76,-2.27,.193),(.94,-2.255,.193),(.98,-2.08,.193),(.94,-1.91,.193)]
    out.append(surface(P,'AERO_FrontSplitter',poly,[(x,y,z-.018) for x,y,z in poly],'MAT_BLACK',.004))
    for sign,side in [(1,'L'),(-1,'R')]:
        a=[(sign*.96,-.89,.224),(sign*.982,-.80,.203),(sign*.98,.82,.203),(sign*.958,.91,.23)]
        out.append(surface(P,'AERO_Sill_'+side,a,[(x,y,z+.035) for x,y,z in a],'MAT_BLACK',.005))
    out.append(box(P,'AERO_RearValance',(0,2.065,.29),(1.56,.025,.135),'MAT_BLACK',.025))
    if P['stage']>1:
        for j,x in enumerate([-.65,-.32,0,.32,.65]):
            a=[(x,1.86,.20),(x,2.22,.245),(x,2.22,.182),(x,1.86,.158)]
            out.append(surface(P,'AERO_DiffuserFin'+str(j),a,[(x+.013,y,z) for x,y,z in a],'MAT_BLACK',.002))
    return out

def louvres(P):
    out=[]
    n=3 if P['stage']==1 else 9
    for i in range(n):
        ya=.73+(.85*i/n); yb=.73+(.85*(i+1)/n)-.012
        za,wa,ba,_=cabin_values(ya);zb,wb,bb,_=cabin_values(yb)
        a=[(-wa*.91,ya,za+.014),(wa*.91,ya,za+.014),(wb*.91,yb,zb+.014),(-wb*.91,yb,zb+.014)]
        out.append(surface(P,'REAR_Louvre'+str(i),a,[(x,y,z-.012) for x,y,z in a],'MAT_BLACK',.002))
    return out

def hood(P):
    if P['stage']==1:return []
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        pts=[]
        for k in range(31):
            y=-2.04+1.14*k/30; sec=body_section(y);x=.56
            top=section_skin(y,12)[:61]
            z=next(z0+(z1-z0)*(x-x0)/(x1-x0) for (x0,z0),(x1,z1) in zip(top,top[1:]) if x0<=x<=x1)
            pts.append((sign*x,y,z+.0015))
        out.append(tube(P,'HOOD_Shutline_'+side,pts,.0017))
    return out

def wheels(P):
    out=[]
    for j,(y,r,w,track) in enumerate(L.WHEELS):
        for sign,side in [(1,'L'),(-1,'R')]:
            label=('Front' if j==0 else 'Rear')+'_'+side; center=(sign*track,y,r); rr=.255 if j==0 else .267
            prof=[(rr*.985,-w*.485),(r*.94,-w*.50),(r*.993,-w*.35),(r,-w*.23),(r,w*.23),(r*.993,w*.35),(r*.94,w*.50),(rr*.985,w*.485)]
            if P['stage']>1:
                # Four circumferential tread channels with beveled shoulders.
                tread=[(r,-w*.23)]
                for q in [-.18,-.06,.06,.18]:
                    tread.extend([(r,w*(q-.018)),(r-.0035,w*(q-.011)),(r-.0035,w*(q+.011)),(r,w*(q+.018))])
                prof=prof[:3]+tread+prof[4:]
            if P['stage']==1:prof=[(r,-w*.45),(r,w*.45),(rr*.7,w*.45),(rr*.7,-w*.45)]
            out.append(mesh.lathe(nm(P,'WHEEL_Tire_'+label),P['coll'],center,prof,P['wseg'],'MAT_RUBBER'))
            if P['stage']==1:
                out.append(mesh.cyl(nm(P,'WHEEL_Rim_'+label),P['coll'],(sign*(track-w*.2),y,r),(sign*(track+w*.46),y,r),rr,16,'MAT_ALLOY'))
                continue
            prof=[(rr*.88,-w*.42),(rr,-w*.42),(rr,w*.46),(rr*.967,w*.50),(rr*.884,w*.43),(rr*.868,w*.28)]
            out.append(hard(mesh.lathe(nm(P,'WHEEL_Rim_'+label),P['coll'],center,prof,P['wseg'],'MAT_ALLOY'),P,.001))
            face=sign*(track+w*.44)
            for k in range(P['spokes']):
                a=2*math.pi*k/P['spokes']; sweep=.14
                shape=[(.064,a-.045),(.068,a+.08),(rr*.90,a+sweep+.034),(rr*.90,a+sweep-.030)]
                pa=[(face,y+rad*math.cos(ang),r+rad*math.sin(ang)) for rad,ang in shape]
                pb=[(x-sign*.026,yy,z) for x,yy,z in pa]
                out.append(surface(P,'WHEEL_Spoke'+str(k)+'_'+label,pa,pb,'MAT_ALLOY',.0012))
            out.append(hard(mesh.cyl(nm(P,'WHEEL_Hub_'+label),P['coll'],(face-sign*.03,y,r),(face+sign*.008,y,r),.068,32,'MAT_ALLOY'),P,.002))
            out.append(mesh.cyl(nm(P,'WHEEL_Brake_'+label),P['coll'],(sign*(track+w*.14),y,r),(sign*(track+w*.18),y,r),rr*.81,64,'MAT_STEEL'))
            out.append(box(P,'WHEEL_Caliper_'+label,(sign*(track+w*.20),y-.145,r+.02),(.043,.078,.19),'MAT_AMBER',.016))
            for k in range(5):
                a=2*math.pi*k/5
                p=(face+sign*.011,y+.043*math.cos(a),r+.043*math.sin(a))
                out.append(mesh.cyl(nm(P,'WHEEL_Lug'+str(k)+'_'+label),P['coll'],p,(p[0]+sign*.006,p[1],p[2]),.007,6,'MAT_BLACK'))
            if P['detail']:
                for k,rad in enumerate([r*.92,r*.945]):
                    out.append(mesh.lathe(nm(P,'WHEEL_SidewallRing'+str(k)+'_'+label),P['coll'],center,[(rad,w*.502),(rad+.0015,w*.501),(rad+.0015,w*.506),(rad,w*.507)],64,'MAT_RUBBER'))
    return out

def cockpit(P):
    if P['stage']==1:return []
    out=[box(P,'INTERIOR_Dashboard',(0,-.64,.745),(1.40,.31,.11),'MAT_BLACK',.035),
         box(P,'INTERIOR_Console',(0,.02,.60),(.22,.86,.20),'MAT_BLACK',.035),
         box(P,'INTERIOR_Binnacle',(-.35,-.53,.814),(.35,.17,.073),'MAT_BLACK',.025)]
    for x,label in [(-.35,'Driver'),(.35,'Passenger')]:
        out.append(box(P,'INTERIOR_SeatBase_'+label,(x,.16,.53),(.48,.48,.17),'MAT_BLACK',.05))
        out.append(box(P,'INTERIOR_SeatBack_'+label,(x,.42,.75),(.46,.18,.46),'MAT_BLACK',.045))
        out.append(box(P,'INTERIOR_Headrest_'+label,(x,.45,1.012),(.24,.135,.12),'MAT_BLACK',.035))
        for sign in [-1,1]:
            out.append(box(P,'INTERIOR_Bolster'+('L' if sign>0 else 'R')+'_'+label,(x+sign*.175,.31,.74),(.09,.12,.34),'MAT_BLACK',.026))
    center=(-.35,-.37,.84)
    pts=[(center[0]+.128*math.cos(k*2*math.pi/48),center[1],center[2]+.128*math.sin(k*2*math.pi/48)) for k in range(49)]
    out.append(tube(P,'INTERIOR_SteeringRim',pts,.014,'MAT_BLACK',10))
    out.append(box(P,'INTERIOR_SteeringHub',center,(.115,.055,.07),'MAT_BLACK',.014))
    for k in [0,2.1,4.2]:
        out.append(tube(P,'INTERIOR_SteeringSpoke'+str(k),[center,(center[0]+.119*math.cos(k),center[1],center[2]+.119*math.sin(k))],.012,'MAT_ALLOY',6))
    return out

def fittings(P):
    if P['stage']==1:return []
    out=[]
    # Two parked wipers sit against the actual windscreen, with a blade and arm.
    for j,xa in enumerate([-.56,.08]):
        pts=[]
        for k in range(10):
            x=xa+k*.048;y=-.782+k*.009;z=cabin_values(y)[0]+.009
            pts.append((x,y,z))
        out.append(tube(P,'GLASS_WiperBlade'+str(j),pts,.005,'MAT_BLACK',8))
        out.append(tube(P,'GLASS_WiperArm'+str(j),[(xa+.10,-.846,.761),pts[4]],.003,'MAT_BLACK',8))
    for sign,label in [(1,'L'),(-1,'R')]:
        rings=[]
        for rad,y in [(.044,2.14),(.044,2.25),(.037,2.25),(.037,2.14)]:
            rings.append([(sign*.64+rad*math.cos(k*math.tau/32),y,.238+rad*math.sin(k*math.tau/32)) for k in range(32)])
        vv=[v for row in rings for v in row];ff=[]
        for row in range(4):
            for k in range(32):ff.append((row*32+k,row*32+(k+1)%32,((row+1)%4)*32+(k+1)%32,((row+1)%4)*32+k))
        out.append(hard(mesh.from_pydata(nm(P,'EXHAUST_Tip_'+label),P['coll'],vv,ff,'MAT_ALLOY'),P,.0008))
        out.append(mesh.cyl(nm(P,'EXHAUST_Bore_'+label),P['coll'],(sign*.64,2.15,.238),(sign*.64,2.16,.238),.037,32,'MAT_BLACK'))
        for j in range(2):
            x=sign*(.475 if j==0 else .711)
            for k in range(9):
                out.append(box(P,'LIGHT_LensFlute'+str(j)+'_'+str(k)+'_'+label,(x-.078+k*.0195,-2.251,.533),(.0014,.002,.052),'MAT_WHITE',.0003))
    return out

def undertray(P):return [box(P,'UNCERTAIN_Undertray',(0,.05,.211),(1.29,3.8,.029),'MAT_BLACK',.007)]
PARTS=[Part('body',body,collision='hull'),Part('greenhouse',greenhouse,collision='hull'),
 Part('frames',frames,collision='none'),Part('trim',side_details,collision='none'),
 Part('fascia',fascia,collision='box'),Part('aero',aero,collision='box'),
 Part('louvres',louvres,collision='none'),Part('hood',hood,collision='none'),
 Part('wheels',wheels,collision='hull'),Part('fittings',fittings,collision='none'),Part('cockpit',cockpit,collision='none'),Part('undertray',undertray,collision='box')]
for j,(y,r,w,t) in enumerate(L.WHEELS):
    for sign,side in [(1,'L'),(-1,'R')]:
        label=('Front' if j==0 else 'Rear')+'_'+side; tire='WHEEL_Tire_'+label
        PIVOTS[tire]=lambda y=y,r=r,t=t,sign=sign:(sign*t,y,r)
        for base in ['Rim','Hub','Brake']+[f'Spoke{k}' for k in range(20)]+[f'Lug{k}' for k in range(5)]+[f'SidewallRing{k}' for k in range(2)]:
            CHILDREN['WHEEL_'+base+'_'+label]=tire

def after_build(stage,objs):
    if stage>=2:
        glass=bpy.data.materials['MAT_GLASS'].node_tree.nodes.get('Principled BSDF')
        glass.inputs['Transmission Weight'].default_value=.88
        glass.inputs['IOR'].default_value=1.46
        glass.inputs['Thin Wall'].default_value=True
    if stage==3:
        rubber=bpy.data.materials['MAT_RUBBER'];rn=rubber.node_tree;rb=rn.nodes.get('Principled BSDF')
        noise=rn.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=420
        noise.inputs['Detail'].default_value=2
        bump=rn.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00015
        rn.links.new(noise.outputs['Fac'],bump.inputs['Height']);rn.links.new(bump.outputs['Normal'],rb.inputs['Normal'])
        steel=bpy.data.materials['MAT_STEEL'];nt=steel.node_tree;b=nt.nodes.get('Principled BSDF')
        b.inputs['Anisotropic'].default_value=.35
        geo=nt.nodes.new('ShaderNodeNewGeometry');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
        scale.inputs[1].default_value=(1800,5,1800)
        noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1
        noise.inputs['Detail'].default_value=2
        bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.000018
        nt.links.new(geo.outputs['Position'],scale.inputs[0]);nt.links.new(scale.outputs[0],noise.inputs['Vector'])
        nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],b.inputs['Normal'])
    # Triangulate n-gon endcaps before UV/export for stable game tessellation.
    for ob in objs:
        bm=bmesh.new();bm.from_mesh(ob.data)
        faces=[f for f in bm.faces if len(f.verts)>4]
        if faces:bmesh.ops.triangulate(bm,faces=faces)
        bm.to_mesh(ob.data);bm.free()

