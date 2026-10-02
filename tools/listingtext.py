"""商店文案与帮助手册之间那几件共用的事。

两个注入脚本（`port-store-listing-pages.py`、`port-store-listing-whatsnew.py`）都要做同一件事：
**从各语言的帮助手册里取那一章的首句**，以及**从各语言的 resw 里取那一页在界面上叫什么**。
放在这里而不是各写一份，理由和渲染器里那些常量一样：同一段规则有两个副本，就有一个副本
会在某天被改对而另一个不会 —— 而这类文件的错法是「14 份里有 1 份措辞不同」，恰恰最不容易
看出来。
"""

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"
HELP = REPO / "src" / "MarketMotionStudio" / "Assets" / "Help"
STRINGS = REPO / "src" / "MarketMotionStudio" / "Strings"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 合并换行时不留空格的：中文与日文（韩文的词间有空格，换行处吞掉就粘成一团了）。
NO_SPACE = ("zh-Hans", "zh-Hant", "ja")

# 句号用「。」的：中文、日文、韩文之外都用 "."。
CJK_STOP = ("zh-Hans", "zh-Hant", "ja", "ko")


def page_name(lang, key):
    """这一页在界面上叫什么（resw 里导航项的名字）。"""
    import xml.etree.ElementTree as ET

    root = ET.parse(STRINGS / lang / "Resources.resw").getroot()

    for entry in root.findall("data"):
        if entry.get("name") == key + ".Content":
            return entry.find("value").text or ""

    raise KeyError(f"{lang}: 没有 {key}.Content")


def first_sentence(lang, index):
    """帮助手册某一章的第一句 —— 洗干净，当作这一页的说明。

    取的是**项目自己的翻译**：这一句在界面旁边也写着，商店文案再手写一遍 14 种语言，
    只会得到 14 句各写各的。
    """
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
