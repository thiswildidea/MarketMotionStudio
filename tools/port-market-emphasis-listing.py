# -*- coding: utf-8 -*-
r"""商店文案里那句「四个市场」，改成按市场说清楚各自是拿来做什么的。

上架的页面上半部分只有两处说到市场：说明段末尾那一句，和功能条第二条。两处原本都只列
名字 —— 「China A-share, Hong Kong, US, and cryptocurrency」这样的名单读完了仍然不知道
该挑哪个市场，更看不出加密货币是为谁准备的。

改完之后两处各说一件事：

- **说明段**：四个市场各点名它自己的核心页面。加密货币那句额外说清它**只在中国大陆以外
  的市场提供**（两个源都在境外），而在那儿它是竖屏视频里最受欢迎的一类题材。
- **功能条**：名单后面补一句 —— 加密货币自带六页，只在中国大陆以外提供。

**四条市场要点写成段落，不写成 `• ` 列表**：`verify-docs.py` 数的是说明段里 `• ` 开头的
行，那个数字跟着页数走（现在是二十四条）。四条市场要点写成列表，那个数就会变成 28，
十四条语言一起红 —— 而清单本身一句没改。

**整句替换才算幂等**：先认旧句，旧句不在就认新句，两句都不在才报错。

文件是 **CRLF 不带 BOM**（与 store-listing.md 的既有约定一致）；照抄原文的行尾与 BOM。

用法：python tools\port-market-emphasis-listing.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import listingtext  # noqa: E402

# 说明段末尾那句：四个市场名单 → 四个市场各自的核心页面。
# 值里成对的 \n\n 是分段（商店描述里就是两个回车）。
MARKET_LINE = {
    "en-US": (
        "Four markets: China A-share, Hong Kong, US, and cryptocurrency — offered "
        "when a crypto source answers. The interface ships in 14 languages.",
        "Four markets, each with the pages its own data can feed. **China A-shares** "
        "— every page, including the whole-market turnover reel no other market's "
        "source reports, the sector race on the Shenwan sectors, the market cap race "
        "over today's largest fifteen, and AH premium. **Hong Kong** — the return "
        "matrix and the calendar on Hong Kong indices and listings, and four Hang Seng "
        "sub-indices racing. **US** — the same two pages on US indices and listings, "
        "ten SPDR sector ETFs racing, amounts in dollars. **Cryptocurrency** — six "
        "pages of its own, offered outside mainland China and nowhere inside it, "
        "because that is where both of its sources are; everywhere else, crypto is the "
        "market most people want on a phone screen, and a coin trades every hour of "
        "every day with no holiday to step over.\n\nThe interface ships in 14 "
        "languages.",
    ),
    "zh-Hans": (
        "支持A股、港股、美股与加密货币四个市场（加密货币在数据源连得上时才出现），界面内置 "
        "14 种语言。",
        "四个市场，各自带着它的数据能喂饱的那些页面。**A 股**——每一页都能用，包括只有它"
        "的源才给出的全市场成交额、申万一级行业上的行业竞速、当天市值最大十五家的市值竞速，"
        "以及 AH 溢价。**港股**——港股指数与个股上的收益矩阵和涨跌日历，以及四个恒生分类"
        "指数的行业竞速。**美股**——同样的两页放在美股指数与个股上，十只 SPDR 行业 ETF "
        "竞速，成交额以美元计价。**加密货币**——它自己有六页，只在中国大陆以外的市场提供："
        "它的两个源都在境外；而在境外，加密货币是竖屏视频里最受欢迎的一类题材，币一天二十四"
        "小时、一年三百六十五天都在交易，区间里没有要跳过的休市日。\n\n界面内置 14 种语言。",
    ),
    "zh-Hant": (
        "支援陸股、港股、美股與加密貨幣四個市場（加密貨幣在資料來源連得上時才出現），介面內建 "
        "14 種語言。",
        "四個市場，各自帶著它的資料能餵飽的那些頁面。**陸股**——每一頁都能用，包括只有它的"
        "源才給出的全市場成交額、申萬一級行業上的行業競速、當天市值最大十五家的市值競速，以及 "
        "AH 溢價。**港股**——港股指數與個股上的收益矩陣和漲跌日曆，以及四個恆生分類指數的"
        "行業競速。**美股**——同樣的兩頁放在美股指數與個股上，十檔 SPDR 產業 ETF 競速，"
        "成交額以美元計價。**加密貨幣**——它自己有六頁，只在中國大陸以外的市場提供：它的兩個"
        "源都在境外；而在境外，加密貨幣是直式影片裡最受歡迎的一類題材，幣一天二十四小時、一年"
        "三百六十五天都在交易，期間裡沒有要跳過的休市日。\n\n介面內建 14 種語言。",
    ),
    "ja": (
        "中国A株・香港・米国・暗号資産の 4 市場に対応（暗号資産はデータ源につながるときに"
        "表示）。インターフェースは 14 言語を内蔵。",
        "四つの市場は、それぞれ自分のデータで描けるページを連れています。**中国 A 株**——"
        "全ページが使えます。他の市場の源は出さない全市場売買代金、申万一級業種のセクター"
        "競争、当日の時価総額上位十五社による時価総額競争、そして AH プレミアムが含まれます。"
        "**香港**——香港の指数と銘柄で読むリターンマトリクスと騰落カレンダー、四つのハンセン"
        "分類指数によるセクター競争。**米国**——同じ二つのページを米国の指数と銘柄で、十本の "
        "SPDR セクター ETF によるセクター競争、売買代金はドル建て。**暗号資産**——六つの"
        "ページを持ち、中国本土以外の市場だけで提供されます。二つの源がそこにあるからです。"
        "本土の外で暗号資産は、スマホの画面に載せたい市場として最も人気があり、コインは一日"
        "二十四時間、年中無休で取引され、飛ばすべき休場日がありません。\n\nインターフェースは "
        "14 言語を内蔵。",
    ),
    "ko": (
        "중국 A주식, 홍콩, 미국, 암호화폐 4개 시장 지원(암호화폐는 데이터 출처에 연결될 때 "
        "표시). 인터페이스는 14개 언어 내장.",
        "네 시장은 각자 자신의 데이터로 그릴 수 있는 페이지를 가지고 있습니다. **중국 "
        "A주**——전체 시장 거래대금(다른 시장의 소스는 이 수치를 주지 않습니다), 선완 1차 "
        "업종 기준 업종 경주, 당일 시가총액 상위 15곳의 시가총액 경주, 그리고 AH 프리미엄을 "
        "포함해 모든 페이지를 쓸 수 있습니다. **홍콩**——홍콩 지수와 종목으로 읽는 수익 "
        "매트릭스와 등락 달력, 그리고 항셍 4개 분류 지수의 업종 경주. **미국**——같은 두 "
        "페이지를 미국 지수와 종목으로, SPDR 섹터 ETF 10개의 업종 경주, 거래대금은 달러 기준. "
        "**암호화폐**——자체 페이지 여섯 개를 가지고 있으며 중국 본토 밖 시장에서만 "
        "제공됩니다. 두 소스가 모두 그곳에 있기 때문입니다. 본토 밖에서 암호화폐는 휴대폰 "
        "화면에 올리고 싶은 시장으로 가장 인기가 높고, 코인은 하루 스물네 시간, 연중무휴로 "
        "거래되어 건너뛸 휴장일이 없습니다.\n\n인터페이스는 14개 언어 내장.",
    ),
    "de": (
        "Vier Märkte: China A-Aktien, Hongkong, USA und Kryptowährungen – angeboten, "
        "wenn eine Krypto-Quelle antwortet. Die Oberfläche gibt es in 14 Sprachen.",
        "Vier Märkte, jeder mit den Seiten, die seine eigenen Daten füttern können. "
        "**China A-Aktien** – jede Seite, darunter der Umsatzfilm für den Gesamtmarkt, "
        "den keine andere Quelle meldet, das Sektor-Rennen über die Shenwan-Sektoren, "
        "das Rennen der Marktkapitalisierung über die heute größten fünfzehn und die "
        "AH-Prämie. **Hongkong** – Renditematrix und Kalender auf Hongkonger Indizes "
        "und Werten, vier Hang-Seng-Subindizes im Rennen. **USA** – dieselben zwei "
        "Seiten auf US-Indizes und -Werten, zehn SPDR-Sektor-ETFs im Rennen, Beträge in "
        "Dollar. **Kryptowährungen** – sechs eigene Seiten, angeboten außerhalb des "
        "chinesischen Festlands und nirgends darin, weil beide Quellen dort liegen; "
        "überall sonst sind Kryptowährungen der Markt, den die meisten auf dem Handy "
        "sehen wollen, und eine Münze wird rund um die Uhr gehandelt, ohne Feiertag zum "
        "Überspringen.\n\nDie Oberfläche gibt es in 14 Sprachen.",
    ),
    "fr": (
        "Quatre marchés : Chine A, Hong Kong, États-Unis et cryptomonnaies — proposées "
        "quand une source crypto répond. L'interface existe en 14 langues.",
        "Quatre marchés, chacun avec les pages que ses propres données peuvent "
        "alimenter. **Chine A** — toutes les pages, dont le film du volume d'échanges "
        "du marché entier qu'aucune autre source ne publie, la course de secteurs sur "
        "les secteurs Shenwan, la course de capitalisation sur les quinze plus grandes "
        "du jour, et la prime AH. **Hong Kong** — la matrice des rendements et le "
        "calendrier sur les indices et valeurs de Hong Kong, quatre sous-indices Hang "
        "Seng en course. **États-Unis** — les deux mêmes pages sur les indices et "
        "valeurs américains, dix ETF sectoriels SPDR en course, montants en dollars. "
        "**Cryptomonnaies** — six pages à elles, proposées hors de Chine continentale "
        "et nulle part à l'intérieur, parce que leurs deux sources s'y trouvent ; "
        "partout ailleurs, les cryptomonnaies sont le marché que le plus de gens veulent "
        "voir sur un téléphone, et une pièce se négocie vingt-quatre heures sur "
        "vingt-quatre, sans jour férié à sauter.\n\nL'interface existe en 14 langues.",
    ),
    "it": (
        "Quattro mercati: Cina A, Hong Kong, Stati Uniti e criptovalute — proposte "
        "quando una fonte crypto risponde. L'interfaccia è disponibile in 14 lingue.",
        "Quattro mercati, ciascuno con le pagine che i suoi dati possono alimentare. "
        "**Cina A** — tutte le pagine, incluso il film del controvalore dell'intero "
        "mercato che nessun'altra fonte pubblica, la gara di settori sui settori "
        "Shenwan, la gara di capitalizzazione sulle quindici maggiori di oggi e il "
        "premio AH. **Hong Kong** — la matrice dei rendimenti e il calendario su "
        "indici e titoli di Hong Kong, quattro sottoindici Hang Seng in gara. **Stati "
        "Uniti** — le stesse due pagine su indici e titoli americani, dieci ETF "
        "settoriali SPDR in gara, importi in dollari. **Criptovalute** — sei pagine "
        "proprie, offerte fuori dalla Cina continentale e in nessun luogo al suo "
        "interno, perché lì si trovano entrambe le fonti; ovunque altrove, le "
        "criptovalute sono il mercato che più persone vogliono vedere sul telefono, e "
        "una moneta si scambia ventiquattro ore su ventiquattro, senza festività da "
        "saltare.\n\nL'interfaccia è disponibile in 14 lingue.",
    ),
    "es": (
        "Cuatro mercados: China A, Hong Kong, EE. UU. y criptomonedas — disponibles "
        "cuando una fuente cripto responde. La interfaz está disponible en 14 idiomas.",
        "Cuatro mercados, cada uno con las páginas que sus propios datos pueden "
        "alimentar. **China A** — todas las páginas, incluido el filme del volumen de "
        "todo el mercado, que ninguna otra fuente publica, la carrera de sectores sobre "
        "los sectores Shenwan, la carrera de capitalización sobre las quince mayores de "
        "hoy y la prima AH. **Hong Kong** — la matriz de rentabilidad y el calendario "
        "sobre índices y valores de Hong Kong, cuatro subíndices Hang Seng en carrera. "
        "**EE. UU.** — las mismas dos páginas sobre índices y valores "
        "estadounidenses, diez ETF sectoriales SPDR en carrera, importes en dólares. "
        "**Criptomonedas** — seis páginas propias, ofrecidas fuera de China "
        "continental y en ningún lugar dentro de ella, porque allí están sus dos "
        "fuentes; fuera de China, las criptomonedas son el mercado que más gente quiere "
        "ver en el móvil, y una moneda cotiza las veinticuatro horas, sin festivo que "
        "saltar.\n\nLa interfaz está disponible en 14 idiomas.",
    ),
    "pt-BR": (
        "Quatro mercados: China A, Hong Kong, EUA e criptomoedas — oferecidas quando "
        "uma fonte cripto responde. A interface vem em 14 idiomas.",
        "Quatro mercados, cada um com as páginas que os seus próprios dados conseguem "
        "alimentar. **China A** — todas as páginas, incluindo o filme do volume de "
        "todo o mercado, que nenhuma outra fonte publica, a corrida de setores sobre os "
        "setores Shenwan, a corrida de capitalização sobre as quinze maiores de hoje e "
        "o prémio AH. **Hong Kong** — a matriz de retorno e o calendário sobre índices "
        "e valores de Hong Kong, quatro subíndices Hang Seng em corrida. **EUA** — as "
        "mesmas duas páginas sobre índices e valores americanos, dez ETFs setoriais "
        "SPDR em corrida, valores em dólares. **Criptomoedas** — seis páginas próprias, "
        "oferecidas fora da China continental e em nenhum lugar dentro dela, porque é lá "
        "que estão as duas fontes; fora da China, as criptomoedas são o mercado que mais "
        "gente quer ver no telefone, e uma moeda é negociada vinte e quatro horas por "
        "dia, sem feriado a saltar.\n\nA interface vem em 14 idiomas.",
    ),
    "pl": (
        "Cztery rynki: Chiny A, Hongkong, USA i kryptowaluty — oferowane, gdy odpowie "
        "źródło krypto. Interfejs dostępny w 14 językach.",
        "Cztery rynki, każdy z tymi stronami, które jego własne dane potrafią zasilić. "
        "**Chiny A** — wszystkie strony, w tym film obrotu całego rynku, którego nie "
        "publikuje żadne inne źródło, wyścig sektorów na sektorach Shenwan, wyścig "
        "kapitalizacji piętnastu największych dnia oraz premia AH. **Hongkong** — "
        "macierz stóp zwrotu i kalendarz na indeksach i spółkach Hongkongu, cztery "
        "subindeksy Hang Seng w wyścigu. **USA** — te same dwie strony na amerykańskich "
        "indeksach i spółkach, dziesięć sektorowych ETF-ów SPDR w wyścigu, kwoty w "
        "dolarach. **Kryptowaluty** — sześć własnych stron, oferowanych poza Chinami "
        "kontynentalnymi i w żadnym miejscu wewnątrz nich, bo tam są oba źródła; "
        "wszędzie indziej kryptowaluty są rynkiem, który najwięcej osób chce widzieć na "
        "telefonie, a moneta jest notowana przez całą dobę, bez świąt do "
        "pominięcia.\n\nInterfejs dostępny w 14 językach.",
    ),
    "cs": (
        "Čtyři trhy: Čína A, Hongkong, USA a kryptoměny — nabízené, když odpoví zdroj "
        "krypta. Rozhraní je ve 14 jazycích.",
        "Čtyři trhy, každý s těmi stránkami, které jeho vlastní data dokážou nakrmit. "
        "**Čína A** — všechny stránky, včetně filmu obratu celého trhu, který žádný "
        "jiný zdroj neuvádí, závodu sektorů na sektorech Shenwan, závodu tržní "
        "kapitalizace patnácti největších dne a prémie AH. **Hongkong** — matice "
        "výnosů a kalendář na hongkongských indexech a titulech, čtyři subindexy Hang "
        "Seng v závodě. **USA** — tytéž dvě stránky na amerických indexech a "
        "titulech, deset sektorových ETF SPDR v závodě, částky v dolarech. "
        "**Kryptoměny** — šest vlastních stránek, nabízených mimo pevninskou Čínu a "
        "nikde uvnitř ní, protože tam jsou oba zdroje; všude jinde jsou kryptoměny "
        "trhem, který chce na telefonu vidět nejvíce lidí, a mince se obchoduje "
        "čtyřiadvacet hodin denně, bez svátku, který by bylo třeba "
        "přeskočit.\n\nRozhraní je ve 14 jazycích.",
    ),
    "ru": (
        "Четыре рынка: Китай (A-акции), Гонконг, США и криптовалюты — предлагаются, "
        "когда отвечает криптоисточник. Интерфейс доступен на 14 языках.",
        "Четыре рынка, у каждого — те страницы, которые способны прокормить его "
        "собственные данные. **Китай (A-акции)** — все страницы, включая ролик оборота "
        "всего рынка, который не публикует ни один другой источник, гонку секторов по "
        "секторам Shenwan, гонку капитализации пятнадцати крупнейших дня и премию AH. "
        "**Гонконг** — матрица доходности и календарь по индексам и бумагам Гонконга, "
        "четыре субиндекса Hang Seng в гонке. **США** — те же две страницы по "
        "американским индексам и бумагам, десять секторальных ETF SPDR в гонке, суммы в "
        "долларах. **Криптовалюты** — шесть собственных страниц, предлагаемых за "
        "пределами материкового Китая и нигде внутри него, потому что оба источника "
        "находятся там; везде в остальном мире криптовалюты — это рынок, который больше "
        "всего людей хотят видеть на экране телефона, а монета торгуется "
        "круглосуточно, без праздников, которые нужно "
        "пропускать.\n\nИнтерфейс доступен на 14 языках.",
    ),
    "tr": (
        "Dört piyasa: Çin A, Hong Kong, ABD ve kripto paralar — bir kripto kaynağı "
        "yanıt verdiğinde sunulur. Arayüz 14 dilde mevcut.",
        "Dört piyasa, her biri kendi verisinin besleyebildiği sayfalarla. **Çin A** — "
        "başka hiçbir kaynağın yayınlamadığı tüm piyasa hacmi filmi, Shenwan "
        "sektörlerinde sektör yarışı, günün en büyük on beş şirketinin piyasa değeri "
        "yarışı ve AH primi dahil tüm sayfalar. **Hong Kong** — Hong Kong endeksleri "
        "ve hisseleri üzerinde getiri matrisi ve takvim, yarışan dört Hang Seng alt "
        "endeksi. **ABD** — aynı iki sayfa Amerikan endeksleri ve hisseleri üzerinde, "
        "yarışan on SPDR sektör ETF'i, tutarlar dolar cinsinden. **Kripto** — kendine "
        "ait altı sayfa, Çin anakarası dışında sunulur ve içinde hiçbir yerde sunulmaz, "
        "çünkü iki kaynağı da oradadır; anakaranın dışında kripto, insanların "
        "telefonda görmek istediği en popüler piyasadır ve bir coin günün yirmi dört "
        "saati işlem görür, atlanacak tatil günü yoktur.\n\nArayüz 14 dilde mevcut.",
    ),
}

# 功能条第二条：名单后面补一句，说清加密货币是哪六页、在哪儿提供。
FEATURE_LINE = {
    "en-US": (
        "- Four markets: China A-share, Hong Kong, US, and cryptocurrency",
        "- Four markets: China A-shares, Hong Kong, US, and cryptocurrency — the last "
        "with six pages of its own, offered outside mainland China",
    ),
    "zh-Hans": (
        "- 覆盖A股、港股、美股与加密货币四大市场",
        "- 覆盖A股、港股、美股与加密货币四大市场——加密货币自带六页，只在中国大陆以外的市场提供",
    ),
    "zh-Hant": (
        "- 涵蓋陸股、港股、美股與加密貨幣四大市場",
        "- 涵蓋陸股、港股、美股與加密貨幣四大市場——加密貨幣自帶六頁，只在中國大陸以外的市場提供",
    ),
    "ja": (
        "- 中国A株・香港・米国・暗号資産の 4 市場に対応",
        "- 中国A株・香港・米国・暗号資産の 4 市場に対応——暗号資産は六つのページを持ち、中国"
        "本土以外の市場で提供",
    ),
    "ko": (
        "- 중국 A주식, 홍콩, 미국, 암호화폐 4개 시장 지원",
        "- 중국 A주식, 홍콩, 미국, 암호화폐 4개 시장 지원——암호화폐는 여섯 페이지를 가지며 "
        "중국 본토 밖 시장에서 제공",
    ),
    "de": (
        "- Vier Märkte: China A-Aktien, Hongkong, USA und Kryptowährungen",
        "- Vier Märkte: China A-Aktien, Hongkong, USA und Kryptowährungen — letztere "
        "mit sechs eigenen Seiten, angeboten außerhalb des chinesischen Festlands",
    ),
    "fr": (
        "- Quatre marchés : Chine A, Hong Kong, États-Unis et cryptomonnaies",
        "- Quatre marchés : Chine A, Hong Kong, États-Unis et cryptomonnaies — ces "
        "dernières avec six pages à elles, proposées hors de Chine continentale",
    ),
    "it": (
        "- Quattro mercati: Cina A, Hong Kong, Stati Uniti e criptovalute",
        "- Quattro mercati: Cina A, Hong Kong, Stati Uniti e criptovalute — quest'ultime "
        "con sei pagine proprie, offerte fuori dalla Cina continentale",
    ),
    "es": (
        "- Cuatro mercados: China A, Hong Kong, EE. UU. y criptomonedas",
        "- Cuatro mercados: China A, Hong Kong, EE. UU. y criptomonedas — estas últimas "
        "con seis páginas propias, ofrecidas fuera de China continental",
    ),
    "pt-BR": (
        "- Quatro mercados: China A, Hong Kong, EUA e criptomoedas",
        "- Quatro mercados: China A, Hong Kong, EUA e criptomoedas — estas últimas com "
        "seis páginas próprias, oferecidas fora da China continental",
    ),
    "pl": (
        "- Cztery rynki: Chiny A, Hongkong, USA i kryptowaluty",
        "- Cztery rynki: Chiny A, Hongkong, USA i kryptowaluty — te ostatnie z "
        "sześcioma własnymi stronami, oferowane poza Chinami kontynentalnymi",
    ),
    "cs": (
        "- Čtyři trhy: Čína A, Hongkong, USA a kryptoměny",
        "- Čtyři trhy: Čína A, Hongkong, USA a kryptoměny — ty poslední s šesti "
        "vlastními stránkami, nabízené mimo pevninskou Čínu",
    ),
    "ru": (
        "- Четыре рынка: Китай (A-акции), Гонконг, США и криптовалюты",
        "- Четыре рынка: Китай (A-акции), Гонконг, США и криптовалюты — у последних "
        "шесть собственных страниц, предлагаемых за пределами материкового Китая",
    ),
    "tr": (
        "- Dört piyasa: Çin A, Hong Kong, ABD ve kripto paralar",
        "- Dört piyasa: Çin A, Hong Kong, ABD ve kripto paralar — kripto kendine ait "
        "altı sayfayla, Çin anakarası dışında sunulur",
    ),
}


def main():
    path = listingtext.LISTING
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig").lstrip("\ufeff")
    joiner = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(joiner)
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
    failed = 0

    # **从后往前改**：14 段在同一份文件里，段号是全局行号。先改第一段，第二段之后的段号
    # 全体后移 —— 往前数第三个语言起，改的就都是别人的段了（实测：前四种语言看着好好地
    # 改对了，第五种开始整句对不上，而每一句都确实在文件里）。
    for n in reversed(range(len(listingtext.LANGS))):
        tag = listingtext.LANGS[n]
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        touched = 0

        for pair in (MARKET_LINE[tag], FEATURE_LINE[tag]):
            old, new = pair

            # 新句里的 \n\n 是分段，所以它落成三行：一段、一个空行、一段。
            wanted = new.split("\n")

            if old in lines[start:end]:
                at = start + lines[start:end].index(old)
                lines[at:at + 1] = wanted
                touched += 1
                end += len(wanted) - 1
            elif wanted[0] not in lines[start:end]:
                print(f"{tag}: 这两句都对不上 —— {old[:40]!r}")
                failed += 1

        print(f"{tag:9} {touched} 处")

    path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + joiner.join(lines).encode("utf-8"))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
