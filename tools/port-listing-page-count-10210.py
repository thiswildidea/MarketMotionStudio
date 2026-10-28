# -*- coding: utf-8 -*-
r"""把商店文案的页数从 30 校准到 31（14 语言，docs/store-listing.md）。

1.0.21.0 上架的新页是「持仓·大盘 双屏」——应用场景里的第三十一页，导航里排在
「实时持仓收益」之后、加密货币十一页之前。1.0.20.0 把页数从 25 校准到 30 时它还不存在，
所以它不在清单里。这一遍补三处：

- **页数行**（说明小节的「N 大图表页」）——30 → 31；
- **枚举行**（产品功能里的「N 种图表：……」）——计数词改 31，页名插在锚点页之后；
- **说明条目**（说明里的 • 清单）——新页一条，插在同一锚点之后。

**新条目的句子不手写**——商店里写的是帮助手册那一章的首句（`listingtext.first_sentence`），
标题用各语言 resw 的导航名；破折号照抄该语言已有条目（`listingtext.dash_of`）。锚点用
**结构**（`NavPortfolioPnl` 的导航名）而不是行数：14 语言的条目同构同序是项目铁律，
但行数会因条目长短而错觉。

幂等：跑第二遍应当是「改了 0 处」。store-listing.md 是 **CRLF 无 BOM**，剥掉 `\r`
比对，写回照原样。

用法：python tools\port-listing-page-count-10210.py
"""
import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

REPO = listingtext.HELP.parents[3]
LISTING = REPO / "docs" / "store-listing.md"

# 「N 大图表页」那一行。上一版是 30，本版 31。
INTRO = {
    "zh-Hans": ("三十大图表页：", "三十一大图表页："),
    "zh-Hant": ("三十大圖表頁：", "三十一大圖表頁："),
    "en-US": ("Thirty chart pages:", "Thirty-one chart pages:"),
    "ja": ("30 つのチャートページ：", "31 つのチャートページ："),
    "ko": ("30가지 차트 페이지:", "31가지 차트 페이지:"),
    "de": ("Dreißig Diagrammseiten:", "Einunddreißig Diagrammseiten:"),
    "fr": ("Trente pages de graphiques :", "Trente et une pages de graphiques :"),
    "it": ("Trenta pagine di grafici:", "Trentuno pagine di grafici:"),
    "es": ("Treinta páginas de gráficos:", "Treinta y una páginas de gráficos:"),
    "pt-BR": ("Trinta páginas de gráficos:", "Trinta e uma páginas de gráficos:"),
    "pl": ("Trzydzieści stron wykresów:", "Trzydzieści jeden stron wykresów:"),
    "cs": ("Třicet stránek s grafy:", "Třicet jedna stránek s grafy:"),
    "ru": ("Тридцать страниц с графиками:", "Тридцать одна страница с графиками:"),
    "tr": ("Otuz grafik sayfası:", "Otuz bir grafik sayfası:"),
}

# 产品功能里那条枚举的计数词：整条 `- N 图表：……`。
COUNT = {
    "zh-Hans": ("三十种图表", "三十一种图表"),
    "zh-Hant": ("三十種圖表", "三十一種圖表"),
    "en-US": ("Thirty charts", "Thirty-one charts"),
    "ja": ("30 種類のチャート", "31 種類のチャート"),
    "ko": ("30가지 차트", "31가지 차트"),
    "de": ("Dreißig Diagramme", "Einunddreißig Diagramme"),
    "fr": ("Trente graphiques", "Trente et une graphiques"),
    "it": ("Trenta grafici", "Trentuno grafici"),
    "es": ("Treinta gráficos", "Treinta y un gráficos"),
    "pt-BR": ("Trinta gráficos", "Trinta e um gráficos"),
    "pl": ("Trzydzieści wykresów", "Trzydzieści jeden wykresów"),
    "cs": ("Třicet grafů", "Třicet jeden grafů"),
    "ru": ("Тридцать графиков", "Тридцать один графиков"),
    "tr": ("Otuz grafik", "Otuz bir grafik"),
}

# 新页在导航里的位置：`NavBoard` 紧跟 `NavPortfolioPnl`，所以两处都插在它后面。
# 名字从 resw 取（HTML 转义 &amp; 还原成 &），不手写。
ANCHOR_KEY = "NavPortfolioPnl"
NEW_KEY = "NavBoard"

# 枚举行里个别语言写的是**短名**，与 resw 的导航名不同：英文那一串写的是
# "live P&L"（导航名 Live portfolio P&L）。照同样的方式，插进去的页名也不必降格，
# 写完整的样子——这一串里 "Extreme days"、"Currency corridors" 都是整名。
ENUM_ANCHOR = {
    "en-US": "live P&L",
}


