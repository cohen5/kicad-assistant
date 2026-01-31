"""PCBWay fabrication presets."""

PCBWAY_STANDARD = {
    "name": "PCBWay Standard",
    "description": "Standard PCB capabilities at PCBWay",
    "min_track_width_mm": 0.127,      # 5 mil
    "min_track_spacing_mm": 0.127,
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
    "supported_layers": [1, 2, 4, 6, 8, 10],
    "min_board_size_mm": [5, 5],
    "max_board_size_mm": [500, 600],
    "copper_weights_oz": [0.5, 1, 2, 3],
    "surface_finishes": ["HASL", "HASL-LF", "ENIG", "OSP", "Immersion Tin", "Immersion Silver"],
    "solder_mask_colors": ["green", "red", "yellow", "blue", "white", "black", "purple", "matte green", "matte black"],
}
