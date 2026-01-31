#!/usr/bin/env python3
"""Compare two KiCad PCB versions and summarize changes."""

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


def get_board_data(filepath: str) -> dict:
    """Extract comparable data from a KiCad board."""
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment

    board = Board.from_file(filepath)

    # Collect component data
    components = {}
    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')
        value = fp.properties.get('Value', '?')
        footprint = fp.entryName or fp.libId or '?'

        components[ref] = {
            "value": value,
            "footprint": footprint,
        }

    # Count tracks and vias
    tracks = [t for t in board.traceItems if isinstance(t, Segment)]
    vias = [t for t in board.traceItems if isinstance(t, Via)]

    # Get layers used
    layers = set()
    for track in tracks:
        if track.layer:
            layers.add(track.layer)

    return {
        "components": components,
        "track_count": len(tracks),
        "via_count": len(vias),
        "zone_count": len(board.zones),
        "net_count": len(board.nets),
        "layers": layers,
    }


def compare_boards(old_path: str, new_path: str) -> dict:
    """Compare two PCB versions and return differences."""
    old_data = get_board_data(old_path)
    new_data = get_board_data(new_path)

    old_refs = set(old_data["components"].keys())
    new_refs = set(new_data["components"].keys())

    # Component changes
    added_refs = new_refs - old_refs
    removed_refs = old_refs - new_refs
    common_refs = old_refs & new_refs

    # Check for value/footprint changes in common components
    modified = []
    for ref in common_refs:
        old_comp = old_data["components"][ref]
        new_comp = new_data["components"][ref]

        changes = []
        if old_comp["value"] != new_comp["value"]:
            changes.append({
                "field": "value",
                "old": old_comp["value"],
                "new": new_comp["value"],
            })
        if old_comp["footprint"] != new_comp["footprint"]:
            changes.append({
                "field": "footprint",
                "old": old_comp["footprint"],
                "new": new_comp["footprint"],
            })

        if changes:
            modified.append({
                "reference": ref,
                "changes": changes,
            })

    # Build added components list with details
    added_components = []
    for ref in sorted(added_refs):
        comp = new_data["components"][ref]
        added_components.append({
            "reference": ref,
            "value": comp["value"],
            "footprint": comp["footprint"],
        })

    # Build removed components list with details
    removed_components = []
    for ref in sorted(removed_refs):
        comp = old_data["components"][ref]
        removed_components.append({
            "reference": ref,
            "value": comp["value"],
            "footprint": comp["footprint"],
        })

    # Layer changes
    old_layers = old_data["layers"]
    new_layers = new_data["layers"]
    added_layers = new_layers - old_layers
    removed_layers = old_layers - new_layers

    return {
        "old_file": old_path,
        "new_file": new_path,
        "summary": {
            "components_added": len(added_refs),
            "components_removed": len(removed_refs),
            "components_modified": len(modified),
            "track_count_change": new_data["track_count"] - old_data["track_count"],
            "via_count_change": new_data["via_count"] - old_data["via_count"],
            "zone_count_change": new_data["zone_count"] - old_data["zone_count"],
            "net_count_change": new_data["net_count"] - old_data["net_count"],
            "layers_added": len(added_layers),
            "layers_removed": len(removed_layers),
        },
        "old_stats": {
            "components": len(old_refs),
            "tracks": old_data["track_count"],
            "vias": old_data["via_count"],
            "zones": old_data["zone_count"],
            "nets": old_data["net_count"],
        },
        "new_stats": {
            "components": len(new_refs),
            "tracks": new_data["track_count"],
            "vias": new_data["via_count"],
            "zones": new_data["zone_count"],
            "nets": new_data["net_count"],
        },
        "added_components": added_components,
        "removed_components": removed_components,
        "modified_components": modified,
        "added_layers": sorted(added_layers),
        "removed_layers": sorted(removed_layers),
    }


def format_text_output(result: dict) -> str:
    """Format comparison result as human-readable text."""
    lines = [
        f"Board Comparison",
        f"  Old: {result['old_file']}",
        f"  New: {result['new_file']}",
        "",
        "Summary:",
    ]

    summary = result["summary"]

    # Component changes
    if summary["components_added"] > 0:
        lines.append(f"  + {summary['components_added']} components added")
    if summary["components_removed"] > 0:
        lines.append(f"  - {summary['components_removed']} components removed")
    if summary["components_modified"] > 0:
        lines.append(f"  ~ {summary['components_modified']} components modified")

    # Routing changes
    track_change = summary["track_count_change"]
    via_change = summary["via_count_change"]
    if track_change != 0:
        sign = "+" if track_change > 0 else ""
        lines.append(f"  {sign}{track_change} tracks")
    if via_change != 0:
        sign = "+" if via_change > 0 else ""
        lines.append(f"  {sign}{via_change} vias")

    # Net changes
    net_change = summary["net_count_change"]
    if net_change != 0:
        sign = "+" if net_change > 0 else ""
        lines.append(f"  {sign}{net_change} nets")

    # Layer changes
    if summary["layers_added"] > 0:
        lines.append(f"  + {summary['layers_added']} layers added")
    if summary["layers_removed"] > 0:
        lines.append(f"  - {summary['layers_removed']} layers removed")

    # No changes case
    if all(v == 0 for v in summary.values()):
        lines.append("  No changes detected")

    # Details
    if result["added_components"]:
        lines.extend(["", "Added components:"])
        for comp in result["added_components"][:20]:
            lines.append(f"  + {comp['reference']}: {comp['value']} ({comp['footprint']})")
        if len(result["added_components"]) > 20:
            lines.append(f"  ... and {len(result['added_components']) - 20} more")

    if result["removed_components"]:
        lines.extend(["", "Removed components:"])
        for comp in result["removed_components"][:20]:
            lines.append(f"  - {comp['reference']}: {comp['value']} ({comp['footprint']})")
        if len(result["removed_components"]) > 20:
            lines.append(f"  ... and {len(result['removed_components']) - 20} more")

    if result["modified_components"]:
        lines.extend(["", "Modified components:"])
        for mod in result["modified_components"][:20]:
            for change in mod["changes"]:
                lines.append(f"  ~ {mod['reference']} {change['field']}: {change['old']} -> {change['new']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare two KiCad PCB versions")
    parser.add_argument("--old", required=True, help="Path to old .kicad_pcb file")
    parser.add_argument("--new", required=True, help="Path to new .kicad_pcb file")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        print("Error: kiutils not installed. Run: pip install kiutils", file=sys.stderr)
        sys.exit(1)

    # Validate both files
    for path, label in [(args.old, "old"), (args.new, "new")]:
        valid, error = validate_kicad_file(path)
        if not valid:
            print(f"Error ({label} file): {error}", file=sys.stderr)
            sys.exit(1)

    try:
        result = compare_boards(args.old, args.new)

        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(format_text_output(result))

    except Exception as e:
        print(f"Error comparing boards: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
