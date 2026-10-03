"""改写商店文案里那十四条「此版本的新增功能」。

为什么是**换掉**而不是接着往后加：说明段已经从十页补到十六页，而那十四条还在说
「本版新增第八个图表页 K线」「本版新增第九个图表页 市值榜竞速」—— 一页一页数着加上去
的旧版本说明，和「十六大图表页」并排放在一起是自相矛盾的。商店这一栏问的是本版，
历史留在 CHANGELOG.md 里。

本版要说的是**新页面优先**：第九到第十六页八个页面逐条列出，其余（自绘图标、共享自选、
四页区间重定）各一句带过。那一栏有 **1500 字符**的上限，八个页面用德/法/意语写就顶到
一千二，所以每条只留帮助手册那一章的**第一个分句**，不整句搬。

**说明从帮助手册里取，不另写**：每一页在 14 份 help-*.md 里早有一句是项目自己翻的、
和界面一致的说法；再手写一遍只会得到 14 句各写各的。页面名从各语言的 resw 里取。

定位：每个语言段里第二个 `###` 小标题之后的第一段正文。幂等：那一段已经与本次生成的
字符串相同就跳过。

用法：python tools/port-store-listing-whatsnew.py
"""

import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 与 port-store-listing-pages.py 共用一套取词规则：同一段规则两个副本，就有一个副本会在
# 某天被改对而另一个不会。（脚本名带连字符，不能当模块名 import。）
from listingtext import chapter_of, first_sentence, page_name  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 第九到第十六页，按导航顺序。括号里那个数字原来是写死的章节序号，插进一章就整体错位
# （第十七页插在大类资产之后，回撤与修复、持有胜率各后移一位），现在从导航顺序推。
PAGES = [(key, chapter_of(key)) for key in (
    "NavMarketCap",
    "NavAhPremium",
    "NavExtremeDays",
    "NavFxCorridor",
    "NavIndexRace",
    "NavAssetRace",
    "NavDrawdown",
    "NavHoldOdds",
)]

# 每条说明最多留多少字符。整句照搬会让德/法/意语越过 1500 的上限，而那一栏是硬上限；
# 截在**分句**上（下一个逗号/破折号），不留半句话。
LIMIT = {"zh-Hans": 46, "zh-Hant": 46, "ja": 52, "ko": 52}

# 列表开头的引导句。
OPEN = {
    "zh-Hans": "本版新增八个图表页：",
    "zh-Hant": "本版新增八個圖表頁：",
    "en-US": "Eight new chart pages:",
    "ja": "このバージョンで八つのチャートページが加わりました：",
    "ko": "이 버전에서 여덟 개의 차트 페이지가 추가되었습니다:",
    "de": "Acht neue Diagrammseiten:",
    "fr": "Huit nouvelles pages de graphiques :",
    "it": "Otto nuove pagine di grafici:",
    "es": "Ocho páginas de gráficos nuevas:",
    "pt-BR": "Oito novas páginas de gráficos:",
    "pl": "Osiem nowych stron wykresów:",
    "cs": "Osm nových stránek s grafy:",
    "ru": "Восемь новых страниц с графиками:",
    "tr": "Sekiz yeni grafik sayfası:",
}

