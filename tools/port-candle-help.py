"""Adds the candle chapter to all fourteen help documents.

The chapter goes in at a fixed position — before the tenth `##` heading, which is
"Video" in every language — rather than by matching a translated title, because
the titles are what differs between the fourteen files.

Idempotent: if the heading already sits at that position the whole section is
replaced, so running this twice changes nothing the second time. Files are written
as UTF-8 **with a BOM**, which is what they are now.

Run:  <venv python> tools/port-candle-help.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# The chapter lands here: after the last page's chapter, before "Video".
POSITION = 9

SECTIONS = {
    "en-US": """## Candles

One instrument's prices as candles: daily, weekly or monthly, drawn four ways, with its averages and its volume underneath.

- **Period** decides how much market time one candle covers — a day, a week or a month. Changing it fetches again, because the three are separate series on the source.
- **Style** decides how the same four prices are drawn: candles, OHLC bars, a closing line, or a closing area. Switching between them re-fetches nothing.
- **Motion** is either candles arriving one after another until the whole range is laid out, or a fixed window of them walking forward. The second is what keeps a candle wide enough to read on a long range, and how wide is the **window** setting.
- Moving averages MA5, MA10 and MA20 can be laid over the candles; the volume panel underneath can be turned off, and the price panel takes the room back.
- A week or a month still in progress is left out. A candle made of three days is not a week.
- Every market is read on its adjusted series, so a split day is not drawn as a fall, and neither is a dividend.
""",
    "de": """## Kerzenchart

Die Kerzen eines Instruments: täglich, wöchentlich oder monatlich, auf vier Arten gezeichnet, mit Durchschnitten und Volumen darunter.

- **Intervall** entscheidet, wie viel Marktzeit eine Kerze abdeckt — ein Tag, eine Woche oder ein Monat. Eine Änderung lädt neu, denn die drei sind auf der Quelle getrennte Reihen.
- **Darstellung** entscheidet, wie dieselben vier Preise gezeichnet werden: Kerzen, OHLC-Balken, Schlusskurslinie oder Schlusskursfläche. Umschalten lädt nichts neu.
- **Ablauf** ist entweder das Eintreffen der Kerzen nacheinander, bis der ganze Zeitraum steht, oder ein festes Fenster, das weiterwandert. Das zweite hält die Kerze auf einem langen Zeitraum breit genug zum Lesen, und wie breit ist die Einstellung **Fenster**.
- Gleitende Durchschnitte MA5, MA10 und MA20 können über die Kerzen gelegt werden; das Volumenfeld darunter lässt sich abschalten, und das Preisfeld nimmt den Platz zurück.
- Eine noch laufende Woche oder ein laufender Monat bleibt draußen. Eine Kerze aus drei Tagen ist keine Woche.
- Jeder Markt wird auf seiner bereinigten Reihe gelesen, damit ein Split-Tag nicht als Rückgang erscheint und eine Dividende auch nicht.
""",
    "es": """## Velas

Las velas de un instrumento: diarias, semanales o mensuales, dibujadas de cuatro formas, con sus medias y su volumen debajo.

- **Intervalo** decide cuánto tiempo de mercado cubre una vela: un día, una semana o un mes. Cambiarlo vuelve a consultar la fuente, porque en ella las tres son series distintas.
- **Tipo de dibujo** decide cómo se dibujan los mismos cuatro precios: velas, barras OHLC, línea de cierre o área de cierre. Pasar de uno a otro no vuelve a consultar nada.
- **Animación** es o bien la llegada de las velas una tras otra hasta trazar todo el periodo, o bien una ventana fija que avanza. La segunda es lo que mantiene la vela lo bastante ancha para leerse en un periodo largo, y esa anchura es el ajuste **Ventana**.
- Las medias móviles MA5, MA10 y MA20 pueden superponerse a las velas; el panel de volumen de abajo se puede apagar, y el panel de precio recupera ese espacio.
- Una semana o un mes aún en curso queda fuera. Una vela hecha de tres días no es una semana.
- Todos los mercados se leen en su serie ajustada, así que un día de split no se dibuja como una caída, ni un dividendo tampoco.
""",
    "fr": """## Chandeliers

Les chandeliers d'un instrument : quotidiens, hebdomadaires ou mensuels, dessinés de quatre façons, avec ses moyennes et son volume en dessous.

