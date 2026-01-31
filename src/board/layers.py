"""Layer management - configure layer types, stackup, power planes."""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class LayerType(Enum):
    """Layer type classification."""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    MIXED = "mixed"


# Standard layer stackups
STACKUPS = {
    "2layer": {
        "layers": ["F.Cu", "B.Cu"],
        "types": [LayerType.SIGNAL, LayerType.SIGNAL],
        "thickness_mm": 1.6,
    },
    "4layer_sig_gnd_pwr_sig": {
        "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
        "types": [LayerType.SIGNAL, LayerType.GROUND, LayerType.POWER, LayerType.SIGNAL],
        "thickness_mm": 1.6,
        "description": "Standard 4-layer: Signal-GND-VCC-Signal",
    },
    "4layer_sig_pwr_gnd_sig": {
        "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
        "types": [LayerType.SIGNAL, LayerType.POWER, LayerType.GROUND, LayerType.SIGNAL],
        "thickness_mm": 1.6,
        "description": "Alternative 4-layer: Signal-VCC-GND-Signal",
    },
    "6layer": {
        "layers": ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"],
        "types": [LayerType.SIGNAL, LayerType.GROUND, LayerType.SIGNAL, LayerType.SIGNAL, LayerType.POWER, LayerType.SIGNAL],
        "thickness_mm": 1.6,
        "description": "6-layer: Signal-GND-Signal-Signal-VCC-Signal",
    },
}


@dataclass
class LayerConfig:
    """Configuration for a single layer."""
    name: str
    type: LayerType
    net: Optional[str] = None  # For power/ground planes


def get_copper_layers(filepath: str) -> list[str]:
    """Get list of copper layer names in the board.

    Args:
        filepath: Path to .kicad_pcb file

    Returns:
        List of copper layer names (e.g., ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
    """
    from kiutils.board import Board

    board = Board.from_file(filepath)

    copper_layers = []
    for layer in board.layers:
        name = layer.name if hasattr(layer, 'name') else str(layer)
        layer_type = layer.type if hasattr(layer, 'type') else ""
        if name.endswith(".Cu") or "copper" in str(layer_type).lower():
            copper_layers.append(name)

    return copper_layers


def configure_layer(
    filepath: str,
    layer_name: str,
    layer_type: LayerType,
    net_name: Optional[str] = None,
) -> bool:
    """Configure a layer's type and optionally assign it to a net.

    Args:
        filepath: Path to .kicad_pcb file
        layer_name: Name of layer to configure (e.g., "In1.Cu")
        layer_type: Type to assign
        net_name: Net name for power/ground layers (e.g., "GND", "VCC")

    Returns:
        True if successful
    """
    from kiutils.board import Board
    from ..utils.backup import create_backup

    # Create backup
    create_backup(filepath)

    board = Board.from_file(filepath)

    # Find and update layer
    for layer in board.layers:
        name = layer.name if hasattr(layer, 'name') else str(layer)
        if name == layer_name:
            # Update layer type in KiCad format
            if hasattr(layer, 'type'):
                if layer_type in (LayerType.POWER, LayerType.GROUND):
                    layer.type = "power"
                else:
                    layer.type = "signal"

    # If it's a power/ground layer and net_name given, add a zone
    if layer_type in (LayerType.POWER, LayerType.GROUND) and net_name:
        from .zones import add_power_plane
        add_power_plane(filepath, layer_name, net_name)

    board.to_file(filepath)
    return True


def add_power_plane(
    filepath: str,
    layer: str,
    net_name: str,
    clearance_mm: float = 0.3,
) -> dict:
    """Add a power/ground plane covering the entire board on a layer.

    This creates a zone (copper pour) that fills the board area.

    Args:
        filepath: Path to .kicad_pcb file
        layer: Layer name (e.g., "In1.Cu", "In2.Cu")
        net_name: Net name (e.g., "GND", "+3V3", "VCC")
        clearance_mm: Clearance around other traces

    Returns:
        Dict with zone details
    """
    from .zones import add_zone, get_board_outline_polygon

    outline = get_board_outline_polygon(filepath)
    if not outline:
        raise ValueError("Board has no outline defined on Edge.Cuts")

    return add_zone(
        filepath=filepath,
        layer=layer,
        net_name=net_name,
        outline=outline,
        clearance_mm=clearance_mm,
        priority=0,  # Lowest priority = background plane
        thermal_relief=True,
    )


def recommend_stackup(filepath: str) -> dict:
    """Analyze board and recommend a layer stackup.

    Args:
        filepath: Path to .kicad_pcb file

    Returns:
        Dict with recommended stackup and reasoning
    """
    from .analyzer import analyze_board

    stats = analyze_board(filepath)

    # Count power nets
    power_nets = []
    ground_nets = []

    from kiutils.board import Board
    board = Board.from_file(filepath)

    for net in board.nets:
        name = net.name if hasattr(net, 'name') else str(net)
        name_upper = name.upper()
        if "GND" in name_upper or "GROUND" in name_upper or "VSS" in name_upper:
            ground_nets.append(name)
        elif "VCC" in name_upper or "VDD" in name_upper or "+3V" in name_upper or "+5V" in name_upper or "PWR" in name_upper:
            power_nets.append(name)

    # Determine recommended layer count
    if stats.tracks < 100 and stats.footprints < 30:
        recommended = "2layer"
        reason = "Simple board with few components - 2 layers sufficient"
    elif len(ground_nets) >= 1 and len(power_nets) >= 1:
        recommended = "4layer_sig_gnd_pwr_sig"
        reason = "Multiple power rails detected - 4 layers with dedicated power planes recommended"
    else:
        recommended = "4layer_sig_gnd_pwr_sig"
        reason = "Standard 4-layer recommended for signal integrity"

    return {
        "recommended": recommended,
        "stackup": STACKUPS[recommended],
        "reason": reason,
        "power_nets": power_nets,
        "ground_nets": ground_nets,
    }
