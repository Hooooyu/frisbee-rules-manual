"""Build the standalone Chinese WFDF web handbook from the approved PDF sources."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
ASSETS = WEB / "assets"
REVIEWED_RULES_PATH = ROOT / "WFDF团队飞盘规则2025-2028_中文校订整合版.md"
REVIEWED_APPENDIX_PATH = Path(r"C:\Users\HOOOOYU\Downloads\WFDF团队飞盘规则2025-2028_附录v2.0_中文校订整合版.md")
REVIEWED_ANNOTATIONS_PATH = Path(r"C:\Users\HOOOOYU\Downloads\WFDF团队飞盘规则2025-2028_官方注释_中文校订整合版.md")
TRANSLATION_CACHE_PATH = ROOT / "tmp" / "web-translation-cache.json"
LEGACY_CACHE_PATH = ROOT / "tmp" / "layout" / "cache.json"
TRANSLATIONS: dict[str, str] = {}

DOCUMENTS = (
    {
        "id": "rules",
        "label": "主规则",
        "title": "WFDF 极限飞盘规则",
        "subtitle": "2025-2028",
        "effective": "2025 年 1 月 1 日生效",
        "source": "WFDF-Rules-of-Ultimate-2025-2028.pdf",
        "download": "downloads/WFDF-极限飞盘规则-2025-2028-中文译本.pdf",
        "kind": "rules",
    },
    {
        "id": "appendix",
        "label": "附录 v2.0",
        "title": "WFDF 极限飞盘规则附录",
        "subtitle": "Appendix v2.0",
        "effective": "2026 年 1 月 1 日生效",
        "source": "WFDF-Rules-of-Ultimate-2025-2028-Appendix-v2.0.pdf",
        "download": "downloads/WFDF-极限飞盘规则-附录-v2.0-中文译本.pdf",
        "kind": "appendix",
    },
    {
        "id": "annotations",
        "label": "官方注释",
        "title": "WFDF 官方注释",
        "subtitle": "Official Annotations",
        "effective": "2026 年 6 月 1 日生效",
        "source": "WFDF-Rules-of-Ultimate-2025-2028-Official-Annotations.pdf",
        "download": "downloads/WFDF-极限飞盘规则-官方注释-中文译本.pdf",
        "kind": "annotations",
    },
    {
        "id": "decision",
        "label": "判定流程图",
        "title": "极限飞盘规则判定流程图",
        "subtitle": "Decision Diagrams",
        "effective": "与 2025-2028 主规则配套阅读",
        "source": "WFDF-Rules-of-Ultimate-2025-2028-Decision-Diagrams.pdf",
        "download": "downloads/WFDF-极限飞盘规则-判定流程图-中文转写.pdf",
        "kind": "diagram",
        "diagram": "decision",
    },
    {
        "id": "pull",
        "label": "发盘图",
        "title": "极限飞盘规则发盘图",
        "subtitle": "Pull Diagrams",
        "effective": "与 2025-2028 主规则第 7 条配套阅读",
        "source": "WFDF-Rules-of-Ultimate-2025-2028-Pull-Diagrams.pdf",
        "download": "downloads/WFDF-极限飞盘规则-发盘图-中文转写.pdf",
        "kind": "diagram",
        "diagram": "pull",
    },
)

DIAGRAM_PAGES = {
    "decision": (
        ("图 1", "发盘落点判定", "根据飞盘是否被触碰、是否落在界内或出界，以及是否叫砖位，确认恢复比赛的枢轴位置。"),
        ("图 2", "接盘者犯规", "接盘者叫犯规后的完成、攻守转换与回传持盘者判定。"),
        ("图 3", "标记者犯规：已传盘", "标记者犯规且已尝试传盘时，依据是否影响比赛决定继续或检查。"),
        ("图 4", "标记者犯规：未传盘", "标记者犯规且未尝试传盘时的比赛状态与 stall 计数恢复。"),
        ("图 5", "持盘者犯规", "持盘者犯规后的继续比赛、回传及 stall 计数判定。"),
        ("图 6", "盯人违例", "盯人违例和持盘者呼叫违规时的纠正与停赛程序。"),
        ("图 7", "走步", "走步呼叫后的枢轴点纠正、传盘结果与 stall 计数处理。"),
        ("图 8", "阻挡", "阻挡呼叫是否影响比赛、队员回位与继续比赛的判定。"),
    ),
    "pull": (
        ("图 1", "发盘直接落界外", "发盘未先落在比赛场地时，后方或侧方出界的可选枢轴位置示例。"),
        ("图 2", "发盘落地后滚出界外", "飞盘先落地后滚出界外时，按首次越过边界线的位置继续。"),
        ("图 3", "发盘留在界内或被界内接住", "展示发盘落地后留在界内、触碰后滚出界外，以及被界内接住时的典型枢轴位置。"),
        ("图 4", "界外接住发盘", "进攻方在界外接住发盘的其余典型情况。"),
    ),
}


def main_rule_figure() -> dict[str, str]:
    """Extract official Figure I for the main rules."""
    target = ASSETS / "figures"
    target.mkdir(parents=True, exist_ok=True)
    original = target / "rules-field-original.jpg"
    pdf = fitz.open(ROOT / "WFDF-Rules-of-Ultimate-2025-2028.pdf")
    image = pdf.extract_image(pdf[2].get_images(full=True)[0][0])
    original.write_bytes(image["image"])
    return {
        "after": "2.7.",
        "description": "Figure I：比赛场地尺寸与分区（WFDF 英文原图）。",
        "image": "assets/figures/rules-field-original.jpg",
        "sourceImage": "assets/figures/rules-field-original.jpg",
        "alt": "图 1：极限飞盘比赛场地尺寸与分区示意图",
    }

MAIN_TITLES = {
    "Introduction": "简介",
    "1": "比赛精神",
    "2": "比赛场地",
    "3": "装备",
    "4": "回合、得分与比赛",
    "5": "队伍",
    "6": "开始比赛",
    "7": "发盘",
    "8": "比赛状态",
    "9": "stall 计数",
    "10": "检查",
    "11": "出界",
    "12": "接盘者与站位",
    "13": "攻守转换",
    "14": "得分",
    "15": "犯规、违例与违规的呼叫",
    "16": "呼叫后的继续比赛",
    "17": "犯规",
    "18": "违例与违规",
    "19": "安全暂停",
    "20": "暂停",
    "Definitions": "术语定义",
    "Legal License": "许可",
}

APPENDIX_TITLES = {
    "Introduction": "简介",
    "A1": "比赛场地",
    "A2": "装备",
    "A3": "比赛开始",
    "A4": "比赛时长",
    "A5": "时间限制",
    "A6": "混合组别",
    "A7": "队伍",
    "A8": "语言",
    "A9": "竞技比赛",
    "A10": "非队员提供建议",
    "A11": "使用技术设备",
    "A12": "犯规与违例的呼叫",
    "A13": "比赛精神暂停",
    "A14": "赛事技术暂停",
    "B1": "名单",
    "B2": "组别",
    "B3": "排名标准与同分决胜",
    "B4": "恶劣天气规则",
    "B5": "暂停或取消的比赛",
    "B6": "比赛官员的职责",
    "C1": "目的",
    "C2": "深色队服",
    "C3": "浅色队服",
    "C4": "颜色要求",
    "C5": "号码",
    "C6": "可选要素",
    "C7": "内搭衣物",
    "D1": "队伍参赛资格 - 通则",
    "D2": "队员参赛资格",
    "D3": "队员资格争议",
    "D4": "参赛人数限制",
    "D5": "年龄组别",
    "E1": "国家队赛事种子排位",
    "E2": "俱乐部赛事种子排位",
    "E3": "分组排位",
    "E4": "赛事比赛日程",
    "E5": "参赛席位",
    "E6": "赛事积分",
    "E7": "赛事日程限制",
    "E8": "赛事积分表",
    "F1": "手势的目的",
    "F2": "手势的使用",
    "G1": "知识共享署名 4.0",
    "H1": "致谢",
}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00ad", "")).strip()


def clean_zh(text: str) -> str:
    """Apply the terminology decisions recorded in WFDF-规则核查问题记录.md."""
    changes = (
        ("危险的玩耍和攻击行为", "危险行为和攻击性行为"),
        ("要求反对派队员通过；和", "要求对方队员传盘；"),
        ("Ultimate", "极限飞盘"),
        ("玩家", "队员"),
        ("游戏精神", "比赛精神"),
        ("游戏", "比赛"),
        ("发球", "发盘"),
        ("拉盘", "发盘"),
        ("拉力", "发盘"),
        ("控球手", "持盘者"),
        ("控球权", "持盘权"),
        ("球门线", "得分线"),
        ("球门", "得分"),
        ("中央区域", "中区"),
        ("中心区域", "中区"),
        ("周界线", "边界线"),
        ("周边线", "边界线"),
        ("计分", "得分"),
        ("分数", "回合"),
        ("比赛状况", "比赛状态"),
        ("安全停车", "安全暂停"),
        ("精神停止活动", "比赛精神暂停"),
        ("违规行为和违规行为", "违例与违规"),
        ("犯规和违规", "违例与违规"),
        ("拨打电话", "呼叫"),
        ("打电话", "呼叫"),
        ("通话", "呼叫"),
        ("旅行", "走步"),
        ("跨骑", "跨立"),
        ("记分违规", "标记违例"),
        ("球队", "队伍"),
        ("拉车人", "发盘者"),
        ("拉车团队", "发盘队伍"),
        ("拉车前", "发盘前"),
        ("拉车", "发盘"),
        ("拉动", "发盘"),
        ("拉扯", "发盘"),
        ("抛拉", "发盘"),
        ("拖延计数", "stall 计数"),
        ("停止计数", "stall 计数"),
        ("记分犯规", "标记违例"),
        ("盯人犯规", "标记违例"),
        ("走球", "走步"),
        ("走球犯规", "走步违例"),
        ("中枢脚", "枢轴脚"),
        ("中枢点", "枢轴点"),
        ("罚球线", "枢轴点"),
        ("控球队伍", "持盘队伍"),
        ("控球", "持盘"),
        ("投掷手", "持盘者"),
        ("投掷者", "持盘者"),
        ("传盘手", "持盘者"),
        ("选手", "队员"),
        ("牌手", "队员"),
        ("制服", "队服"),
        ("球员", "队员"),
        ("判罚", "呼叫"),
        ("宣判", "呼叫"),
        ("跟注", "呼叫"),
        ("呼叫给", "呼叫"),
        ("线标记", "场地标志物"),
        ("每个点", "每个回合"),
        ("个目标", "分"),
    )
    for old, new in changes:
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("。 ", "。")
    text = text.replace(
        "在每个回合期间，每个队伍将最多放置七(7)个队员，最少放置五(5)个队员。",
        "每个回合期间，每支队伍最多派出七(7)名队员、至少五(5)名队员上场。",
    )
    text = text.replace(
        "在得分得分之后，在队伍发出发盘准备就绪信号之前，队伍可以进行无限次替换。",
        "得分后、队伍为发盘发出准备就绪信号前，队伍可以不限次数换人。",
    )
    text = text.replace("一名队长和一个比赛精神队长", "一名队长和一名比赛精神队长")
    text = text.replace("队伍队长", "队长").replace("队伍比赛精神队长", "比赛精神队长")
    text = text.replace("每节比赛", "每个回合").replace("进攻方上的一名队员", "一名进攻队员")
    text = text.replace("发盘者和一名发盘者员", "发盘者和一名进攻队员")
    text = text.replace("防守方向进攻方", "防守方向进攻方")
    text = text.replace("每分以进球得分结束", "每个回合以得分结束")
    text = text.replace("每个回合。", "每个回合进行")
    text = text.replace("为了发盘", "为发盘")
    text = text.replace("半场时间", "半场休息")
    text = text.replace("八 (8) 分。", "八 (8) 分时开始。")
    text = text.replace("球门", "得分")
    text = text.replace("极限赛", "极限飞盘比赛")
    text = text.replace("传球", "传盘")
    text = text.replace("传递", "传盘")
    text = text.replace("完成传球", "完成传盘")
    text = text.replace("普通比赛", "标准比赛")
    text = text.replace("进攻端区", "进攻得分区")
    text = text.replace("防守端区", "防守得分区")
    text = text.replace("拥有飞盘", "持盘")
    text = text.replace("飞盘权", "持盘权")
    text = text.replace("投掷动作", "传盘动作")
    text = text.replace("被阻挡", "受到阻挡")
    text = re.sub(r"\s+([，。:：；、])", r"\1", text)
    text = re.sub(r"([，。:：；、])\s+", r"\1", text)
    text = re.sub(r"\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+", "", text)
    text = text.replace(
        "5.1.在每个回合期间，每个队伍将最多放置七(7)个队员，最少放置五(5)个队员。",
        "5.1. 每个回合期间，每支队伍最多派出七(7)名队员、至少五(5)名队员上场。",
    )
    text = text.replace(
        "5.2.每个队伍必须指定一名队长和一个比赛精神队长来代表队伍。",
        "5.2. 每个队伍必须指定一名队长和一名比赛精神队长代表队伍。",
    )
    text = text.replace(
        "5.3.在得分得分之后，在队伍发出发盘准备就绪信号之前，队伍可以进行无限次替换。",
        "5.3. 得分后、队伍为发盘发出准备就绪信号前，队伍可以不限次数换人。",
    )
    text = re.sub(r"((?:[A-H]?\d+)(?:\.\d+)+)。(?!\d)", r"\1.", text)
    text = re.sub(r"((?:[A-H]?\d+)(?:\.\d+)+\.)(?=[\u4e00-\u9fff])", r"\1 ", text)
    return text


def reviewed_main_rules() -> tuple[dict[str, str], dict[str, str]]:
    """Load the reviewed main rules, keyed strictly by their WFDF rule numbers."""
    markdown = REVIEWED_RULES_PATH.read_text(encoding="utf-8")
    titles: dict[str, str] = {}
    rules: dict[str, str] = {}
    order: list[str] = []
    current_section: str | None = None
    unnumbered: dict[str, list[str]] = {"Introduction": [], "Definitions": [], "Legal License": []}

    def plain(text: str) -> str:
        text = text.strip().replace("**", "").replace("`", "")
        return f"• {text[2:]}" if text.startswith("- ") else text

    for raw in markdown.splitlines():
        line = raw.strip()
        heading = re.match(r"^# (\d+)\.\s*(.+)$", line)
        if heading:
            current_section = heading.group(1)
            titles[current_section] = plain(heading.group(2))
            continue
        if line == "# 引言":
            current_section = "Introduction"
            titles[current_section] = "引言"
            continue
        if line.startswith("# 定义"):
            current_section = "Definitions"
            titles[current_section] = plain(line.removeprefix("# "))
            continue
        if line.startswith("# 法律许可"):
            current_section = "Legal License"
            titles[current_section] = plain(line.removeprefix("# "))
            continue

        numbered_heading = re.match(r"^## (\d+(?:\.\d+)+)\.\s*(.+)$", line)
        numbered_rule = re.match(r"^\*\*(\d+(?:\.\d+)+)\.\s*(?:\*\*\s*)?(.+?)(?:\*\*)?$", line)
        match = numbered_heading or numbered_rule
        if match:
            number, text = match.groups()
            if number in rules:
                raise ValueError(f"校订稿规则编号重复：{number}")
            rules[number] = f"{number}. {plain(text)}"
            order.append(number)
            continue

        if current_section in unnumbered and line and not line.startswith(">") and line != "**——正文结束——**":
            unnumbered[current_section].append(plain(line))

    for key, lines in unnumbered.items():
        rules[key] = "\n".join(lines)
    rules["__order__"] = "\n".join(order)
    return titles, rules


def reviewed_appendix_rules() -> tuple[dict[str, str], dict[str, str]]:
    """Load the reviewed appendix, keyed strictly by WFDF appendix rule number."""
    markdown = REVIEWED_APPENDIX_PATH.read_text(encoding="utf-8")
    titles: dict[str, str] = {}
    rules: dict[str, str] = {}
    order: list[str] = []
    rule_keys: list[str] = []
    unnumbered: dict[str, list[str]] = {}
    current_section: str | None = None
    last_rule: str | None = None
    skip_signal_details = False

    def plain(text: str) -> str:
        text = text.strip().replace("**", "").replace("`", "")
        return f"• {text[2:]}" if text.startswith("- ") else text

    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line.startswith(">") or line.startswith("*注："):
            continue

        if line == "# 引言":
            current_section, last_rule, skip_signal_details = "Introduction", None, False
            titles[current_section] = "引言"
            continue

        chapter = re.match(r"^# 附录 ([A-H])：\s*(.+)$", line)
        if chapter:
            letter, title = chapter.groups()
            current_section, last_rule, skip_signal_details = f"appendix-{letter.lower()}", None, False
            titles[current_section] = title
            continue

        section = re.match(r"^## ([A-F]\d+)\.\s*(.+)$", line)
        if section:
            current_section, title = section.groups()
            titles[current_section] = plain(title)
            last_rule = None
            continue

        if line == "## 手势 1–24":
            skip_signal_details = True
            last_rule = None
            continue

        if skip_signal_details:
            continue

        if line.startswith("#"):
            if current_section in {"appendix-g", "appendix-h"}:
                unnumbered.setdefault(current_section, []).append(plain(line.lstrip("# ")))
            continue

        numbered = re.match(r"^\*\*([A-F]\d+(?:\.\d+)*)\.\*\*\s*(.+)$", line)
        if numbered:
            number, text = numbered.groups()
            suffix = 2
            key = number
            while key in rules:
                key = f"{number}#{suffix}"
                suffix += 1
            rules[key] = f"{number}. {plain(text)}"
            order.append(number)
            rule_keys.append(key)
            last_rule = key
            continue

        if current_section is None:
            continue
        if last_rule:
            rules[last_rule] = f"{rules[last_rule]}\n{plain(line)}"
        else:
            unnumbered.setdefault(current_section, []).append(plain(line))

    for key, lines in unnumbered.items():
        rules[key] = "\n".join(lines)
    rules["__order__"] = "\n".join(order)
    rules["__rule_keys__"] = "\n".join(rule_keys)
    return titles, rules


def reviewed_annotations() -> tuple[dict[str, str], dict[str, object]]:
    """Load reviewed annotations by their exact chapter and annotation number."""
    markdown = REVIEWED_ANNOTATIONS_PATH.read_text(encoding="utf-8")
    titles: dict[str, str] = {}
    content: dict[str, object] = {"Introduction": [], "Principles": []}
    current_section: str | None = None
    current_number: str | None = None
    started = False

    def plain(text: str) -> str:
        text = text.strip().replace("**", "").replace("`", "")
        return f"• {text[2:]}" if text.startswith("- ") else text

    for raw in markdown.splitlines():
        line = raw.strip()
        if line == "# 引言":
            started = True
            current_section, current_number = "Introduction", None
            titles[current_section] = "引言（Introduction）"
            continue
        if not started or not line or line.startswith(">") or line == "---":
            continue
        if line == "# 官方注释":
            current_section, current_number = None, None
            continue
        if line == "# 原则":
            current_section, current_number = "Principles", None
            titles[current_section] = "原则（Principles）"
            continue

        chapter = re.match(r"^# (\d+)\.\s*(.+)$", line)
        if chapter:
            current_section, current_number = chapter.groups()[0], None
            titles[current_section] = MAIN_TITLES.get(current_section, plain(chapter.groups()[1]))
            content.setdefault(current_section, {})
            continue

        annotation = re.match(r"^## (\d+\.\d+)\.\s*(.+)$", line)
        if annotation:
            if current_section is None or not current_section.isdigit():
                raise ValueError(f"官方注释编号缺少章节：{line}")
            current_number, title = annotation.groups()
            section = content.setdefault(current_section, {})
            if current_number in section:
                raise ValueError(f"官方注释编号重复：{current_number}")
            section[current_number] = {"title": plain(title), "body": []}
            continue

        if current_section is None or line.startswith("#"):
            continue
        if current_number is None:
            content.setdefault(current_section, []).append(plain(line))
        else:
            content[current_section][current_number]["body"].append(plain(line))

    for section in content.values():
        if isinstance(section, list):
            while section and section[-1].startswith("——《WFDF 团队飞盘规则"):
                section.pop()
        elif isinstance(section, dict):
            for item in section.values():
                while item["body"] and item["body"][-1].startswith("——《WFDF 团队飞盘规则"):
                    item["body"].pop()

    return titles, content


def cached_translation(source: str) -> str:
    return ""


GLOSSARY = (
    ("Spirit of the Game", "比赛精神"),
    ("spirit captain", "比赛精神队长"),
    ("playing field", "比赛场地"),
    ("field of play", "比赛场地"),
    ("central zone", "中区"),
    ("defending end zone", "防守得分区"),
    ("attacking end zone", "进攻得分区"),
    ("end zones?", "得分区"),
    ("goal lines?", "得分线"),
    ("perimeter lines?", "边界线"),
    ("brick marks?", "砖块标记"),
    ("out-of-bounds", "界外"),
    ("in-bounds", "界内"),
    ("offensive players?", "进攻队员"),
    ("defensive players?", "防守队员"),
    ("non-players?", "非队员"),
    ("team-mates?", "队友"),
    ("game officials?", "比赛官员"),
    ("official game discs?", "官方比赛用盘"),
    ("stall counts?", "stall 计数"),
    ("pivot points?", "枢轴点"),
    ("pivot locations?", "枢轴位置"),
    ("time-outs?", "暂停"),
    ("turnovers?", "攻守转换"),
    ("receivers?", "接盘者"),
    ("throwers?", "持盘者"),
    ("markers?", "标记者"),
    ("pullers?", "发盘者"),
    ("offence", "进攻方"),
    ("defence", "防守方"),
    ("possessions?", "持盘权"),
    ("fouls?", "犯规"),
    ("infractions?", "违例"),
    ("violations?", "违规"),
    ("travels?", "走步"),
    ("picks?", "阻挡"),
    ("checks?", "检查"),
    ("calls?", "呼叫"),
    ("pulls?", "发盘"),
    ("points?", "回合"),
    ("goals?", "得分"),
    ("discs?", "飞盘"),
    ("players?", "队员"),
        ("teams?", "队伍"),
    ("game", "比赛"),
    ("legal position", "合法位置"),
    ("ground contact", "地面接触"),
    ("hand signals?", "手势"),
)


def protect_terms(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    for index, (english, chinese) in enumerate(GLOSSARY):
        token = f"__WFDFTERM{index:02d}__"
        pattern = re.compile(rf"\b{english}\b", re.IGNORECASE)
        if pattern.search(text):
            text = pattern.sub(token, text)
            replacements[token] = chinese
    return text, replacements


def translate_text(source: str, cache: dict[str, str], legacy: dict[str, str]) -> str:
    key = hashlib.sha1(source.encode("utf-8")).hexdigest()
    if key in cache:
        return cache[key]
    protected, replacements = protect_terms(source)
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + urllib.parse.quote(protected)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part and part[0])
            for token, chinese in replacements.items():
                translated = translated.replace(token, chinese)
            cache[key] = clean_zh(translated)
            return cache[key]
        except Exception:
            time.sleep(attempt + 1)
    return clean_zh(legacy.get(key, source))


def translate_all(sources: set[str]) -> dict[str, str]:
    cache = json.loads(TRANSLATION_CACHE_PATH.read_text(encoding="utf-8")) if TRANSLATION_CACHE_PATH.exists() else {}
    legacy = json.loads(LEGACY_CACHE_PATH.read_text(encoding="utf-8")) if LEGACY_CACHE_PATH.exists() else {}
    missing = [source for source in sources if hashlib.sha1(source.encode("utf-8")).hexdigest() not in cache]
    if missing:
        print(f"translating {len(missing)} logical rule units", flush=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            for source, translated in zip(missing, pool.map(lambda value: translate_text(value, cache, legacy), missing)):
                cache[hashlib.sha1(source.encode("utf-8")).hexdigest()] = translated
        TRANSLATION_CACHE_PATH.parent.mkdir(exist_ok=True)
        TRANSLATION_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def pdf_lines(page: fitz.Page) -> list[tuple[float, float, str]]:
    raw = []
    for block in page.get_text("dict").get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"] if span["text"]).strip()
            if text:
                raw.append((line["bbox"][0], line["bbox"][1], norm(text)))
    # PyMuPDF exposes adjacent spans as separate lines when a rule number is
    # printed in a narrow column (``1.6.1.`` + its text). Merge same-baseline
    # fragments so headings and numbered rules remain single logical lines.
    merged: list[tuple[float, float, str]] = []
    for x, y, text in sorted(raw, key=lambda item: (item[1], item[0])):
        if merged and abs(y - merged[-1][1]) < 1.5 and x - (merged[-1][0] + 1) < 260:
            prev_x, prev_y, prev_text = merged[-1]
            merged[-1] = (prev_x, prev_y, norm(f"{prev_text} {text}"))
        else:
            merged.append((x, y, text))
    return merged


def section_heading(meta: dict, x: float, text: str) -> tuple[str, str] | None:
    if meta["kind"] == "rules":
        if x < 80 and text in {"Definitions", "Legal License", "Introduction"}:
            return text, MAIN_TITLES[text]
        match = re.match(r"^(\d+)\.\s+(.+)$", text)
        if x < 80 and match and match.group(1) in MAIN_TITLES:
            return match.group(1), MAIN_TITLES[match.group(1)]
    if meta["kind"] == "appendix":
        match = re.match(r"^Appendix ([A-H]):\s+(.+)$", text)
        if x < 80 and match:
            titles = {"A": "WFDF 比赛附加规则", "B": "WFDF 赛事附加规则", "C": "队服要求", "D": "WFDF 参赛资格与名单指南", "E": "种子、赛程与赛事席位", "F": "手势", "G": "许可条款", "H": "致谢"}
            return f"appendix-{match.group(1).lower()}", titles[match.group(1)]
        match = re.match(r"^([A-H]\d+)\.\s+(.+)$", text)
        if x < 80 and match:
            return match.group(1), APPENDIX_TITLES.get(match.group(1), match.group(2))
        if x < 80 and text == "Introduction":
            return "Introduction", "简介"
    if meta["kind"] == "annotations":
        if x < 130 and text == "Introduction":
            return "Introduction", "简介"
        if x < 130 and text == "Principles":
            return "Principles", "原则"
        # This is a repeated page header, not a content section.
        if text == "Official Annotations":
            return None
        match = re.match(r"^(\d+)\.\s+(.+)$", text)
        if x < 130 and match:
            return match.group(1), MAIN_TITLES.get(match.group(1), match.group(2))
    return None


def is_rule_start(meta: dict, x: float, text: str) -> bool:
    if meta["kind"] == "rules":
        # PDF often places the rule number in its own indented line, with no
        # trailing space (e.g. ``1.6.1.``). Treat that as a new logical unit.
        return x >= 55 and bool(re.match(r"^\d+(?:\.\d+)+\.(?:\s|$)", text))
    if meta["kind"] == "appendix":
        return x >= 80 and bool(re.match(r"^[A-H]\d+(?:\.\d+)*\.(?:\s|$)", text))
    if meta["kind"] == "annotations":
        return x >= 90 and bool(re.match(r"^\d+\.\d+(?:\s|$)", text))
    return False


def source_sections(meta: dict) -> list[dict]:
    pdf = fitz.open(ROOT / meta["source"])
    sections: list[dict] = []
    current: dict | None = None
    unit: str | None = None

    def flush() -> None:
        nonlocal unit
        if current is not None and unit:
            current["sourceUnits"].append(unit.strip())
        unit = None

    for page_index, page in enumerate(pdf):
        if meta["kind"] in {"appendix", "annotations"} and page_index == 0:
            # Appendix/annotation first page is cover/contents only. The main
            # rules first page also contains the real Introduction, so retain it.
            continue
        for x, y, text in pdf_lines(page):
            if y < 48 or y > page.rect.height - 42 or text == "Contents" or "................................................................" in text:
                continue
            if meta["kind"] == "rules" and page_index == 0 and y < 540:
                continue
            if text.startswith("WFDF Rules of Ultimate") or text.startswith("Official Version") or text.startswith("- APPENDIX") or text.startswith("Figure ") or (meta["kind"] == "annotations" and text == "Official Annotations"):
                continue
            text = re.sub(r"\s+\d+\s+(?=(?:[A-H]?\d+\.\d+\.))", " ", text)
            text = re.sub(r"\s+\d+\.\s+(?=[A-Z])", " ", text)
            heading = section_heading(meta, x, text)
            if heading:
                flush()
                key, title = heading
                current = {"id": f"{meta['id']}-{key.lower().replace(' ', '-')}", "key": key, "title": title, "sourceUnits": []}
                sections.append(current)
                continue
            if current is None:
                continue
            if is_rule_start(meta, x, text):
                flush()
                unit = text
            elif unit:
                unit = f"{unit} {text}"
            else:
                unit = text
    flush()
    return [
        section for section in sections
        if section["sourceUnits"] or (meta["kind"] == "appendix" and section["key"].startswith("appendix-"))
    ]


def translate_source_sections(meta: dict, sections: list[dict]) -> dict:
    if meta["id"] == "rules":
        reviewed_titles, reviewed = reviewed_main_rules()
    elif meta["id"] == "appendix":
        reviewed_titles, reviewed = reviewed_appendix_rules()
    elif meta["id"] == "annotations":
        reviewed_titles, reviewed = reviewed_annotations()
    else:
        reviewed_titles, reviewed = {}, {}
    if reviewed:
        if meta["id"] == "annotations":
            source_order = [(section["key"], annotation_number(unit)) for section in sections for unit in section["sourceUnits"] if section["key"].isdigit()]
            reviewed_order = [(section, number) for section, values in reviewed.items() if section.isdigit() for number in values]
            if source_order != reviewed_order:
                raise ValueError(f"官方注释与英文 PDF 编号或顺序不一致；英文={source_order}；校订={reviewed_order}")
            reviewed_key_by_source_index = iter(source_order)
        else:
            source_order = [rule_number(unit) for section in sections for unit in section["sourceUnits"] if rule_number(unit)]
            reviewed_order = reviewed.pop("__order__").splitlines()
            reviewed_keys = reviewed.pop("__rule_keys__", "\n".join(reviewed_order)).splitlines()
            if source_order != reviewed_order:
                missing = sorted(set(source_order) - set(reviewed_order))
                extra = sorted(set(reviewed_order) - set(source_order))
                raise ValueError(f"校订稿与英文主规则编号或顺序不一致；缺失={missing}；多出={extra}")
            if len(source_order) != len(reviewed_keys):
                raise ValueError("校订稿规则映射数量不一致")
            reviewed_key_by_source_index = iter(reviewed_keys)
    else:
        reviewed_key_by_source_index = iter(())
    rendered = []
    for section in sections:
        paragraphs = []
        for source in section.pop("sourceUnits"):
            if meta["id"] == "annotations":
                number = annotation_number(source)
                if section["key"] in {"Introduction", "Principles"}:
                    reviewed_paragraphs = reviewed[section["key"]]
                else:
                    reviewed_section, reviewed_number = next(reviewed_key_by_source_index)
                    if (section["key"], number) != (reviewed_section, reviewed_number):
                        raise ValueError(f"官方注释映射错位：英文 {section['key']}.{number}，校订 {reviewed_section}.{reviewed_number}")
                    item = reviewed[reviewed_section][reviewed_number]
                    reviewed_paragraphs = [f"{reviewed_number}. {item['title']}", *item["body"]]
                paragraphs.extend({"zh": text, "en": source if index == 0 else "", "page": None} for index, text in enumerate(reviewed_paragraphs))
                continue
            number = rule_number(source)
            translated = reviewed[next(reviewed_key_by_source_index) if number else section["key"]] if reviewed else TRANSLATIONS.get(hashlib.sha1(source.encode("utf-8")).hexdigest(), source)
            reviewed_paragraphs = translated.splitlines() if reviewed and not number else [translated]
            paragraphs.extend({"zh": text, "en": source if index == 0 else "", "page": None} for index, text in enumerate(reviewed_paragraphs))
        rendered_section = {**section, "title": reviewed_titles.get(section["key"], section["title"]), "paragraphs": paragraphs}
        if meta["id"] == "rules" and section["key"] == "2":
            rendered_section["figure"] = main_rule_figure()
        rendered.append(rendered_section)
    return {**meta, "original": f"downloads/{meta['source']}", "sections": rendered}


RULE_START = re.compile(r"(?<![\w.])((?:[A-H]?\d+)(?:\.\d+)*\.)\s*")


def split_rules(text: str) -> list[str]:
    """Split a PDF text block at actual rule numbers, never at visual line breaks."""
    starts = list(RULE_START.finditer(text))
    if not starts:
        return [text] if text else []
    prefix = text[:starts[0].start()].strip()
    parts = [prefix] if prefix else []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        parts.append(text[match.start():end].strip())
    return [part for part in parts if part]


def rule_number(text: str) -> str | None:
    match = RULE_START.match(text)
    return match.group(1).rstrip(".") if match else None


ANNOTATION_START = re.compile(r"^(\d+\.\d+)\s+")


def annotation_number(text: str) -> str | None:
    match = ANNOTATION_START.match(text)
    return match.group(1) if match else None


def matching_rule_parts(source: str, translated: str) -> list[tuple[str, str]]:
    """Keep source and translation paired after splitting a multi-rule PDF block."""
    sources, translated_parts = split_rules(source), split_rules(translated)
    source_numbers = [rule_number(part) for part in sources]
    translated_numbers = [rule_number(part) for part in translated_parts]
    if len(sources) == len(translated_parts) and source_numbers == translated_numbers:
        return list(zip(sources, translated_parts))
    return [(source, translated)]


def append_to_paragraph(paragraph: dict, zh: str, en: str, page_no: int) -> None:
    paragraph["zh"] = f"{paragraph['zh']}{zh}".strip()
    paragraph["en"] = f"{paragraph['en']} {en}".strip()
    paragraph["pageEnd"] = page_no


def add_rule_text(section: dict, source: str, translated: str, page_no: int) -> None:
    """Add a logical rule. Hard-wrapped PDF continuations join their preceding rule."""
    source, translated = source.strip(), translated.strip()
    if not source or not translated:
        return
    number = rule_number(source)
    paragraphs = section["paragraphs"]
    if number or not paragraphs:
        paragraphs.append({"zh": translated, "en": source, "page": page_no + 1, "pageEnd": page_no + 1})
    else:
        append_to_paragraph(paragraphs[-1], translated, source, page_no + 1)


def section_for(kind: str, raw: str) -> tuple[str | None, str | None, str]:
    """Return section key, human title, and source text left after a heading."""
    if raw.startswith("Introduction"):
        return "Introduction", MAIN_TITLES["Introduction"], raw.removeprefix("Introduction").strip()
    if kind == "rules":
        for heading in ("Definitions", "Legal License"):
            if raw.startswith(heading):
                return heading, MAIN_TITLES[heading], raw.removeprefix(heading).strip()
        match = re.fullmatch(r"(\d+)\.\s+.+", raw)
        if match and match.group(1) in MAIN_TITLES:
            return match.group(1), MAIN_TITLES[match.group(1)], ""
    if kind == "appendix":
        appendix_heading = re.fullmatch(r"Appendix ([A-H]):\s+(.+)", raw)
        if appendix_heading:
            key, english = appendix_heading.groups()
            titles = {
                "A": "WFDF 比赛附加规则",
                "B": "WFDF 赛事附加规则",
                "C": "队服要求",
                "D": "WFDF 参赛资格与名单指南",
                "E": "种子、赛程与赛事席位",
                "F": "手势",
                "G": "许可条款",
                "H": "致谢",
            }
            return f"appendix-{key.lower()}", titles[key], ""
        match = re.fullmatch(r"([A-H]\d+)\.\s+(.+)", raw)
        if match:
            key = match.group(1)
            return key, APPENDIX_TITLES.get(key, clean_zh(cached_translation(raw) or match.group(2))), ""
    if kind == "annotations":
        if raw in {"Official Annotations", "Principles"}:
            return raw, "官方注释" if raw == "Official Annotations" else "原则", ""
        match = re.fullmatch(r"(\d+)\.\s+.+", raw)
        if match and match.group(1) in MAIN_TITLES:
            key = match.group(1)
            return key, MAIN_TITLES[key], ""
    return None, None, raw


def split_top_level_appendix_sections(raw: str) -> list[str]:
    """PDF text blocks often place an A/B chapter heading after ordinary paragraphs."""
    return [part.strip() for part in re.split(r"(?=\b(?:Appendix [A-H]:|[A-H]\d+\.\s+[A-Z]))", raw) if part.strip()]


def strip_repeated_heading(text: str, title: str) -> str:
    return re.sub(rf"^{re.escape(title)}[：:、. ]*", "", text).strip()


def build_document(meta: dict) -> dict:
    if meta["kind"] == "diagram":
        return build_diagram_document(meta)
    return translate_source_sections(meta, source_sections(meta))


def build_diagram_document(meta: dict) -> dict:
    translated_pdf = fitz.open(ROOT / "output" / "pdf" / Path(meta["download"]).name)
    source_pdf = fitz.open(ROOT / meta["source"])
    target = ASSETS / "diagrams"
    target.mkdir(parents=True, exist_ok=True)
    sections = []
    for index, (key, title, description) in enumerate(DIAGRAM_PAGES[meta["diagram"]]):
        zh_page, en_page = translated_pdf[index], source_pdf[index]
        zh_name = f"{meta['id']}-{index + 1}.png"
        en_name = f"{meta['id']}-{index + 1}-original.png"
        zh_page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).save(target / zh_name)
        en_page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).save(target / en_name)
        zh_text = clean_zh(norm(zh_page.get_text()))
        en_text = norm(en_page.get_text())
        sections.append({
            "id": f"{meta['id']}-{index + 1}",
            "key": key,
            "title": title,
            "description": description,
            "keywords": zh_text,
            "sourceKeywords": en_text,
            "image": f"assets/diagrams/{zh_name}",
            "sourceImage": f"assets/diagrams/{en_name}",
            "alt": f"{meta['title']}{key}：{title}",
            "paragraphs": [],
        })
    return {**meta, "original": f"downloads/{meta['source']}", "sections": sections}


def copy_reading_files() -> None:
    """Keep the static site self-contained when served from the web directory."""
    downloads = WEB / "downloads"
    downloads.mkdir(exist_ok=True)
    for meta in DOCUMENTS:
        shutil.copy2(ROOT / meta["source"], downloads / meta["source"])
        translated = Path(meta["download"]).name
        shutil.copy2(ROOT / "output" / "pdf" / translated, downloads / translated)
    shutil.copy2(ROOT / "WFDF-规则核查问题记录.md", WEB / "规则核查问题记录.md")


def main() -> None:
    WEB.mkdir(exist_ok=True)
    copy_reading_files()
    shutil.rmtree(ASSETS / "diagrams", ignore_errors=True)
    raw_sections = {meta["id"]: source_sections(meta) for meta in DOCUMENTS if meta["kind"] != "diagram"}
    translation_sources = {unit for sections in raw_sections.values() for section in sections for unit in section["sourceUnits"]}
    global TRANSLATIONS
    TRANSLATIONS = translate_all(translation_sources)
    data = {
        "documents": [translate_source_sections(meta, raw_sections[meta["id"]]) if meta["kind"] != "diagram" else build_document(meta) for meta in DOCUMENTS],
        "terms": [
            ["发盘（pull）", "每半场开始及得分后，由防守方发出、用于开始比赛的飞盘。"],
            ["持盘者（thrower）", "当前持有飞盘的进攻队员，或在传盘结果确定前刚完成传盘的进攻队员。"],
            ["标记者（marker）", "可以对持盘者执行 stall 计数的防守队员。"],
            ["攻守转换（turnover）", "导致拥有持盘权的队伍改变的任何事件；不属于违例。"],
            ["检查（check）", "暂停后的恢复程序；恢复后比赛重新进入 live 状态。"],
            ["比赛精神（Spirit of the Game）", "极限飞盘的自主裁判基础：队员共同负责公平、规则与争议解决。"],
        ],
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    (WEB / "data.js").write_text(f"window.HANDBOOK_DATA={payload};\n", encoding="utf-8")
    print(f"Wrote {WEB / 'data.js'}: {len(payload):,} characters")


if __name__ == "__main__":
    main()