# 列表之后：图标、共享自选、四页区间各一句。
ALSO = {
    "zh-Hans": "另外：十六个页面各有自己画的图标（此前三对页面共用同一个系统字形）；"
               "指数长跑、大类资产、回撤与修复、持有胜率四页共用一份自选，三个市场可混装；"
               "四页的区间按接口实测重定——K线日线多了 5 年与 10 年，成交量换手率与行业板块竞速"
               "多了 24 个月（自定义上限 900 天），市值榜多了「最长」（月线一次给满 180 期）。",
    "zh-Hant": "另外：十六個頁面各有自己畫的圖示（此前三對頁面共用同一個系統字形）；"
               "指數長跑、大類資產、回撤與修復、持有勝率四頁共用一份自選，三個市場可混裝；"
               "四頁的區間按介面實測重定——K線日線多了 5 年與 10 年，成交量與換手率、行業板塊競速"
               "多了 24 個月（自訂上限 900 天），市值榜多了「最長」（月線一次給滿 180 期）。",
    "en-US": "Also: each of the sixteen pages now has an icon drawn for it (three pairs had been "
             "sharing one system glyph); the index race, asset classes, drawdowns and hold odds "
             "share one watchlist that may mix all three markets; and four range menus were "
             "re-cut against what the endpoints return — daily candles gained 5 and 10 years, "
             "Volume & Turnover and Sector Race gained 24 months (custom spans up to 900 days), "
             "and Market Cap Race gained Longest, one request returning all 180 monthly periods.",
    "ja": "また、十六のページすべてに専用のアイコンを用意しました（以前は三組のページが同じ"
          "システム字形を共有していました）。指数レース・資産クラス・下落と回復・保有勝率の"
          "四ページは一つのウォッチリストを共有し、三つの市場を混在できます。"
          "四ページの期間は実際の API が返す量に合わせて見直し、ローソク足の日足に 5 年と 10 年、"
          "出来高・回転率とセクターレースに 24 か月（カスタムは最大 900 日）、"
          "時価総額レースに「最長」（月足 180 期）を追加しました。",
    "ko": "또한 열여섯 개 페이지에 각각의 아이콘을 그렸습니다(이전에는 세 쌍이 같은 시스템 글리프를 "
          "공유했습니다). 지수 경주·자산군·낙폭과 회복·보유 승률 네 페이지는 하나의 관심 목록을 "
          "공유하며 세 시장을 섞을 수 있습니다. 네 페이지의 구간은 API가 실제로 돌려주는 양에 맞춰 "
          "다시 정했습니다: 캔들 일간에 5년과 10년, 거래량·회전율과 업종 경주에 24개월(사용자 지정 "
          "최대 900일), 시가총액 레이스에 「가장 긴 구간」(월간 180개 기간)을 추가했습니다.",
    "de": "Außerdem: Jede der sechzehn Seiten hat nun ein eigenes Symbol; Index-Rennen, "
          "Anlageklassen, Verluste und Erholung sowie Gewinnchancen nutzen eine gemeinsame "
          "Watchlist, die alle drei Märkte mischen darf; und die Zeiträume von vier Seiten "
          "wurden an das angepasst, was die Endpunkte liefern — Tageskerzen bekamen 5 und "
          "10 Jahre, Volumen/Umschlag und Sektor-Rennen 24 Monate (eigene Zeiträume bis "
          "900 Tage), das Marktkapitalisierungs-Rennen „Längster“ mit 180 Monatsperioden.",
    "fr": "Par ailleurs : chacune des seize pages a désormais son icône ; la course des indices, "
          "les classes d'actifs, les replis et les chances de détention partagent une liste de "
          "suivi qui peut mêler les trois marchés ; et les plages de quatre pages ont été "
          "recalées sur ce que renvoient les points d'accès — 5 et 10 ans sur le quotidien des "
          "chandeliers, 24 mois sur Volume et rotation et la course de secteurs (plage "
          "personnalisée jusqu'à 900 jours), « Maximale » sur la course des capitalisations, "
          "180 périodes mensuelles en une requête.",
    "it": "Inoltre: ognuna delle sedici pagine ha ora la sua icona; la corsa degli indici, le "
          "classi di attività, i cali e i recuperi e le probabilità di detenzione condividono un "
          "elenco che può mescolare i tre mercati; e gli intervalli di quattro pagine sono stati "
          "rimisurati su ciò che restituiscono gli endpoint — 5 e 10 anni sul giornaliero delle "
          "candele, 24 mesi su Volume e rotazione e sulla corsa dei settori (intervallo "
          "personalizzato fino a 900 giorni), «Massimo» sulla corsa delle capitalizzazioni, "
          "180 periodi mensili in una richiesta.",
    "es": "Además: cada una de las dieciséis páginas tiene ya su icono (antes tres pares "
          "compartían un glifo del sistema); la carrera de índices, las clases de activos, los "
          "repliegues y las probabilidades de tenencia comparten una lista que puede mezclar los "
          "tres mercados; y los rangos de cuatro páginas se reajustaron a lo que devuelven los "
          "endpoints — 5 y 10 años en el diario de velas, 24 meses en Volumen y rotación y en la "
          "carrera de sectores (personalizado hasta 900 días), «Máximo» en la carrera de "
          "capitalización, 180 periodos mensuales en una petición.",
    "pt-BR": "Além disso: cada uma das dezesseis páginas agora tem seu ícone (antes três pares "
             "compartilhavam um glifo do sistema); a corrida de índices, as classes de ativos, os "
             "recuos e as chances de manutenção compartilham uma lista que pode misturar os três "
             "mercados; e os intervalos de quatro páginas foram reajustados ao que os endpoints "
             "devolvem — 5 e 10 anos no diário do candlestick, 24 meses em Volume e giro e na "
             "corrida de setores (personalizado até 900 dias), «Máximo» na corrida de valor de "
             "mercado, 180 períodos mensais em um pedido.",
    "pl": "Poza tym: każda z szesnastu stron ma teraz własną ikonę (wcześniej trzy pary dzieliły "
          "jeden glif systemowy); wyścig indeksów, klasy aktywów, obsunięcia i szanse utrzymania "
          "korzystają z jednej listy obserwowanych, która może mieszać trzy rynki; a zakresy "
          "czterech stron przejrzano pod kątem tego, co zwracają endpointy — 5 i 10 lat na "
          "interwale dziennym świec, 24 miesiące w Wolumenie i obrocie oraz w wyścigu sektorów "
          "(własny zakres do 900 dni), „Najdłuższy“ w wyścigu kapitalizacji, 180 okresów "
          "miesięcznych w jednym żądaniu.",
    "cs": "Dále: každá z šestnácti stran má nyní vlastní ikonu (dříve tři dvojice sdílely jeden "
          "systémový glyf); závod indexů, třídy aktiv, propady a šance držení sdílejí jeden "
          "seznam, který může míchat všechny tři trhy; a rozsahy čtyř stran byly znovu změřeny "
          "podle toho, co vracejí koncové body — 5 a 10 let u denního intervalu svíček, 24 měsíců "
          "u Objemu a obratu a závodu sektorů (vlastní rozsah do 900 dnů), „Nejdelší“ u závodu "
          "kapitalizací, 180 měsíčních období v jednom požadavku.",
    "ru": "Кроме того: у каждой из шестнадцати страниц теперь своя иконка; гонка индексов, "
          "классы активов, просадки и шансы удержания используют один список наблюдения, "
          "который может смешивать все три рынка; "
          "а диапазоны четырёх страниц пересчитаны по тому, что возвращают конечные точки — "
          "5 и 10 лет на дневном интервале свечей, 24 месяца у «Объёма и оборачиваемости» и "
          "гонки секторов (свой диапазон до 900 дней), «Максимальный» у гонки капитализаций, "
          "180 месячных периодов за один запрос.",
    "tr": "Ayrıca: on altı sayfanın her birinin artık kendi simgesi var (önceden üç çift aynı "
          "sistem glifini paylaşıyordu); endeks yarışı, varlık sınıfları, düşüşler ve elde tutma "
          "oranları üç pazarı karıştırabilen tek bir izleme listesi paylaşıyor; dört sayfanın "
          "aralıkları da uç noktaların döndürdüğüne göre yeniden ayarlandı — günlük mumlarda 5 ve "
          "10 yıl, Hacim ve devir ile sektör yarışında 24 ay (özel aralık 900 güne kadar), piyasa "
          "değeri yarışında 「En uzun」, tek istekte 180 aylık dönem.",
}


