#!/usr/bin/env python3
"""Export BOM (Bill of Materials) from KiCad PCB file."""

import argparse
import csv
import json
import os
import re
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


def natural_sort_key(ref: str):
    """Natural sort key for reference designators (R1, R2, R10 not R1, R10, R2)."""
    parts = re.split(r'(\d+)', ref)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def export_bom(filepath: str, include_all: bool = False) -> list:
    """Extract BOM data from a KiCad PCB."""
    from kiutils.board import Board

    board = Board.from_file(filepath)

    # Group components by value and footprint
    components = {}

    for fp in board.footprints:
        # Extract component properties
        ref = fp.properties.get('Reference', '?')
        value = fp.properties.get('Value', '?')

        # Get footprint name from libId (format: "Library:Footprint")
        footprint_name = fp.entryName or fp.libId or '?'

        # Skip non-component footprints unless include_all is set
        if not include_all:
            ref_prefix = "".join(c for c in ref if c.isalpha())
            if ref_prefix in ("FID", "TP", "MH", "H", "REF", "LOGO"):
                continue

        # Group by value + footprint
        key = (value, footprint_name)

        if key not in components:
            components[key] = {
                "value": value,
                "footprint": footprint_name,
                "references": [],
                "quantity": 0,
            }
        components[key]["references"].append(ref)
        components[key]["quantity"] += 1

    # Process and sort
    bom = []
    for comp in components.values():
        comp["references"] = sorted(comp["references"], key=natural_sort_key)
        bom.append(comp)

    # Sort BOM entries by first reference
    bom.sort(key=lambda x: natural_sort_key(x["references"][0]) if x["references"] else [])

    return bom


def main():
    parser = argparse.ArgumentParser(description="Export BOM from KiCad PCB")
    parser.add_argument("--file", required=True, help="Path to .kicad_pcb file")
    parser.add_argument("--format", choices=["csv", "json"], default="csv",
                        help="Output format (default: csv)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--include-all", action="store_true",
                        help="Include fiducials, test points, and mounting holes")
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
        bom = export_bom(args.file, args.include_all)

        # Determine output destination
        outfile = None
        close_file = False
        if args.output:
            outfile = open(args.output, "w", newline="", encoding="utf-8")
            close_file = True
        else:
            outfile = sys.stdout

        try:
            if args.format == "json":
                json.dump(bom, outfile, indent=2)
                outfile.write("\n")
            else:
                writer = csv.writer(outfile)
                writer.writerow(["Reference", "Value", "Footprint", "Quantity"])
                for comp in bom:
                    writer.writerow([
                        ", ".join(comp["references"]),
                        comp["value"],
                        comp["footprint"],
                        comp["quantity"],
                    ])
        finally:
            if close_file:
                outfile.close()

        if args.output:
            print(f"BOM exported to {args.output}", file=sys.stderr)

    except Exception as e:
        print(f"Error exporting BOM: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
