"""Fab presets and DFM rules."""

from .jlcpcb import JLCPCB_STANDARD, JLCPCB_ADVANCED
from .pcbway import PCBWAY_STANDARD
from .oshpark import OSHPARK

ALL_PRESETS = {
    "jlcpcb_standard": JLCPCB_STANDARD,
    "jlcpcb_advanced": JLCPCB_ADVANCED,
    "pcbway_standard": PCBWAY_STANDARD,
    "oshpark": OSHPARK,
}

__all__ = [
    "JLCPCB_STANDARD",
    "JLCPCB_ADVANCED",
    "PCBWAY_STANDARD",
    "OSHPARK",
    "ALL_PRESETS",
]
