"""Geometry utilities for PCB analysis."""

import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class Point:
    """2D point."""
    x: float
    y: float

    def __iter__(self):
        yield self.x
        yield self.y


def distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Check if a point is inside a polygon using ray casting.

    Args:
        point: (x, y) tuple
        polygon: List of (x, y) vertices

    Returns:
        True if point is inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


def get_board_outline(board) -> list[tuple[float, float]]:
    """Extract board outline from Edge.Cuts layer.

    Args:
        board: kiutils Board object

    Returns:
        List of (x, y) points forming the board outline
    """
    points = []

    for item in board.graphicItems:
        if hasattr(item, 'layer') and item.layer == 'Edge.Cuts':
            if hasattr(item, 'start') and item.start:
                points.append((item.start.X, item.start.Y))
            if hasattr(item, 'end') and item.end:
                points.append((item.end.X, item.end.Y))

    if not points:
        return []

    # Sort points to form a polygon (simple convex hull approximation)
    # For complex outlines, this is simplified
    if len(points) < 3:
        return points

    # Find centroid
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)

    # Sort by angle from centroid
    def angle_from_center(p):
        return math.atan2(p[1] - cy, p[0] - cx)

    # Remove duplicates
    unique_points = list(set(points))
    sorted_points = sorted(unique_points, key=angle_from_center)

    return sorted_points


def get_bounding_box(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Get bounding box of a set of points.

    Returns:
        (min_x, min_y, max_x, max_y)
    """
    if not points:
        return (0, 0, 0, 0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return (min(xs), min(ys), max(xs), max(ys))


def generate_grid(outline: list[tuple[float, float]], spacing: float) -> list[tuple[float, float]]:
    """Generate a grid of points within a polygon outline.

    Args:
        outline: Polygon vertices
        spacing: Grid spacing in mm

    Returns:
        List of (x, y) grid points inside the outline
    """
    if not outline or len(outline) < 3:
        return []

    min_x, min_y, max_x, max_y = get_bounding_box(outline)

    # Add margin
    margin = spacing
    min_x += margin
    min_y += margin
    max_x -= margin
    max_y -= margin

    points = []
    x = min_x
    while x <= max_x:
        y = min_y
        while y <= max_y:
            if point_in_polygon((x, y), outline):
                points.append((x, y))
            y += spacing
        x += spacing

    return points