- **Granularité** décide de la durée que couvre un chandelier : un jour, une semaine ou un mois. La changer relance la récupération, car les trois sont des séries distinctes sur la source.
- **Type de tracé** décide comment les quatre mêmes prix sont dessinés : chandeliers, barres OHLC, ligne de clôture ou aire de clôture. Passer de l'un à l'autre ne récupère rien.
- **Animation** est soit l'arrivée des chandeliers l'un après l'autre jusqu'à ce que tout l'intervalle soit tracé, soit une fenêtre fixe qui avance. C'est la seconde qui garde le chandelier assez large pour être lu sur un intervalle long, et cette largeur est le réglage **Fenêtre**.
- Les moyennes mobiles MA5, MA10 et MA20 peuvent être superposées aux chandeliers ; le panneau de volume en dessous peut être désactivé, et le panneau de prix reprend la place.
- Une semaine ou un mois encore en cours est laissé de côté. Un chandelier fait de trois jours n'est pas une semaine.
- Chaque marché est lu sur sa série ajustée : un jour de division n'est donc pas dessiné comme une baisse, et un dividende non plus.
""",
    "it": """## Candele

Le candele di uno strumento: giornaliere, settimanali o mensili, disegnate in quattro modi, con le medie e il volume sotto.

- **Intervallo** decide quanto tempo di mercato copre una candela: un giorno, una settimana o un mese. Cambiarlo ricarica i dati, perché sulla fonte le tre sono serie distinte.
- **Tipo di disegno** decide come vengono disegnati gli stessi quattro prezzi: candele, barre OHLC, linea di chiusura o area di chiusura. Passare dall'uno all'altro non ricarica nulla.
- **Animazione** è l'arrivo delle candele una dopo l'altra finché tutto l'intervallo è tracciato, oppure una finestra fissa che avanza. La seconda è ciò che mantiene la candela abbastanza larga da leggersi su un intervallo lungo, e quella ampiezza è l'impostazione **Finestra**.
- Le medie mobili MA5, MA10 e MA20 possono essere sovrapposte alle candele; il pannello del volume sotto può essere spento, e il pannello del prezzo riprende lo spazio.
- Una settimana o un mese ancora in corso resta fuori. Una candela fatta di tre giorni non è una settimana.
- Ogni mercato è letto sulla sua serie rettificata, quindi un giorno di frazionamento non è disegnato come un calo, e nemmeno un dividendo.
""",
    "pl": """## Wykres świecowy

Świece jednego instrumentu: dzienne, tygodniowe lub miesięczne, rysowane na cztery sposoby, ze średnimi i wolumenem poniżej.

- **Interwał** decyduje, jaki czas rynkowy obejmuje jedna świeca: dzień, tydzień lub miesiąc. Zmiana go pobiera dane ponownie, bo na źródle to trzy osobne serie.
- **Rodzaj wykresu** decyduje, jak te same cztery ceny są rysowane: świece, słupki OHLC, linia zamknięcia lub obszar zamknięcia. Przełączanie niczego nie pobiera.
- **Animacja** to pojawianie się świec jedna po drugiej, aż cały zakres zostanie narysowany, albo stałe okno, które przesuwa się w przód. To drugie sprawia, że świeca na długim zakresie zostaje dość szeroka do odczytania, a jej szerokość to ustawienie **Okno**.
- Średnie kroczące MA5, MA10 i MA20 można nałożyć na świece; panel wolumenu poniżej można wyłączyć, a panel ceny odzyskuje to miejsce.
- Tydzień lub miesiąc wciąż trwający zostaje pominięty. Świeca złożona z trzech dni nie jest tygodniem.
- Każdy rynek jest czytany na swojej serii skorygowanej, więc dzień splitu nie jest rysowany jako spadek, tak samo jak dywidenda.
""",
    "pt-BR": """## Candlestick

Os candles de um instrumento: diários, semanais ou mensais, desenhados de quatro formas, com médias e volume abaixo.

- **Intervalo** decide quanto tempo de mercado um candle cobre: um dia, uma semana ou um mês. Mudá-lo busca os dados de novo, porque na fonte as três são séries distintas.
- **Tipo de desenho** decide como os mesmos quatro preços são desenhados: candles, barras OHLC, linha de fechamento ou área de fechamento. Trocar de um para outro não busca nada.
- **Animação** é a chegada dos candles um após o outro até traçar todo o período, ou uma janela fixa que avança. A segunda é o que mantém o candle largo o bastante para ser lido num período longo, e essa largura é o ajuste **Janela**.
- As médias móveis MA5, MA10 e MA20 podem ser sobrepostas aos candles; o painel de volume abaixo pode ser desligado, e o painel de preço recupera o espaço.
- Uma semana ou um mês ainda em curso fica de fora. Um candle feito de três dias não é uma semana.
- Todo mercado é lido na sua série ajustada, então um dia de desdobramento não é desenhado como queda, e um dividendo tampouco.
""",
    "cs": """## Svíčkový graf

Svíčky jednoho nástroje: denní, týdenní nebo měsíční, kreslené čtyřmi způsoby, s průměry a objemem pod nimi.

