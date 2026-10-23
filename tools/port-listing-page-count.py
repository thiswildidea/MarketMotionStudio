# -*- coding: utf-8 -*-
r"""把商店文案的页数从 25 校准到 30（14 语言，docs/store-listing.md）。

1.0.18 上架时清点漏了五个页面：说明里的图表清单、产品功能的图表枚举、四市场段与
市场功能条里的「加密货币七页」都停留在 25/7（德语与波兰语的功能条甚至还写着 6 页，
捷克语同——更早的口径）。实际是 30 页：19 个股票页 + 11 个加密页。缺的五个：

- 实时持仓收益（股票页，1.0.15 起就有，从没进过清单）；
- 加密货币比较 / 涨跌 / 占比 / 年度回报（1.0.18 上架、1.0.20 才补进手册的四页）。

**新条目的句子不手写**——说明里的页面条目与手册章节首句是同一句话
（`listingtext.first_sentence`），标题用各语言 resw 的导航名。四市场段的「七页」
改成「十一页」，功能条里德/波/捷三处残留的「六页」一并纠正。

幂等：跑第二遍应当是「改了 0 处」。store-listing.md 是 **CRLF 无 BOM**，剥掉 `\r`
比对，写回照原样。

用法：python tools\port-listing-page-count.py
"""
import html  # noqa: F401  （标题取自 resw 时若带 &amp; 之类，用它还原）
import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

REPO = listingtext.HELP.parents[3]
LISTING = REPO / "docs" / "store-listing.md"

# 「25 页」那一行的开头（不含行尾两个空格的硬换行）。
INTRO = {
    "zh-Hans": ("二十五大图表页：", "三十大图表页："),
    "zh-Hant": ("二十五大圖表頁：", "三十大圖表頁："),
    "en-US": ("Twenty-five chart pages:", "Thirty chart pages:"),
    "ja": ("25 つのチャートページ：", "30 つのチャートページ："),
    "ko": ("25가지 차트 페이지:", "30가지 차트 페이지:"),
    "de": ("Fünfundzwanzig Diagrammseiten:", "Dreißig Diagrammseiten:"),
    "fr": ("Vingt-cinq pages de graphiques :", "Trente pages de graphiques :"),
    "it": ("Venticinque pagine di grafici:", "Trenta pagine di grafici:"),
    "es": ("Veinticinco páginas de gráficos:", "Treinta páginas de gráficos:"),
    "pt-BR": ("Vinte e cinco páginas de gráficos:", "Trinta páginas de gráficos:"),
    "pl": ("Dwadzieścia pięć stron wykresów:", "Trzydzieści stron wykresów:"),
    "cs": ("Dvacet pět stránek s grafy:", "Třicet stránek s grafy:"),
    "ru": ("Двадцать пять страниц с графиками:", "Тридцать страниц с графиками:"),
    "tr": ("Yirmi beş grafik sayfası:", "Otuz grafik sayfası:"),
}

# 四市场段与市场功能条里的「七页」（个别语言功能条还写着六页，一并纠正）。
# 每项是一组 (旧, 新)；同一语言里的多条会各改各的。
PAGES_PHRASES = {
    "zh-Hans": [("它自己有七页", "它自己有十一页"), ("加密货币自带七页", "加密货币自带十一页")],
    "zh-Hant": [("它自己有七頁", "它自己有十一頁"), ("自帶七頁", "自帶十一頁")],
    "en-US": [("seven pages of its own", "eleven pages of its own")],
    "ja": [("七つのページを持ち", "十一のページを持ち")],
    "ko": [("자체 페이지 일곱 개", "자체 페이지 열한 개"),
           ("암호화폐는 여섯 페이지", "암호화폐는 열한 페이지")],
    "de": [("sieben eigene Seiten", "elf eigene Seiten"),
           ("mit sechs eigenen Seiten", "mit elf eigenen Seiten")],
    "fr": [("sept pages à elles", "onze pages à elles")],
    "it": [("sette pagine proprie", "undici pagine proprie")],
    "es": [("siete páginas propias", "once páginas propias")],
    "pt-BR": [("sete páginas próprias", "onze páginas próprias")],
    "pl": [("siedem własnych stron", "jedenaście własnych stron"),
           ("z sześcioma własnymi stronami", "z jedenastoma własnymi stronami")],
    "cs": [("sedm vlastních stránek", "jedenáct vlastních stránek"),
           ("s šesti vlastními stránkami", "s jedenácti vlastními stránkami")],
    "ru": [("семь собственных страниц", "одиннадцать собственных страниц")],
    "tr": [("kendine ait yedi sayfa", "kendine ait on bir sayfa")],
}

