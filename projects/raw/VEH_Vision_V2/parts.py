"""Procedural builders for the original Vision V2 stainless grand-tourer concept."""
import math

import bpy
import bmesh

import landmarks as L
from workbench import stages
from workbench.stages import Part
from workbench.bl import materials, mesh, mods

CATEGORY = "hero_vehicle"
TARGET_DIMS = (L.TARGET_WIDTH, L.TARGET_LENGTH, L.TARGET_HEIGHT)
GROUND = True

PROFILES = {
    1: stages.profile(1, stations=18, wheel_segments=12, spokes=5),
    2: stages.profile(2, stations=72, wheel_segments=64, spokes=7),
    3: stages.profile(3, stations=100, wheel_segments=96, spokes=10),
}
GAME = dict(engine="godot", bake=True, tex=2048, lod=(0.5, 0.25))
PALETTE = {
    "MAT_STAINLESS": ((0.48, 0.53, 0.57), 0.96, 0.27),
    "MAT_TRIM": ((0.025, 0.038, 0.045), 0.0, 0.38),
    "MAT_GLASS": ((0.018, 0.055, 0.068), 0.0, 0.17),
    "MAT_RUBBER": ((0.022, 0.024, 0.026), 0.0, 0.84),
    "MAT_ALLOY": ((0.47, 0.51, 0.54), 0.93, 0.24),
    "MAT_HEADLAMP": dict(
        rgb=(0.72, 0.82, 0.91), metallic=0.0, roughness=0.2,
        emission=(0.48, 0.67, 0.88), emission_strength=0.45,
    ),
    "MAT_TAILLAMP": dict(
        rgb=(0.48, 0.018, 0.024), metallic=0.0, roughness=0.24,
        emission=(0.42, 0.006, 0.012), emission_strength=0.32,
    ),
    "MAT_AMBER": ((0.72, 0.22, 0.025), 0.12, 0.3),
}
CRITICAL_PAIRS = []
UNCERTAIN = ["UNCERTAIN_Undertray", "UNCERTAIN_HiddenMechanicalLayout"]
ASSUMPTIONS = [
    "All proportions are original concept dimensions, not measured production-car data",
    "Closed conventional side doors; static presentation and game-ready rigid asset",
    "Opaque tinted glazing is used for reliable baked glTF materials",
]
KNOWN_LIMITATIONS = [
    "Independent retro-futuristic concept; no production vehicle silhouette or badges",
    "No engine, suspension, or functional steering assembly",
]
PIVOTS = {}
CHILDREN = {}


def nm(profile, name):
    return stages.nm(profile, name)


def hard(ob, profile, width=0.003):
    return mods.finish_hard(ob, width, enabled=profile["bevel"])


def box(profile, name, center, size, material="MAT_TRIM", bevel=0.003):
    obj = mesh.box(nm(profile, name), profile["coll"], center, size, material)
    safe_bevel = min(bevel, min(size) * 0.22)
    return hard(obj, profile, safe_bevel)


