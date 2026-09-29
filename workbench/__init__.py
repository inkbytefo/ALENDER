"""
Blender Workbench - reusable library for reference-driven 3D modelling with headless Blender.

Layout
  workbench.paths     project / output folder conventions            (pure python)
  workbench.refmap    photo pixel <-> world metre mapping            (pure python)
  workbench.tables    polyline / table interpolation helpers         (pure python)
  workbench.bl.*      bpy-only modules (scene, mesh, mods, materials, cameras, render,
                      fasteners, rig, anim, validate, export)        (inside Blender)
  workbench.host.*    PIL tools run with normal python (crop, compare, sheet)

Importing `workbench` never imports bpy, so host tools and landmark files stay usable
outside Blender. See docs/04_MODELING_TOOLKIT.md for the API map.
"""
__version__ = "2.0.0"