- **Interval** určuje, jaké tržní období jedna svíčka pokrývá: den, týden nebo měsíc. Jeho změna načte data znovu, protože na zdroji jde o tři samostatné řady.
- **Způsob zobrazení** určuje, jak jsou tytéž čtyři ceny nakresleny: svíčky, OHLC sloupce, čára závěru nebo plocha závěru. Přepínání nic nenačítá.
- **Animace** je buď přicházení svíček jedna po druhé, dokud není celé období rozkreslené, nebo pevné okno, které se posouvá vpřed. Druhá z nich udrží svíčku na dlouhém období dostatečně širokou ke čtení a její šířka je nastavení **Okno**.
- Klouzavé průměry MA5, MA10 a MA20 lze položit přes svíčky; panel objemu dole lze vypnout a panel ceny místo získá zpět.
- Probíhající týden nebo měsíc je vynechán. Svíčka ze tří dnů není týden.
- Každý trh se čte na své upravené řadě, takže den štěpení akcií není nakreslen jako pokles, a dividenda také ne.
""",
    "tr": """## Mum grafiği

Bir enstrümanın mumları: günlük, haftalık veya aylık, dört farklı şekilde çizilir; altında ortalamaları ve hacmi.

- **Aralık**, bir mumun ne kadar piyasa zamanını kapsadığını belirler: bir gün, bir hafta veya bir ay. Bunu değiştirmek yeniden veri çeker, çünkü kaynakta üçü ayrı serilerdir.
- **Çizim türü**, aynı dört fiyatın nasıl çizileceğini belirler: mumlar, OHLC çubukları, kapanış çizgisi veya kapanış alanı. Aralarında geçiş yapmak hiçbir şey yeniden çekmez.
- **Animasyon**, mumların tek tek gelip tüm aralığı çizmesi ya da ilerleyen sabit bir penceredir. İkincisi, mumu uzun bir aralıkta okunacak kadar geniş tutan şeydir ve bu genişlik **Pencere** ayarıdır.
- MA5, MA10 ve MA20 hareketli ortalamaları mumların üzerine bindirilebilir; alttaki hacim paneli kapatılabilir ve fiyat paneli o alanı geri alır.
- Henüz bitmemiş bir hafta veya ay dışarıda bırakılır. Üç günden oluşan bir mum bir hafta değildir.
- Her piyasa düzeltilmiş serisinden okunur, bu yüzden bir bölünme günü düşüş olarak çizilmez; temettü de çizilmez.
""",
    "ru": """## Свечной график

Свечи одного инструмента: дневные, недельные или месячные, в четырёх видах, со скользящими средними и объёмом ниже.

- **Интервал** определяет, какой отрезок рынка покрывает одна свеча: день, неделю или месяц. Его смена запрашивает данные заново, потому что на источнике это три отдельные серии.
- **Вид графика** определяет, как рисуются одни и те же четыре цены: свечи, бары OHLC, линия закрытия или область закрытия. Переключение ничего не запрашивает.
- **Анимация** — это либо появление свечей одна за другой, пока весь диапазон не будет построен, либо фиксированное окно, которое движется вперёд. Второе и сохраняет свечу достаточно широкой для чтения на длинном диапазоне, а её ширина — это настройка **Окно**.
- Скользящие средние MA5, MA10 и MA20 можно наложить на свечи; панель объёма ниже можно отключить, и панель цены вернёт себе это место.
- Незавершённая неделя или месяц не включается. Свеча из трёх дней — это не неделя.
- Каждый рынок читается по своей скорректированной серии, поэтому день дробления не рисуется как падение, и дивиденд тоже.
""",
    "ja": """## ローソク足

1つの銘柄のローソク足。日足・週足・月足から選び、4つの描き方で表示します。下段に移動平均と出来高。

- **期間**は1本のローソク足がどれだけの市場時間を表すかを決めます。1日、1週間、1か月のいずれか。変更すると再取得します。ソース上で3つは別々の系列だからです。
- **描き方**は同じ4本値をどう描くかを決めます。ローソク足、OHLCバー、終値ライン、終値エリア。切り替えても再取得はしません。
- **進行**は、全区間を埋めるまでローソク足が1本ずつ現れる方法か、固定した窓が前方へ進む方法のどちらかです。長い期間でもローソク足を読みやすい幅に保つのは後者で、その幅が**表示本数**です。
- 移動平均 MA5・MA10・MA20 をローソク足に重ねて描けます。下の出来高パネルは消せます。消すと価格パネルがその分だけ広がります。
- まだ終わっていない週や月は含めません。3日分のローソク足は1週間ではないからです。
- どの市場でも調整済みの系列から読むため、分割の日が下落として描かれることはなく、配当も同じです。
""",
    "ko": """## 캔들 차트

한 종목의 캔들입니다. 일·주·월 중에서 고르고 네 가지 방식으로 그립니다. 아래에 이동평균과 거래량.

