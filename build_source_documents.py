"""Recover maintainable Markdown sources from the current web handbook."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WEB_DATA = ROOT / "web" / "data.js"
DOCS = ROOT / "docs"
DIAGRAM_ASSETS = DOCS / "diagram-assets"


def load_data() -> dict:
    source = WEB_DATA.read_text(encoding="utf-8")
    payload = source.removeprefix("window.HANDBOOK_DATA=").rstrip(";\n")
    return json.loads(payload)


def numbered_line(text: str, pattern: str) -> str | None:
    match = re.match(pattern, text)
    if not match:
        return None
    number, body = match.groups()
    return f"**{number}.** {body}"


def write_appendix(document: dict) -> None:
    lines = [
        "# WFDF 团队飞盘规则 2025-2028 附录 v2.0（中文校订整合版）",
        "",
        "> 本文件由当前网页版手册内容回溯生成，作为附录中文源稿。正式适用版本以 WFDF 发布文本为准。",
        "",
    ]
    chapter_titles = {
        "appendix-a": "WFDF 比赛附加规则",
        "appendix-b": "WFDF 赛事附加规则",
        "appendix-c": "比赛服装要求",
        "appendix-d": "WFDF 参赛资格与参赛名单指南",
        "appendix-e": "种子、赛程与赛事席位",
        "appendix-f": "手势",
        "appendix-g": "许可条款",
        "appendix-h": "致谢",
    }
    for section in document["sections"]:
        key = section["key"]
        if key == "Introduction":
            lines.extend(["# 引言", ""])
        elif key == "signals":
            lines.extend(["## 手势 1–24", ""])
        elif key.startswith("appendix-"):
            letter = key[-1].upper()
            lines.extend([f"# 附录 {letter}：{chapter_titles.get(key, section['title'])}", ""])
        else:
            lines.extend([f"## {key}. {section['title']}", ""])
        for paragraph in section["paragraphs"]:
            for raw_line in paragraph["zh"].splitlines() or [""]:
                converted = numbered_line(raw_line, r"^([A-F]\d+(?:\.\d+)*)\.\s*(.+)$")
                lines.append(converted or raw_line)
            lines.append("")
    (DOCS / "WFDF团队飞盘规则2025-2028_附录v2.0_中文校订整合版.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_annotations(document: dict) -> None:
    lines = [
        "# WFDF 官方注释 2025-2028（中文校订整合版）",
        "",
        "> 本文件由当前网页版手册内容回溯生成，作为官方注释中文源稿。正式适用版本以 WFDF 发布文本为准。",
        "",
    ]
    for section in document["sections"]:
        key = section["key"]
        if key == "Introduction":
            lines.extend(["# 引言", ""])
            for paragraph in section["paragraphs"]:
                lines.extend(paragraph["zh"].splitlines() or [""])
                lines.append("")
            lines.extend(["# 官方注释", "", "# 原则", ""])
            continue
        if key == "Principles":
            for paragraph in section["paragraphs"]:
                lines.extend(paragraph["zh"].splitlines() or [""])
                lines.append("")
            continue
        lines.extend([f"# {key}. {section['title']}", ""])
        for paragraph in section["paragraphs"]:
            for raw_line in paragraph["zh"].splitlines() or [""]:
                match = re.match(r"^(\d+\.\d+)\.\s*(.+)$", raw_line)
                lines.append(f"## {match.group(1)}. {match.group(2)}" if match else raw_line)
            lines.append("")
    (DOCS / "WFDF团队飞盘规则2025-2028_官方注释_中文校订整合版.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_diagram_source(document: dict) -> None:
    name = "判定流程图" if document["id"] == "decision" else "发盘图"
    filename = f"WFDF-极限飞盘规则-{name}-中文转写.md"
    lines = [
        f"# WFDF 极限飞盘规则 2025-2028 - {name}（中文转写）",
        "",
        "> 本文件是网页中文图示的可维护 Markdown 源稿。网页构建直接使用其中的本地 PNG 素材。",
        "",
    ]
    for index, section in enumerate(document["sections"], start=1):
        asset = f"diagram-assets/{document['id']}-{index}.png"
        lines.extend([
            f"## {section['key']}：{section['title']}",
            "",
            section["description"],
            "",
            f"![{section['alt']}]({asset})",
            "",
        ])
        if section.get("keywords"):
            lines.extend(["### 图中文字检索串", "", section["keywords"], ""])
    (DOCS / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    DIAGRAM_ASSETS.mkdir(parents=True, exist_ok=True)
    for index in range(1, len(document["sections"]) + 1):
        source = WEB_DATA.parent / "assets" / "diagrams" / f"{document['id']}-{index}.png"
        target = DIAGRAM_ASSETS / source.name
        shutil.copy2(source, target)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    data = load_data()
    documents = {item["id"]: item for item in data["documents"]}
    write_appendix(documents["appendix"])
    write_annotations(documents["annotations"])
    write_diagram_source(documents["decision"])
    write_diagram_source(documents["pull"])
    print(f"Recovered sources under {DOCS}")


if __name__ == "__main__":
    main()
