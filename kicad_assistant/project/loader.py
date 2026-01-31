"""Project loader - find and load KiCad project files."""

import os
import json
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class KiCadProject:
    """Represents a KiCad project."""
    project_file: str
    directory: str
    name: str
    board_file: Optional[str] = None
    schematic_files: list[str] = field(default_factory=list)
    library_files: list[str] = field(default_factory=list)


def load_project(filepath: str) -> KiCadProject:
    """Load a KiCad project from .kicad_pro file.

    Args:
        filepath: Path to .kicad_pro file

    Returns:
        KiCadProject with file paths
    """
    if not filepath.endswith(".kicad_pro"):
        raise ValueError("Expected .kicad_pro file")

    directory = os.path.dirname(filepath) or "."
    name = os.path.basename(filepath).replace(".kicad_pro", "")

    # Find associated files
    board_file = None
    schematic_files = []
    library_files = []

    for f in os.listdir(directory):
        full_path = os.path.join(directory, f)

        if f.endswith(".kicad_pcb"):
            board_file = full_path
        elif f.endswith(".kicad_sch"):
            schematic_files.append(full_path)
        elif f.endswith(".kicad_sym") or f.endswith(".kicad_mod"):
            library_files.append(full_path)

    return KiCadProject(
        project_file=filepath,
        directory=directory,
        name=name,
        board_file=board_file,
        schematic_files=schematic_files,
        library_files=library_files,
    )


def find_project_files(directory: str) -> dict:
    """Find KiCad project files in a directory.

    Args:
        directory: Directory to search

    Returns:
        Dict with file paths by type
    """
    files = {
        "project": None,
        "board": None,
        "schematics": [],
        "libraries": [],
    }

    for f in os.listdir(directory):
        full_path = os.path.join(directory, f)

        if f.endswith(".kicad_pro"):
            files["project"] = full_path
        elif f.endswith(".kicad_pcb"):
            files["board"] = full_path
        elif f.endswith(".kicad_sch"):
            files["schematics"].append(full_path)
        elif f.endswith(".kicad_sym") or f.endswith(".kicad_mod"):
            files["libraries"].append(full_path)

    return files


def find_kicad_file(path: str) -> Optional[str]:
    """Find a KiCad file from path (handles directories).

    Args:
        path: File or directory path

    Returns:
        Path to .kicad_pcb or .kicad_sch file
    """
    if os.path.isfile(path):
        return path

    if os.path.isdir(path):
        # Look for board first, then schematic
        for f in os.listdir(path):
            if f.endswith(".kicad_pcb"):
                return os.path.join(path, f)

        for f in os.listdir(path):
            if f.endswith(".kicad_sch"):
                return os.path.join(path, f)

    return None
