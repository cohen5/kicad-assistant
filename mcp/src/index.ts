#!/usr/bin/env node
/**
 * KiCad MCP Server
 *
 * A thin wrapper that exposes KiCad PCB analysis tools via the Model Context Protocol.
 * All functionality is delegated to Python scripts in the scripts/ directory.
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

// Scripts are in ../../scripts relative to dist/index.js
const SCRIPTS_DIR = path.resolve(__dirname, "../../scripts");

// Tool definitions with their corresponding Python scripts
const TOOLS = [
  {
    name: "analyze_pcb",
    description: "Analyze a KiCad PCB file and return statistics including dimensions, track/via counts, component breakdown, and layer usage.",
    script: "analyze_pcb.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        file: {
          type: "string",
          description: "Path to the .kicad_pcb file to analyze",
        },
        format: {
          type: "string",
          enum: ["json", "text"],
          default: "json",
          description: "Output format",
        },
      },
      required: ["file"],
    },
  },
  {
    name: "export_bom",
    description: "Export a Bill of Materials (BOM) from a KiCad PCB file. Groups components by value and footprint.",
    script: "export_bom.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        file: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        format: {
          type: "string",
          enum: ["csv", "json"],
          default: "csv",
          description: "Output format",
        },
        include_all: {
          type: "boolean",
          default: false,
          description: "Include fiducials, test points, and mounting holes",
        },
      },
      required: ["file"],
    },
  },
  {
    name: "check_dfm",
    description: "Check a KiCad PCB against Design for Manufacturing (DFM) rules. Validates track widths, via sizes, annular rings, and pad dimensions.",
    script: "dfm_check.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        file: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        preset: {
          type: "string",
          enum: ["standard", "budget", "advanced"],
          default: "standard",
          description: "DFM rule preset (standard=JLCPCB/PCBWay, budget=cheaper fabs, advanced=premium fabs)",
        },
        format: {
          type: "string",
          enum: ["json", "text"],
          default: "json",
          description: "Output format",
        },
      },
      required: ["file"],
    },
  },
  {
    name: "compare_boards",
    description: "Compare two KiCad PCB versions and summarize changes including added/removed components, routing changes, and layer modifications.",
    script: "compare_boards.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        old: {
          type: "string",
          description: "Path to the old .kicad_pcb file",
        },
        new: {
          type: "string",
          description: "Path to the new .kicad_pcb file",
        },
        format: {
          type: "string",
          enum: ["json", "text"],
          default: "json",
          description: "Output format",
        },
      },
      required: ["old", "new"],
    },
  },
  {
    name: "run_drc",
    description: "Run Design Rule Check (DRC) on a KiCad PCB using kicad-cli. Requires KiCad 7+ installed.",
    script: "run_drc.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        file: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        output_dir: {
          type: "string",
          description: "Optional directory to save DRC report",
        },
        format: {
          type: "string",
          enum: ["json", "text"],
          default: "json",
          description: "Output format",
        },
      },
      required: ["file"],
    },
  },
  {
    name: "generate_gerbers",
    description: "Generate Gerber and drill files for PCB manufacturing using kicad-cli. Requires KiCad 7+ installed.",
    script: "generate_gerbers.py",
    inputSchema: {
      type: "object" as const,
      properties: {
        file: {
          type: "string",
          description: "Path to the .kicad_pcb file",
        },
        output: {
          type: "string",
          description: "Output directory for Gerber files",
        },
        format: {
          type: "string",
          enum: ["json", "text"],
          default: "json",
          description: "Output format",
        },
      },
      required: ["file", "output"],
    },
  },
];

/**
 * Execute a Python script and return its output
 */
async function callPython(
  script: string,
  args: Record<string, unknown>
): Promise<string> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(SCRIPTS_DIR, script);

    // Convert args to CLI arguments
    const cliArgs: string[] = [];
    for (const [key, value] of Object.entries(args)) {
      if (value === undefined || value === null) continue;

      // Convert snake_case to kebab-case for CLI
      const cliKey = key.replace(/_/g, "-");

      if (typeof value === "boolean") {
        if (value) {
          cliArgs.push(`--${cliKey}`);
        }
      } else {
        cliArgs.push(`--${cliKey}`, String(value));
      }
    }

    const proc = spawn("python3", [scriptPath, ...cliArgs], {
      stdio: ["pipe", "pipe", "pipe"],
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
        // Include stderr in the error for debugging
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
      name: "kicad-mcp",
      version: "1.0.0",
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
      const result = await callPython(tool.script, args as Record<string, unknown>);
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

  console.error("KiCad MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
