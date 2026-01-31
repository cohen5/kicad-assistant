#!/usr/bin/env python3
"""
KiCad MCP Server - Python implementation

Run with: python -m kicad_assistant.mcp_server
Or after pip install: kicad-mcp
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our modules
from kicad_assistant.board.analyzer import analyze_board
from kicad_assistant.board.dfm import check_dfm, DFM_PRESETS
from kicad_assistant.board.fixer import fix_board_issues
from kicad_assistant.board.layers import add_power_plane, recommend_stackup
from kicad_assistant.board.zones import add_stitching_vias, add_thermal_vias
from kicad_assistant.schematic.analyzer import analyze_schematic
from kicad_assistant.schematic.erc import check_erc
from kicad_assistant.project.bom import export_bom
from kicad_assistant.project.loader import find_project_files


# Tool definitions
TOOLS = [
    Tool(
        name="analyze_board",
        description="Analyze a KiCad PCB file. Returns dimensions, track/via counts, component breakdown, layer usage.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="analyze_schematic",
        description="Analyze a KiCad schematic file. Returns symbol counts, wire counts, hierarchical sheet info.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_sch file"},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="check_dfm",
        description="Check PCB against Design for Manufacturing rules (JLCPCB, PCBWay, OSHPark).",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "preset": {
                    "type": "string",
                    "enum": ["jlcpcb_standard", "jlcpcb_advanced", "pcbway_standard", "oshpark"],
                    "default": "jlcpcb_standard",
                    "description": "Fab preset",
                },
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="check_erc",
        description="Run Electrical Rule Check on schematic. Checks duplicate refs, missing values.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_sch file"},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="fix_board_issues",
        description="Auto-fix DFM issues: widen tracks, enlarge vias, fix annular rings. Creates backup.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "preset": {
                    "type": "string",
                    "enum": ["jlcpcb_standard", "jlcpcb_advanced", "pcbway_standard", "oshpark"],
                    "default": "jlcpcb_standard",
                },
                "dry_run": {"type": "boolean", "default": False, "description": "Report without applying"},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="add_power_plane",
        description="Add power/ground plane (copper pour) on a layer.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "layer": {"type": "string", "description": "Layer name (e.g., 'In1.Cu')"},
                "net_name": {"type": "string", "description": "Net name (e.g., 'GND', '+3V3')"},
                "clearance_mm": {"type": "number", "default": 0.3},
            },
            "required": ["filepath", "layer", "net_name"],
        },
    ),
    Tool(
        name="add_stitching_vias",
        description="Add ground stitching vias across the board for EMC.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "net_name": {"type": "string", "default": "GND"},
                "spacing_mm": {"type": "number", "default": 5.0},
                "drill_mm": {"type": "number", "default": 0.3},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="add_thermal_vias",
        description="Add thermal vias under a component's thermal pad.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "component_ref": {"type": "string", "description": "Component reference (e.g., 'U1')"},
                "net_name": {"type": "string", "default": "GND"},
                "count": {"type": "integer", "default": 4},
            },
            "required": ["filepath", "component_ref"],
        },
    ),
    Tool(
        name="recommend_stackup",
        description="Analyze board and recommend layer stackup (2/4/6 layers).",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="export_bom",
        description="Export Bill of Materials from PCB.",
        inputSchema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to .kicad_pcb file"},
                "include_all": {"type": "boolean", "default": False},
            },
            "required": ["filepath"],
        },
    ),
    Tool(
        name="find_project_files",
        description="Find KiCad project files in a directory.",
        inputSchema={
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory to search"},
            },
            "required": ["directory"],
        },
    ),
]


def dataclass_to_dict(obj: Any) -> Any:
    """Convert dataclass to dict recursively."""
    from dataclasses import is_dataclass, asdict

    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    return obj


async def handle_tool_call(name: str, arguments: dict) -> str:
    """Execute a tool and return JSON result."""
    try:
        if name == "analyze_board":
            result = analyze_board(arguments["filepath"])
        elif name == "analyze_schematic":
            result = analyze_schematic(arguments["filepath"])
        elif name == "check_dfm":
            result = check_dfm(
                arguments["filepath"],
                arguments.get("preset", "jlcpcb_standard"),
            )
        elif name == "check_erc":
            result = check_erc(arguments["filepath"])
        elif name == "fix_board_issues":
            result = fix_board_issues(
                arguments["filepath"],
                arguments.get("preset", "jlcpcb_standard"),
                dry_run=arguments.get("dry_run", False),
            )
        elif name == "add_power_plane":
            result = add_power_plane(
                arguments["filepath"],
                arguments["layer"],
                arguments["net_name"],
                arguments.get("clearance_mm", 0.3),
            )
        elif name == "add_stitching_vias":
            result = add_stitching_vias(
                arguments["filepath"],
                arguments.get("net_name", "GND"),
                arguments.get("spacing_mm", 5.0),
                arguments.get("drill_mm", 0.3),
            )
        elif name == "add_thermal_vias":
            result = add_thermal_vias(
                arguments["filepath"],
                arguments["component_ref"],
                arguments.get("net_name", "GND"),
                arguments.get("count", 4),
            )
        elif name == "recommend_stackup":
            result = recommend_stackup(arguments["filepath"])
        elif name == "export_bom":
            result = export_bom(
                arguments["filepath"],
                arguments.get("include_all", False),
            )
        elif name == "find_project_files":
            result = find_project_files(arguments["directory"])
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

        return json.dumps(dataclass_to_dict(result), indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})


async def main():
    """Run the MCP server."""
    server = Server("kicad-assistant")

    @server.list_tools()
    async def list_tools():
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        result = await handle_tool_call(name, arguments)
        return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main_sync():
    """Synchronous entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
