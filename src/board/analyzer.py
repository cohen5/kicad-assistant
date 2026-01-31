"""Board analysis - extract statistics and structure from KiCad PCB files."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class BoardStats:
    """Statistics extracted from a PCB."""
    file: str
    tracks: int = 0
    vias: int = 0
    footprints: int = 0
    zones: int = 0
    nets: int = 0
    layers_used: list[str] = field(default_factory=list)
    layer_count: int = 0
    board_width_mm: float = 0.0
    board_height_mm: float = 0.0
    board_area_mm2: float = 0.0
    track_width_min_mm: float = 0.0
    track_width_max_mm: float = 0.0
    via_drill_min_mm: float = 0.0
    via_drill_max_mm: float = 0.0
    component_types: dict = field(default_factory=dict)


def analyze_board(filepath: str) -> BoardStats:
    """Analyze a KiCad PCB file and extract statistics.

    Args:
        filepath: Path to .kicad_pcb file

    Returns:
        BoardStats dataclass with analysis results
    """
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment

    board = Board.from_file(filepath)

    # Separate tracks and vias
    tracks = [t for t in board.traceItems if isinstance(t, Segment)]
    vias = [t for t in board.traceItems if isinstance(t, Via)]

    # Get unique layers used
    layers_used = set()
    for track in tracks:
        if track.layer:
            layers_used.add(track.layer)
    for via in vias:
        if via.layers:
            for layer in via.layers:
                layers_used.add(layer)

    # Board dimensions from Edge.Cuts
    edge_points_x = []
    edge_points_y = []
    for item in board.graphicItems:
        if hasattr(item, 'layer') and item.layer == 'Edge.Cuts':
            if hasattr(item, 'start') and item.start:
                edge_points_x.append(item.start.X)
                edge_points_y.append(item.start.Y)
            if hasattr(item, 'end') and item.end:
                edge_points_x.append(item.end.X)
                edge_points_y.append(item.end.Y)

    width_mm = max(edge_points_x) - min(edge_points_x) if edge_points_x else 0
    height_mm = max(edge_points_y) - min(edge_points_y) if edge_points_y else 0

    # Track widths
    track_widths = [t.width for t in tracks if t.width]
    track_min = min(track_widths) if track_widths else 0
    track_max = max(track_widths) if track_widths else 0

    # Via drills
    via_drills = [v.drill for v in vias if v.drill]
    via_min = min(via_drills) if via_drills else 0
    via_max = max(via_drills) if via_drills else 0

    # Component types
    component_types = {}
    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')
        prefix = "".join(c for c in ref if c.isalpha())
        if prefix:
            component_types[prefix] = component_types.get(prefix, 0) + 1

    return BoardStats(
        file=filepath,
        tracks=len(tracks),
        vias=len(vias),
        footprints=len(board.footprints),
        zones=len(board.zones),
        nets=len(board.nets),
        layers_used=sorted(layers_used),
        layer_count=len(layers_used),
        board_width_mm=round(width_mm, 2),
        board_height_mm=round(height_mm, 2),
        board_area_mm2=round(width_mm * height_mm, 2),
        track_width_min_mm=round(track_min, 4),
        track_width_max_mm=round(track_max, 4),
        via_drill_min_mm=round(via_min, 4),
        via_drill_max_mm=round(via_max, 4),
        component_types=component_types,
    )


def get_board_layers(filepath: str) -> list[dict]:
    """Get all layers defined in the board.

    Returns:
        List of layer info dicts with name, type, and usage
    """
    from kiutils.board import Board

    board = Board.from_file(filepath)

    layers = []
    for layer in board.layers:
        layers.append({
            "name": layer.name if hasattr(layer, 'name') else str(layer),
            "type": layer.type if hasattr(layer, 'type') else "unknown",
        })

    return layers
