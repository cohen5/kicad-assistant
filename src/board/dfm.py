"""DFM (Design for Manufacturing) checks with fab presets."""

from typing import Optional
from dataclasses import dataclass, field


# Fab presets
DFM_PRESETS = {
    "jlcpcb_standard": {
        "name": "JLCPCB Standard",
        "min_track_width_mm": 0.127,
        "min_track_spacing_mm": 0.127,
        "min_via_drill_mm": 0.3,
        "min_via_diameter_mm": 0.5,
        "min_annular_ring_mm": 0.125,
        "min_hole_spacing_mm": 0.5,
        "min_silk_width_mm": 0.15,
        "min_silk_height_mm": 0.8,
        "min_smd_pad_mm": 0.2,
        "board_thickness_mm": 1.6,
        "max_aspect_ratio": 10,
    },
    "jlcpcb_advanced": {
        "name": "JLCPCB Advanced",
        "min_track_width_mm": 0.09,
        "min_track_spacing_mm": 0.09,
        "min_via_drill_mm": 0.2,
        "min_via_diameter_mm": 0.35,
        "min_annular_ring_mm": 0.075,
        "min_hole_spacing_mm": 0.45,
        "min_silk_width_mm": 0.12,
        "min_silk_height_mm": 0.6,
        "min_smd_pad_mm": 0.15,
        "board_thickness_mm": 1.6,
        "max_aspect_ratio": 12,
    },
    "pcbway_standard": {
        "name": "PCBWay Standard",
        "min_track_width_mm": 0.127,
        "min_track_spacing_mm": 0.127,
        "min_via_drill_mm": 0.3,
        "min_via_diameter_mm": 0.5,
        "min_annular_ring_mm": 0.125,
        "min_hole_spacing_mm": 0.5,
        "min_silk_width_mm": 0.15,
        "min_silk_height_mm": 0.8,
        "min_smd_pad_mm": 0.2,
        "board_thickness_mm": 1.6,
        "max_aspect_ratio": 10,
    },
    "oshpark": {
        "name": "OSH Park",
        "min_track_width_mm": 0.152,
        "min_track_spacing_mm": 0.152,
        "min_via_drill_mm": 0.254,
        "min_via_diameter_mm": 0.508,
        "min_annular_ring_mm": 0.127,
        "min_hole_spacing_mm": 0.381,
        "min_silk_width_mm": 0.15,
        "min_silk_height_mm": 0.8,
        "min_smd_pad_mm": 0.2,
        "board_thickness_mm": 1.6,
        "max_aspect_ratio": 8,
    },
}


@dataclass
class DFMViolation:
    """A single DFM violation."""
    type: str
    severity: str  # "error" or "warning"
    message: str
    location: Optional[tuple[float, float]] = None
    layer: Optional[str] = None
    value: Optional[float] = None
    limit: Optional[float] = None
    fixable: bool = False
    fix_action: Optional[str] = None


@dataclass
class DFMResult:
    """Result of DFM check."""
    file: str
    preset: str
    status: str  # "pass" or "fail"
    violations: list[DFMViolation] = field(default_factory=list)

    @property
    def errors(self) -> list[DFMViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[DFMViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    @property
    def fixable_count(self) -> int:
        return sum(1 for v in self.violations if v.fixable)


def check_dfm(filepath: str, preset: str = "jlcpcb_standard") -> DFMResult:
    """Check a KiCad PCB against DFM rules.

    Args:
        filepath: Path to .kicad_pcb file
        preset: Fab preset name or custom rules dict

    Returns:
        DFMResult with all violations found
    """
    from kiutils.board import Board
    from kiutils.items.brditems import Via, Segment

    if isinstance(preset, str):
        rules = DFM_PRESETS.get(preset, DFM_PRESETS["jlcpcb_standard"])
        preset_name = preset
    else:
        rules = preset
        preset_name = "custom"

    board = Board.from_file(filepath)
    violations = []

    # Separate tracks and vias
    tracks = [t for t in board.traceItems if isinstance(t, Segment)]
    vias = [t for t in board.traceItems if isinstance(t, Via)]

    # Check track widths
    min_track = rules.get("min_track_width_mm", 0)
    for track in tracks:
        if track.width and track.width < min_track:
            violations.append(DFMViolation(
                type="track_width",
                severity="error",
                message=f"Track width {track.width:.4f}mm < minimum {min_track}mm",
                location=(track.start.X, track.start.Y) if track.start else None,
                layer=track.layer,
                value=track.width,
                limit=min_track,
                fixable=True,
                fix_action=f"Widen to {min_track}mm",
            ))

    # Check via drill sizes
    min_via_drill = rules.get("min_via_drill_mm", 0)
    min_annular = rules.get("min_annular_ring_mm", 0)
    board_thickness = rules.get("board_thickness_mm", 1.6)
    max_aspect = rules.get("max_aspect_ratio", 10)

    for via in vias:
        # Drill size
        if via.drill and via.drill < min_via_drill:
            violations.append(DFMViolation(
                type="via_drill",
                severity="error",
                message=f"Via drill {via.drill:.4f}mm < minimum {min_via_drill}mm",
                location=(via.position.X, via.position.Y) if via.position else None,
                value=via.drill,
                limit=min_via_drill,
                fixable=True,
                fix_action=f"Enlarge drill to {min_via_drill}mm",
            ))

        # Annular ring
        if via.drill and via.size:
            annular = (via.size - via.drill) / 2
            if annular < min_annular:
                violations.append(DFMViolation(
                    type="annular_ring",
                    severity="error",
                    message=f"Annular ring {annular:.4f}mm < minimum {min_annular}mm",
                    location=(via.position.X, via.position.Y) if via.position else None,
                    value=annular,
                    limit=min_annular,
                    fixable=True,
                    fix_action=f"Enlarge via pad",
                ))

        # Aspect ratio
        if via.drill:
            aspect = board_thickness / via.drill
            if aspect > max_aspect:
                violations.append(DFMViolation(
                    type="aspect_ratio",
                    severity="warning",
                    message=f"Aspect ratio {aspect:.1f}:1 > maximum {max_aspect}:1",
                    location=(via.position.X, via.position.Y) if via.position else None,
                    value=aspect,
                    limit=max_aspect,
                    fixable=True,
                    fix_action="Enlarge drill diameter",
                ))

    # Check SMD pad sizes
    min_smd = rules.get("min_smd_pad_mm", 0)
    for fp in board.footprints:
        ref = fp.properties.get('Reference', '?')
        for pad in fp.pads:
            pad_type = getattr(pad, 'type', '')
            if pad_type == 'smd' and hasattr(pad, 'size') and pad.size:
                min_dim = min(pad.size.X, pad.size.Y) if hasattr(pad.size, 'X') else 0
                if min_dim > 0 and min_dim < min_smd:
                    violations.append(DFMViolation(
                        type="smd_pad_size",
                        severity="warning",
                        message=f"SMD pad on {ref}: {min_dim:.4f}mm < minimum {min_smd}mm",
                        value=min_dim,
                        limit=min_smd,
                        fixable=False,
                    ))

    status = "fail" if any(v.severity == "error" for v in violations) else "pass"

    return DFMResult(
        file=filepath,
        preset=preset_name,
        status=status,
        violations=violations,
    )
