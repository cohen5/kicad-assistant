"""OSH Park fabrication presets."""

OSHPARK = {
    "name": "OSH Park",
    "description": "OSH Park (purple boards) capabilities",
    "min_track_width_mm": 0.152,      # 6 mil
    "min_track_spacing_mm": 0.152,
    "min_via_drill_mm": 0.254,        # 10 mil
    "min_via_diameter_mm": 0.508,     # 20 mil
    "min_annular_ring_mm": 0.127,     # 5 mil
    "min_hole_spacing_mm": 0.381,
    "min_silk_width_mm": 0.15,
    "min_silk_height_mm": 0.8,
    "min_smd_pad_mm": 0.2,
    "min_drill_size_mm": 0.254,
    "board_thickness_mm": 1.6,
    "max_aspect_ratio": 8,
    "supported_layers": [2, 4],
    "min_board_size_mm": [5, 5],
    "max_board_size_mm": [152.4, 152.4],  # 6 inches
    "copper_weights_oz": [1, 2],
    "surface_finishes": ["ENIG"],
    "solder_mask_colors": ["purple"],
    "silkscreen_color": "white",
    "notes": "OSH Park uses ENIG finish with distinctive purple soldermask",
}
