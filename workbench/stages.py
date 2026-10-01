"""
Stage model of the workbench pipeline (pure python, no bpy).

  S0 INTAKE     reference analysis -> landmarks.py, project.md          (no geometry)
  S1 PRIMITIVE  masses + proportions from primitives                    *_PRIM   10_S1_PRIMITIVE
  S2 LOWPOLY    real forms, clean topology, UVs = game LOD0 base         *_LP     20_S2_LOWPOLY
  S3 DETAIL     bevels, subsurf, fasteners = hero mesh + bake source     *_HP     30_S3_DETAIL
  S4 GAME       atlas, bake S3->S2, LOD1-2, collision, export            *_LODn   40_S4_GAME
  S5 PRESENT    studio renders (python wb.py present)

One builder per part reads landmarks.py at every stage, so proportions cannot drift between
stages; a stage profile (dict) tells the builder how much detail to make.

    P = stages.profile(2, ring=16, stations=18)       # S2 profile with builder knobs
    stages.nm(P, "RECV_Body")  -> "RECV_Body_LP"
    stages.base_name("RECV_Body_LP") -> "RECV_Body"
"""
import re

PRIMITIVE, LOWPOLY, DETAIL, GAME, PRESENT = 1, 2, 3, 4, 5

STAGES = {
    1: dict(key="PRIMITIVE", suffix="_PRIM", coll="10_S1_PRIMITIVE", milestone="S1_PRIMITIVE"),
    2: dict(key="LOWPOLY", suffix="_LP", coll="20_S2_LOWPOLY", milestone="S2_LOWPOLY"),
    3: dict(key="DETAIL", suffix="_HP", coll="30_S3_DETAIL", milestone="S3_DETAIL"),
    4: dict(key="GAME", suffix="_LOD0", coll="40_S4_GAME", milestone="S4_GAME"),
}
COLL_COLLISION = "41_S4_COLLISION"
COLLECTIONS = ["00_REFERENCE", "01_GUIDES", "10_S1_PRIMITIVE", "20_S2_LOWPOLY", "30_S3_DETAIL",
               "40_S4_GAME", COLL_COLLISION, "08_TEMP", "09_PRESENTATION"]

# every suffix a stage or the game export may put on a part name (longest first for stripping)
_SUFFIX_RE = re.compile(r"(_PRIM|_LP|_HP|_LOW|_LOD\d)$")
# GROUP_Part[_Detail...][stage suffix]; optional UNCERTAIN_ prefix; no spaces, no .001
NAME_RE = re.compile(r"^(UNCERTAIN_)?[A-Z][A-Z0-9]*_[A-Za-z0-9]+(_[A-Za-z0-9]+)*$")


class Part:
    """One entry of the part registry (parts.PARTS). A part is a group of objects built by ONE
    function per stage; every builder takes a stage profile and reads landmarks.py.

      key        registry id, also the collision group ("receiver", "magazine")
      low        builder for S2 LOWPOLY (required); also used for S3 unless `high` is given
      high       builder for S3 DETAIL (default: low with the S3 profile)
      prim       builder for S1 PRIMITIVE (default: low with the S1 profile)
      collision  "hull" | "box" | "none"  (game collision of the whole group, S4)
    """

    def __init__(self, key, low, prim=None, high=None, collision="hull"):
        self.key, self.low, self.prim, self.high, self.collision = key, low, prim, high, collision

    def builder(self, stage):
        if stage == PRIMITIVE:
            return self.prim or self.low
        if stage == DETAIL:
            return self.high or self.low
        return self.low

    def __repr__(self):
        return f"Part({self.key!r})"


def profile(stage, **knobs):
    """Stage profile for builders. The legacy collection keys (C_PRIMARY ...) all point at the stage
    collection so older builder code keeps working; `detail`/`bevel` default per stage."""
    s = STAGES[stage]
    p = dict(name=s["key"], stage=stage, suffix=s["suffix"], coll=s["coll"],
             C_PRIMARY=s["coll"], C_SECONDARY=s["coll"], C_MECH=s["coll"], C_DETAIL=s["coll"],
             bevel=stage >= DETAIL, detail=stage >= DETAIL, subsurf=stage >= DETAIL)
    p.update(knobs)
    return p


def nm(p, name):
    """Part name for a stage profile (idempotent: never doubles a suffix)."""
    return base_name(name) + p["suffix"]


def base_name(name):
    """Name without any stage / LOD suffix (and without Blender's .001 counters)."""
    name = name.split(".")[0]
    return _SUFFIX_RE.sub("", name)


def stage_of(name):
    m = _SUFFIX_RE.search(name.split(".")[0])
    if not m:
        return None
    suf = m.group(1)
    for k, s in STAGES.items():
        if s["suffix"] == suf:
            return k
    return GAME if suf.startswith("_LOD") else None


def milestone_tag(stage):
    return STAGES[stage]["milestone"]


def parse_stage_args(argv, default_stages=(1, 2, 3, 4)):
    """--stage N (only N) | --from N | --until N  ->  sorted list of stages to run."""
    stages = list(default_stages)
    if "--stage" in argv:
        return [int(argv[argv.index("--stage") + 1])]
    if "--from" in argv:
        f = int(argv[argv.index("--from") + 1])
        stages = [s for s in stages if s >= f]
    if "--until" in argv:
        u = int(argv[argv.index("--until") + 1])
        stages = [s for s in stages if s <= u]
    return stages
