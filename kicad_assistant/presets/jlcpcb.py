"""JLCPCB fabrication presets."""

JLCPCB_STANDARD = {
    "name": "JLCPCB Standard",
    "description": "Standard PCB capabilities at JLCPCB",
    "min_track_width_mm": 0.127,      # 5 mil
    "min_track_spacing_mm": 0.127,    # 5 mil
    "min_via_drill_mm": 0.3,
    "min_via_diameter_mm": 0.5,
    "min_annular_ring_mm": 0.125,
    "min_hole_spacing_mm": 0.5,
    "min_silk_width_mm": 0.15,
    "min_silk_height_mm": 0.8,
    "min_smd_pad_mm": 0.2,
    "min_drill_size_mm": 0.2,
    "board_thickness_mm": 1.6,
    "max_aspect_ratio": 10,
    "supported_layers": [1, 2, 4, 6, 8],
    "min_board_size_mm": [10, 10],
    "max_board_size_mm": [400, 500],
    "copper_weights_oz": [1, 2],
    "surface_finishes": ["HASL", "HASL-LF", "ENIG"],
    "solder_mask_colors": ["green", "red", "yellow", "blue", "white", "black", "purple"],
}

JLCPCB_ADVANCED = {
    "name": "JLCPCB Advanced",
    "description": "Advanced/high-density PCB capabilities at JLCPCB",
    "min_track_width_mm": 0.09,       # 3.5 mil
    "min_track_spacing_mm": 0.09,
    "min_via_drill_mm": 0.2,
    "min_via_diameter_mm": 0.35,
    "min_annular_ring_mm": 0.075,
    "min_hole_spacing_mm": 0.45,
    "min_silk_width_mm": 0.12,
    "min_silk_height_mm": 0.6,
    "min_smd_pad_mm": 0.15,
    "min_drill_size_mm": 0.15,
    "board_thickness_mm": 1.6,
    "max_aspect_ratio": 12,
    "supported_layers": [4, 6, 8, 10, 12],
    "min_board_size_mm": [10, 10],
    "max_board_size_mm": [400, 500],
    "copper_weights_oz": [0.5, 1, 2],
    "surface_finishes": ["ENIG", "OSP", "Immersion Silver"],
    "solder_mask_colors": ["green", "black", "matte green", "matte black"],
}
