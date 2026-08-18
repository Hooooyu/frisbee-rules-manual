"""Build the web handbook with the reviewed Chinese front matter and terminology."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_web_handbook as handbook


CANONICAL_MAIN_TITLES = {
    "1": "飞盘精神",
    "2": "比赛场地",
    "3": "装备",
    "4": "回合、得分与比赛",
    "5": "队伍",
    "6": "比赛开始",
    "7": "开盘",
    "8": "比赛状态",
    "9": "读秒",
    "10": "验盘（Check）",
    "11": "出界",
    "12": "接盘队员与位置",
    "13": "攻防转换",
    "14": "得分",
    "15": "犯规、违规和违例的示意",
    "16": "示意后的比赛继续",
    "17": "犯规",
    "18": "违规和违例",
    "19": "安全中断",
    "20": "暂停",
}

DECLARATION_PATH = handbook.DOCS / "官方注释_规则引用编号校订说明.md"


def clean_markdown_inline(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()


def annotation_revision_notice() -> dict:
    """Load the canonical cross-reference correction declaration shown before Introduction."""
    markdown = DECLARATION_PATH.read_text(encoding="utf-8")
    lines = markdown.splitlines()
    title = ""
    body_start = 0

    for index, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("## "):
            title = clean_markdown_inline(line[3:])
            body_start = index + 1
            break

    if not title:
        raise ValueError("规则引用编号校订说明缺少标题")

    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in lines[body_start:]:
        if raw.strip():
            current.append(raw.rstrip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    paragraphs: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        stripped = [line.strip() for line in block]

        if stripped[0].startswith("### "):
            heading = clean_markdown_inline(stripped[0][4:])
            if index + 1 < len(blocks) and all(line.strip().startswith("|") for line in blocks[index + 1]):
                table = "\n".join(clean_markdown_inline(line) for line in blocks[index + 1])
                paragraphs.append(f"{heading}\n{table}")
                index += 2
                continue
            paragraphs.append(heading)
            index += 1
            continue

        if all(line.startswith("- ") for line in stripped):
            paragraphs.extend(f"• {clean_markdown_inline(line[2:])}" for line in stripped)
            index += 1
            continue

        if all(line.startswith("|") for line in stripped):
            paragraphs.append("\n".join(clean_markdown_inline(line) for line in stripped))
            index += 1
            continue

        paragraphs.append(clean_markdown_inline(" ".join(stripped)))
        index += 1

    if not paragraphs or not any("23 处" in paragraph for paragraph in paragraphs):
        raise ValueError("规则引用编号校订说明内容不完整")
    if not any("| 23 |" in paragraph for paragraph in paragraphs):
        raise ValueError("规则引用编号差异表未完整载入 23 条记录")

    return {
        "id": "annotations-revision-notice",
        "key": "",
        "title": title,
        "paragraphs": [
            {"zh": value, "en": "", "page": None}
            for value in paragraphs
        ],
    }


def is_legacy_annotation_front_matter(section: dict) -> bool:
    """Return True for the old source-authored notice/contents that must not render on the web."""
    return (
        section.get("id") == "annotations-revision-notice"
        or section.get("title") in {"修订公告", "目录"}
        or section.get("key") in {"Revision Notice", "Contents"}
    )


def install_reviewed_overrides() -> None:
    handbook.MAIN_TITLES.update(CANONICAL_MAIN_TITLES)
    original_translate = handbook.translate_source_sections

    def translate_source_sections(meta: dict, sections: list[dict]) -> dict:
        rendered = original_translate(meta, sections)
        if meta["id"] == "annotations":
            clean_sections = [
                section
                for section in rendered["sections"]
                if not is_legacy_annotation_front_matter(section)
            ]
            rendered["sections"] = [annotation_revision_notice(), *clean_sections]
        return rendered

    handbook.translate_source_sections = translate_source_sections


def normalize_quick_terms() -> None:
    path = handbook.WEB / "data.js"
    text = path.read_text(encoding="utf-8")
    replacements = {
        "发盘（pull）": "开盘（pull）",
        "攻守转换（turnover）": "攻防转换（turnover）",
        "检查（check）": "验盘（check）",
        "比赛精神（Spirit of the Game）": "飞盘精神（Spirit of the Game）",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def validate() -> None:
    data = (handbook.WEB / "data.js").read_text(encoding="utf-8")
    required = (
        '"id":"annotations-revision-notice","key":"","title":"关于英文《Official Annotations》中规则引用编号的校订说明"',
        "部分中文注释中的规则编号会有意与英文 Official Annotations PDF 不同",
        "下表完整记录目前确认的 23 处编号差异",
        "| 23 | 18.15「走步违例后的比赛恢复」标题 | 18.2.7 | 18.2.6 | 待校正 |",
        '"title":"飞盘精神"',
        '"title":"比赛开始"',
        '"title":"开盘"',
        '"title":"读秒"',
        '"title":"验盘（Check）"',
        '"title":"接盘队员与位置"',
        '"title":"攻防转换"',
        '"title":"犯规、违规和违例的示意"',
        '"title":"示意后的比赛继续"',
        '"title":"违规和违例"',
        '"title":"安全中断"',
    )
    missing = [value for value in required if value not in data]
    if missing:
        raise ValueError(f"校订网页内容缺失：{missing}")

    notice = annotation_revision_notice()
    notice_missing = [
        paragraph["zh"]
        for paragraph in notice["paragraphs"]
        if paragraph["zh"] not in data
    ]
    if notice_missing:
        raise ValueError(f"规则引用编号校订说明未完整同步：{notice_missing}")

    if '"title":"修订公告"' in data:
        raise ValueError("网页仍在显示被替换的通用修订公告")
    if '"title":"目录"' in data or '"key":"Contents"' in data:
        raise ValueError("网页正文不应重复渲染目录；请使用网页侧栏目录")


if __name__ == "__main__":
    install_reviewed_overrides()
    handbook.main()
    normalize_quick_terms()
    validate()
    print("Reviewed Chinese web handbook build completed.")
