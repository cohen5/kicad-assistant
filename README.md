# KiCad Assistant

A Claude Code skill for analyzing KiCad PCB files, exporting BOMs, running DFM checks, and comparing board versions.

## What is this?

This is a **skill** for [Claude Code](https://claude.ai/claude-code) (Anthropic's CLI coding assistant). Once installed, Claude can automatically analyze your KiCad PCB files when you ask questions like:

- "Analyze my board at ~/projects/board.kicad_pcb"
- "Export a BOM from this PCB"
- "Check if this board meets JLCPCB manufacturing rules"
- "Compare v1 and v2 of my board"

## Installation

```bash
# 1. Clone to Claude Code skills directory
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant

# 2. Install Python dependency
pip install kiutils
```

That's it. Claude Code will automatically detect the skill.

### Optional: For DRC and Gerber export

Install KiCad 7+ and ensure `kicad-cli` is in your PATH.

## Usage with Claude Code

Just ask naturally in a Claude Code conversation:

```
You: Analyze the PCB at ~/projects/sensor-board.kicad_pcb

Claude: [runs analyze_pcb.py and returns stats]
        Board: 45.2 x 32.1 mm
        Components: 47 (23 capacitors, 12 resistors, 5 ICs...)
        Tracks: 234, Vias: 89
        ...
```

```
You: Does this board meet JLCPCB specs?

Claude: [runs dfm_check.py with standard preset]
        DFM Check: PASS
        No violations found.
```

```
You: Export BOM as CSV

Claude: [runs export_bom.py]
        Reference,Value,Footprint,Quantity
        C1,100nF,0402,12
        ...
```

## Features

| Feature | Description | Requires KiCad? |
|---------|-------------|-----------------|
| **Analyze PCB** | Track/via counts, dimensions, component stats | No |
| **Export BOM** | CSV or JSON bill of materials | No |
| **DFM Check** | Validate against fab rules (JLCPCB, PCBWay) | No |
| **Compare Boards** | Diff two PCB versions | No |
| **Run DRC** | Design rule check | Yes (kicad-cli) |
| **Generate Gerbers** | Export manufacturing files | Yes (kicad-cli) |

## CLI Usage (without Claude)

You can also run the scripts directly:

```bash
# Analyze
python3 ~/.claude/skills/kicad-assistant/scripts/analyze_pcb.py \
  --file board.kicad_pcb --format text

# Export BOM
python3 ~/.claude/skills/kicad-assistant/scripts/export_bom.py \
  --file board.kicad_pcb --format csv

# DFM Check
python3 ~/.claude/skills/kicad-assistant/scripts/dfm_check.py \
  --file board.kicad_pcb --preset standard

# Compare versions
python3 ~/.claude/skills/kicad-assistant/scripts/compare_boards.py \
  --old v1.kicad_pcb --new v2.kicad_pcb
```

## DFM Presets

| Preset | Min Track | Min Via Drill | Use Case |
|--------|-----------|---------------|----------|
| `standard` | 0.127mm (5mil) | 0.3mm | JLCPCB, PCBWay standard |
| `budget` | 0.15mm | 0.3mm | Cheaper fabs |
| `advanced` | 0.09mm (3.5mil) | 0.2mm | Premium fabs |

```bash
python3 scripts/dfm_check.py --list-presets  # See all rules
```

## Requirements

- Python 3.10+
- `kiutils` (pure Python, no KiCad needed)
- Optional: KiCad 7+ for DRC and Gerber export

## Example

An example board (`STRF.kicad_pcb`) is included in the `examples/` folder.

## License

MIT
