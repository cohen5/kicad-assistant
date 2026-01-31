# Quick Install Guide

## For Claude Code Users (2 commands)

```bash
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant
pip install kiutils
```

Restart Claude Code. Try: "Analyze the PCB at path/to/board.kicad_pcb"

---

## For MCP Users (Claude Desktop, Cursor, etc.)

### Step 1: Clone and build

```bash
git clone https://github.com/cohen5/kicad-assistant ~/kicad-assistant
pip install kiutils
cd ~/kicad-assistant/mcp && npm install && npm run build
```

### Step 2: Add to MCP config

**Claude Code** (`~/.claude/mcp.json`):
```json
{
  "mcpServers": {
    "kicad": {
      "command": "node",
      "args": ["/Users/YOUR_USERNAME/kicad-assistant/mcp/dist/index.js"]
    }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "kicad": {
      "command": "node",
      "args": ["/Users/YOUR_USERNAME/kicad-assistant/mcp/dist/index.js"]
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual username.

### Step 3: Restart

Restart your app. KiCad tools should now be available.

---

## Verify Installation

```bash
python3 ~/kicad-assistant/src/board/analyzer.py
# Or with the example:
cd ~/kicad-assistant
python3 -c "from src.board.analyzer import analyze_board; print(analyze_board('examples/STRF.kicad_pcb'))"
```

---

## Available Tools

| Tool | What it does |
|------|--------------|
| `analyze_board` | Board stats (dimensions, components, routing) |
| `check_dfm` | DFM validation (JLCPCB, PCBWay, OSHPark) |
| `fix_board_issues` | Auto-fix DFM violations |
| `add_power_plane` | Add GND/VCC copper pour |
| `add_stitching_vias` | Add ground stitching |
| `add_thermal_vias` | Add thermal vias under components |
| `recommend_stackup` | Suggest layer configuration |
| `export_bom` | Export BOM (CSV or JSON) |
| `check_erc` | Schematic electrical rule check |

---

## Requirements

- Python 3.10+
- Node.js 18+ (MCP only)
- `pip install kiutils`
- Optional: KiCad 7+ for DRC/Gerber tools
