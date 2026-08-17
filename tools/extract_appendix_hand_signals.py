"""Extract the Appendix F hand-signal diagram from the bundled WFDF Appendix PDF.

The source diagram may be stored as a raster image or as vector/text content.  This
script therefore prefers the exact signal artwork bounds when they can be found and
falls back to rendering the Appendix F region.  The resulting PNG is suitable for
static web deployment and always comes from the repository's source PDF.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "docs" / "source-pdf" / "WFDF-Rules-of-Ultimate-2025-2028-Appendix-v2.0.pdf"
DEFAULT_OUTPUT = ROOT / "web" / "assets" / "figures" / "appendix-hand-signals.png"

SIGNAL_ANCHORS = (
    "1. Foul",
    "5. Accepted",
    "9. Disc Up",
    "13. Turnover",
    "17. Spirit Stoppage",
    "21. Play has stopped",
    "24. Match Point",
)


def _page_text(page: fitz.Page) -> str:
    return " ".join(page.get_text("text").replace("\u00ad", "").split())


def _union(rects: list[fitz.Rect]) -> fitz.Rect | None:
    if not rects:
        return None
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result |= rect
    return result


def _trim_white(image: Image.Image, padding: int = 20) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    bbox = ImageChops.difference(rgb, background).getbbox()
    if not bbox:
        return rgb
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(rgb.width, right + padding)
    bottom = min(rgb.height, bottom + padding)
    return rgb.crop((left, top, right, bottom))


def _section_pages(pdf: fitz.Document) -> tuple[int, int]:
    start = None
    end = None
    for index, page in enumerate(pdf):
        text = _page_text(page)
        if start is None and (
            "F1. Purpose of Hand Signals" in text
            or "Appendix F: Hand Signals" in text
            or ("Purpose of Hand Signals" in text and "Use of Signals" in text)
        ):
            start = index
            continue
        if start is not None and index >= start and (
            "Appendix G" in text
            or "G1. Creative Commons" in text
            or "G1. Attribution" in text
        ):
            end = index
            break
    if start is None:
        raise RuntimeError("Could not locate Appendix F (Hand Signals) in the source PDF")
    if end is None:
        end = min(len(pdf) - 1, start + 3)
    return start, end


def _clip_for_page(page: fitz.Page, *, first: bool, last: bool) -> tuple[fitz.Rect, dict]:
    page_rect = page.rect
    meta: dict[str, object] = {"strategy": "section-render"}

    # If signal labels are real PDF text, their union gives the cleanest crop.
    anchor_rects: list[fitz.Rect] = []
    found_anchors: list[str] = []
    for anchor in SIGNAL_ANCHORS:
        matches = page.search_for(anchor)
        if matches:
            found_anchors.append(anchor)
            anchor_rects.extend(matches)
    if anchor_rects:
        bounds = _union(anchor_rects)
        assert bounds is not None
        clip = fitz.Rect(24, max(24, bounds.y0 - 44), page_rect.width - 24, min(page_rect.height - 24, bounds.y1 + 120))
        # The anchors may be distributed across a grid. Extend to the end of the
        # Appendix-F content so illustrations below the last anchor are preserved.
        if last:
            g_rects = page.search_for("Appendix G") or page.search_for("G1.")
            clip.y1 = min(clip.y1 if clip.y1 > bounds.y1 + 20 else page_rect.height - 24,
                          min((rect.y0 - 12 for rect in g_rects), default=page_rect.height - 24))
        else:
            clip.y1 = page_rect.height - 24
        meta.update({"strategy": "signal-text-anchors", "anchors": found_anchors})
        return clip, meta

    # When the diagram is a placed bitmap, use its image rectangle rather than the
    # whole page. Ignore tiny logos/icons and anything clearly above F2.3.
    f23_rects = page.search_for("F2.3") if first else []
    min_y = max((rect.y1 for rect in f23_rects), default=24) + (8 if first else 0)
    image_rects: list[fitz.Rect] = []
    page_area = page_rect.width * page_rect.height
    for image_info in page.get_images(full=True):
        xref = image_info[0]
        for rect in page.get_image_rects(xref):
            if rect.y1 <= min_y:
                continue
            if rect.width * rect.height < page_area * 0.01:
                continue
            image_rects.append(rect)
    if image_rects:
        bounds = _union(image_rects)
        assert bounds is not None
        clip = fitz.Rect(max(18, bounds.x0 - 8), max(min_y, bounds.y0 - 8), min(page_rect.width - 18, bounds.x1 + 8), min(page_rect.height - 18, bounds.y1 + 8))
        meta.update({"strategy": "embedded-image-bounds", "embedded_images": len(image_rects)})
        return clip, meta

    # Vector artwork fallback: render the Appendix-F portion of the page. On the
    # first page start immediately after F2.3; on the last page stop before Appendix G.
    y0 = min_y if first else 24
    y1 = page_rect.height - 24
    if last:
        g_rects = page.search_for("Appendix G") or page.search_for("G1.")
        if g_rects:
            y1 = min(rect.y0 for rect in g_rects) - 12
    return fitz.Rect(24, y0, page_rect.width - 24, max(y0 + 20, y1)), meta


def extract(pdf_path: Path, output_path: Path, manifest_path: Path | None = None, scale: float = 2.5) -> dict:
    pdf = fitz.open(pdf_path)
    start, end = _section_pages(pdf)
    rendered: list[Image.Image] = []
    pages_meta: list[dict] = []

    for index in range(start, end + 1):
        page = pdf[index]
        clip, meta = _clip_for_page(page, first=index == start, last=index == end)
        if clip.height <= 20 or clip.width <= 20:
            continue
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        image = _trim_white(image)
        # Skip effectively blank crops.
        if image.width < 80 or image.height < 80:
            continue
        rendered.append(image)
        pages_meta.append({
            "pdf_page": index + 1,
            "clip": [round(clip.x0, 2), round(clip.y0, 2), round(clip.x1, 2), round(clip.y1, 2)],
            "output_size": [image.width, image.height],
            **meta,
        })

    if not rendered:
        raise RuntimeError("Appendix F was found, but no hand-signal artwork could be rendered")

    gap = 24
    width = max(image.width for image in rendered)
    height = sum(image.height for image in rendered) + gap * (len(rendered) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for image in rendered:
        x = (width - image.width) // 2
        canvas.paste(image, (x, y))
        y += image.height + gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)
    result = {
        "source": str(pdf_path.relative_to(ROOT) if pdf_path.is_relative_to(ROOT) else pdf_path),
        "output": str(output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path),
        "section_pages": [start + 1, end + 1],
        "rendered_pages": pages_meta,
        "final_size": [canvas.width, canvas.height],
    }
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--scale", type=float, default=2.5)
    args = parser.parse_args()
    result = extract(args.pdf, args.output, args.manifest, args.scale)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