def unescape(text):
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def bullet_title(line):
    """`• 标题<破折号>句子` 里的标题 —— 破折号那一刀之前的部分。"""
    hit = re.search(r"[–—―−]", line)

    return line[:hit.start()].strip() if hit else line.strip()


def insert_after_bullet(lines, index, title, sentence):
    """在 bullets[index] 之后插一条 `• 标题<破折号>句子`，破折号照抄该条自己的。"""
    # 破折号可能连着写（中文里是「——」），所以要吃掉**整串**，不能只取第一个。
    m = re.search(r"\s*[–—―−]+\s*", lines[index])
    sep = m.group(0) if m else " — "
    wanted = "• " + title + sep + sentence
    titles = [bullet_title(lines[i]) for i, _ in enumerate(lines) if lines[i].startswith("• ")]

    if any(t == "• " + title for t in titles):
        return lines, False

    lines[index + 1:index + 1] = [wanted]
    return lines, True


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    changed = 0
    index = listingtext.chapter_of(NEW_KEY)

    for lang in listingtext.LANGS:
        anchor = unescape(listingtext.page_name(lang, ANCHOR_KEY))
        title = unescape(listingtext.page_name(lang, NEW_KEY))
        sentence = listingtext.first_sentence(lang, index)

        m = re.search(rf"^## [^\n]*[（(]{re.escape(lang)}[）)][^\n]*\n", text, flags=re.M)

        if m is None:
            print(f"  ! {lang}: 语言段找不到")
            continue

        start = m.end()
        nxt = text.find("\n## ", start)
        end = len(text) if nxt < 0 else nxt
        section = text[start:end]
        original = section
        notes = []

        # 1) 页数行 30 → 31
        old, new = INTRO[lang]

        if old in section:
            section = section.replace(old, new, 1)
            notes.append("页数行")
        elif new not in section:
            print(f"  ! {lang}: 页数行既无旧也无新：{old!r}")

        # 2) 产品功能的枚举行：计数词 + 新页名（插在锚点页之后）。行按**新**计数词找，
        #    找新也找旧 —— 上一轮已经改过计数的语言，第二轮仍要走进去重插这段。
        old_word, new_word = COUNT[lang]
        lines = section.split("\n")
        hit = -1

        for i, line in enumerate(lines):
            if line.startswith("- ") and (new_word in line or old_word in line):
                hit = i
                break

        if hit < 0:
            print(f"  ! {lang}: 找不到枚举行（既无 {old_word!r} 也无 {new_word!r}）")
        else:
            if old_word in lines[hit]:
                lines[hit] = lines[hit].replace(old_word, new_word, 1)
                notes.append("枚举计数")

            # 枚举里的页名是该语言的行文形式：英文写 "live P&L"（小写）、俄文整串小写，
            # 俄文、捷克语等句子中间一律小写。所以大小写不敏感地找锚点，插进去的页名
            # 也跟着锚点自己的首字母大小写 —— 清单这一行的规矩由这一行自己说了算。
            probes = [anchor]

            if lang in ENUM_ANCHOR:
                probes.append(ENUM_ANCHOR[lang])

            m2 = None

            for probe in probes:
                m2 = re.search(re.escape(probe) + r"(\s*[,、・]\s*)", lines[hit], flags=re.IGNORECASE)

                if m2 is not None:
                    break

            if m2 is None:
                print(f"  ! {lang}: 枚举行里找不到锚点「{anchor}」")
            else:
                sep = m2.group(1)
                name = title if m2.group(0)[0].isupper() else title[0].lower() + title[1:]

                if re.search(r"[,、・]\s*" + re.escape(name) + r"\s*[,、・]", lines[hit]):
                    pass                               # 已经插过
                else:
                    lines[hit] = lines[hit][:m2.end()] + name + sep + lines[hit][m2.end():]
                    notes.append("枚举+新页")

        # 3) 说明里的 • 条目：新页一条，插在锚点条目之后
        bullets = [i for i, l in enumerate(lines) if l.startswith("• ")]

        if len(bullets) < 10:
            raise SystemExit(f"  ! {lang}: 条目只有 {len(bullets)} 条，结构对不上")

        at = -1

        for i in bullets:
            if bullet_title(lines[i]) == "• " + anchor:
                at = i
                break

        if at < 0:
            print(f"  ! {lang}: 说明条目里找不到锚点「{anchor}」")
        else:
            lines, did = insert_after_bullet(lines, at, title, sentence)

            if did:
                notes.append("+说明条目")

        section = "\n".join(lines)

        if section != original:
            text = text[:start] + section + text[end:]
            changed += 1
            print(f"  + {lang}: {'、'.join(notes)}")
        else:
            print(f"  = {lang}")

    if changed:
        LISTING.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))

    print(f"changed {changed} sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
