from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from app.models import DiffEntity
from app.services.parsing import ParsedEntity

try:  # pragma: no cover - optional dependency
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover - executed when reportlab missing
    REPORTLAB_AVAILABLE = False


@dataclass(slots=True)
class _Viewport:
    min_x: float
    min_y: float
    scale: float
    page_width: float
    page_height: float


def render_diff_pdf(
    job_id: str,
    *,
    original_entities: Sequence[ParsedEntity],
    revised_entities: Sequence[ParsedEntity],
    diff_entities: Sequence[DiffEntity],
    output_path: Path,
) -> bool:
    """Render a PDF overlay report; returns True when using the rich renderer."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if REPORTLAB_AVAILABLE:
        try:
            _render_with_reportlab(job_id, original_entities, revised_entities, diff_entities, output_path)
            return True
        except Exception:  # pragma: no cover - runtime rendering issues fall back to stub
            pass

    _write_stub_pdf(job_id, len(diff_entities), output_path)
    return False


def _render_with_reportlab(
    job_id: str,
    original_entities: Sequence[ParsedEntity],
    revised_entities: Sequence[ParsedEntity],
    diff_entities: Sequence[DiffEntity],
    output_path: Path,
) -> None:
    viewport = _compute_viewport(original_entities, revised_entities, diff_entities)
    pdf = canvas.Canvas(str(output_path), pagesize=(viewport.page_width, viewport.page_height))
    pdf.setTitle(f"Floor Plan Diff Report - {job_id}")

    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, viewport.page_width, viewport.page_height, fill=1, stroke=0)

    pdf.setFillColor(colors.HexColor("#e2e8f0"))
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(36, viewport.page_height - 36, "Floor Plan Diff Overlay")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.drawString(36, viewport.page_height - 52, f"Job ID: {job_id}")

    _draw_entities(pdf, original_entities, viewport, stroke=colors.HexColor("#cbd5f5"), fill=None)
    _draw_entities(pdf, revised_entities, viewport, stroke=colors.HexColor("#93c5fd"), fill=None)

    diff_palette = {
        "added": (colors.HexColor("#34d399"), colors.HexColor("#bbf7d0")),
        "removed": (colors.HexColor("#f87171"), colors.HexColor("#fecaca")),
        "modified": (colors.HexColor("#f59e0b"), colors.HexColor("#fde68a")),
    }

    for entity in diff_entities:
        stroke_color, fill_color = diff_palette.get(entity.change_type, (colors.black, colors.HexColor("#e2e8f0")))
        _draw_diff_entity(pdf, entity, viewport, stroke=stroke_color, fill=fill_color)

    _draw_legend(pdf, viewport)

    pdf.showPage()
    pdf.save()


def _collect_points(
    original_entities: Sequence[ParsedEntity],
    revised_entities: Sequence[ParsedEntity],
    diff_entities: Sequence[DiffEntity],
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for collection in (original_entities, revised_entities):
        for entity in collection:
            points.extend(entity.vertices)
    for entity in diff_entities:
        points.extend(entity.polygon.points)
    return points


def _compute_viewport(
    original_entities: Sequence[ParsedEntity],
    revised_entities: Sequence[ParsedEntity],
    diff_entities: Sequence[DiffEntity],
) -> _Viewport:
    points = _collect_points(original_entities, revised_entities, diff_entities)
    if not points:
        return _Viewport(0.0, 0.0, 1.0, 612.0, 792.0)

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    margin = 72.0
    target = 720.0
    scale = min(target / width, target / height)
    page_width = width * scale + margin * 2
    page_height = height * scale + margin * 2

    return _Viewport(min_x=min_x, min_y=min_y, scale=scale, page_width=page_width, page_height=page_height)


def _transform(point: tuple[float, float], viewport: _Viewport) -> tuple[float, float]:
    x = (point[0] - viewport.min_x) * viewport.scale + 72.0
    y = (point[1] - viewport.min_y) * viewport.scale + 72.0
    return (x, viewport.page_height - y)


def _draw_entities(
    pdf: "canvas.Canvas",
    entities: Sequence[ParsedEntity],
    viewport: _Viewport,
    *,
    stroke,
    fill,
) -> None:
    pdf.setLineWidth(0.6)
    pdf.setStrokeColor(stroke)
    if fill is not None:
        pdf.setFillColor(fill)
    for entity in entities:
        if len(entity.vertices) < 2:
            continue
        path = pdf.beginPath()
        first = _transform(entity.vertices[0], viewport)
        path.moveTo(*first)
        for vertex in entity.vertices[1:]:
            path.lineTo(*_transform(vertex, viewport))
        pdf.drawPath(path, fill=bool(fill), stroke=1)


def _draw_diff_entity(pdf: "canvas.Canvas", entity: DiffEntity, viewport: _Viewport, *, stroke, fill) -> None:
    if not entity.polygon.points:
        return
    path = pdf.beginPath()
    first = _transform(entity.polygon.points[0], viewport)
    path.moveTo(*first)
    for point in entity.polygon.points[1:]:
        path.lineTo(*_transform(point, viewport))
    path.close()
    pdf.setStrokeColor(stroke)
    pdf.setFillColor(fill)
    pdf.setLineWidth(1.2)
    pdf.drawPath(path, fill=1, stroke=1)


def _draw_legend(pdf: "canvas.Canvas", viewport: _Viewport) -> None:
    entries = [
        ("#cbd5f5", "原图"),
        ("#93c5fd", "改图"),
        ("#34d399", "新增"),
        ("#f87171", "删除"),
        ("#f59e0b", "修改"),
    ]
    pdf.setFont("Helvetica", 9)
    x = 36
    y = 48
    for color_hex, label in entries:
        pdf.setFillColor(colors.HexColor(color_hex))
        pdf.rect(x, y, 10, 10, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.drawString(x + 14, y, label)
        x += 80


def _write_stub_pdf(job_id: str, entity_count: int, destination: Path) -> None:
    lines = [
        "Floor Plan Diff Overlay",
        f"Job: {job_id}",
        "reportlab not available; rendered placeholder PDF.",
        f"Diff entities: {entity_count}",
    ]
    content = _build_pdf_content(lines)
    destination.write_bytes(content)


def _build_pdf_content(lines: Iterable[str]) -> bytes:
    import io

    def _escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")

    objects: list[bytes] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")

    page_obj = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    objects.append(page_obj)

    text_lines = []
    y = 760
    for line in lines:
        safe = _escape(line)
        text_lines.append(f"BT /F1 14 Tf 72 {y} Td ({safe}) Tj ET")
        y -= 20
    stream = "\n".join(text_lines).encode("latin-1")
    content_obj = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
    objects.append(content_obj)

    font_obj = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects.append(font_obj)

    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(body)
        buffer.write(b"\nendobj\n")

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))

    buffer.write(b"trailer\n")
    buffer.write(f"<< /Size {len(offsets)} /Root 1 0 R >>\n".encode("ascii"))
    buffer.write(b"startxref\n")
    buffer.write(f"{xref_start}\n".encode("ascii"))
    buffer.write(b"%%EOF")

    return buffer.getvalue()


__all__ = ["render_diff_pdf"]
