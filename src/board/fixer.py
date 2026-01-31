"""Auto-fix board issues."""

import os
from typing import Optional
from dataclasses import dataclass, field

from ..utils.backup import create_backup
from .dfm import check_dfm, DFMResult, DFMViolation


@dataclass
class FixAction:
    """A single fix action applied to the board."""
    type: str
    description: str
    location: Optional[tuple[float, float]] = None
    old_value: Optional[float] = None
    new_value: Optional[float] = None
    layer: Optional[str] = None


@dataclass
class FixResult:
    """Result of applying fixes to a board."""
    file: str
    backup_file: str
    fixes_applied: list[FixAction] = field(default_factory=list)
    fixes_skipped: list[str] = field(default_factory=list)
    remaining_issues: int = 0


def fix_board_issues(
    filepath: str,
    preset: str = "jlcpcb_standard",
    fix_types: Optional[list[str]] = None,
    dry_run: bool = False,
) -> FixResult:
    """Automatically fix DFM issues in a board.

    Args:
        filepath: Path to .kicad_pcb file
        preset: Fab preset for DFM rules
        fix_types: List of issue types to fix (None = all fixable)
        dry_run: If True, report fixes without applying

    Returns:
        FixResult with details of applied fixes
    """
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment
    from .dfm import DFM_PRESETS

    # Get rules
    rules = DFM_PRESETS.get(preset, DFM_PRESETS["jlcpcb_standard"])

    # Create backup before modifying
    backup_path = ""
    if not dry_run:
        backup_path = create_backup(filepath)

    # Load board
    board = Board.from_file(filepath)

    fixes_applied = []
    fixes_skipped = []

    # Fix track widths
    if fix_types is None or "track_width" in fix_types:
        min_track = rules.get("min_track_width_mm", 0)
        tracks = [t for t in board.traceItems if isinstance(t, Segment)]

        for track in tracks:
            if track.width and track.width < min_track:
                old_width = track.width
                track.width = min_track
                fixes_applied.append(FixAction(
                    type="track_width",
                    description=f"Widened track from {old_width:.4f}mm to {min_track:.4f}mm",
                    location=(track.start.X, track.start.Y) if track.start else None,
                    old_value=old_width,
                    new_value=min_track,
                    layer=track.layer,
                ))

    # Fix via drill sizes
    if fix_types is None or "via_drill" in fix_types:
        min_drill = rules.get("min_via_drill_mm", 0)
        vias = [t for t in board.traceItems if isinstance(t, Via)]

        for via in vias:
            if via.drill and via.drill < min_drill:
                old_drill = via.drill
                # Also increase pad size proportionally
                if via.size:
                    size_increase = min_drill - old_drill
                    via.size = via.size + size_increase
                via.drill = min_drill
                fixes_applied.append(FixAction(
                    type="via_drill",
                    description=f"Enlarged via drill from {old_drill:.4f}mm to {min_drill:.4f}mm",
                    location=(via.position.X, via.position.Y) if via.position else None,
                    old_value=old_drill,
                    new_value=min_drill,
                ))

    # Fix annular rings
    if fix_types is None or "annular_ring" in fix_types:
        min_annular = rules.get("min_annular_ring_mm", 0)
        vias = [t for t in board.traceItems if isinstance(t, Via)]

        for via in vias:
            if via.drill and via.size:
                current_annular = (via.size - via.drill) / 2
                if current_annular < min_annular:
                    old_size = via.size
                    new_size = via.drill + (2 * min_annular)
                    via.size = new_size
                    fixes_applied.append(FixAction(
                        type="annular_ring",
                        description=f"Enlarged via pad from {old_size:.4f}mm to {new_size:.4f}mm",
                        location=(via.position.X, via.position.Y) if via.position else None,
                        old_value=old_size,
                        new_value=new_size,
                    ))

    # Save modified board
    if not dry_run and fixes_applied:
        board.to_file(filepath)

    # Check remaining issues
    remaining = check_dfm(filepath, preset)

    return FixResult(
        file=filepath,
        backup_file=backup_path,
        fixes_applied=fixes_applied,
        fixes_skipped=fixes_skipped,
        remaining_issues=len(remaining.violations),
    )


def fix_track_widths(filepath: str, min_width_mm: float, dry_run: bool = False) -> FixResult:
    """Fix only track width issues.

    Args:
        filepath: Path to .kicad_pcb file
        min_width_mm: Minimum track width to enforce
        dry_run: If True, report without applying

    Returns:
        FixResult
    """
    custom_preset = {"min_track_width_mm": min_width_mm}
    return fix_board_issues(
        filepath,
        preset=custom_preset,
        fix_types=["track_width"],
        dry_run=dry_run,
    )


def fix_via_sizes(filepath: str, min_drill_mm: float, min_annular_mm: float, dry_run: bool = False) -> FixResult:
    """Fix only via size issues.

    Args:
        filepath: Path to .kicad_pcb file
        min_drill_mm: Minimum via drill diameter
        min_annular_mm: Minimum annular ring width
        dry_run: If True, report without applying

    Returns:
        FixResult
    """
    custom_preset = {
        "min_via_drill_mm": min_drill_mm,
        "min_annular_ring_mm": min_annular_mm,
    }
    return fix_board_issues(
        filepath,
        preset=custom_preset,
        fix_types=["via_drill", "annular_ring"],
        dry_run=dry_run,
    )
