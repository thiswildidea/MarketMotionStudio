"""把商店文案（docs/store-listing.md，14 语言）的说明段补到**第二十四页**、**四个市场**。

应用里现在是二十四页、四个市场，而说明段停在十八页、三个市场 —— 加密货币那六页（K 线、定投、
持仓、涨跌日历、市值历程、市值榜）一次都没进过商店，加密货币作为第四个市场也没进过。这一版要
把它们交上去，商店说得出的话就得和应用里有的东西对上：清单写着十八页、市场写着三个，比「还有
六页没写」更容易被当成谎话。

**描述不另写。** 六条说明从 14 份 help-*.md 的同一章开场段取 —— 那是项目自己翻的、和界面一致的
说法。再手写 14×6 句，只会得到 84 句各写各的。

为什么不是一个 `-10160.py`
--------------------------
按仓库的老规矩，版本号那几个脚本（`-1050` … `-10160`）除改说明段外还要**换掉**「此版本的新增功能」
那一栏，而那一栏是**换**不是加，必须与 manifest 版本号、CHANGELOG 同一轮动 —— 文案不能先于匹配的
包上传。本脚本只碰说明段的四行（清单、标题、功能条、市场句），那一栏留给 `-10160.py`。

**一个位置只有一个 owner。** 这里的四行与「新增功能」那一栏不是同一行，分工不冲突。

数字词不在本脚本手写第二份
--------------------------
「十八」「二十四」怎么说，各语言各有一套词（日语是 `18 つの`、德语是 `Achtzehn`/`Vierundzwanzig`），
写错了标题就变成「二十四大图表页十八页」这种自相矛盾的句子，而十四份里只错一两个语言的时候肉眼
看不出来。所以这里**不写「十八」**，而是从上一轮的 owner —— `port-store-listing-caphistory.py` 的
`HEADING` / `FEATURE` 两张表 —— 按路径加载进来取它的「十八」作为锚，本脚本只提供目的地（「二十四」）。
同一个数字词因此只有一个地方写得出来。

市场句是本脚本第一次动，没有上一轮的锚，所以 `MARKET_DESC` / `MARKET_FEAT` 里 old 那一半是从
文件里抄来的原句：**整行精确替换**，某语言的措辞与表不一致时报错，而不是留下一句旧话。

定位与幂等：清单按页面名查重（已有这条就不插）；标题、功能条、市场句按整行精确替换，已经改过的
语言跳过而不报错。store-listing.md 是 **CRLF 无 BOM**，写完照原样写回。

用法：python tools\\port-store-listing-crypto-pages.py      （跑第二遍应当是「改了 0 处」）
"""

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import listingtext as lt                                     # noqa: E402
from listingtext import LANGS, LISTING, dash_of, page_name    # noqa: E402

# 上一轮的 owner：它是「页清单补到十八」那件事的唯一事实来源。文件名带连字符，只能按路径加载；
# **清 argv 再加载**，否则它会把本脚本的命令行参数当成自己的（见 tools/ 的那些坑）。
_argv = sys.argv
sys.argv = [sys.argv[0]]

_spec = importlib.util.spec_from_file_location(
    "port_store_listing_caphistory",
    os.path.join(HERE, "port-store-listing-caphistory.py"))
_prev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prev)

sys.argv = _argv

assert sorted(_prev.HEADING) == sorted(LANGS), "上一轮的标题表缺语言"
assert sorted(_prev.FEATURE) == sorted(LANGS), "上一轮的功能条表缺语言"

# 这次补的六页，按导航顺序（章序号由 chapter_of 从 MainWindow.xaml 算出，不写死）。
PAGES = ["NavCryptoCandle", "NavCryptoDca", "NavCryptoPosition",
         "NavCryptoCalendar", "NavCryptoCapHistory", "NavCryptoMarketCap"]

# 目的地：十八 → 二十四。锚是上一轮那两张表里的「十八」，所以这里只写增量那一半。
HEADING = {
    "zh-Hans": "二十四大图表页",
    "zh-Hant": "二十四大圖表頁",
    "en-US": "Twenty-four chart pages",
    "ja": "24 つのチャートページ",
    "ko": "24가지 차트 페이지",
    "de": "Vierundzwanzig Diagrammseiten",
    "fr": "Vingt-quatre pages de graphiques",
    "it": "Ventiquattro pagine di grafici",
    "es": "Veinticuatro páginas de gráficos",
    "pt-BR": "Vinte e quatro páginas de gráficos",
    "pl": "Dwadzieścia cztery stron wykresów",
    "cs": "Dvacet čtyři stránek s grafy",
    "ru": "Двадцать четыре страницы с графиками",
    "tr": "Yirmi dört grafik sayfası",
}

