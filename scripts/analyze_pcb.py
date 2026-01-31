#!/usr/bin/env python3
"""Analyze a KiCad PCB file and return statistics."""

import argparse
import json
import os
import sys

KICAD_PCB_MAGIC = "(kicad_pcb"


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        from kiutils.board import Board
        return True
    except ImportError:
        return False


def validate_kicad_file(filepath: str) -> tuple[bool, str]:
    """Validate that the file exists and appears to be a KiCad PCB file."""
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    if not filepath.endswith(".kicad_pcb"):
        return False, f"File does not have .kicad_pcb extension: {filepath}"

    # Check file magic/header
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            header = f.read(64)
            if KICAD_PCB_MAGIC not in header:
                return False, f"File does not appear to be a valid KiCad PCB file: {filepath}"
    except UnicodeDecodeError:
        return False, f"File is not a valid text-based KiCad PCB file: {filepath}"
    except IOError as e:
        return False, f"Cannot read file: {e}"

    return True, ""


def analyze(filepath: str) -> dict:
    """Load a KiCad PCB and extract statistics."""
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment

    board = Board.from_file(filepath)

    # Separate tracks and vias
    tracks = [t for t in board.traceItems if isinstance(t, Segment)]
    vias = [t for t in board.traceItems if isinstance(t, Via)]
    footprints = board.footprints
    zones = board.zones

    # Get unique layers used by tracks
    layers_used = set()
    for track in tracks:
        if track.layer:
            layers_used.add(track.layer)
    for via in vias:
        if via.layers:
            for layer in via.layers:
                layers_used.add(layer)

    # Calculate board dimensions from general settings or edge cuts
    width_mm = 0.0
    height_mm = 0.0

    # Try to get board outline from Edge.Cuts graphic items
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
            if hasattr(item, 'center') and item.center:
                edge_points_x.append(item.center.X)
                edge_points_y.append(item.center.Y)

    if edge_points_x and edge_points_y:
        width_mm = max(edge_points_x) - min(edge_points_x)
        height_mm = max(edge_points_y) - min(edge_points_y)

    # Collect track width statistics
    track_widths = [t.width for t in tracks if t.width]
    track_width_stats = {}
    if track_widths:
        track_width_stats = {
            "min_mm": round(min(track_widths), 4),
            "max_mm": round(max(track_widths), 4),
            "unique_count": len(set(round(w, 4) for w in track_widths)),
        }

    # Collect via statistics
    via_drills = [v.drill for v in vias if v.drill]
    via_sizes = [v.size for v in vias if v.size]
    via_stats = {}
    if via_drills:
        via_stats = {
            "min_drill_mm": round(min(via_drills), 4),
            "max_drill_mm": round(max(via_drills), 4),
            "unique_drill_sizes": len(set(round(d, 4) for d in via_drills)),
        }
    if via_sizes:
        via_stats["min_size_mm"] = round(min(via_sizes), 4)
        via_stats["max_size_mm"] = round(max(via_sizes), 4)

    # Count components by type (based on reference prefix)
    component_types = {}
    for fp in footprints:
        ref = fp.properties.get('Reference', '?')
        # Extract prefix (e.g., "R" from "R1", "C" from "C42")
        prefix = "".join(c for c in ref if c.isalpha())
        if prefix:
            component_types[prefix] = component_types.get(prefix, 0) + 1

    # Get layer information (board.layers is a list of LayerToken objects)
    layer_info = {}
    if board.layers:
        for layer in board.layers:
            if hasattr(layer, 'name') and hasattr(layer, 'type'):
                layer_info[layer.name] = layer.type

    stats = {
        "file": filepath,
        "tracks": len(tracks),
        "vias": len(vias),
        "footprints": len(footprints),
        "zones": len(zones),
        "nets": len(board.nets),
        "layers_used": sorted(layers_used),
        "layer_count": len(layers_used),
        "board_width_mm": round(width_mm, 2),
        "board_height_mm": round(height_mm, 2),
        "board_area_mm2": round(width_mm * height_mm, 2),
        "track_width_stats": track_width_stats,
        "via_stats": via_stats,
        "component_types": component_types,
    }

    return stats


def format_text_output(stats: dict) -> str:
    """Format statistics as human-readable text."""
    lines = [
        f"PCB Analysis: {stats['file']}",
        f"",
        f"Board Dimensions:",
        f"  Size: {stats['board_width_mm']} x {stats['board_height_mm']} mm",
        f"  Area: {stats['board_area_mm2']} mm²",
        f"",
        f"Routing:",
        f"  Tracks: {stats['tracks']}",
        f"  Vias: {stats['vias']}",
        f"  Zones: {stats['zones']}",
        f"  Nets: {stats['nets']}",
        f"  Layers used: {', '.join(stats['layers_used']) if stats['layers_used'] else 'none'}",
    ]

    if stats.get("track_width_stats"):
        tw = stats["track_width_stats"]
        lines.extend([
            f"  Track widths: {tw['min_mm']} - {tw['max_mm']} mm ({tw['unique_count']} unique)",
        ])

    if stats.get("via_stats"):
        vs = stats["via_stats"]
        lines.extend([
            f"  Via drills: {vs.get('min_drill_mm', 'N/A')} - {vs.get('max_drill_mm', 'N/A')} mm ({vs.get('unique_drill_sizes', 0)} sizes)",
        ])

    lines.extend([
        f"",
        f"Components:",
        f"  Total footprints: {stats['footprints']}",
    ])

    if stats.get("component_types"):
        for prefix, count in sorted(stats["component_types"].items()):
            lines.append(f"    {prefix}: {count}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze a KiCad PCB file")
    parser.add_argument("--file", required=True, help="Path to .kicad_pcb file")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    # Check dependencies first
    if not check_dependencies():
        print("Error: kiutils not installed. Run: pip install kiutils", file=sys.stderr)
        sys.exit(1)

    # Validate the input file
    valid, error = validate_kicad_file(args.file)
    if not valid:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    try:
        result = analyze(args.file)

        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(format_text_output(result))

    except Exception as e:
        print(f"Error analyzing PCB: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
