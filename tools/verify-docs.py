"""文档一致性检查：版本号、商店文案、帮助手册、README 是不是说的同一件事。

这一版动的全是文档，而文档里最容易出错的恰恰是**数字**：说明段说十七页、功能条说十七种、
帮助说 900 天、CHANGELOG 首条与 manifest 说同一个版本号 —— 任何一个留在旧数字上，读的人
看到的是一个自相矛盾的应用。所以这些断言一条条把数字钉住。

**为什么断言里全是数字**：`900`、`180`、`24`、`16` 在 14 种语言里写法都一样，而"最长"、
"Longest"、"Sechzehn" 各不相同。用数字当锚，一份断言能管住 14 份文件；用词当锚，就得
写 14 份同义词表，而那个表本身也会过时。

不启真机：这些是文本文件，读一遍就知道对不对。
"""

import importlib.util
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

sys.path.insert(0, str(REPO / "tools"))

import listingtext  # noqa: E402

# 帮助手册章节序号（0 起），**推出来的，不是抄下来的**。
#
# 三个页面章问导航要：章节顺序就是导航顺序，往中间插一章会让它后面每一章整体后移一位，
# 而抄在下面的数字不会跟着动 —— 1.0.8.0 加了「市值历程」这一章，写死的 23 从此指向
# 「动画背景」，于是那条断言开始说「数据章写着 900 而不是 640」，而它抱怨的那一章根本
# 不是数据章。用 `chapter_of` 问，同一个数字由导航自己算。
#
# 数据章不是页面，导航里没有它，所以按它在文件末尾的位置取：它永远是倒数第三章，而往
# 中间插多少章都不影响这一点。负数索引直接喂给 `chapter_bullets`。
CH_CANDLE = listingtext.chapter_of("NavCandle")
CH_VOLUME = listingtext.chapter_of("NavStockVolume")
CH_CAP = listingtext.chapter_of("NavMarketCap")
CH_DATA = -3

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


