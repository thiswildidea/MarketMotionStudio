# -*- coding: utf-8 -*-
r"""让手册按市场说清楚「这个市场是拿来做什么的」，并说出加密货币属于哪一个市场。

两处改动，一件事：

1. **第 2 章「选择市场」**：四个市场各一条，原本只写「哪些页能用、哪些页隐藏」—— 那是
   一份限制清单，读完之后仍然不知道该挑哪个市场。每条补一句这个市场的核心页面。加密
   货币那条额外说两件事：它**只在中国大陆以外的市场出现**（两个源都在境外），而在那儿
   它是竖屏视频里最受欢迎的一类题材。
2. **加密 K 线章末条**：还在说「这三个页面」，而加密现在是六个页面。整条换掉，顺带把
   「为哪些市场准备的」讲清楚 —— 这一条原本只解释了为什么大陆的机器看不到它们。

**为什么是追加而不是重写**：那四条的原句是 14 种语言各自斟酌过的翻译，重写一遍只会得到
14 句各写各的。追加的句子是独立的，接在原句末尾，原句一个字不动。

**位置按 bullet 序号认，不按关键词认**（第 2 章第 1~4 条 bullet 依次是 A 股 / 港股 / 美股 /
加密货币）—— 章内顺序是这 14 份文件里唯一相同的事，各语言写「加密货币」这个词的方式
并不一致。

**幂等**：追加前先看这一句在不在；替换前先看旧词在不在。第二遍跑应当是 0 处改动。

文件是 **UTF-8 不带 BOM、LF**；BOM 与行尾照抄原文。

用法：python tools\port-market-emphasis-help.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"
sys.path.insert(0, str(ROOT / "tools"))

import listingtext  # noqa: E402

# 「这个市场是拿来做什么的」—— A 股 / 港股 / 美股 / 加密货币，各语言一句。
# 顺序与第 2 章里那四条 bullet 一一对应。中日韩不加前导空格（它们本来就不分词间空格）。
FOR = {
    "en-US": [
        " What it is for: the whole-market turnover reel — the only market whose source "
        "reports one — the sector race across the Shenwan level-one sectors, the market "
        "cap race over today's largest fifteen, and AH premium, one company's two "
        "listings against each other.",
        " What it is for: the return matrix and the calendar read on Hong Kong indices "
        "and listings, four Hang Seng sub-indices racing, and the Hang Seng trackers as "
        "presets.",
        " What it is for: the return matrix and the calendar read on US indices and "
        "listings, ten SPDR sector ETFs racing, and the broad presets — SPY, QQQ, DIA.",
        " Outside mainland China, crypto is by a wide margin the most-watched thing to "
        "put on a phone screen, and it brings six pages of its own: one coin's candles, "
        "a DCA plan, a holding's return, the gain calendar, and two pages about market "
        "cap.",
    ],
    "zh-Hans": [
        "它适合做的是：全市场成交额（只有这个市场的源给出这个数）、申万一级行业上的行业竞速、"
        "当天市值最大十五家的市值竞速，以及 AH 溢价——同一家公司两个上市地之间的比较。",
        "它适合做的是：港股指数与个股上的收益矩阵和涨跌日历、四个恒生分类指数之间的行业竞速，"
        "预设标的就是恒生系的几只基金。",
        "它适合做的是：美股指数与个股上的收益矩阵和涨跌日历、十只 SPDR 行业 ETF 之间的行业"
        "竞速，预设标的就是 SPY、QQQ、DIA 这些宽基。",
        "在中国大陆以外的市场，加密货币是竖屏视频里最受欢迎的一类题材，它带着六页：一个币的 "
        "K 线、定投计划、持仓收益、涨跌日历，以及两页市值。",
    ],
    "zh-Hant": [
        "它適合做的是：全市場成交額（只有這個市場的源給出這個數）、申萬一級行業上的行業競速、"
        "當天市值最大十五家的市值競速，以及 AH 溢價——同一家公司兩個上市地之間的比較。",
        "它適合做的是：港股指數與個股上的收益矩陣和漲跌日曆、四個恆生分類指數之間的行業競速，"
        "預設標的就是恆生系的幾檔基金。",
        "它適合做的是：美股指數與個股上的收益矩陣和漲跌日曆、十檔 SPDR 產業 ETF 之間的行業"
        "競速，預設標的就是 SPY、QQQ、DIA 這些寬基。",
        "在中國大陸以外的市場，加密貨幣是直式影片裡最受歡迎的一類題材，它帶著六頁：一個幣的 "
        "K 線、定期定額計畫、持倉收益、漲跌日曆，以及兩頁市值。",
    ],
    "ja": [
        "この市場でこそできるのは、市場全体の売買代金（この数字を出す源があるのはこの市場だけ）、"
        "申万一級業種によるセクター競争、その日の時価総額上位十五社による時価総額競争、そして "
        "AH プレミアム、つまり同じ企業の二つの上場先の比較です。",
        "香港の指数と銘柄で読むリターンマトリクスと騰落カレンダー、四つのハンセン分類指数による"
        "セクター競争、そして初期候補としてのハンセン系トラッカーです。",
        "米国の指数と銘柄で読むリターンマトリクスと騰落カレンダー、十本の SPDR セクター ETF "
        "によるセクター競争、そして SPY・QQQ・DIA といった主要な初期候補です。",
        "中国本土以外の市場では、暗号資産は縦型動画で最も注目される題材です。この市場には六つの"
        "ページがあります。あるコインのローソク足、積立計画、保有リターン、騰落カレンダー、そして"
        "時価総額の二ページです。",
    ],
    "ko": [
        "이 시장에서만 할 수 있는 것은 전체 시장 거래대금(이 수치를 주는 소스가 있는 시장은 "
        "여기뿐입니다), 선완 1차 업종 기준 업종 경주, 당일 시가총액 상위 15곳의 시가총액 경주, "
        "그리고 같은 기업의 두 상장지를 견주는 AH 프리미엄입니다.",
        "홍콩 지수와 종목으로 읽는 수익 매트릭스와 등락 달력, 항셍 4개 분류 지수로 벌이는 업종 "
        "경주, 그리고 기본 후보인 항셍 계열 트래커입니다.",
        "미국 지수와 종목으로 읽는 수익 매트릭스와 등락 달력, SPDR 섹터 ETF 10개로 벌이는 업종 "
        "경주, 그리고 SPY·QQQ·DIA 같은 대표 기본 후보입니다.",
        "중국 본토 밖 시장에서 암호화폐는 세로 영상에서 가장 많이 찾는 소재이며, 여섯 페이지를 "
        "거느립니다. 한 코인의 캔들, 적립식 계획, 보유 수익, 등락 달력, 그리고 시가총액 두 "
        "페이지입니다.",
    ],
    "de": [
        "Wofür er da ist: der Umsatzfilm für den Gesamtmarkt — der einzige Markt, dessen "
        "Quelle ihn meldet — das Sektor-Rennen über die Shenwan-Sektoren erster Ebene, "
        "das Rennen der Marktkapitalisierung über die heute größten fünfzehn und die "
        "AH-Prämie, die beiden Notierungen ein und desselben Unternehmens gegeneinander.",
        "Wofür er da ist: Renditematrix und Kalender, gelesen auf Hongkonger Indizes und "
        "Werten, das Sektor-Rennen über die vier Hang-Seng-Subindizes und die "
        "Hang-Seng-Tracker als Voreinstellungen.",
        "Wofür er da ist: Renditematrix und Kalender, gelesen auf US-Indizes und "
        "-Werten, das Sektor-Rennen über zehn SPDR-Sektor-ETFs und die breiten "
        "Voreinstellungen — SPY, QQQ, DIA.",
        "Außerhalb Chinas sind Kryptowährungen mit Abstand das gefragteste Thema für ein "
        "Video auf dem Handy, und sie bringen sechs eigene Seiten mit: die Kerzen einer "
        "Münze, einen Sparplan, die Rendite eines Bestands, den Kalender und zwei Seiten "
        "über die Marktkapitalisierung.",
    ],
    "fr": [
        "À quoi il sert : le film du volume d'échanges du marché entier — le seul marché "
        "dont la source le publie — la course de secteurs sur les secteurs Shenwan de "
        "premier niveau, la course de capitalisation sur les quinze plus grandes du jour, "
        "et la prime AH, les deux cotations d'une même société l'une contre l'autre.",
        "À quoi il sert : la matrice des rendements et le calendrier lus sur les indices "
        "et valeurs de Hong Kong, la course de secteurs sur les quatre sous-indices Hang "
        "Seng, et les trackers Hang Seng comme préréglages.",
        "À quoi il sert : la matrice des rendements et le calendrier lus sur les indices "
        "et valeurs américains, la course de secteurs sur dix ETF sectoriels SPDR, et "
        "les grands préréglages — SPY, QQQ, DIA.",
        "Hors de Chine continentale, les cryptomonnaies sont de loin le sujet le plus "
        "demandé pour une vidéo sur téléphone, et elles apportent six pages propres : "
        "les chandeliers d'une pièce, un plan d'achat programmé, le rendement d'une "
        "position, le calendrier et deux pages sur la capitalisation.",
    ],
    "it": [
        "A cosa serve: il film del controvalore dell'intero mercato — l'unico mercato la "
        "cui fonte lo riporta — la gara di settori sui settori Shenwan di primo livello, "
        "la gara di capitalizzazione sulle quindici maggiori di oggi e il premio AH, le "
        "due quotazioni di una stessa società l'una contro l'altra.",
        "A cosa serve: la matrice dei rendimenti e il calendario letti su indici e titoli "
        "di Hong Kong, la gara di settori sui quattro sottoindici Hang Seng e i tracker "
        "Hang Seng come preimpostazioni.",
        "A cosa serve: la matrice dei rendimenti e il calendario letti su indici e titoli "
        "statunitensi, la gara di settori su dieci ETF settoriali SPDR e le grandi "
        "preimpostazioni — SPY, QQQ, DIA.",
        "Fuori dalla Cina continentale, le criptovalute sono di gran lunga il tema più "
        "richiesto per un video sul telefono, e portano sei pagine proprie: le candele di "
        "una moneta, un piano di accumulo, il rendimento di una posizione, il calendario "
        "e due pagine sulla capitalizzazione.",
    ],
    "es": [
        "Para qué sirve: la película del volumen de todo el mercado — el único mercado "
        "cuya fuente lo publica — la carrera de sectores sobre los sectores Shenwan de "
        "primer nivel, la carrera de capitalización sobre las quince mayores de hoy y la "
        "prima AH, las dos cotizaciones de una misma empresa enfrentadas.",
        "Para qué sirve: la matriz de rentabilidad y el calendario leídos sobre índices "
        "y valores de Hong Kong, la carrera de sectores sobre los cuatro subíndices Hang "
        "Seng y los trackers Hang Seng como ajustes predefinidos.",
        "Para qué sirve: la matriz de rentabilidad y el calendario leídos sobre índices "
        "y valores estadounidenses, la carrera de sectores sobre diez ETF sectoriales "
        "SPDR y los grandes ajustes predefinidos — SPY, QQQ, DIA.",
        "Fuera de China continental, las criptomonedas son con diferencia el tema más "
        "buscado para un vídeo en el móvil, y traen seis páginas propias: las velas de "
        "una moneda, un plan de compra periódica, la rentabilidad de una posición, el "
        "calendario y dos páginas de capitalización.",
    ],
    "pt-BR": [
        "Para que serve: o filme do volume de todo o mercado — o único mercado cuja fonte "
        "o publica — a corrida de setores sobre os setores Shenwan de primeiro nível, a "
        "corrida de capitalização sobre as quinze maiores de hoje e o prémio AH, as duas "
        "cotações da mesma empresa frente a frente.",
        "Para que serve: a matriz de retorno e o calendário lidos sobre índices e valores "
        "de Hong Kong, a corrida de setores sobre os quatro subíndices Hang Seng e os "
        "trackers Hang Seng como predefinições.",
        "Para que serve: a matriz de retorno e o calendário lidos sobre índices e valores "
        "americanos, a corrida de setores sobre dez ETFs setoriais SPDR e as grandes "
        "predefinições — SPY, QQQ, DIA.",
        "Fora da China continental, as criptomoedas são de longe o tema mais procurado "
        "para um vídeo no telefone, e trazem seis páginas próprias: as velas de uma "
        "moeda, um plano de compra periódica, o retorno de uma posição, o calendário e "
        "duas páginas de capitalização.",
    ],
    "pl": [
        "Do czego służy: film obrotu całego rynku — jedyny rynek, którego źródło go "
        "podaje — wyścig sektorów na sektorach Shenwan pierwszego poziomu, wyścig "
        "kapitalizacji piętnastu największych dnia oraz premia AH, czyli dwie notowania "
        "tej samej spółki wobec siebie.",
        "Do czego służy: macierz stóp zwrotu i kalendarz czytane na indeksach i spółkach "
        "Hongkongu, wyścig sektorów na czterech subindeksach Hang Seng oraz trackery "
        "Hang Seng jako ustawienia domyślne.",
        "Do czego służy: macierz stóp zwrotu i kalendarz czytane na amerykańskich "
        "indeksach i spółkach, wyścig sektorów na dziesięciu sektorowych ETF-ach SPDR "
        "oraz szerokie ustawienia domyślne — SPY, QQQ, DIA.",
        "Poza Chinami kryptowaluty są zdecydowanie najczęściej szukanym tematem na wideo "
        "w telefonie i mają sześć własnych stron: świece jednej monety, plan regularnego "
        "kupna, wynik pozycji, kalendarz oraz dwie strony o kapitalizacji.",
    ],
    "cs": [
        "K čemu je: film obratu celého trhu — jediný trh, jehož zdroj ho uvádí — závod "
        "sektorů na sektorech Shenwan první úrovně, závod tržní kapitalizace patnácti "
        "největších dne a prémie AH, tedy dvě kotace téže společnosti proti sobě.",
        "K čemu je: matice výnosů a kalendář čtené na hongkongských indexech a titulech, "
        "závod sektorů na čtyřech subindexech Hang Seng a trackery Hang Seng jako "
        "předvolby.",
        "K čemu je: matice výnosů a kalendář čtené na amerických indexech a titulech, "
        "závod sektorů na deseti sektorových ETF SPDR a široké předvolby — SPY, QQQ, DIA.",
        "Mimo pevninskou Čínu jsou kryptoměny zdaleka nejžádanějším tématem pro video v "
        "telefonu a mají šest vlastních stránek: svíce jedné mince, plán pravidelného "
        "nákupu, výnos pozice, kalendář a dvě stránky o tržní kapitalizaci.",
    ],
    "ru": [
        "Для чего он: ролик оборота всего рынка — единственный рынок, чей источник его "
        "публикует — гонка секторов по секторам Shenwan первого уровня, гонка "
        "капитализации пятнадцати крупнейших дня и премия AH, то есть две котировки одной "
        "компании друг против друга.",
        "Для чего он: матрица доходности и календарь, считанные по индексам и бумагам "
        "Гонконга, гонка секторов по четырём субиндексам Hang Seng и трекеры Hang Seng "
        "как предустановки.",
        "Для чего он: матрица доходности и календарь, считанные по американским индексам "
        "и бумагам, гонка секторов по десяти секторальным ETF SPDR и широкие "
        "предустановки — SPY, QQQ, DIA.",
        "За пределами материкового Китая криптовалюты — безусловно самая востребованная "
        "тема для видео на телефоне, и у них шесть собственных страниц: свечи одной "
        "монеты, план регулярной покупки, доходность позиции, календарь и две страницы о "
        "капитализации.",
    ],
    "tr": [
        "Ne için: tüm piyasanın hacim filmi — bu sayıyı yayınlayan kaynağı olan tek "
        "piyasa — Shenwan birinci düzey sektörlerinde sektör yarışı, günün en büyük on "
        "beş şirketinin piyasa değeri yarışı ve AH primi, yani aynı şirketin iki "
        "kotasyonunun karşı karşıya gelmesi.",
        "Ne için: Hong Kong endeksleri ve hisseleri üzerinden okunan getiri matrisi ve "
        "takvim, dört Hang Seng alt endeksinde sektör yarışı ve ön ayar olarak Hang Seng "
        "takip fonları.",
        "Ne için: ABD endeksleri ve hisseleri üzerinden okunan getiri matrisi ve takvim, "
        "on SPDR sektör ETF'i ile sektör yarışı ve SPY, QQQ, DIA gibi geniş ön ayarlar.",
        "Çin anakarası dışında kripto, telefonda izlenen videolar için açık ara en çok "
        "aranan konu ve kendisine ait altı sayfası var: bir coinin mumları, düzenli alım "
        "planı, bir pozisyonun getirisi, takvim ve piyasa değeriyle ilgili iki sayfa.",
    ],
}

# 加密那条还在说「三页」，而加密现在是六个页面。逐语言换掉那个数词。
SIX = {
    "en-US": ("the three crypto pages", "the six crypto pages"),
    "zh-Hans": ("加密货币的三页", "加密货币的六页"),
    "zh-Hant": ("加密貨幣的三頁", "加密貨幣的六頁"),
    "ja": ("暗号資産の 3 ページ", "暗号資産の 6 ページ"),
    "ko": ("암호화폐 세 페이지", "암호화폐 여섯 페이지"),
    "de": ("die drei Krypto-Seiten", "die sechs Krypto-Seiten"),
    "fr": ("les trois pages crypto", "les six pages crypto"),
    "it": ("le tre pagine cripto", "le sei pagine cripto"),
    "es": ("las tres páginas cripto", "las seis páginas cripto"),
    "pt-BR": ("as três páginas cripto", "as seis páginas cripto"),
    "pl": ("trzy strony krypto", "sześć stron krypto"),
    "cs": ("tři krypto stránky", "šest krypto stránek"),
    "ru": ("три криптостраницы", "шесть криптостраниц"),
    "tr": ("üç kripto sayfası", "altı kripto sayfası"),
}

# 同一章里还有一句「这三页上都不做复权」—— 加密现在是六个页面，这句话也是三处之一。
ADJUST = {
    "en-US": ("anywhere on these three pages", "anywhere on these six pages"),
    "zh-Hans": ("这三页上任何地方都不做复权", "这六页上任何地方都不做复权"),
    "zh-Hant": ("這三頁上任何地方都不做復權", "這六頁上任何地方都不做復權"),
    "ja": ("この 3 ページではどこにも調整をかけていません",
           "この 6 ページではどこにも調整をかけていません"),
    "ko": ("이 세 페이지에서는 어디에도 조정을 하지 않습니다",
           "이 여섯 페이지에서는 어디에도 조정을 하지 않습니다"),
    "de": ("auf diesen drei Seiten wird nirgends bereinigt",
           "auf diesen sechs Seiten wird nirgends bereinigt"),
    "fr": ("sur ces trois pages", "sur ces six pages"),
    "it": ("su queste tre pagine", "su queste sei pagine"),
    "es": ("en estas tres páginas", "en estas seis páginas"),
    "pt-BR": ("nestas três páginas", "nestas seis páginas"),
    "pl": ("na tych trzech stronach", "na tych sześciu stronach"),
    "cs": ("na těchto třech stránkách", "na těchto šesti stránkách"),
    "ru": ("на этих трёх страницах", "на этих шести страницах"),
    "tr": ("bu üç sayfada", "bu altı sayfada"),
}

# 加密 K 线章的末条：整条换掉。三页改六页，并说出这一组页面是为哪些市场准备的 —— 原来
# 那条只解释了为什么中国大陆的机器看不到它，而没说在看得见的地方它是拿来做什么的。
TAIL = {
    "en-US": (
        "- **These three pages appear only when a source answers.** Both sources are "
        "outside the mainland's reach, so a machine inside it simply does not get them "
        "in the menu — three items offering data they cannot fetch would be three items "
        "that fail.",
        "- **These six pages appear only where a source answers.** Both sources sit "
        "outside mainland China, so a machine inside it never sees them in the menu — six "
        "items offering data they cannot fetch would be six items that fail. Everywhere "
        "else, crypto is by a wide margin the most-watched market to put on a phone "
        "screen, and these are the pages for it: a coin trades around the clock, every "
        "day of the year, with no holiday to step over.",
    ),
    "zh-Hans": (
        "- **这三个页面只在某个源应答时出现。** 两个源都在中国大陆之外，所以在大陆的机器上"
        "它们根本不进菜单——三个取不到数据的入口，就是三个会失败的入口。",
        "- **这六个页面只在某个源应答的市场出现。** 两个源都在中国大陆之外，所以在大陆的"
        "机器上它们根本不进菜单——六个取不到数据的入口，就是六个会失败的入口。在中国大陆"
        "以外的市场，加密货币是竖屏视频里最受欢迎的一类题材，这六页就是为它准备的：币全年"
        "无休、一天二十四小时都在交易，区间里没有任何要跳过的休市日。",
    ),
    "zh-Hant": (
        "- **這三個頁面只在某個源應答時出現。** 兩個源都在中國大陸之外，所以在大陸的機器上"
        "它們根本不進選單——三個取不到數據的入口，就是三個會失敗的入口。",
        "- **這六個頁面只在某個源應答的市場出現。** 兩個源都在中國大陸之外，所以在大陸的"
        "機器上它們根本不進選單——六個取不到數據的入口，就是六個會失敗的入口。在中國大陸"
        "以外的市場，加密貨幣是直式影片裡最受歡迎的一類題材，這六頁就是為它準備的：幣全年"
        "無休、一天二十四小時都在交易，期間裡沒有任何要跳過的休市日。",
    ),
    "ja": (
        "- **この 3 つのページは、どちらかのソースが応答したときだけ表示されます。** "
        "どちらのソースも中国本土からは届かないため、その環境ではメニューに現れません。"
        "取れないデータを並べる項目は、失敗する項目になるだけだからです。",
        "- **この 6 つのページは、ソースが応答する市場でだけ表示されます。** どちらの"
        "ソースも中国本土からは届かないため、その環境ではメニューに現れません。取れない"
        "データを並べる項目は、失敗する項目になるだけだからです。中国本土以外の市場では、"
        "暗号資産は縦型動画で最も注目される題材であり、この 6 ページはそのためのものです。"
        "コインは年中無休、一日二十四時間取引され、飛ばすべき休場日はありません。",
    ),
    "ko": (
        "- **이 세 페이지는 소스가 응답할 때만 나타납니다.** 두 소스 모두 중국 본토에서는 "
        "닿지 않으므로 그 환경에서는 메뉴에 아예 나오지 않습니다. 가져올 수 없는 데이터를 "
        "내놓는 항목은 실패하는 항목일 뿐입니다.",
        "- **이 여섯 페이지는 소스가 응답하는 시장에서만 나타납니다.** 두 소스 모두 중국 "
        "본토에서는 닿지 않으므로 그 환경에서는 메뉴에 아예 나오지 않습니다. 가져올 수 없는 "
        "데이터를 내놓는 항목은 실패하는 항목일 뿐입니다. 중국 본토 밖 시장에서 암호화폐는 "
        "세로 영상에서 가장 많이 찾는 소재이며, 이 여섯 페이지가 바로 그것을 위한 것입니다. "
        "코인은 연중무휴, 하루 스물네 시간 거래되므로 건너뛸 휴장일이 없습니다.",
    ),
    "de": (
        "- **Diese drei Seiten erscheinen nur, wenn eine Quelle antwortet.** Beide "
        "Quellen liegen außerhalb der Reichweite des Festlands; ein Rechner dort bekommt "
        "sie im Menü schlicht nicht — drei Einträge, die Daten anbieten, die sie nicht "
        "holen können, wären drei Einträge, die scheitern.",
        "- **Diese sechs Seiten erscheinen nur, wo eine Quelle antwortet.** Beide Quellen "
        "liegen außerhalb der Reichweite des chinesischen Festlands; ein Rechner dort "
        "bekommt sie im Menü schlicht nicht — sechs Einträge, die Daten anbieten, die sie "
        "nicht holen können, wären sechs Einträge, die scheitern. Außerhalb Chinas sind "
        "Kryptowährungen mit Abstand das gefragteste Thema für ein Handy-Video, und genau "
        "dafür sind diese sechs Seiten da: Eine Münze wird rund um die Uhr gehandelt, an "
        "jedem Tag des Jahres, ohne übersprungenen Feiertag.",
    ),
    "fr": (
        "- **Ces trois pages n'apparaissent que lorsqu'une source répond.** Les deux "
        "sources sont hors de portée de la Chine continentale : une machine qui s'y "
        "trouve ne les voit tout simplement pas dans le menu — trois entrées offrant des "
        "données qu'elles ne peuvent pas récupéreraient seraient trois entrées qui "
        "échouent.",
        "- **Ces six pages n'apparaissent que là où une source répond.** Les deux sources "
        "sont hors de portée de la Chine continentale : une machine qui s'y trouve ne les "
        "voit tout simplement pas dans le menu — six entrées offrant des données qu'elles "
        "ne peuvent pas récupérer seraient six entrées qui échouent. Partout ailleurs, "
        "les cryptomonnaies sont de loin le sujet le plus recherché pour une vidéo sur "
        "téléphone, et ces six pages sont faites pour lui : une pièce se négocie "
        "vingt-quatre heures sur vingt-quatre, chaque jour de l'année, sans jour férié à "
        "sauter.",
    ),
    "it": (
        "- **Queste tre pagine appaiono solo quando una fonte risponde.** Entrambe le "
        "fonti sono fuori dalla portata della Cina continentale, quindi una macchina lì "
        "dentro non le trova affatto nel menu: tre voci che offrono dati che non possono "
        "recuperare sarebbero tre voci che falliscono.",
        "- **Queste sei pagine appaiono solo dove una fonte risponde.** Entrambe le fonti "
        "sono fuori dalla portata della Cina continentale, quindi una macchina lì dentro "
        "non le trova affatto nel menu: sei voci che offrono dati che non possono "
        "recuperare sarebbero sei voci che falliscono. Ovunque altrove, le criptovalute "
        "sono di gran lunga il tema più richiesto per un video sul telefono, e queste sei "
        "pagine sono fatte per quello: una moneta si scambia ventiquattro ore su "
        "ventiquattro, ogni giorno dell'anno, senza festività da saltare.",
    ),
    "es": (
        "- **Estas tres páginas solo aparecen cuando una fuente responde.** Ambas fuentes "
        "están fuera del alcance de China continental, así que un equipo allí simplemente "
        "no las ve en el menú: tres entradas que ofrecen datos que no pueden obtener "
        "serían tres entradas que fallan.",
        "- **Estas seis páginas solo aparecen donde una fuente responde.** Ambas fuentes "
        "están fuera del alcance de China continental, así que un equipo allí simplemente "
        "no las ve en el menú: seis entradas que ofrecen datos que no pueden obtener "
        "serían seis entradas que fallan. Fuera de China, las criptomonedas son con "
        "diferencia el tema más buscado para un vídeo en el móvil, y estas seis páginas "
        "están hechas para eso: una moneda cotiza las veinticuatro horas, todos los días "
        "del año, sin festivo que saltar.",
    ),
    "pt-BR": (
        "- **Estas três páginas aparecem apenas quando uma fonte responde.** Ambas as "
        "fontes estão fora do alcance da China continental, então uma máquina lá "
        "simplesmente não as recebe no menu: três itens oferecendo dados que não conseguem "
        "buscar seriam três itens que falham.",
        "- **Estas seis páginas aparecem apenas onde uma fonte responde.** Ambas as fontes "
        "estão fora do alcance da China continental, então uma máquina lá simplesmente não "
        "as recebe no menu: seis itens oferecendo dados que não conseguem buscar seriam "
        "seis itens que falham. Fora da China, as criptomoedas são de longe o tema mais "
        "procurado para um vídeo no telefone, e estas seis páginas são feitas para isso: "
        "uma moeda é negociada vinte e quatro horas por dia, todos os dias do ano, sem "
        "feriado a saltar.",
    ),
    "pl": (
        "- **Te trzy strony pojawiają się tylko wtedy, gdy jakieś źródło odpowie.** Oba "
        "źródła są poza zasięgiem Chin kontynentalnych, więc komputer tam po prostu nie "
        "dostaje ich w menu: trzy pozycje oferujące dane, których nie mogą pobrać, "
        "byłyby trzema pozycjami, które zawodzą.",
        "- **Te sześć stron pojawia się tylko tam, gdzie jakieś źródło odpowie.** Oba "
        "źródła są poza zasięgiem Chin kontynentalnych, więc komputer tam po prostu nie "
        "dostaje ich w menu: sześć pozycji oferujących dane, których nie mogą pobrać, "
        "byłoby sześcioma pozycjami, które zawodzą. Poza Chinami kryptowaluty są "
        "zdecydowanie najczęściej szukanym tematem na pionowe wideo i właśnie dla niego "
        "jest tych sześć stron: moneta jest notowana przez całą dobę, każdego dnia roku, "
        "bez świąt do pominięcia.",
    ),
    "cs": (
        "- **Tyto tři stránky se objeví jen tehdy, když nějaký zdroj odpoví.** Oba zdroje "
        "jsou mimo dosah pevninské Číny, takže počítač tam je v menu prostě nedostane: "
        "tři položky nabízející data, která nemohou načíst, by byly tři položky, které "
        "selžou.",
        "- **Těchto šest stránek se objeví jen tam, kde nějaký zdroj odpoví.** Oba zdroje "
        "jsou mimo dosah pevninské Číny, takže počítač tam je v menu prostě nedostane: "
        "šest položek nabízejících data, která nemohou načíst, by bylo šest položek, "
        "které selžou. Mimo pevninskou Čínu jsou kryptoměny zdaleka nejžádanějším tématem "
        "pro video na telefonu a právě pro ně je těchto šest stránek: mince se obchoduje "
        "čtyřiadvacet hodin denně, každý den v roce, bez svátku, který by bylo třeba "
        "přeskočit.",
    ),
    "ru": (
        "- **Эти три страницы появляются только тогда, когда какой-то источник отвечает.** "
        "Оба источника вне досягаемости материкового Китая, поэтому машина там просто не "
        "получит их в меню: три пункта, предлагающие данные, которые они не могут "
        "получить, были бы тремя пунктами, которые не работают.",
        "- **Эти шесть страниц появляются только там, где какой-то источник отвечает.** "
        "Оба источника вне досягаемости материкового Китая, поэтому машина там просто не "
        "получит их в меню: шесть пунктов, предлагающих данные, которые они не могут "
        "получить, были бы шестью пунктами, которые не работают. За пределами материкового "
        "Китая криптовалюты — безусловно самая востребованная тема для видео на телефоне, "
        "и эти шесть страниц сделаны для неё: монета торгуется круглосуточно, каждый день "
        "в году, без праздников, которые нужно пропускать.",
    ),
    "tr": (
        "- **Bu üç sayfa yalnızca bir kaynak yanıt verdiğinde görünür.** Her iki kaynak da "
        "anakaranın erişiminin dışında, bu yüzden oradaki bir makine menüde onları hiç "
        "görmez: getiremeyecekleri veriyi sunan üç girdi, başarısız olan üç girdi olurdu.",
        "- **Bu altı sayfa yalnızca bir kaynağın yanıt verdiği yerde görünür.** Her iki "
        "kaynak da anakaranın erişiminin dışında, bu yüzden oradaki bir makine menüde "
        "onları hiç görmez: getiremeyecekleri veriyi sunan altı girdi, başarısız olan altı "
        "girdi olurdu. Çin dışında kripto, telefonda izlenen videolar için açık ara en "
        "çok aranan konudur ve bu altı sayfa onun için yapıldı: bir coin günün yirmi dört "
        "saati, yılın her günü işlem görür; atlanacak tatil günü yoktur.",
    ),
}

# 加密 K 线章在手册里是第几章，从导航推 —— 不写死序号。
CANDLE = listingtext.chapter_of("NavCryptoCandle")

# 第 2 章是「选择市场」：两章领头章之后的第 0 章。
MARKET = 0


def bullets_of(lines, heads, index):
    start = heads[index]
    end = heads[index + 1] if index + 1 < len(heads) else len(lines)

    return [i for i in range(start, end) if lines[i].startswith("- ")]


def main():
    failed = 0

    for tag in listingtext.LANGS:
        path = HELP / ("help-%s.md" % tag)
        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig").lstrip("\ufeff")
        joiner = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(joiner)
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        touched = 0

        # ---- 一、第 2 章四条市场 bullet ----
        market = bullets_of(lines, heads, MARKET)

        if len(market) != 5:
            print(f"{tag}: 「选择市场」章有 {len(market)} 条，本该是 5 条")
            failed += 1
            continue

        six_old, six_new = SIX[tag]

        for slot, at in enumerate(market[1:5], start=0):
            # 加密货币那条（第 4 条）还在说三页。
            if slot == 3 and six_old in lines[at]:
                lines[at] = lines[at].replace(six_old, six_new)
                touched += 1
            elif slot == 3 and six_new not in lines[at]:
                print(f"{tag}: 加密那条里既没有 {six_old!r} 也没有 {six_new!r}")
                failed += 1

            said = FOR[tag][slot]

            if said in lines[at]:
                continue

            # 中文与日文不写词间空格，追加时也不能带一个进来；其余语言那句自带前导空格。
            lines[at] = lines[at] + (said.lstrip() if tag in listingtext.NO_SPACE else said)
            touched += 1

        # ---- 二、加密 K 线章：三页改六页，末条整条换掉 ----
        candle = bullets_of(lines, heads, CANDLE)
        three, six = ADJUST[tag]

        if three in lines[candle[3]]:
            lines[candle[3]] = lines[candle[3]].replace(three, six)
            touched += 1
        elif six not in lines[candle[3]]:
            print(f"{tag}: 加密 K 线章第 4 条里既没有 {three!r} 也没有 {six!r}")
            failed += 1

        old, new = TAIL[tag]

        if old in lines:
            lines[lines.index(old)] = new
            touched += 1
        elif new not in lines:
            print(f"{tag}: 加密 K 线章末条两句都对不上")
            failed += 1

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"")
                         + joiner.join(lines).encode("utf-8"))
        print(f"{tag:9} {touched} 处")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
