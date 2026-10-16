# PROP_Weapon_Spawner_Pad

Floor-mounted weapon spawner pad for a sci-fi training gym level. Low-profile hexagonal metallic platform (1.5m diameter x 0.16m height) with beveled perimeter edges, glowing cyan emissive border strip, and integrated upward-facing projector lenses.

## Category / targets
prop
budget key: large_prop (workbench.tables.BUDGETS)
targets: game (S4) | render (S3 + S5)
engine: godot (GLB LOD0-2 with -convcolonly collision)

## Objective
High-tech, reference-accurate game asset featuring a hexagonal floor spawner base, 45-degree beveled perimeter skirt with maintenance vents, segmented deck plates, recessed cyan emissive border strip, and central circular hologram projector well with 4 satellite emitter lenses and central core.

## References
- ref/REAL_REFERENCE.png: Hero perspective render with glowing cyan projection rays
- ref/REF_COMPOSITE.png: Full reference sheet including multi-angle wireframe views

## Scale & measurements
- Bounding Dimensions: 1.500m (X) x 1.299m (Y) x 0.160m (Z)
- Outer Hexagon: Radius 0.750m (diameter 1.500m)
- Deck Height: 0.150m, Total Height: 0.160m at lens bezels
- Emissive Strip: Hexagonal channel at radius 0.570m
- Central Projector Well: Radius 0.350m, stepped circular well
- Projector Lenses: 1 central lens (radius 0.115m) + 4 satellite lenses (radius 0.048m, offset 0.215m)

## Stage plan
| Stage | content | budget (tris) |
|-------|---------|---------------|
| S1 PRIMITIVE | hexagonal base block, deck slab, central cylinder, lenses | < 800 |
| S2 LOWPOLY (LOD0) | chamfered skirt, vents, segmented deck plates, emissive strip channel, circular projector well, 5 lenses | 1,500 - 8,000 |
| S3 DETAIL | beveled edges, panel seams, grip treads, bolt fasteners, lens bezels, weighted normals | < 25,000 |
| S4 GAME | baked PBR maps (base, orm, normal), LOD1 (50%), LOD2 (25%), convex collision | auto |

## Part breakdown (registry parts.PARTS)
| Part key | prim builder | real builder | collision | moving? |
|----------|--------------|--------------|-----------|---------|
| base | base_prim | base | box | no |
| deck | deck_prim | deck | box | no |
| emissive_strip | emissive_strip_prim | emissive_strip | none | no |
| projector_hub | projector_hub_prim | projector_hub | box | no |
| lenses | lenses_prim | lenses | none | no |

## Uncertain / hidden areas
- Underside mounting bolts (flush against gym floor).
