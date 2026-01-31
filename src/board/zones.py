"""Zone (copper pour) management - create zones, power planes, stitching vias."""

from typing import Optional
from dataclasses import dataclass

from ..utils.backup import create_backup
from ..utils.geometry import get_board_outline, generate_grid, distance


def get_board_outline_polygon(filepath: str) -> list[tuple[float, float]]:
    """Get the board outline as a polygon.

    Args:
        filepath: Path to .kicad_pcb file

    Returns:
        List of (x, y) points forming the outline
    """
    from kiutils.board import Board

    board = Board.from_file(filepath)
    return get_board_outline(board)


def add_zone(
    filepath: str,
    layer: str,
    net_name: str,
    outline: list[tuple[float, float]],
    clearance_mm: float = 0.3,
    min_width_mm: float = 0.25,
    priority: int = 0,
    thermal_relief: bool = True,
    thermal_gap_mm: float = 0.5,
    thermal_bridge_mm: float = 0.5,
) -> dict:
    """Add a zone (copper pour) to the board.

    Args:
        filepath: Path to .kicad_pcb file
        layer: Layer name (e.g., "F.Cu", "In1.Cu")
        net_name: Net to connect zone to
        outline: List of (x, y) polygon points
        clearance_mm: Clearance around other copper
        min_width_mm: Minimum fill width
        priority: Zone priority (0 = lowest)
        thermal_relief: Use thermal relief for pads
        thermal_gap_mm: Gap in thermal relief
        thermal_bridge_mm: Width of thermal spokes

    Returns:
        Dict with zone details
    """
    from kiutils.board import Board
    from kiutils.items.zones import Zone, ZoneFillSettings, ZoneConnectPadsSettings
    from kiutils.items.common import Position

    create_backup(filepath)

    board = Board.from_file(filepath)

    # Find net number
    net_code = 0
    for net in board.nets:
        if hasattr(net, 'name') and net.name == net_name:
            net_code = net.number if hasattr(net, 'number') else 0
            break

    if net_code == 0:
        # Net not found, might need to add it
        raise ValueError(f"Net '{net_name}' not found in board")

    # Create zone
    zone = Zone()
    zone.net = net_code
    zone.netName = net_name
    zone.layer = layer
    zone.uuid = None  # Will be auto-generated
    zone.name = f"{net_name}_plane"
    zone.priority = priority

    # Set outline polygon
    zone.polygon = [Position(X=x, Y=y) for x, y in outline]

    # Fill settings
    zone.filledPolygons = []  # Will be filled when opened in KiCad

    # Settings
    zone.minThickness = min_width_mm
    zone.clearance = clearance_mm

    if thermal_relief:
        zone.thermalGap = thermal_gap_mm
        zone.thermalBridgeWidth = thermal_bridge_mm
        zone.padConnection = "thermal_relief"
    else:
        zone.padConnection = "solid"

    board.zones.append(zone)
    board.to_file(filepath)

    return {
        "layer": layer,
        "net": net_name,
        "priority": priority,
        "clearance_mm": clearance_mm,
        "points": len(outline),
    }


def add_stitching_vias(
    filepath: str,
    net_name: str = "GND",
    spacing_mm: float = 5.0,
    drill_mm: float = 0.3,
    size_mm: float = 0.6,
    layers: Optional[list[str]] = None,
) -> dict:
    """Add ground stitching vias across the board.

    Args:
        filepath: Path to .kicad_pcb file
        net_name: Net for vias (usually "GND")
        spacing_mm: Grid spacing
        drill_mm: Via drill diameter
        size_mm: Via pad diameter
        layers: Layers to connect (default: F.Cu to B.Cu)

    Returns:
        Dict with count and locations of added vias
    """
    from kiutils.board import Board
    from kiutils.items.brditems import Via
    from kiutils.items.common import Position

    create_backup(filepath)

    board = Board.from_file(filepath)

    # Get outline
    outline = get_board_outline(board)
    if not outline:
        raise ValueError("Board has no outline")

    # Find net
    net_code = 0
    for net in board.nets:
        if hasattr(net, 'name') and net.name == net_name:
            net_code = net.number if hasattr(net, 'number') else 0
            break

    if layers is None:
        layers = ["F.Cu", "B.Cu"]

    # Generate grid points
    grid_points = generate_grid(outline, spacing_mm)

    # Get existing via/hole locations for conflict check
    existing_positions = set()
    for item in board.traceItems:
        if isinstance(item, Via) and item.position:
            existing_positions.add((round(item.position.X, 2), round(item.position.Y, 2)))

    # Also check footprint pads
    for fp in board.footprints:
        if hasattr(fp, 'position') and fp.position:
            for pad in fp.pads:
                if hasattr(pad, 'position') and pad.position:
                    # Pad position is relative to footprint
                    abs_x = fp.position.X + pad.position.X
                    abs_y = fp.position.Y + pad.position.Y
                    existing_positions.add((round(abs_x, 2), round(abs_y, 2)))

    # Add vias at grid points that don't conflict
    vias_added = []
    min_distance = max(size_mm, drill_mm) + 0.3  # Clearance

    for x, y in grid_points:
        # Check for conflicts
        conflict = False
        for ex, ey in existing_positions:
            if distance((x, y), (ex, ey)) < min_distance:
                conflict = True
                break

        if not conflict:
            via = Via()
            via.position = Position(X=x, Y=y)
            via.drill = drill_mm
            via.size = size_mm
            via.net = net_code
            via.layers = layers

            board.traceItems.append(via)
            vias_added.append((x, y))
            existing_positions.add((round(x, 2), round(y, 2)))

    board.to_file(filepath)

    return {
        "net": net_name,
        "vias_added": len(vias_added),
        "spacing_mm": spacing_mm,
        "drill_mm": drill_mm,
        "locations": vias_added[:10],  # First 10 for preview
    }


