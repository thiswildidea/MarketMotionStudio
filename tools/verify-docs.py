"""文档一致性检查：版本号、商店文案、帮助手册、README 是不是说的同一件事。

这一版动的全是文档，而文档里最容易出错的恰恰是**数字**：说明段说十六页、功能条说十六种、
帮助说 900 天、CHANGELOG 说 1.0.4.0、manifest 说 1.0.4.0 —— 任何一个留在旧数字上，读的人
看到的是一个自相矛盾的应用。所以这些断言一条条把数字钉住。

**为什么断言里全是数字**：`900`、`180`、`24`、`16` 在 14 种语言里写法都一样，而"最长"、
"Longest"、"Sechzehn" 各不相同。用数字当锚，一份断言能管住 14 份文件；用词当锚，就得
写 14 份同义词表，而那个表本身也会过时。

不启真机：这些是文本文件，读一遍就知道对不对。
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

REPO = pathlib.Path(__file__).resolve().parent.parent
STRINGS = REPO / "src" / "MarketMotionStudio" / "Strings"
HELP = REPO / "src" / "MarketMotionStudio" / "Assets" / "Help"
LISTING = REPO / "docs" / "store-listing.md"
CHANGELOG = REPO / "CHANGELOG.md"
README = REPO / "README.md"
MANIFEST = REPO / "src" / "MarketMotionStudio" / "Package.appxmanifest"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 帮助手册章节序号（0 起）。25 章在 14 种语言里同顺序。
# Chapter positions, which is to say positions in the navigation: the seventeenth page went in
# after the asset race, so every chapter after it — and every constant below that points at one —
# moved down by one. The headings are in fourteen languages, so a position is the only thing that
# can be asserted on.
CH_CANDLE, CH_VOLUME, CH_CAP, CH_DATA = 3, 4, 6, 23

PASSED = []
FAILED = []


def check(name, ok, detail=""):
    (PASSED if ok else FAILED).append(name)
    print(f"{'·' if ok else '×'} {name}" + (f" —— {detail}" if detail else ""))


def sections(text):
    """按 `## ` 切段，返回 [(标题, 起, 止)]。"""
    lines = text.split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    return [(lines[i][3:].strip(), i, heads[n + 1] if n + 1 < len(heads) else len(lines))
            for n, i in enumerate(heads)]


def bullets(lines, start, end, mark="• "):
    return [i for i in range(start, end) if lines[i].lstrip().startswith(mark.strip())]


def page_name(lang, key):
    root = ET.parse(STRINGS / lang / "Resources.resw").getroot()

    for entry in root.findall("data"):
        if entry.get("name") == key + ".Content":
            return entry.find("value").text or ""

    raise KeyError(key)


def chapter_bullets(lang, index):
    text = (HELP / f"help-{lang}.md").read_text(encoding="utf-8-sig")
    lines = text.split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
    start = heads[index]
    end = heads[index + 1] if index + 1 < len(heads) else len(lines)

    return [lines[i] for i in bullets(lines, start, end, "- ")]


def version_checks():
    """CHANGELOG 第一条与 manifest 必须是同一个号 —— 少做一步，版本号就对不上记录。"""
    manifest = MANIFEST.read_text(encoding="utf-8")
    hit = re.search(r'Version="(\d+\.\d+\.\d+\.\d+)"', manifest)
    check("manifest 里能读到版本号", hit is not None)
    version = hit.group(1)

    entries = re.findall(r"(?m)^## (\d+\.\d+\.\d+\.\d+) — ", CHANGELOG.read_text(encoding="utf-8"))
    check("CHANGELOG 第一条就是 manifest 里的号", bool(entries) and entries[0] == version,
          f"manifest {version} / CHANGELOG {entries[0] if entries else '（没有条目）'}")

    numbers = [tuple(int(p) for p in v.split(".")) for v in entries]
    check("条目按新到旧排", numbers == sorted(numbers, reverse=True), str(entries[:3]))
    check("第四段恒为 0", all(v[3] == 0 for v in numbers))
    check("1.0.4.0 在其中", "1.0.4.0" in entries)


def listing_checks():
    raw = LISTING.read_bytes()
    check("store-listing.md 不带 BOM", not raw.startswith(b"\xef\xbb\xbf"))
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    secs = sections("\n".join(lines))
    check("商店文案是 14 个语言段", len(secs) == 14, f"{len(secs)} 段")

    for n, lang in enumerate(LANGS):
        _, start, end = secs[n]
        items = bullets(lines, start, end)
        last = page_name(lang, "NavHoldOdds")

        # 一页一条，所以这个数字**跟着页数走**：第十七页「债市固收」落地之后这一版应当是
        # 十七条，而商店文案按惯例要等发版时才写（见 marketmotion-store-release），所以
        # 现在仍是十六。改动这一页时它不会红——它就是发版时要改的那个提醒点。
        check(f"{lang} 说明段是十六条", len(items) == 16, f"{len(items)} 条")

        if items:
            check(f"{lang} 最后一条是持有胜率",
                  lines[items[-1]].startswith(f"• {last}"),
                  lines[items[-1]][:40])

        # 「此版本的新增功能」：本版要写在里面，上一版那一页一页数的旧文案不能还在。
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            check(f"{lang} 有小标题", False)
            continue

        at = subs[1] + 1

        while at < end and not lines[at].strip():
            at += 1

        body = lines[at]
        check(f"{lang} 新增功能写着本版的 900 天", "900" in body, body[:40])
        check(f"{lang} 新增功能不超过 1500 字", len(body) <= 1500, f"{len(body)} 字")

    # 上一版那句"新增第八个图表页"式的旧文案，中英文各断一次足够。
    text = "\n".join(lines)
    check("中文里不再有「本版新增第八个图表页」", "本版新增第八个图表页" not in text)
    check("英文里不再有 an eighth chart page", "an eighth chart page" not in text)
    check("英文里不再有 a ninth chart page", "a ninth chart page" not in text)


def help_checks():
    """四章各有一句带数字的档位说明 —— 数字在所有语言里写法一致。"""
    for lang in LANGS:
        candle = chapter_bullets(lang, CH_CANDLE)
        check(f"{lang} K线章末条写着 10 年", bool(candle) and "10" in candle[-1],
              candle[-1][:40] if candle else "（没有 bullet）")

        vol = chapter_bullets(lang, CH_VOLUME)
        check(f"{lang} 成交量章末条写着 24 个月", bool(vol) and "24" in vol[-1],
              vol[-1][:40] if vol else "（没有 bullet）")

        cap = chapter_bullets(lang, CH_CAP)
        check(f"{lang} 市值榜章末条写着 180 期", bool(cap) and "180" in cap[-1],
              cap[-1][:40] if cap else "（没有 bullet）")

        data = chapter_bullets(lang, CH_DATA)
        check(f"{lang} 数据章写着 900 而不是 640",
              bool(data) and "900" in data[-1] and "640" not in data[-1],
              data[-1][:40] if data else "（没有 bullet）")


def readme_checks():
    text = README.read_text(encoding="utf-8")

    # 断「页数」而不是「出现过 sixteen 这个词」——自选上限也有十六（`three to sixteen racers`），
    # 所以旧写法在页数改成十七之后照样绿。加一页就要回来改这里，那正是它该有的摩擦。
    check("README 说清了共十七页", "seventeen pages" in text)
    check("README 的页数清单标题是十七", "## The seventeen pages" in text)
    check("README 里不再有「十六页」的说法", "sixteen pages" not in text and
          "The sixteen pages" not in text)
    check("README 说到 make-icons.py", "make-icons.py" in text)
    check("README 说到 PathIcon 的包围盒", "bounding box" in text)


def main():
    version_checks()
    listing_checks()
    help_checks()
    readme_checks()
    print(f"\n通过 {len(PASSED)} 项，失败 {len(FAILED)} 项")

    if FAILED:
        for name in FAILED:
            print(f"  × {name}")

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
