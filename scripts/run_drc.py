#!/usr/bin/env python3
"""Run DRC (Design Rule Check) on a KiCad PCB file using kicad-cli."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

KICAD_PCB_MAGIC = "(kicad_pcb"


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


def run_drc(filepath: str, output_dir: str = None) -> dict:
    """Run KiCad DRC and parse results."""
    # Determine output location
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="kicad_drc_")
        cleanup_output = True
    else:
        os.makedirs(output_dir, exist_ok=True)
        cleanup_output = False

    report_file = os.path.join(output_dir, "drc_report.json")

    # Build kicad-cli command
    cmd = [
        "kicad-cli", "pcb", "drc",
        "--output", report_file,
        "--format", "json",
        "--severity-all",  # Include all severity levels
        filepath,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for large boards
        )

        if os.path.exists(report_file):
            with open(report_file, "r", encoding="utf-8") as f:
                drc_data = json.load(f)

            # Parse violations
            violations = drc_data.get("violations", [])

            # Categorize by severity
            errors = []
            warnings = []
            exclusions = []

            for v in violations:
                severity = v.get("severity", "").lower()
                if severity == "error":
                    errors.append(v)
                elif severity == "warning":
                    warnings.append(v)
                elif severity == "exclusion":
                    exclusions.append(v)
                else:
                    warnings.append(v)  # Default to warning

            # Build summary
            summary = {
                "file": filepath,
                "status": "pass" if len(errors) == 0 else "fail",
                "total_violations": len(violations),
                "errors": len(errors),
                "warnings": len(warnings),
                "exclusions": len(exclusions),
                "kicad_version": drc_data.get("source", {}).get("kicad_version", "unknown"),
            }

            # Include violation details (limit to first 50 for readability)
            if errors or warnings:
                summary["error_details"] = errors[:25]
                summary["warning_details"] = warnings[:25]

            # Keep the report file if user specified output_dir
            if not cleanup_output:
                summary["report_file"] = report_file

            return summary

        else:
            # No report generated
            return {
                "file": filepath,
                "status": "error",
                "message": f"DRC report not generated. Exit code: {result.returncode}",
                "stderr": result.stderr[:500] if result.stderr else None,
                "stdout": result.stdout[:500] if result.stdout else None,
            }

    except subprocess.TimeoutExpired:
        return {
            "file": filepath,
            "status": "error",
            "message": "DRC check timed out after 120 seconds",
        }
    except FileNotFoundError:
        return {
            "file": filepath,
            "status": "error",
            "message": "kicad-cli not found. Ensure KiCad 7+ is installed and kicad-cli is in PATH.",
        }
    except Exception as e:
        return {
            "file": filepath,
            "status": "error",
            "message": f"Unexpected error: {e}",
        }
    finally:
        # Clean up temp directory if we created it
        if cleanup_output and os.path.exists(output_dir):
            try:
                import shutil
                shutil.rmtree(output_dir)
            except Exception:
                pass


def format_violation(v: dict) -> str:
    """Format a single violation for human-readable output."""
    desc = v.get("description", "Unknown violation")
    severity = v.get("severity", "?").upper()
    rule = v.get("type", "")

    # Extract position if available
    items = v.get("items", [])
    pos_str = ""
    if items:
        first_item = items[0]
        pos = first_item.get("pos", {})
        if pos:
            x = pos.get("x", 0)
            y = pos.get("y", 0)
            pos_str = f" at ({x:.2f}, {y:.2f})"

    return f"[{severity}] {rule}: {desc}{pos_str}"


def main():
    parser = argparse.ArgumentParser(description="Run DRC on KiCad PCB")
    parser.add_argument("--file", required=True, help="Path to .kicad_pcb file")
    parser.add_argument("--output-dir", help="Directory to save DRC report")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    # Check kicad-cli availability
    available, version_info = check_kicad_cli()
    if not available:
        print(f"Error: {version_info}", file=sys.stderr)
        print("DRC requires kicad-cli from KiCad 7 or later.", file=sys.stderr)
        sys.exit(1)

    # Validate the input file
    valid, error = validate_kicad_file(args.file)
    if not valid:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Run DRC
    result = run_drc(args.file, args.output_dir)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # Text format
        print(f"DRC Report: {result['file']}")
        print(f"Status: {result['status'].upper()}")

        if result["status"] == "error":
            print(f"Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"")
            print(f"Summary:")
            print(f"  Errors: {result['errors']}")
            print(f"  Warnings: {result['warnings']}")
            print(f"  Exclusions: {result.get('exclusions', 0)}")

            if result.get("error_details"):
                print(f"\nErrors:")
                for v in result["error_details"]:
                    print(f"  {format_violation(v)}")

            if result.get("warning_details"):
                print(f"\nWarnings:")
                for v in result["warning_details"][:10]:  # Limit text output
                    print(f"  {format_violation(v)}")
                if len(result.get("warning_details", [])) > 10:
                    remaining = len(result["warning_details"]) - 10
                    print(f"  ... and {remaining} more warnings")

    # Exit with error code if DRC failed
    if result["status"] == "fail":
        sys.exit(1)
    elif result["status"] == "error":
        sys.exit(2)


if __name__ == "__main__":
    main()