# 产品功能里那条图表枚举：整行替换（计数词、补实时持仓收益、补四个加密页一步到位）。
FEATURE_LINE = {
    "zh-Hans": (
        "- 二十五种图表：成交额、量价、板块竞速、市值榜、AH 溢价、收益矩阵、涨跌日历、定投、持仓、K线、极端交易日、汇率走廊、指数长跑、大类资产、回撤与修复、持有胜率、债市固收、市值历程、加密货币 K 线、加密货币定投、加密货币持仓、加密货币涨跌日历、加密货币市值历程、加密货币市值榜、加密货币月度收益",
        "- 三十种图表：成交额、量价、板块竞速、市值榜、AH 溢价、收益矩阵、涨跌日历、定投、持仓、实时持仓收益、K线、极端交易日、汇率走廊、指数长跑、大类资产、回撤与修复、持有胜率、债市固收、市值历程、加密货币 K 线、加密货币定投、加密货币持仓、加密货币涨跌日历、加密货币市值历程、加密货币市值榜、加密货币月度收益、加密货币比较、加密货币涨跌、加密货币占比、加密货币年度回报"),
    "zh-Hant": (
        "- 二十五種圖表：成交額、量價、板塊競速、市值榜、AH 溢價、收益矩陣、漲跌日曆、定期定額、持倉、K線、極端交易日、匯率走廊、指數長跑、大類資產、回撤與修復、持有勝率、債市固收、市值歷程、加密貨幣 K 線、加密貨幣定投、加密貨幣持倉、加密貨幣漲跌日曆、加密貨幣市值歷程、加密貨幣市值榜、加密貨幣月度收益",
        "- 三十種圖表：成交額、量價、板塊競速、市值榜、AH 溢價、收益矩陣、漲跌日曆、定期定額、持倉、即時持倉收益、K線、極端交易日、匯率走廊、指數長跑、大類資產、回撤與修復、持有勝率、債市固收、市值歷程、加密貨幣 K 線、加密貨幣定投、加密貨幣持倉、加密貨幣漲跌日曆、加密貨幣市值歷程、加密貨幣市值榜、加密貨幣月度收益、加密貨幣比較、加密貨幣漲跌、加密貨幣佔比、加密貨幣年度報酬"),
    "en-US": (
        "- Twenty-five charts: turnover, volume, sector race, market cap, AH premium, return matrix, calendar, DCA, position replay, candles, Extreme days, Currency corridors, Index race, Asset classes, Drawdowns, Hold odds, Bond market, Market value, Crypto Candles, Crypto DCA, Crypto Holdings, Crypto Gain Calendar, Crypto Market Cap History, Crypto Market Cap Race, Crypto Monthly Returns",
        "- Thirty charts: turnover, volume, sector race, market cap, AH premium, return matrix, calendar, DCA, position replay, live P&L, candles, Extreme days, Currency corridors, Index race, Asset classes, Drawdowns, Hold odds, Bond market, Market value, Crypto Candles, Crypto DCA, Crypto Holdings, Crypto Gain Calendar, Crypto Market Cap History, Crypto Market Cap Race, Crypto Monthly Returns, Crypto Compare, Crypto Movers, Crypto Dominance, Crypto Annual Returns"),
    "ja": (
        "- 25 種類のチャート：売買代金、量価、セクターレース、時価総額レース、A/H プレミアム、リターンマトリクス、カレンダー、積立、保有収益、ローソク足、極端な日、為替コリドー、指数レース、資産クラス、ドローダウン、保有勝率、債券市場、時価総額の推移、暗号資産のローソク足、暗号資産のつみたて、暗号資産の保有、暗号資産の値動きカレンダー、暗号資産の時価総額の推移、暗号資産の時価総額レース、暗号資産の月次リターン",
        "- 30 種類のチャート：売買代金、量価、セクターレース、時価総額レース、A/H プレミアム、リターンマトリクス、カレンダー、積立、保有収益、リアルタイム保有損益、ローソク足、極端な日、為替コリドー、指数レース、資産クラス、ドローダウン、保有勝率、債券市場、時価総額の推移、暗号資産のローソク足、暗号資産のつみたて、暗号資産の保有、暗号資産の値動きカレンダー、暗号資産の時価総額の推移、暗号資産の時価総額レース、暗号資産の月次リターン、暗号資産の比較、暗号資産の値動き、暗号資産の占有率、暗号資産の年間収益"),
    "ko": (
        "- 25가지 차트: 거래대금, 거래량, 업종 경주, 시가총액 레이스, A/H 프리미엄, 수익 매트릭스, 달력, 적립 투자, 보유 수익, 캔들、극단의 날、환율 코리도、지수 레이스、자산군、낙폭、보유 승률、채권시장、시가총액 추이、크립토 캔들、크립토 적립、크립토 보유、크립토 등락 캘린더、크립토 시가총액 추이、크립토 시가총액 레이스、크립토 월간 수익률",
        "- 30가지 차트: 거래대금, 거래량, 업종 경주, 시가총액 레이스, A/H 프리미엄, 수익 매트릭스, 달력, 적립 투자, 보유 수익, 실시간 보유 손익, 캔들、극단의 날、환율 코리도、지수 레이스、자산군、낙폭、보유 승률、채권시장、시가총액 추이、크립토 캔들、크립토 적립、크립토 보유、크립토 등락 캘린더、크립토 시가총액 추이、크립토 시가총액 레이스、크립토 월간 수익률、암호화폐 비교、암호화폐 등락、암호화폐 점유율、암호화폐 연간 수익"),
    "de": (
        "- Fünfundzwanzig Diagramme: Umsatz, Volumen, Sektor-Rennen, Marktkapitalisierungs-Rennen, A/H-Prämie, Renditematrix, Kalender, Sparplan, Depotrendite, Kerzen, Extreme Tage, Währungskorridore, Index-Rennen, Anlageklassen, Rücksetzer, Haltequote, Anleihemarkt, Marktwert, Krypto-Kerzen, Krypto-Sparplan, Krypto-Bestände, Krypto-Gewinnkalender, Krypto-Marktkapitalisierung im Verlauf, Rennen der Krypto-Marktkapitalisierung, Krypto-Monatsrenditen",
        "- Dreißig Diagramme: Umsatz, Volumen, Sektor-Rennen, Marktkapitalisierungs-Rennen, A/H-Prämie, Renditematrix, Kalender, Sparplan, Depotrendite, Depot live, Kerzen, Extreme Tage, Währungskorridore, Index-Rennen, Anlageklassen, Rücksetzer, Haltequote, Anleihemarkt, Marktwert, Krypto-Kerzen, Krypto-Sparplan, Krypto-Bestände, Krypto-Gewinnkalender, Krypto-Marktkapitalisierung im Verlauf, Rennen der Krypto-Marktkapitalisierung, Krypto-Monatsrenditen, Krypto-Vergleich, Krypto-Bewegungen, Krypto-Dominanz, Krypto-Jahresrenditen"),
    "fr": (
        "- Vingt-cinq graphiques : volume d'échanges, volume et rotation, course de secteurs, course des capitalisations, prime A/H, matrice des rendements, calendrier, plan DCA, rendement de position, chandeliers, Jours extrêmes, Couloirs de devises, Course des indices, Classes d'actifs, Reculs, Taux de réussite, Marché obligataire, Valeur de marché, Chandeliers crypto, DCA crypto, Portefeuille crypto, Calendrier des hausses et baisses crypto, Historique de capitalisation crypto, Course des capitalisations crypto, Rendements mensuels crypto",
        "- Trente graphiques : volume d'échanges, volume et rotation, course de secteurs, course des capitalisations, prime A/H, matrice des rendements, calendrier, plan DCA, rendement de position, P&L en direct, chandeliers, Jours extrêmes, Couloirs de devises, Course des indices, Classes d'actifs, Reculs, Taux de réussite, Marché obligataire, Valeur de marché, Chandeliers crypto, DCA crypto, Portefeuille crypto, Calendrier des hausses et baisses crypto, Historique de capitalisation crypto, Course des capitalisations crypto, Rendements mensuels crypto, Comparaison crypto, Mouvements crypto, Dominance crypto, Rendements annuels crypto"),
    "it": (
        "- Venticinque grafici: scambi, volume e rotazione, corsa dei settori, corsa delle capitalizzazioni, premio A/H, matrice dei rendimenti, calendario, piano DCA, rendimento della posizione, candele, Giorni estremi, Corridoi valutari, Corsa degli indici, Classi di attività, Ribassi, Tasso di riuscita, Mercato obbligazionario, Valore di mercato, Candele crypto, DCA crypto, Portafoglio crypto, Calendario dei movimenti crypto, Storia della capitalizzazione crypto, Corsa della capitalizzazione crypto, Rendimenti mensili crypto",
        "- Trenta grafici: scambi, volume e rotazione, corsa dei settori, corsa delle capitalizzazioni, premio A/H, matrice dei rendimenti, calendario, piano DCA, rendimento della posizione, P&L in tempo reale, candele, Giorni estremi, Corridoi valutari, Corsa degli indici, Classi di attività, Ribassi, Tasso di riuscita, Mercato obbligazionario, Valore di mercato, Candele crypto, DCA crypto, Portafoglio crypto, Calendario dei movimenti crypto, Storia della capitalizzazione crypto, Corsa della capitalizzazione crypto, Rendimenti mensili crypto, Confronto crypto, Movimenti crypto, Dominanza crypto, Rendimenti annuali crypto"),
    "es": (
        "- Veinticinco gráficos: volumen negociado, volumen y rotación, carrera de sectores, carrera de capitalización, prima A/H, matriz de rentabilidad, calendario, plan DCA, rentabilidad de cartera, velas, Días extremos, Corredores de divisas, Carrera de índices, Clases de activos, Caídas, Tasa de acierto, Renta fija, Valor de mercado, Velas cripto, DCA cripto, Cartera cripto, Calendario de ganancias cripto, Historial de capitalización cripto, Carrera de capitalización cripto, Rendimientos mensuales cripto",
        "- Treinta gráficos: volumen negociado, volumen y rotación, carrera de sectores, carrera de capitalización, prima A/H, matriz de rentabilidad, calendario, plan DCA, rentabilidad de cartera, P&L en vivo, velas, Días extremos, Corredores de divisas, Carrera de índices, Clases de activos, Caídas, Tasa de acierto, Renta fija, Valor de mercado, Velas cripto, DCA cripto, Cartera cripto, Calendario de ganancias cripto, Historial de capitalización cripto, Carrera de capitalización cripto, Rendimientos mensuales cripto, Comparar cripto, Movimientos cripto, Dominancia cripto, Rendimientos anuales cripto"),
    "pt-BR": (
        "- Vinte e cinco gráficos: volume financeiro, volume e giro, corrida de setores, corrida de valor de mercado, prêmio A/H, matriz de retorno, calendário, plano DCA, retorno de posição, candles, Dias extremos, Corredores de câmbio, Corrida de índices, Classes de ativos, Quedas, Taxa de acerto, Mercado de títulos, Histórico de valor de mercado, Velas cripto, DCA cripto, Carteira cripto, Calendário de altas e baixas cripto, Histórico de capitalização cripto, Corrida de capitalização cripto, Retornos mensais cripto",
        "- Trinta gráficos: volume financeiro, volume e giro, corrida de setores, corrida de valor de mercado, prêmio A/H, matriz de retorno, calendário, plano DCA, retorno de posição, P&L ao vivo, candles, Dias extremos, Corredores de câmbio, Corrida de índices, Classes de ativos, Quedas, Taxa de acerto, Mercado de títulos, Histórico de valor de mercado, Velas cripto, DCA cripto, Carteira cripto, Calendário de altas e baixas cripto, Histórico de capitalização cripto, Corrida de capitalização cripto, Retornos mensais cripto, Comparar cripto, Movimentos cripto, Dominância cripto, Retornos anuais cripto"),
    "pl": (
        "- Dwadzieścia pięć wykresów: obroty, wolumen, wyścig sektorów, wyścig kapitalizacji, premia A/H, macierz stóp zwrotu, kalendarz, plan DCA, zwrot z pozycji, świece, Ekstremalne dni, Korytarze walutowe, Wyścig indeksów, Klasy aktywów, Obsunięcia, Skuteczność, Rynek obligacji, Wartość rynkowa, Świece krypto, Krypto DCA, Portfel krypto, Kalendarz zmian krypto, Historia kapitalizacji krypto, Wyścig kapitalizacji krypto, Miesięczne stopy zwrotu krypto",
        "- Trzydzieści wykresów: obroty, wolumen, wyścig sektorów, wyścig kapitalizacji, premia A/H, macierz stóp zwrotu, kalendarz, plan DCA, zwrot z pozycji, wynik na żywo, świece, Ekstremalne dni, Korytarze walutowe, Wyścig indeksów, Klasy aktywów, Obsunięcia, Skuteczność, Rynek obligacji, Wartość rynkowa, Świece krypto, Krypto DCA, Portfel krypto, Kalendarz zmian krypto, Historia kapitalizacji krypto, Wyścig kapitalizacji krypto, Miesięczne stopy zwrotu krypto, Porównanie krypto, Ruchy krypto, Dominacja krypto, Roczne stopy krypto"),
    "cs": (
        "- Dvacet pět grafů: obrat, objem, závod sektorů, závod kapitalizací, prémie A/H, matice výnosů, kalendář, DCA plán, výnos pozice, svíčky, Extrémní dny, Měnové koridory, Závod indexů, Třídy aktiv, Poklesy, Úspěšnost, Trh dluhopisů, Tržní hodnota, Krypto svíčky, Krypto DCA, Krypto portfolio, Kalendář pohybů krypto, Historie kapitalizace krypto, Závod kapitalizací krypto, Měsíční výnosy krypto",
        "- Třicet grafů: obrat, objem, závod sektorů, závod kapitalizací, prémie A/H, matice výnosů, kalendář, DCA plán, výnos pozice, výsledek živě, svíčky, Extrémní dny, Měnové koridory, Závod indexů, Třídy aktiv, Poklesy, Úspěšnost, Trh dluhopisů, Tržní hodnota, Krypto svíčky, Krypto DCA, Krypto portfolio, Kalendář pohybů krypto, Historie kapitalizace krypto, Závod kapitalizací krypto, Měsíční výnosy krypto, Srovnání krypto, Krypto pohyby, Krypto dominance, Roční výnosy krypto"),
    "ru": (
        "- Двадцать пять графиков: оборот, объём, гонка секторов, гонка капитализаций, премия A/H, матрица доходности, календарь, план DCA, доходность позиции, свечи, Экстремальные дни, Валютные коридоры, Гонка индексов, Классы активов, Просадки, Доля удачных, Рынок облигаций, История капитализации, Криптосвечи, Крипто-DCA, Криптопортфель, Календарь роста и падения крипто, История капитализации крипто, Гонка капитализаций крипто, Месячная доходность крипто",
        "- Тридцать графиков: оборот, объём, гонка секторов, гонка капитализаций, премия A/H, матрица доходности, календарь, план DCA, доходность позиции, портфель онлайн, свечи, Экстремальные дни, Валютные коридоры, Гонка индексов, Классы активов, Просадки, Доля удачных, Рынок облигаций, История капитализации, Криптосвечи, Крипто-DCA, Криптопортфель, Календарь роста и падения крипто, История капитализации крипто, Гонка капитализаций крипто, Месячная доходность крипто, Сравнение крипто, Движения крипто, Доминирование крипто, Годовые доходности крипто"),
    "tr": (
        "- Yirmi beş grafik: işlem hacmi, hacim ve devir, sektör yarışı, piyasa değeri yarışı, A/H primi, getiri matrisi, takvim, DCA planı, pozisyon getirisi, mumlar, Aşırı günler, Döviz koridorları, Endeks yarışı, Varlık sınıfları, Düşüşler, Tutma oranı, Tahvil piyasası, Piyasa değeri geçmişi, Kripto mumlar, Kripto DCA, Kripto varlıklar, Kripto artış-düşüş takvimi, Kripto piyasa değeri geçmişi, Kripto piyasa değeri yarışı, Kripto aylık getiriler",
        "- Otuz grafik: işlem hacmi, hacim ve devir, sektör yarışı, piyasa değeri yarışı, A/H primi, getiri matrisi, takvim, DCA planı, pozisyon getirisi, canlı portföy, mumlar, Aşırı günler, Döviz koridorları, Endeks yarışı, Varlık sınıfları, Düşüşler, Tutma oranı, Tahvil piyasası, Piyasa değeri geçmişi, Kripto mumlar, Kripto DCA, Kripto varlıklar, Kripto artış-düşüş takvimi, Kripto piyasa değeri geçmişi, Kripto piyasa değeri yarışı, Kripto aylık getiriler, Kripto Karşılaştırma, Kripto Hareketler, Kripto Hakimiyeti, Kripto Yıllık Getiriler"),
}

