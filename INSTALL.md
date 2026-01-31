# Quick Install Guide

## Recommended: pip install

```bash
pip install kicad-assistant
```

Then add to `~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "kicad": {
      "command": "kicad-mcp"
    }
  }
}
```

Restart Claude Code. Done.

---

## Alternative: Claude Code Skill

```bash
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant
pip install kiutils
```

Restart Claude Code. Done.

---

## MCP Config Locations

| App | Config File |
|-----|-------------|
| Claude Code | `~/.claude/mcp.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cursor | Cursor settings |

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

## Verify Installation

```bash
# Check CLI
kicad-mcp --help

# Check Python
python -c "from kicad_assistant.board.analyzer import analyze_board; print('OK')"
```

---

## Requirements

- Python 3.10+
- Installed automatically: `kiutils`, `mcp`
