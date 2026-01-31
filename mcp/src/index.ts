#!/usr/bin/env node
/**
 * KiCad MCP Server
 *
 * Provides AI assistants with tools for analyzing, checking, and modifying KiCad PCB designs.
 * Supports DFM validation, power plane management, auto-fixing, and more.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Python module is in ../../src relative to dist/index.js
const SRC_DIR = path.resolve(__dirname, "../../src");

// Tool definitions
const TOOLS = [
  // Analysis tools
  {
    name: "analyze_board",
    description: "Analyze a KiCad PCB file. Returns dimensions, track/via counts, component breakdown, layer usage, and statistics.",
    module: "board.analyzer",
    function: "analyze_board",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
      },
      required: ["filepath"],
    },
  },
  {
    name: "analyze_schematic",
    description: "Analyze a KiCad schematic file. Returns symbol counts, wire counts, hierarchical sheet info.",
    module: "schematic.analyzer",
    function: "analyze_schematic",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_sch file",
        },
      },
      required: ["filepath"],
    },
  },

  // DFM/ERC checks
  {
    name: "check_dfm",
    description: "Check PCB against Design for Manufacturing rules. Validates track widths, via sizes, clearances against fab capabilities (JLCPCB, PCBWay, OSHPark).",
    module: "board.dfm",
    function: "check_dfm",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        preset: {
          type: "string",
          enum: ["jlcpcb_standard", "jlcpcb_advanced", "pcbway_standard", "oshpark"],
          default: "jlcpcb_standard",
          description: "Fab preset to check against",
        },
      },
      required: ["filepath"],
    },
  },
  {
    name: "check_erc",
    description: "Run Electrical Rule Check on a schematic. Checks for duplicate references, missing values, unconnected pins.",
    module: "schematic.erc",
    function: "check_erc",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_sch file",
        },
      },
      required: ["filepath"],
    },
  },

  // Auto-fix tools
  {
    name: "fix_board_issues",
    description: "Automatically fix DFM issues in a PCB. Widens narrow tracks, enlarges small vias, fixes annular rings. Creates backup before modifying.",
    module: "board.fixer",
    function: "fix_board_issues",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        preset: {
          type: "string",
          enum: ["jlcpcb_standard", "jlcpcb_advanced", "pcbway_standard", "oshpark"],
          default: "jlcpcb_standard",
          description: "Fab preset for DFM rules",
        },
        dry_run: {
          type: "boolean",
          default: false,
          description: "If true, report fixes without applying",
        },
      },
      required: ["filepath"],
    },
  },

  // Layer and power plane management
  {
    name: "add_power_plane",
    description: "Add a power or ground plane to a layer. Creates a zone (copper pour) covering the board area.",
    module: "board.layers",
    function: "add_power_plane",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        layer: {
          type: "string",
          description: "Layer name (e.g., 'In1.Cu', 'In2.Cu', 'B.Cu')",
        },
        net_name: {
          type: "string",
          description: "Net name for the plane (e.g., 'GND', '+3V3', 'VCC')",
        },
        clearance_mm: {
          type: "number",
          default: 0.3,
          description: "Clearance around other copper in mm",
        },
      },
      required: ["filepath", "layer", "net_name"],
    },
  },
  {
    name: "add_stitching_vias",
    description: "Add ground stitching vias across the board. Connects ground planes on different layers for better EMC.",
    module: "board.zones",
    function: "add_stitching_vias",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        net_name: {
          type: "string",
          default: "GND",
          description: "Net for the vias (usually 'GND')",
        },
        spacing_mm: {
          type: "number",
          default: 5.0,
          description: "Grid spacing between vias in mm",
        },
        drill_mm: {
          type: "number",
          default: 0.3,
          description: "Via drill diameter in mm",
        },
      },
      required: ["filepath"],
    },
  },
  {
    name: "add_thermal_vias",
    description: "Add thermal vias under a component's thermal pad. Improves heat dissipation to inner/bottom layers.",
    module: "board.zones",
    function: "add_thermal_vias",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        component_ref: {
          type: "string",
          description: "Component reference (e.g., 'U1', 'U3')",
        },
        net_name: {
          type: "string",
          default: "GND",
          description: "Net for the vias",
        },
        count: {
          type: "integer",
          default: 4,
          description: "Number of thermal vias to add",
        },
      },
      required: ["filepath", "component_ref"],
    },
  },
  {
    name: "recommend_stackup",
    description: "Analyze board and recommend a layer stackup. Suggests 2/4/6 layer configuration based on complexity and power nets.",
    module: "board.layers",
    function: "recommend_stackup",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
      },
      required: ["filepath"],
    },
  },

  // BOM export
  {
    name: "export_bom",
    description: "Export Bill of Materials from a PCB. Groups components by value and footprint.",
    module: "project.bom",
    function: "export_bom",
    inputSchema: {
      type: "object" as const,
      properties: {
        filepath: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        include_all: {
          type: "boolean",
          default: false,
          description: "Include fiducials, test points, mounting holes",
        },
      },
      required: ["filepath"],
    },
  },

  // Project loader
  {
    name: "find_project_files",
    description: "Find KiCad project files in a directory. Returns paths to board, schematics, and libraries.",
    module: "project.loader",
    function: "find_project_files",
    inputSchema: {
      type: "object" as const,
      properties: {
        directory: {
          type: "string",
          description: "Directory to search for KiCad files",
        },
      },
      required: ["directory"],
    },
  },
];

/**
 * Execute a Python function from the src module
 */
async function callPython(
  module: string,
  func: string,
  args: Record<string, unknown>
): Promise<string> {
  return new Promise((resolve, reject) => {
    // Build Python code to call the function
    const argsJson = JSON.stringify(args);
    const pythonCode = `
import sys
import json
sys.path.insert(0, ${JSON.stringify(SRC_DIR)})
sys.path.insert(0, ${JSON.stringify(path.resolve(SRC_DIR, ".."))})

from src.${module} import ${func}
from dataclasses import asdict, is_dataclass

args = json.loads('''${argsJson}''')
result = ${func}(**args)

# Convert dataclass to dict if needed
if is_dataclass(result) and not isinstance(result, type):
    result = asdict(result)
elif isinstance(result, list) and result and is_dataclass(result[0]):
    result = [asdict(r) for r in result]

print(json.dumps(result, indent=2, default=str))
`;

    const proc = spawn("python3", ["-c", pythonCode], {
      stdio: ["pipe", "pipe", "pipe"],
      cwd: path.resolve(SRC_DIR, ".."),
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        const errorMsg = stderr || stdout || `Process exited with code ${code}`;
        reject(new Error(errorMsg));
      }
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

/**
 * Main entry point
 */
async function main() {
  const server = new Server(
    {
      name: "kicad-assistant",
      version: "2.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register tool list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: TOOLS.map((tool) => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      })),
    };
  });

  // Register tool call handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    const tool = TOOLS.find((t) => t.name === name);
    if (!tool) {
      return {
        content: [
          {
            type: "text",
            text: `Unknown tool: ${name}`,
          },
        ],
        isError: true,
      };
    }

    try {
      const result = await callPython(
        tool.module,
        tool.function,
        args as Record<string, unknown>
      );
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: [
          {
            type: "text",
            text: `Error: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  });

  // Connect to stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error("KiCad Assistant MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