# 说明里新条目的锚点（resw 导航名：持仓收益 / 加密货币月度收益）。
ANCHORS = {
    "zh-Hans": ("持仓收益", "加密货币月度收益"),
    "zh-Hant": ("持倉收益", "加密貨幣月度收益"),
    "en-US": ("Holdings Return", "Crypto Monthly Returns"),
    "ja": ("保有収益", "暗号資産の月次リターン"),
    "ko": ("보유 수익", "크립토 월간 수익률"),
    "de": ("Depotrendite", "Krypto-Monatsrenditen"),
    "fr": ("Rendement de position", "Rendements mensuels crypto"),
    "it": ("Rendimento di posizione", "Rendimenti mensili crypto"),
    "es": ("Rentabilidad de cartera", "Rendimientos mensuales cripto"),
    "pt-BR": ("Retorno de posição", "Retornos mensais cripto"),
    "pl": ("Zwrot z pozycji", "Miesięczne stopy zwrotu krypto"),
    "cs": ("Výnos pozice", "Měsíční výnosy krypto"),
    "ru": ("Доходность позиции", "Месячная доходность крипто"),
    "tr": ("Pozisyon Getirisi", "Kripto aylık getiriler"),
}

# 说明里新条目的标题（resw 导航名；&amp; 还原成 &）。
TITLES = {
    "zh-Hans": ("实时持仓收益", "加密货币比较", "加密货币涨跌", "加密货币占比", "加密货币年度回报"),
    "zh-Hant": ("即時持倉收益", "加密貨幣比較", "加密貨幣漲跌", "加密貨幣佔比", "加密貨幣年度報酬"),
    "en-US": ("Live portfolio P&L", "Crypto Compare", "Crypto Movers", "Crypto Dominance", "Crypto Annual Returns"),
    "ja": ("リアルタイム保有損益", "暗号資産の比較", "暗号資産の値動き", "暗号資産の占有率", "暗号資産の年間収益"),
    "ko": ("실시간 보유 손익", "암호화폐 비교", "암호화폐 등락", "암호화폐 점유율", "암호화폐 연간 수익"),
    "de": ("Depot live", "Krypto-Vergleich", "Krypto-Bewegungen", "Krypto-Dominanz", "Krypto-Jahresrenditen"),
    "fr": ("P&L en direct", "Comparaison crypto", "Mouvements crypto", "Dominance crypto", "Rendements annuels crypto"),
    "it": ("P&L in tempo reale", "Confronto crypto", "Movimenti crypto", "Dominanza crypto", "Rendimenti annuali crypto"),
    "es": ("P&L en vivo", "Comparar cripto", "Movimientos cripto", "Dominancia cripto", "Rendimientos anuales cripto"),
    "pt-BR": ("P&L ao vivo", "Comparar cripto", "Movimentos cripto", "Dominância cripto", "Retornos anuais cripto"),
    "pl": ("Wynik na żywo", "Porównanie krypto", "Ruchy krypto", "Dominacja krypto", "Roczne stopy krypto"),
    "cs": ("Výsledek živě", "Srovnání krypto", "Krypto pohyby", "Krypto dominance", "Roční výnosy krypto"),
    "ru": ("Портфель онлайн", "Сравнение крипто", "Движения крипто", "Доминирование крипто", "Годовые доходности крипто"),
    "tr": ("Canlı portföy", "Kripto Karşılaştırma", "Kripto Hareketler", "Kripto Hakimiyeti", "Kripto Yıllık Getiriler"),
}


