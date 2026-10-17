# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的说明段补到**第二十五页**、**七个加密页**。

应用里现在是二十五页、四个市场；加密货币从六个页面变成七个——本版加的「加密货币月度收益」
（NavCryptoMatrix）是第七个。这一版要把三处数字词同步过去：

- 说明段标题「二十四大图表页」→「二十五大图表页」（锚来自上轮的 crypto-pages.py）。
- 产品功能第一句「二十四种图表」→「二十五种图表」，并在末尾补上「加密货币月度收益」的名字。
- 说明段里「它自己有六页」的市场句 → 「七页」（逐语言只换那一个词，别处不动）。

**只换那一个词**，因为这份文案里「六页」出现在说明段的加密市场句、**也可能**出现在功能条的加密市场句
（繁中那一条写「自帶六頁」），两处都该变成七页，所以整段替换同一个词最稳，且幂等。

**不碰「此版本的新增功能」那一栏**——那一栏是换不是加，必须与 manifest、CHANGELOG 同一轮动，
留给 `port-store-listing-10180.py`。

数字词不在本脚本手写第二份：标题/功能词的锚来自 `port-store-listing-crypto-pages.py` 的
`HEADING`/`FEATURE` 两张表（二十四 / 二十四种图表），本脚本只写增量那一半（二十五 / 二十五种）。

定位与幂等：标题按整行替换（锚命中才换、否则报错）；功能条按整句替换（锚命中才换）；7 页那一条
按名字查重（已有就跳过）；「六/七页」按词替换。store-listing.md 是 **CRLF 无 BOM**，写完照原样写回。