- **주기**는 캔들 하나가 담는 시장 시간을 정합니다. 하루, 한 주, 한 달 중 하나입니다. 바꾸면 다시 가져오는데, 소스에서 세 가지는 별개의 계열이기 때문입니다.
- **표시 방식**은 같은 네 가격을 어떻게 그릴지 정합니다. 캔들, OHLC 바, 종가 선, 종가 영역. 서로 바꿔도 다시 가져오지 않습니다.
- **진행 방식**은 캔들이 하나씩 나타나 전체 구간을 채우는 방식이거나, 고정된 창이 앞으로 이동하는 방식입니다. 구간이 길어도 캔들을 읽을 만큼 넓게 유지하는 것은 후자이며, 그 너비가 **창 크기**입니다.
- 이동평균 MA5·MA10·MA20을 캔들 위에 겹쳐 그릴 수 있습니다. 아래 거래량 패널은 끌 수 있고, 그러면 가격 패널이 그 공간을 되찾습니다.
- 아직 끝나지 않은 주나 달은 넣지 않습니다. 사흘로 만든 캔들은 한 주가 아니기 때문입니다.
- 모든 시장에서 조정된 계열로 읽으므로, 액면분할일이 하락으로 그려지지 않고 배당도 마찬가지입니다.
""",
    "zh-Hans": """## K线走势

一只标的的价格 K 线：日K、周K、月K 三种周期，四种画法，下方带均线与成交量。

- **周期**决定一根 K 线覆盖多长的市场时间——一天、一周还是一个月。改它会重新取数，因为三者在行情源上是各自独立的序列。
- **画法**决定同样四个价格怎么画：蜡烛图、美国线、收盘线、面积图。相互切换不需要重新取数。
- **推进方式**有两种：K 线一根根出现直到铺满整个区间，或者一个固定窗口向前滚动。长区间里还能把 K 线保持在看得清的宽度上，靠的是后者，而这个宽度就是**窗口根数**。
- 均线 MA5、MA10、MA20 可以叠在 K 线上；下方的成交量面板可以关闭，价格图会收回那块空间。
- 尚未走完的周或月不画。由三天组成的蜡烛不是一周。
- 每个市场读的都是各自的复权序列，所以拆股日不会被画成下跌，分红也不会。
""",
    "zh-Hant": """## K線走勢

一檔標的的 K 線：日K、週K、月K 三種週期，四種畫法，下方帶均線與成交量。

- **週期**決定一根 K 線涵蓋多長的市場時間——一天、一週還是一月。改它會重新取數，因為三者在行情源上是各自獨立的序列。
- **畫法**決定同樣四個價格怎麼畫：蠟燭圖、美國線、收盤線、面積圖。相互切換不需要重新取數。
- **推進方式**有兩種：K 線一根根出現直到鋪滿整個區間，或者一個固定視窗向前滾動。長區間裡還能把 K 線維持在看得清的寬度上，靠的是後者，而這個寬度就是**視窗根數**。
- 均線 MA5、MA10、MA20 可以疊在 K 線上；下方的成交量面板可以關閉，價格圖會收回那塊空間。
- 尚未走完的週或月不畫。由三天組成的蠟燭不是一週。
- 每個市場讀的都是各自的復權序列，所以拆股日不會被畫成下跌，配息也不會。
""",
}


def main() -> int:
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        text = path.read_bytes().decode("utf-8-sig")

        # A second BOM can survive that decode: `utf-8-sig` strips only the first
        # one, so a file that already carried two keeps one, and this pass writes
        # another — a zero-width character parked at the head of the title line.
        text = text.lstrip("\ufeff")

        # These files are CRLF. Splitting on "\n" alone would leave a "\r" on every
        # original line and none on the inserted ones, which is a mixed file that
        # shows as a whole-section rewrite in git.
        crlf = "\r\n" in text
        joiner = "\r\n" if crlf else "\n"
        lines = text.split(joiner)

        headings = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(headings) <= POSITION:
            print(f"{tag}: only {len(headings)} headings, expected more than {POSITION}")
            return 1

        section = SECTIONS[tag].rstrip("\n").split("\n")
        wanted = section[0].strip()

        if lines[headings[POSITION]].strip() == wanted:
            # Already there: replace from this heading to the next one.
            end = headings[POSITION + 1] if len(headings) > POSITION + 1 else len(lines)
            lines = lines[:headings[POSITION]] + section + [""] + lines[end:]
            print(f"{tag:9} replaced")
        else:
            at = headings[POSITION]
            lines = lines[:at] + section + [""] + lines[at:]
            print(f"{tag:9} inserted before {lines[at + len(section) + 1]!r}")

        path.write_bytes(b"\xef\xbb\xbf" + joiner.join(lines).encode("utf-8"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