def gloss(lang, index):
    """帮助手册某一章的首句，截到第一个分句 —— 整句照搬会越过商店那一栏的 1500 字上限。"""
    para = first_sentence(lang, index)
    limit = LIMIT.get(lang, 118)

    if len(para) <= limit:
        return para

    cut = max(para.rfind("，", 0, limit), para.rfind(", ", 0, limit),
              para.rfind("；", 0, limit), para.rfind(" — ", 0, limit))

    return para[:cut] if cut > limit * 0.4 else para[:limit].rstrip() + "…"


def news(lang):
    dash = "——" if lang in ("zh-Hans", "zh-Hant") else " — "
    sep = "；" if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else "; "

    items = [f"{page_name(lang, key)}{dash}{gloss(lang, index)}" for key, index in PAGES]

    return OPEN[lang] + sep.join(items) + ("。" if lang in ("zh-Hans", "zh-Hant", "ja", "ko") else ". ") \
        + ALSO[lang]


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # store-listing.md 是 CRLF，帮助手册是 LF —— 各文件保持自己的行尾。不剥掉 \r 的话，
    # "这一行是不是已经改过了"永远比不出来（每次都差一个 \r），幂等就成了空话。
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
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = news(lang)

        if lines[at] == text:
            print(f"· {lang}: （已是本版）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    long = [(l, len(news(l))) for l in LANGS if len(news(l)) > 1500]

    if long:
        print(f"\n！超过商店 1500 字上限：{long}")
    else:
        print(f"\n最长的语言 {max(len(news(l)) for l in LANGS)} 字，都在 1500 以内")

    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
