# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.9.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是订阅认的是哪一只
加载项 —— 那件事本身已经上架，接着往后加只会让这一栏自相矛盾。

本版要说的一件事是：**新增第十八页「市值历程」**。这一页是这轮的主打，而且它是少数几个
「数字不是行情源给的」的页面之一：行情源没有任何一天的历史股本，所以股本由换手率反推
（成交量 ÷ 换手率 就是流通股本），市值等于当日价格乘以它。这句话必须说，否则用户会拿它
去和行情软件显示的「总市值」对账，而对不上（两地上市的公司只算本市场那部分）。

**不在这里写第十九套「十八个图表页」。** 那句话已经在说明段里长期成立（第十八页本身也是在
它已经在应用里之后，由 `port-store-listing-caphistory.py` 补进说明段的）。这一栏只说本版
新增的这一页。

**也不谈价格、不谈订阅**，那两件事上一版说完了；这一栏换掉的就是它们。

**重音字母照写。** 德语的 ü/ä、法语的 é/ç、捷克的 ř/ž 是这个字的一部分，不是装饰；为了
「保险」把它们写成 u/a/e/c/r/z 等于在商店里挂一句拼错的德语。文件是 UTF-8，Python 3 源码
默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

用法：python tools\\port-store-listing-1090.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。一句话远够不着，但每次换文案都要算一遍最长的那一种语言 —— 上限是
# 按字符算的，德/法/意语一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**新增市值历程一页；市值由换手率反推股本算出来；
# 只算本市场可交易的股票；每条线末端跟着一个标签，写着公司名字和它此刻的数值。**
NEWS = {
    "zh-Hans":
        "本版新增「市值历程」一页：一只股票流通市值逐日的曲线，下方同一时间轴上是它的股价；"
        "也可以同时画几家公司，各一条线。行情源没有任何一天的历史股本，所以股本由换手率反推"
        "——成交量除以换手率就是流通股本，市值等于当日价格乘以它；只算本市场可交易的股票，"
        "两地上市的公司因此会低于行情软件显示的「总市值」。每条线的末端跟着一个标签，写着"
        "公司名字和它此刻到达的数值，随动画一起走；几家公司同框时，这些标签也是分辨哪条线是"
        "哪一家的唯一线索。",
    "zh-Hant":
        "本版新增「市值歷程」一頁：一檔股票流通市值逐日的曲線，下方同一時間軸上是它的股價；"
        "也可以同時畫幾家公司，各一條線。行情源沒有任何一天的歷史股本，所以股本由換手率反推"
        "——成交量除以換手率就是流通股本，市值等於當日價格乘以它；只算本市場可交易的股票，"
        "兩地上市的公司因此會低於行情軟體顯示的「總市值」。每條線的末端跟著一個標籤，寫著"
        "公司名字和它此刻到達的數值，隨動畫一起走；幾家公司同框時，這些標籤也是分辨哪條線是"
        "哪一家的唯一線索。",
    "en-US":
        "New in this version: Market Value History - one stock's circulating market value day by "
        "day, with its share price beneath it on the same time axis, or several companies at once, "
        "one line each. No source carries a historical share count, so the count is recovered from "
        "the turnover rate: volume divided by the turnover rate is the circulating count, and the "
        "value is the day's price times it. Only the shares traded in this market are counted, so "
        "a company listed in two places sits below the \"total market value\" a quote app shows. A "
        "label rides each line's leading end with the company's name and the value it has reached "
        "at that moment, moving with the animation; with several companies on one frame, those "
        "labels are also the only thing that says which line is which.",
    "ja":
        "今バージョンの新機能は「時価総額の推移」です。ある銘柄の流通時価総額を日ごとに曲線で"
        "描き、その下に同じ時間軸で株価を置きます。複数社を同時に描くこともでき、会社ごとに"
        "一本の線になります。ソースはどの日についても過去の株式数を持っていないため、株式数は"
        "回転率から逆算します——出来高を回転率で割ったものがそのまま流通株式数で、時価総額は"
        "その日の価格にこれを掛けたものです。数えるのはこの市場で取引される株式だけなので、"
        "二重上場の会社は相場アプリが示す「総時価総額」より低くなります。各線の先端にはラベル"
        "が付き、会社名とその時点で到達した値を示しながらアニメーションと一緒に動きます。複数社"
        "を一枚に描いたときは、このラベルがどの線がどの会社かを見分ける唯一の手掛かりにも"
        "なります。",
    "ko":
        "이 버전의 새 기능은 「시가총액 추이」입니다. 한 종목의 유통 시가총액을 날짜별로 곡선으로 "
        "그리고, 그 아래 같은 시간 축에 주가를 놓습니다. 여러 기업을 동시에 그릴 수도 있고 기업마다 "
        "선이 하나씩 생깁니다. 출처에는 어느 날의 과거 주식 수도 없으므로 주식 수는 회전율에서 "
        "되찾습니다——거래량을 회전율로 나눈 것이 곧 유통 주식 수이고, 시가총액은 그날의 가격에 "
        "이를 곱한 값입니다. 이 시장에서 거래되는 주식만 세므로 이중 상장 기업은 시세 앱이 보여주는 "
        "「총 시가총액」보다 낮게 나옵니다. 각 선 끝에는 라벨이 붙어 회사 이름과 그 시점에 도달한 "
        "값을 보여주며 애니메이션과 함께 움직입니다. 여러 기업을 한 화면에 그릴 때는 이 라벨이 어떤 "
        "선이 어느 기업인지 구분하는 유일한 단서이기도 합니다.",
    "de":
        "Neu in dieser Version: Marktwert-Verlauf - die frei handelbare Marktkapitalisierung einer "
        "Aktie Tag für Tag als Kurve, darunter auf derselben Zeitachse ihr Kurs, oder mehrere "
        "Unternehmen zugleich, mit je einer Linie. Keine Quelle kennt einen historischen "
        "Aktienbestand, deshalb wird er aus der Umschlagsrate ermittelt: das Volumen geteilt durch "
        "die Umschlagsrate ist die frei handelbare Stückzahl, und der Wert ist der Tageskurs mal "
        "diese Zahl. Gezählt werden nur die an diesem Markt gehandelten Aktien, weshalb ein doppelt "
        "notiertes Unternehmen unter der Gesamtmarktkapitalisierung liegt, die eine Kurs-App zeigt. "
        "Am vorderen Ende jeder Linie sitzt ein Etikett mit dem Namen des Unternehmens und dem Wert, "
        "den es in diesem Moment erreicht hat, und es wandert mit der Animation; bei mehreren "
        "Unternehmen in einem Bild sind diese Etiketten auch das Einzige, was sagt, welche Linie "
        "welche ist.",
    "fr":
        "Nouveau dans cette version : Historique de la valeur de marché - la capitalisation "
        "flottante d'une action au jour le jour, avec son cours en dessous sur le même axe de temps, "
        "ou plusieurs entreprises à la fois, une courbe chacune. Aucune source ne connaît le nombre "
        "d'actions historique ; il est donc retrouvé à partir du taux de rotation : le volume divisé "
        "par le taux de rotation est le nombre d'actions flottantes, et la valeur est le cours du "
        "jour multiplié par ce nombre. Seules les actions négociées sur ce marché sont comptées, si "
        "bien qu'une entreprise cotée à deux endroits se situe sous la capitalisation totale "
        "affichée par une application de cotations. Une étiquette suit l'extrémité de chaque courbe "
        "avec le nom de l'entreprise et la valeur atteinte à cet instant, et elle avance avec "
        "l'animation ; avec plusieurs entreprises sur une même image, ces étiquettes sont aussi la "
        "seule chose qui dise quelle courbe est laquelle.",
    "it":
        "Novità di questa versione: Storia del valore di mercato - la capitalizzazione flottante di "
        "un'azione giorno per giorno, con sotto il suo prezzo sullo stesso asse temporale, oppure "
        "più aziende insieme, una linea ciascuna. Nessuna fonte conserva un numero storico di "
        "azioni, quindi lo si ricava dal tasso di rotazione: il volume diviso per il tasso di "
        "rotazione è il numero di azioni flottanti, e il valore è il prezzo del giorno per questo "
        "numero. Si contano solo le azioni scambiate su questo mercato, perciò un'azienda quotata in "
        "due piazze resta sotto la capitalizzazione totale mostrata da un'app di quotazioni. "
        "Un'etichetta segue l'estremità di ogni linea con il nome dell'azienda e il valore raggiunto "
        "in quell'istante, e si muove con l'animazione; con più aziende in un solo quadro, queste "
        "etichette sono anche l'unica cosa che dice quale linea è quale.",
    "es":
        "Novedad de esta versión: Historial de valor de mercado - la capitalización circulante de "
        "una acción día a día, con su cotización debajo en el mismo eje temporal, o varias empresas "
        "a la vez, una línea cada una. Ninguna fuente guarda un número histórico de acciones, así "
        "que se recupera desde la tasa de rotación: el volumen dividido por la tasa de rotación es "
        "el número de acciones en circulación, y el valor es el precio del día multiplicado por ese "
        "número. Solo se cuentan las acciones negociadas en este mercado, de modo que una empresa "
        "cotizada en dos plazas queda por debajo de la capitalización total que muestra una app de "
        "cotizaciones. Una etiqueta sigue el extremo de cada línea con el nombre de la empresa y el "
        "valor alcanzado en ese instante, y avanza con la animación; con varias empresas en un mismo "
        "cuadro, esas etiquetas son también lo único que dice qué línea es cuál.",
    "pt-BR":
        "Novo nesta versão: Histórico de valor de mercado - o valor de mercado circulante de uma "
        "ação dia a dia, com o preço dela abaixo no mesmo eixo de tempo, ou várias empresas ao mesmo "
        "tempo, uma linha cada. Nenhuma fonte guarda uma contagem histórica de ações, então ela é "
        "recuperada pela taxa de giro: o volume dividido pela taxa de giro é a quantidade de ações "
        "em circulação, e o valor é o preço do dia vezes essa quantidade. Só entram as ações "
        "negociadas neste mercado, por isso uma empresa listada em duas praças fica abaixo da "
        "capitalização total que um app de cotações mostra. Um rótulo acompanha a ponta de cada "
        "linha com o nome da empresa e o valor alcançado naquele instante, e anda com a animação; "
        "com várias empresas num mesmo quadro, esses rótulos são também a única coisa que diz qual "
        "linha é qual.",
    "pl":
        "Nowość w tej wersji: Historia wartości rynkowej - kapitalizacja obrotowa jednej akcji dzień "
        "po dniu, a pod nią na tej samej osi czasu jej kurs, albo kilka spółek naraz, każda ze swoją "
        "linią. Żadne źródło nie ma historycznej liczby akcji, więc odtwarza się ją ze wskaźnika "
        "obrotu: wolumen podzielony przez wskaźnik obrotu to liczba akcji w obrocie, a wartość to "
        "kurs dnia razy ta liczba. Liczone są tylko akcje handlowane na tym rynku, więc spółka "
        "notowana w dwóch miejscach wypada poniżej całkowitej kapitalizacji pokazywanej przez "
        "aplikację z notowaniami. Etykieta podąża za końcem każdej linii z nazwą spółki i wartością, "
        "jaką ta osiągnęła w danej chwili, i porusza się razem z animacją; przy kilku spółkach na "
        "jednym obrazie te etykiety są też jedyną rzeczą, która mówi, która linia jest która.",
    "cs":
        "Novinkou této verze je Historie tržní hodnoty - obchodovaná tržní kapitalizace jedné akcie "
        "den po dni, pod ní na stejné časové ose její kurz, nebo několik firem najednou, každá se "
        "svou čarou. Žádný zdroj neuchovává historický počet akcií, a tak se dopočítává z míry "
        "obratu: objem dělený mírou obratu je počet akcií v oběhu a hodnota je kurz dne krát tento "
        "počet. Počítají se jen akcie obchodované na tomto trhu, takže firma kótovaná na dvou "
        "místech je pod celkovou tržní kapitalizací, kterou ukazuje aplikace s kurzy. Štítek jede na "
        "konci každé čáry s názvem firmy a hodnotou, které v tu chvíli dosáhla, a pohybuje se s "
        "animací; při několika firmách v jednom obraze jsou tyto štítky také tím jediným, co říká, "
        "která čára je která.",
    "ru":
        "Новое в этой версии: История капитализации - капитализация одной акции в свободном "
        "обращении день за днём, а под ней на той же оси времени её цена; можно вывести и несколько "
        "компаний сразу, по одной линии на каждую. Ни один источник не хранит историческое число "
        "акций, поэтому оно восстанавливается из оборачиваемости: объём, делённый на "
        "оборачиваемость, - это и есть число акций в обращении, а капитализация - цена дня, "
        "умноженная на него. Учитываются только акции, которыми торгуют на этом рынке, поэтому "
        "компания с листингом в двух местах оказывается ниже общей капитализации, которую "
        "показывает приложение с котировками. Ярлык едет у конца каждой линии с названием компании "
        "и значением, которого она достигла в этот момент, и движется вместе с анимацией; когда в "
        "одном кадре несколько компаний, эти ярлыки - ещё и единственное, что говорит, какая линия "
        "какая.",
    "tr":
        "Bu sürümde yeni: Piyasa değeri geçmişi - bir hissenin dolaşımdaki piyasa değeri gün gün, "
        "altında aynı zaman ekseninde fiyatı; ya da birden çok şirket aynı anda, her birine bir "
        "çizgi. Hiçbir kaynak geçmiş hisse sayısını saklamıyor, bu yüzden o devir hızından geri "
        "çıkarılıyor: hacmin devir hızına bölümü dolaşımdaki hisse sayısıdır ve değer, günün "
        "fiyatının bu sayıyla çarpımıdır. Yalnızca bu piyasada işlem gören hisseler sayılır, bu "
        "yüzden iki yerde listelenen bir şirket, fiyat uygulamasının gösterdiği toplam piyasa "
        "değerinin altında kalır. Her çizginin ucunda bir etiket şirketin adını ve o anda ulaştığı "
        "değeri taşır ve animasyonla birlikte hareket eder; tek karede birkaç şirket varken bu "
        "etiketler aynı zamanda hangi çizginin hangisi olduğunu söyleyen tek şeydir.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 各文件保持自己的行尾：store-listing.md 是 CRLF。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
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

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