def intro_sentence(lang, key):
    """章节**正文**的首句（跳过图行）。

    listingtext.first_sentence 会把「![…](media/…)」的图行也捞进来——带图章节的
    「第一句」就成了图题而不是正文。商店清单里的页面条目历来写的是正文首句，这里照
    正文取。等 port-help-images.py 把图行挂上之后，这条仍然成立。
    """
    import listingtext as lt

    index = lt.chapter_of(key)
    body = (lt.HELP / f"help-{lang}.md").read_text(encoding="utf-8-sig")
    chunk = re.split(r"(?m)^## ", body)[1:][index]
    lines = chunk.split("\n")[1:]

    picked = []
    for line in lines:
        if not line.strip():
            if picked:
                break
            continue
        if line.strip().startswith("!["):
            continue
        picked.append(line.strip())

    para = (" " if lang not in listingtext.NO_SPACE else "").join(picked)
    para = para.replace("**", "").strip()

    if lang in listingtext.CJK_STOP:
        cut = para.find("。")
        return para[:cut + 1] if cut > 0 else para

    hit = re.search(r"\.\s", para)
    if hit:
        return para[:hit.start() + 1]
    return para


def bullet_for(lang, title, key):
    """「• 标题<分隔>首句」，分隔符照抄该语言锚点条目里现成的那一个。"""
    sentence = intro_sentence(lang, key)
    return title, sentence


