#!/usr/bin/env python3
"""Generate Gerber and drill files from KiCad PCB using kicad-cli."""

import argparse
import json
import os
import shutil
import subprocess
import sys

KICAD_PCB_MAGIC = "(kicad_pcb"

# Comprehensive list of Gerber file patterns
GERBER_EXTENSIONS = {
    # Standard extensions
    ".gbr", ".ger",
    # Traditional naming
    ".gtl", ".gbl",  # Top/Bottom copper
    ".gts", ".gbs",  # Top/Bottom soldermask
    ".gto", ".gbo",  # Top/Bottom silkscreen
    ".gtp", ".gbp",  # Top/Bottom paste
    ".gko", ".gm1",  # Board outline / mechanical
    # Inner layers
    ".g2", ".g3", ".g4", ".g5", ".g6", ".g7", ".g8",
    ".in1", ".in2", ".in3", ".in4",
}

DRILL_EXTENSIONS = {
    ".drl", ".xln", ".exc", ".ncd",
}


def check_kicad_cli() -> tuple[bool, str]:
    """Check if kicad-cli is available and return version info."""
    kicad_cli = shutil.which("kicad-cli")
    if not kicad_cli:
        return False, "kicad-cli not found in PATH"

    try:
        result = subprocess.run(
            [kicad_cli, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip() or result.stderr.strip()
        return True, version
    except subprocess.TimeoutExpired:
        return False, "kicad-cli timed out"
    except Exception as e:
        return False, str(e)


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


def is_gerber_file(filename: str) -> bool:
    """Check if a filename appears to be a Gerber file."""
    lower = filename.lower()

    # Check standard extensions
    for ext in GERBER_EXTENSIONS:
        if lower.endswith(ext):
            return True

    # KiCad's modern naming: project-F_Cu.gbr, project-B_SilkS.gbr, etc.
    gerber_layer_patterns = [
        "-f_cu.", "-b_cu.",  # Copper layers
        "-f_mask.", "-b_mask.",  # Solder mask
        "-f_silks.", "-b_silks.",  # Silkscreen
        "-f_paste.", "-b_paste.",  # Paste
        "-edge_cuts.",  # Board outline
        "-in1_cu.", "-in2_cu.", "-in3_cu.", "-in4_cu.",  # Inner copper
        "-f_fab.", "-b_fab.",  # Fab layers
        "-dwgs_user.",  # User drawings
    ]
    for pattern in gerber_layer_patterns:
        if pattern in lower:
            return True

    return False


def is_drill_file(filename: str) -> bool:
    """Check if a filename appears to be a drill file."""
    lower = filename.lower()

    for ext in DRILL_EXTENSIONS:
        if lower.endswith(ext):
            return True

    # KiCad drill file patterns
    if "-pth." in lower or "-npth." in lower:
        return True

    return False


def generate_gerbers(filepath: str, output_dir: str) -> dict:
    """Generate manufacturing files using KiCad CLI."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    results = {
        "input_file": filepath,
        "output_dir": output_dir,
        "gerbers": [],
        "drills": [],
        "other": [],
        "errors": [],
    }

    # Get list of files before generation
    existing_files = set(os.listdir(output_dir)) if os.path.exists(output_dir) else set()

    # Generate Gerbers
    gerber_cmd = [
        "kicad-cli", "pcb", "export", "gerbers",
        "--output", output_dir + "/",  # Trailing slash important
        "--layers", "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts",
        "--subtract-soldermask",
        "--no-protel-ext",  # Use modern .gbr extension
        filepath,
    ]

    try:
        result = subprocess.run(
            gerber_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            results["errors"].append({
                "stage": "gerber_generation",
                "message": f"Exit code {result.returncode}",
                "stderr": result.stderr[:500] if result.stderr else None,
            })
    except FileNotFoundError:
        results["errors"].append({
            "stage": "gerber_generation",
            "message": "kicad-cli not found",
        })
        return results
    except subprocess.TimeoutExpired:
        results["errors"].append({
            "stage": "gerber_generation",
            "message": "Command timed out after 120 seconds",
        })
        return results

    # Generate drill files
    drill_cmd = [
        "kicad-cli", "pcb", "export", "drill",
        "--output", output_dir + "/",
        "--format", "excellon",
        "--drill-origin", "plot",
        "--excellon-units", "mm",
        "--generate-map",
        "--map-format", "gerberx2",
        filepath,
    ]

    try:
        result = subprocess.run(
            drill_cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            results["errors"].append({
                "stage": "drill_generation",
                "message": f"Exit code {result.returncode}",
                "stderr": result.stderr[:500] if result.stderr else None,
            })
    except subprocess.TimeoutExpired:
        results["errors"].append({
            "stage": "drill_generation",
            "message": "Command timed out after 60 seconds",
        })

    # Categorize generated files
    current_files = set(os.listdir(output_dir))
    new_files = current_files - existing_files

    for filename in sorted(new_files):
        filepath = os.path.join(output_dir, filename)
        file_info = {
            "name": filename,
            "size_bytes": os.path.getsize(filepath),
        }

        if is_drill_file(filename):
            results["drills"].append(file_info)
        elif is_gerber_file(filename):
            results["gerbers"].append(file_info)
        else:
            results["other"].append(file_info)

    # Summary
    results["summary"] = {
        "total_files": len(new_files),
        "gerber_count": len(results["gerbers"]),
        "drill_count": len(results["drills"]),
        "error_count": len(results["errors"]),
        "status": "success" if not results["errors"] else "partial" if new_files else "failed",
    }

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Gerbers from KiCad PCB")
    parser.add_argument("--file", required=True, help="Path to .kicad_pcb file")
    parser.add_argument("--output", required=True, help="Output directory for Gerber files")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    # Check kicad-cli availability
    available, version_info = check_kicad_cli()
    if not available:
        print(f"Error: {version_info}", file=sys.stderr)
        print("Gerber export requires kicad-cli from KiCad 7 or later.", file=sys.stderr)
        sys.exit(1)

    # Validate the input file
    valid, error = validate_kicad_file(args.file)
    if not valid:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Generate files
    result = generate_gerbers(args.file, args.output)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Text format
        print(f"Gerber Export: {result['input_file']}")
        print(f"Output: {result['output_dir']}")
        print(f"Status: {result['summary']['status'].upper()}")
        print()

        if result["gerbers"]:
            print(f"Gerber files ({len(result['gerbers'])}):")
            for f in result["gerbers"]:
                print(f"  {f['name']} ({f['size_bytes']} bytes)")

        if result["drills"]:
            print(f"\nDrill files ({len(result['drills'])}):")
            for f in result["drills"]:
                print(f"  {f['name']} ({f['size_bytes']} bytes)")

        if result["errors"]:
            print(f"\nErrors:")
            for e in result["errors"]:
                print(f"  [{e['stage']}] {e['message']}")

    # Exit with appropriate code
    if result["summary"]["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
