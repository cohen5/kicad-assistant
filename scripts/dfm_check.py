#!/usr/bin/env python3
"""Check KiCad PCB against Design for Manufacturing (DFM) rules."""

import argparse
import json
import os
import sys

KICAD_PCB_MAGIC = "(kicad_pcb"

# Default DFM rules based on common PCB fab capabilities (JLCPCB, PCBWay, etc.)
DEFAULT_DFM_RULES = {
    "min_track_width_mm": 0.127,      # 5 mil minimum track
    "min_track_spacing_mm": 0.127,    # 5 mil minimum spacing
    "min_via_drill_mm": 0.3,          # Minimum via drill diameter
    "min_via_annular_ring_mm": 0.125, # Minimum annular ring
    "min_hole_to_hole_mm": 0.5,       # Minimum hole-to-hole spacing
    "min_silk_width_mm": 0.15,        # Minimum silkscreen line width
    "min_silk_height_mm": 0.8,        # Minimum silkscreen text height
    "min_smd_pad_mm": 0.2,            # Minimum SMD pad dimension
    "min_drill_size_mm": 0.2,         # Minimum drill size (any hole)
    "max_aspect_ratio": 10.0,         # Maximum hole aspect ratio (depth/diameter)
    "board_thickness_mm": 1.6,        # Assumed board thickness for aspect ratio
}

# Named rule presets
RULE_PRESETS = {
    "standard": DEFAULT_DFM_RULES,
    "budget": {
        "min_track_width_mm": 0.15,
        "min_track_spacing_mm": 0.15,
        "min_via_drill_mm": 0.3,
        "min_via_annular_ring_mm": 0.15,
        "min_hole_to_hole_mm": 0.55,
        "min_silk_width_mm": 0.2,
        "min_silk_height_mm": 1.0,
        "min_smd_pad_mm": 0.25,
        "min_drill_size_mm": 0.3,
        "max_aspect_ratio": 8.0,
        "board_thickness_mm": 1.6,
    },
    "advanced": {
        "min_track_width_mm": 0.09,   # 3.5 mil
        "min_track_spacing_mm": 0.09,
        "min_via_drill_mm": 0.2,
        "min_via_annular_ring_mm": 0.1,
        "min_hole_to_hole_mm": 0.45,
        "min_silk_width_mm": 0.12,
        "min_silk_height_mm": 0.6,
        "min_smd_pad_mm": 0.15,
        "min_drill_size_mm": 0.15,
        "max_aspect_ratio": 12.0,
        "board_thickness_mm": 1.6,
    },
}


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