FEATURE = {
    "zh-Hans": "二十四种图表",
    "zh-Hant": "二十四種圖表",
    "en-US": "Twenty-four charts",
    "ja": "24 種類のチャート",
    "ko": "24가지 차트",
    "de": "Vierundzwanzig Diagramme",
    "fr": "Vingt-quatre graphiques",
    "it": "Ventiquattro grafici",
    "es": "Veinticuatro gráficos",
    "pt-BR": "Vinte e quatro gráficos",
    "pl": "Dwadzieścia cztery wykresów",
    "cs": "Dvacet čtyři grafů",
    "ru": "Двадцать четыре графика",
    "tr": "Yirmi dört grafik",
}

# 市场句：三个市场 → 四个市场。加密货币**可达才在市场下拉里出现**，这句话要说在前面 ——
# 用户装完发现下拉里只有三格，比商店先说一句「源连得上才有第四格」更像故障。
MARKET_DESC = {
    "zh-Hans": ("支持A股、港股、美股三个市场，界面内置 14 种语言。",
                "支持A股、港股、美股与加密货币四个市场（加密货币在数据源连得上时才出现），界面内置 14 种语言。"),
    "zh-Hant": ("支援陸股、港股、美股三個市場，介面內建 14 種語言。",
                "支援陸股、港股、美股與加密貨幣四個市場（加密貨幣在資料來源連得上時才出現），介面內建 14 種語言。"),
    "en-US": ("Three markets: China A-share, Hong Kong, and US. The interface ships in 14 languages.",
              "Four markets: China A-share, Hong Kong, US, and cryptocurrency — offered when a crypto "
              "source answers. The interface ships in 14 languages."),
    "ja": ("中国A株・香港・米国の 3 市場に対応。インターフェースは 14 言語を内蔵。",
           "中国A株・香港・米国・暗号資産の 4 市場に対応（暗号資産はデータ源につながるときに表示）。インターフェースは 14 言語を内蔵。"),
    "ko": ("중국 A주식, 홍콩, 미국 3개 시장 지원. 인터페이스는 14개 언어 내장.",
           "중국 A주식, 홍콩, 미국, 암호화폐 4개 시장 지원(암호화폐는 데이터 출처에 연결될 때 표시). 인터페이스는 14개 언어 내장."),
    "de": ("Drei Märkte: China A-Aktien, Hongkong und USA. Die Oberfläche gibt es in 14 Sprachen.",
           "Vier Märkte: China A-Aktien, Hongkong, USA und Kryptowährungen – angeboten, wenn eine "
           "Krypto-Quelle antwortet. Die Oberfläche gibt es in 14 Sprachen."),
    "fr": ("Trois marchés : Chine A, Hong Kong et États-Unis. L'interface existe en 14 langues.",
           "Quatre marchés : Chine A, Hong Kong, États-Unis et cryptomonnaies — proposées quand une "
           "source crypto répond. L'interface existe en 14 langues."),
    "it": ("Tre mercati: Cina A, Hong Kong e Stati Uniti. L'interfaccia è disponibile in 14 lingue.",
           "Quattro mercati: Cina A, Hong Kong, Stati Uniti e criptovalute — proposte quando una fonte "
           "crypto risponde. L'interfaccia è disponibile in 14 lingue."),
    "es": ("Tres mercados: China A, Hong Kong y EE. UU. La interfaz está disponible en 14 idiomas.",
           "Cuatro mercados: China A, Hong Kong, EE. UU. y criptomonedas — disponibles cuando una "
           "fuente cripto responde. La interfaz está disponible en 14 idiomas."),
    "pt-BR": ("Três mercados: China A, Hong Kong e EUA. A interface vem em 14 idiomas.",
              "Quatro mercados: China A, Hong Kong, EUA e criptomoedas — oferecidas quando uma fonte "
              "cripto responde. A interface vem em 14 idiomas."),
    "pl": ("Trzy rynki: Chiny A, Hongkong i USA. Interfejs dostępny w 14 językach.",
           "Cztery rynki: Chiny A, Hongkong, USA i kryptowaluty — oferowane, gdy odpowie źródło "
           "krypto. Interfejs dostępny w 14 językach."),
    "cs": ("Tři trhy: Čína A, Hongkong a USA. Rozhraní je ve 14 jazycích.",
           "Čtyři trhy: Čína A, Hongkong, USA a kryptoměny — nabízené, když odpoví zdroj krypta. "
           "Rozhraní je ve 14 jazycích."),
    "ru": ("Три рынка: Китай (A-акции), Гонконг и США. Интерфейс доступен на 14 языках.",
           "Четыре рынка: Китай (A-акции), Гонконг, США и криптовалюты — предлагаются, когда отвечает "
           "криптоисточник. Интерфейс доступен на 14 языках."),
    "tr": ("Üç piyasa: Çin A, Hong Kong ve ABD. Arayüz 14 dilde mevcut.",
           "Dört piyasa: Çin A, Hong Kong, ABD ve kripto paralar — bir kripto kaynağı yanıt verdiğinde "
           "sunulur. Arayüz 14 dilde mevcut."),
}

