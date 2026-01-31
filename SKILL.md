---
name: kicad-assistant
description: Analyze KiCad PCB files, run DRC checks, export BOMs and Gerbers
metadata: {"moltbot":{"requires":{"bins":["python3"],"env":[]},"os":["darwin","linux"]}}
---

# KiCad PCB Assistant

Use this skill when the user asks about:
- PCB design analysis, DRC checks, or design rule violations
- BOM (Bill of Materials) export or component lists
- Gerber generation or manufacturing file export
- Track widths, via counts, layer stackups, or board statistics
- Panelization or manufacturing preparation

## Prerequisites

The following must be installed on the Moltbot host:
- Python 3.10+
- `pip install kiutils` (pure Python KiCad file parser - no KiCad installation required)
- Optional: KiCad 7+ with `kicad-cli` in PATH (only needed for DRC and Gerber export)
- Optional: `pip install kikit` (only needed for panelization)

## Available Commands

### Analyze a PCB file

```bash
python3 {baseDir}/scripts/analyze_pcb.py --file "/path/to/board.kicad_pcb"
```

Returns: Track count, via count, component count, layer usage, board dimensions.

Options:
- `--format json` (default) or `--format text` for human-readable output

### Run DRC Check

```bash
python3 {baseDir}/scripts/run_drc.py --file "/path/to/board.kicad_pcb"
```

Returns: List of DRC violations with coordinates and severity.

Options:
- `--output-dir "/path/"` to specify where to save the DRC report

Note: Requires KiCad 7+ with `kicad-cli` in PATH.

### Export BOM

```bash
python3 {baseDir}/scripts/export_bom.py --file "/path/to/board.kicad_pcb" --format csv
```

Outputs: CSV file with Reference, Value, Footprint, Quantity.

Options:
- `--format csv` (default) or `--format json`
- `--output "/path/to/bom.csv"` to save to file instead of stdout

### Generate Gerbers

```bash
python3 {baseDir}/scripts/generate_gerbers.py --file "/path/to/board.kicad_pcb" --output "/path/to/output/"
```

Outputs: Gerber files + drill files ready for manufacturing.

Note: Requires KiCad 7+ with `kicad-cli` in PATH.

### Panelize Board (via KiKit)

```bash
kikit panelize grid --gridsize 2 2 --space 3 "/path/to/board.kicad_pcb" "/path/to/panel.kicad_pcb"
```

Creates a 2x2 panel with 3mm spacing between boards.

### Compare Two Board Versions

```bash
python3 {baseDir}/scripts/compare_boards.py --old "/path/to/v1.kicad_pcb" --new "/path/to/v2.kicad_pcb"
```

Returns: Summary of added/removed components and routing changes.

### DFM (Design for Manufacturing) Check

```bash
python3 {baseDir}/scripts/dfm_check.py --file "/path/to/board.kicad_pcb"
```

Returns: Manufacturing rule violations (track width, clearance, drill size, etc.)

Options:
- `--rules "/path/to/rules.json"` to use custom DFM rules

## Response Guidelines

- Always confirm the file path exists before running commands
- Present DRC results in a clear summary (X errors, Y warnings)
- For BOM exports, offer to format as table or save to file
- If KiCad or dependencies aren't installed, inform the user and suggest alternatives
- When analyzing boards, highlight any concerning metrics (e.g., very high via count, unusual layer usage)
- For DFM checks, explain what each violation means and how to fix it
