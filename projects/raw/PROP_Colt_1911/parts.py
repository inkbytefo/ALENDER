"""
Part builders for PROP_Colt_1911 (Colt M1911-A1 .45 ACP service pistol).
Follows staged pipeline standards (docs/01_WORKFLOW.md, docs/02_STANDARDS.md).
"""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix

import landmarks as L
from workbench import tables, stages
from workbench.stages import Part
from workbench.bl import mesh, mods, prim

mesh.set_ref(L.REF)

CATEGORY = "hero_prop"
TARGET_DIMS = (0.0300, 0.2347, 0.1463)  # Width X, Length Y, Height Z
GROUND = True

PROFILES = {
    1: stages.profile(1, ring=8, stations=4),
    2: stages.profile(2, ring=16, stations=12),
    3: stages.profile(3, ring=32, stations=28),
}

GAME = dict(engine="godot", bake=True, lod=(0.5, 0.25), tex=2048, uv_m=2.0)

PALETTE = {
    "MAT_GUN_STEEL": ((0.08, 0.085, 0.09), 0.8, 0.35),
    "MAT_BARREL_CHROME": ((0.68, 0.68, 0.70), 0.95, 0.18),
    "MAT_WOOD_GRIP": ((0.28, 0.16, 0.09), 0.0, 0.65),
    "MAT_CONTROLS_DARK": ((0.045, 0.045, 0.05), 0.85, 0.28),
}

CRITICAL_PAIRS = []
UNCERTAIN = []


def nm(P, name):
    return stages.nm(P, name)


