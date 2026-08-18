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


def annotation_front_matter() -> list[dict]:
    """Return the Chinese-only revision notice and contents before Introduction."""
    markdown = handbook.REVIEWED_ANNOTATIONS_PATH.read_text(encoding="utf-8")
    titles = {"Revision Notice": "修订公告", "Contents": "目录"}
    content: dict[str, list[str]] = {"Revision Notice": [], "Contents": []}
    current: str | None = None

    for raw in markdown.splitlines():
        line = raw.strip()
        if line == "# 修订公告":
            current = "Revision Notice"
            continue
        if line == "# 目录":
            current = "Contents"
            continue
        if line == "# 引言":
            break
        if current is None or not line or line.startswith("#"):
            continue
        if line.startswith(">"):
            line = line[1:].strip()
        if line:
            content[current].append(line.replace("**", "").replace("`", ""))

    sections = []
    for key in ("Revision Notice", "Contents"):
        if not content[key]:
            raise ValueError(f"官方注释前置章节缺失：{titles[key]}")
        sections.append(
            {
                "id": f"annotations-{key.lower().replace(' ', '-')}",
                "key": key,
                "title": titles[key],
                "paragraphs": [
                    {"zh": value, "en": "", "page": None}
                    for value in content[key]
                ],
            }
        )
    return sections


def install_reviewed_overrides() -> None:
    handbook.MAIN_TITLES.update(CANONICAL_MAIN_TITLES)
    original_translate = handbook.translate_source_sections

    def translate_source_sections(meta: dict, sections: list[dict]) -> dict:
        rendered = original_translate(meta, sections)
        if meta["id"] == "annotations":
            rendered["sections"] = [*annotation_front_matter(), *rendered["sections"]]
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
        '"title":"修订公告"',
        '"title":"目录"',
        "本项目为非官方中文阅读版",
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


if __name__ == "__main__":
    install_reviewed_overrides()
    handbook.main()
    normalize_quick_terms()
    validate()
    print("Reviewed Chinese web handbook build completed.")