MARKET_FEAT = {
    "zh-Hans": ("覆盖A股、港股、美股三大市场", "覆盖A股、港股、美股与加密货币四大市场"),
    "zh-Hant": ("涵蓋陸股、港股、美股三大市場", "涵蓋陸股、港股、美股與加密貨幣四大市場"),
    "en-US": ("Three markets: China A-share, Hong Kong, and US",
              "Four markets: China A-share, Hong Kong, US, and cryptocurrency"),
    "ja": ("中国A株・香港・米国の 3 市場に対応", "中国A株・香港・米国・暗号資産の 4 市場に対応"),
    "ko": ("중국 A주식, 홍콩, 미국 3개 시장 지원", "중국 A주식, 홍콩, 미국, 암호화폐 4개 시장 지원"),
    "de": ("Drei Märkte: China A-Aktien, Hongkong und USA",
           "Vier Märkte: China A-Aktien, Hongkong, USA und Kryptowährungen"),
    "fr": ("Trois marchés : Chine A, Hong Kong et États-Unis",
           "Quatre marchés : Chine A, Hong Kong, États-Unis et cryptomonnaies"),
    "it": ("Tre mercati: Cina A, Hong Kong e Stati Uniti",
           "Quattro mercati: Cina A, Hong Kong, Stati Uniti e criptovalute"),
    "es": ("Tres mercados: China A, Hong Kong y EE. UU.",
           "Cuatro mercados: China A, Hong Kong, EE. UU. y criptomonedas"),
    "pt-BR": ("Três mercados: China A, Hong Kong e EUA",
              "Quatro mercados: China A, Hong Kong, EUA e criptomoedas"),
    "pl": ("Trzy rynki: Chiny A, Hongkong i USA", "Cztery rynki: Chiny A, Hongkong, USA i kryptowaluty"),
    "cs": ("Tři trhy: Čína A, Hongkong a USA", "Čtyři trhy: Čína A, Hongkong, USA a kryptoměny"),
    "ru": ("Три рынка: Китай (A-акции), Гонконг и США",
           "Четыре рынка: Китай (A-акции), Гонконг, США и криптовалюты"),
    "tr": ("Üç piyasa: Çin A, Hong Kong ve ABD", "Dört piyasa: Çin A, Hong Kong, ABD ve kripto paralar"),
}

# 中文那条清单用双破折号、前后不留空；其余语言用一个破折号、前后各留一个空格 —— 已有的十八条
# 就是这么写的，新加的六条不能看着像从另一种文件抄来的。
DASH = {"zh-Hans": "——", "zh-Hant": "——"}

# 功能条里名字之间的分隔符。
COMMA = {"zh-Hans": "、", "zh-Hant": "、", "ja": "、", "ko": "、"}

EXPECTED = 18           # 补之前清单里应当正好十八条。


