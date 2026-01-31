# Quick Install Guide for Coworkers

## For Claude Code Users (2 commands)

```bash
# Install as Claude Code skill
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant
pip install kiutils
```

Done. Restart Claude Code and try: "Analyze the PCB at path/to/board.kicad_pcb"

---

## For Claude Desktop / Cursor Users

### Step 1: Clone and build

```bash
git clone https://github.com/cohen5/kicad-assistant ~/kicad-assistant
pip install kiutils
cd ~/kicad-assistant/mcp && npm install && npm run build
```

### Step 2: Add to your config

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

Replace `YOUR_USERNAME` with your actual username.

### Step 3: Restart your app

Restart Claude Desktop or Cursor. The KiCad tools should now be available.

---

## Verify Installation

Test with the included example board:

```bash
python3 ~/kicad-assistant/scripts/analyze_pcb.py \
  --file ~/kicad-assistant/examples/STRF.kicad_pcb --format text
```

You should see board statistics including dimensions, component counts, etc.

---

## Available Tools

| Tool | What it does |
|------|--------------|
| analyze_pcb | Board stats (dimensions, components, routing) |
| export_bom | Bill of Materials (CSV or JSON) |
| check_dfm | DFM validation (JLCPCB, PCBWay rules) |
| compare_boards | Diff two PCB versions |
| run_drc | KiCad DRC (requires kicad-cli) |
| generate_gerbers | Export Gerbers (requires kicad-cli) |

---

## Requirements

- Python 3.10+
- Node.js 18+ (MCP only)
- `pip install kiutils`
- Optional: KiCad 7+ for DRC/Gerber tools
