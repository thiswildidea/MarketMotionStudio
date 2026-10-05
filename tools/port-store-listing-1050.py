# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）改到 1.0.5.0。

三处改动，每处都照 `port-store-listing-pages.py` / `port-store-listing-whatsnew.py` 已经
定下的做法：

1. **说明段的图表页清单补上第十七页（债市固收）**，标题与功能条从十六改成十七。这一页在
   应用里早已在、排在**大类资产之后**，只是从来没进过商店文案 —— 它不是本版才有的，但既然
   文案要写「十七页」，那一页就不能缺。清单是历史上一次次上架时追加出来的顺序，所以新的一
   页**追加在末尾**，不动前面的顺序。
2. **「此版本的新增功能」换掉**（这一栏是**换**不是加，历史留在 CHANGELOG.md）。1.0.5.0 要
   说的四件事：债市固收这一页、成交额页的自选篮、K线指定某一个交易日、持仓页最多六只对比。

**描述从帮助手册里取，不另写。** 债市、K线、持仓三章的开场句在 14 份 help-*.md 里早就有，
那是项目自己翻的、与界面一致的说法；再手写一遍只会得到 14 句各写各的。唯一例外是成交额那
一条：那一章的开场句讲的是「全市场成交额」，没有涵盖本版加进去的「自选篮」——所以那一条
是手写的，写在这里时一并写了 14 种语言。

**开场句不能用 `listingtext.first_sentence`。** 持仓与 K线两章的第一行是配图（
`![...](media/...)`），而它的 alt 文字正好是「这一页的全貌：…」——`first_sentence` 会把这句
当成那一章的开场。所以这里自己走：跳过标题行、空行与图片行，取第一行正文。

定位与幂等：标题/功能条按整行精确匹配（某语言的措辞与脚本不一致时会报错，而不是留下一个旧
数字）；「新增功能」比对整行；清单按页面名查重。store-listing.md 是 **CRLF**，写完照原样写回。

