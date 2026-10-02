"""Deterministic hard-surface DeLorean; every stage shares measured pixel landmarks."""
import math
from mathutils import Vector
import landmarks as L
from workbench import tables,stages
from workbench.stages import Part
from workbench.bl import mesh,mods,prim
mesh.set_ref(L.REF)
CATEGORY='hero_vehicle'
TARGET_DIMS=(None,4.213,1.136)
GROUND=True
PROFILES={1:stages.profile(1,ring=12,arch_step=10,wseg=16,spokes=0),
          2:stages.profile(2,ring=16,arch_step=3,wseg=64,spokes=32),
          3:stages.profile(3,ring=16,arch_step=3,wseg=64,spokes=32)}
GAME=dict(engine='godot',bake=True,lod=(.5,.25))
PALETTE={'MAT_BODY':((.51,.54,.56),1.,.32),'MAT_TRIM':'plastic_black',
         'MAT_TIRE':'rubber','MAT_RIM':((.65,.67,.69),.92,.26),
         'MAT_GLASS':((.024,.038,.043),.35,.12),
         'MAT_LAMP':((.71,.79,.82),.25,.12),'MAT_RED':((.46,.009,.014),.0,.23),
         'MAT_AMBER':((.85,.24,.012),.0,.24)}
CRITICAL_PAIRS=[('WHEEL_Tire','BODY_Shell')]
UNCERTAIN=['UNCERTAIN_Underbody','UNCERTAIN_WheelWellLiners','UNCERTAIN_Interior','UNCERTAIN_BodyWidths',
           'UNCERTAIN_RearEngineBay','UNCERTAIN_DoorHingeDepth']
ASSUMPTIONS=['AI-sheet side view is primary truth by user decision; printed dimensions approximate',
             'Approximate stock width and track used for depth; bilateral symmetry assumed',
             'Godot glTF delivery selected from existing project; no engine preference supplied']
KNOWN_LIMITATIONS=['No real photo supplied; fidelity is to the sheet concept, not a verified stock car',
                   'Opaque tinted glazing; cockpit and hidden mechanical components not reconstructed',
                   'Static closed doors; wheel pivots provided, no opening animation or exposed door interior',
                   'Sheet tire sizes contradict drawing; drawn proportions preserved',
                   'No logos or numberplate text; no photogrammetric surface detail']
LICENCE='User-supplied reference; model generated locally from code.'
PIVOTS={}
CHILDREN={}
Y=lambda u:L.P(u,0)[0]
Z=lambda v:L.P(0,v)[1]
def nm(P,n):return stages.nm(P,n)
def hard(o,P,b=.003):return mods.finish_hard(o,b,enabled=P['bevel'])
def bx(P,n,uv,size,x=0,mat='MAT_BODY',b=.003):
    return hard(mesh.box(nm(P,n),P['coll'],L.P3(*uv,x),size,mat),P,b)
def pl(P,n,poly,x0,x1,mat='MAT_BODY',b=.002):
    return hard(mesh.plate(nm(P,n),P['coll'],poly,x0,x1,mat),P,b)
def line(P,n,pts,r=.0025,mat='MAT_TRIM'):
    return hard(mesh.tube(nm(P,n),P['coll'],pts,r,6,mat,smooth_path=False),P,.001)
def shell(P):
    us={u for u,v in L.BODY_TOP}|{u for u,v in L.BODY_BOTTOM}
    for c,a in zip(L.WHEEL_U,L.ARCH_R):
        us|={c-a,c+a}
        us|={c+a*math.cos(math.pi*k/(P['arch_step'] if P['stage']==1 else 42)) for k in range((P['arch_step'] if P['stage']==1 else 42)+1)}
    rings=[]
    for u in sorted(x for x in us if 9<=x<=516):
        vt=tables.polyline_v(L.BODY_TOP,u); vb=tables.polyline_v(L.BODY_BOTTOM,u)
        for c,v,a in zip(L.WHEEL_U,L.WHEEL_V,L.ARCH_R):
            if abs(u-c)<=a:vb=min(vb,v-math.sqrt(max(0,a*a-(u-c)**2)))
        vb=max(vb,vt+3)
        hw=tables.interp(L.BODY_HALF_W,u)
        shoulder=min(vt+6,vb-1); lower=max(shoulder,vb-2)
        # Crisp wedge sections; panel curvature is never subdivided.
        sec=[(hw*.76,vt),(hw*.97,shoulder),(hw,lower),(hw*.86,vb),
             (-hw*.86,vb),(-hw,lower),(-hw*.97,shoulder),(-hw*.76,vt)]
        rings.append([L.P3(u,v,x) for x,v in sec])
    return [hard(mesh.loft_rings(nm(P,'BODY_Shell'),P['coll'],rings,'MAT_BODY',smooth=False),P,.003)]