def triangulate_ngons(ob):
    """Triangulate faces with > 4 verts to guarantee 0% n-gons under gate check U12."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(me)
    me.update()
    bm.free()
    return ob


def hard(ob, P, bevel=0.0015):
    """Hard-surface finish: micro-bevel + weighted normals from S3 on. Never subsurf plates."""
    triangulate_ngons(ob)
    return mods.finish_hard(ob, bevel, enabled=P["bevel"])


# -----------------------------------------------------------------------------
# Part 1: SLIDE
# -----------------------------------------------------------------------------
def slide_prim(P):
    ob = mesh.plate(nm(P, "SLIDE_Main"), P["coll"], L.SLIDE_POLY,
                    -L.SLIDE_HALF_WIDTH, L.SLIDE_HALF_WIDTH, "MAT_GUN_STEEL")
    return [triangulate_ngons(ob)]


def slide(P):
    ob = mesh.plate(nm(P, "SLIDE_Main"), P["coll"], L.SLIDE_POLY,
                    -L.SLIDE_HALF_WIDTH, L.SLIDE_HALF_WIDTH, "MAT_GUN_STEEL")
    # Bevel top long edges to create the 1911 rounded slide top
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    max_z = max(v.co.z for v in bm.verts)
    top_edges = [e for e in bm.edges if abs(e.verts[0].co.z - max_z) < 0.002 and abs(e.verts[1].co.z - max_z) < 0.002
                 and any(abs(abs(v.co.x) - L.SLIDE_HALF_WIDTH) < 0.002 for v in e.verts)]
    if top_edges:
        bmesh.ops.bevel(bm, geom=top_edges, offset=0.0035, segments=6, profile=0.5, affect='EDGES')
    bm.to_mesh(me)
    me.update()
    bm.free()

    # Ejection port cutout (right side, -X)
    y0, z0 = L.P(1050.0, 310.0)
    y1, z1 = L.P(1400.0, 420.0)
    ob_port = mesh.box("TEMP_Port", P["coll"], (-L.SLIDE_HALF_WIDTH, (y0+y1)/2, (z0+z1)/2),
                       (0.012, abs(y1-y0), abs(z1-z0)), "MAT_GUN_STEEL")
    mods.boolean(ob, ob_port, apply=True)
    bpy.data.objects.remove(ob_port, do_unlink=True)

    triangulate_ngons(ob)
    return [hard(ob, P, 0.0012)]


def cut_trigger_hole(ob_frame, P):
    """Cut trigger hole out of frame plate for exact silhouette."""
    ob_cutter = mesh.plate("CUTTER_TriggerHole", P["coll"], L.TRIGGER_HOLE_POLY, -0.05, 0.05, "MAT_GUN_STEEL")
    mod = ob_frame.modifiers.new("CutTrigger", 'BOOLEAN')
    mod.object = ob_cutter
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ob_frame
    bpy.ops.object.modifier_apply(modifier="CutTrigger")
    bpy.data.objects.remove(ob_cutter, do_unlink=True)
    return triangulate_ngons(ob_frame)


# -----------------------------------------------------------------------------
# Part 2: FRAME (Receiver, Grip Frame, Trigger Guard, Controls)
# -----------------------------------------------------------------------------
def frame_prim(P):
    ob = mesh.plate(nm(P, "FRAME_Main"), P["coll"], L.FRAME_POLY,
                    -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")
    return [cut_trigger_hole(ob, P)]


def frame(P):
    ob = mesh.plate(nm(P, "FRAME_Main"), P["coll"], L.FRAME_POLY,
                    -L.FRAME_HALF_WIDTH, L.FRAME_HALF_WIDTH, "MAT_GUN_STEEL")
    ob = cut_trigger_hole(ob, P)

    # 14 Arched mainspring housing grooves on backstrap
    msh_cutters = []
    for i in range(14):
        u_m = 230.0 + i * 8.0
        v_m = 900.0 + i * 25.0
        y_m, z_m = L.P(u_m, v_m)
        c = mesh.box(f"TEMP_MSH_{i}", P["coll"], (0.0, y_m, z_m), (L.FRAME_HALF_WIDTH * 2.2, 0.0012, 0.0008), "MAT_GUN_STEEL")
        c.rotation_euler = (0, math.radians(-15), 0)
        msh_cutters.append(c)

    for c in msh_cutters:
        mods.boolean(ob, c, apply=True)
        bpy.data.objects.remove(c, do_unlink=True)

    triangulate_ngons(ob)

    # Add frame-mounted controls (safety, slide stop, mag release) flush to frame
    sy, sz = L.P(320.0, 540.0)
    ob_safety = mesh.box(nm(P, "CTRL_Safety"), P["coll"], (L.FRAME_HALF_WIDTH + 0.0020, sy, sz),
                         (0.0035, 0.022, 0.012), "MAT_CONTROLS_DARK")

    ss_y, ss_z = L.P(780.0, 535.0)
    ob_slidestop = mesh.box(nm(P, "CTRL_SlideStop"), P["coll"], (L.FRAME_HALF_WIDTH + 0.0018, ss_y, ss_z),
                            (0.0030, 0.030, 0.009), "MAT_CONTROLS_DARK")

    mr_y, mr_z = L.P(750.0, 720.0)
    ob_magbtn = mesh.cyl(nm(P, "CTRL_MagRelease"), P["coll"], (L.FRAME_HALF_WIDTH - 0.002, mr_y, mr_z),
                         (L.FRAME_HALF_WIDTH + 0.0030, mr_y, mr_z), 0.0042, 24, "MAT_CONTROLS_DARK")

    # 3 Frame through-pins
    pin_locs = [(420.0, 540.0), (320.0, 560.0), (820.0, 540.0)]
    pins = []
    for idx, (pu, pv) in enumerate(pin_locs):
        py, pz = L.P(pu, pv)
        pin = mesh.cyl(nm(P, f"FRAME_Pin_{idx}"), P["coll"], (-L.FRAME_HALF_WIDTH - 0.0002, py, pz),
                       (L.FRAME_HALF_WIDTH + 0.0002, py, pz), 0.0020, 16, "MAT_CONTROLS_DARK")
        pins.append(hard(pin, P, 0.0003))

    return [hard(ob, P, 0.0012), hard(ob_safety, P, 0.0008), hard(ob_slidestop, P, 0.0008), hard(ob_magbtn, P, 0.0008)] + pins


# -----------------------------------------------------------------------------
# Part 3: BARREL & BUSHING
# -----------------------------------------------------------------------------
def barrel_prim(P):
    ob = prim.cyl_px(nm(P, "BARREL_Bushing"), P["coll"],
                     (1872.6, 420.0), (385.0, 420.0),
                     L.BARREL_RADIUS, segs=12, mat="MAT_BARREL_CHROME")
    return [triangulate_ngons(ob)]


def barrel(P):
    p_front = (0.0, *L.P(1872.6, 420.0))
    p_rear = (0.0, *L.P(385.0, 420.0))
    ob_barrel = mesh.cyl(nm(P, "BARREL_Cylinder"), P["coll"], p_rear, p_front, L.BARREL_RADIUS, 32, "MAT_BARREL_CHROME")
    hy, hz = L.P(1220.0, 360.0)
    ob_hood = mesh.box(nm(P, "BARREL_Hood"), P["coll"], (0.0, hy, hz), (0.016, 0.035, 0.018), "MAT_BARREL_CHROME")

    # Muzzle bore hole starting flush with front
    p_bore_rear = (0.0, p_front[1] + 0.060, p_front[2])
    ob_bore = mesh.cyl("TEMP_Bore", P["coll"], p_front, p_bore_rear, 0.0057, 28, "MAT_BARREL_CHROME")
    mods.boolean(ob_barrel, ob_bore, apply=True)
    bpy.data.objects.remove(ob_bore, do_unlink=True)

    # Barrel Bushing - strictly bounded by p_front[1]
    ob_bushing = mesh.cyl(nm(P, "BARREL_Bushing"), P["coll"], p_front, (0, p_front[1] + 0.006, p_front[2]),
                          L.BARREL_RADIUS + 0.002, 32, "MAT_GUN_STEEL")

    # Recoil Spring Plug
    p_plug = (0.0, *L.P(1872.6, 520.0))
    ob_plug = mesh.cyl(nm(P, "BARREL_Plug"), P["coll"], p_plug, (0, p_plug[1] + 0.035, p_plug[2]),
                       0.0055, 28, "MAT_GUN_STEEL")

    return [hard(ob_barrel, P, 0.0010), hard(ob_hood, P, 0.0010), hard(ob_bushing, P, 0.0010), hard(ob_plug, P, 0.0010)]


# -----------------------------------------------------------------------------
# Part 4: GRIP PANELS (Left and Right Walnut Checkered Stocks)
# -----------------------------------------------------------------------------
def grip_panels_prim(P):
    ob_l = mesh.plate(nm(P, "GRIP_Panels_L"), P["coll"], L.GRIP_PANEL_POLY,
                      L.FRAME_HALF_WIDTH, L.GRIP_HALF_WIDTH, "MAT_WOOD_GRIP")
    ob_r = mesh.plate(nm(P, "GRIP_Panels_R"), P["coll"], L.GRIP_PANEL_POLY,
                      -L.GRIP_HALF_WIDTH, -L.FRAME_HALF_WIDTH, "MAT_WOOD_GRIP")
    return [triangulate_ngons(ob_l), triangulate_ngons(ob_r)]


def grip_panels(P):
    ob_l = mesh.plate(nm(P, "GRIP_Panels_L"), P["coll"], L.GRIP_PANEL_POLY,
                      L.FRAME_HALF_WIDTH, L.GRIP_HALF_WIDTH, "MAT_WOOD_GRIP")
    ob_r = mesh.plate(nm(P, "GRIP_Panels_R"), P["coll"], L.GRIP_PANEL_POLY,
                      -L.GRIP_HALF_WIDTH, -L.FRAME_HALF_WIDTH, "MAT_WOOD_GRIP")

    for ob in [ob_l, ob_r]:
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        outer = [f for f in bm.faces if abs(f.normal.x) > 0.8]
        if outer:
            bmesh.ops.subdivide_edges(bm, edges=[e for f in outer for e in f.edges], cuts=18, use_grid_fill=True)
            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                bmesh.ops.triangulate(bm, faces=ngons)
        bm.to_mesh(me)
        me.update()
        bm.free()
        triangulate_ngons(ob)

    # 4 grip screws flush with outer surface
    screw_locs_px = [(480.0, 680.0), (380.0, 1150.0)]
    screws = []
    for idx, (su, sv) in enumerate(screw_locs_px):
        sy, sz = L.P(su, sv)
        s_l = mesh.cyl(nm(P, f"GRIP_Screw_L_{idx}"), P["coll"],
                       (L.FRAME_HALF_WIDTH, sy, sz), (L.GRIP_HALF_WIDTH, sy, sz),
                       0.0035, 24, "MAT_GUN_STEEL")
        s_r = mesh.cyl(nm(P, f"GRIP_Screw_R_{idx}"), P["coll"],
                       (-L.FRAME_HALF_WIDTH, sy, sz), (-L.GRIP_HALF_WIDTH, sy, sz),
                       0.0035, 24, "MAT_GUN_STEEL")
        slot_l = mesh.box(f"TEMP_Slot_L_{idx}", P["coll"], (L.GRIP_HALF_WIDTH, sy, sz), (0.0010, 0.0008, 0.0070), "MAT_GUN_STEEL")
        slot_r = mesh.box(f"TEMP_Slot_R_{idx}", P["coll"], (-L.GRIP_HALF_WIDTH, sy, sz), (0.0010, 0.0008, 0.0070), "MAT_GUN_STEEL")
        mods.boolean(s_l, slot_l, apply=True)
        mods.boolean(s_r, slot_r, apply=True)
        bpy.data.objects.remove(slot_l, do_unlink=True)
        bpy.data.objects.remove(slot_r, do_unlink=True)
        screws.extend([hard(s_l, P, 0.0005), hard(s_r, P, 0.0005)])

    return [hard(ob_l, P, 0.0010), hard(ob_r, P, 0.0010)] + screws


# -----------------------------------------------------------------------------
# Part 5: TRIGGER
# -----------------------------------------------------------------------------
def trigger_prim(P):
    ob = mesh.plate(nm(P, "TRIGGER_Shoe"), P["coll"], L.TRIGGER_POLY,
                    -L.TRIGGER_HALF_WIDTH, L.TRIGGER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    return [triangulate_ngons(ob)]


def trigger(P):
    ob = mesh.plate(nm(P, "TRIGGER_Shoe"), P["coll"], L.TRIGGER_POLY,
                    -L.TRIGGER_HALF_WIDTH, L.TRIGGER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    return [hard(ob, P, 0.0008)]


# -----------------------------------------------------------------------------
# Part 6: HAMMER
# -----------------------------------------------------------------------------
def hammer_prim(P):
    ob = mesh.plate(nm(P, "HAMMER_Main"), P["coll"], L.HAMMER_POLY,
                    -L.HAMMER_HALF_WIDTH, L.HAMMER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    return [triangulate_ngons(ob)]


def hammer(P):
    ob = mesh.plate(nm(P, "HAMMER_Main"), P["coll"], L.HAMMER_POLY,
                    -L.HAMMER_HALF_WIDTH, L.HAMMER_HALF_WIDTH, "MAT_CONTROLS_DARK")
    return [hard(ob, P, 0.0008)]


# -----------------------------------------------------------------------------
# Part 7: SIGHTS (Front Blade & Rear Notch)
# -----------------------------------------------------------------------------
def sights_prim(P):
    ob_f = mesh.plate(nm(P, "SIGHTS_Front"), P["coll"], L.SIGHT_FRONT_POLY,
                      -0.0010, 0.0010, "MAT_CONTROLS_DARK")
    ob_r = mesh.plate(nm(P, "SIGHTS_Rear"), P["coll"], L.SIGHT_REAR_POLY,
                      -0.0070, 0.0070, "MAT_CONTROLS_DARK")
    return [triangulate_ngons(ob_f), triangulate_ngons(ob_r)]


def sights(P):
    ob_f = mesh.plate(nm(P, "SIGHTS_Front"), P["coll"], L.SIGHT_FRONT_POLY,
                      -0.0010, 0.0010, "MAT_CONTROLS_DARK")
    ob_r = mesh.plate(nm(P, "SIGHTS_Rear"), P["coll"], L.SIGHT_REAR_POLY,
                      -0.0070, 0.0070, "MAT_CONTROLS_DARK")
    ny, nz = L.P(530.0, 260.0)
    ob_notch = mesh.box("TEMP_Notch", P["coll"], (0.0, ny, nz), (0.0026, 0.010, 0.004), "MAT_CONTROLS_DARK")
    mods.boolean(ob_r, ob_notch, apply=True)
    bpy.data.objects.remove(ob_notch, do_unlink=True)
    return [hard(ob_f, P, 0.0008), hard(ob_r, P, 0.0008)]


# -----------------------------------------------------------------------------
# PARTS Registry
# -----------------------------------------------------------------------------
PARTS = [
    Part("slide", slide, prim=slide_prim, collision="box"),
    Part("frame", frame, prim=frame_prim, collision="convcol"),
    Part("barrel", barrel, prim=barrel_prim, collision="capsule"),
    Part("grip_panels", grip_panels, prim=grip_panels_prim, collision="box"),
    Part("trigger", trigger, prim=trigger_prim, collision="box"),
    Part("hammer", hammer, prim=hammer_prim, collision="box"),
    Part("sights", sights, prim=sights_prim, collision="box"),
]

# Pivots for animation (muzzle is along -Y)
PIVOTS = {
    "SLIDE_Main": lambda: (0.0, *L.P(384.0, 482.0)),
    "TRIGGER_Shoe": lambda: (0.0, *L.P(822.0, 618.0)),
    "HAMMER_Main": lambda: (0.0, *L.P(420.0, 540.0)),
    "CTRL_Safety": lambda: (L.FRAME_HALF_WIDTH, *L.P(280.0, 560.0)),
    "CTRL_SlideStop": lambda: (L.FRAME_HALF_WIDTH, *L.P(820.0, 540.0)),
}

CHILDREN = {
    "BARREL_Bushing": "SLIDE_Main",
    "BARREL_Plug": "SLIDE_Main",
    "SIGHTS_Front": "SLIDE_Main",
    "SIGHTS_Rear": "SLIDE_Main",
}


def guide_points():
    return {"ANCHOR": L.ANCHORS[0][0]}
