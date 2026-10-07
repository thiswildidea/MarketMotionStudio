# -*- coding: utf-8 -*-
r"""把「市值历程」这一页要用的 resw 键注入 14 份 Resources.resw。

这一页的文案有一处**别的页面没有的难处**：市值这一栏的单位是「亿」，而亿没有英文。
德文是 100 Mio.、俄文是 100 млн、日文与中文写作億 —— 同一个数量级，十四种写法。
所以 `CapHistoryCapUnit` 是「数量级 + 货币」两截的模板，货币由页面用市场自己的
键（`MarketProfile.CurrencyKey`）填进去，而不是每种货币各写一个键。

两个共享键也在这里加：`StudioRange60M` / `StudioRange120M`（五年、十年）。这一页
要的是跨度 —— 一两个月的市值曲线没有故事 —— 而既有档位最长只有两年。

格式与坑都照 `port-marketcap-resw.py`：resw 是 UTF-8 **带 BOM** + LF，必须
`read_bytes().decode('utf-8-sig')` 读、`write_bytes()` 写回；删同名键要按「基础名 +
可选后缀」匹配、正则后跟 `[^>]*`（文件里两种条目格式并存，写死 `">` 只匹配其中一种，
漏删会让 MakePri 以 PRI278 拒绝整份文件）。

幂等：先删后插，跑几遍结果一样。

用法：python tools\port-caphistory-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 列序与 LANGS 一致：en de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans
# 条：**导航名在这一语境里不能和另一页重名**，这是这一页踩过的一次实打实的坑。最初这
# 一列是照各语言的习惯缩写取的，于是 pt-BR / tr / ru / ja / ko 五种语言里它和上一页
# 「市值榜」的导航名**逐字相同** —— 侧边栏里两个不同页面叫同一个名字，用户分不出哪
# 个是哪个。而且这不只难看：商店清单那个脚本按「清单里有没有以这一页名字开头的条目」
# 判重，日文的「時価総額レース」正是以「時価総額」开头，于是第十八页那一条被**静默跳过**
# 了 —— 脚本报「已最新」，少一条。所以撞车的五种语言改用手册里那一章的全名，它天生长
# 出那一截说「历程」的话。其余九种语言原本就没重名，不动。
PAGE = [
    ("NavCapHistory.Content", [
        "Market value", "Marktwert", "Valor de mercado", "Valeur de marché",
        "Valore di mercato", "Wartość rynkowa", "Histórico de valor de mercado",
        "Tržní hodnota", "Piyasa değeri geçmişi", "История капитализации",
        "時価総額の推移", "시가총액 추이", "市值歷程", "市值历程"]),

    ("CapHistoryPageTitle.Text", [
        "Market Value History", "Marktwert-Verlauf", "Historial de valor de mercado",
        "Historique de la valeur de marché", "Storia del valore di mercato",
        "Historia wartości rynkowej", "Histórico de valor de mercado",
        "Historie tržní hodnoty", "Piyasa değeri geçmişi", "История капитализации",
        "時価総額の推移", "시가총액 추이", "市值歷程", "市值历程"]),

    # 这一条后来被改过：这一页现在能同时画几家公司，标题下的副标题得说清两副样子 —— 一家
    # 公司时是「市值在上、股价在下」，几家时是整个画面留给市值、每条线在末端写名字。
    # **同一个键只有一个 owner 脚本**，多标的那批新键在 `port-caphistory-compare-resw.py`，
    # 两边都沾这个键的话，先跑的那份留下的字会被后跑的删掉，而删的一方一声不响。
    ("CapHistoryPageSubtitle.Text", [
        "One company's circulating market value over the years with its share price "
        "beneath it — or several companies compared as one line each, named at its end.",
        "Der Marktwert eines Unternehmens im Zeitverlauf, darunter sein Aktienkurs — oder "
        "mehrere Unternehmen, je eine Linie, am Ende beschriftet.",
        "El valor de mercado en circulación de una empresa a lo largo de los años con su "
        "cotización debajo — o varias empresas comparadas, cada una una línea rotulada en "
        "su extremo.",
        "La valeur de marché en circulation d'une entreprise au fil des années, avec son "
        "cours en dessous — ou plusieurs entreprises comparées, chacune une courbe nommée "
        "à son extrémité.",
        "Il valore di mercato flottante di un'azienda nel tempo, con sotto il prezzo "
        "dell'azione — o più aziende a confronto, una linea ciascuna, nominata all'estremità.",
        "Wartość rynkowa jednej spółki na przestrzeni lat, a pod nią kurs akcji — albo kilka "
        "spółek, każda jedną linią podpisaną na końcu.",
        "O valor de mercado em circulação de uma empresa ao longo dos anos, com o preço da "
        "ação abaixo — ou várias empresas comparadas, uma linha cada, nomeada na ponta.",
        "Tržní hodnota jedné firmy v čase a pod ní cena akcie — nebo více firem, každá jednou "
        "linií pojmenovanou na konci.",
        "Bir şirketin yıllar içindeki dolaşımdaki piyasa değeri, altında hisse fiyatı — ya da "
        "karşılaştırılan birden çok şirket, her biri ucunda adı yazan bir çizgi.",
        "Капитализация одной компании по годам, а под ней — цена акции; либо несколько "
        "компаний, у каждой своя линия с подписью на конце.",
        "一社の流通時価総額の推移と、同じ軸上にその株価。複数社なら一本ずつの線になり、"
        "末端に名前が付きます。",
        "한 기업의 유통 시가총액 추이와 같은 축 위의 주가. 여러 기업이면 선 하나씩으로 "
        "그려지고 끝에 이름이 붙습니다.",
        "一家公司流通市值隨年份的變化，同一時間軸上是它的股價；選了幾家公司則各畫一條線，"
        "在末端標出名字。",
        "一家公司流通市值随年份的变化，同一时间轴上是它的股价；选了几家公司则各画一条线，"
        "在末端标出名字。"]),

    # 上面板名。写「流通」而不是「总」：源端只给出流通股本的口径，画面上写错了
    # 口径，数字再准也是错的。
    ("CapHistoryCapWord", [
        "Market value", "Marktwert", "Valor en circulación", "Valeur en circulation",
        "Valore flottante", "Wartość w obrocie", "Valor em circulação", "Tržní hodnota",
        "Dolaşımdaki değer", "Капитализация", "流通時価総額", "유통 시가총액",
        "流通市值", "流通市值"]),

    ("CapHistoryPriceWord", [
        "Share price", "Aktienkurs", "Cotización", "Cours de l'action",
        "Prezzo dell'azione", "Kurs akcji", "Preço da ação", "Cena akcie",
        "Hisse fiyatı", "Цена акции", "株価", "주가", "股價", "股价"]),

    # 只有香港用这一条：那个市场拿不到不复权收盘价，价格是成交额除以成交量。
    # 画面上必须说清它是均价，不然「股价」画的是另一个数。
    ("CapHistoryAveragePriceWord", [
        "Average trade price", "Durchschnittlicher Handelskurs",
        "Precio medio de negociación", "Prix moyen des transactions",
        "Prezzo medio degli scambi", "Średnia cena transakcji",
        "Preço médio de negociação", "Průměrná obchodní cena", "Ortalama işlem fiyatı",
        "Средняя цена сделки", "平均売買価格", "평균 거래가", "成交均價", "成交均价"]),

    # 数量级 + 货币。亿在英文里没有，所以每种语言写自己的数量级。
    ("CapHistoryCapUnit", [
        "100M {0}", "100 Mio. {0}", "100 M {0}", "100 M {0}", "100 Mln {0}",
        "100 mln {0}", "100 mi {0}", "100 mil. {0}", "100 Mn {0}", "100 млн {0}",
        "億{0}", "억 {0}", "億{0}", "亿{0}"]),

    ("CapHistoryDefaultTitle", [
        "{0} market value", "{0} Marktwert", "{0} valor de mercado",
        "{0} valeur de marché", "{0} valore di mercato", "{0} wartość rynkowa",
        "{0} valor de mercado", "{0} tržní hodnota", "{0} piyasa değeri",
        "{0} капитализация", "{0} の時価総額", "{0} 시가총액", "{0}市值歷程",
        "{0}市值历程"]),

    ("CapHistoryFetched", [
        "{0} trading days, {1} to {2}. Value at the end: {3}.",
        "{0} Handelstage, {1} bis {2}. Marktwert am Ende: {3}.",
        "{0} sesiones, del {1} al {2}. Valor al final: {3}.",
        "{0} séances, du {1} au {2}. Valeur à la fin : {3}.",
        "{0} sedute, dal {1} al {2}. Valore alla fine: {3}.",
        "{0} sesji, od {1} do {2}. Wartość na koniec: {3}.",
        "{0} pregões, de {1} a {2}. Valor no fim: {3}.",
        "{0} obchodních dnů, {1} až {2}. Tržní hodnota na konci: {3}.",
        "{0} işlem günü, {1} - {2}. Sonda değer: {3}.",
        "{0} торговых дней, с {1} по {2}. Капитализация в конце: {3}.",
        "{0} 営業日、{1} から {2}。期末の時価総額は {3}。",
        "{0}거래일, {1}~{2}. 기말 시가총액 {3}.",
        "已取到 {0} 個交易日，{1} 至 {2}。期末市值 {3}。",
        "已取到 {0} 个交易日，{1} 至 {2}。期末市值 {3}。"]),

    # 这一条是这一页最常见的失败，所以写清原因：指数没有换手率，股本无从还原。
    ("CapHistoryNoTurnover", [
        "No turnover figure for this instrument in that range. The share count — and so "
        "the value — is recovered from it, so without one there is nothing to draw.",
        "Für dieses Instrument liegt in diesem Zeitraum keine Umsatzrate vor. Aus ihr wird "
        "die Aktienzahl und damit der Wert gewonnen — ohne sie gibt es nichts zu zeichnen.",
        "No hay dato de rotación para este instrumento en ese rango. De él se deduce el "
        "número de acciones y por tanto el valor; sin él no hay nada que dibujar.",
        "Aucune donnée de rotation pour cet instrument sur cette période. Le nombre "
        "d'actions, et donc la valeur, en est déduit : sans elle, rien à tracer.",
        "Nessun dato di rotazione per questo strumento in quell'intervallo. Il numero di "
        "azioni, e quindi il valore, se ne ricava: senza, non c'è nulla da disegnare.",
        "Brak danych o rotacji dla tego instrumentu w tym zakresie. Z nich wylicza się "
        "liczbę akcji, a więc i wartość — bez nich nie ma czego rysować.",
        "Não há dado de giro para este instrumento nesse intervalo. A quantidade de ações, "
        "e portanto o valor, vem dele; sem ele não há o que desenhar.",
        "Pro tento nástroj v tomto rozsahu chybí údaj o obratu. Z něj se počítá počet akcií "
        "a tedy hodnota — bez něj není co kreslit.",
        "Bu aralıkta bu enstrüman için devir verisi yok. Hisse sayısı ve dolayısıyla değer "
        "onunla bulunur; olmadan çizilecek bir şey yok.",
        "Для этого инструмента в этом диапазоне нет данных об оборачиваемости. Из них "
        "восстанавливается число акций, а значит и капитализация — без них рисовать нечего.",
        "この銘柄にはこの期間の売買高回転率のデータがありません。株数、そして時価総額は"
        "そこから求めるため、それがなければ描けるものがありません。",
        "해당 구간에 이 종목의 회전율 데이터가 없습니다. 주식 수와 시가총액은 그것에서 "
        "구하므로, 없으면 그릴 것이 없습니다.",
        "該標的在這個區間沒有換手率數據。股本（以及市值）要由它還原，沒有它就畫不出來。",
        "该标的在这个区间没有换手率数据。股本（以及市值）要由它还原，没有它就画不出来。"]),

    # 三个市场现在都支持，所以这一条只在将来某个市场不支持时才说。写「这个市场」而不是
    # 点名任何一个：曾经点名纽约，理由（换手率只有一位有效数字）后来被实测推翻了。
    ("CapHistoryMarketNone", [
        "This market is not served: its turnover rate will not give up a share count, and "
        "without one there is no value to draw.",
        "Dieser Markt wird nicht bedient: Seine Umsatzrate ergibt keine Aktienzahl, und "
        "ohne sie gibt es keinen Wert zu zeichnen.",
        "Este mercado no está disponible: su tasa de rotación no da un número de acciones, "
        "y sin él no hay valor que dibujar.",
        "Ce marché n'est pas servi : son taux de rotation ne donne pas de nombre d'actions, "
        "et sans lui il n'y a aucune valeur à tracer.",
        "Questo mercato non è servito: il suo tasso di rotazione non restituisce un numero "
        "di azioni, e senza quello non c'è valore da disegnare.",
        "Ten rynek nie jest obsługiwany: jego wskaźnik rotacji nie daje liczby akcji, a bez "
        "niej nie ma wartości do narysowania.",
        "Este mercado não é atendido: sua taxa de giro não fornece uma contagem de ações, e "
        "sem ela não há valor a desenhar.",
        "Tento trh není podporován: jeho míra obratu nedává počet akcií, a bez něj není "
        "žádná hodnota ke kreslení.",
        "Bu piyasa sunulmuyor: devir oranı bir hisse sayısı vermiyor, o olmadan çizilecek "
        "bir değer de yok.",
        "Этот рынок не обслуживается: его оборачиваемость не даёт числа акций, а без него "
        "рисовать нечего.",
        "この市場は対象外です。回転率から株式数が得られず、それがなければ描ける値も"
        "ありません。",
        "이 시장은 지원되지 않습니다. 회전율에서 주식 수를 얻을 수 없고, 그것 없이는 "
        "그릴 값도 없습니다.",
        "目前市場不支援：該市場的換手率換算不出股本，沒有股本就沒有市值可畫。",
        "目前市场不支持：该市场的换手率换算不出股本，没有股本就没有市值可画。"]),

    ("CapHistoryRangeTooLong", [
        "That span is longer than this page can walk: about {0} years is the most one "
        "run of requests reaches.",
        "Dieser Zeitraum ist länger, als diese Seite gehen kann: etwa {0} Jahre sind das "
        "Meiste, was ein Durchlauf erreicht.",
        "Ese rango es más largo de lo que esta página puede recorrer: unos {0} años es lo "
        "máximo que alcanza una tanda de peticiones.",
        "Cette période dépasse ce que cette page peut parcourir : environ {0} ans, c'est le "
        "maximum atteint par une série de requêtes.",
        "Questo intervallo è più lungo di quanto questa pagina possa percorrere: circa "
        "{0} anni è il massimo che una serie di richieste raggiunge.",
        "Ten zakres jest dłuższy, niż ta strona może przejść: około {0} lat to maksimum "
        "jednej serii zapytań.",
        "Esse intervalo é mais longo do que esta página pode percorrer: cerca de {0} anos "
        "é o máximo que uma série de consultas alcança.",
        "Tento rozsah je delší, než kolik tato strana může projít: asi {0} let je maximum "
        "jedné série požadavků.",
        "Bu aralık bu sayfanın yürüyebileceğinden uzun: bir dizi isteğin ulaştığı en fazla "
        "süre yaklaşık {0} yıl.",
        "Этот диапазон длиннее, чем эта страница может пройти: примерно {0} лет — максимум "
        "одной серии запросов.",
        "この期間はこのページが辿れる範囲を超えています。一連のリクエストで届くのは"
        "およそ {0} 年までです。",
        "이 구간은 이 페이지가 탐색할 수 있는 범위를 넘습니다. 한 번의 요청으로 닿는 "
        "범위는 약 {0}년입니다.",
        "這個區間超過了本頁能回溯的長度：一次取數最多約 {0} 年。",
        "这个区间超过了本页能回溯的长度：一次取数最多约 {0} 年。"]),

    # 口径说明，放在选标的的那一栏旁边。这一条说的是「本市场口径」，不是「流通 vs 总」：
    # 换手率的分母是本市场的流通股本，所以这条线本来就不含其它市场的股票。容易被读错的
    # 恰恰是反过来的方向——行情软件那个「总市值」把别的市场的股票按本市场价格折了进来，
    # 拿它当参照才会以为图上少画了什么（工商银行差的三成全是它的 H 股）。
    # `.Text` 后缀：这是 XAML 里一个 `x:Uid`，不是代码里 `Strings.Get` 的裸键。
    ("CapHistoryNote.Text", [
        "Only the shares traded in this market are counted, not the ones this company "
        "lists elsewhere. For a company listed in two places the line therefore sits "
        "below the “total market value” a quote app shows, which prices those other "
        "shares at this market's price too.",
        "Gezählt werden nur die Aktien, die in diesem Markt gehandelt werden — nicht die, "
        "die dieses Unternehmen anderswo notiert hat. Bei doppelter Notierung liegt die "
        "Linie daher unter der „Gesamtmarktkapitalisierung“, die eine Kurs-App zeigt: Dort "
        "werden die anderen Aktien zum Kurs dieses Marktes bewertet.",
        "Solo se cuentan las acciones negociadas en este mercado, no las que la empresa "
        "cotiza en otros. En una empresa con doble cotización la línea queda por debajo "
        "de la «capitalización total» que muestra una app de cotizaciones, que valora "
        "esas otras acciones al precio de este mercado.",
        "Seules les actions négociées sur ce marché sont comptées, pas celles que "
        "l'entreprise cote ailleurs. Pour une société à double cotation, la courbe passe "
        "donc sous la « capitalisation totale » des applications de cotation, qui évalue "
        "ces autres actions au cours de ce marché.",
        "Si contano solo le azioni scambiate in questo mercato, non quelle che la società "
        "quota altrove. Per una società a doppia quotazione la linea resta quindi sotto la "
        "«capitalizzazione totale» mostrata dalle app di quotazioni, che valuta quelle "
        "altre azioni al prezzo di questo mercato.",
        "Liczone są tylko akcje handlowane na tym rynku, nie te, które spółka notuje gdzie "
        "indziej. Przy podwójnym notowaniu linia przebiega więc poniżej „całkowitej "
        "kapitalizacji“, którą pokazuje aplikacja z notowaniami i która wycenia tamte "
        "akcje po cenie tego rynku.",
        "Só entram as ações negociadas neste mercado, não as que a empresa lista em "
        "outros. Para uma empresa com dupla listagem a linha fica abaixo do «valor de "
        "mercado total» que um app de cotações mostra, que precifica aquelas outras ações "
        "pelo preço deste mercado.",
        "Počítají se jen akcie obchodované na tomto trhu, ne ty, které firma kotuje jinde. "
        "U firmy kotované ve dvou místech proto linie leží pod „celkovou tržní hodnotou“, "
        "kterou ukazuje aplikace s kurzy a která oceňuje ony další akcie cenou tohoto trhu.",
        "Yalnızca bu piyasada işlem gören hisseler sayılır; şirketin başka yerde "
        "listelediği hisseler sayılmaz. İki yerde listelenen bir şirkette çizgi bu yüzden "
        "bir fiyat uygulamasının gösterdiği «toplam piyasa değeri»nin altında kalır; o "
        "değer, diğer hisseleri de bu piyasanın fiyatıyla hesaplar.",
        "Учитываются только акции, которыми торгуют на этом рынке, а не те, что компания "
        "разместила где-то ещё. У компании с двойным листингом линия поэтому идёт ниже "
        "«общей капитализации», которую показывает котировальное приложение: там те акции "
        "оценивают по цене этого рынка.",
        "ここで数えるのはこの市場で取引される株式だけで、この会社が別の市場に上場して"
        "いる株式は含みません。二重上場の会社では、その線は相場アプリが示す『総時価"
        "総額』より下になります——あちらは別市場の株式もこの市場の価格で換算している"
        "からです。",
        "이 시장에서 거래되는 주식만 셉니다. 회사가 다른 시장에 상장한 주식은 포함하지 "
        "않습니다. 이중 상장 기업이라면 이 선은 시세 앱이 보여주는 '총 시가총액'보다 "
        "낮게 나옵니다. 그 값은 다른 시장의 주식까지 이 시장 가격으로 환산하기 때문입니다.",
        "這裡只算本市場可交易的股票，不含這家公司在其它市場的股票。兩地上市公司的圖上值"
        "因此會低於行情軟體的「總市值」——後者把其它市場的股票也按本市場價格折了進來。",
        "这里只算本市场可交易的股票，不含这家公司在其它市场的股票。两地上市公司的图上值"
        "因此会低于行情软件的「总市值」——后者把其它市场的股票也按本市场价格折了进来。"]),

    # 极值标注带上数值。共享的 StockHigh/LowLabel 是纯文字（K 线与成交量那一页把数值
    # 单独写在旁边），而这一页十年的市值曲线里，最低点离底边只有几个像素——只有一个
    # 圆点和「最低」两个字，会被读成「市值一度归零」。所以这两个键是本页自己的。
    ("CapHistoryHighMark", [
        "High {0}", "Hoch {0}", "Máximo {0}", "Haut {0}", "Massimo {0}", "Maksimum {0}",
        "Máximo {0}", "Maximum {0}", "En yüksek {0}", "Максимум {0}", "最高 {0}",
        "최고 {0}", "最高 {0}", "最高 {0}"]),

    ("CapHistoryLowMark", [
        "Low {0}", "Tief {0}", "Mínimo {0}", "Bas {0}", "Minimo {0}", "Minimum {0}",
        "Mínimo {0}", "Minimum {0}", "En düşük {0}", "Минимум {0}", "最低 {0}",
        "최저 {0}", "最低 {0}", "最低 {0}"]),

    # 两个共享档位：这一页的跨度以年计，既有档位最长只有两年。
    ("StudioRange60M", [
        "5 years", "5 Jahre", "5 años", "5 ans", "5 anni", "5 lat", "5 anos",
        "5 let", "5 yıl", "5 лет", "5 年", "5년", "5 年", "5 年"]),

    ("StudioRange120M", [
        "10 years", "10 Jahre", "10 años", "10 ans", "10 anni", "10 lat", "10 anos",
        "10 let", "10 yıl", "10 лет", "10 年", "10년", "10 年", "10 年"]),
]


def entry(key, value):
    """One resw row, XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224: root node not found`
    — naming the root element and the project file, and saying nothing about the text
    that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        at = LANGS.index(tag)
        lines = []

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[at]))

        # Idempotent: drop a key of the same base name wherever it already sits, then
        # append. The optional suffix is matched so that renaming a key from `X` to
        # `X.Text` does not leave the old one behind, and `[^>]*` follows the name
        # because this file holds two entry shapes — the single-line one a machine
        # wrote, and a hand-edited `<data name="K" xml:space="preserve">` with the
        # value on the next line. Insisting on `">` matches only the first.
        for key, _ in PAGE:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        mark = text.rfind("</root>")
        assert mark > 0, f"{tag}: no </root>"

        text = text[:mark] + "".join(lines) + text[mark:]

        # Bytes, not text: read_text/write_text would normalise the line endings and
        # git would see the whole file rewritten.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