def this_version_news():
    """「此版本的新增功能」那一栏，从**本版那个 port 脚本**里取。

    那一栏每次发版整段换掉（历史留在 CHANGELOG.md），所以「本版说什么」的事实来源是
    `tools/port-store-listing-<版本>.py`，不是这个文件。这里按路径把它加载进来取那张表 ——
    自己再列一遍「本版要说的四件事」，就是给同一件事留了第二份答案，而两份答案对不上的
    时候，看的人只会以为是某一侧写错了字。

    **脚本名从 manifest 的版本号算，不写死**：曾经写死成 `…-1060.py`，版本号前进到
    1.0.7.0 之后它去比上一版那一份，于是十四条里红四条（而且红的那四条看着像是某几种
    语言的文案漏改）。同一个病第四次犯，就是因为每一处都在「这回就用这个号」的时候
    顺手写进去了。

    （脚本名带连字符，不能当模块名 import；**且不要顺手调它的 main**。）
    """
    manifest = MANIFEST.read_text(encoding="utf-8")
    hit = re.search(r'Version="(\d+)\.(\d+)\.(\d+)\.(\d+)"', manifest)

    if hit is None:
        raise SystemExit("manifest 里读不到版本号，算不出本版那个 port 脚本的名字")

    # 1.0.6.0 -> 1060，四段全拼（不是前三段：那样会算出 106）。
    tag = "".join(hit.group(i) for i in (1, 2, 3, 4))
    script = REPO / "tools" / ("port-store-listing-%s.py" % tag)

    if not script.exists():
        raise SystemExit("本版那个 port 脚本不在：%s（manifest 是 %s）"
                         % (script, hit.group(0)))

    saved = sys.argv
    sys.argv = [sys.argv[0]]

    try:
        spec = importlib.util.spec_from_file_location(
            "port_store_listing_" + tag, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.argv = saved

    return module.NEWS


def previous_version_news():
    """上一版那一栏说什么，从**上一版那个 port 脚本**取。

    版本号不写死：从 CHANGELOG 的版本序列里取第二新的那个（最新的那条是本版）。这一栏每次
    发版整段换掉，所以「本版这一句和上一版逐字相同」只有一个解释 —— 那一栏根本没换。

    判据曾以「那一栏里有没有出现页面名」当代理指标：上一版那一栏是一页一页数过来的，所以
    页面名在 = 旧文案还在。1.0.11.0 把它打回原形 —— 那一版修的正是三个页面上的同一件事，
    点名是对的，而代理指标把「点名」读成了「没换」。**真正要防的是这一栏没换，那就直接比
    上一版那一栏**：代理指标会失效，直接比不会。

    上一版那个脚本可能没有留下来（比如那一版不是这样发的），那就跳过而不是判红 —— 这一条
    防的是没换，不是防档案不全。
    """
    versions = re.findall(r"^## (\d+)\.(\d+)\.(\d+)\.(\d+)",
                          CHANGELOG.read_text(encoding="utf-8"), re.M)

    if len(versions) < 2:
        return None

    # 与 this_version_news() 同一套算法：四段全拼。
    tag = "".join(versions[1])
    script = REPO / "tools" / ("port-store-listing-%s.py" % tag)

    if not script.exists():
        return None

    saved = sys.argv
    sys.argv = [sys.argv[0]]

    try:
        spec = importlib.util.spec_from_file_location(
            "port_store_listing_prev_" + tag, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.argv = saved

    return module.NEWS


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

    NEWS = this_version_news()
    PREV = previous_version_news()

    for n, lang in enumerate(LANGS):
        _, start, end = secs[n]
        items = bullets(lines, start, end)

        # 一页一条，所以这个数字**跟着页数走**：加一页就要回来改这里，那正是它该有的摩擦。
        # 清单是历来一次次上架时追加出来的顺序，所以新的一页追加在末尾 —— 末尾那条也因此
        # 换了页。（1.0.5.0 之前这一条是「十六条 / 最后一条是持有胜率」；第十七页债市固收
        # 从来没进过商店文案，直到那一版；第十八页市值历程同样是在它已经在应用里之后才由
        # `port-store-listing-caphistory.py` 补进来的。）
        check(f"{lang} 说明段是十八条", len(items) == 18, f"{len(items)} 条")

        if items:
            last = page_name(lang, "NavCapHistory")
            check(f"{lang} 最后一条是市值历程",
                  lines[items[-1]].startswith(f"• {last}"),
                  lines[items[-1]][:40])

            # 倒数第二条还在债市固收：追加不动前面的顺序，所以第十七页被第十八页顶开一位，
            # 而不是被换掉。
            before = page_name(lang, "NavBondRace")
            check(f"{lang} 倒数第二条仍是债市固收",
                  len(items) < 2 or lines[items[-2]].startswith(f"• {before}"),
                  lines[items[-2]][:40] if len(items) > 1 else "（只有一条）")

        # 「此版本的新增功能」：本版要写在里面，上一版那一页一页数的旧文案不能还在。
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            check(f"{lang} 有小标题", False)
            continue

        at = subs[1] + 1

        while at < end and not lines[at].strip():
            at += 1

        body = lines[at]

        check(f"{lang} 新增功能与本版那份文案逐字一致", body == NEWS[lang],
              f"{len(body)} 字" if body == NEWS[lang]
              else f"文案 {len(body)} 字 / 脚本 {len(NEWS[lang])} 字")

        # 反过来看一遍：这一栏是**换**不是加，所以它不能和上一版那一栏是同一句。判据曾数
        # 页面名当代理指标，1.0.11.0 把它打回原形（见 previous_version_news 的注释）——
        # 本版点名是对的，直接比上一版那一栏才是这一条真正要说的事。
        check(f"{lang} 新增功能不是上一版那一句",
              PREV is None or body != PREV[lang],
              "与上一版逐字相同（那一栏没换）" if PREV and body == PREV[lang] else "")
        check(f"{lang} 新增功能不超过 1500 字", len(body) <= 1500, f"{len(body)} 字")

    # 上一版那句"新增八个图表页"式的旧文案，中英文各断一次足够：这一栏是**换**不是加，
    # 上一版一页一页数的那句留在里面，就和"十七大图表页"并排自相矛盾。
    text = "\n".join(lines)
    check("中文里不再有「本版新增八个图表页」", "本版新增八个图表页" not in text)
    check("中文里不再有「本版新增第八个图表页」", "本版新增第八个图表页" not in text)
    check("英文里不再有 Eight new chart pages", "Eight new chart pages" not in text)
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


def chapter_index_checks():
    """章节序号必须是**推出来的**，不是抄下来的。

    插进第十七页之后，`port-store-listing-pages.py` 里那行 `CHAPTERS = [8, 9, 10, 11, 12, 13]`
    和 whatsnew 里那八个括号里的数字全体错位一位 —— 商店文案会把「债市固收」的首句挂到
    「回撤与修复」头上，14 种语言全错，而每一句单独看都通顺。所以这里钉住两件事：
    导航里每一个页面项都解得出来，且解出来的序号是**连续的一段**，从领头章节之后开始。
    """
    sys.path.insert(0, str(REPO / "tools"))
    import listingtext

    order = listingtext.nav_order()
    got = [listingtext.chapter_of(key) for key in order]

    # 不写「手册正好 26 章」—— 末尾那些非页面的章随时会加。要断的是页面章都落在手册里。
    chapters = len(sections((HELP / "help-en-US.md").read_text(encoding="utf-8-sig")))
    check("最后一页的章节仍落在手册里", got[-1] < chapters,
          f"末页第 {got[-1]} 章 / 共 {chapters} 章")

    check("每一页解出的章节序号是连续的一段",
          got == list(range(listingtext.LEADING_CHAPTERS,
                            listingtext.LEADING_CHAPTERS + len(order))),
          str(got))

    check("第十七页接在大类资产之后",
          listingtext.chapter_of("NavBondRace") == listingtext.chapter_of("NavAssetRace") + 1)

    # 那两个商店脚本的清单本身也得还指得着真页面（写错 AutomationId 时 chapter_of 会抛）。
    for key in ("NavMarketCap", "NavAhPremium", "NavExtremeDays", "NavFxCorridor",
                "NavIndexRace", "NavAssetRace", "NavDrawdown", "NavHoldOdds"):
        check(f"商店文案还指得着 {key}", listingtext.chapter_of(key) >= 0)


def nav_name_checks():
    """侧边栏里两页不能叫同一个名字 —— 而这真的发生过。

    「市值历程」刚加进来时，五种语言（pt-BR / tr / ru / ja / ko）的导航名是照各语言习惯
    缩出来的，结果和上一页「市值榜」**逐字相同**。代价有两层：用户分不出两个不同的页面；
    更麻烦的是商店清单那个脚本按「清单里有没有以这一页名字开头的条目」判重，而日文的
    「時価総額レース」正是以「時価総額」开头 —— 于是第十八页那一条被静默跳过，脚本还报
    「已最新」。读出 UML 那样无害的重复，代价是这一条本该被拒绝却一路绿灯。
    """
    for lang in LANGS:
        root = ET.parse(STRINGS / lang / "Resources.resw").getroot()
        said = {}

        for entry in root.findall("data"):
            name = entry.get("name") or ""

            if not name.startswith("Nav") or not name.endswith(".Content"):
                continue

            word = (entry.find("value").text or "").strip()
            said.setdefault(word, []).append(name[:-len(".Content")])

        twin = {word: keys for word, keys in said.items() if len(keys) > 1}

        check(f"{lang} 导航里没有两页同名", not twin,
              "、".join(f"{w}（{ks}）" for w, ks in twin.items()) if twin else "")


def word_of(count):
    """页数写成英文单词的样子 —— README 用单词写页数，不用阿拉伯数字。

    **为什么把这个数由导航算出来**：写死的「十七」在加第十九页那天照样是绿的，而它读的那个
    文件说的已经不是事实 —— 这份脚本里别的锚差不多都已经是算出来的，这个不能是例外。
    """
    words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
             "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
    assert 0 < count < len(words), count
    return words[count]


def readme_checks():
    text = README.read_text(encoding="utf-8")

    # 页数从导航问（`nav_order` 认 `x:Uid`，所以帮助与设置都不算进去）。
    pages = len(listingtext.nav_order())
    word = word_of(pages)

    check(f"README 说清了共 {pages} 页", f"{word} pages" in text)
    check(f"README 的页数清单标题写着 {pages}", f"## The {word} pages" in text)
    check(f"README 里不再有「{pages - 1} 页」的说法",
          f"{word_of(pages - 1)} pages" not in text and
          f"The {word_of(pages - 1)} pages" not in text)
    check("README 说到 make-icons.py", "make-icons.py" in text)
    check("README 说到 PathIcon 的包围盒", "bounding box" in text)


def main():
    version_checks()
    listing_checks()
    help_checks()
    chapter_index_checks()
    nav_name_checks()
    readme_checks()
    print(f"\n通过 {len(PASSED)} 项，失败 {len(FAILED)} 项")

    if FAILED:
        for name in FAILED:
            print(f"  × {name}")

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