def cabin_x(u,v):
    vt=tables.polyline_v(L.ROOF_TOP,u); ht=tables.interp(L.CABIN_HW,u)
    return ht+(.855-ht)*max(0,min(1,(v-vt)/(L.CABIN_BASE-vt)))
def cabin(P):
    rings=[]
    for u,vt in L.ROOF_TOP:
        hw=tables.interp(L.CABIN_HW,u); vb=L.CABIN_BASE
        sec=[(hw*.72,vt),(hw,vt+1.3),(.855,vb),(.82,vb+6),(-.82,vb+6),(-.855,vb),(-hw,vt+1.3),(-hw*.72,vt)]
        rings.append([L.P3(u,v,x) for x,v in sec])
    return [hard(mesh.loft_rings(nm(P,'CABIN_Greenhouse'),P['coll'],rings,'MAT_BODY',smooth=False),P,.003)]
def glass(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        for label,poly in [('Door',L.WINDOW_SIDE),('Quarter',L.WINDOW_QUARTER)]:
            pa=[L.P3(u,v,sign*(cabin_x(u,v)+.008)) for u,v in poly]
            pb=[Vector(p)-Vector((sign*.006,0,0)) for p in pa]
            out.append(hard(mesh.extrude_polys(nm(P,'GLASS_'+label+'_'+side),P['coll'],[(pa,pb)],'MAT_GLASS'),P,.001))
    # Follow every roof-slope break; a single flat quad penetrates the roof.
    rings=[]
    for u,w in [(180,.727),(184,.715),(220,.63),(249,.574)]:
        v=tables.polyline_v(L.ROOF_TOP,u)-.35
        rings.append([L.P3(u,v,x) for x in [-w,w]]+[L.P3(u,v+.15,x) for x in [w,-w]])
    out.append(hard(mesh.loft_rings(nm(P,'GLASS_Windshield'),P['coll'],rings,'MAT_GLASS',smooth=False),P,.0006))
    return out

def hood(P):
    rings=[]
    for u in [27,40,114,151]:
        v=tables.polyline_v(L.BODY_TOP,u)
        w=tables.interp([(27,.64),(151,.70)],u)
        rings.append([L.P3(u,v-.12,x) for x in [-w,w]]+[L.P3(u,v+.25,x) for x in [w,-w]])
    return [hard(mesh.loft_rings(nm(P,'BODY_Hood'),P['coll'],rings,'MAT_BODY',smooth=False),P,.0007)]
def bumpers(P):
    out=[pl(P,'BUMPER_Front',[(9,84),(25,83),(27,104),(9,101)],-.82,.82,'MAT_TRIM'),
         pl(P,'BUMPER_Rear',[(505,79),(516,81),(516,98),(505,104)],-.84,.84,'MAT_TRIM')]
    return out

def splitter(P):
    return [pl(P,'AERO_Splitter',[(25,112),(68,121),(72,130),(15,132),(10,130),(23,122)],-.89,.89,'MAT_TRIM'),
            pl(P,'BUMPER_LowerIntake',[(25,103),(69,114),(72,129),(25,126)],-.74,.74,'MAT_TRIM')]
def skirts(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        a,b=sorted([sign*.88,sign*.96])
        out.append(pl(P,'AERO_Skirt_'+side,[(160,119),(370,118),(373,128),(160,131)],a,b,'MAT_TRIM'))
    return out

def diffuser(P):
    out=[pl(P,'AERO_RearDiffuser',[(461,117),(504,104),(504,112),(462,127)],-.83,.83,'MAT_TRIM')]
    if P['detail']:
        for i,x in enumerate([-.60,-.3,0,.3,.6]):
            out.append(pl(P,'AERO_DiffuserFin'+str(i),[(465,117),(501,106),(501,115),(465,128)],x-.008,x+.008,'MAT_TRIM'))
    return out

def louvres(P):
    out=[]
    n=3 if P['stage']==1 else 9
    for i in range(n):
        u=349+(476-349)*i/n; un=349+(476-349)*(i+1)/n
        v=tables.polyline_v(L.ROOF_TOP,u)-.5; vn=tables.polyline_v(L.ROOF_TOP,un)-.5
        w=tables.interp(L.CABIN_HW,u)*.88
        pa=[L.P3(u,v,x) for x in [-w,w]]+[L.P3(un-1,vn,x) for x in [w,-w]]
        pb=[Vector(p)-Vector((0,0,.018)) for p in pa]
        out.append(hard(mesh.extrude_polys(nm(P,'REAR_Louvre'+str(i)),P['coll'],[(pa,pb)],'MAT_TRIM'),P,.001))
    return out

def mirrors(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        out.append(pl(P,'TRIM_Mirror_'+side,[(202,45),(212,44),(214,54),(203,59),(198,53)],*sorted([sign*.875,sign*1.01]),'MAT_TRIM'))
        if P['stage']>=2:
            out.append(bx(P,'TRIM_MirrorGlass_'+side,(211,51),(.09,.008,.053),sign*.95,'MAT_GLASS',.001))
    return out

def trim(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        for i,(a,b) in enumerate([(35,68),(158,373),(462,505)]):
            out.append(pl(P,'TRIM_Belt'+str(i)+'_'+side,[(a,80),(b,78),(b,81),(a,83)],*sorted([sign*.926,sign*.936]),'MAT_TRIM',.001))
        out.append(bx(P,'DOOR_Handle_'+side,(328,82),(.013,.17,.027),sign*.943,'MAT_TRIM',.001))
        if P['stage']>=2:
            out.append(line(P,'DOOR_Seam_'+side,[L.P3(u,v,sign*(cabin_x(u,v)+.011 if v<70 else .912)) for u,v in L.DOOR_SEAM],.0018))
            out.append(bx(P,'DOOR_Lock_'+side,(330,62),(.015,.016,.017),sign*(cabin_x(330,62)+.01),'MAT_TRIM',.001))
    if P['detail']:
        for sign,side in [(1,'L'),(-1,'R')]:
            out.append(line(P,'BODY_HoodSeam_'+side,[L.P3(u,v,sign*.74) for u,v in L.HOOD_EDGE],.0018))
        out.append(line(P,'TRIM_Antenna',[L.P3(486,42,-.77),L.P3(489,22,-.77)],.0018,'MAT_TRIM'))
    return out

def lamps(P):
    out=[]
    for sign,side in [(1,'L'),(-1,'R')]:
        for j,x in enumerate([.39,.64]):
            out.append(bx(P,'LIGHT_Head'+str(j)+'_'+side,(8.8,89),(.20,.018,.11),sign*x,'MAT_LAMP',.003))
        out.append(bx(P,'LIGHT_FrontIndicator_'+side,(12,101),(.21,.015,.034),sign*.60,'MAT_AMBER',.001))
        out.append(bx(P,'LIGHT_RearCluster_'+side,(516.5,88),(.46,.007,.115),sign*.54,'MAT_RED',.001))
        out.append(bx(P,'LIGHT_RearIndicator_'+side,(516.8,88),(.12,.007,.115),sign*.72,'MAT_AMBER',.001))
        for label,u,v in [('Front',48,84),('Rear',480,83)]:
            out.append(bx(P,'LIGHT_Sidemarker'+label+'_'+side,(u,v),(.012,.20,.015),sign*.935,'MAT_AMBER',.001))
        if P['detail']:
            for k in range(5):
                out.append(bx(P,'LIGHT_RearGrid'+str(k)+'_'+side,(517.2,88),(.009,.006,.12),sign*(.35+k*.08),'MAT_TRIM',.0005))
    out.append(bx(P,'TRIM_FrontGrille',(8.5,89),(.54,.02,.12),0,'MAT_TRIM',.001))
    out.append(bx(P,'TRIM_RearPlate',(517,99),(.36,.014,.12),0,'MAT_AMBER',.002))
    return out

def wheels(P):
    out=[]
    for j,(u,v,r,rr,w,t) in enumerate(zip(L.WHEEL_U,L.WHEEL_V,L.TIRE_R_PX,L.RIM_R_PX,L.TIRE_W,L.TRACK_X)):
        rad=r/L.S; rim=rr/L.S
        for sign,side in [(1,'L'),(-1,'R')]:
            label=('Front' if j==0 else 'Rear')+'_'+side
            center=L.P3(u,v,sign*t)
            if P['stage']==1:
                out.append(prim.wheel_px(nm(P,'WHEEL_Tire_'+label),P['coll'],(u,v),r,w/2,P['wseg'],'MAT_TIRE',x=sign*t))
                continue
            prof=[(rim*.96,-w*.49),(rad*.93,-w*.49),(rad,-w*.32),(rad,w*.32),(rad*.94,w*.49),(rim*.96,w*.49)]
            out.append(mesh.lathe(nm(P,'WHEEL_Tire_'+label),P['coll'],center,prof,P['wseg'],'MAT_TIRE'))
            rp=[(rim*.78,-w*.43),(rim,-w*.43),(rim,w*.48),(rim*.90,w*.48),(rim*.78,w*.30)]
            out.append(hard(mesh.lathe(nm(P,'WHEEL_Rim_'+label),P['coll'],center,rp,P['wseg'],'MAT_RIM'),P,.0015))
            out.append(mesh.cyl(nm(P,'WHEEL_Hub_'+label),P['coll'],L.P3(u,v,sign*(t+w*.32)),L.P3(u,v,sign*(t+w*.50)),rim*.23,24,'MAT_RIM'))
            out.append(mesh.cyl(nm(P,'WHEEL_Recess_'+label),P['coll'],L.P3(u,v,sign*(t+w*.15)),L.P3(u,v,sign*(t+w*.21)),rim*.80,48,'MAT_TRIM'))
            # Period turbine spokes with offset sweep, clear openings and solid topology.
            for k in range(P['spokes']):
                a=2*math.pi*k/P['spokes']; b=a+.10
                c=Vector(center); x=sign*(t+w*.46)
                aa=(x,c.y+rim*.24*math.cos(a),c.z+rim*.24*math.sin(a))
                bb=(x,c.y+rim*.91*math.cos(b),c.z+rim*.91*math.sin(b))
                out.append(hard(mesh.cyl(nm(P,'WHEEL_Spoke'+str(k)+'_'+label),P['coll'],aa,bb,.006,5,'MAT_RIM'),P,.0006))
            if P['detail']:
                for k in range(4):
                    a=2*math.pi*k/4
                    out.append(mesh.cyl(nm(P,'WHEEL_Lug'+str(k)+'_'+label),P['coll'],L.P3(u+5*math.cos(a),v+5*math.sin(a),sign*(t+w*.50)),L.P3(u+5*math.cos(a),v+5*math.sin(a),sign*(t+w*.54)),.008,8,'MAT_RIM'))
    return out

def underbody(P):
    out=[bx(P,'UNCERTAIN_Underbody',(266,112),(1.36,1.6,.055),0,'MAT_TRIM')]
    for j,(u,v,a) in enumerate(zip(L.WHEEL_U,L.WHEEL_V,L.ARCH_R)):
        for sign,side in [(1,'L'),(-1,'R')]:
            # Visible dark cavity, depth unknown. Behind wheel, separate from shell.
            rad=a+.2
            arc=[(u+rad*math.cos(math.pi-k*math.pi/48),v-rad*math.sin(math.pi-k*math.pi/48)) for k in range(49)]
            poly=[(u-rad,130)]+arc+[(u+rad,130)]
            out.append(pl(P,'UNCERTAIN_WheelWell'+str(j)+'_'+side,poly,
                *sorted([sign*.61,sign*.63]),'MAT_TRIM',.001))
    return out

PARTS=[Part('body',shell,collision='hull'),Part('cabin',cabin,collision='hull'),
       Part('hood',hood,collision='box'),Part('glass',glass,collision='none'),
       Part('bumpers',bumpers,collision='box'),Part('splitter',splitter,collision='box'),
       Part('skirts',skirts,collision='box'),Part('diffuser',diffuser,collision='box'),
       Part('louvres',louvres,collision='box'),Part('mirrors',mirrors,collision='box'),
       Part('trim',trim,collision='none'),Part('lamps',lamps,collision='none'),
       Part('wheels',wheels,collision='hull'),Part('underbody',underbody,collision='box')]
for j,(u,v,t) in enumerate(zip(L.WHEEL_U,L.WHEEL_V,L.TRACK_X)):
    for sign,side in [(1,'L'),(-1,'R')]:
        label=('Front' if j==0 else 'Rear')+'_'+side
        tire='WHEEL_Tire_'+label
        PIVOTS[tire]=lambda u=u,v=v,t=t,sign=sign:L.P3(u,v,sign*t)
        for base in ['WHEEL_Rim','WHEEL_Hub','WHEEL_Recess']:
            CHILDREN[base+'_'+label]=tire
        for k in range(32):CHILDREN['WHEEL_Spoke'+str(k)+'_'+label]=tire
        for k in range(4):CHILDREN['WHEEL_Lug'+str(k)+'_'+label]=tire

def guide_points():return {'ANCHOR':L.ANCHORS[0][0]}