用法：python tools\\port-store-listing-1050.py      （跑第二遍应当 0 处改动）
"""

import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 取页面名与破折号，与另外两个 port 脚本共用一份规则。
from listingtext import HELP, LANGS, LISTING, dash_of, page_name  # noqa: E402

# 本版涉及的四页，按导航顺序。章节序号从导航推出，不写死 —— 往导航中间插一页，后面每一章
# 的序号都会后移，写死的序号会让说明挂到错的那章头上。
BOND = ("NavBondRace", 12)
TURNOVER = ("NavMarketTurnover", None)
CANDLE = ("NavCandle", 3)
POSITION = ("NavPosition", 18)

# 标题里的「十六」→「十七」。各语言各自的词，改错了标题就变成「十七大图表页十六页」。
HEADING = {
    "zh-Hans": ("十六大图表页", "十七大图表页"),
    "zh-Hant": ("十六大圖表頁", "十七大圖表頁"),
    "en-US": ("Sixteen chart pages", "Seventeen chart pages"),
    "ja": ("16 つのチャートページ", "17 つのチャートページ"),
    "ko": ("16가지 차트 페이지", "17가지 차트 페이지"),
    "de": ("Sechzehn Diagrammseiten", "Siebzehn Diagrammseiten"),
    "fr": ("Seize pages de graphiques", "Dix-sept pages de graphiques"),
    "it": ("Sedici pagine di grafici", "Diciassette pagine di grafici"),
    "es": ("Dieciséis páginas de gráficos", "Diecisiete páginas de gráficos"),
    "pt-BR": ("Dezesseis páginas de gráficos", "Dezessete páginas de gráficos"),
    "pl": ("Szesnaście stron wykresów", "Siedemnaście stron wykresów"),
    "cs": ("Šestnáct stránek s grafy", "Sedmnáct stránek s grafy"),
    "ru": ("Шестнадцать страниц с графиками", "Семнадцать страниц с графиками"),
    "tr": ("On altı grafik sayfası", "On yedi grafik sayfası"),
}

# 功能条里的「十六种图表」→「十七种图表」。只改数字词，新名字靠追加。
FEATURE = {
    "zh-Hans": ("十六种图表", "十七种图表"),
    "zh-Hant": ("十六種圖表", "十七種圖表"),
    "en-US": ("Sixteen charts", "Seventeen charts"),
    "ja": ("16 種類のチャート", "17 種類のチャート"),
    "ko": ("16가지 차트", "17가지 차트"),
    "de": ("Sechzehn Diagramme", "Siebzehn Diagramme"),
    "fr": ("Seize graphiques", "Dix-sept graphiques"),
    "it": ("Sedici grafici", "Diciassette grafici"),
    "es": ("Dieciséis gráficos", "Diecisiete gráficos"),
    "pt-BR": ("Dezesseis gráficos", "Dezessete gráficos"),
    "pl": ("Szesnaście wykresów", "Siedemnaście wykresów"),
    "cs": ("Šestnáct grafů", "Sedmnáct grafů"),
    "ru": ("Шестнадцать графиков", "Семнадцать графиков"),
    "tr": ("On altı grafik", "On yedi grafik"),
}

# 「此版本的新增功能」的引导句。
OPEN = {
    "zh-Hans": "本版新增一个图表页，并给三页各加了新能力：",
    "zh-Hant": "本版新增一個圖表頁，並給三頁各加了新能力：",
    "en-US": "One new chart page, and three pages that gained something new:",
    "ja": "このバージョンでは新しいチャートページが 1 つ加わり、既存の 3 ページにも新しい機能が入りました：",
    "ko": "이 버전에서는 새 차트 페이지 하나가 추가되고, 기존 세 페이지에도 새 기능이 들어갔습니다:",
    "de": "Eine neue Diagrammseite, und drei Seiten, die etwas Neues bekamen:",
    "fr": "Une nouvelle page de graphiques, et trois pages qui gagnent quelque chose de nouveau :",
    "it": "Una nuova pagina di grafici, e tre pagine che guadagnano qualcosa di nuovo:",
    "es": "Una página de gráficos nueva, y tres páginas que ganan algo nuevo:",
    "pt-BR": "Uma nova página de gráficos, e três páginas que ganham algo novo:",
    "pl": "Jedna nowa strona wykresów i trzy strony, które zyskały coś nowego:",
    "cs": "Jedna nová stránka s grafy a tři stránky, které získaly něco nového:",
    "ru": "Одна новая страница с графиками и три страницы, которые получили что-то новое:",
    "tr": "Bir yeni grafik sayfası ve yeni bir şey kazanan üç sayfa:",
}

# 成交额那一条：**唯一手写的一条**。那一章的开场句讲的是「全市场成交额是怎么算出来的」，
# 说不到本版加进去的那个篮子；而手册里讲到篮子的那一条是一整段，取不出一句能单独站着的话。
BASKET = {
    "zh-Hans": "可以把自选清单里的几只加成一个篮子，点一下名称就把它加进或移出合计",
    "zh-Hant": "可以把自選清單裡的幾隻加成一個籃子，點一下名稱就把它加進或移出合計",
    "en-US": "can add several picks from your own list into one basket — clicking a name includes "
             "it in the total or leaves it out",
    "ja": "自分のリストから複数の銘柄を一つのかごにまとめられます。名前をクリックすれば合計に"
          "加えたり外したりできます",
    "ko": "관심 목록의 여러 종목을 하나의 바구니로 묶을 수 있습니다. 이름을 클릭하면 합계에"
          " 넣거나 뺄 수 있습니다",
    "de": "kann mehrere Einträge aus Ihrer eigenen Liste zu einem Korb zusammenfassen — ein Klick "
          "auf den Namen nimmt ihn in die Summe auf oder lässt ihn weg",
    "fr": "peut réunir plusieurs titres de votre propre liste en un panier — un clic sur le nom "
          "l'ajoute au total ou l'en retire",
    "it": "può riunire diversi titoli della tua lista in un paniere — un clic sul nome lo aggiunge "
          "al totale o lo esclude",
    "es": "puede reunir varios valores de tu propia lista en una cesta: un clic en el nombre lo "
          "incluye en el total o lo deja fuera",
    "pt-BR": "pode reunir vários itens da sua própria lista em uma cesta — um clique no nome o "
             "inclui no total ou o deixa fora",
    "pl": "może zebrać kilka pozycji z własnej listy w jeden koszyk — kliknięcie nazwy włącza ją "
          "do sumy lub ją pomija",
    "cs": "může spojit několik položek z vlastního seznamu do jednoho koše — kliknutí na název ji "
          "do součtu přidá nebo vynechá",
    "ru": "может собрать несколько позиций из вашего списка в одну корзину — щелчок по названию "
          "включает её в сумму или убирает",
    "tr": "kendi listenizdeki birkaç kalemi tek bir sepette toplayabilir — ismine tıklamak onu "
          "toplama dahil eder veya çıkarır",
}

# 中文那条用双破折号、前后不留空；其余语言用一个破折号、前后各留一个空格 ——
# 已有的十六条就是这么写的，新加的那条不能看着像另一种文件。
DASH = {"zh-Hans": "——", "zh-Hant": "——"}
# 功能条里名字之间的分隔符。
COMMA = {"zh-Hans": "、", "zh-Hant": "、", "ja": "、", "ko": "、"}

# 商店「此版本的新增功能」的硬上限。
MOST = 1500


def intro(lang, chapter):
    """那一章的开场句 —— 见 docstring：不能用 `first_sentence`，它会认成配图的 alt 文字。

    **开场句在手册里是换行的**，不是一行：英文的债市那一章是
    "…as what" / "holding it earned." 两行，只取第一行就得到半句话。所以这里一直读到
    空行或第一条要点为止，把这几行接起来。
    """
    text = (HELP / f"help-{lang}.md").read_text(encoding="utf-8")
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

    return re.sub(r"\*\*(.+?)\*\*", r"\1", " ".join(said))


def bare(item):
    """去掉每条自带的那一个句号 —— 拼进一串里，只有最后一个该有句号。"""
    return item.rstrip().rstrip("。．.").rstrip()


def news(lang):
    dash = DASH.get(lang) or " — "
    sep = "；" if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else "; "
    stop = "。" if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else "."

    items = [
        f"{page_name(lang, BOND[0])}{dash}{intro(lang, BOND[1])}",
        f"{page_name(lang, TURNOVER[0])}{dash}{BASKET[lang]}",
        f"{page_name(lang, CANDLE[0])}{dash}{intro(lang, CANDLE[1])}",
        f"{page_name(lang, POSITION[0])}{dash}{intro(lang, POSITION[1])}",
    ]

    # 引导句末尾那个冒号后面要不要留一个空格，按语言分：中文不留，其余要留。上一版那十四
    # 行是「pages:Market cap」连着的 —— 中文看着对，英文看着像漏字，所以这里分开处理。
    gap = "" if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else " "

    return OPEN[lang] + gap + sep.join(bare(item) for item in items) + stop


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # store-listing.md 是 CRLF。插进去的新行也必须跟着 CRLF，否则同一份文件里两种行尾。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    # 超了 1500 就一个字都别写：这一栏是硬上限，而 14 份里只要有一份超了，上传时才会发现。
    over = [(lang, len(news(lang))) for lang in LANGS if len(news(lang)) > MOST]

    if over:
        for lang, size in over:
            print(f"× {lang}: 「新增功能」{size} 字，超过 {MOST} 的上限")
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        bond = page_name(lang, BOND[0])
        done = []

        # 1) 说明段：在清单末尾追加第十七页
        bullets = [i for i in range(start, end) if lines[i].startswith("• ")]

        if len(bullets) < 16:
            print(f"× {lang}: 说明段只有 {len(bullets)} 条")
            return 1

        at = bullets[-1]

        # 标题在清单**前面**，所以要在插入之前认清楚：插进去的那一条会顶掉「往回找第一行」
        # 这种定位办法。
        title = at

        while lines[title].lstrip().startswith("•"):   # 跳过整条清单
            title -= 1

        while not lines[title].strip():                # 再跳过清单与标题之间的空行
            title -= 1

        if not any(lines[i].startswith(f"• {bond}") for i in bullets):
            dash = DASH.get(lang) or f" {dash_of(lines[bullets[0]])} "

            # 清单里那十六条一条也不带句末句号，所以新加的这条也不能带 —— 手册那一章的开场
            # 句是一句完整的话，句号是它自己的。
            lines.insert(at + 1, f"• {bond}{dash}{bare(intro(lang, BOND[1]))}")
            changed += 1
            done.append("说明段 +1")

            # 插入把这一段撑长了一行，段尾的边界必须重算 —— 否则段末的「产品功能」
            # 那些行会落到边界外面，看上去就像这一语言没有功能条。
            heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
            start = heads[n]
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)

        # 2) 标题：十六 → 十七
        old, new = HEADING[lang]

        if old in lines[title]:
            lines[title] = lines[title].replace(old, new)
            changed += 1
            done.append("标题")
        elif new not in lines[title]:
            print(f"× {lang}: 标题行「{lines[title]}」里既没有 {old!r} 也没有 {new!r}")
            return 1

        # 3) 产品功能条：十六种 → 十七种，末尾补上那一页的名字
        old, new = FEATURE[lang]
        hit = [i for i in range(start, end) if lines[i].startswith("- ") and old in lines[i]]

        if hit:
            comma = COMMA.get(lang, ", ")
            lines[hit[0]] = lines[hit[0]].replace(old, new) + comma + bond
            changed += 1
            done.append("功能条")
        elif not any(lines[i].startswith("- ") and new in lines[i] for i in range(start, end)):
            print(f"× {lang}: 功能条里找不到 {old!r}")
            return 1

        # 4) 「此版本的新增功能」整行换掉
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1

        while at < end and not lines[at].strip():
            at += 1

        text = news(lang)

        if lines[at] != text:
            lines[at] = text
            changed += 1
            done.append(f"新增功能（{len(text)} 字）")

        # 段号会因为插入而位移，所以按标题重新定位一次。
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: {' / '.join(done) or '（已是本版）'}")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
