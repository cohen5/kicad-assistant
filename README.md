# KiCad Assistant

A Claude Code skill and MCP server for analyzing KiCad PCB files, exporting BOMs, running DFM checks, and comparing board versions.

## What is this?

KiCad Assistant gives AI assistants the ability to analyze your KiCad PCB files. Once installed, you can ask questions like:

- "Analyze my board at ~/projects/board.kicad_pcb"
- "Export a BOM from this PCB"
- "Check if this board meets JLCPCB manufacturing rules"
- "Compare v1 and v2 of my board"

## Installation Options

Choose ONE of the following methods:

### Option 1: Claude Code Skill (Recommended for Claude Code users)

```bash
# 1. Clone to Claude Code skills directory
git clone https://github.com/cohen5/kicad-assistant ~/.claude/skills/kicad-assistant

# 2. Install Python dependency
pip install kiutils
```

That's it. Claude Code will automatically detect the skill.

### Option 2: MCP Server (Works with Claude Code, Claude Desktop, Cursor, etc.)

The MCP server provides the same functionality but works with any MCP-compatible client.

```bash
# 1. Clone the repository
git clone https://github.com/cohen5/kicad-assistant ~/kicad-assistant

# 2. Install dependencies
pip install kiutils
cd ~/kicad-assistant/mcp && npm install && npm run build

# 3. Configure your MCP client (see below)
```

#### MCP Configuration for Claude Code

Add to `~/.claude/mcp.json` (create if it doesn't exist):

```json
{
  "mcpServers": {
    "kicad": {
      "command": "node",
      "args": ["~/kicad-assistant/mcp/dist/index.js"]
    }
  }
}
```

Or for project-specific use, add to `.claude/mcp.json` in your project directory.

#### MCP Configuration for Claude Desktop

Add to your Claude Desktop config (usually `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

#### MCP Configuration for Cursor

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "kicad": {
      "command": "node",
      "args": ["/absolute/path/to/kicad-assistant/mcp/dist/index.js"]
    }
  }
}
```

### Optional: For DRC and Gerber export

Install KiCad 7+ and ensure `kicad-cli` is in your PATH.

## Usage

### With Claude Code (Skill or MCP)

Just ask naturally:

```
You: Analyze the PCB at ~/projects/sensor-board.kicad_pcb

Claude: [runs analyze_pcb and returns stats]
        Board: 45.2 x 32.1 mm
        Components: 47 (23 capacitors, 12 resistors, 5 ICs...)
        Tracks: 234, Vias: 89
        ...
```

```
You: Does this board meet JLCPCB specs?

Claude: [runs dfm_check with standard preset]
        DFM Check: PASS
        No violations found.
```

```
You: Export BOM as CSV

Claude: [runs export_bom]
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

## CLI Usage (without AI)

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

## MCP Tools Reference

When using the MCP server, the following tools are available:

| Tool | Description |
|------|-------------|
| `analyze_pcb` | Analyze PCB statistics (dimensions, components, routing) |
| `export_bom` | Export Bill of Materials |
| `check_dfm` | Validate against manufacturing rules |
| `compare_boards` | Compare two PCB versions |
| `run_drc` | Run KiCad DRC (requires kicad-cli) |
| `generate_gerbers` | Export Gerber files (requires kicad-cli) |

## Requirements

- Python 3.10+
- `kiutils` Python package (pure Python, no KiCad needed)
- Node.js 18+ (for MCP server only)
- Optional: KiCad 7+ for DRC and Gerber export

## Example

An example board (`STRF.kicad_pcb`) is included in the `examples/` folder.

## Troubleshooting

### "kiutils not installed"

Run: `pip install kiutils`

### MCP server not connecting

1. Make sure you built the MCP server: `cd mcp && npm run build`
2. Check the path in your MCP config is absolute
3. Try running directly: `node /path/to/kicad-assistant/mcp/dist/index.js`

### DRC/Gerber commands fail

These require `kicad-cli` from KiCad 7+. Make sure KiCad is installed and `kicad-cli` is in your PATH.

## License

MIT
