"""给 14 份帮助手册补上本版改过的区间口径。

四处，都按**章节位置**定位而不是按句子匹配 —— 因为同一种说法在 14 种语言里长得
不一样，而"第 N 章的最后一条 bullet"在哪一种语言里都是同一处。

- 数据章最后一条（那条写「超过约 640 个自然日」的）：整行替换。它现在说得不对了 ——
  成交量与板块竞速的上限是 900 天，K线页靠分页能到十五年，月线一次给满。
- K线 / 成交量换手率 / 市值榜三章：在最后一条 bullet 后面各加一句本页的档位。

幂等：替换前先确认旧行还在（旧行的指纹是它含 "640"，这在 14 种语言里都一样）；
插入前先确认那一句还没在。跑第二遍应当一行都不动。

BOM 与 LF 都保持原样：这些 md 有的带 BOM 有的不带，脚本读的时候记下来，写回去照原样。
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
HELP = REPO / "src" / "MarketMotionStudio" / "Assets" / "Help"

# 章节序号（0 起，按 `## ` 出现的顺序）。25 章在 14 种语言里同结构同顺序，
# 这是项目既定的约束，脚本靠它活着。
CH_CANDLE = 3
CH_VOLUME = 4
CH_CAP = 6
CH_DATA = 22


def candle(lang):
    """K线页：区间随周期变，日线十年在里面（一页 640 根、翻六页）。"""
    return {
        "zh-Hans":
            "- **区间**跟着周期走：日线是 3、6、12 个月或 3、5、10 年；周线 1、3、5、10 年；"
            "月线 3、5、10 年或最长（约 13 年）。日线一次请求约 640 根，这一页会一页页往回翻，"
            "十年约两千五百根。",
        "zh-Hant":
            "- **區間**跟著週期走：日線是 3、6、12 個月或 3、5、10 年；週線 1、3、5、10 年；"
            "月線 3、5、10 年或最長（約 13 年）。日線一次請求約 640 根，這一頁會一頁頁往回翻，"
            "十年約兩千五百根。",
        "en-US":
            "- **Range** follows the period: daily offers 3, 6 or 12 months and 3, 5 or 10 years; "
            "weekly 1, 3, 5 or 10 years; monthly 3, 5 or 10 years, or as far back as the source "
            "goes (about 13). One request carries about 640 daily bars and this page walks "
            "backwards a page at a time, so ten years — around 2,500 bars — is inside it.",
        "ja":
            "- **期間**は周期によって変わります：日足は 3、6、12 か月または 3、5、10 年、"
            "週足は 1、3、5、10 年、月足は 3、5、10 年または最長（約 13 年）。"
            "1 回のリクエストで約 640 本の日足が返り、このページはページごとに遡るので、"
            "10 年（約 2,500 本）も範囲内です。",
        "ko":
            "- **구간**은 주기에 따라 달라집니다: 일간은 3·6·12개월 또는 3·5·10년, "
            "주간은 1·3·5·10년, 월간은 3·5·10년 또는 가장 긴 구간(약 13년). "
            "한 번의 요청으로 약 640개의 일간 봉이 돌아오고 이 페이지는 한 페이지씩 거슬러 올라가므로, "
            "10년(약 2,500개)도 범위 안입니다.",
        "de":
            "- **Der Zeitraum** folgt der Periode: Tageskerzen bieten 3, 6 oder 12 Monate sowie "
            "3, 5 oder 10 Jahre; Wochenkerzen 1, 3, 5 oder 10 Jahre; Monatskerzen 3, 5 oder "
            "10 Jahre oder so weit zurück, wie die Quelle reicht (etwa 13). Eine Anfrage liefert "
            "rund 640 Tageskerzen, und diese Seite blättert seitenweise zurück — zehn Jahre, "
            "etwa 2.500 Kerzen, liegen darin.",
        "fr":
            "- **La plage** suit la période : en quotidien 3, 6 ou 12 mois, ou 3, 5 ou 10 ans ; "
            "en hebdomadaire 1, 3, 5 ou 10 ans ; en mensuel 3, 5 ou 10 ans, ou le maximum dont "
            "la source dispose (environ 13 ans). Une requête ramène environ 640 bougies "
            "quotidiennes et la page remonte page par page : dix ans, soit quelque 2 500 bougies, "
            "y tiennent.",
        "it":
            "- **L'intervallo** segue il periodo: il giornaliero offre 3, 6 o 12 mesi e 3, 5 o "
            "10 anni; il settimanale 1, 3, 5 o 10 anni; il mensile 3, 5 o 10 anni, oppure il "
            "massimo di cui la fonte dispone (circa 13). Una richiesta porta circa 640 barre "
            "giornaliere e la pagina torna indietro una pagina alla volta: dieci anni, circa "
            "2.500 barre, ci stanno dentro.",
        "es":
            "- **El rango** sigue al periodo: en diario, 3, 6 o 12 meses, o 3, 5 o 10 años; en "
            "semanal, 1, 3, 5 o 10 años; en mensual, 3, 5 o 10 años o el máximo del que dispone "
            "la fuente (unos 13). Una petición devuelve unas 640 velas diarias y la página "
            "retrocede página a página, así que diez años —unas 2.500 velas— entran sin problema.",
        "pt-BR":
            "- **O intervalo** acompanha o período: no diário, 3, 6 ou 12 meses, ou 3, 5 ou "
            "10 anos; no semanal, 1, 3, 5 ou 10 anos; no mensal, 3, 5 ou 10 anos ou o máximo de "
            "que a fonte dispõe (cerca de 13). Um pedido traz cerca de 640 barras diárias e a "
            "página volta página por página, então dez anos — cerca de 2.500 barras — cabem nela.",
        "pl":
            "- **Zakres** zależy od interwału: dzienny daje 3, 6 lub 12 miesięcy albo 3, 5 lub "
            "10 lat; tygodniowy 1, 3, 5 lub 10 lat; miesięczny 3, 5 lub 10 lat lub maksimum, "
            "jakie ma źródło (około 13). Jedno żądanie przynosi około 640 świec dziennych, a "
            "strona cofa się strona po stronie, więc dziesięć lat — około 2.500 świec — mieści "
            "się w tym.",
        "cs":
            "- **Rozsah** se řídí periodou: denní nabízí 3, 6 nebo 12 měsíců a 3, 5 nebo 10 let; "
            "týdenní 1, 3, 5 nebo 10 let; měsíční 3, 5 nebo 10 let nebo maximum, které zdroj má "
            "(asi 13). Jeden požadavek přinese asi 640 denních svíček a strana se vrací po "
            "stránkách, takže deset let — asi 2 500 svíček — se do toho vejde.",
        "ru":
            "- **Диапазон** зависит от периода: дневной даёт 3, 6 или 12 месяцев либо 3, 5 или "
            "10 лет; недельный — 1, 3, 5 или 10 лет; месячный — 3, 5 или 10 лет или максимум "
            "источника (около 13). Один запрос приносит около 640 дневных свечей, а страница "
            "листает назад по страницам, поэтому десять лет — примерно 2 500 свечей — входят "
            "в предел.",
        "tr":
            "- **Aralık** periyoda göre değişir: günlükte 3, 6 veya 12 ay ya da 3, 5 veya 10 yıl; "
            "haftalıkta 1, 3, 5 veya 10 yıl; aylıkta 3, 5 veya 10 yıl ya da kaynağın sunduğu en "
            "uzun aralık (yaklaşık 13). Bir istek yaklaşık 640 günlük mum getirir ve sayfa geriye "
            "doğru sayfa sayfa ilerler, bu yüzden on yıl — yaklaşık 2.500 mum — sınırın içinde kalır.",
    }[lang]


def volume(lang):
    """成交量换手率：日线多了 24 个月档，自定义上限是 900 天。"""
    return {
        "zh-Hans":
            "- 日线的区间可选 1、3、6、12、24 个月或自定义起止日；自定义最长约 900 个自然日——"
            "一次请求能取的量——日期选择器到此为止。日内模式只能在这几个交易日里挑一天。",
        "zh-Hant":
            "- 日線的區間可選 1、3、6、12、24 個月或自訂起訖日；自訂最長約 900 個自然日——"
            "一次請求能取的量——日期選擇器到此為止。日內模式只能在這幾個交易日裡挑一天。",
        "en-US":
            "- On daily bars the range is 1, 3, 6, 12 or 24 months, or a start and end date of "
            "your own; a custom span stops at about 900 calendar days — what one request returns "
            "— and the date pickers stop there too. The intraday mode offers a choice among "
            "those few trading days.",
        "ja":
            "- 日足の期間は 1、3、6、12、24 か月、または開始日と終了日の指定から選べます。"
            "カスタム期間は約 900 日（1 回のリクエストで取得できる量）までで、"
            "日付ピッカーもそこまでです。日中モードでは、その数営業日の中から 1 日を選びます。",
        "ko":
            "- 일간 구간은 1·3·6·12·24개월 또는 직접 지정하는 시작일과 종료일 중에서 고릅니다. "
            "사용자 지정은 약 900일(한 번의 요청으로 가져올 수 있는 양)까지이며, "
            "날짜 선택기도 거기까지입니다. 일중 모드는 그 며칠의 거래일 가운데 하루를 고릅니다.",
        "de":
            "- Bei Tagesbalken sind es 1, 3, 6, 12 oder 24 Monate oder ein eigenes Start- und "
            "Enddatum; ein eigener Zeitraum endet bei etwa 900 Kalendertagen — so viel liefert "
            "eine Anfrage — und die Datumsauswahl endet dort ebenfalls. Der Intraday-Modus bietet "
            "eine Wahl unter den wenigen verfügbaren Handelstagen.",
        "fr":
            "- En quotidien, la plage est de 1, 3, 6, 12 ou 24 mois, ou de dates de début et de "
            "fin à votre choix ; une plage personnalisée s'arrête à environ 900 jours calendaires "
            "— ce qu'une requête ramène — et les sélecteurs de date s'arrêtent au même endroit. "
            "Le mode intrajournalier propose de choisir un jour parmi les quelques séances "
            "disponibles.",
        "it":
            "- Sul giornaliero l'intervallo è di 1, 3, 6, 12 o 24 mesi, oppure una data di inizio "
            "e di fine scelte da te; un intervallo personalizzato si ferma a circa 900 giorni di "
            "calendario — quanto restituisce una richiesta — e anche i selettori di data si "
            "fermano lì. La modalità intraday propone di scegliere uno dei pochi giorni "
            "disponibili.",
        "es":
            "- En diario el rango es de 1, 3, 6, 12 o 24 meses, o unas fechas de inicio y fin "
            "propias; un intervalo personalizado se detiene en unos 900 días naturales —lo que "
            "devuelve una petición— y los selectores de fecha se detienen ahí también. El modo "
            "intradía ofrece elegir un día entre los pocos disponibles.",
        "pt-BR":
            "- No diário o intervalo é de 1, 3, 6, 12 ou 24 meses, ou datas de início e fim "
            "definidas por você; um intervalo personalizado para em cerca de 900 dias corridos "
            "— o que um pedido devolve — e os seletores de data também param aí. O modo "
            "intradiário oferece escolher um dia entre os poucos disponíveis.",
        "pl":
            "- W interwale dziennym zakres to 1, 3, 6, 12 lub 24 miesiące albo własne daty "
            "początku i końca; zakres niestandardowy kończy się na około 900 dniach "
            "kalendarzowych — tyle zwraca jedno żądanie — i wybór dat kończy się w tym samym "
            "miejscu. Tryb intraday pozwala wybrać jeden z kilku dostępnych dni.",
        "cs":
            "- U denních dat je rozsah 1, 3, 6, 12 nebo 24 měsíců, nebo vlastní datum začátku a "
            "konce; vlastní rozsah končí asi na 900 kalendářních dnech — tolik vrátí jeden "
            "požadavek — a výběr data končí tamtéž. V intradenním režimu si vybíráte jeden "
            "z několika dostupných dnů.",
        "ru":
            "- На дневных данных диапазон — 1, 3, 6, 12 или 24 месяца либо свои даты начала и "
            "конца; пользовательский диапазон ограничен примерно 900 календарными днями — столько "
            "возвращает один запрос — и выбор даты заканчивается там же. Внутридневной режим "
            "предлагает выбрать один из нескольких доступных дней.",
        "tr":
            "- Günlük veride aralık 1, 3, 6, 12 veya 24 ay ya da kendi belirlediğiniz başlangıç "
            "ve bitiş tarihidir; özel aralık yaklaşık 900 takvim gününde durur — bir isteğin "
            "döndürdüğü kadar — ve tarih seçiciler de orada durur. Gün içi modu, o birkaç işlem "
            "günü arasından bir gün seçmenizi sağlar.",
    }[lang]


def marketcap(lang):
    """市值榜：多了「最长」，它的尽头是月线一次给满的 180 期。"""
    return {
        "zh-Hans":
            "- 区间可选近 12 个月、3 年、5 年、10 年，或「最长」——月线一次请求就给满 180 期"
            "（约 15 年），这一档的尽头就在那里。也可以自己填起止日期。",
        "zh-Hant":
            "- 區間可選近 12 個月、3 年、5 年、10 年，或「最長」——月線一次請求就給滿 180 期"
            "（約 15 年），這一檔的盡頭就在那裡。也可以自己填起訖日期。",
        "en-US":
            "- The range is the last 12 months, 3, 5 or 10 years, or **Longest** — one request "
            "returns all 180 monthly periods, about fifteen years, and that is where the longest "
            "entry ends. A start and an end date of your own is offered too.",
        "ja":
            "- 期間は直近 12 か月、3 年、5 年、10 年、または「最長」から選べます——"
            "月足は 1 回のリクエストで 180 期（約 15 年）まるごと返るので、最長の終点はそこです。"
            "開始日と終了日を自分で指定することもできます。",
        "ko":
            "- 구간은 최근 12개월, 3년, 5년, 10년 또는 「가장 긴 구간」에서 고릅니다. "
            "월간은 한 번의 요청으로 180개 기간(약 15년)이 모두 돌아오므로, "
            "가장 긴 항목의 끝도 거기입니다. 시작일과 종료일을 직접 지정할 수도 있습니다.",
        "de":
            "- Der Zeitraum sind die letzten 12 Monate, 3, 5 oder 10 Jahre oder **Längster** — "
            "eine Anfrage liefert alle 180 Monatsperioden, etwa fünfzehn Jahre, und dort endet "
            "dieser Eintrag. Ein eigenes Start- und Enddatum wird ebenfalls angeboten.",
        "fr":
            "- La plage est les 12 derniers mois, 3, 5 ou 10 ans, ou **Maximale** — une requête "
            "ramène les 180 périodes mensuelles, soit environ quinze ans, et c'est là que cette "
            "entrée s'arrête. Des dates de début et de fin à vous sont proposées également.",
        "it":
            "- L'intervallo è gli ultimi 12 mesi, 3, 5 o 10 anni, o **Massimo** — una richiesta "
            "restituisce tutti i 180 periodi mensili, circa quindici anni, ed è lì che finisce "
            "questa voce. Sono offerte anche una data di inizio e una di fine scelte da te.",
        "es":
            "- El rango son los últimos 12 meses, 3, 5 o 10 años, o **Máximo** — una petición "
            "devuelve los 180 periodos mensuales, unos quince años, y ahí termina esa opción. "
            "También puedes fijar tus propias fechas de inicio y fin.",
        "pt-BR":
            "- O intervalo são os últimos 12 meses, 3, 5 ou 10 anos, ou **Máximo** — um pedido "
            "devolve todos os 180 períodos mensais, cerca de quinze anos, e é aí que essa opção "
            "termina. Também é possível definir suas próprias datas de início e fim.",
        "pl":
            "- Zakres to ostatnie 12 miesięcy, 3, 5 lub 10 lat albo **Najdłuższy** — jedno żądanie "
            "zwraca wszystkie 180 okresów miesięcznych, około piętnastu lat, i tam kończy się ta "
            "pozycja. Możesz też podać własne daty początku i końca.",
        "cs":
            "- Rozsah je posledních 12 měsíců, 3, 5 nebo 10 let, nebo **Nejdelší** — jeden "
            "požadavek vrátí všech 180 měsíčních období, asi patnáct let, a tam tato položka "
            "končí. Lze zadat i vlastní datum začátku a konce.",
        "ru":
            "- Диапазон — последние 12 месяцев, 3, 5 или 10 лет либо «Максимальный»: один запрос "
            "возвращает все 180 месячных периодов, примерно пятнадцать лет, и на этом этот пункт "
            "заканчивается. Можно задать и свои даты начала и конца.",
        "tr":
            "- Aralık son 12 ay, 3, 5 veya 10 yıl ya da **En uzun** seçeneğidir — bir istek 180 "
            "aylık dönemin tamamını, yani yaklaşık on beş yılı döndürür ve bu seçenek orada biter. "
            "Kendi başlangıç ve bitiş tarihlerinizi de yazabilirsiniz.",
    }[lang]


def data_note(lang):
    """数据章那条上限说明：现在的口径按页分档，且点明丢的是开头。"""
    return {
        "zh-Hans":
            "- 区间超过一次请求能取回的量就会被直接拒绝，而不是悄悄截断：日线约 900 个自然日，"
            "K线页靠一页页往回翻能到约十五年，月线则一次给满。悄悄截断是最坏的结果——丢的是"
            "开头，而开头少了几年的图看起来完全正常。",
        "zh-Hant":
            "- 區間超過一次請求能取回的量就會被直接拒絕，而不是悄悄截斷：日線約 900 個自然日，"
            "K線頁靠一頁頁往回翻能到約十五年，月線則一次給滿。悄悄截斷是最壞的結果——丟的是"
            "開頭，而開頭少了幾年的圖看起來完全正常。",
        "en-US":
            "- A range longer than one request can return is refused rather than quietly "
            "truncated: about 900 calendar days of daily bars, about fifteen years on the candle "
            "page, which pages backwards, and a full history of monthly bars. Truncating quietly "
            "is the worst outcome — what goes missing is the **beginning**, and a chart missing "
            "its first years is a shorter chart that looks entirely correct.",
        "ja":
            "- 1 回のリクエストで取れる量を超える期間は、こっそり切り詰めるのではなく拒否されます："
            "日足は約 900 日、K線ページはページを遡って約 15 年、月足は全期間が一度に返ります。"
            "こっそり切り詰めるのが最悪の結果です——失われるのは**冒頭**で、"
            "最初の数年が抜けたグラフは短くなっただけで、見た目はまったく普通だからです。",
        "ko":
            "- 한 번의 요청으로 가져올 수 있는 양을 넘는 구간은 조용히 잘라내지 않고 거부됩니다: "
            "일간은 약 900일, K선 페이지는 페이지를 거슬러 약 15년, 월간은 전체 기간을 한 번에 "
            "줍니다. 조용히 잘라내는 것이 최악의 결과입니다——사라지는 것은 **앞부분**이며, "
            "첫 몇 년이 빠진 차트는 짧아졌을 뿐 전혀 정상적으로 보이기 때문입니다.",
        "de":
            "- Ein Zeitraum, der über das hinausgeht, was eine Anfrage liefert, wird abgelehnt "
            "statt still gekürzt: etwa 900 Kalendertage bei Tagesbalken, etwa fünfzehn Jahre auf "
            "der Kerzenseite, die seitenweise zurückblättert, und die ganze Historie bei "
            "Monatsbalken. Stilles Kürzen ist das schlechteste Ergebnis — es fehlt dann der "
            "**Anfang**, und ein Diagramm ohne seine ersten Jahre ist ein kürzeres Diagramm, das "
            "völlig normal aussieht.",
        "fr":
            "- Une plage plus longue que ce qu'une requête peut ramener est refusée plutôt que "
            "tronquée en silence : environ 900 jours calendaires en quotidien, environ quinze ans "
            "sur la page Chandeliers, qui remonte page par page, et toute l'historique en "
            "mensuel. Tronquer en silence est le pire résultat — ce qui disparaît alors, c'est le "
            "**début**, et un graphique amputé de ses premières années est un graphique plus court "
            "qui a l'air parfaitement normal.",
        "it":
            "- Un intervallo più lungo di quanto una richiesta possa restituire viene rifiutato "
            "invece di essere troncato in silenzio: circa 900 giorni di calendario sul "
            "giornaliero, circa quindici anni sulla pagina Candele, che sfoglia indietro una "
            "pagina alla volta, e tutta la storia sul mensile. Troncare in silenzio è il risultato "
            "peggiore — a mancare è l'**inizio**, e un grafico senza i suoi primi anni è un grafico "
            "più corto che sembra del tutto normale.",
        "es":
            "- Un rango mayor que lo que una petición puede devolver se rechaza en lugar de "
            "recortarse en silencio: unos 900 días naturales en diario, unos quince años en la "
            "página de velas, que retrocede página a página, y el historial completo en mensual. "
            "Recortar en silencio es el peor resultado — lo que falta es el **principio**, y un "
            "gráfico sin sus primeros años es un gráfico más corto que parece completamente normal.",
        "pt-BR":
            "- Um intervalo maior do que um pedido pode devolver é recusado em vez de ser cortado "
            "em silêncio: cerca de 900 dias corridos no diário, cerca de quinze anos na página de "
            "velas, que volta página por página, e o histórico completo no mensal. Cortar em "
            "silêncio é o pior resultado — o que desaparece é o **começo**, e um gráfico sem seus "
            "primeiros anos é um gráfico mais curto que parece inteiramente normal.",
        "pl":
            "- Zakres dłuższy niż to, co jedno żądanie może zwrócić, jest odrzucany zamiast po "
            "cichu ucięty: około 900 dni kalendarzowych na interwale dziennym, około piętnastu lat "
            "na stronie świec, która cofa się strona po stronie, i cała historia na miesięcznym. "
            "Ciche ucięcie to najgorszy wynik — znika wtedy **początek**, a wykres bez pierwszych "
            "lat to po prostu krótszy wykres, który wygląda zupełnie normalnie.",
        "cs":
            "- Rozsah delší, než může jeden požadavek vrátit, je odmítnut místo tichého zkrácení: "
            "asi 900 kalendářních dnů u denních dat, asi patnáct let na straně svíček, která "
            "listuje zpět po stránkách, a celá historie u měsíčních. Tiché zkrácení je nejhorší "
            "výsledek — chybí pak **začátek**, a graf bez prvních let je jen kratší graf, který "
            "vypadá naprosto normálně.",
        "ru":
            "- Диапазон длиннее того, что может вернуть один запрос, отклоняется, а не обрезается "
            "молча: около 900 календарных дней на дневных данных, около пятнадцати лет на странице "
            "свечей, которая листает назад по страницам, и вся история на месячных. Тихая обрезка "
            "— худший исход: пропадает **начало**, а график без первых лет — это просто более "
            "короткий график, который выглядит совершенно нормально.",
        "tr":
            "- Bir isteğin döndürebileceğinden uzun bir aralık sessizce kısaltılmaz, reddedilir: "
            "günlükte yaklaşık 900 takvim günü, sayfa sayfa geri giden mum sayfasında yaklaşık on "
            "beş yıl ve aylıkta tüm geçmiş. Sessizce kısaltmak en kötü sonuçtur — eksilen kısım "
            "**başlangıçtır** ve ilk yılları çıkmış bir grafik, tamamen normal görünen daha kısa "
            "bir grafiktir.",
    }[lang]


LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]


def chapters(text):
    """按 `## ` 切章，返回 [(标题, 起, 止)]，止不含下一章标题行。"""
    lines = text.split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
    out = []

    for n, start in enumerate(heads):
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        out.append((lines[start][3:].strip(), start, end))

    return out, lines


def last_bullet(lines, start, end):
    """这一章最后一条 `- ` 开头的行号；没有就返回 None。"""
    hit = None

    for i in range(start, end):
        if lines[i].startswith("- "):
            hit = i

    return hit


def main():
    changed = 0

    for lang in LANGS:
        path = HELP / f"help-{lang}.md"
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig" if bom else "utf-8")
        lines = text.split("\n")
        chaps, _ = chapters(text)
        done = []

        if len(chaps) < 23:
            print(f"× {lang}: 只数到 {len(chaps)} 章，应当是 25")
            return 1

        # 1) 三章各加一句：插在这一章最后一条 bullet 后面。
        for index, maker in ((CH_CANDLE, candle), (CH_VOLUME, volume), (CH_CAP, marketcap)):
            _, start, end = chaps[index]
            at = last_bullet(lines, start, end)

            if at is None:
                print(f"× {lang}: 「{chaps[index][0]}」里没有 bullet")
                return 1

            line = maker(lang)

            # 幂等：插完之后它就是这一章的最后一条，所以"最后一条已经是它"等于"插过了"。
            if lines[at] == line:
                continue

            lines.insert(at + 1, line)
            chaps, _ = chapters("\n".join(lines))
            done.append(chaps[index][0])
            changed += 1

        # 2) 数据章那条上限：整行替换。旧行的指纹是它写着 640 —— 14 种语言都一样。
        _, start, end = chaps[CH_DATA]
        hit = None

        for i in range(start, end):
            if lines[i].startswith("- ") and "640" in lines[i]:
                hit = i

        note = data_note(lang)

        if hit is None:
            if any(note == s for s in lines[start:end]):
                pass  # 已经换过了
            else:
                print(f"× {lang}: 「{chaps[CH_DATA][0]}」里找不到写 640 的那条")
                return 1
        elif lines[hit] != note:
            lines[hit] = note
            done.append(chaps[CH_DATA][0])
            changed += 1

        if done:
            path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + "\n".join(lines).encode("utf-8"))
            print(f"· {lang}: {' / '.join(done)}")

    print(f"\n改了 {changed} 处（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
