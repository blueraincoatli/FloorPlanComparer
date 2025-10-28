from __future__ import annotations

import argparse
from pathlib import Path

from dataclasses import dataclass
from typing import Optional

from pypdf import PdfReader, PdfWriter


@dataclass
class PageInfo:
    reader: PdfReader
    page_index: int
    width: float
    height: float


def _page_info(path: Path, page_number: int = 0) -> PageInfo:
    reader = PdfReader(path)
    page = reader.pages[page_number]
    mediabox = page.mediabox
    width = float(mediabox.width)
    height = float(mediabox.height)
    return PageInfo(reader=reader, page_index=page_number, width=width, height=height)


def overlay_pdfs(
    original: Path,
    revised: Path,
    output: Path,
    *,
    alpha: float = 0.5,
    poppler_path: str | None = None,
) -> None:
    original_info = _page_info(original)
    revised_info = _page_info(revised)

    if original_info.width != revised_info.width or original_info.height != revised_info.height:
        scale_x = revised_info.width / original_info.width
        scale_y = revised_info.height / original_info.height
        base_page = original_info.reader.pages[original_info.page_index]
        overlay_page = revised_info.reader.pages[revised_info.page_index]

        overlay_page.scale_to(original_info.width, original_info.height)
    else:
        base_page = original_info.reader.pages[original_info.page_index]
        overlay_page = revised_info.reader.pages[revised_info.page_index]

    base_page.merge_page(overlay_page)
    writer = PdfWriter()
    writer.add_page(base_page)
    with output.open("wb") as output_file:
        writer.write(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Overlay two PDF pages with adjustable opacity")
    parser.add_argument("original", type=Path, help="Path to original PDF")
    parser.add_argument("revised", type=Path, help="Path to revised PDF")
    parser.add_argument("output", type=Path, help="Path to output overlay PDF")
    parser.add_argument("--alpha", type=float, default=0.5, help="Alpha transparency for overlay (0-1)")
    parser.add_argument("--poppler", type=str, default=None, help="Optional path to poppler bin folder (if poppler tools are present)")
    args = parser.parse_args()

    overlay_pdfs(args.original, args.revised, args.output, alpha=args.alpha, poppler_path=args.poppler)


if __name__ == "__main__":
    main()
