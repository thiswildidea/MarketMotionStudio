# -*- coding: utf-8 -*-
r"""给 14 份 help-*.md 的「选择市场」一章补上加密货币这个市场，并修掉 A 股那一行的旧数字。

**要做两件事，因为它们在同一个列表里。**

1. **加一条加密货币。** 它原来只是导航里并列的三项，现在是一个可选的市场，而「支持哪些
   市场」是这一章的主题 —— 不写在这里，读者只能靠下拉里有没有那一格来推断规则。
   规则有两半，都要说：**能不能选**（两个源都在大陆访问不到）与**选了之后剩下什么**
   （只剩加密货币的三页，股票各页全部移除）。

2. **把 A 股那条的「八个页面」去掉。** 它写在很久以前，现在是 18 个股票页，而这个数字
   **没有任何事实源**：页数由导航算出（`verify-docs.py` 的 `word_of` 早就是这么算 README 的），
   手册这几行却一直手写。数字留在正文里，每加一页就要改 14 份文档，漏一份就是一句假话 ——
   所以这一条改成不带数字的说法，与页数彻底脱钩。

**插入位置**是**第一处含 `SPDR` 的那一行之后**（美股那条）。用 SPDR 当锚而不是行号：行号在
14 份文件里会因为前面几章的段落数不同而漂。第一处一定在「选择市场」里 —— 这一章在文件开头，
而 SPDR 在全文只出现在市场那一章与行业竞速那一章，后者远在后面。

**幂等**：先按「行首是 `- **<市场名>**`」删掉旧行再插入（市场名表与
`port-crypto-market-resw.py` 同一份），A 股那条用整句替换 —— 新句里不含旧句，重跑时旧句
找不到就跳过。两半都是重跑安全的。

help-*.md 是 **LF 无 BOM**（实测；`port-candle-help.py` 的注释说带 BOM 已经过时）。BOM 按
原文照抄，不猜。

用法：python tools\port-crypto-market-help.py
"""
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 市场名（与 port-crypto-market-resw.py 同一份，用来认旧行）--------------------------------
#
# 这份表在这里的用途只有一个：认出上一趟插进去的那一行。**必须是市场名本身**，不能用
# 「行里有 crypto / 暗号資産」之类的关键词 —— 德语写的是 Kryptowährungen，日语写的是
# 暗号資産，而两种语言里正文别处也可能出现这些词。

NAMES = [
    "Cryptocurrency", "Kryptowährungen", "Criptomonedas", "Cryptomonnaies",
    "Criptovalute", "Kryptowaluty", "Criptomoedas", "Kryptoměny",
    "Kripto", "Криптовалюты", "暗号資産", "암호화폐",
    "加密貨幣", "加密货币",
]

# ---- A 股那一条：去掉数字 --------------------------------------------------------------

AS_HARE_OLD = [
    "- **A-shares**: all eight pages are available.",
    "- **A-Aktien**: alle acht Seiten sind verfügbar.",
    "- **Acciones A**: las ocho páginas están disponibles.",
    "- **Actions A** : les huit pages sont disponibles.",
    "- **Azioni A**: tutte e otto le pagine sono disponibili.",
    "- **Akcje A**: dostępnych jest wszystkich osiem stron.",
    "- **Ações A**: as oito páginas estão disponíveis.",
    "- **A-akcie**: všech osm stránek je k dispozici.",
    "- **A hisseleri**: sekiz sayfanın tümü kullanılabilir.",
    "- **A-акции**: доступны все восемь страниц.",
    "- **A 株**：8 つのページすべてが利用できます。",
    "- **A주**: 여덟 페이지를 모두 사용할 수 있습니다.",
    "- **A 股**：八個頁面全部可用。",
    "- **A 股**：八个页面全部可用。",
]

AS_HARE_NEW = [
    "- **A-shares**: every stock page is available.",
    "- **A-Aktien**: jede Aktienseite ist verfügbar.",
    "- **Acciones A**: todas las páginas de acciones están disponibles.",
    "- **Actions A** : toutes les pages d'actions sont disponibles.",
    "- **Azioni A**: tutte le pagine azionarie sono disponibili.",
    "- **Akcje A**: wszystkie strony akcyjne są dostępne.",
    "- **Ações A**: todas as páginas de ações estão disponíveis.",
    "- **A-akcie**: všechny akciové stránky jsou k dispozici.",
    "- **A hisseleri**: tüm hisse sayfaları kullanılabilir.",
    "- **A-акции**: доступны все страницы акций.",
    "- **A 株**：株式のページはすべて利用できます。",
    "- **A주**: 주식 페이지를 모두 사용할 수 있습니다.",
    "- **A 股**：股票各頁全部可用。",
    "- **A 股**：股票各页全部可用。",
]

# ---- 加密货币那一条 --------------------------------------------------------------------

