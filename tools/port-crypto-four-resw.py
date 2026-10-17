# -*- coding: utf-8 -*-
r"""把「做这四个」里四个新加密页面的字符串注入 14 份 Resources.resw。

四个页面（都在加密市场下，跟着既有的加密键走，不另起一套措辞）：

  * CryptoCompare  —— 币种归一化对比（归一化价格赛跑）
  * CryptoMovers   —— 24h 涨跌榜（按涨跌幅排序的赛跑）
  * CryptoDominance—— 市值占比（按 Amount 赛跑，占比加起来为一百）
  * CryptoAnnual   —— 年度收益热力（MatrixSpec，币种×年份）

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配（见 port-crypto-market-resw.py
的同一套做法），所以每行给**完整键名**（`Foo.Text` / `Foo.Content` / 裸键），删的时候只动自己那条。

用法：python tools\port-crypto-four-resw.py
"""

import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]


def E(values):
    """14 个值，按 LANGS 顺序。顺序错了这里就断言挂掉。"""
    assert len(values) == len(LANGS), f"{len(values)} values, expected {len(LANGS)}"
    return values


# 顺序：en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans
ROWS = [
    # ---- 页面 A：CryptoCompare ----------------------------------------------
    ("CryptoComparePageTitle.Text", E([
        "Crypto Compare",
        "Krypto-Vergleich",
        "Comparar cripto",
        "Comparaison crypto",
        "Confronto crypto",
        "Porównanie krypto",
        "Comparar cripto",
        "Srovnání krypto",
        "Kripto Karşılaştırma",
        "Сравнение крипто",
        "暗号資産の比較",
        "암호화폐 비교",
        "加密貨幣比較",
        "加密货币比较",
    ])),
    ("CryptoComparePageSubtitle.Text", E([
        "Several coins' prices, each rebased to 100 on the first shared day, raced as cumulative returns. A line climbing fastest is the coin whose price grew most from the same start.",
        "Die Preise mehrerer Coins, je auf 100 am ersten gemeinsamen Tag umgerechnet, als laufende Renditen im Rennen. Die steilste Linie ist der Coin, dessen Preis vom selben Start am stärksten stieg.",
        "Los precios de varias monedas, cada uno rebasado a 100 el primer día común, en carrera como rendimientos acumulados. La línea que sube más rápido es la moneda cuyo precio creció más desde el mismo inicio.",
        "Les prix de plusieurs cryptos, chacun replié à 100 le premier jour commun, courus en rendements cumulés. La ligne qui monte le plus vite est la crypto dont le prix a le plus progressé depuis le même départ.",
        "I prezzi di diverse monete, ciascuno ricalcolato a 100 al primo giorno comune, in corsa come rendimenti cumulati. La linea che sale più velocemente è la moneta il cui prezzo è cresciuto di più dalla stessa partenza.",
        "Ceny kilku coinów, każda przeliczona na 100 w pierwszym wspólnym dniu, ścigane jako skumulowane stopy zwrotu. Najszybciej rosnąca linia to coin, którego cena wzrosła najbardziej od tego samego startu.",
        "Os preços de várias moedas, cada um rebaseado para 100 no primeiro dia comum, disputados como retornos acumulados. A linha que sobe mais rápido é a moeda cujo preço mais cresceu desde o mesmo início.",
        "Ceny několika coinů, každá přepočítaná na 100 v prvním společném dni, v závodě kumulovaných výnosů. Nejrychleji stoupající čára je coin, jehož cena od stejného startu nejvíc vzrostla.",
        "Birkaç coinin fiyatı, her biri ilk ortak günde 100'e endekslenerek kümülatif getiriler olarak yarışır. En hızlı çıkan çizgi, fiyatı aynı başlangıçtan en çok yükselen coindir.",
        "Цены нескольких монет, каждая пересчитанная в 100 в первый общий день, соревнуются как кумулятивная доходность. Быстрее всего растёт линия монеты, чья цена выросла больше всего с одного старта.",
        "複数のコインの価格を、共通の最初の日にそれぞれ100に基準化し、累積収益率のレースにします。最も急上昇する線は、同じ起点から価格が最も伸びたコインです。",
        "여러 코인의 가격을 공통된 첫날을 100으로 환산해 누적 수익률로 경주시킵니다. 가장 가파르게 오르는 선은 같은 출발점에서 가격이 가장 많이 오른 코인입니다.",
        "把多個幣的價格都在第一個共同交易日重設為 100，再以累積報酬率賽跑。爬升最快的那條線，就是從同一個起點漲最多的幣。",
        "把多个币的价格都在第一个共同交易日重设为 100，再以累积报酬率赛跑。爬升最快的那条线，就是从同一个起点涨最多的币。",
    ])),
    ("CryptoCompareNote.Text", E([
        "Each coin starts at 100 on the first day every chosen coin has a price; the bars show whose price grew fastest from that line. Daily prices in US dollars from a public source.",
        "Jeder Coin startet bei 100 am ersten Tag, an dem jeder gewählte Coin einen Preis hat; die Balken zeigen, wessen Preis von dieser Linie am schnellsten wuchs. Tagespreise in US-Dollar aus einer öffentlichen Quelle.",
        "Cada moneda empieza en 100 el primer día en que todas las monedas elegidas tienen precio; las barras muestran qué precio creció más rápido desde esa línea. Precios diarios en dólares de una fuente pública.",
        "Chaque crypto démarre à 100 le premier jour où chaque coin choisi a un prix ; les barres montrent quel prix a le plus vite progressé depuis cette ligne. Prix journaliers en dollars US d'une source publique.",
        "Ogni moneta parte da 100 il primo giorno in cui ogni coin scelto ha un prezzo; le barre mostrano quale prezzo è cresciuto più velocemente da quella linea. Prezzi giornalieri in dollari USA da una fonte pubblica.",
        "Każdy coin startuje od 100 w pierwszym dniu, w którym każdy wybrany coin ma cenę; słupki pokazują, czyj cena urosła najszybciej od tej linii. Ceny dzienne w dolarach z publicznego źródła.",
        "Cada moeda começa em 100 no primeiro dia em que todas as moedas escolhidas têm preço; as barras mostram de quem o preço cresceu mais rápido a partir dessa linha. Preços diários em dólar de uma fonte pública.",
        "Každý coin začíná na 100 v prvním dni, kdy má každý zvolený coin cenu; sloupce ukazují, čí cena od této linie nejvíce vzrostla. Denní ceny v dolarech z veřejného zdroje.",
        "Her coin, seçili tüm coinlerin fiyatı olan ilk günde 100'den başlar; çubuklar hangi fiyatın bu çizgiden en hızlı yükseldiğini gösterir. Günlük fiyatlar ABD doları cinsinden, herkese açık bir kaynaktan.",
        "Каждая монета начинается со 100 в первый день, когда у всех выбранных монет есть цена; столбцы показывают, чья цена выросла быстрее всего от этой линии. Дневные цены в долларах США из открытого источника.",
        "各コインは、選んだコイン全てに価格がある最初の日に100から始まります。棒はその基準線から価格が最も速く伸びたコインを示します。日次価格は米ドル建てで公開ソース由来。",
        "각 코인은 선택한 코인 모두에 가격이 있는 첫날을 100으로 시작하며, 막대는 그 기준선에서 가격이 가장 빨리 오른 코인을 보여줍니다. 일별 가격은 공개 소스의 미 달러 기준입니다.",
        "每個幣都從「所有選中幣都有價格的第一天」起算為 100；長條顯示從那條基準線起，誰的價格漲得最快。日價格取自公開來源，以美元計。",
        "每个币都从「所有选中币都有价格的第一天」起算为 100；长条显示从那条基准线起，谁的价格涨得最快。日价格取自公开来源，以美元计。",
    ])),
    ("CryptoCompareFetched", E([
        "Got {0} coins · {1} days ({2} to {3}), leading at the end: {4}.",
        "{0} Coins · {1} Tage ({2} bis {3}), am Ende führend: {4}.",
        "{0} monedas · {1} días ({2} a {3}), líder al final: {4}.",
        "{0} cryptos · {1} jours ({2} à {3}), en tête à la fin : {4}.",
        "{0} monete · {1} giorni ({2} a {3}), in testa alla fine: {4}.",
        "{0} coinów · {1} dni ({2} do {3}), na końcu prowadzi: {4}.",
        "{0} moedas · {1} dias ({2} a {3}), líder ao final: {4}.",
        "{0} coinů · {1} dní ({2} až {3}), v čele na konci: {4}.",
        "{0} coin · {1} gün ({2}–{3}), sonunda önde: {4}.",
        "{0} монет · {1} дней ({2}–{3}), впереди в конце: {4}.",
        "{0} コイン · {1} 日 ({2}～{3})、最終的に首位: {4}。",
        "{0} 코인 · {1}일 ({2}~{3}), 마지막에 선두: {4}.",
        "取得 {0} 個幣 · {1} 天（{2} 至 {3}），最後領先：{4}。",
        "取得 {0} 个币 · {1} 天（{2} 至 {3}），最后领先：{4}。",
    ])),

    # ---- 页面 B：CryptoMovers -----------------------------------------------
    ("CryptoMoversPageTitle.Text", E([
        "Crypto Movers",
        "Krypto-Bewegungen",
        "Movimientos cripto",
        "Mouvements crypto",
        "Movimenti crypto",
        "Ruchy krypto",
        "Movimentos cripto",
        "Krypto pohyby",
        "Kripto Hareketler",
        "Движения крипто",
        "暗号資産の値動き",
        "암호화폐 등락",
        "加密貨幣漲跌",
        "加密货币涨跌",
    ])),
    ("CryptoMoversPageSubtitle.Text", E([
        "The biggest 24-hour moves, day by day. When the live ranking is not reachable, each coin's move is its daily close over the previous day's from a public source — a proxy for the 24-hour change, named by the note.",
        "Die größten 24-Stunden-Bewegungen, Tag für Tag. Ist das Live-Ranking nicht erreichbar, ist die Bewegung eines Coins sein Tageschluss gegen den Vortag aus einer öffentlichen Quelle — ein Proxy für die 24-Stunden-Änderung, benannt in der Notiz.",
        "Los mayores movimientos de 24 horas, día a día. Cuando el ranking en vivo no es accesible, el movimiento de cada moneda es su cierre diario frente al del día anterior de una fuente pública — un proxy del cambio de 24 horas, que nombra la nota.",
        "Les plus grands mouvements sur 24 heures, jour après jour. Quand le classement en direct n'est pas joignable, le mouvement d'une crypto est sa clôture quotidienne face à la veille, d'une source publique — un proxy du changement sur 24 heures, nommé dans la note.",
        "I maggiori movimenti su 24 ore, giorno per giorno. Quando la classifica in diretta non è raggiungibile, il movimento di una moneta è la sua chiusura giornaliera rispetto al giorno precedente da una fonte pubblica — un proxy del cambiamento su 24 ore, indicato nella nota.",
        "Największe ruchy w ciągu 24 godzin, dzień po dniu. Gdy ranking na żywo jest niedostępny, ruchem coina jest jego zamknięcie dzienne wobec poprzedniego dnia z publicznego źródła — proxy zmiany 24-godzinnej, opisane w nocie.",
        "Os maiores movimentos de 24 horas, dia a dia. Quando o ranking ao vivo não está acessível, o movimento de cada moeda é seu fechamento diário contra o dia anterior de uma fonte pública — um proxy para a mudança de 24 horas, citado na nota.",
        "Největší 24hodinové pohyby, den po dni. Když živé pořadí není dostupné, je pohybem coinu jeho denní závěr oproti předchozímu dni z veřejného zdroje — proxy pro 24hodinovou změnu, uvedená v poznámce.",
        "En büyük 24 saatlik hareketler, gün gün. Canlı sıralama erişilemediğinde, her coinin hareketi bir kamu kaynağından önceki güne göre günlük kapanışıdır — 24 saatlik değişimin proxy'si, notta belirtilmiştir.",
        "Крупнейшие движения за 24 часа, день за днём. Когда живой рейтинг недоступен, движение монеты — это её дневное закрытие относительно предыдущего дня из открытого источника — замена 24-часовому изменению, названная в примечании.",
        "最大の24時間値動きを日々追います。ライブランキングに届かない場合、各コインの動きは公開ソースの前日比日次終値となり、24時間変化の代用です（注記参照）。",
        "가장 큰 24시간 등락을 날마다 추적합니다. 실시간 순위에 닿지 않으면 각 코인의 움직임은 공개 소스의 전일 대비 일별 종가로, 24시간 변화의 대용값입니다(노트 참조).",
        "逐日追蹤最大的 24 小時漲跌。當即時排行榜連不上時，每個幣的漲跌就取公開來源「相對前一日的每日收盤」，是 24 小時變化的替代值，詳見註記。",
        "逐日追踪最大的 24 小时涨跌。当即时排行榜连不上时，每个币的涨跌就取公开来源「相对前一日的每日收盘」，是 24 小时变化的替代值，详见注记。",
    ])),
    ("CryptoMoversNote.Text", E([
        "Ranked by the size of the move, red for a rise and green for a fall. The live 24-hour board is the natural source and is used when reachable; when it is not, the move is each coin's daily close over the previous day's — a proxy, not the live figure.",
        "Nach Größe der Bewegung geordnet, rot für Anstieg und grün für Fall. Das live 24-Stunden-Board ist die natürliche Quelle und wird genutzt, wenn erreichbar; sonst ist die Bewegung der Tageschluss gegen den Vortag — ein Proxy, nicht die Live-Zahl.",
        "Ordenado por el tamaño del movimiento, rojo para subida y verde para bajada. El tablero en vivo de 24 horas es la fuente natural y se usa cuando es accesible; si no, el movimiento es el cierre diario frente al anterior — un proxy, no la cifra en vivo.",
        "Classé par ampleur du mouvement, rouge pour une hausse et vert pour une baisse. Le classement live sur 24 heures est la source naturelle et est utilisé quand il est joignable ; sinon le mouvement est la clôture quotidienne face à la veille — un proxy, pas le chiffre en direct.",
        "Ordinato per ampiezza del movimento, rosso per un rialzo e verde per un calo. La classifica live su 24 ore è la fonte naturale ed è usata quando raggiungibile; altrimenti il movimento è la chiusura giornaliera rispetto al giorno prima — un proxy, non il dato in diretta.",
        "Uporządkowane według wielkości ruchu, czerwony dla wzrostu, zielony dla spadku. Na żywo tablica 24-godzinna to naturalne źródło i jest używana, gdy dostępna; w przeciwnym razie ruchem jest dzienne zamknięcie wobec poprzedniego dnia — proxy, nie wartość na żywo.",
        "Ordenado pelo tamanho do movimento, vermelho para alta e verde para baixa. O quadro ao vivo de 24 horas é a fonte natural e é usado quando acessível; quando não, o movimento é o fechamento diário contra o dia anterior — um proxy, não o número ao vivo.",
        "Seřazeno podle velikosti pohybu, červená pro růst, zelená pro pokles. Živá 24h tabule je přirozený zdroj a používá se, když je dostupná; jinak je pohybem denní závěr oproti předchozímu dni — proxy, ne živé číslo.",
        "Hareketin büyüklüğüne göre sıralı, yükseliş kırmızı, düşüş yeşil. Canlı 24 saatlik tablo doğal kaynaktır ve erişilebildiğinde kullanılır; erişilemediğinde hareket, bir önceki güne göre günlük kapanıştır — canlı sayı değil, bir proxy.",
        "Упорядочено по величине движения, красный — рост, зелёный — падение. Живая 24-часовая таблица — естественный источник и используется, когда доступна; иначе движение — это дневное закрытие относительно предыдущего дня — замена, не живое число.",
        "動きの大きさ順に並べ、上昇は赤、下落は緑。ライブの24時間ボードが本来のソースで、届くときはそちらを使います。届かないときは前日比の日次終値を動きとし、これは代用値で実数ではありません。",
        "움직임의 크기순으로 정렬하며 상승은 빨강, 하락은 초록입니다. 실시간 24시간 보드가 본래 소스로, 닿을 때는 그것을 씁니다. 닿지 않으면 전일 대비 일별 종가를 움직임으로 삼으며, 이것은 실제값이 아닌 대용값입니다.",
        "依漲跌幅度排序，紅色為漲、綠色為跌。即時 24 小時榜才是本源，連得上時用它；連不上時以「相對前一日的每日收盤」當作漲跌，這是替代值而非即時數字。",
        "依涨跌幅度排序，红色为涨、绿色为跌。即时 24 小时榜才是本源，连得上时用它；连不上时以「相对前一日的每日收盘」当作涨跌，这是替代值而非即时数字。",
    ])),
    ("CryptoMoversFetched", E([
        "Got {0} coins · {1} days ({2} to {3}), biggest move at the end: {4}.",
        "{0} Coins · {1} Tage ({2} bis {3}), größte Bewegung am Ende: {4}.",
        "{0} monedas · {1} días ({2} a {3}), mayor movimiento al final: {4}.",
        "{0} cryptos · {1} jours ({2} à {3}), plus grand mouvement à la fin : {4}.",
        "{0} monete · {1} giorni ({2} a {3}), movimento più grande alla fine: {4}.",
        "{0} coinów · {1} dni ({2} do {3}), największy ruch na końcu: {4}.",
        "{0} moedas · {1} dias ({2} a {3}), maior movimento ao final: {4}.",
        "{0} coinů · {1} dní ({2} až {3}), největší pohyb na konci: {4}.",
        "{0} coin · {1} gün ({2}–{3}), sonunda en büyük hareket: {4}.",
        "{0} монет · {1} дней ({2}–{3}), самое большое движение в конце: {4}.",
        "{0} コイン · {1} 日 ({2}～{3})、最終的に最大の動き: {4}。",
        "{0} 코인 · {1}일 ({2}~{3}), 마지막에 가장 큰 움직임: {4}.",
        "取得 {0} 個幣 · {1} 天（{2} 至 {3}），最後最大漲跌：{4}。",
        "取得 {0} 个币 · {1} 天（{2} 至 {3}），最后最大涨跌：{4}。",
    ])),

    # ---- 页面 C：CryptoDominance --------------------------------------------
    ("CryptoDominancePageTitle.Text", E([
        "Crypto Dominance",
        "Krypto-Dominanz",
        "Dominancia cripto",
        "Dominance crypto",
        "Dominanza crypto",
        "Dominacja krypto",
        "Dominância cripto",
        "Krypto dominance",
        "Kripto Hakimiyeti",
        "Доминирование крипто",
        "暗号資産の占有率",
        "암호화폐 점유율",
        "加密貨幣佔比",
        "加密货币占比",
    ])),
    ("CryptoDominancePageSubtitle.Text", E([
        "Each chosen coin's share of the chosen set's total market cap, day by day. The shares sum to one hundred across the coins on the frame — a slice of the whole market, read within the set you picked.",
        "Der Anteil jedes gewählten Coins an der Gesamtmarktkapitalisierung des gewählten Sets, Tag für Tag. Die Anteile ergeben über die Coins im Bild hundert — ein Stück des Gesamtmarkts, gelesen innerhalb der gewählten Menge.",
        "La cuota de cada moneda elegida sobre la capitalización total del conjunto elegido, día a día. Las cuotas suman cien entre las monedas del marco — una porción del mercado total, leída dentro del conjunto que escogiste.",
        "La part de chaque crypto choisie dans la capitalisation totale de l'ensemble choisi, jour après jour. Les parts font cent au total sur les cryptos du cadre — une tranche du marché entier, lue dans le groupe que vous avez pris.",
        "La quota di ogni moneta scelta sul cap totale dell'insieme scelto, giorno per giorno. Le quote sommano a cento tra le monete nel quadro — una fetta dell'intero mercato, letta dentro l'insieme scelto.",
        "Udział każdego wybranego coina w całkowitej kapitalizacji wybranego zestawu, dzień po dniu. Udziały sumują się do stu wśród coinów na ramce — kawałek całego rynku, czytany w ramach wybranego zestawu.",
        "A fatia de cada moeda escolhida sobre a capitalização total do conjunto escolhido, dia a dia. As fatias somam cem entre as moedas do quadro — uma porção de todo o mercado, lida dentro do conjunto que você escolheu.",
        "Podíl každého zvoleného coinu na celkové tržní kapitalizaci zvolené sady, den po dni. Podíly se mezi coiny na snímku sčítají na sto — dílek celého trhu, čtený v rámci vybrané sady.",
        "Her seçili coinin, seçili setin toplam piyasa değerindeki payı, gün gün. Paylar çerçevedeki coinler arasında yüze tamamlanır — bütün piyasanın bir dilimi, seçtiğiniz set içinde okunur.",
        "Доля каждой выбранной монеты в суммарной капитализации выбранного набора, день за днём. Доли по монетам на экране в сумме дают сто — кусок всего рынка, читаемый внутри выбранного набора.",
        "選んだ各コインの、選んだセット全体の時価総額に占める割合を日々表示します。画面内のコインの割合は合計100になります——市場全体の一片を、選んだセットの中で読みます。",
        "선택한 각 코인이 선택한 세트 전체 시가총액에서 차지하는 비중을 날마다 보여줍니다. 화면의 코인 비중은 합쳐 100이 됩니다—시장 전체의 한 조각을, 선택한 세트 안에서 읽습니다.",
        "逐日顯示每個選中幣在「所選集合總市值」裡的佔比。畫面中這幾個幣的佔比加總為 100——是整個市場的一塊，在你挑的那組裡讀。",
        "逐日显示每个选中币在「所选集合总市值」里的占比。画面中这几个币的占比加总为 100——是整个市场的一块，在你挑的那组里读。",
    ])),
    ("CryptoDominanceNote.Text", E([
        "The share is of the coins you picked, not of the entire market — a total the source serves per coin but not as one figure — so the bars sum to one hundred across the chosen coins. Circulating caps in US dollars from a public source.",
        "Der Anteil bezieht sich auf die von dir gewählten Coins, nicht auf den gesamten Markt — eine Summe, die die Quelle pro Coin liefert, aber nicht als eine Zahl. Daher ergeben die Balken über die gewählten Coins hundert. Umlaufende Kaps in US-Dollar aus einer öffentlichen Quelle.",
        "La cuota es de las monedas que elegiste, no de todo el mercado — un total que la fuente da por moneda pero no como una cifra única — así que las barras suman cien entre las monedas elegidas. Caps en circulación en dólares de una fuente pública.",
        "La part porte sur les cryptos que vous avez choisies, pas sur tout le marché — un total que la source fournit par crypto mais pas en un seul chiffre — donc les barres font cent au total sur les cryptos choisies. Caps en circulation en dollars US d'une source publique.",
        "La quota riguarda le monete che hai scelto, non l'intero mercato — un totale che la fonte dà per moneta ma non come una sola cifra — perciò le barre sommano a cento tra le monete scelte. Cap in circolazione in dollari USA da una fonte pubblica.",
        "Udział dotyczy wybranych przez ciebie coinów, nie całego rynku — sumy, którą źródło podaje na coin, ale nie jako jedną liczbę — więc słupki sumują się do stu wśród wybranych coinów. Kapitalizacja w obiegu w dolarach z publicznego źródła.",
        "A fatia é das moedas que você escolheu, não de todo o mercado — um total que a fonte fornece por moeda, mas não como um número único — portanto as barras somam cem entre as moedas escolhidas. Caps em circulação em dólar de uma fonte pública.",
        "Podíl se vztahuje k coinům, které jste vybrali, ne k celému trhu — součet, který zdroj uvádí pro každý coin, ale ne jako jedno číslo — sloupce se proto mezi vybranými coiny sčítají na sto. V oběhu dostupná kapitalizace v dolarech z veřejného zdroje.",
        "Pay, seçtiğiniz coinlere aittir, tüm piyasaya değil — kaynağın coin başına verdiği ama tek bir sayı olarak vermediği bir toplam — bu yüzden çubuklar seçili coinler arasında yüze tamamlanır. Dolaşımdaki değerler ABD doları cinsinden, herkese açık bir kaynaktan.",
        "Доля относится к выбранным вами монетам, а не ко всему рынку — сумма, которую источник даёт по монете, но не как одно число — поэтому столбцы по выбранным монетам в сумме дают сто. Капитализация в обращении в долларах США из открытого источника.",
        "占有率は選んだコイン群に対するもので、市場全体に対するものではありません——ソースが各コインごとに出すものの、一つの数字としては出しません——そのため棒は選んだコイン間で合計100になります。循環時価総額は米ドル建てで公開ソース由来。",
        "비중은 선택한 코인들에 대한 것이지 전체 시장에 대한 것이 아닙니다—소스가 코인별로 주되 하나의 숫자로는 주지 않는 합계라—막대는 선택한 코인들 사이에서 합쳐 100이 됩니다. 유통 시가총액은 미 달러 기준 공개 소스입니다.",
        "佔比是對「你挑的那組幣」而言，不是對整個市場——來源只給每個幣各自的數字，不給一個總額——所以長條在所選幣之間加總為 100。流通市值取自公開來源，以美元計。",
        "占比是对「你挑的那组币」而言，不是对整个市场——来源只给每个币各自的数字，不给一个总额——所以长条在所选币之间加总为 100。流通市值取自公开来源，以美元计。",
    ])),
    ("CryptoDominanceFetched", E([
        "Got {0} coins · {1} days ({2} to {3}), largest share at the end: {4}.",
        "{0} Coins · {1} Tage ({2} bis {3}), größter Anteil am Ende: {4}.",
        "{0} monedas · {1} días ({2} a {3}), mayor cuota al final: {4}.",
        "{0} cryptos · {1} jours ({2} à {3}), plus grande part à la fin : {4}.",
        "{0} monete · {1} giorni ({2} a {3}), quota maggiore alla fine: {4}.",
        "{0} coinów · {1} dni ({2} do {3}), największy udział na końcu: {4}.",
        "{0} moedas · {1} dias ({2} a {3}), maior fatia ao final: {4}.",
        "{0} coinů · {1} dní ({2} až {3}), největší podíl na konci: {4}.",
        "{0} coin · {1} gün ({2}–{3}), sonunda en büyük pay: {4}.",
        "{0} монет · {1} дней ({2}–{3}), самая большая доля в конце: {4}.",
        "{0} コイン · {1} 日 ({2}～{3})、最終的に最大の占有率: {4}。",
        "{0} 코인 · {1}일 ({2}~{3}), 마지막에 가장 큰 비중: {4}.",
        "取得 {0} 個幣 · {1} 天（{2} 至 {3}），最後最大佔比：{4}。",
        "取得 {0} 个币 · {1} 天（{2} 至 {3}），最后最大占比：{4}。",
    ])),

    # ---- 页面 D：CryptoAnnual（矩阵）----------------------------------------
    ("CryptoAnnualPageTitle.Text", E([
        "Crypto Annual Returns",
        "Krypto-Jahresrenditen",
        "Rendimientos anuales cripto",
        "Rendements annuels crypto",
        "Rendimenti annuali crypto",
        "Roczne stopy krypto",
        "Retornos anuais cripto",
        "Roční výnosy krypto",
        "Kripto Yıllık Getiriler",
        "Годовые доходности крипто",
        "暗号資産の年間収益",
        "암호화폐 연간 수익",
        "加密貨幣年度報酬",
        "加密货币年度回报",
    ])),
    ("CryptoAnnualPageSubtitle.Text", E([
        "Coins as rows, calendar years as columns, each cell a coin's return over that year, red for a rise and green for a fall. The still-walking year is left off, because a half year read as a whole one is a lie about the size of the move.",
        "Coins als Zeilen, Kalenderjahre als Spalten, jede Zelle eine Jahresrendite des Coins, rot für Anstieg und grün für Fall. Das laufende Jahr bleibt weg, denn ein halbes Jahr als ganzes gelesen lügt über die Größe der Bewegung.",
        "Monedas en filas, años del calendario en columnas, cada celda el rendimiento de una moneda en ese año, rojo para subida y verde para bajada. El año en curso se omite, porque un medio año leído como entero miente sobre el tamaño del movimiento.",
        "Les cryptos en lignes, les années civiles en colonnes, chaque cellule le rendement d'une crypto sur cette année, rouge pour une hausse et vert pour une baisse. L'année en cours est omise, car un demi-année lue comme entière ment sur la taille du mouvement.",
        "Monete come righe, anni calendariali come colonne, ogni cella il rendimento di una moneta su quell'anno, rosso per rialzo e verde per calo. L'anno in corso è lasciato fuori, perché un mezzo anno letto come intero mente sulla dimensione del movimento.",
        "Coiny w wierszach, lata kalendarzowe w kolumnach, każda komórka to roczna stopa coina, czerwony dla wzrostu, zielony dla spadku. Trwający rok jest pomijany, bo pół roku czytane jako cały kłamie o wielkości ruchu.",
        "Moedas em linhas, anos do calendário em colunas, cada célula o retorno de uma moeda naquele ano, vermelho para alta e verde para baixa. O ano em andamento é deixado de fora, porque meio ano lido como um ano inteiro mente sobre o tamanho do movimento.",
        "Coiny jako řádky, kalendářní roky jako sloupce, každá buňka je roční výnos coinu, červená pro růst, zelená pro pokles. Probíhající rok se vynechává, protože půl roku čtený jako celý lže o velikosti pohybu.",
        "Satırlarda coinler, sütunlarda takvim yılları, her hücre bir coinin o yıldaki getirisi, yükseliş kırmızı, düşüş yeşil. Yürümekte olan yıl çıkarılır, çünkü yarı yılın bütün bir yıl gibi okunması hareketin büyüklüğü konusunda yalan söyler.",
        "Монеты — строки, календарные годы — столбцы, каждая ячейка — годовая доходность монеты, красный — рост, зелёный — падение. Идущий год не показывается, потому что полгода, прочитанные как целый год, лгут о величине движения.",
        "行がコイン、列が暦年。各セルはそのコインの年間収益で、上昇は赤、下落は緑。進行中の年は除外します。半年を丸一年として読むのは、動きの大きさについての嘘だからです。",
        "행은 코인, 열은 역년입니다. 각 칸은 해당 코인의 연간 수익으로 상승은 빨강, 하락은 초록입니다. 진행 중인 해는 제외합니다. 반년을 온전한 1년으로 읽는 것은 움직임의 크기에 대한 거짓이기 때문입니다.",
        "行是幣、列是曆年，每格是該幣那一年的報酬，紅色為漲、綠色為跌。正在走的這一年不列入，因為把半年當整年讀，是對漲跌幅度的一種謊報。",
        "行是币、列是历年，每格是该币那一年的回报，红色为涨、绿色为跌。正在走的这一年不列入，因为把半年当整年读，是对涨跌幅度的一种谎报。",
    ])),
    ("CryptoAnnualNote.Text", E([
        "Each year's return is the price at its close against the prior year's close. The summary column compounds every shown year into one figure. The current year is not on the grid until it has closed.",
        "Die Rendite eines Jahres ist der Preis am Jahresende gegen den des Vorjahres. Die Zusammenfassungsspalte verrechnet jedes gezeigte Jahr zu einer Zahl. Das laufende Jahr steht nicht im Raster, bis es geschlossen ist.",
        "El rendimiento de un año es el precio a su cierre frente al del año anterior. La columna de resumen compone cada año mostrado en una cifra. El año actual no está en la cuadrícula hasta que cierra.",
        "Le rendement d'une année est le prix à sa clôture face à celui de l'année précédente. La colonne de résumé compose chaque année montrée en un seul chiffre. L'année en cours n'est pas dans la grille tant qu'elle n'est pas close.",
        "Il rendimento di un anno è il prezzo alla sua chiusura rispetto a quello dell'anno precedente. La colonna di riepilogo compone ogni anno mostrato in un'unica cifra. L'anno in corso non è nella griglia finché non è chiuso.",
        "Rendiment roku to cena na jego zamknięciu wobec zamknięcia poprzedniego roku. Kolumna podsumowania zestawia każdy pokazany rok w jedną liczbę. Bieżący rok nie jest w siatce, dopóki się nie zamknie.",
        "O retorno de um ano é o preço no fechamento contra o fechamento do ano anterior. A coluna de resumo composta cada ano mostrado em um número. O ano atual não está na grade até fechar.",
        "Výnos roku je cena při jeho závěru proti závěru předchozího roku. Souhrnný sloupec složí každý zobrazený rok do jednoho čísla. Aktuální rok není v mřížce, dokud se neuzavře.",
        "Bir yılın getirisi, kapanışındaki fiyatın bir önceki yılın kapanışına göre oranıdır. Özet sütunu gösterilen her yılı tek bir sayıda bileştirir. Güncel yıl, kapanana kadar ızgarada yer almaz.",
        "Доходность года — это цена на его закрытии относительно закрытия предыдущего года. Сводный столбец сводит каждый показанный год в одну цифру. Текущий год не на сетке, пока не закроется.",
        "ある年の収益は、その年末の価格を前年末の価格に対して比べたものです。まとめ列は表示された各年を一つの数値に複利で合算します。現在の年は終わるまでグリッドに乗りません。",
        "한 해의 수익은 그 해 종가를 전년 종가에 대비한 것입니다. 요약 열은 표시된 각 해를 하나의 수치로 복리 합산합니다. 현재 연도는 마감될 때까지 격자에 들어가지 않습니다.",
        "某一年的報酬，是該年年底收盤價相對前一年年底收盤價。摘要欄把顯示的每一年複利合併成一個數字。本年度要等收盤後才會進格子。",
        "某一年的回报，是该年年底收盘价相对前一年年底收盘价。摘要栏把显示的每一年复利合并成一个数字。本年度要等收盘后才会进格子。",
    ])),

    # ---- 载入/矩阵内部键（非页面专属，但这次才用到）-------------------------
    ("CryptoPriceNoData", E([
        "No price data came back for that span.",
        "Für diesen Zeitraum kamen keine Preisdaten zurück.",
        "No se recibieron datos de precios para ese periodo.",
        "Aucune donnée de prix n'est revenue pour cette période.",
        "Nessun dato di prezzo è tornato per quel periodo.",
        "Dla tego zakresu nie wróciły żadne dane o cenach.",
        "Nenhum dado de preço voltou para esse período.",
        "Pro toto období se nevrátila žádná cenová data.",
        "Bu aralık için fiyat verisi gelmedi.",
        "За этот период не вернулись данные о ценах.",
        "その期間の価格データは返ってきませんでした。",
        "해당 기간의 가격 데이터가 돌아오지 않았습니다.",
        "該時間範圍沒有傳回任何價格資料。",
        "该时间范围没有返回任何价格数据。",
    ])),
    ("CryptoPriceTooFewDays", E([
        "Not enough price history in this span.",
        "Nicht genug Preishistorie in diesem Zeitraum.",
        "No hay suficiente historial de precios en este periodo.",
        "Pas assez d'historique de prix sur cette période.",
        "Storico dei prezzi insufficiente per questo periodo.",
        "Za mało historii cen w tym zakresie.",
        "Histórico de preços insuficiente neste período.",
        "V tomto období je málo cenové historie.",
        "Bu aralıkta yeterli fiyat geçmişi yok.",
        "В этом диапазоне недостаточно истории цен.",
        "この期間の価格履歴が不十分です。",
        "이 기간의 가격 기록이 부족합니다.",
        "此時間範圍的價格歷史不足。",
        "此时间范围的价格历史不足。",
    ])),
    ("CryptoAnnualTooFewYears", E([
        "Not enough full years in this span.",
        "Nicht genug volle Jahre in diesem Zeitraum.",
        "No hay suficientes años completos en este periodo.",
        "Pas assez d'années complètes sur cette période.",
        "Non abbastanza anni interi in questo periodo.",
        "Za mało pełnych lat w tym zakresie.",
        "Anos completos insuficientes neste período.",
        "V tomto období je málo celých let.",
        "Bu aralıkta yeterli tam yıl yok.",
        "В этом диапазоне недостаточно полных лет.",
        "この期間の満了年が不十分です。",
        "이 기간의 온전한 연도가 부족합니다.",
        "此時間範圍的完整年度不足。",
        "此时间范围的完整年度不足。",
    ])),
    ("CryptoAnnualTail", E([
        "Combined",
        "Kombiniert",
        "Combinado",
        "Combiné",
        "Combinato",
        "Łącznie",
        "Combinado",
        "Celkem",
        "Bileşik",
        "Совокупно",
        "合算",
        "복합",
        "合計",
        "合计",
    ])),
    ("CryptoAnnualSpan", E([
        "{0}–{1} · {2} years",
        "{0}–{1} · {2} Jahre",
        "{0}–{1} · {2} años",
        "{0}–{1} · {2} ans",
        "{0}–{1} · {2} anni",
        "{0}–{1} · {2} lat",
        "{0}–{1} · {2} anos",
        "{0}–{1} · {2} let",
        "{0}–{1} · {2} yıl",
        "{0}–{1} · {2} лет",
        "{0}–{1} · {2}年",
        "{0}–{1} · {2}년",
        "{0}–{1} · {2} 年",
        "{0}–{1} · {2} 年",
    ])),
    ("CryptoAnnualTitle", E([
        "Crypto annual returns {0}–{1}",
        "Krypto-Jahresrenditen {0}–{1}",
        "Rendimientos anuales cripto {0}–{1}",
        "Rendements annuels crypto {0}–{1}",
        "Rendimenti annuali crypto {0}–{1}",
        "Roczne stopy krypto {0}–{1}",
        "Retornos anuais cripto {0}–{1}",
        "Roční výnosy krypto {0}–{1}",
        "Kripto yıllık getirileri {0}–{1}",
        "Годовые доходности крипто {0}–{1}",
        "暗号資産の年間収益 {0}–{1}",
        "암호화폐 연간 수익 {0}–{1}",
        "加密貨幣年度報酬 {0}–{1}",
        "加密货币年度回报 {0}–{1}",
    ])),
    ("CryptoAnnualSubtitle", E([
        "{0} years",
        "{0} Jahre",
        "{0} años",
        "{0} ans",
        "{0} anni",
        "{0} lat",
        "{0} anos",
        "{0} let",
        "{0} yıl",
        "{0} лет",
        "{0}年",
        "{0}년",
        "{0} 年",
        "{0} 年",
    ])),
    ("CryptoAnnualStatBest", E([
        "Best",
        "Beste",
        "Mejor",
        "Meilleure",
        "Migliore",
        "Najlepsza",
        "Melhor",
        "Nejlepší",
        "En iyi",
        "Лучшая",
        "最高",
        "최고",
        "最佳",
        "最佳",
    ])),
    ("CryptoAnnualStatWorst", E([
        "Worst",
        "Schlechteste",
        "Peor",
        "Pire",
        "Peggiore",
        "Najgorsza",
        "Pior",
        "Nejhorší",
        "En kötü",
        "Худшая",
        "最悪",
        "최저",
        "最差",
        "最差",
    ])),
    ("CryptoAnnualStatTargets", E([
        "Coins",
        "Coins",
        "Monedas",
        "Cryptos",
        "Monete",
        "Coiny",
        "Moedas",
        "Coiny",
        "Coinler",
        "Монеты",
        "コイン",
        "코인",
        "幣",
        "币",
    ])),
    ("CryptoAnnualStatYears", E([
        "Years",
        "Jahre",
        "Años",
        "Ans",
        "Anni",
        "Lata",
        "Anos",
        "Léta",
        "Yıllar",
        "Годы",
        "年",
        "년",
        "年",
        "年",
    ])),

    # MatrixCountYears 给 CryptoAnnual 的 Stats 用（和 MatrixCountTargets 同形，只给数字）
    ("MatrixCountYears", E([
        "{0}", "{0}", "{0}", "{0}", "{0}", "{0}", "{0}",
        "{0}", "{0}", "{0}", "{0}", "{0}", "{0}", "{0}",
    ])),

    # ---- 导航项 --------------------------------------------------------------
    ("NavCryptoCompare.Content", E([
        "Crypto Compare",
        "Krypto-Vergleich",
        "Comparar cripto",
        "Comparaison crypto",
        "Confronto crypto",
        "Porównanie krypto",
        "Comparar cripto",
        "Srovnání krypto",
        "Kripto Karşılaştırma",
        "Сравнение крипто",
        "暗号資産の比較",
        "암호화폐 비교",
        "加密貨幣比較",
        "加密货币比较",
    ])),
    ("NavCryptoMovers.Content", E([
        "Crypto Movers",
        "Krypto-Bewegungen",
        "Movimientos cripto",
        "Mouvements crypto",
        "Movimenti crypto",
        "Ruchy krypto",
        "Movimentos cripto",
        "Krypto pohyby",
        "Kripto Hareketler",
        "Движения крипто",
        "暗号資産の値動き",
        "암호화폐 등락",
        "加密貨幣漲跌",
        "加密货币涨跌",
    ])),
    ("NavCryptoDominance.Content", E([
        "Crypto Dominance",
        "Krypto-Dominanz",
        "Dominancia cripto",
        "Dominance crypto",
        "Dominanza crypto",
        "Dominacja krypto",
        "Dominância cripto",
        "Krypto dominance",
        "Kripto Hakimiyeti",
        "Доминирование крипто",
        "暗号資産の占有率",
        "암호화폐 점유율",
        "加密貨幣佔比",
        "加密货币占比",
    ])),
    ("NavCryptoAnnual.Content", E([
        "Crypto Annual Returns",
        "Krypto-Jahresrenditen",
        "Rendimientos anuales cripto",
        "Rendements annuels crypto",
        "Rendimenti annuali crypto",
        "Roczne stopy krypto",
        "Retornos anuais cripto",
        "Roční výnosy krypto",
        "Kripto Yıllık Getiriler",
        "Годовые доходности крипто",
        "暗号資産の年間収益",
        "암호화폐 연간 수익",
        "加密貨幣年度報酬",
        "加密货币年度回报",
    ])),
]


def entry(key, value):
    """One resw row, with the value XML-escaped."""
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
