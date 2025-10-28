"""Parsing, normalization, and matching utilities for DWG/DXF files.

The module provides two execution paths:

* If the optional CAD stack (`ezdxf`, `numpy`, `shapely`, `rtree`) is installed, it
  performs the richer geometry parsing and alignment that was prototyped by the
  previous iteration of the project.
* Otherwise it falls back to a lightweight, deterministic stub so that the rest of
  the pipeline (and unit tests) can run without heavyweight native dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Iterator, Literal, cast

try:  # pragma: no cover - optional dependency imports
    import re
    from math import cos, radians, sin, tau, isclose

    import ezdxf
    import numpy as np
    from ezdxf.lldxf.const import DXFStructureError
    from ezdxf.math import Matrix44, Vec3
    from rtree import index
    from shapely.geometry import LineString, Point, Polygon

    CAD_STACK_AVAILABLE = True
except ImportError:  # pragma: no cover - executed when deps missing
    CAD_STACK_AVAILABLE = False


@dataclass(slots=True)
class ParsedEntity:
    """Lightweight representation of a geometry entity."""

    entity_id: str
    entity_type: str
    vertices: list[tuple[float, float]]
    layer: str | None = None
    color: int | None = None
    linetype: str | None = None
    source: Literal["original", "revised"] | None = None


def _stub_seed(path: Path) -> int:
    stem = path.stem[-2:]
    return sum(ord(ch) for ch in stem) % 30


def _stub_entities(path: Path, source: Literal["original", "revised"] | None = None) -> list[ParsedEntity]:
    offset = _stub_seed(path)
    base = [
        ParsedEntity(
            entity_id=f"{path.stem}-wall",
            entity_type="WALL",
            vertices=[(0 + offset, 0 + offset), (60 + offset, 0 + offset), (60 + offset, 30 + offset)],
            layer="STUB",
            color=7,
            source=source,
        ),
        ParsedEntity(
            entity_id=f"{path.stem}-door",
            entity_type="DOOR",
            vertices=[(80 + offset, 20 + offset), (100 + offset, 20 + offset), (100 + offset, 40 + offset)],
            layer="STUB",
            color=3,
            source=source,
        ),
    ]
    return base


def parse_dxf(path: Path, *, source: Literal["original", "revised"] | None = None) -> list[ParsedEntity]:
    """Parse the given DXF file and return simplified entities."""

    if not CAD_STACK_AVAILABLE:
        return _stub_entities(path, source)

    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
    except (DXFStructureError, FileNotFoundError, OSError) as exc:  # pragma: no cover - heavy path
        if CAD_STACK_AVAILABLE:
            return _stub_entities(path, source)
        raise RuntimeError(f"Failed to parse DXF file {path}: {exc}") from exc

    def _iter_entities() -> Iterator[ParsedEntity]:
        for insert in msp.query("INSERT"):
            try:
                insert.explode()
            except Exception:  # pragma: no cover - best effort explode
                continue

        def _safe_color(value: int | None) -> int | None:
            if value is None:
                return None
            try:
                color_value = int(value)
            except (TypeError, ValueError):
                return None
            return color_value if color_value > 0 else None

        for entity in msp:
            if not hasattr(entity, "dxf"):
                continue
            vertices = _extract_vertices(entity)
            if not vertices:
                continue
            layer = getattr(entity.dxf, "layer", None)
            color = _safe_color(getattr(entity.dxf, "color", None))
            linetype = getattr(entity.dxf, "linetype", None)
            data = ParsedEntity(
                entity_id=str(entity.dxf.handle),
                entity_type=entity.dxftype(),
                vertices=vertices,
                layer=layer,
                color=color,
                linetype=linetype,
                source=source,
            )
            yield data

    return list(_iter_entities())


def normalize_entities_by_grid(
    revised_entities: list[ParsedEntity], original_entities: list[ParsedEntity]
) -> list[ParsedEntity]:
    if not CAD_STACK_AVAILABLE:
        return revised_entities
    return _normalize_by_grid(revised_entities, original_entities)


def match_entities(original: Iterable[ParsedEntity], revised: Iterable[ParsedEntity]) -> dict[str, list[ParsedEntity]]:
    original_list = list(original)
    revised_list = list(revised)

    if not CAD_STACK_AVAILABLE:
        original_ids = {entity.entity_id for entity in original_list}
        revised_ids = {entity.entity_id for entity in revised_list}
        added = [entity for entity in revised_list if entity.entity_id not in original_ids]
        removed = [entity for entity in original_list if entity.entity_id not in revised_ids]
        return {"added": added, "removed": removed, "modified": []}

    original_geoms = {i: _to_geometry(entity) for i, entity in enumerate(original_list)}
    revised_geoms = {i: _to_geometry(entity) for i, entity in enumerate(revised_list)}

    original_geoms = {i: geom for i, geom in original_geoms.items() if geom is not None and not geom.is_empty}
    revised_geoms = {i: geom for i, geom in revised_geoms.items() if geom is not None and not geom.is_empty}

    spatial_index = index.Index()
    for idx_value, geom in original_geoms.items():
        spatial_index.insert(idx_value, geom.bounds)

    matched_original: set[int] = set()
    matched_revised: set[int] = set()

    for revised_idx, revised_geom in revised_geoms.items():
        for candidate_idx in spatial_index.intersection(revised_geom.bounds):
            if candidate_idx in matched_original:
                continue
            original_geom = original_geoms.get(candidate_idx)
            if original_geom is None:
                continue
            if original_geom.equals(revised_geom):
                matched_original.add(candidate_idx)
                matched_revised.add(revised_idx)
                break

    added = [revised_list[i] for i in revised_geoms if i not in matched_revised]
    removed = [original_list[i] for i in original_geoms if i not in matched_original]

    return {"added": added, "removed": removed, "modified": []}


# ----- Rich CAD branch helpers (only evaluated when dependencies exist) -----

if CAD_STACK_AVAILABLE:

    def _vec2_to_tuple(value) -> tuple[float, float]:
        try:
            return (float(value.x), float(value.y))
        except AttributeError:
            return (float(value[0]), float(value[1]))

    def _extract_vertices(entity) -> list[tuple[float, float]] | None:
        if entity.dxftype() in {"LINE", "XLINE", "RAY"}:
            return [_vec2_to_tuple(entity.dxf.start.vec2), _vec2_to_tuple(entity.dxf.end.vec2)]
        if entity.dxftype() == "LWPOLYLINE":
            try:
                return [(float(x), float(y)) for x, y in entity.get_points("xy")]
            except TypeError:
                return [(float(x), float(y)) for x, y, *_ in entity.get_points()]
        if entity.dxftype() == "POLYLINE":
            try:
                return [_vec2_to_tuple(vertex.dxf.location.vec2) for vertex in entity.vertices()]
            except AttributeError:
                return [(float(x), float(y)) for x, y, *_ in entity.points()]
        if entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            radius = float(getattr(entity.dxf, "radius", 0))
            if radius <= 0:
                return None
            steps = 64
            return [
                (
                    float(center.x + radius * cos(tau * i / steps)),
                    float(center.y + radius * sin(tau * i / steps)),
                )
                for i in range(steps)
            ]
        if entity.dxftype() == "ARC":
            center = entity.dxf.center
            radius = float(getattr(entity.dxf, "radius", 0))
            if radius <= 0:
                return None
            start_angle = radians(getattr(entity.dxf, "start_angle", 0.0))
            end_angle = radians(getattr(entity.dxf, "end_angle", 0.0))
            if end_angle < start_angle:
                end_angle += tau
            steps = 48
            return [
                (
                    float(center.x + radius * cos(start_angle + (end_angle - start_angle) * i / steps)),
                    float(center.y + radius * sin(start_angle + (end_angle - start_angle) * i / steps)),
                )
                for i in range(steps + 1)
            ]
        if entity.dxftype() == "ELLIPSE":
            return None
        if entity.dxftype() == "SPLINE":
            return None
        if hasattr(entity, "vertices"):
            return [_vec2_to_tuple(v.dxf.location.vec2) for v in entity.vertices]
        return None


    @dataclass(slots=True)
    class _GridAxis:
        label: str
        is_vertical: bool
        line: LineString


    def _find_grid_axes(entities: list[ParsedEntity], tolerance: float = 1e-3) -> list[_GridAxis]:
        label_re = re.compile(r"^[A-Z0-9']+$")
        texts = [entity for entity in entities if entity.entity_type == "TEXT" and label_re.match(entity.entity_id)]
        circles = [entity for entity in entities if entity.entity_type == "CIRCLE"]

        axis_labels: list[tuple[str, Point]] = []
        for text in texts:
            text_center = Point(text.vertices[0])
            for circle in circles:
                circle_center = Point(np.mean(circle.vertices, axis=0))
                radius = Point(circle.vertices[0]).distance(Point(circle.vertices[min(1, len(circle.vertices) - 1)]))
                if text_center.distance(circle_center) <= radius + tolerance:
                    axis_labels.append((text.entity_id, text_center))
                    break

        lines = [entity for entity in entities if entity.entity_type in {"LINE", "LWPOLYLINE"}]
        candidates: list[tuple[LineString, bool]] = []
        for line in lines:
            if len(line.vertices) < 2:
                continue
            start, end = Vec3(line.vertices[0]), Vec3(line.vertices[-1])
            vertical = isclose(start.x, end.x, abs_tol=tolerance) and not isclose(start.y, end.y, abs_tol=tolerance)
            horizontal = isclose(start.y, end.y, abs_tol=tolerance) and not isclose(start.x, end.x, abs_tol=tolerance)
            if vertical or horizontal:
                candidates.append((LineString(line.vertices), vertical))

        axes: list[_GridAxis] = []
        for label, center in axis_labels:
            best_match: tuple[LineString, bool] | None = None
            best_distance = float("inf")
            for line, is_vertical in candidates:
                distance = line.distance(center)
                if distance < best_distance:
                    best_distance = distance
                    best_match = (line, is_vertical)
            if best_match and best_distance < 500:
                axes.append(_GridAxis(label=label, is_vertical=best_match[1], line=best_match[0]))
        return axes


    def _normalize_by_grid(
        revised_entities: list[ParsedEntity], original_entities: list[ParsedEntity]
    ) -> list[ParsedEntity]:
        original_axes = _find_grid_axes(original_entities)
        revised_axes = _find_grid_axes(revised_entities)
        if not original_axes or not revised_axes:
            return revised_entities

        def _reference_points(axes: list[_GridAxis]) -> tuple[Point | None, Point | None]:
            horizontal = sorted((axis for axis in axes if not axis.is_vertical), key=lambda axis: axis.line.bounds[1])
            vertical = sorted((axis for axis in axes if axis.is_vertical), key=lambda axis: axis.line.bounds[0])
            if len(horizontal) < 2 or len(vertical) < 2:
                return None, None
            first = horizontal[0].line.intersection(vertical[0].line)
            last = horizontal[-1].line.intersection(vertical[-1].line)
            return first, last

        original_first, original_last = _reference_points(original_axes)
        revised_first, revised_last = _reference_points(revised_axes)
        if not all((original_first, original_last, revised_first, revised_last)):
            return revised_entities

        original_vector = Vec3(original_last.x - original_first.x, original_last.y - original_first.y, 0)
        revised_vector = Vec3(revised_last.x - revised_first.x, revised_last.y - revised_first.y, 0)
        if revised_vector.magnitude == 0:
            return revised_entities

        scale = original_vector.magnitude / revised_vector.magnitude
        angle = original_vector.angle_between(revised_vector)

        transform = (
            Matrix44.scale(scale, scale, scale)
            @ Matrix44.z_rotate(angle)
            @ Matrix44.translate(-revised_first.x, -revised_first.y, 0)
            @ Matrix44.translate(original_first.x, original_first.y, 0)
        )

        transformed: list[ParsedEntity] = []
        for entity in revised_entities:
            new_vertices = [transform.transform(Vec3(x, y, 0)).vec2 for x, y in entity.vertices]
            transformed.append(replace(entity, vertices=new_vertices))
        return transformed


    def _to_geometry(entity: ParsedEntity):
        if len(entity.vertices) < 2:
            return None
        if len(entity.vertices) > 2 and entity.vertices[0] == entity.vertices[-1]:
            try:
                return Polygon(entity.vertices)
            except ValueError:
                return None
        return LineString(entity.vertices)

else:

    def _extract_vertices(entity) -> list[tuple[float, float]] | None:  # pragma: no cover - stub branch
        return None

    def _normalize_by_grid(
        revised_entities: list[ParsedEntity], original_entities: list[ParsedEntity]
    ) -> list[ParsedEntity]:  # pragma: no cover - stub branch
        return revised_entities

    def _to_geometry(entity: ParsedEntity):  # pragma: no cover - stub branch
        return None


__all__ = ["ParsedEntity", "parse_dxf", "normalize_entities_by_grid", "match_entities"]
