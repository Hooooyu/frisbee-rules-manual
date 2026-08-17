"""Extract the 24 official hand-signal illustrations from the bundled WFDF Appendix.

The Appendix v2.0 PDF contains the hand-signal artwork as 24 embedded PNG images:
12 on the first diagram page and 12 on the next.  This script locates those pages
from their text, orders the embedded images by their visual position, and writes one
stable web asset per signal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "docs" / "source-pdf" / "WFDF-Rules-of-Ultimate-2025-2028-Appendix-v2.0.pdf"
DEFAULT_OUTPUT_DIR = ROOT / "web" / "assets" / "figures" / "hand-signals"

SIGNAL_FILES = (
    "01-foul.png",
    "02-violation.png",
    "03-goal.png",
    "04-contest.png",
    "05-accepted.png",
    "06-retracted.png",
    "07-in-out-of-bounds.png",
    "08-disc-down.png",
    "09-disc-up.png",
    "10-pick.png",
    "11-travel.png",
    "12-marking-infraction.png",
    "13-turnover.png",
    "14-timing-violation.png",
    "15-pulling-violation.png",
    "16-time-out.png",
    "17-spirit-stoppage.png",
    "18-stoppage.png",
    "19-personnel-ratio-male.png",
    "20-personnel-ratio-female.png",
    "21-play-has-stopped.png",
    "22-who-made-the-call.png",
    "23-did-not-affect-play.png",
    "24-match-point.png",
)


def _page_text(page: fitz.Page) -> str:
    return " ".join(page.get_text("text").replace("\u00ad", "").split())


def _ordered_image_xrefs(page: fitz.Page) -> list[int]:
    entries: list[tuple[float, float, int]] = []
    for image_info in page.get_images(full=True):
        xref = image_info[0]
        rects = page.get_image_rects(xref)
        if not rects:
            continue
        rect = rects[0]
        entries.append((rect.y0, rect.x0, xref))

    if len(entries) != 12:
        raise RuntimeError(f"Expected 12 embedded hand-signal images on PDF page {page.number + 1}, found {len(entries)}")

    entries.sort(key=lambda item: item[0])
    rows: list[list[tuple[float, float, int]]] = []
    for entry in entries:
        row_y = sum(item[0] for item in rows[-1]) / len(rows[-1]) if rows else None
        if row_y is None or abs(entry[0] - row_y) > 18:
            rows.append([entry])
        else:
            rows[-1].append(entry)

    ordered: list[int] = []
    for row in rows:
        ordered.extend(item[2] for item in sorted(row, key=lambda item: item[1]))
    if len(ordered) != 12:
        raise RuntimeError(f"Could not determine visual order for hand-signal images on PDF page {page.number + 1}")
    return ordered


def _locate_signal_pages(pdf: fitz.Document) -> tuple[int, int]:
    first = None
    second = None
    for index, page in enumerate(pdf):
        text = _page_text(page)
        image_count = len(page.get_images(full=True))
        if first is None and image_count == 12 and "1. Foul" in text and "12. Marking Infraction" in text:
            first = index
            continue
        if first is not None and index > first and image_count == 12 and "24. Match Point" in text:
            second = index
            break

    if first is None or second is None or second != first + 1:
        raise RuntimeError("Could not locate the two consecutive Appendix F hand-signal diagram pages")
    return first, second


def extract(pdf_path: Path, output_dir: Path, manifest_path: Path | None = None) -> dict:
    pdf = fitz.open(pdf_path)
    first_page, second_page = _locate_signal_pages(pdf)
    xrefs = _ordered_image_xrefs(pdf[first_page]) + _ordered_image_xrefs(pdf[second_page])

    output_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, object]] = []
    for number, (filename, xref) in enumerate(zip(SIGNAL_FILES, xrefs, strict=True), start=1):
        image = pdf.extract_image(xref)
        if image["ext"] != "png":
            raise RuntimeError(f"Signal {number} is unexpectedly stored as {image['ext']} instead of PNG")
        target = output_dir / filename
        target.write_bytes(image["image"])
        files.append({
            "number": number,
            "file": str(target.relative_to(ROOT) if target.is_relative_to(ROOT) else target),
            "xref": xref,
            "width": image["width"],
            "height": image["height"],
            "bytes": len(image["image"]),
        })

    result = {
        "source": str(pdf_path.relative_to(ROOT) if pdf_path.is_relative_to(ROOT) else pdf_path),
        "pdf_pages": [first_page + 1, second_page + 1],
        "count": len(files),
        "files": files,
    }
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = extract(args.pdf, args.output_dir, args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
