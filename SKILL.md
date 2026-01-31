---
name: kicad-assistant
description: AI-powered design review and repair for KiCad PCB projects - analyze boards, check DFM, auto-fix issues, manage power planes
metadata: {"requires":{"bins":["python3"],"packages":["kicad-assistant"]},"os":["darwin","linux","windows"]}
---

# KiCad Design Assistant

AI-powered design review and repair tool for KiCad PCB projects. Analyzes boards, checks manufacturing rules, auto-fixes issues, and manages power planes.

Use this skill when the user asks about:
- PCB design analysis, DFM checks, or design rule violations
- Auto-fixing DFM issues (track widths, via sizes, annular rings)
- Adding power planes, ground planes, or configuring layer stackups
- Adding stitching vias or thermal vias
- BOM (Bill of Materials) export
- Comparing board versions
- Gerber generation or manufacturing file export

## Prerequisites

```bash
pip install kicad-assistant
```

## Capabilities

### Analysis
```python
from kicad_assistant.board.analyzer import analyze_board
result = analyze_board("/path/to/board.kicad_pcb")
# Returns: dimensions, track/via counts, component stats, layers
```

### DFM Check
```python
from kicad_assistant.board.dfm import check_dfm
result = check_dfm("/path/to/board.kicad_pcb", preset="jlcpcb_standard")
# Returns: violations with fixable flag
```

Presets: `jlcpcb_standard`, `jlcpcb_advanced`, `pcbway_standard`, `oshpark`

### Auto-Fix Issues
```python
from kicad_assistant.board.fixer import fix_board_issues
result = fix_board_issues("/path/to/board.kicad_pcb", preset="jlcpcb_standard")
# Creates backup, widens tracks, enlarges vias, fixes annular rings
```

### Add Power Plane
```python
from kicad_assistant.board.layers import add_power_plane
add_power_plane("/path/to/board.kicad_pcb", layer="In1.Cu", net_name="GND")
```

### Add Stitching Vias
```python
from kicad_assistant.board.zones import add_stitching_vias
add_stitching_vias("/path/to/board.kicad_pcb", net_name="GND", spacing_mm=5.0)
```

### Add Thermal Vias
```python
from kicad_assistant.board.zones import add_thermal_vias
add_thermal_vias("/path/to/board.kicad_pcb", component_ref="U1", count=4)
```

### Recommend Stackup
```python
from kicad_assistant.board.layers import recommend_stackup
result = recommend_stackup("/path/to/board.kicad_pcb")
# Returns: recommended 2/4/6 layer configuration
```

### Export BOM
```python
from kicad_assistant.project.bom import export_bom, format_bom_csv
bom = export_bom("/path/to/board.kicad_pcb")
print(format_bom_csv(bom))
```

## DFM Presets

| Preset | Min Track | Min Via Drill | Use Case |
|--------|-----------|---------------|----------|
| `jlcpcb_standard` | 0.127mm (5mil) | 0.3mm | JLCPCB standard |
| `jlcpcb_advanced` | 0.09mm (3.5mil) | 0.2mm | JLCPCB HDI |
| `pcbway_standard` | 0.127mm | 0.3mm | PCBWay |
| `oshpark` | 0.152mm (6mil) | 0.254mm | OSH Park |

## Response Guidelines

- Always create backups before modifying files
- Confirm file paths exist before operations
- For DFM issues, explain what they mean and offer to auto-fix
- When adding power planes, ask about net names (GND, VCC, +3V3)
- For stackup recommendations, explain the tradeoffs
- Present results clearly with counts and summaries
