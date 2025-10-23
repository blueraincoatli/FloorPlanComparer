"""Parsing and matching utilities for DWG/DXF files.

This module currently contains placeholder logic that mimics the output of a real
geometry pipeline. It should be replaced with genuine implementations once the
ODA conversion, ezdxf parsing, and shapely-based matching are integrated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class ParsedEntity:
    """Lightweight representation of a geometry entity."""

    entity_id: str
    entity_type: str
    vertices: list[tuple[float, float]]


def parse_dxf(path: Path) -> list[ParsedEntity]:
    """Parse the given DXF file and return simplified entities.

    Placeholder implementation that returns mocked geometry. Replace this with
    `ezdxf` or other CAD parsing libraries once available.
    """

    seed = path.stem[-2:]
    offset = sum(ord(ch) for ch in seed) % 30
    return [
        ParsedEntity(
            entity_id=f"{path.stem}-wall",
            entity_type="wall",
            vertices=[(0 + offset, 0 + offset), (60 + offset, 0 + offset), (60 + offset, 30 + offset)],
        ),
        ParsedEntity(
            entity_id=f"{path.stem}-door",
            entity_type="door",
            vertices=[(80 + offset, 20 + offset), (100 + offset, 20 + offset), (100 + offset, 40 + offset)],
        ),
    ]


def match_entities(original: Iterable[ParsedEntity], revised: Iterable[ParsedEntity]) -> dict[str, list[ParsedEntity]]:
    """Match entities between two drawings.

    Returns a mapping keyed by change type. The current implementation simply
    compares entity IDs to determine added/removed/modified stubs.
    """

    original_map = {entity.entity_id: entity for entity in original}
    revised_map = {entity.entity_id: entity for entity in revised}

    added: list[ParsedEntity] = []
    removed: list[ParsedEntity] = []
    modified: list[ParsedEntity] = []

    for entity_id, entity in revised_map.items():
        if entity_id not in original_map:
            added.append(entity)
        else:
            original_vertices = original_map[entity_id].vertices
            if original_vertices != entity.vertices:
                modified.append(entity)

    for entity_id, entity in original_map.items():
        if entity_id not in revised_map:
            removed.append(entity)

    return {"added": added, "removed": removed, "modified": modified}


__all__ = ["ParsedEntity", "parse_dxf", "match_entities"]
