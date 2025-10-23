"""Parsing, normalization, and matching utilities for DWG/DXF files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, cast

import ezdxf
import numpy as np
from ezdxf.math import Matrix44, Vec3
from ezdxf.errors import DXFStructureError
from rtree import index
from shapely.geometry import LineString, Point, Polygon

# --- Data Models ---

@dataclass(slots=True)
class ParsedEntity:
    """Lightweight representation of a geometry entity."""
    entity_id: str
    entity_type: str
    vertices: list[tuple[float, float]]

# --- 1. Parsing Step ---

def _extract_vertices(entity) -> list[tuple[float, float]] | None:
    """Extract vertices from a DXF entity."""
    if entity.dxftype() in {"LINE", "XLINE", "RAY"}:
        return [entity.dxf.start.vec2, entity.dxf.end.vec2]
    if entity.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
        return list(entity.points())
    if entity.dxftype() == "CIRCLE":
        return list(entity.vertices(32))
    if entity.dxftype() == "ARC":
        return list(entity.vertices(16))
    if entity.dxftype() == "ELLIPSE":
        return list(entity.vertices(32))
    if entity.dxftype() == "SPLINE":
        return list(entity.flattening(1, 16))
    if hasattr(entity, "vertices"):
        return [v.dxf.location.vec2 for v in entity.vertices]
    return None

def parse_dxf(path: Path) -> list[ParsedEntity]:
    """Parse the given DXF file and return simplified entities."""
    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
    except (DXFStructureError, FileNotFoundError, IOError) as e:
        print(f"Error reading or parsing DXF file {path}: {e}")
        return []

    entities: list[ParsedEntity] = []
    # Explode block references to get their raw geometry
    for entity in msp.query("INSERT"):
        try:
            entity.explode()
        except Exception:
            pass # Some blocks cannot be exploded

    for entity in msp:
        if not hasattr(entity, "dxf"):
            continue

        vertices = _extract_vertices(entity)
        if not vertices:
            continue

        handle = str(entity.dxf.handle)
        entities.append(ParsedEntity(entity_id=handle, entity_type=entity.dxftype(), vertices=vertices))
    return entities

# --- 2. Normalization Step ---

@dataclass(slots=True)
class _GridAxis:
    label: str
    is_vertical: bool
    line: LineString

def _find_grid_axes(entities: list[ParsedEntity], tolerance: float = 1e-3) -> list[_GridAxis]:
    """Identifies grid axes by finding axis labels and matching them to long lines."""
    # Find text labels within circles on axis-related layers
    label_re = re.compile(r"^[A-Z0-9']+$")
    texts = [e for e in entities if e.entity_type == "TEXT" and e.entity_type == "AXIS_TEXT" and label_re.match(e.entity_id)]
    circles = [e for e in entities if e.entity_type == "CIRCLE" and e.entity_type == "AXIS_TEXT"]
    
    axis_labels = []
    for text in texts:
        text_center = Point(text.vertices[0])
        for circle in circles:
            circle_center = Point(np.mean(circle.vertices, axis=0))
            if text_center.distance(circle_center) < np.linalg.norm(np.subtract(circle.vertices[0], circle.vertices[1])) / 2:
                axis_labels.append((text.entity_id, text_center))
                break

    # Find long, straight, horizontal/vertical lines
    lines = [e for e in entities if e.entity_type in {"LINE", "LWPOLYLINE"}]
    candidate_lines = []
    for line in lines:
        if len(line.vertices) < 2:
            continue
        p1, p2 = Vec3(line.vertices[0]), Vec3(line.vertices[-1])
        is_vertical = abs(p1.x - p2.x) < tolerance and abs(p1.y - p2.y) > tolerance
        is_horizontal = abs(p1.y - p2.y) < tolerance and abs(p1.x - p2.x) > tolerance
        if is_vertical or is_horizontal:
            candidate_lines.append((LineString(line.vertices), is_vertical))

    # Match labels to lines
    grid_axes = []
    for label, center in axis_labels:
        best_match = None
        min_dist = float('inf')
        for line, is_vertical in candidate_lines:
            dist = line.distance(center)
            if dist < min_dist:
                min_dist = dist
                best_match = (line, is_vertical)
        if best_match and min_dist < 500: # 500mm tolerance for matching label to line
            grid_axes.append(_GridAxis(label=label, is_vertical=best_match[1], line=best_match[0]))

    return grid_axes

def normalize_entities_by_grid(revised_entities: list[ParsedEntity], original_entities: list[ParsedEntity]) -> list[ParsedEntity]:
    """Aligns the revised entities to the original entities based on identified grid axes."""
    # 1. Find grid systems in both drawings
    original_axes = _find_grid_axes(original_entities)
    revised_axes = _find_grid_axes(revised_entities)

    if not original_axes or not revised_axes:
        return revised_entities # Cannot normalize if grids aren't found

    # 2. Find two common reference points (intersections of first/last axes)
    def get_ref_points(axes: list[_GridAxis]):
        h_axes = sorted([a for a in axes if not a.is_vertical], key=lambda a: a.line.bounds[1])
        v_axes = sorted([a for a in axes if a.is_vertical], key=lambda a: a.line.bounds[0])
        if not h_axes or not v_axes or len(h_axes) < 2 or len(v_axes) < 2:
            return None, None
        p1 = h_axes[0].line.intersection(v_axes[0].line)
        p2 = h_axes[-1].line.intersection(v_axes[-1].line)
        return p1, p2

    o_p1, o_p2 = get_ref_points(original_axes)
    r_p1, r_p2 = get_ref_points(revised_axes)

    if not all([o_p1, o_p2, r_p1, r_p2]):
        return revised_entities # Not enough common axes found

    # 3. Calculate transformation
    o_vec = Vec3(o_p2.x - o_p1.x, o_p2.y - o_p1.y, 0)
    r_vec = Vec3(r_p2.x - r_p1.x, r_p2.y - r_p1.y, 0)

    if r_vec.magnitude == 0:
        return revised_entities

    scale = o_vec.magnitude / r_vec.magnitude
    angle = o_vec.angle_between(r_vec)
    
    # Build transformation matrix: scale -> rotate -> translate
    transform = (
        Matrix44.scale(scale, scale, scale) 
        @ Matrix44.z_rotate(angle)
        @ Matrix44.translate(-r_p1.x, -r_p1.y, 0)
        @ Matrix44.translate(o_p1.x, o_p1.y, 0)
    )

    # 4. Apply transformation to all revised entities
    transformed_revised: list[ParsedEntity] = []
    for entity in revised_entities:
        new_vertices = [transform.transform(Vec3(v[0], v[1], 0)).vec2 for v in entity.vertices]
        transformed_revised.append(ParsedEntity(entity.entity_id, entity.entity_type, new_vertices))

    return transformed_revised

# --- 3. Matching Step ---

def _to_shapely(entity: ParsedEntity):
    """Convert a ParsedEntity to a Shapely geometry object."""
    # (Implementation remains the same)
    if len(entity.vertices) < 2:
        return None
    if len(entity.vertices) > 2 and entity.vertices[0] == entity.vertices[-1]:
        try:
            return Polygon(entity.vertices)
        except ValueError:
            return None # Invalid polygon
    return LineString(entity.vertices)

def match_entities(original: Iterable[ParsedEntity], revised: Iterable[ParsedEntity]) -> dict[str, list[ParsedEntity]]:
    """Match entities between two drawings using spatial indexing."""
    # (Implementation remains largely the same, but now operates on normalized `revised` entities)
    original_geoms = {i: _to_shapely(entity) for i, entity in enumerate(original)}
    revised_geoms = {i: _to_shapely(entity) for i, entity in enumerate(revised)}

    original_entities = list(original)
    revised_entities = list(revised)
    original_geoms = {i: g for i, g in original_geoms.items() if g and not g.is_empty}
    revised_geoms = {i: g for i, g in revised_geoms.items() if g and not g.is_empty}

    idx = index.Index()
    for i, geom in original_geoms.items():
        idx.insert(i, geom.bounds)

    matched_original_indices = set()
    matched_revised_indices = set()

    for i, r_geom in revised_geoms.items():
        candidate_indices = list(idx.intersection(r_geom.bounds))
        for j in candidate_indices:
            if j in matched_original_indices:
                continue
            o_geom = original_geoms.get(j)
            if o_geom and o_geom.equals(r_geom):
                matched_original_indices.add(j)
                matched_revised_indices.add(i)
                break

    added = [revised_entities[i] for i in revised_geoms if i not in matched_revised_indices]
    removed = [original_entities[i] for i in original_geoms if i not in matched_original_indices]

    return {"added": added, "removed": removed, "modified": []}

# --- Exports ---

__all__ = ["ParsedEntity", "parse_dxf", "normalize_entities_by_grid", "match_entities"]