def check_dfm(filepath: str, rules: dict) -> dict:
    """Check a KiCad PCB against DFM rules."""
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment

    board = Board.from_file(filepath)
    violations = []

    # Separate tracks and vias
    tracks = [t for t in board.traceItems if isinstance(t, Segment)]
    vias = [t for t in board.traceItems if isinstance(t, Via)]

    # Check track widths
    min_track = rules.get("min_track_width_mm", 0)
    for track in tracks:
        if track.width and track.width < min_track:
            violations.append({
                "type": "track_width",
                "severity": "error",
                "message": f"Track width {track.width:.4f}mm < minimum {min_track}mm",
                "value_mm": track.width,
                "limit_mm": min_track,
                "location": f"({track.start.X:.2f}, {track.start.Y:.2f})" if track.start else "unknown",
                "layer": track.layer,
            })

    # Check via drill sizes and annular ring
    min_via_drill = rules.get("min_via_drill_mm", 0)
    min_annular = rules.get("min_via_annular_ring_mm", 0)
    board_thickness = rules.get("board_thickness_mm", 1.6)
    max_aspect_ratio = rules.get("max_aspect_ratio", 10.0)

    for via in vias:
        # Check drill size
        if via.drill and via.drill < min_via_drill:
            violations.append({
                "type": "via_drill",
                "severity": "error",
                "message": f"Via drill {via.drill:.4f}mm < minimum {min_via_drill}mm",
                "value_mm": via.drill,
                "limit_mm": min_via_drill,
                "location": f"({via.position.X:.2f}, {via.position.Y:.2f})" if via.position else "unknown",
            })

        # Check annular ring
        if via.drill and via.size:
            annular_mm = (via.size - via.drill) / 2
            if annular_mm < min_annular:
                violations.append({
                    "type": "annular_ring",
                    "severity": "error",
                    "message": f"Via annular ring {annular_mm:.4f}mm < minimum {min_annular}mm",
                    "value_mm": annular_mm,
                    "limit_mm": min_annular,
                    "location": f"({via.position.X:.2f}, {via.position.Y:.2f})" if via.position else "unknown",
                })

        # Check aspect ratio
        if via.drill:
            aspect_ratio = board_thickness / via.drill
            if aspect_ratio > max_aspect_ratio:
                violations.append({
                    "type": "aspect_ratio",
                    "severity": "warning",
                    "message": f"Via aspect ratio {aspect_ratio:.1f}:1 > maximum {max_aspect_ratio}:1",
                    "value": aspect_ratio,
                    "limit": max_aspect_ratio,
                    "location": f"({via.position.X:.2f}, {via.position.Y:.2f})" if via.position else "unknown",
                })

    # Check footprint pads
    min_smd = rules.get("min_smd_pad_mm", 0)
    min_drill = rules.get("min_drill_size_mm", 0)

    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')

        for pad in fp.pads:
            # Check SMD pad size
            pad_type = getattr(pad, 'type', '')
            if pad_type == 'smd' and hasattr(pad, 'size') and pad.size:
                min_dim = min(pad.size.X, pad.size.Y) if hasattr(pad.size, 'X') else 0
                if min_dim > 0 and min_dim < min_smd:
                    violations.append({
                        "type": "smd_pad_size",
                        "severity": "warning",
                        "message": f"SMD pad on {ref} is {min_dim:.4f}mm < minimum {min_smd}mm",
                        "value_mm": min_dim,
                        "limit_mm": min_smd,
                        "component": ref,
                    })

            # Check through-hole drill
            if hasattr(pad, 'drill') and pad.drill:
                drill_size = pad.drill.diameter if hasattr(pad.drill, 'diameter') else pad.drill
                if isinstance(drill_size, (int, float)) and drill_size > 0 and drill_size < min_drill:
                    violations.append({
                        "type": "hole_size",
                        "severity": "error",
                        "message": f"Drill hole on {ref} is {drill_size:.4f}mm < minimum {min_drill}mm",
                        "value_mm": drill_size,
                        "limit_mm": min_drill,
                        "component": ref,
                    })

    # Categorize violations
    errors = [v for v in violations if v.get("severity") == "error"]
    warnings = [v for v in violations if v.get("severity") == "warning"]

    return {
        "file": filepath,
        "rules_used": rules,
        "status": "pass" if len(errors) == 0 else "fail",
        "total_violations": len(violations),
        "errors": len(errors),
        "warnings": len(warnings),
        "error_details": errors[:50],  # Limit output
        "warning_details": warnings[:50],
    }


def format_text_output(result: dict) -> str:
    """Format DFM check results as human-readable text."""
    lines = [
        f"DFM Check: {result['file']}",
        f"Status: {result['status'].upper()}",
        "",
        f"Summary:",
        f"  Errors: {result['errors']}",
        f"  Warnings: {result['warnings']}",
    ]

    if result.get("error_details"):
        lines.extend(["", "Errors:"])
        for v in result["error_details"][:20]:
            lines.append(f"  [{v['type']}] {v['message']}")
        if len(result["error_details"]) > 20:
            lines.append(f"  ... and {len(result['error_details']) - 20} more")

    if result.get("warning_details"):
        lines.extend(["", "Warnings:"])
        for v in result["warning_details"][:10]:
            lines.append(f"  [{v['type']}] {v['message']}")
        if len(result["warning_details"]) > 10:
            lines.append(f"  ... and {len(result['warning_details']) - 10} more")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check KiCad PCB against DFM rules")
    parser.add_argument("--file", help="Path to .kicad_pcb file")
    parser.add_argument("--rules", help="Path to custom rules JSON file")
    parser.add_argument("--preset", choices=list(RULE_PRESETS.keys()), default="standard",
                        help="Rule preset to use (default: standard)")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--list-presets", action="store_true",
                        help="List available rule presets and exit")
    args = parser.parse_args()

    # List presets if requested (doesn't require --file)
    if args.list_presets:
        print("Available DFM rule presets:")
        for name, rules in RULE_PRESETS.items():
            print(f"\n{name}:")
            for key, value in sorted(rules.items()):
                print(f"  {key}: {value}")
        sys.exit(0)

    # Require --file for actual DFM checks
    if not args.file:
        parser.error("--file is required unless using --list-presets")

    # Check dependencies
    if not check_dependencies():
        print("Error: kiutils not installed. Run: pip install kiutils", file=sys.stderr)
        sys.exit(1)

    # Validate the input file
    valid, error = validate_kicad_file(args.file)
    if not valid:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Load rules
    if args.rules:
        try:
            with open(args.rules, "r") as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Error loading rules file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        rules = RULE_PRESETS.get(args.preset, DEFAULT_DFM_RULES)

    try:
        result = check_dfm(args.file, rules)

        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(format_text_output(result))

        # Exit with error if DFM check failed
        if result["status"] == "fail":
            sys.exit(1)

    except Exception as e:
        print(f"Error running DFM check: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
