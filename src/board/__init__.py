"""Board (PCB) analysis and modification modules."""

from .analyzer import analyze_board
from .dfm import check_dfm, DFM_PRESETS
from .fixer import fix_board_issues
from .layers import add_power_plane, configure_layer
from .zones import add_zone, add_stitching_vias

__all__ = [
    "analyze_board",
    "check_dfm",
    "DFM_PRESETS",
    "fix_board_issues",
    "add_power_plane",
    "configure_layer",
    "add_zone",
    "add_stitching_vias",
]
