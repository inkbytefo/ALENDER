"""Metric specification landmarks for PROP_TWR_Industrial_Watchtower.

No photo/reference was supplied, so all placement is authored directly in metres. The only
confirmed dimensions are the 8 x 6 m platform and +6 m walking surface; all other values are
explicit design assumptions in project.md and parts.py.
"""

ASSET = "PROP_TWR_Industrial_Watchtower"

# Confirmed platform envelope and walking height.
PLATFORM_X = 8.0
PLATFORM_Y = 6.0
DECK_Z = 6.0
RAIL_HEIGHT = 1.0

# Modular structural layout assumptions, in metres.
COLUMN_X = 3.65
COLUMN_Y = 2.65
GRID = 1.0

# Straight south stair assumption: 32 equal risers and 0.28 m treads.
STAIR_COUNT = 32
STAIR_WIDTH = 1.25
STAIR_RISE = DECK_Z / STAIR_COUNT
STAIR_TREAD = 0.28
STAIR_RUN = STAIR_COUNT * STAIR_TREAD
STAIR_Y_END = -PLATFORM_Y * 0.5
STAIR_Y_START = STAIR_Y_END - STAIR_RUN
STAIR_THICKNESS = 0.05
