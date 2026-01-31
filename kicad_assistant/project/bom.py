"""BOM (Bill of Materials) export."""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class BOMEntry:
    """A single BOM entry."""
    references: list[str]
    value: str
    footprint: str
    quantity: int
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None


def natural_sort_key(ref: str):
    """Natural sort key for reference designators."""
    parts = re.split(r'(\d+)', ref)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def export_bom(
    filepath: str,
    include_all: bool = False,
    group_by: str = "value_footprint",
) -> list[BOMEntry]:
    """Export BOM from a KiCad PCB file.

    Args:
        filepath: Path to .kicad_pcb file
        include_all: Include fiducials, test points, etc.
        group_by: How to group components ("value_footprint", "value", "footprint")

    Returns:
        List of BOMEntry objects
    """
    from kiutils.board import Board

    board = Board.from_file(filepath)

    # Group components
    components = {}

    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')
        value = fp.properties.get('Value', '?')
        footprint_name = fp.entryName or fp.libId or '?'

        # Skip non-component footprints
        if not include_all:
            prefix = "".join(c for c in ref if c.isalpha())
            if prefix in ("FID", "TP", "MH", "H", "REF", "LOGO", "G"):
                continue

        # Determine grouping key
        if group_by == "value":
            key = value
        elif group_by == "footprint":
            key = footprint_name
        else:
            key = (value, footprint_name)

        if key not in components:
            components[key] = BOMEntry(
                references=[],
                value=value,
                footprint=footprint_name,
                quantity=0,
            )

        components[key].references.append(ref)
        components[key].quantity += 1

    # Sort references within each entry
    bom = []
    for entry in components.values():
        entry.references = sorted(entry.references, key=natural_sort_key)
        bom.append(entry)

    # Sort BOM by first reference
    bom.sort(key=lambda x: natural_sort_key(x.references[0]) if x.references else [])

    return bom


def format_bom_csv(bom: list[BOMEntry]) -> str:
    """Format BOM as CSV string."""
    lines = ["Reference,Value,Footprint,Quantity"]
    for entry in bom:
        refs = ", ".join(entry.references)
        lines.append(f'"{refs}","{entry.value}","{entry.footprint}",{entry.quantity}')
    return "\n".join(lines)


def format_bom_json(bom: list[BOMEntry]) -> list[dict]:
    """Format BOM as JSON-serializable list."""
    return [
        {
            "references": entry.references,
            "value": entry.value,
            "footprint": entry.footprint,
            "quantity": entry.quantity,
        }
        for entry in bom
    ]
