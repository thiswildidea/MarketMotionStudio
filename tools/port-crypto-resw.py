# -*- coding: utf-8 -*-
r"""把「加密货币」三个新页面用到的 resw 键注入 14 份 Resources.resw。

**为什么不复用股票页那批键。** 表面上 K线 / 持仓 / 定投三页说的是同一件事，但那批键说的是
*交易日*（`trading days`），而一个币**一年里天天都在交易** —— 区间里不会有缺口，也没有
「这个市场休市」的说法。共用那批键会逼着 14 种语言在「到底是交易日还是自然日」上各猜一次，
而猜错的那一份看起来完全正常。所以这一批键自带一套措辞：天数就是天数。

**币种名也进 resw**（`INSTBTC` … `INSTAVAX`），走 `InstrumentNames` 既有的键规则。做法
照 `port-marketcap-pool-resw.py` 那次的结论：**只有中文、日文、韩文、俄文里确实有惯用写法的
才换字，其余语言一律保留拉丁原名** —— 这是有意的降级，不是遗漏：一个德国人看到 "Bitcoin"
认得出，看到「比特币」认不出。BNB、XRP、TRON、Chainlink、Avalanche 在中文里也没有稳定到
能印进视频标题的写法，所以连中文都保留原名。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-crypto-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 导航 -----------------------------------------------------------------------
#
# 三个词各自带 crypto，因为导航里它们的股票孪生页就在上面几行：一个只写「K线」的项
# 排在另一个「K线」下面，读的人要数位置才知道自己点到的是哪一个。

NAV_CANDLE = [
    "Crypto Candles", "Krypto-Kerzen", "Velas cripto", "Chandeliers crypto",
    "Candele crypto", "Świece krypto", "Velas cripto", "Krypto svíčky",
    "Kripto mumlar", "Криптосвечи", "暗号資産のローソク足", "크립토 캔들",
    "加密貨幣 K 線", "加密货币 K 线",
]

NAV_DCA = [
    "Crypto DCA", "Krypto-Sparplan", "DCA cripto", "DCA crypto",
    "DCA crypto", "Krypto DCA", "DCA cripto", "Krypto DCA",
    "Kripto DCA", "Крипто-DCA", "暗号資産のつみたて", "크립토 적립",
    "加密貨幣定投", "加密货币定投",
]

NAV_POSITION = [
    "Crypto Holdings", "Krypto-Bestände", "Cartera cripto", "Portefeuille crypto",
    "Portafoglio crypto", "Portfel krypto", "Carteira cripto", "Krypto portfolio",
    "Kripto varlıklar", "Криптопортфель", "暗号資産の保有", "크립토 보유",
    "加密貨幣持倉", "加密货币持仓",
]

# ---- 页头 -----------------------------------------------------------------------

CANDLE_TITLE = NAV_CANDLE

CANDLE_SUBTITLE = [
    "One coin's daily candles, in US dollars, from a public source. Weekly and monthly are gathered from those same days.",
    "Die Tageskerzen einer Münze, in US-Dollar, aus einer öffentlichen Quelle. Wochen- und Monatskerzen werden aus denselben Tagen gebildet.",
    "Las velas diarias de una moneda, en dólares estadounidenses, de una fuente pública. Las semanales y mensuales se agrupan a partir de esos mismos días.",
    "Les chandeliers quotidiens d'une cryptomonnaie, en dollars américains, depuis une source publique. Les hebdomadaires et mensuels sont regroupés à partir de ces mêmes jours.",
    "Le candele giornaliere di una moneta, in dollari statunitensi, da una fonte pubblica. Settimanali e mensili sono raggruppate a partire dagli stessi giorni.",
    "Dzienne świece jednej monety, w dolarach amerykańskich, z publicznego źródła. Tygodniowe i miesięczne są grupowane z tych samych dni.",
    "As velas diárias de uma moeda, em dólares americanos, de uma fonte pública. As semanais e mensais são agrupadas a partir desses mesmos dias.",
    "Denní svíčky jedné mince v amerických dolarech z veřejného zdroje. Týdenní a měsíční jsou složeny ze stejných dnů.",
    "Bir coin'in günlük mumları, ABD doları cinsinden, herkese açık bir kaynaktan. Haftalık ve aylık mumlar aynı günlerden toplanır.",
    "Дневные свечи одной монеты в долларах США из открытого источника. Недельные и месячные собираются из тех же дней.",
    "公開ソースから取得した、ある暗号資産の日足（米ドル建て）。週足と月足は同じ日足から集計します。",
    "공개 소스에서 가져온 암호화폐의 일봉(미국 달러 기준). 주봉과 월봉은 같은 일봉에서 모읍니다.",
    "某個幣種的日 K 線，以美元計價，取自公開數據源。週線與月線由同一批日線聚合而成。",
    "某个币种的日 K 线，以美元计价，取自公开数据源。周线与月线由同一批日线聚合而成。",
]

DCA_TITLE = [
    "Crypto DCA Plan", "Krypto-Sparplan", "Plan DCA cripto", "Plan DCA crypto",
    "Piano DCA crypto", "Plan DCA krypto", "Plano DCA cripto", "Plán krypto DCA",
    "Kripto DCA planı", "Криптоплан DCA", "暗号資産つみたて計画", "크립토 적립 계획",
    "加密貨幣定投計劃", "加密货币定投计划",
]

DCA_SUBTITLE = [
    "Buying one coin on a fixed rhythm: what the plan has cost, what it holds, and what that is worth today.",
    "Eine Münze in festem Rhythmus kaufen: was der Plan gekostet hat, was er hält und was das heute wert ist.",
    "Comprar una moneda con ritmo fijo: cuánto ha costado el plan, cuánto tiene y cuánto vale hoy.",
    "Acheter une cryptomonnaie à rythme fixe : ce que le plan a coûté, ce qu'il détient, et ce que cela vaut aujourd'hui.",
    "Comprare una moneta a ritmo fisso: quanto è costato il piano, cosa detiene e quanto vale oggi.",
    "Kupowanie jednej monety w stałym rytmie: ile plan kosztował, ile trzyma i ile jest dziś wart.",
    "Comprar uma moeda em ritmo fixo: quanto o plano custou, o que ele tem e quanto isso vale hoje.",
    "Nakupovat jednu minci v pevném rytmu: co plán stál, co drží a za kolik to je dnes.",
    "Bir coin'i sabit bir ritimle almak: planın maliyeti, elinde tuttuğu ve bugünkü değeri.",
    "Покупка одной монеты в заданном ритме: сколько план стоил, что он держит и сколько это стоит сегодня.",
    "ある暗号資産を一定のリズムで買い続ける：計画の費用、保有量、そして今日の価値。",
    "암호화폐를 일정한 리듬으로 매수: 계획의 비용, 보유량, 그리고 오늘의 가치.",
    "按固定節奏買入某個幣種：這份計劃花了多少、現在持有多少、今天值多少。",
    "按固定节奏买入某个币种：这份计划花了多少、现在持有多少、今天值多少。",
]

POSITION_TITLE = [
    "Crypto Holdings Return", "Ertrag der Krypto-Bestände",
    "Rentabilidad de la cartera cripto", "Rendement du portefeuille crypto",
    "Rendimento del portafoglio crypto", "Zwrot portfela krypto",
    "Retorno da carteira cripto", "Výnos krypto portfolia",
    "Kripto varlık getirisi", "Доходность криптопортфеля",
    "暗号資産の保有収益", "크립토 보유 수익",
    "加密貨幣持倉收益", "加密货币持仓收益",
]

POSITION_SUBTITLE = [
    "A sum put into one coin on a day: what it is worth now, and the road it took to get there.",
    "Ein Betrag, an einem Tag in eine Münze gelegt: was er heute wert ist und welchen Weg er genommen hat.",
    "Una suma puesta en una moneda un día: cuánto vale hoy y el camino que recorrió.",
    "Une somme placée dans une cryptomonnaie un jour donné : ce qu'elle vaut aujourd'hui, et le chemin parcouru.",
    "Una somma messa in una moneta in un giorno: quanto vale oggi e la strada che ha fatto.",
    "Kwota włożona w jedną monetę pewnego dnia: ile jest dziś warta i jaką drogę przeszła.",
    "Uma quantia colocada em uma moeda em um dia: quanto vale hoje e o caminho percorrido.",
    "Částka vložená do jedné mince v jednom dni: kolik má dnes hodnotu a jakou cestu urazila.",
    "Bir günde bir coin'e konulan bir tutar: bugünkü değeri ve oraya gelene kadarki yol.",
    "Сумма, вложенная в одну монету в определённый день: сколько она стоит сейчас и какой путь прошла.",
    "ある日に暗号資産に投じた金額：いまの価値と、そこに至るまでの道のり。",
    "어느 날 암호화폐에 넣은 금액: 지금의 가치와 그곳까지의 과정.",
    "某一天把一筆錢投進某個幣種：現在值多少，以及中間走過的路。",
    "某一天把一笔钱投进某个币种：现在值多少，以及中间走过的路。",
]

# ---- 两处说明 -------------------------------------------------------------------
#
# 样式说明只在备源（只有收盘价）时显示：蜡烛与柱状要四个价，备源只有一个，硬画出来是coin
# 从没走出过的形状。免责声明说的是两件股票页没说过的事：价格以美元计（股票页跟着市场走），
# 以及一年里没有缺失的一天。

STYLE_NOTE = [
    "This source carries the daily close only, so candles and bars are drawn as a line.",
    "Diese Quelle hat nur den Tagesschlusskurs, deshalb werden Kerzen und Balken als Linie gezeichnet.",
    "Esta fuente solo tiene el cierre diario, por eso las velas y las barras se dibujan como línea.",
    "Cette source ne porte que la clôture quotidienne : chandeliers et barres sont donc tracés en ligne.",
    "Questa fonte ha solo la chiusura giornaliera, quindi candele e barre sono disegnate come linea.",
    "To źródło ma tylko kurs zamknięcia, dlatego świece i słupki są rysowane jako linia.",
    "Esta fonte traz apenas o fechamento diário, por isso velas e barras são desenhadas como linha.",
    "Tento zdroj má jen denní závěr, proto se svíčky a sloupce kreslí jako čára.",
    "Bu kaynakta yalnızca günlük kapanış var, bu yüzden mumlar ve çubuklar çizgi olarak çizilir.",
    "У этого источника есть только дневное закрытие, поэтому свечи и бары рисуются линией.",
    "この情報源は日次の終値のみを持つため、ローソク足とバーは線で描かれます。",
    "이 소스는 일일 종가만 제공하므로 캔들과 바는 선으로 그립니다.",
    "這個來源只有每日收盤價，因此蠟燭圖與柱狀圖改以折線繪製。",
    "这个来源只有每日收盘价，因此蜡烛图与柱状图改以折线绘制。",
]

DISCLAIMER = [
    "Daily prices in US dollars from a public source; a coin trades every day of the year, so no day is missing. For reference only, not investment advice.",
    "Tageskurse in US-Dollar aus einer öffentlichen Quelle; eine Münze wird an jedem Tag des Jahres gehandelt, es fehlt also kein Tag. Nur zur Information, keine Anlageberatung.",
    "Precios diarios en dólares estadounidenses de una fuente pública; una moneda cotiza todos los días del año, así que no falta ninguno. Solo informativo, no es asesoramiento de inversión.",
    "Cours quotidiens en dollars américains depuis une source publique ; une cryptomonnaie se négocie tous les jours de l'année, aucun jour ne manque donc. À titre d'information, pas un conseil en investissement.",
    "Prezzi giornalieri in dollari statunitensi da una fonte pubblica; una moneta viene scambiata ogni giorno dell'anno, quindi non manca nessun giorno. Solo a scopo informativo, non consulenza d'investimento.",
    "Kursy dzienne w dolarach amerykańskich z publicznego źródła; moneta jest notowana każdego dnia roku, więc żaden dzień nie brakuje. Wyłącznie informacyjnie, nie porada inwestycyjna.",
    "Preços diários em dólares americanos de uma fonte pública; uma moeda é negociada todos os dias do ano, então nenhum dia fica faltando. Apenas informativo, não é recomendação de investimento.",
    "Denní ceny v amerických dolarech z veřejného zdroje; mince se obchoduje každý den v roce, takže žádný den nechybí. Pouze informativně, ne investiční poradenství.",
    "Herkese açık bir kaynaktan ABD doları cinsinden günlük fiyatlar; bir coin yılın her günü işlem görür, bu yüzden hiçbir gün eksik değildir. Yalnızca bilgi amaçlıdır, yatırım tavsiyesi değildir.",
    "Дневные цены в долларах США из открытого источника; монета торгуется каждый день в году, поэтому ни один день не пропущен. Только для справки, не инвестиционная рекомендация.",
    "公開ソースから取得した米ドル建ての日次価格。暗号資産は年中無休で取引されるため、欠けている日はありません。参考情報であり、投資助言ではありません。",
    "공개 소스의 미국 달러 기준 일일 가격. 암호화폐는 연중 매일 거래되므로 빠진 날이 없습니다. 참고용이며 투자 권유가 아닙니다.",
    "每日價格以美元計價，取自公開數據源；加密貨幣全年無休交易，因此不會缺任何一天。僅供參考，不構成投資建議。",
    "每日价格以美元计价，取自公开数据源；加密货币全年无休交易，因此不会缺任何一天。仅供参考，不构成投资建议。",
]

# ---- 画面默认标题 ---------------------------------------------------------------
#
# 标题会印进导出的视频，所以三页各自带 crypto 这个词：一段只有「比特币 · 定投计划」的视频
# 看不出它的价格来自哪一个市场。

CANDLE_DEFAULT = ["{0} · {1}"] * 14

DCA_DEFAULT = [
    "Crypto DCA: {0}", "Krypto-Sparplan: {0}", "DCA cripto: {0}", "DCA crypto : {0}",
    "DCA crypto: {0}", "Krypto DCA: {0}", "DCA cripto: {0}", "Krypto DCA: {0}",
    "Kripto DCA: {0}", "Крипто-DCA: {0}", "暗号資産つみたて: {0}", "크립토 적립: {0}",
    "加密貨幣定投：{0}", "加密货币定投：{0}",
]

POSITION_DEFAULT = [
    "Crypto holdings: {0}", "Krypto-Bestand: {0}", "Cartera cripto: {0}",
    "Portefeuille crypto : {0}", "Portafoglio crypto: {0}", "Portfel krypto: {0}",
    "Carteira cripto: {0}", "Krypto portfolio: {0}", "Kripto varlık: {0}",
    "Криптопортфель: {0}", "暗号資産の保有: {0}", "크립토 보유: {0}",
    "加密貨幣持倉：{0}", "加密货币持仓：{0}",
]

# ---- 状态行 ---------------------------------------------------------------------
#
# 每一句里的「天」都是自然日，不是交易日 —— 这就是这一批键存在的理由。

CANDLE_FETCHED = [
    "{0} {1} candles ({2} to {3})", "{0} {1}-Kerzen ({2} bis {3})",
    "{0} velas {1} ({2} a {3})", "{0} chandeliers {1} ({2} au {3})",
    "{0} candele {1} ({2} al {3})", "{0} świec {1} ({2} do {3})",
    "{0} velas {1} ({2} a {3})", "{0} svíček {1} ({2} až {3})",
    "{0} adet {1} mum ({2} - {3})", "{0} свечей {1} ({2} — {3})",
    "{1}ローソク足 {0} 本（{2}〜{3}）", "{1} 캔들 {0}개({2}~{3})",
    "{1} K 線 {0} 根（{2} 至 {3}）", "{1} K 线 {0} 根（{2} 至 {3}）",
]

CANDLE_BOARD = [
    "{0} coins over {1} days ({2} to {3})", "{0} Münzen über {1} Tage ({2} bis {3})",
    "{0} monedas en {1} días ({2} a {3})", "{0} cryptomonnaies sur {1} jours ({2} au {3})",
    "{0} monete su {1} giorni ({2} al {3})", "{0} monet przez {1} dni ({2} do {3})",
    "{0} moedas em {1} dias ({2} a {3})", "{0} mincí za {1} dní ({2} až {3})",
    "{1} günde {0} coin ({2} - {3})", "Монет: {0} за {1} дней ({2} — {3})",
    "{0} 銘柄・{1} 日間（{2}〜{3}）", "{0}개 코인 · {1}일({2}~{3})",
    "{0} 個幣種 · {1} 天（{2} 至 {3}）", "{0} 个币种 · {1} 天（{2} 至 {3}）",
]

DCA_FETCHED = [
    "{0} days ({1} to {2}), {3} buys", "{0} Tage ({1} bis {2}), {3} Käufe",
    "{0} días ({1} a {2}), {3} compras", "{0} jours ({1} au {2}), {3} achats",
    "{0} giorni ({1} al {2}), {3} acquisti", "{0} dni ({1} do {2}), {3} zakupów",
    "{0} dias ({1} a {2}), {3} compras", "{0} dní ({1} až {2}), {3} nákupů",
    "{0} gün ({1} - {2}), {3} alım", "{0} дней ({1} — {2}), покупок: {3}",
    "{0}日間（{1}〜{2}）、買付 {3} 回", "{0}일({1}~{2}), 매수 {3}회",
    "{0} 天（{1} 至 {2}），買入 {3} 次", "{0} 天（{1} 至 {2}），买入 {3} 次",
]

DCA_BOARD = [
    "{0} plans · {1} days ({2} to {3})", "{0} Pläne · {1} Tage ({2} bis {3})",
    "{0} planes · {1} días ({2} a {3})", "{0} plans · {1} jours ({2} au {3})",
    "{0} piani · {1} giorni ({2} al {3})", "{0} planów · {1} dni ({2} do {3})",
    "{0} planos · {1} dias ({2} a {3})", "{0} plánů · {1} dní ({2} až {3})",
    "{0} plan · {1} gün ({2} - {3})", "Планов: {0} · дней {1} ({2} — {3})",
    "{0} 件のプラン · {1} 日間（{2}〜{3}）", "플랜 {0}개 · {1}일({2}~{3})",
    "{0} 份計劃 · {1} 天（{2} 至 {3}）", "{0} 份计划 · {1} 天（{2} 至 {3}）",
]

POSITION_FETCHED = [
    "{0} days ({1} to {2})", "{0} Tage ({1} bis {2})", "{0} días ({1} a {2})",
    "{0} jours ({1} au {2})", "{0} giorni ({1} al {2})", "{0} dni ({1} do {2})",
    "{0} dias ({1} a {2})", "{0} dní ({1} až {2})", "{0} gün ({1} - {2})",
    "{0} дней ({1} — {2})", "{0}日間（{1}〜{2}）", "{0}일({1}~{2})",
    "{0} 天（{1} 至 {2}）", "{0} 天（{1} 至 {2}）",
]

POSITION_BOARD = [
    "{0} holdings over {1} days ({2} to {3})", "{0} Bestände über {1} Tage ({2} bis {3})",
    "{0} carteras en {1} días ({2} a {3})", "{0} portefeuilles sur {1} jours ({2} au {3})",
    "{0} portafogli su {1} giorni ({2} al {3})", "{0} portfeli przez {1} dni ({2} do {3})",
    "{0} carteiras em {1} dias ({2} a {3})", "{0} portfolií za {1} dní ({2} až {3})",
    "{1} günde {0} varlık ({2} - {3})", "Портфелей: {0} за {1} дней ({2} — {3})",
    "{0} 件の保有 · {1} 日間（{2}〜{3}）", "{0}개 보유 · {1}일({2}~{3})",
    "{0} 筆持倉 · {1} 天（{2} 至 {3}）", "{0} 笔持仓 · {1} 天（{2} 至 {3}）",
]

# 备源只带一年（见 `CryptoQuotes.GeckoMostDays`），要十年会被答以一年。区间悄悄从更晚的
# 那天开始，是一个区间最不该给出的答案，所以要说出来。
RANGE_SHORT = [
    "This source only reaches back to {0}, so the span starts there",
    "Diese Quelle reicht nur bis {0} zurück, die Spanne beginnt also dort",
    "Esta fuente solo llega hasta {0}, así que el rango empieza ahí",
    "Cette source ne remonte qu'à {0} : l'intervalle commence donc là",
    "Questa fonte arriva solo fino al {0}, quindi l'intervallo inizia lì",
    "To źródło sięga tylko do {0}, więc zakres zaczyna się tam",
    "Esta fonte só vai até {0}, então o intervalo começa aí",
    "Tento zdroj sahá jen do {0}, proto období začíná tam",
    "Bu kaynak yalnızca {0} tarihine kadar uzanıyor, bu yüzden aralık oradan başlıyor",
    "Этот источник хранит данные только с {0}, поэтому диапазон начинается оттуда",
    "この情報源は {0} までしか遡れないため、期間はそこから始まります",
    "이 소스는 {0}까지만 제공하므로 구간은 거기서 시작합니다",
    "這個來源只能追溯到 {0}，因此區間從那天開始",
    "这个来源只能追溯到 {0}，因此区间从那天开始",
]

PICK_ONE = [
    "Switch on at least one coin", "Schalten Sie mindestens eine Münze ein",
    "Activa al menos una moneda", "Activez au moins une cryptomonnaie",
    "Attiva almeno una moneta", "Włącz co najmniej jedną monetę",
    "Ative pelo menos uma moeda", "Zapněte alespoň jednu minci",
    "En az bir coin açın", "Включите хотя бы одну монету",
    "少なくとも 1 つの暗号資産を選んでください", "암호화폐를 하나 이상 켜세요",
    "請至少勾選一個幣種", "请至少勾选一个币种",
]

# 选择器下面那一行：勾了几个、上限几个。上限写在这里而不是等按第七个时才说，
# 因为「按了没反应」和「这里写着最多六个」是两种完全不同的体验。
PICKS_NOTE = [
    "{0} of at most {1} coins switched on", "{0} von höchstens {1} Münzen eingeschaltet",
    "{0} de {1} monedas como máximo activadas", "{0} cryptomonnaies activées sur {1} au maximum",
    "{0} monete attive su {1} al massimo", "{0} z co najwyżej {1} monet włączonych",
    "{0} de no máximo {1} moedas ativadas", "{0} z nejvýše {1} mincí zapnuto",
    "En çok {1} coinden {0} tanesi açık", "Включено {0} из {1} возможных монет",
    "最大 {1} 銘柄中 {0} 銘柄を選択中", "최대 {1}개 중 {0}개 선택됨",
    "已選 {0} 個，最多 {1} 個", "已选 {0} 个，最多 {1} 个",
]

# ---- 币种名 ---------------------------------------------------------------------
#
# 键名由 `InstrumentNames.Key` 机械算出来（"BTC" -> `INSTBTC`），这里按同一个规则写死。
# 只有确实有惯用写法的语言换字，其余保留拉丁原名，理由见文件头。

LATIN = 9  # en-US … tr：一律用原名

COINS = [
    ("BTC", "Bitcoin", dict(ru="Биткоин", ja="ビットコイン", ko="비트코인",
                            zh_Hant="比特幣", zh_Hans="比特币")),
    ("ETH", "Ethereum", dict(ru="Эфириум", ja="イーサリアム", ko="이더리움",
                             zh_Hant="以太坊", zh_Hans="以太坊")),
    ("BNB", "BNB", {}),
    ("SOL", "Solana", dict(ru="Солана", ja="ソラナ", ko="솔라나",
                           zh_Hant="索拉納", zh_Hans="索拉纳")),
    ("XRP", "XRP", {}),
    ("DOGE", "Dogecoin", dict(ru="Догикоин", ja="ドージコイン", ko="도지코인",
                              zh_Hant="狗狗幣", zh_Hans="狗狗币")),
    ("ADA", "Cardano", dict(ru="Кардано", ja="カルダノ", ko="카르다노",
                            zh_Hant="艾達幣", zh_Hans="艾达币")),
    ("TRX", "TRON", {}),
    ("LTC", "Litecoin", dict(ru="Лайткоин", ja="ライトコイン", ko="라이트코인",
                             zh_Hant="萊特幣", zh_Hans="莱特币")),
    ("LINK", "Chainlink", {}),
    ("DOT", "Polkadot", dict(ja="ポルカドット", ko="폴카닷",
                             zh_Hant="波卡", zh_Hans="波卡")),
    ("AVAX", "Avalanche", dict(ja="アバランチ", ko="아발란체")),
]

# 键名里 zh-Hant / zh-Hans 对应列序的最后两列；ru / ja / ko 是第 10~12 列。
COLUMN_OF = {"ru": 9, "ja": 10, "ko": 11, "zh_Hant": 12, "zh_Hans": 13}


def coin_row(code, latin, local):
    values = [latin] * LATIN + ["", "", "", "", ""]

    for name, text in local.items():
        values[COLUMN_OF[name]] = text or latin

    # 没有对应写法的语言落回原名，而不是留空 —— 空名字进画面就是一个空白标题。
    return [value or latin for value in values]


ROWS = [
    ("NavCryptoCandle.Content", NAV_CANDLE),
    ("NavCryptoDca.Content", NAV_DCA),
    ("NavCryptoPosition.Content", NAV_POSITION),
    ("CryptoCandlePageTitle.Text", CANDLE_TITLE),
    ("CryptoCandlePageSubtitle.Text", CANDLE_SUBTITLE),
    ("CryptoDcaPageTitle.Text", DCA_TITLE),
    ("CryptoDcaPageSubtitle.Text", DCA_SUBTITLE),
    ("CryptoPositionPageTitle.Text", POSITION_TITLE),
    ("CryptoPositionPageSubtitle.Text", POSITION_SUBTITLE),
    ("CryptoCandleStyleNote.Text", STYLE_NOTE),
    ("CryptoDisclaimer.Text", DISCLAIMER),
    ("CryptoCandleDefaultTitle", CANDLE_DEFAULT),
    ("CryptoDcaDefaultTitle", DCA_DEFAULT),
    ("CryptoPositionDefaultTitle", POSITION_DEFAULT),
    ("CryptoCandleFetched", CANDLE_FETCHED),
    ("CryptoCandleBoardFetched", CANDLE_BOARD),
    ("CryptoDcaFetched", DCA_FETCHED),
    ("CryptoDcaBoardFetched", DCA_BOARD),
    ("CryptoPositionFetched", POSITION_FETCHED),
    ("CryptoPositionBoardFetched", POSITION_BOARD),
    ("CryptoRangeShort", RANGE_SHORT),
    ("CryptoPickOne", PICK_ONE),
    ("CryptoPicksNote", PICKS_NOTE),
] + [(f"INST{code}", coin_row(code, latin, local)) for code, latin, local in COINS]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project
    file rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