def intro(lang, chapter):
    """这一章的开场段 —— 商店清单里那一条说明。

    **取整段不取整句**：这几章的开场常常是两句，第二句说的正是这一页最要紧的那件事
    （「周线与月线由同一批日线聚合而成」），截到第一个句号会把它删掉。
    """
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

    # 清单里那十八条一条也不带句末句号，新加的六条也不能带。
    return said.strip().rstrip("。．.").rstrip()


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # CRLF 要原样写回：同一份文件里两种行尾，上传时看不出来，diff 里看得出来。
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

        # 十八条是补之前、二十四条是补之后，两者都合法 —— 这是幂等脚本第二遍跑时的样子。
        if len(bullets) not in (EXPECTED, EXPECTED + len(PAGES)):
            print(f"× {lang}: 说明段有 {len(bullets)} 条，应当是 {EXPECTED} 或 {EXPECTED + len(PAGES)} 条")
            return 1

        # 标题在清单**前面**，所以要在插入之前认清楚：插进去的六条会顶掉「往回找第一行」
        # 这种定位办法。
        title = bullets[0]

        while lines[title].lstrip().startswith("•"):      # 跳过整条清单
            title -= 1

        while not lines[title].strip():                   # 再跳过清单与标题之间的空行
            title -= 1

        add = []

        for key in PAGES:
            name = page_name(lang, key)

            if any(lines[i].startswith(f"• {name}") for i in bullets):
                continue

            dash = DASH.get(lang) or f" {dash_of(lines[bullets[0]])} "
            add.append(f"• {name}{dash}{intro(lang, lt.chapter_of(key))}")

        if add:
            lines[bullets[-1] + 1:bullets[-1] + 1] = add
            changed += len(add)
            done.append(f"说明段 +{len(add)}")

            # 插入把这一段撑长了，段尾边界必须重算 —— 否则段末的「产品功能」那些行会落到
            # 边界外面，看上去就像这一语言没有功能条。
            heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
            start = heads[n]
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)

        # 标题：十八 → 二十四。锚从上一轮那张表来，不是从这里写进去的「十八」。
        anchor = _prev.HEADING[lang]

        if anchor in lines[title]:
            lines[title] = lines[title].replace(anchor, HEADING[lang])
            changed += 1
            done.append("标题")
        elif HEADING[lang] not in lines[title]:
            print(f"× {lang}: 标题行「{lines[title]}」里既没有 {anchor!r} 也没有 {HEADING[lang]!r}")
            return 1

        # 功能条：十八种 → 二十四种，末尾补上这六页的名字。
        anchor = _prev.FEATURE[lang]
        hit = [i for i in range(start, end)
               if lines[i].startswith("- ") and anchor in lines[i]]

        if hit:
            comma = COMMA.get(lang, ", ")
            names = comma.join(page_name(lang, key) for key in PAGES)
            lines[hit[0]] = lines[hit[0]].replace(anchor, FEATURE[lang]) + comma + names
            changed += 1
            done.append("功能条")
        elif not any(lines[i].startswith("- ") and FEATURE[lang] in lines[i]
                     for i in range(start, end)):
            print(f"× {lang}: 功能条里找不到 {anchor!r}")
            return 1

        # 市场句两处：说明段那一句、功能条第二条。**整行精确替换**，措辞对不上就报错，
        # 而不是留下「Three markets」和一份二十四页的清单摆在一起。
        for at, table in ((market_line(lines, start, end), MARKET_DESC),
                          (feature_line(lines, start, end), MARKET_FEAT)):
            old, new = table[lang]

            if at is None:
                print(f"× {lang}: 找不到市场句那一行的位置")
                return 1

            if new in lines[at]:
                continue

            if old not in lines[at]:
                print(f"× {lang}: 市场句「{lines[at]}」里没有 {old!r}")
                return 1

            lines[at] = lines[at].replace(old, new)
            changed += 1
            done.append("市场句")

        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: {' / '.join(done) or '（已是二十四页、四个市场）'}")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


def market_line(lines, start, end):
    """说明段里「三个市场」那一句：清单之后第一段。"""
    bullets = [i for i in range(start, end) if lines[i].startswith("• ")]

    at = bullets[-1] + 1

    while at < end and not lines[at].strip():
        at += 1

    return at if at < end and not lines[at].startswith("#") else None


def feature_line(lines, start, end):
    """功能条里「三个市场」那一条：第二条功能条。

    第一条是「一键生成」，历次上架都没变过顺序；市场那条一直在第二条。
    """
    feats = [i for i in range(start, end) if lines[i].startswith("- ")]

    return feats[1] if len(feats) > 1 else None


if __name__ == "__main__":
    sys.exit(main())
