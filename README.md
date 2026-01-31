# KiCad Assistant Skill

An AI skill for analyzing KiCad PCB files, exporting BOMs, running DFM checks, and comparing board versions.

## Features

- **Analyze PCB** - Extract track/via counts, board dimensions, component statistics
- **Export BOM** - Generate Bill of Materials in CSV or JSON format
- **DFM Check** - Validate against manufacturing rules (JLCPCB, PCBWay compatible)
- **Compare Boards** - Diff two PCB versions to see what changed
- **Run DRC** - Design Rule Check via kicad-cli (requires KiCad 7+)
- **Generate Gerbers** - Export manufacturing files via kicad-cli

## Installation

### For Claude Code / Moltbot

```bash
# Clone to skills directory
git clone https://github.com/YOUR_USERNAME/kicad-assistant ~/.claude/skills/kicad-assistant

# Or for Moltbot
git clone https://github.com/YOUR_USERNAME/kicad-assistant ~/.moltbot/skills/kicad-assistant

# Install Python dependency
pip install kiutils
```

### Manual Installation

```bash
# Copy files
cp -r kicad-assistant ~/.claude/skills/

# Install dependency
pip install kiutils

# Optional: for DRC and Gerber export
# Install KiCad 7+ and ensure kicad-cli is in PATH
```

## Usage

### Analyze a PCB

```bash
python3 scripts/analyze_pcb.py --file board.kicad_pcb --format text
```

Output:
```
PCB Analysis: board.kicad_pcb

Board Dimensions:
  Size: 38.95 x 15 mm
  Area: 584.25 mm²

Routing:
  Tracks: 40
  Vias: 30
  Zones: 5
  Nets: 50
  Layers used: B.Cu, F.Cu
  Track widths: 0.2934 - 0.75 mm (2 unique)

Components:
  Total footprints: 39
    C: 18
    R: 5
    U: 4
    ...
```

### Export BOM

```bash
python3 scripts/export_bom.py --file board.kicad_pcb --format csv
```

### DFM Check

```bash
# Standard rules (JLCPCB/PCBWay compatible)
python3 scripts/dfm_check.py --file board.kicad_pcb --preset standard

# Budget fab rules (looser tolerances)
python3 scripts/dfm_check.py --file board.kicad_pcb --preset budget

# Advanced fab rules (tighter tolerances)
python3 scripts/dfm_check.py --file board.kicad_pcb --preset advanced

# List all presets
python3 scripts/dfm_check.py --list-presets
```

### Compare Board Versions

```bash
python3 scripts/compare_boards.py --old v1.kicad_pcb --new v2.kicad_pcb --format text
```

## Requirements

- Python 3.10+
- `kiutils` - Pure Python KiCad file parser (no KiCad installation needed)
- Optional: KiCad 7+ with `kicad-cli` in PATH (for DRC and Gerber export)

## License

MIT