def recalculate_normals(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if bm.faces and bm.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        obj.data.update()
    finally:
        bm.free()


def tube(profile, name, points, radius, material="MAT_TRIM", segments=8):
    obj = mesh.tube(
        nm(profile, name), profile["coll"], points, radius,
        segments, material, smooth_path=False,
    )
    if profile["bevel"]:
        mods.weighted_normal(obj)
    return obj


def lerp_rows(rows, y, column):
    if y <= rows[0][0]:
        return rows[0][column]
    if y >= rows[-1][0]:
        return rows[-1][column]
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        if a[0] <= y <= b[0]:
            span = b[0] - a[0]
            t = (y - a[0]) / span
            prev = rows[max(0, i - 1)]
            nxt = rows[min(len(rows) - 1, i + 2)]
            m0 = (b[column] - prev[column]) / max(b[0] - prev[0], 1e-6)
            m1 = (nxt[column] - a[column]) / max(nxt[0] - a[0], 1e-6)
            return (
                (2 * t**3 - 3 * t**2 + 1) * a[column]
                + (t**3 - 2 * t**2 + t) * span * m0
                + (-2 * t**3 + 3 * t**2) * b[column]
                + (t**3 - t**2) * span * m1
            )
    raise RuntimeError(f"Could not interpolate station at y={y}")


def body_section(y):
    return tuple(lerp_rows(L.BODY, y, i) for i in range(1, 4))


def wheel_arch_bottom(y):
    lowest = 0.235
    for center_y, radius, _width, _track in L.WHEELS:
        arch_radius = radius + 0.060
        distance = abs(y - center_y)
        if distance <= arch_radius:
            lowest = max(
                lowest,
                radius + math.sqrt(max(0.0, arch_radius**2 - distance**2)),
            )
    return lowest


def body_ring(y):
    half_width, hood_z, shoulder_z = body_section(y)
    edge_z = wheel_arch_bottom(y)
    half = [
        (0.0, hood_z),
        (half_width * 0.27, hood_z + 0.014),
        (half_width * 0.64, hood_z + 0.021),
        (half_width * 0.90, shoulder_z),
        (half_width, shoulder_z - 0.032),
        (half_width * 1.006, max(edge_z, 0.39)),
        (half_width * 0.97, edge_z),
        (half_width * 0.70, 0.247),
        (0.0, 0.215),
    ]
    section = half + [(-x, z) for x, z in reversed(half[1:-1])]
    return [(x, y, z) for x, z in section]


def body(profile):
    count = profile["stations"]
    ys = {
        L.BODY[0][0] + (L.BODY[-1][0] - L.BODY[0][0]) * i / (count - 1)
        for i in range(count)
    }
    ys.update(row[0] for row in L.BODY)
    for center_y, radius, _width, _track in L.WHEELS:
        arch = radius + 0.060
        for i in range(17):
            ys.add(center_y - arch + 2 * arch * i / 16)
    rings = [body_ring(y) for y in sorted(ys)]
    obj = mesh.loft_rings(
        nm(profile, "BODY_OuterShell"), profile["coll"], rings, "MAT_STAINLESS",
        sharp_angle=65,
    )
    hard(obj, profile, 0.0025)
    return [obj]


def cabin_section(y):
    return tuple(lerp_rows(L.CABIN, y, i) for i in range(1, 5))


def cabin_ring(y):
    roof_z, roof_width, lower_width, base_z = cabin_section(y)
    pts = [
        (-lower_width, base_z),
        (-lower_width * 0.98, base_z + (roof_z - base_z) * 0.42),
        (-roof_width, roof_z - 0.082),
        (-roof_width * 0.78, roof_z - 0.012),
        (0.0, roof_z + 0.012),
        (roof_width * 0.78, roof_z - 0.012),
        (roof_width, roof_z - 0.082),
        (lower_width * 0.98, base_z + (roof_z - base_z) * 0.42),
        (lower_width, base_z),
    ]
    return [(x, y, z) for x, z in pts]


def cabin(profile):
    count = 8 if profile["stage"] == 1 else 34 if profile["stage"] == 2 else 48
    ys = {
        L.CABIN[0][0] + (L.CABIN[-1][0] - L.CABIN[0][0]) * i / (count - 1)
        for i in range(count)
    }
    ys.update(row[0] for row in L.CABIN)
    obj = mesh.loft_rings(
        nm(profile, "CABIN_RoofAndPillars"), profile["coll"],
        [cabin_ring(y) for y in sorted(ys)], "MAT_STAINLESS",
        sharp_angle=55,
    )
    hard(obj, profile, 0.002)
    if profile["stage"] == 1:
        return [obj]

    glass = bpy.data.materials["MAT_GLASS"]
    tint = bpy.data.materials["MAT_TRIM"]
    obj.data.materials.append(glass)
    obj.data.materials.append(tint)
    for face in obj.data.polygons:
        center = face.center
        normal = face.normal
        if abs(normal.x) > 0.68 and -0.60 < center.y < 0.88 and center.z > 0.87:
            face.material_index = 1
        elif center.z > 0.80 and (
            (-0.82 < center.y < -0.42 and normal.y < -0.14)
            or (0.82 < center.y < 1.21 and normal.y > 0.14)
        ):
            face.material_index = 1

    out = [obj]
    if profile["stage"] == 2:
        return out

    # A subtle bright roof perimeter and restrained dark structural divisions.
    for sign, side in ((1, "L"), (-1, "R")):
        roof = []
        for y in [row[0] for row in L.CABIN]:
            roof_z, roof_width, _lower_width, _base_z = cabin_section(y)
            roof.append((sign * roof_width * 0.78, y, roof_z - 0.006))
        out.append(tube(profile, f"CABIN_RoofRail_{side}", roof, 0.006, "MAT_ALLOY"))

        for label, y in (("A", -0.43), ("B", 0.43), ("C", 0.88)):
            roof_z, roof_width, lower_width, base_z = cabin_section(y)
            out.append(tube(
                profile, f"CABIN_{label}Pillar_{side}",
                [
                    (sign * (lower_width + 0.004), y, base_z + 0.06),
                    (sign * (roof_width + 0.004), y, roof_z - 0.075),
                ],
                0.010 if label != "B" else 0.012,
                "MAT_STAINLESS",
            ))
    return out


def windows(profile):
    if profile["stage"] == 1:
        return []

    def prism(name, front, offset):
        back = [(x + offset[0], y + offset[1], z + offset[2]) for x, y, z in front]
        return mesh.extrude_polys(
            nm(profile, name), profile["coll"], [(front, back)], "MAT_GLASS",
        )

    out = []
    windshield = [
        (-0.655, -0.835, 0.790), (0.655, -0.835, 0.790),
        (0.582, -0.305, 1.175), (-0.582, -0.305, 1.175),
    ]
    out.append(prism("GLASS_Windshield", windshield, (0.0, -0.003, 0.002)))
    rear_screen = [
        (-0.605, 0.610, 1.238), (0.605, 0.610, 1.238),
        (0.715, 1.175, 0.828), (-0.715, 1.175, 0.828),
    ]
    out.append(prism("GLASS_FastbackScreen", rear_screen, (0.0, 0.003, 0.002)))

    for sign, side in ((1, "L"), (-1, "R")):
        window_ys = [-0.48 + 1.20 * i / 24 for i in range(25)]

        def side_x(y, z):
            roof_z, roof_width, lower_width, base_z = cabin_section(y)
            z0 = base_z + (roof_z - base_z) * 0.42
            z1 = roof_z - 0.082
            t = min(1.0, max(0.0, (z - z0) / max(z1 - z0, 1e-5)))
            return lower_width * 0.98 + (roof_width - lower_width * 0.98) * t

        upper = []
        lower = []
        for y in window_ys:
            roof_z, _roof_width, _lower_width, base_z = cabin_section(y)
            for edge, z in ((upper, roof_z - 0.12), (lower, base_z + 0.145)):
                edge.append((sign * (side_x(y, z) + 0.003), y, z))
        front = upper + list(reversed(lower))
        back = [(x - sign * 0.006, y, z) for x, y, z in front]
        out.append(mesh.extrude_polys(
            nm(profile, f"GLASS_SideWindow_{side}"), profile["coll"],
            [(front, back)], "MAT_GLASS",
        ))
    return out


def arch_trim(profile):
    if profile["stage"] == 1:
        return []
    out = []
    for axle_index, (center_y, radius, _width, track) in enumerate(L.WHEELS):
        arch_radius = radius + 0.060
        for sign, side in ((1, "L"), (-1, "R")):
            points = []
            for i in range(25):
                angle = math.pi * i / 24
                y = center_y - arch_radius * math.cos(angle)
                z = radius + arch_radius * math.sin(angle)
                half_width, _hood, _shoulder = body_section(y)
                points.append((sign * (half_width + 0.004), y, z))
            label = "Front" if axle_index == 0 else "Rear"
            out.append(tube(
                profile, f"TRIM_ArchLip_{label}_{side}", points,
                0.007, "MAT_TRIM", profile["wheel_segments"],
            ))
    return out


def wheels(profile):
    out = []
    for axle_index, (y, radius, width, track) in enumerate(L.WHEELS):
        axle = "Front" if axle_index == 0 else "Rear"
        for sign, side in ((1, "L"), (-1, "R")):
            label = f"{axle}_{side}"
            center = (sign * track, y, radius)
            segs = profile["wheel_segments"]
            if profile["stage"] == 1:
                tread_profile = [
                    (radius, -width * 0.46), (radius, width * 0.46),
                    (radius * 0.69, width * 0.46), (radius * 0.69, -width * 0.46),
                ]
                out.append(mesh.lathe(
                    nm(profile, f"WHEEL_Tire_{label}"), profile["coll"],
                    center, tread_profile, segs, "MAT_RUBBER",
                ))
                out.append(mesh.cyl(
                    nm(profile, f"WHEEL_Rim_{label}"), profile["coll"],
                    (sign * (track - width * 0.28), y, radius),
                    (sign * (track + width * 0.32), y, radius),
                    radius * 0.70, segs, "MAT_ALLOY",
                ))
                continue

            tread = [
                (radius * 0.965, -width * 0.49),
                (radius, -width * 0.42),
                (radius, -width * 0.30),
                (radius, width * 0.30),
                (radius, width * 0.42),
                (radius * 0.965, width * 0.49),
                (radius * 0.88, width * 0.49),
                (radius * 0.88, -width * 0.49),
            ]
            out.append(mesh.lathe(
                nm(profile, f"WHEEL_Tire_{label}"), profile["coll"],
                center, tread, segs, "MAT_RUBBER",
            ))

            rim_profile = [
                (radius * 0.70, -width * 0.38),
                (radius * 0.80, -width * 0.43),
                (radius * 0.84, -width * 0.37),
                (radius * 0.84, width * 0.36),
                (radius * 0.78, width * 0.42),
                (radius * 0.69, width * 0.35),
            ]
            out.append(hard(mesh.lathe(
                nm(profile, f"WHEEL_Rim_{label}"), profile["coll"],
                center, rim_profile, segs, "MAT_ALLOY",
            ), profile, 0.0015))

            blade_pairs = []
            blade_count = profile["spokes"]
            for face_sign in (1, -1):
                x0 = sign * (track + face_sign * width * 0.25)
                x1 = sign * (track + face_sign * width * 0.43)
                for i in range(blade_count):
                    angle = math.tau * i / blade_count
                    # Seven broad swept blades distinguish the alloy from a turbine mesh.
                    shape = [
                        (radius * 0.15, angle - 0.12),
                        (radius * 0.27, angle + 0.05),
                        (radius * 0.77, angle + 0.39),
                        (radius * 0.78, angle + 0.24),
                    ]
                    face_a = [
                        (x0, y + r * math.cos(a), radius + r * math.sin(a))
                        for r, a in shape
                    ]
                    face_b = [
                        (x1, yy, z)
                        for _x, yy, z in face_a
                    ]
                    if x1 > x0:
                        face_a.reverse()
                        face_b.reverse()
                    blade_pairs.append((face_a, face_b))
            spoke_obj = mesh.extrude_polys(
                nm(profile, f"WHEEL_Spokes_{label}"), profile["coll"],
                blade_pairs, "MAT_ALLOY",
            )
            recalculate_normals(spoke_obj)
            out.append(spoke_obj)

            rotor_radius = radius * 0.61
            out.append(mesh.cyl(
                nm(profile, f"WHEEL_Rotor_{label}"), profile["coll"],
                (sign * (track - width * 0.12), y, radius),
                (sign * (track + width * 0.12), y, radius),
                rotor_radius, segs, "MAT_TRIM",
            ))
            out.append(mesh.cyl(
                nm(profile, f"WHEEL_Hub_{label}"), profile["coll"],
                (sign * (track + width * 0.31), y, radius),
                (sign * (track + width * 0.47), y, radius),
                radius * 0.16, max(16, segs // 3), "MAT_ALLOY",
            ))
            if profile["stage"] == 3:
                out.append(box(
                    profile, f"WHEEL_Caliper_{label}",
                    (sign * (track + width * 0.17), y - radius * 0.28, radius),
                    (width * 0.17, radius * 0.25, radius * 0.45),
                    "MAT_AMBER", 0.008,
                ))
    return out


def fascia(profile):
    if profile["stage"] == 1:
        return [
            box(profile, "FASCIA_FrontMass", (0, -2.172, 0.485), (1.48, 0.075, 0.25)),
            box(profile, "FASCIA_RearMass", (0, 2.172, 0.475), (1.48, 0.075, 0.24)),
        ]

    out = [
        box(profile, "FASCIA_FrontIntake", (0, -2.182, 0.430), (1.28, 0.026, 0.105), "MAT_TRIM", 0.018),
        box(profile, "FASCIA_FrontLip", (0, -2.192, 0.340), (1.54, 0.055, 0.058), "MAT_TRIM", 0.018),
        box(profile, "FASCIA_RearInsert", (0, 2.179, 0.455), (1.42, 0.025, 0.105), "MAT_TRIM", 0.014),
        box(profile, "FASCIA_RearBumper", (0, 2.190, 0.344), (1.54, 0.060, 0.065), "MAT_STAINLESS", 0.018),
        box(profile, "LIGHT_RearBar", (0, 2.196, 0.585), (1.44, 0.014, 0.042), "MAT_TAILLAMP", 0.018),
    ]
    for sign, side in ((1, "L"), (-1, "R")):
        # Round projector lamps and low amber markers form a new, non-branded front signature.
        x = sign * 0.665
        out.append(mesh.cyl(
            nm(profile, f"LIGHT_Projector_{side}"), profile["coll"],
            (x, -2.216, 0.635), (x, -2.197, 0.635),
            0.070, profile["wheel_segments"], "MAT_HEADLAMP",
        ))
        out.append(box(
            profile, f"LIGHT_FrontMarker_{side}",
            (sign * 0.805, -2.183, 0.515), (0.095, 0.018, 0.020),
            "MAT_AMBER", 0.007,
        ))
        out.append(box(
            profile, f"LIGHT_RearMarker_{side}",
            (sign * 0.762, 2.198, 0.585), (0.035, 0.017, 0.052),
            "MAT_AMBER", 0.009,
        ))
    if profile["stage"] == 3:
        for i in range(9):
            x = -0.52 + i * 0.13
            out.append(box(
                profile, f"FASCIA_IntakeSlat_{i:02d}",
                (x, -2.170, 0.430), (0.006, 0.018, 0.065),
                "MAT_ALLOY", 0.001,
            ))
    return out


def side_details(profile):
    if profile["stage"] == 1:
        return [
            box(
                profile, f"MIRROR_Block_{side}",
                (sign * 0.991, -0.735, 0.858), (0.058, 0.132, 0.050),
                "MAT_STAINLESS", 0.014,
            )
            for sign, side in ((1, "L"), (-1, "R"))
        ]
    out = []
    for sign, side in ((1, "L"), (-1, "R")):
        # Soft shoulder line, a narrow rocker, and a simple closed-door reveal.
        points = []
        for i in range(23):
            y = -1.78 + 3.55 * i / 22
            half_width, _hood, shoulder = body_section(y)
            points.append((sign * (half_width + 0.003), y, shoulder - 0.105))
        out.append(tube(profile, f"TRIM_ShoulderLine_{side}", points, 0.0045, "MAT_ALLOY"))
        out.append(box(
            profile, f"TRIM_Rocker_{side}", (sign * 0.881, 0.015, 0.274),
            (0.048, 2.18, 0.060), "MAT_TRIM", 0.018,
        ))

        seam = [
            (sign * 0.918, -1.08, 0.735),
            (sign * 0.924, -0.82, 0.650),
            (sign * 0.917, -0.68, 0.490),
            (sign * 0.914, 0.78, 0.490),
            (sign * 0.915, 0.98, 0.642),
            (sign * 0.900, 1.10, 0.755),
        ]
        out.append(tube(profile, f"DOOR_ClosedSeam_{side}", seam, 0.0025, "MAT_TRIM"))
        out.append(box(
            profile, f"DOOR_FlushHandle_{side}",
            (sign * 0.923, 0.22, 0.690), (0.012, 0.105, 0.020),
            "MAT_TRIM", 0.006,
        ))

        # Compact mirrored housing is kept inside the authored total-width target.
        out.append(tube(
            profile, f"MIRROR_Stem_{side}",
            [(sign * 0.77, -0.70, 0.790), (sign * 0.92, -0.72, 0.835),
             (sign * 0.98, -0.73, 0.845)],
            0.012, "MAT_TRIM",
        ))
        out.append(box(
            profile, f"MIRROR_Housing_{side}",
            (sign * 0.991, -0.735, 0.858), (0.058, 0.132, 0.050),
            "MAT_STAINLESS", 0.014,
        ))
        out.append(box(
            profile, f"MIRROR_Inset_{side}",
            (sign * 1.021, -0.735, 0.858), (0.004, 0.098, 0.030),
            "MAT_GLASS", 0.008,
        ))
    return out


def hood_details(profile):
    if profile["stage"] == 1:
        return []
    out = []
    for sign, side in ((1, "L"), (-1, "R")):
        points = []
        for i in range(27):
            y = -2.02 + 1.08 * i / 26
            half_width, top_z, _shoulder = body_section(y)
            x = sign * half_width * 0.61
            z = top_z + 0.023 - 0.004 * abs(x / half_width)
            points.append((x, y, z))
        out.append(tube(profile, f"HOOD_Crease_{side}", points, 0.0018, "MAT_ALLOY"))
    return out


def undertray(profile):
    return [box(
        profile, "UNCERTAIN_Undertray", (0, 0.02, 0.205),
        (1.45, 3.72, 0.045), "MAT_TRIM", 0.008,
    )]


PARTS = [
    Part("body", body, collision="hull"),
    Part("cabin", cabin, collision="hull"),
    Part("windows", windows, collision="none"),
    Part("arch-trim", arch_trim, collision="none"),
    Part("wheels", wheels, collision="hull"),
    Part("fascia", fascia, collision="none"),
    Part("side-details", side_details, collision="none"),
    Part("hood-details", hood_details, collision="none"),
    Part("undertray", undertray, collision="box"),
]

for axle_index, (y, radius, _width, track) in enumerate(L.WHEELS):
    axle = "Front" if axle_index == 0 else "Rear"
    for sign, side in ((1, "L"), (-1, "R")):
        tire = f"WHEEL_Tire_{axle}_{side}"
        PIVOTS[tire] = lambda y=y, radius=radius, track=track, sign=sign: (
            sign * track, y, radius,
        )
        for part_name in ("Rim", "Spokes", "Rotor", "Hub", "Caliper"):
            CHILDREN[f"WHEEL_{part_name}_{axle}_{side}"] = tire


def guide_points():
    return {
        "FRONT_AXLE": (0.0, L.FRONT_AXLE_Y, L.WHEELS[0][1]),
        "REAR_AXLE": (0.0, L.REAR_AXLE_Y, L.WHEELS[1][1]),
        "GROUND_ORIGIN": (0.0, 0.0, L.GROUND_Z),
    }


def after_build(stage, _objects):
    if stage != 3:
        return

    body_material = bpy.data.materials["MAT_STAINLESS"]
    body_nodes = body_material.node_tree
    shader = body_nodes.nodes.get("Principled BSDF")
    position = body_nodes.nodes.get("V2_BrushPosition") or body_nodes.nodes.new("ShaderNodeNewGeometry")
    position.name = "V2_BrushPosition"
    scale = body_nodes.nodes.get("V2_BrushScale") or body_nodes.nodes.new("ShaderNodeVectorMath")
    scale.name = "V2_BrushScale"
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = (1900.0, 8.0, 1900.0)
    noise = body_nodes.nodes.get("V2_BrushNoise") or body_nodes.nodes.new("ShaderNodeTexNoise")
    noise.name = "V2_BrushNoise"
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 2.0
    bump = body_nodes.nodes.get("V2_BrushBump") or body_nodes.nodes.new("ShaderNodeBump")
    bump.name = "V2_BrushBump"
    bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.000025
    body_nodes.links.new(position.outputs["Position"], scale.inputs[0])
    body_nodes.links.new(scale.outputs["Vector"], noise.inputs["Vector"])
    body_nodes.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    body_nodes.links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    tire_material = bpy.data.materials["MAT_RUBBER"]
    tire_nodes = tire_material.node_tree
    tire_shader = tire_nodes.nodes.get("Principled BSDF")
    tire_noise = tire_nodes.nodes.get("V2_RubberNoise") or tire_nodes.nodes.new("ShaderNodeTexNoise")
    tire_noise.name = "V2_RubberNoise"
    tire_noise.inputs["Scale"].default_value = 230.0
    tire_noise.inputs["Detail"].default_value = 2.0
    tire_bump = tire_nodes.nodes.get("V2_RubberBump") or tire_nodes.nodes.new("ShaderNodeBump")
    tire_bump.name = "V2_RubberBump"
    tire_bump.inputs["Strength"].default_value = 0.12
    tire_bump.inputs["Distance"].default_value = 0.00012
    tire_nodes.links.new(tire_noise.outputs["Fac"], tire_bump.inputs["Height"])
    tire_nodes.links.new(tire_bump.outputs["Normal"], tire_shader.inputs["Normal"])
