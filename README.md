# KiCad Design Assistant

AI-powered design review and repair tool for KiCad PCB projects.

**Features:**
- Analyze PCB boards and schematics
- Check DFM rules for JLCPCB, PCBWay, OSHPark
- Auto-fix issues (track widths, via sizes, annular rings)
- Add power planes and ground stitching vias
- Export BOM (Bill of Materials)
- Works as Claude Code skill AND MCP server

## Installation

### Option 1: pip install (Recommended)

```bash
pip install kicad-assistant
```

Then configure MCP in `~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "kicad": {
      "command": "kicad-mcp"
    }
  }
}
```

### Option 2: Claude Code Skill

```bash
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant
pip install kiutils
```

### Option 3: From source

```bash
git clone https://github.com/cohen5/kicad-assistant
cd kicad-assistant
pip install -e .
```

## Usage Examples

### Analyze a board
```
Analyze the PCB at ~/projects/myboard.kicad_pcb
```

### Check manufacturing rules
```
Check if this board meets JLCPCB specs
Check DFM for PCBWay advanced capabilities
```

### Auto-fix issues
```
Fix all DFM issues in this board
Fix the track widths to meet JLCPCB rules
```

### Add power planes
```
Add a GND plane on layer In1.Cu
Add +3V3 power plane on In2.Cu
```

### Add stitching vias
```
Add ground stitching vias with 5mm spacing
```

### Add thermal vias
```
Add thermal vias under U1
```

### Recommend stackup
```
What layer stackup should I use for this board?
```

### Export BOM
```
Export BOM as CSV
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_board` | Board statistics and structure |
| `analyze_schematic` | Schematic structure |
| `check_dfm` | DFM validation against fab rules |
| `check_erc` | Schematic electrical rule check |
| `fix_board_issues` | Auto-fix DFM violations |
| `add_power_plane` | Create power/ground plane |
| `add_stitching_vias` | Add ground stitching |
| `add_thermal_vias` | Add thermal vias under component |
| `recommend_stackup` | Suggest layer configuration |
| `export_bom` | Export Bill of Materials |
| `find_project_files` | Find KiCad files in directory |

## DFM Presets

| Preset | Min Track | Min Via Drill | Description |
|--------|-----------|---------------|-------------|
| `jlcpcb_standard` | 0.127mm (5mil) | 0.3mm | JLCPCB standard process |
| `jlcpcb_advanced` | 0.09mm (3.5mil) | 0.2mm | JLCPCB HDI process |
| `pcbway_standard` | 0.127mm | 0.3mm | PCBWay standard |
| `oshpark` | 0.152mm (6mil) | 0.254mm | OSH Park (purple boards) |

## Python API

```python
from kicad_assistant.board.analyzer import analyze_board
from kicad_assistant.board.dfm import check_dfm
from kicad_assistant.board.fixer import fix_board_issues

# Analyze
stats = analyze_board("board.kicad_pcb")
print(f"Board: {stats.board_width_mm} x {stats.board_height_mm} mm")

# Check DFM
result = check_dfm("board.kicad_pcb", preset="jlcpcb_standard")
print(f"Status: {result.status}, Errors: {len(result.errors)}")

# Auto-fix
fix_result = fix_board_issues("board.kicad_pcb", preset="jlcpcb_standard")
print(f"Fixed {len(fix_result.fixes_applied)} issues")
```

## Requirements

- Python 3.10+
- Dependencies installed automatically: `kiutils`, `mcp`

## Safety

All file modifications:
1. Create `.bak` backup before changes
2. Validate files after modification
3. Support dry-run mode

## License

MIT License