def add_thermal_vias(
    filepath: str,
    component_ref: str,
    pad_number: Optional[str] = None,
    net_name: str = "GND",
    count: int = 4,
    drill_mm: float = 0.3,
    size_mm: float = 0.6,
) -> dict:
    """Add thermal vias under a component's thermal pad.

    Args:
        filepath: Path to .kicad_pcb file
        component_ref: Component reference (e.g., "U1")
        pad_number: Pad number for thermal pad (often the largest/center)
        net_name: Net for vias
        count: Number of vias to add
        drill_mm: Via drill diameter
        size_mm: Via pad diameter

    Returns:
        Dict with via locations
    """
    from kiutils.board import Board
    from kiutils.items.brditems import Via
    from kiutils.items.common import Position
    import math

    create_backup(filepath)

    board = Board.from_file(filepath)

    # Find component
    component = None
    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')
        if ref == component_ref:
            component = fp
            break

    if not component:
        raise ValueError(f"Component '{component_ref}' not found")

    # Find thermal pad (usually largest pad or specified)
    thermal_pad = None
    max_area = 0

    for pad in component.pads:
        if pad_number and str(getattr(pad, 'number', '')) == str(pad_number):
            thermal_pad = pad
            break
        elif hasattr(pad, 'size') and pad.size:
            area = pad.size.X * pad.size.Y
            if area > max_area:
                max_area = area
                thermal_pad = pad

    if not thermal_pad:
        raise ValueError(f"No suitable thermal pad found on {component_ref}")

    # Find net
    net_code = 0
    for net in board.nets:
        if hasattr(net, 'name') and net.name == net_name:
            net_code = net.number if hasattr(net, 'number') else 0
            break

    # Calculate via positions in grid pattern
    fp_x = component.position.X if component.position else 0
    fp_y = component.position.Y if component.position else 0
    pad_x = thermal_pad.position.X if thermal_pad.position else 0
    pad_y = thermal_pad.position.Y if thermal_pad.position else 0

    center_x = fp_x + pad_x
    center_y = fp_y + pad_y

    pad_w = thermal_pad.size.X if hasattr(thermal_pad, 'size') and thermal_pad.size else 2
    pad_h = thermal_pad.size.Y if hasattr(thermal_pad, 'size') and thermal_pad.size else 2

    # Grid layout based on count
    cols = int(math.ceil(math.sqrt(count)))
    rows = int(math.ceil(count / cols))

    spacing_x = (pad_w - size_mm) / max(cols, 1)
    spacing_y = (pad_h - size_mm) / max(rows, 1)

    vias_added = []
    via_index = 0

    start_x = center_x - (spacing_x * (cols - 1)) / 2
    start_y = center_y - (spacing_y * (rows - 1)) / 2

    for row in range(rows):
        for col in range(cols):
            if via_index >= count:
                break

            x = start_x + col * spacing_x
            y = start_y + row * spacing_y

            via = Via()
            via.position = Position(X=x, Y=y)
            via.drill = drill_mm
            via.size = size_mm
            via.net = net_code
            via.layers = ["F.Cu", "B.Cu"]

            board.traceItems.append(via)
            vias_added.append((x, y))
            via_index += 1

    board.to_file(filepath)

    return {
        "component": component_ref,
        "vias_added": len(vias_added),
        "locations": vias_added,
    }