用法：python tools\\port-store-listing-crypto-monthly.py      （跑第二遍应当是「改了 0 处」）
"""

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import listingtext as lt                                     # noqa: E402
from listingtext import LANGS, LISTING, page_name, chapter_of  # noqa: E402

# 上一轮的 owner：它是「页清单补到二十四」那件事的唯一事实来源（二十四 / 二十四种图表）。
_argv = sys.argv
sys.argv = [sys.argv[0]]

_spec = importlib.util.spec_from_file_location(
    "port_store_listing_crypto_pages",
    os.path.join(HERE, "port-store-listing-crypto-pages.py"))
_prev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prev)

sys.argv = _argv

assert sorted(_prev.HEADING) == sorted(LANGS), "上一轮的标题表缺语言"
assert sorted(_prev.FEATURE) == sorted(LANGS), "上一轮的功能条表缺语言"

# 这次补的第七个加密页，按导航顺序（章节号由 chapter_of 从 MainWindow.xaml 算出）。
PAGE = "NavCryptoMatrix"
EXPECTED = 24           # 补之前清单里应当正好二十四条（crypto-pages.py 补到的结果）。

# 目的地：二十四 → 二十五，二十四种 → 二十五种。锚是上一轮那两张表里的「二十四」，
# 所以这里只写增量那一半。
HEADING25 = {
    "zh-Hans": "二十五大图表页",
    "zh-Hant": "二十五大圖表頁",
    "en-US": "Twenty-five chart pages",
    "ja": "25 つのチャートページ",
    "ko": "25가지 차트 페이지",
    "de": "Fünfundzwanzig Diagrammseiten",
    "fr": "Vingt-cinq pages de graphiques",
    "it": "Venticinque pagine di grafici",
    "es": "Veinticinco páginas de gráficos",
    "pt-BR": "Vinte e cinco páginas de gráficos",
    "pl": "Dwadzieścia pięć stron wykresów",
    "cs": "Dvacet pět stránek s grafy",
    "ru": "Двадцать пять страниц с графиками",
    "tr": "Yirmi beş grafik sayfası",
}

FEATURE25 = {
    "zh-Hans": "二十五种图表",
    "zh-Hant": "二十五種圖表",
    "en-US": "Twenty-five charts",
    "ja": "25 種類のチャート",
    "ko": "25가지 차트",
    "de": "Fünfundzwanzig Diagramme",
    "fr": "Vingt-cinq graphiques",
    "it": "Venticinque grafici",
    "es": "Veinticinco gráficos",
    "pt-BR": "Vinte e cinco gráficos",
    "pl": "Dwadzieścia pięć wykresów",
    "cs": "Dvacet pět grafů",
    "ru": "Двадцать пять графиков",
    "tr": "Yirmi beş grafik",
}

# 说明段里「它自己有 N 页」那一个词：只换它，别处不动。
SIX2SEVEN = {
    "zh-Hans": ("六页", "七页"),
    "zh-Hant": ("六頁", "七頁"),
    "en-US": ("six pages", "seven pages"),
    "ja": ("六つのページ", "七つのページ"),
    "ko": ("여섯 개", "일곱 개"),
    "de": ("sechs eigene Seiten", "sieben eigene Seiten"),
    "fr": ("six pages", "sept pages"),
    "it": ("sei pagine", "sette pagine"),
    "es": ("seis páginas", "siete páginas"),
    "pt-BR": ("seis páginas", "sete páginas"),
    "pl": ("sześć własnych stron", "siedem własnych stron"),
    "cs": ("šest vlastních stránek", "sedm vlastních stránek"),
    "ru": ("шесть собственных страниц", "семь собственных страниц"),
    "tr": ("altı sayfa", "yedi sayfa"),
}

# 清单里中文用双破折号、前后不留空；其余语言用单破折号、前后各留一个空格
# （沿用 crypto-pages.py 的写法，新加的一条不能看着像另一种文件）。
DASH = {"zh-Hans": "——", "zh-Hant": "——"}
COMMA = {"zh-Hans": "、", "zh-Hant": "、", "ja": "、", "ko": "、"}

EXPECTED_BULLET = 24


def intro(lang, chapter):
    """这一章的开场段 —— 商店清单里那一条说明（取整段不取整句，见 crypto-pages.py）。"""
    text = (lt.HELP / f"help-{lang}.md").read_text(encoding="utf-8")
    body = re.split(r"(?m)^## ", text)[chapter + 1]
    lines = body.split("\n")[1:]
    at = 0

    while at < len(lines) and (not lines[at].strip() or lines[at].lstrip().startswith("![")):
        at += 1

    said = []

    while at < len(lines):
        line = lines[at].strip()

        if not line or line.startswith("- ") or line.startswith("• "):
            break

        said.append(line)
        at += 1

    joiner = "" if lang in ("zh-Hans", "zh-Hant", "ja") else " "
    said = re.sub(r"\*\*(.+?)\*\*", r"\1", joiner.join(said))

    return said.strip().rstrip("。．.").rstrip()


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

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
        done = []

        bullets = [i for i in range(start, end) if lines[i].startswith("• ")]

        if len(bullets) not in (EXPECTED_BULLET, EXPECTED_BULLET + 1):
            print(f"× {lang}: 说明段有 {len(bullets)} 条，应当是 {EXPECTED_BULLET} 或 {EXPECTED_BULLET + 1} 条")
            return 1

        # 标题在清单**前面**，插入清单前先认清楚。
        title = bullets[0]

        while lines[title].lstrip().startswith("•"):      # 跳过整条清单
            title -= 1

        while not lines[title].strip():                   # 清单与标题之间的空行
            title -= 1

        # 第七页那一条说明。
        name = page_name(lang, PAGE)

        if not any(lines[i].startswith(f"• {name}") for i in bullets):
            dash = DASH.get(lang) or f" {lt.dash_of(lines[bullets[0]])} "
            add = f"• {name}{dash}{intro(lang, chapter_of(PAGE))}"
            lines[bullets[-1] + 1:bullets[-1] + 1] = [add]
            changed += 1
            done.append("说明段 +1")
            heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
            start = heads[n]
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        else:
            done.append("（7 页已在）")

        # 标题：二十四 → 二十五。
        anchor = _prev.HEADING[lang]

        if anchor in lines[title]:
            lines[title] = lines[title].replace(anchor, HEADING25[lang])
            changed += 1
            done.append("标题")
        elif HEADING25[lang] not in lines[title]:
            print(f"× {lang}: 标题行「{lines[title]}」里既没有 {anchor!r} 也没有 {HEADING25[lang]!r}")
            return 1

        # 功能条：二十四种 → 二十五种，末尾补上第七页的名字。
        anchor = _prev.FEATURE[lang]
        hit = [i for i in range(start, end)
               if lines[i].startswith("- ") and anchor in lines[i]]

        if hit:
            comma = COMMA.get(lang, ", ")
            lines[hit[0]] = (lines[hit[0]].replace(anchor, FEATURE25[lang])
                             + comma + name)
            changed += 1
            done.append("功能条")
        elif not any(lines[i].startswith("- ") and FEATURE25[lang] in lines[i]
                     for i in range(start, end)):
            print(f"× {lang}: 功能条里找不到 {anchor!r}")
            return 1

        # 说明段加密市场句：六页 → 七页（只换那一个词）。
        # 整块里可能有不止一处「六页」（例如说明段市场句 + 功能条市场句都写了「六页」），
        # 必须把**所有**出现都换掉，否则第一遍换一处、第二遍换另一处，脚本就不幂等了。
        old, new = SIX2SEVEN[lang]
        replaced = False

        for i in range(start, end):
            if old in lines[i]:
                lines[i] = lines[i].replace(old, new)
                replaced = True

        if replaced:
            changed += 1
            done.append("市场句")
        elif new not in lines[title] and not any(new in lines[i] for i in range(start, end)):
            print(f"× {lang}: 找不到「{old}」")
            return 1

        print(f"· {lang}: {' / '.join(done)}")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
