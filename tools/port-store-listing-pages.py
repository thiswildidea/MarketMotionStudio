"""把商店文案的「十大图表页」补成十六页 —— 14 种语言。

应用早就是十六页了，而说明段还停在十页：后加的六页（极端交易日、汇率走廊、指数长跑、
大类资产、回撤与修复、持有胜率）从来没进过商店文案。这次补上。

**描述不另写，从帮助手册里取**：每一页的说明在 14 份 help-*.md 里早就各有一句，那是
项目自己翻的、和界面一致的说法；再手写一遍 14 种语言，只会得到 14 句各写各的。所以脚本
读那六章的首句，去掉 markdown、截到句号，作为这一页的说明。

页面名也不写死：从各语言的 resw 里取导航用的那个名字，商店文案和界面就必须叫同一个东西。

幂等：标题、列表、功能条三处各自先认一遍"已经改过了"再动手。
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"
HELP = REPO / "src" / "MarketMotionStudio" / "Assets" / "Help"
STRINGS = REPO / "src" / "MarketMotionStudio" / "Strings"

# 后加的六页，按导航顺序。前面十页的顺序是历史上一次次上架时追加出来的，不动。
PAGES = ["NavExtremeDays", "NavFxCorridor", "NavIndexRace",
         "NavAssetRace", "NavDrawdown", "NavHoldOdds"]

# 帮助手册里的章节序号（0 起，25 章在 14 种语言里同顺序）。
CHAPTERS = [8, 9, 10, 11, 12, 13]

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 标题里的"十"→"十六"。各语言各自的词，改错了标题就变成"十六页图表十页"。
HEADING = {
    "zh-Hans": ("十大图表页", "十六大图表页"),
    "zh-Hant": ("十大圖表頁", "十六大圖表頁"),
    "en-US": ("Ten chart pages", "Sixteen chart pages"),
    "ja": ("10 つのチャートページ", "16 つのチャートページ"),
    "ko": ("10가지 차트 페이지", "16가지 차트 페이지"),
    "de": ("Zehn Diagrammseiten", "Sechzehn Diagrammseiten"),
    "fr": ("Dix pages de graphiques", "Seize pages de graphiques"),
    "it": ("Dieci pagine di grafici", "Sedici pagine di grafici"),
    "es": ("Diez páginas de gráficos", "Dieciséis páginas de gráficos"),
    "pt-BR": ("Dez páginas de gráficos", "Dezesseis páginas de gráficos"),
    "pl": ("Dziesięć stron wykresów", "Szesnaście stron wykresów"),
    "cs": ("Deset stránek s grafy", "Šestnáct stránek s grafy"),
    "ru": ("Десять страниц с графиками", "Шестнадцать страниц с графиками"),
    "tr": ("On grafik sayfası", "On altı grafik sayfası"),
}

# 功能条里"十种图表"→"十六种图表"。只改数字词，后面六个名字靠追加。
FEATURE = {
    "zh-Hans": ("十种图表", "十六种图表"),
    "zh-Hant": ("十種圖表", "十六種圖表"),
    "en-US": ("Ten charts", "Sixteen charts"),
    "ja": ("10 種類のチャート", "16 種類のチャート"),
    "ko": ("10가지 차트", "16가지 차트"),
    "de": ("Zehn Diagramme", "Sechzehn Diagramme"),
    "fr": ("Dix graphiques", "Seize graphiques"),
    "it": ("Dieci grafici", "Sedici grafici"),
    "es": ("Diez gráficos", "Dieciséis gráficos"),
    "pt-BR": ("Dez gráficos", "Dezesseis gráficos"),
    "pl": ("Dziesięć wykresów", "Szesnaście wykresów"),
    "cs": ("Deset grafů", "Šestnáct grafů"),
    "ru": ("Десять графиков", "Шестнадцать графиков"),
    "tr": ("On grafik", "On altı grafik"),
}

# 合并换行时不留空格的：中文与日文（韩文的词间有空格，换行处吞掉就粘成一团了）。
NO_SPACE = ("zh-Hans", "zh-Hant", "ja")
# 句号用「。」的：中文、日文、韩文之外都用 "."。
CJK_STOP = ("zh-Hans", "zh-Hant", "ja", "ko")
# 中文那条用双破折号、前后不留空；其余语言用一个破折号、前后各留一个空格 ——
# 已有的十条就是这么写的，新加的六条不能看着像另一种文件。
DASH = {"zh-Hans": "——", "zh-Hant": "——"}
# 功能条里名字之间的分隔符。
COMMA = {"zh-Hans": "、", "zh-Hant": "、", "ja": "、", "ko": "、"}


def page_name(lang, key):
    """这一页在界面上叫什么（resw 里导航项的名字）。"""
    import xml.etree.ElementTree as ET

    root = ET.parse(STRINGS / lang / "Resources.resw").getroot()

    for entry in root.findall("data"):
        if entry.get("name") == key + ".Content":
            return entry.find("value").text or ""

    raise KeyError(f"{lang}: 没有 {key}.Content")


def first_sentence(lang, index):
    """帮助手册某一章的第一句 —— 洗干净，当作这一页的说明。"""
    text = (HELP / f"help-{lang}.md").read_text(encoding="utf-8-sig")
    body = re.split(r"(?m)^## ", text)[1:][index]
    lines = body.split("\n")[1:]
    picked = []

    for line in lines:
        if not line.strip():
            if picked:
                break
            continue
        picked.append(line.strip())

    joiner = "" if lang in NO_SPACE else " "
    para = joiner.join(picked)
    para = para.replace("**", "").replace("![", "").strip()

    # 截到第一个句号。中日韩用「。」，其余用 ". " 或末尾的 "."。
    if lang in CJK_STOP:
        cut = para.find("。")

        if cut > 0:
            para = para[:cut + 1]
    else:
        hit = re.search(r"\.\s", para)

        if hit:
            para = para[:hit.start() + 1]
        elif para.endswith("."):
            pass
        else:
            cut = para.find(".")

            if cut > 0:
                para = para[:cut + 1]

    # 已有的十条都不带句号，新加的六条也不带。
    para = para.strip()

    if para.endswith("。") or para.endswith("."):
        para = para[:-1].strip()

    return para


def dash_of(sample):
    """这一语言自己用的那条破折号。

    德语那一段写的是 "–"（短），英文写的是 "—"（长）—— 抄哪一段的规矩由那段自己说了算，
    所以从它已有的第一条里取，而不是替十四种语言挑一个。
    """
    for ch in sample:
        if ch in "–—―−":
            return ch

    return "—"


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 这个文件是 CRLF。插进去的新行也必须跟着 CRLF，否则同一份文件里两种行尾。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        names = [page_name(lang, key) for key in PAGES]
        comma = COMMA.get(lang, ", ")
        done = []

        # 1) 说明段：在列表末尾追加六条
        bullets = [i for i in range(start, end) if lines[i].startswith("• ")]

        if len(bullets) < 10:
            print(f"× {lang}: 说明段只有 {len(bullets)} 条")
            return 1

        # 破折号要等列表算出来再取：它抄的是这一段自己已有的那一条。
        dash = DASH.get(lang) or f" {dash_of(lines[bullets[0]])} "
        at = bullets[-1]

        # 标题在列表**前面**，所以要在插入之前认清楚：插进去的六条会顶掉"往回找第一行"
        # 这种定位办法。
        title = at

        while lines[title].lstrip().startswith("•"):   # 跳过整条列表
            title -= 1

        while not lines[title].strip():                # 再跳过列表与标题之间的空行
            title -= 1

        if not any(lines[i].startswith(f"• {names[0]}") for i in bullets):
            for name, index in zip(names, CHAPTERS):
                at += 1
                lines.insert(at, f"• {name}{dash}{first_sentence(lang, index)}")

            changed += 1
            done.append("说明段 +6")

            # 插入把这一段撑长了六行，段尾的边界必须重算 —— 否则段末的"产品功能"
            # 那些行会落到边界外面，看上去就像这一语言没有功能条。
            heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
            start = heads[n]
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)

        # 2) 标题：十 → 十六
        old, new = HEADING[lang]

        if old in lines[title]:
            lines[title] = lines[title].replace(old, new)
            changed += 1
            done.append("标题")
        elif new not in lines[title]:
            print(f"× {lang}: 标题行「{lines[title]}」里既没有 {old!r} 也没有 {new!r}")
            return 1

        # 3) 产品功能条：十种 → 十六种，末尾补六个名字
        old, new = FEATURE[lang]
        hit = [i for i in range(start, end) if lines[i].startswith("- ") and old in lines[i]]

        if hit:
            lines[hit[0]] = lines[hit[0]].replace(old, new) + comma + comma.join(names)
            changed += 1
            done.append("功能条")
        elif not any(lines[i].startswith("- ") and new in lines[i] for i in range(start, end)):
            print(f"× {lang}: 功能条里找不到 {old!r}")
            return 1

        # 段号会因为插入而位移，所以按标题重新定位一次。
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: {' / '.join(done) or '（已是最新）'}")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