def insert_bullet(lines, index_after, title, sentence):
    """在 bullets[index_after] 之后插一条新 •。已在就返回原列表。

    **已存在的判定要防标题前缀**：「加密货币涨跌」是「加密货币涨跌日历」的前缀——
    只比 startswith 会把后者当成前者（2026-10-23 实测，涨跌那条因此漏插）。
    """
    m = re.search(r"——| — |—", lines[index_after])
    sep = m.group(0) if m else "——"
    wanted = "• " + title + sep + sentence

    for line in lines:
        if line == wanted:
            return lines, False

    lines[index_after + 1:index_after + 1] = [wanted]
    return lines, True


def main():
    raw = LISTING.read_bytes()
    had_crlf = b"\r\n" in raw
    text = raw.decode("utf-8")
    text = text.replace("\r\n", "\n")
    changed = 0

    for lang in listingtext.LANGS:
        # 语言段以「## <名称>（<tag>）」开头；直接按 tag 找。
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

        # 1) 「25 页」行
        old, new = INTRO[lang]
        if old in section:
            section = section.replace(old, new, 1)
            notes.append("页数行")
        elif new not in section:
            print(f"  ! {lang}: 页数行既无旧也无新：{old!r}")

        # 2) 七页 → 十一页
        for old, new in PAGES_PHRASES[lang]:
            if old in section:
                section = section.replace(old, new)
                notes.append("十一页")

        # 3) 图表枚举行
        old, new = FEATURE_LINE[lang]
        if old in section:
            section = section.replace(old, new, 1)
            notes.append("枚举行")
        elif new not in section:
            print(f"  ! {lang}: 枚举行既无旧也无新")

        # 4) 新条目（说明里的 • 清单）。锚点走**结构**：14 语言的条目同构同序（项目
        #    铁律），第 7 条是持仓收益（实时持仓收益插它后面），最后一条是加密货币
        #    月度收益（四个加密页依次插它后面）。
        t_intra, t_cmp, t_mov, t_dom, t_ann = TITLES[lang]
        section_lines = section.split("\n")
        bullets = [i for i, l in enumerate(section_lines) if l.startswith("• ")]

        if len(bullets) < 8:
            raise SystemExit(f"  ! {lang}: 条目只有 {len(bullets)} 条，结构对不上")

        section_lines, did1 = insert_bullet(
            section_lines, bullets[6], t_intra, intro_sentence(lang, "NavPortfolioPnl"))
        if did1:
            notes.append("+实时持仓收益")

        for title, key in ((t_cmp, "NavCryptoCompare"), (t_mov, "NavCryptoMovers"),
                           (t_dom, "NavCryptoDominance"), (t_ann, "NavCryptoAnnual")):
            bullets = [i for i, l in enumerate(section_lines) if l.startswith("• ")]
            section_lines, did = insert_bullet(
                section_lines, bullets[-1], title, intro_sentence(lang, key))
            if did:
                notes.append("+" + title)
        section = "\n".join(section_lines)

        if section != original:
            text = text[:start] + section + text[end:]
            changed += 1
            print(f"  + {lang}: {'、'.join(notes)}")
        else:
            print(f"  = {lang}")

    if changed:
        out = text.replace("\n", "\r\n") if had_crlf else text
        LISTING.write_bytes(out.encode("utf-8"))

    print(f"changed {changed} sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
