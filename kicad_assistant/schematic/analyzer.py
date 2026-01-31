"""Schematic analysis - extract structure from KiCad schematic files."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SchematicStats:
    """Statistics from a schematic."""
    file: str
    symbols: int = 0
    wires: int = 0
    labels: int = 0
    power_symbols: int = 0
    hierarchical_sheets: int = 0
    component_types: dict = field(default_factory=dict)


def analyze_schematic(filepath: str) -> SchematicStats:
    """Analyze a KiCad schematic file.

    Args:
        filepath: Path to .kicad_sch file

    Returns:
        SchematicStats with analysis results
    """
    from kiutils.schematic import Schematic

    sch = Schematic.from_file(filepath)

    # Count symbols by type
    component_types = {}
    power_symbols = 0

    for symbol in sch.schematicSymbols:
        # Get reference
        ref = ""
        for prop in symbol.properties:
            if prop.key == "Reference":
                ref = prop.value
                break

        if ref:
            prefix = "".join(c for c in ref if c.isalpha())
            if prefix:
                # Power symbols often have #PWR prefix
                if prefix.startswith("#"):
                    power_symbols += 1
                else:
                    component_types[prefix] = component_types.get(prefix, 0) + 1

    # Count wires
    wire_count = len(sch.wires) if hasattr(sch, 'wires') and sch.wires else 0

    # Count labels
    label_count = 0
    if hasattr(sch, 'labels'):
        label_count = len(sch.labels)
    if hasattr(sch, 'globalLabels'):
        label_count += len(sch.globalLabels)

    # Count hierarchical sheets
    sheet_count = len(sch.sheets) if hasattr(sch, 'sheets') and sch.sheets else 0

    return SchematicStats(
        file=filepath,
        symbols=len(sch.schematicSymbols),
        wires=wire_count,
        labels=label_count,
        power_symbols=power_symbols,
        hierarchical_sheets=sheet_count,
        component_types=component_types,
    )


def get_nets(filepath: str) -> list[dict]:
    """Get all nets in the schematic.

    Args:
        filepath: Path to .kicad_sch file

    Returns:
        List of net info dicts
    """
    from kiutils.schematic import Schematic

    sch = Schematic.from_file(filepath)

    nets = []

    # Get from labels
    if hasattr(sch, 'labels'):
        for label in sch.labels:
            nets.append({
                "name": label.text if hasattr(label, 'text') else str(label),
                "type": "local",
            })

    if hasattr(sch, 'globalLabels'):
        for label in sch.globalLabels:
            nets.append({
                "name": label.text if hasattr(label, 'text') else str(label),
                "type": "global",
            })

    return nets