CRYPTO_RULE = [
    "- **Cryptocurrency**: offered only where a price can be fetched — both of its sources are outside the mainland's reach. Choosing it leaves the three crypto pages in the navigation and takes every stock page out, because those read an endpoint that quotes no coin at all. Prices are in US dollars and a coin trades every day of the year, so no day is missing.",
    "- **Kryptowährungen**: nur dort angeboten, wo ein Kurs geladen werden kann — beide Quellen liegen außerhalb der Reichweite des Festlands. Wer sie wählt, behält die drei Krypto-Seiten in der Navigation und verliert jede Aktienseite, denn diese lesen einen Endpunkt, der keine einzige Münze notiert. Preise in US-Dollar, und eine Münze wird an jedem Tag des Jahres gehandelt, es fehlt also kein Tag.",
    "- **Criptomonedas**: solo aparece donde se puede obtener un precio — sus dos fuentes están fuera del alcance del continente. Al elegirlo, las tres páginas cripto se quedan en la navegación y todas las páginas de acciones desaparecen, porque estas leen un endpoint que no cotiza ninguna moneda. Los precios están en dólares estadounidenses y una moneda cotiza todos los días del año, así que no falta ningún día.",
    "- **Cryptomonnaies** : proposé uniquement là où un cours peut être obtenu — ses deux sources sont hors de portée du continent. Le choisir garde les trois pages crypto dans la navigation et retire toutes les pages d'actions, car celles-ci interrogent un point d'accès qui ne cote aucune cryptomonnaie. Les prix sont en dollars américains et une cryptomonnaie se négocie tous les jours de l'année : aucun jour ne manque.",
    "- **Criptovalute**: offerto solo dove un prezzo è raggiungibile — entrambe le sue fonti sono fuori portata dal continente. Sceglierlo lascia le tre pagine cripto nella navigazione e toglie ogni pagina azionaria, perché quelle leggono un endpoint che non quota alcuna moneta. I prezzi sono in dollari statunitensi e una moneta viene scambiata ogni giorno dell'anno, quindi non manca nessun giorno.",
    "- **Kryptowaluty**: oferowane tylko tam, gdzie da się pobrać cenę — oba jego źródła są poza zasięgiem kontynentu. Wybranie go zostawia w nawigacji trzy strony krypto, a usuwa wszystkie strony akcyjne, bo one czytają endpoint, który nie notuje żadnej monety. Ceny są w dolarach amerykańskich, a moneta jest notowana każdego dnia roku, więc żaden dzień nie brakuje.",
    "- **Criptomoedas**: oferecido apenas onde um preço pode ser obtido — suas duas fontes estão fora do alcance do continente. Escolhê-lo mantém as três páginas cripto na navegação e remove todas as páginas de ações, porque estas leem um endpoint que não cota nenhuma moeda. Os preços estão em dólares americanos e uma moeda é negociada todos os dias do ano, então nenhum dia falta.",
    "- **Kryptoměny**: nabízeno jen tam, kde lze získat cenu — oba jeho zdroje jsou z pevniny nedosažitelné. Jeho volba ponechá v navigaci tři krypto stránky a odebere všechny akciové, protože ty čtou endpoint, který nekotuje žádnou minci. Ceny jsou v amerických dolarech a mince se obchoduje každý den v roce, takže žádný den nechybí.",
    "- **Kripto**: yalnızca fiyat alınabilen yerlerde sunulur — iki kaynağı da anakaranın erişimi dışındadır. Seçildiğinde gezinmede üç kripto sayfası kalır ve tüm hisse sayfaları kaldırılır, çünkü onlar hiçbir coin kotasyonu vermeyen bir uç noktayı okur. Fiyatlar ABD doları cinsindendir ve bir coin yılın her günü işlem görür, bu yüzden hiçbir gün eksik değildir.",
    "- **Криптовалюты**: предлагается только там, где можно получить цену — оба его источника недоступны с материка. При выборе в навигации остаются три криптостраницы, а все страницы акций убираются: они читают endpoint, который не котирует ни одной монеты. Цены в долларах США, монета торгуется каждый день в году, поэтому ни один день не пропущен.",
    "- **暗号資産**：価格を取得できる地域でだけ選べます。2 つの情報源はどちらも中国本土からは到達できません。これを選ぶとナビゲーションには暗号資産の 3 ページだけが残り、株式のページはすべて外れます（株式側はコインを 1 つも扱わないエンドポイントを読むためです）。価格は米ドル建てで、暗号資産は年中無休で取引されるため、期間に欠ける日はありません。",
    "- **암호화폐**: 가격을 받아올 수 있는 지역에서만 나타납니다. 두 소스 모두 중국 본토에서는 닿을 수 없습니다. 이 시장을 고르면 탐색에는 암호화폐 세 페이지만 남고 주식 페이지는 모두 빠집니다. 주식 페이지는 코인을 하나도 제공하지 않는 엔드포인트를 읽기 때문입니다. 가격은 미국 달러 기준이며 암호화폐는 연중 매일 거래되므로 빠진 날이 없습니다.",
    "- **加密貨幣**：只有在能取到價格的地區才會出現這一項——它的兩個數據源在中國大陸都訪問不到。選中它之後，導覽裡只留下加密貨幣的三頁，股票各頁全部移除，因為那些頁面讀的介面一個幣也不提供。價格以美元計價，幣全年天天交易，因此區間裡不會缺任何一天。",
    "- **加密货币**：只有在能取到价格的地方才会出现这一项——它的两个数据源在中国大陆都访问不到。选中它之后，导航里只留下加密货币的三页，股票各页全部移除，因为那些页面读的接口一个币也不提供。价格以美元计价，币全年天天交易，因此区间里不会缺任何一天。",
]


def main():
    for tag in LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig")

        index = LANGS.index(tag)
        name, rule = NAMES[index], CRYPTO_RULE[index]

        # The old sentence goes first: it sits above where the new line is inserted, and
        # leaving it in would put a stale page count right next to a rule about pages.
        if AS_HARE_OLD[index] in text:
            text = text.replace(AS_HARE_OLD[index], AS_HARE_NEW[index], 1)

        lines = text.split("\n")

        # Idempotent: drop a line this script put here last time, wherever it sits.
        lines = [line for line in lines if not line.startswith(f"- **{name}**")]

        at = next(i for i, line in enumerate(lines) if "SPDR" in line)
        lines.insert(at + 1, rule)

        text = "\n".join(lines)

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))

        print(f"{tag}: +1 market rule, A-share line rewritten")


if __name__ == "__main__":
    main()
