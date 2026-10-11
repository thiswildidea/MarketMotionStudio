# -*- coding: utf-8 -*-
r"""把「涨跌日历 / 市值历程 / 市值榜」三页用到的 resw 键注入 14 份 Resources.resw。

**为什么又是新的一族键，而不是接着 `port-crypto-resw.py` 那批写。** 那批键说的是 *同一个币的
价格*，这一批说的是 *市值* 与 *逐日涨跌*，两件事各有一套名词（流通市值 / 估算口径 / 稳定币），
共用会让 14 种语言在「cap 指什么」上各猜一次。

**三件新事要说清，14 份都要说：**

1. **市值指流通市值，不是「当前流通量 × 历史价格」的外推。** 外推会让市值线与价格线恒平行，
   这一页就失去意义；所以数据来自 CoinMetrics 的逐日市值，btc 可回溯到 2010 年。
2. **市值榜是动态的**：取数那一刻按 CoinGecko 的实时市值取前 15 名作候选池，**不写死清单**。
   榜上有稳定币 —— 用户拍板保留，忠实反映排名（它们价格恒为一美元，那条线是平的）。
3. **天数一律是自然日**，与股票页的「交易日」不是一回事。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-crypto-caps-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 导航 -----------------------------------------------------------------------
#
# 三个词各自带 crypto：导航里它们的股票孪生页就在上面几行，一个只写「涨跌日历」的项排在
# 另一个「涨跌日历」下面，读的人要数位置才知道点到的是哪一个。

NAV_CALENDAR = [
    "Crypto Gain Calendar", "Krypto-Gewinnkalender", "Calendario de ganancias cripto",
    "Calendrier des hausses et baisses crypto", "Calendario dei movimenti crypto",
    "Kalendarz zmian krypto", "Calendário de altas e baixas cripto",
    "Kalendář pohybů krypto", "Kripto artış-düşüş takvimi",
    "Календарь роста и падения крипто", "暗号資産の値動きカレンダー",
    "크립토 등락 캘린더", "加密貨幣漲跌日曆", "加密货币涨跌日历",
]

NAV_CAP_HISTORY = [
    "Crypto Market Cap History", "Krypto-Marktkapitalisierung im Verlauf",
    "Historial de capitalización cripto", "Historique de capitalisation crypto",
    "Storia della capitalizzazione crypto", "Historia kapitalizacji krypto",
    "Histórico de capitalização cripto", "Historie kapitalizace krypto",
    "Kripto piyasa değeri geçmişi", "История капитализации крипто",
    "暗号資産の時価総額の推移", "크립토 시가총액 추이",
    "加密貨幣市值歷程", "加密货币市值历程",
]

NAV_MARKET_CAP = [
    "Crypto Market Cap Race", "Rennen der Krypto-Marktkapitalisierung",
    "Carrera de capitalización cripto", "Course des capitalisations crypto",
    "Corsa della capitalizzazione crypto", "Wyścig kapitalizacji krypto",
    "Corrida de capitalização cripto", "Závod kapitalizací krypto",
    "Kripto piyasa değeri yarışı", "Гонка капитализаций крипто",
    "暗号資産の時価総額レース", "크립토 시가총액 레이스",
    "加密貨幣市值榜", "加密货币市值榜",
]

CALENDAR_TITLE = NAV_CALENDAR
CAP_HISTORY_TITLE = NAV_CAP_HISTORY
MARKET_CAP_TITLE = NAV_MARKET_CAP

# ---- 页头 -----------------------------------------------------------------------

# 日历页那句副标题要挡住一个必然的误读：一格一天的全年网格上没有空格，读者会以为是漏掉了
# 休息日。股票页那张日历是有空格的（休市），这一页没有 —— 说明它，不然「空白」会被读成缺陷。
CALENDAR_SUBTITLE = [
    "One coin's daily move, one square per day. A coin trades every day of the year, so the calendar has no gaps — that is not a missing holiday, it is a market that never rests.",
    "Die tägliche Bewegung einer Münze, ein Feld pro Tag. Eine Münze wird an jedem Tag des Jahres gehandelt, der Kalender hat also keine Lücken — das ist kein fehlender Feiertag, sondern ein Markt, der nie ruht.",
    "El movimiento diario de una moneda, un cuadro por día. Una moneda cotiza todos los días del año, así que el calendario no tiene huecos — no es un festivo omitido, es un mercado que nunca descansa.",
    "Le mouvement quotidien d'une cryptomonnaie, une case par jour. Une cryptomonnaie se négocie tous les jours de l'année : le calendrier n'a donc pas de trou — ce n'est pas un jour férié manquant, c'est un marché qui ne s'arrête jamais.",
    "Il movimento giornaliero di una moneta, un quadrato per giorno. Una moneta viene scambiata ogni giorno dell'anno, quindi il calendario non ha spazi vuoti — non è una festività mancante, è un mercato che non riposa mai.",
    "Dzienne zmiany jednej monety, jedno pole na dzień. Moneta jest notowana każdego dnia roku, więc kalendarz nie ma luk — to nie brakujące święto, to rynek, który nigdy nie odpoczywa.",
    "O movimento diário de uma moeda, um quadrado por dia. Uma moeda é negociada todos os dias do ano, então o calendário não tem lacunas — não é um feriado faltando, é um mercado que nunca descansa.",
    "Denní pohyb jedné mince, jeden čtvereček za den. Mince se obchoduje každý den v roce, takže kalendář nemá mezery — to není chybějící svátek, je to trh, který nikdy neodpočívá.",
    "Bir coin'in günlük hareketi, güne bir kare. Bir coin yılın her günü işlem görür, bu yüzden takvimde boşluk yok — bu eksik bir tatil değil, hiç dinlenmeyen bir piyasa.",
    "Дневное движение одной монеты, одна клетка на день. Монета торгуется каждый день в году, поэтому в календаре нет пропусков — это не потерянный праздник, это рынок, который не отдыхает.",
    "ある暗号資産の日々の値動きを、1 日 1 マスで。暗号資産は年中無休で取引されるため、カレンダーに空白はありません。休日が抜けているのではなく、この市場は休まないのです。",
    "암호화폐의 일간 변동을 하루에 한 칸씩. 암호화폐는 연중 매일 거래되므로 캘린더에 빈칸이 없습니다. 빠진 휴일이 아니라, 쉬지 않는 시장입니다.",
    "某個幣種每日的漲跌，一格一天。加密貨幣全年無休交易，因此日曆上沒有空格——那不是漏掉了休息日，而是這個市場不休息。",
    "某个币种每一天的涨跌，一格一天。加密货币全年无休交易，因此日历上没有空格——这不是漏掉了休息日，而是这个市场不休息。",
]

# 市值历程那句副标题说两件事：上一条线是流通市值、下一条是价格，以及「两条线分头走」正是
# 这一页要看的东西（增发与销毁），不是画错了。
CAP_HISTORY_SUBTITLE = [
    "One coin's circulating market cap over time, from the public CoinMetrics API, with the price over the same days beneath it. Where the two lines pull apart, you are looking at issuance and burns.",
    "Die zirkulierende Marktkapitalisierung einer Münze im Verlauf, aus der öffentlichen CoinMetrics-Schnittstelle, darunter der Kurs über dieselben Tage. Wo die beiden Linien auseinanderlaufen, sieht man Ausgabe und Verbrennung von Münzen.",
    "La capitalización circulante de una moneda a lo largo del tiempo, desde la API pública de CoinMetrics, con el precio de los mismos días debajo. Donde las dos líneas se separan, lo que se ve es emisión y quema.",
    "La capitalisation circulante d'une cryptomonnaie au fil du temps, depuis l'API publique CoinMetrics, avec le cours des mêmes jours en dessous. Là où les deux lignes s'écartent, on voit l'émission et la destruction de jetons.",
    "La capitalizzazione circolante di una moneta nel tempo, dall'API pubblica CoinMetrics, con il prezzo degli stessi giorni sotto. Dove le due linee si separano, si vedono emissione e distruzione di token.",
    "Krążąca kapitalizacja jednej monety w czasie, z publicznego API CoinMetrics, a pod nią kurs w tych samych dniach. Tam, gdzie obie linie się rozchodzą, widać emisję i spalanie tokenów.",
    "A capitalização circulante de uma moeda ao longo do tempo, pela API pública da CoinMetrics, com o preço dos mesmos dias abaixo. Onde as duas linhas se separam, está a emissão e a queima de tokens.",
    "Cirkulující kapitalizace jedné mince v čase z veřejného API CoinMetrics, pod ní cena za stejné dny. Tam, kde se obě čáry rozcházejí, vidíte emisi a pálení tokenů.",
    "Bir coin'in dolaşımdaki piyasa değerinin zaman içindeki seyri, herkese açık CoinMetrics API'sinden; altında aynı günlerin fiyatı. İki çizginin ayrıldığı yerde görülen şey arz artışı ve yakımdır.",
    "Капитализация монеты в обращении во времени из публичного API CoinMetrics, под ней — цена за те же дни. Там, где две линии расходятся, видны эмиссия и сжигание.",
    "公開 API の CoinMetrics から取得した、ある暗号資産の流通時価総額の推移。その下に同じ期間の価格。2 本の線が離れるところが、新規発行とバーンです。",
    "공개 API CoinMetrics에서 가져온 암호화폐의 유통 시가총액 추이. 아래에는 같은 기간의 가격. 두 선이 갈라지는 곳이 발행과 소각입니다.",
    "某個幣種流通市值的歷史，取自 CoinMetrics 公開介面；下方是同期價格。兩條線分頭走的地方，看的就是增發與銷毀。",
    "某个币种流通市值的历史，取自 CoinMetrics 公开接口；下方是同期价格。两条线分头走的地方，看的就是增发与销毁。",
]

# 「市值」这个词在加密语境里有两个答案（流通 / 完全稀释），而画面上只有一条线 —— 页面下方
# 那句说明必须把它钉在流通上，并说清最早能到哪一年。
CAP_HISTORY_NOTE = [
    "Market cap here means circulating cap — the coins already issued and in circulation, not a fully diluted count that assumes every future coin. Figures come from the public CoinMetrics API: Bitcoin reaches back to 2010, other coins go back as far as the source holds them.",
    "Marktkapitalisierung bedeutet hier die zirkulierende Kapitalisierung — die bereits ausgegebenen und im Umlauf befindlichen Münzen, nicht eine voll verwässerte Zahl, die jede künftige Münze annimmt. Die Werte stammen aus der öffentlichen CoinMetrics-Schnittstelle: Bitcoin reicht bis 2010 zurück, andere Münzen so weit, wie die Quelle sie hält.",
    "Aquí capitalización significa la circulante — las monedas ya emitidas y en circulación, no un cálculo totalmente diluido que supone todas las futuras. Los datos vienen de la API pública de CoinMetrics: Bitcoin llega hasta 2010, las demás monedas hasta donde la fuente las tenga.",
    "Ici, capitalisation signifie capitalisation circulante — les jetons déjà émis et en circulation, et non une valorisation entièrement diluée qui suppose tous les jetons futurs. Les chiffres viennent de l'API publique CoinMetrics : Bitcoin remonte à 2010, les autres cryptomonnaies remontent aussi loin que la source les garde.",
    "Qui capitalizzazione significa circolante — le monete già emesse e in circolazione, non un conteggio completamente diluito che presuppone ogni moneta futura. I dati vengono dall'API pubblica CoinMetrics: Bitcoin arriva al 2010, le altre monete fino a dove la fonte le conserva.",
    "Kapitalizacja oznacza tu kapitalizację krążącą — monety już wyemitowane i będące w obiegu, nie rozwodnioną wartość zakładającą wszystkie przyszłe monety. Dane pochodzą z publicznego API CoinMetrics: Bitcoin sięga 2010 roku, pozostałe monety tak daleko, jak źródło je przechowuje.",
    "Aqui capitalização significa a circulante — as moedas já emitidas e em circulação, não uma contagem totalmente diluída que pressupõe todas as futuras. Os dados vêm da API pública da CoinMetrics: o Bitcoin chega a 2010, as demais moedas vão até onde a fonte as mantém.",
    "Kapitalizace zde znamená obíhající kapitalizaci — mince již vydané a v oběhu, nikoli plně zředěný počet, který počítá každou budoucí minci. Údaje pocházejí z veřejného API CoinMetrics: Bitcoin sahá do roku 2010, ostatní mince tak daleko, jak je zdroj drží.",
    "Burada piyasa değeri dolaşımdaki değer demektir — halihazırda çıkarılmış ve dolaşımda olan coin'ler, gelecekteki tüm coin'leri varsayan tam seyreltilmiş bir sayım değil. Veriler herkese açık CoinMetrics API'sinden gelir: Bitcoin 2010'a kadar uzanır, diğer coin'ler kaynağın tuttuğu kadar geriye gider.",
    "Здесь капитализация означает капитализацию в обращении — уже выпущенные монеты, а не полностью размытый подсчёт, учитывающий все будущие монеты. Данные из публичного API CoinMetrics: биткоин доступен с 2010 года, остальные монеты — насколько далеко источник их хранит.",
    "ここでの時価総額は流通時価総額、つまりすでに発行され流通している分です。将来の発行分まで含めた完全希薄化後の数値ではありません。データは公開 API の CoinMetrics から取得：ビットコインは 2010 年まで遡れ、その他の銘柄はソースが保持する範囲までです。",
    "여기서 시가총액은 유통 시가총액, 즉 이미 발행되어 유통되는 물량입니다. 미래 발행분까지 포함한 완전 희석 기준이 아닙니다. 데이터는 공개 API CoinMetrics에서 가져옵니다: 비트코인은 2010년까지, 나머지 코인은 소스가 보유한 범위까지 거슬러 올라갑니다.",
    "市值指「流通市值」——已經產出並在流通的幣，不是把未來所有幣都算進去的總市值。數據來自 CoinMetrics 公開介面：比特幣可回溯到 2010 年，其餘幣按源端持有多少算多少。",
    "市值指「流通市值」——已经产出并在流通的币，不是把未来所有币都算进去的总市值。数据来自 CoinMetrics 公开接口：比特币可回溯到 2010 年，其余币按源端持有多少算多少。",
]

# ---- 选择器 ---------------------------------------------------------------------
#
# 两页各有一个币种下拉，各自一个键而不共用：它们的 AutomationId 不同（`CryptoCalendarCoin`
# / `CryptoCapCoin`），而键名跟着控件走，改一处时不会顺手改掉另一页。

COIN_HEADER = [
    "Coin", "Münze", "Moneda", "Cryptomonnaie", "Moneta", "Moneta", "Moeda",
    "Mince", "Coin", "Монета", "銘柄", "코인", "幣種", "币种",
]

# ---- 画面上的词 -----------------------------------------------------------------
#
# 渲染器不自带「描述数据」的字，全由页面传进来。这三个词直接印进导出的视频。

CAP_WORD = [
    "Circulating cap", "Zirkulierende Kapitalisierung", "Capitalización circulante",
    "Capitalisation circulante", "Capitalizzazione circolante", "Kapitalizacja krążąca",
    "Capitalização circulante", "Obíhající kapitalizace", "Dolaşımdaki piyasa değeri",
    "Капитализация в обращении", "流通時価総額", "유통 시가총액", "流通市值", "流通市值",
]

PRICE_WORD = [
    "Price", "Kurs", "Precio", "Cours", "Prezzo", "Kurs", "Preço", "Cena",
    "Fiyat", "Цена", "価格", "가격", "價格", "价格",
]

# 拼在天数后面（`{天数} {SpanWord}`），所以开头不带数字也不带空格。
DAYS_UNIT = [
    "days", "Tage", "días", "jours", "giorni", "dni", "dias", "dní", "gün",
    "дней", "日間", "일", "個自然日", "个自然日",
]

UNIT_COINS = [
    "coins", "Münzen", "monedas", "cryptomonnaies", "monete", "monet", "moedas",
    "mincí", "coin", "монет", "銘柄", "코인", "個幣種", "个币种",
]

CAP_DEFAULT_TITLE = [
    "{0} market cap history", "{0} Marktkapitalisierung im Verlauf",
    "Capitalización de {0} en el tiempo", "Capitalisation de {0} dans le temps",
    "Capitalizzazione di {0} nel tempo", "Kapitalizacja {0} w czasie",
    "Capitalização de {0} ao longo do tempo", "Kapitalizace {0} v čase",
    "{0} piyasa değeri geçmişi", "Капитализация {0} во времени",
    "{0}の時価総額の推移", "{0} 시가총액 추이", "{0}市值歷程", "{0}市值历程",
]

# ---- 状态行 ---------------------------------------------------------------------
#
# 每一句里的「天」都是自然日。市值历程那句末尾的单位是亿美元（`CryptoCapLoader.PerYi`），
# 与股票页 `CapHistoryCapUnit` 的「100M USD」是同一个量级 —— 各语言按自己习惯写倍数。

CALENDAR_FETCHED = [
    "{0} days ({1} to {2}) · {3} up · {4} down",
    "{0} Tage ({1} bis {2}) · {3} im Plus · {4} im Minus",
    "{0} días ({1} a {2}) · {3} al alza · {4} a la baja",
    "{0} jours ({1} au {2}) · {3} en hausse · {4} en baisse",
    "{0} giorni ({1} al {2}) · {3} in rialzo · {4} in ribasso",
    "{0} dni ({1} do {2}) · {3} na plusie · {4} na minusie",
    "{0} dias ({1} a {2}) · {3} em alta · {4} em baixa",
    "{0} dní ({1} až {2}) · {3} rostlo · {4} klesalo",
    "{0} gün ({1} - {2}) · {3} yükseliş · {4} düşüş",
    "{0} дней ({1} — {2}) · рост {3} · падение {4}",
    "{0} 日間（{1}〜{2}）・上昇 {3} 日・下落 {4} 日",
    "{0}일({1}~{2}) · 상승 {3}일 · 하락 {4}일",
    "{0} 個自然日（{1} ~ {2}）· 上漲 {3} 天 · 下跌 {4} 天",
    "{0} 个自然日（{1} ~ {2}）· 上涨 {3} 天 · 下跌 {4} 天",
]

CAP_FETCHED = [
    "Got {0} days, {1} to {2}. Cap at the end: {3} × 100M US dollars.",
    "{0} Tage geholt, {1} bis {2}. Kapitalisierung am Ende: {3} × 100 Mio. US-Dollar.",
    "Se obtuvieron {0} días, {1} a {2}. Capitalización al final: {3} × 100 M USD.",
    "{0} jours récupérés, {1} au {2}. Capitalisation à la fin : {3} × 100 M de dollars US.",
    "Ottenuti {0} giorni, {1} al {2}. Capitalizzazione alla fine: {3} × 100 M di dollari USA.",
    "Pobrano {0} dni, {1} do {2}. Kapitalizacja na koniec: {3} × 100 mln USD.",
    "Obtidos {0} dias, {1} a {2}. Capitalização no fim: {3} × 100 M de dólares americanos.",
    "Získáno {0} dní, {1} až {2}. Kapitalizace na konci: {3} × 100 mil. USD.",
    "{0} gün alındı, {1} - {2}. Sondaki piyasa değeri: {3} × 100 M ABD doları.",
    "Получено дней: {0}, {1} — {2}. Капитализация на конец: {3} × 100 млн долл. США.",
    "{0} 日間を取得（{1}〜{2}）。期末の時価総額は 1 億米ドル × {3}。",
    "{0}일을 가져왔습니다({1}~{2}). 기말 시가총액: 1억 달러 × {3}.",
    "已取到 {0} 個自然日，{1} 至 {2}。期末市值 {3} 億美元。",
    "已取到 {0} 个自然日，{1} 至 {2}。期末市值 {3} 亿美元。",
]

# 取数成功了但历史太短（源端没有那么多天）。与「一个币都没取到」分开说：前者是区间选错了，
# 后者是源没答 —— 两种修法不一样。
TOO_SHORT = [
    "Not enough market cap history in this span.",
    "In diesem Zeitraum gibt es nicht genug Marktkapitalisierungs-Historie.",
    "No hay suficiente historial de capitalización en este rango.",
    "Pas assez d'historique de capitalisation dans cet intervalle.",
    "Non abbastanza storia della capitalizzazione in questo intervallo.",
    "W tym zakresie nie ma wystarczająco długiej historii kapitalizacji.",
    "Não há histórico de capitalização longo o suficiente neste intervalo.",
    "V tomto období není dostatečně dlouhá historie kapitalizace.",
    "Bu aralıkta yeterince uzun piyasa değeri geçmişi yok.",
    "В этом диапазоне недостаточно длинной истории капитализации.",
    "この期間には十分な長さの時価総額の履歴がありません。",
    "이 구간에는 충분히 긴 시가총액 이력이 없습니다.",
    "這個區間裡沒有取到足夠長的市值歷史。",
    "这个区间里没有取到足够长的市值历史。",
]

MARKET_CAP_SUBTITLE = [
    "The fifteen coins with the largest market cap today, and how that ranking moved day by day, in US dollars.",
    "Die fünfzehn Münzen mit der größten Marktkapitalisierung heute und wie sich diese Rangliste Tag für Tag bewegte, in US-Dollar.",
    "Las quince monedas con mayor capitalización hoy y cómo se movió esa clasificación día a día, en dólares estadounidenses.",
    "Les quinze cryptomonnaies à la plus forte capitalisation aujourd'hui et l'évolution de ce classement jour après jour, en dollars américains.",
    "Le quindici monete con la capitalizzazione maggiore oggi e come questa classifica si è mossa giorno per giorno, in dollari americani.",
    "Piętnaście monet o największej kapitalizacji dziś i jak ta klasyfikacja zmieniała się dzień po dniu, w dolarach amerykańskich.",
    "As quinze moedas com a maior capitalização hoje e como esse ranking se moveu dia a dia, em dólares americanos.",
    "Patnáct mincí s největší kapitalizací dnes a jak se toto pořadí den po dni měnilo, v amerických dolarech.",
    "Bugün piyasa değeri en yüksek on beş coin ve bu sıralamanın gün gün nasıl değiştiği, ABD doları cinsinden.",
    "Пятнадцать монет с крупнейшей капитализацией сегодня и то, как этот рейтинг менялся день за днём, в долларах США.",
    "現在の時価総額が大きい十五銘柄と、その順位が日々どう動いたか。米ドル建て。",
    "현재 시가총액이 가장 큰 열다섯 코인과 그 순위가 날마다 어떻게 움직였는지. 미국 달러 기준.",
    "目前市值最大的十五個幣種，以及這個排名逐日的演變，以美元計價。",
    "当前市值最大的十五个币种，逐日市值排名演变，以美元计价。",
]

# 「榜上有哪些币」不是写死的清单，是取数那一刻的实时前 N 名 —— 这一页唯一一个没有选择器的
# 页面，所以这句话要替选择器回答「这些币从哪来」。稳定币那半句是用户拍板的：忠实反映排名。
MARKET_CAP_COUNT = [
    "At fetch time the {0} largest by market cap today become the pool, and every frame shows the top {0} by cap. The board includes stablecoins — they are a real part of this ranking.",
    "Beim Abruf werden die heute {0} größten nach Marktkapitalisierung zum Pool, und jedes Bild zeigt die {0} größten nach Kapitalisierung. Die Tafel enthält Stablecoins — sie sind ein echter Teil dieser Rangliste.",
    "Al obtener los datos, las {0} mayores por capitalización actual forman el grupo, y cada fotograma muestra las {0} primeras por capitalización. El tablero incluye monedas estables — son una parte real de esta clasificación.",
    "Au moment de la récupération, les {0} plus fortes capitalisations actuelles forment le vivier, et chaque image montre les {0} premières par capitalisation. Le tableau inclut les stablecoins — elles font réellement partie de ce classement.",
    "Al momento del recupero, le {0} maggiori per capitalizzazione attuale formano il gruppo, e ogni fotogramma mostra le prime {0} per capitalizzazione. La classifica include le stablecoin — sono una parte reale di questa graduatoria.",
    "Przy pobieraniu {0} największych według obecnej kapitalizacji tworzy pulę, a każda klatka pokazuje {0} największych według kapitalizacji. Tabela zawiera stablecoiny — są prawdziwą częścią tego rankingu.",
    "Na busca, as {0} maiores por capitalização atual formam o grupo, e cada quadro mostra as {0} primeiras por capitalização. O ranking inclui stablecoins — elas são parte real desta classificação.",
    "Při načtení tvoří {0} největších podle současné kapitalizace základnu a každý snímek ukazuje {0} největších podle kapitalizace. Tabulka zahrnuje stablecoiny — jsou skutečnou součástí tohoto žebříčku.",
    "Veri çekilirken bugünkü piyasa değerine göre en büyük {0} coin havuzu oluşturur ve her kare, değere göre ilk {0}'ı gösterir. Liste stabilcoinleri içerir — onlar bu sıralamanın gerçek bir parçası.",
    "При загрузке {0} крупнейших по текущей капитализации образуют пул, и каждый кадр показывает {0} крупнейших по капитализации. В рейтинг входят стейблкоины — они реальная часть этой таблицы.",
    "取得時点の時価総額上位 {0} 銘柄が候補となり、各フレームでは時価総額上位 {0} 銘柄を表示します。ランキングにはステーブルコインも含まれます——それらはこの順位の実際の一部です。",
    "조회 시점의 시가총액 상위 {0}개가 후보가 되고, 각 프레임은 시가총액 상위 {0}개를 보여줍니다. 순위에는 스테이블코인도 포함됩니다——그것은 이 순위의 실제 일부입니다.",
    "取數時按目前市值取前 {0} 名作候選池，每一期顯示市值前 {0} 名。榜單含穩定幣——它們是這個市值榜上真實的一部分。",
    "取数时按当前市值取前 {0} 名作候选池，每一期显示市值前 {0} 名。榜单含稳定币——它们是这个市值榜上真实的一部分。",
]

# 两个源各干一件事：排名来自 CoinGecko 的实时榜，逐日市值来自 CoinMetrics 的估算系列
# （全币种统一从 2019-06 起）。稳定币那句解释画面上那条「平的线」——没有它，读者会以为坏了。
MARKET_CAP_NOTE = [
    "The ranking comes from CoinGecko's live market cap board, and the daily caps from the public CoinMetrics API (its estimate series, which starts in June 2019). A stablecoin's price is one dollar by definition, so its line runs flat.",
    "Die Rangliste stammt vom Live-Marktkapital-Board von CoinGecko, die täglichen Werte aus der öffentlichen CoinMetrics-Schnittstelle (deren Schätzreihe, die im Juni 2019 beginnt). Der Kurs eines Stablecoins ist definitionsgemäß ein Dollar, deshalb verläuft seine Linie flach.",
    "La clasificación viene del tablero de capitalización en vivo de CoinGecko, y las capitalizaciones diarias de la API pública de CoinMetrics (su serie estimada, que empieza en junio de 2019). El precio de una moneda estable es un dólar por definición, así que su línea queda plana.",
    "Le classement vient du tableau de capitalisation en direct de CoinGecko, et les capitalisations quotidiennes de l'API publique CoinMetrics (sa série estimée, qui commence en juin 2019). Le cours d'un stablecoin est un dollar par définition, sa ligne est donc plate.",
    "La classifica viene dalla classifica di capitalizzazione in tempo reale di CoinGecko, e le capitalizzazioni giornaliere dall'API pubblica CoinMetrics (la sua serie stimata, che inizia a giugno 2019). Il prezzo di una stablecoin è un dollaro per definizione, quindi la sua linea resta piatta.",
    "Ranking pochodzi z aktualnej tablicy kapitalizacji CoinGecko, a dzienne kapitalizacje z publicznego API CoinMetrics (jego seria szacunkowa, zaczynająca się w czerwcu 2019). Cena stablecoina to z definicji jeden dolar, więc jego linia jest płaska.",
    "O ranking vem do quadro de capitalização ao vivo da CoinGecko, e as capitalizações diárias da API pública da CoinMetrics (sua série estimada, que começa em junho de 2019). O preço de uma stablecoin é um dólar por definição, então sua linha fica reta.",
    "Pořadí pochází z živého žebříčku kapitalizace CoinGecko a denní kapitalizace z veřejného API CoinMetrics (jeho odhadovaná řada začíná v červnu 2019). Cena stablecoinu je z definice jeden dolar, proto je její čára rovná.",
    "Sıralama CoinGecko'nun canlı piyasa değeri tablosundan, günlük değerler ise herkese açık CoinMetrics API'sinden (tahmin serisi, Haziran 2019'da başlar) gelir. Stabilcoin'in fiyatı tanım gereği bir dolardır, bu yüzden çizgisi düzdür.",
    "Рейтинг берётся из живого списка капитализации CoinGecko, а ежедневные капитализации — из публичного API CoinMetrics (оценочная серия, начинается в июне 2019). Цена стейблкоина по определению равна одному доллару, поэтому его линия идёт ровно.",
    "順位は CoinGecko のライブ時価総額ランキングから、日々の時価総額は公開 API の CoinMetrics（推計系列、2019 年 6 月開始）から取得しています。ステーブルコインの価格は定義上 1 ドルなので、その線は平らになります。",
    "순위는 CoinGecko의 실시간 시가총액 순위에서, 일별 시가총액은 공개 API CoinMetrics(추정 시리즈, 2019년 6월 시작)에서 가져옵니다. 스테이블코인의 가격은 정의상 1달러이므로 그 선은 평평합니다.",
    "排名取自 CoinGecko 的即時市值榜，逐日市值取自 CoinMetrics 公開介面（估算市值口徑，自 2019 年 6 月起）。穩定幣價格恆為一美元，因此它們那條線是平的。",
    "排名取自 CoinGecko 的实时市值榜，逐日市值取自 CoinMetrics 公开接口（估算市值口径，自 2019 年 6 月起）。稳定币价格恒为一美元，因此它们那条线是平的。",
]

MARKET_CAP_FETCHED = [
    "Got {0} coins · {1} days ({2} to {3}), leading at the end: {4}.",
    "{0} Münzen geholt · {1} Tage ({2} bis {3}), am Ende vorn: {4}.",
    "Se obtuvieron {0} monedas · {1} días ({2} a {3}), primera al final: {4}.",
    "{0} cryptomonnaies récupérées · {1} jours ({2} au {3}), en tête à la fin : {4}.",
    "Ottenute {0} monete · {1} giorni ({2} al {3}), in testa alla fine: {4}.",
    "Pobrano {0} monet · {1} dni ({2} do {3}), na końcu prowadzi: {4}.",
    "Obtidas {0} moedas · {1} dias ({2} a {3}), liderando no fim: {4}.",
    "Získáno {0} mincí · {1} dní ({2} až {3}), na konci vede: {4}.",
    "{0} coin alındı · {1} gün ({2} - {3}), sonda lider: {4}.",
    "Получено монет: {0} · дней {1} ({2} — {3}), на конец лидирует {4}.",
    "{0} 銘柄・{1} 日間を取得（{2}〜{3}）。期末の 1 位は {4}。",
    "{0}개 코인 · {1}일을 가져왔습니다({2}~{3}). 기말 1위는 {4}.",
    "已取到 {0} 個幣種 · {1} 個自然日（{2} 至 {3}），期末第一是 {4}。",
    "已取到 {0} 个币种 · {1} 个自然日（{2} 至 {3}），期末第一是 {4}。",
]

# 榜上取到的币少于 `CryptoCapBoard.FewestCoins`。缺数据的币是丢弃而不是画零，所以这一句
# 会在「前 15 名里有几个币源端不携带」时出现 —— 它不是错误，是要说出来的降级。
MARKET_CAP_TOO_FEW = [
    "A market-cap board needs at least 5 coins, and this time fewer came back.",
    "Eine Marktkapital-Tafel braucht mindestens 5 Münzen, diesmal kamen weniger zurück.",
    "Un tablero de capitalización necesita al menos 5 monedas, y esta vez volvieron menos.",
    "Un tableau de capitalisation a besoin d'au moins 5 cryptomonnaies, et cette fois il en est revenu moins.",
    "Una classifica di capitalizzazione richiede almeno 5 monete, e questa volta ne sono tornate meno.",
    "Tabela kapitalizacji potrzebuje co najmniej 5 monet, tym razem wróciło mniej.",
    "Um quadro de capitalização precisa de pelo menos 5 moedas, e desta vez voltaram menos.",
    "Tabulka kapitalizace potřebuje alespoň 5 mincí, tentokrát jich přišlo méně.",
    "Bir piyasa değeri tablosu en az 5 coin gerektirir, bu kez daha azı döndü.",
    "Для таблицы капитализации нужно минимум 5 монет, а в этот раз вернулось меньше.",
    "時価総額ランキングには最低 5 銘柄必要ですが、今回はそれより少なくなりました。",
    "시가총액 순위에는 최소 5개 코인이 필요하지만, 이번에는 더 적게 가져왔습니다.",
    "市值榜至少需要 5 個幣種，這次只取到了更少。",
    "市值榜至少需要 5 个币种，这次只取到了更少。",
]


ROWS = [
    ("NavCryptoCalendar.Content", NAV_CALENDAR),
    ("NavCryptoCapHistory.Content", NAV_CAP_HISTORY),
    ("NavCryptoMarketCap.Content", NAV_MARKET_CAP),
    ("CryptoCalendarPageTitle.Text", CALENDAR_TITLE),
    ("CryptoCalendarPageSubtitle.Text", CALENDAR_SUBTITLE),
    ("CryptoCalendarCoin.Header", COIN_HEADER),
    ("CryptoCalendarFetched", CALENDAR_FETCHED),
    ("CryptoCapHistoryPageTitle.Text", CAP_HISTORY_TITLE),
    ("CryptoCapHistoryPageSubtitle.Text", CAP_HISTORY_SUBTITLE),
    ("CryptoCapHistoryNote.Text", CAP_HISTORY_NOTE),
    ("CryptoCapCoin.Header", COIN_HEADER),
    ("CryptoCapWord", CAP_WORD),
    ("CryptoPriceWord", PRICE_WORD),
    ("CryptoDaysUnit", DAYS_UNIT),
    ("CryptoCapDefaultTitle", CAP_DEFAULT_TITLE),
    ("CryptoCapFetched", CAP_FETCHED),
    ("CryptoCapTooFewDays", TOO_SHORT),
    ("CryptoMarketCapPageTitle.Text", MARKET_CAP_TITLE),
    ("CryptoMarketCapPageSubtitle.Text", MARKET_CAP_SUBTITLE),
    ("CryptoMarketCapCount", MARKET_CAP_COUNT),
    ("CryptoMarketCapNote.Text", MARKET_CAP_NOTE),
    ("CryptoMarketCapFetched", MARKET_CAP_FETCHED),
    ("CryptoMarketCapTooFew", MARKET_CAP_TOO_FEW),
    ("CryptoMarketCapTooShort", TOO_SHORT),
    ("CryptoUnitCoins", UNIT_COINS),
]


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
