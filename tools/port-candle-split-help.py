# -*- coding: utf-8 -*-
r"""给 14 份帮助手册「K 线走势」章加一条：多标的的两种排布，以及收尾那排卡片。

用户要的是两件事，都在多标的的画面上：

1. **「分图显示」**：一个下拉，在「多标的叠在一张图上」与「每只一张图、上下排列」之间切。
   后者每个标的一格，各自一条纵轴（按各自的涨跌范围缩放，零线仍留在格内），横轴与日期共用、
   只出现在最下面那一格底下。最多 3 格 —— 第九分之一高的格子是竖屏帧能读得下的下限。
2. **最下方逐只列涨幅**：每只一张卡片，大字是它的区间涨幅，下面一行是涨了多少点（或多少钱），
   与曲线末端那个数字是同一个。这一排其实就是**持仓收益页**多标的收尾那一排
   （现在的 `Render/TrackCards.cs`），两种排布下都有。

**为什么按「上一条的结尾」定位**：这一章的条数随版本变（现在 11 条），而「比较」那条是上一轮
刚写进去的、全 14 语言各有一句独有的结尾 —— 用它的结尾当锚，找到就插在它后面，找不到就大声
失败（悄悄跳过会留下 13 份说了、1 份没说）。

**重音字母照写。** 德语的 ü、法语的 é/è/ô、捷克语的 ř/ž/í、土耳其语的 ğ/ı/ş、俄语的 я/ё、
韩语的字素都是这个词的一部分，不是装饰。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM。

幂等：这一条已经在章里就跳过。

用法：<venv python> tools/port-candle-split-help.py     （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP
CHAPTER = lt.chapter_of("NavCandle")

# 上一条（「选两个以上标的，画面就变成比较」）的结尾 —— 上一轮刚写进去的那句。锚在它被改过
# 或换了行时找不到，那时该红着，不能猜。
ANCHOR = {
    "zh-Hans": "所以末端那个数字就是各标的的当日涨跌幅。",
    "zh-Hant": "就是各標的的當日漲跌幅。",
    "en-US": "so the figure at the end is each instrument's move for the day.",
    "ja": "末端の数字は各銘柄のその日の騰落率になります。",
    "ko": "끝의 숫자가 각 종목의 그날 등락률입니다.",
    "de": "die Zahl am Ende ist also die Tagesveränderung des jeweiligen Instruments.",
    "fr": "le chiffre au bout est donc la variation du jour de chaque instrument.",
    "it": "la cifra in fondo è quindi la variazione del giorno di ciascuno strumento.",
    "es": "así que la cifra del final es la variación del día de cada instrumento.",
    "pt-BR": "então o número no fim é a variação do dia de cada instrumento.",
    "pl": "liczba na końcu to więc dzienna zmiana każdego instrumentu.",
    "cs": "číslo na konci je tedy denní změna každého nástroje.",
    "ru": "число на конце — это дневное изменение каждого инструмента.",
    "tr": "yani uçtaki sayı her enstrümanın o günkü değişimidir.",
}

NEW = {
    "zh-Hans": "- **多标的可以叠在一张图里，也可以每只一张图。**「分图显示」选「每只一张图」时，每个标的一格、"
               "上下排列，各有一条按自己涨跌范围缩放的纵轴，零线仍在格内；横轴与日期是共用的，只画在最下面那一格"
               "底下。分图最多 3 只，清单里多于 3 只时按顺序只画前 3 只，其余在状态行里点名。两种排布之间切换不"
               "重新取数。无论哪种排布，画面最下方都逐只列出一张卡片：大字是它的**区间涨幅**，下面一行是涨了多少"
               "点（或多少钱）—— 与曲线末端那个数字是同一个。",
    "zh-Hant": "- **多標的可以疊在一張圖裡，也可以每隻一張圖。**「分圖顯示」選「每隻一張圖」時，每個標的一格、"
               "上下排列，各有一條按自己漲跌範圍縮放的縱軸，零線仍在格內；橫軸與日期是共用的，只畫在最下面那一格"
               "底下。分圖最多 3 隻，清單裡多於 3 隻時按順序只畫前 3 隻，其餘在狀態列裡點名。兩種排布之間切換不"
               "重新取數。無論哪種排布，畫面最下方都逐隻列出一張卡片：大字是它的**區間漲幅**，下面一行是漲了多少"
               "點（或多少錢）—— 與曲線末端那個數字是同一個。",
    "en-US": "- **Several instruments can share one chart, or each have its own.** With **layout** set to one chart "
             "each, every instrument gets a panel, stacked, on an axis of its own scaled to its own range with the "
             "zero line still inside it; the x axis and the dates are shared and drawn once, under the bottom panel. "
             "A split frame holds three, so with more than three picked the first three in the list are drawn and the "
             "rest are named in the status line. Switching between the two layouts re-fetches nothing. Either way the "
             "frame ends on one card per instrument: its **move over the range** in large type, and under it how many "
             "points — or how much money — that move was, the same figure the label at the end of its curve is "
             "showing.",
    "ja": "- **複数の銘柄は 1 枚のチャートに重ねることも、1 銘柄ずつに分けることもできます。**「レイアウト」で"
          "「1 銘柄 1 チャート」を選ぶと、銘柄ごとに 1 つのパネルを縦に並べ、自分の変動幅に合わせた縦軸（ゼロ線は"
          "パネル内）を持ちます。横軸と日付は共有で、日付は最下段のパネルの下にだけ描きます。分割表示は最大 3 銘柄"
          "なので、4 銘柄以上を選ぶとリスト順に前の 3 銘柄だけを描き、残りはステータス行に表示します。2 つの"
          "レイアウトの切り替えで再取得は起きません。どちらの場合も、いちばん下に 1 銘柄につき 1 枚のカードが並び、"
          "大きな字が**区間の騰落率**、その下が何ポイント（またはいくら）動いたかです。曲線の末端に出ている数字と"
          "同じ値です。",
    "ko": "- **여러 종목을 한 차트에 겹쳐 그릴 수도, 종목마다 따로 그릴 수도 있습니다.**「분할 표시」에서「종목별 한 "
          "차트」를 고르면 종목마다 패널 하나가 위아래로 놓이고, 자기 변동 폭에 맞춘 세로축을 가지며 0선은 패널 안에 "
          "남습니다. 가로축과 날짜는 공유하므로 날짜는 맨 아래 패널 밑에만 그립니다. 분할 표시는 최대 3종목이라 3개를 "
          "넘게 고르면 목록 순서대로 앞의 3개만 그리고 나머지는 상태 표시줄에 적습니다. 두 배치를 오갈 때 다시 받아오지 "
          "않습니다. 어느 쪽이든 화면 맨 아래에 종목마다 카드 한 장이 놓이고, 큰 글씨가 **구간 등락률**, 그 아래가 몇 "
          "포인트(또는 얼마) 움직였는지입니다. 곡선 끝의 숫자와 같은 값입니다.",
    "de": "- **Mehrere Instrumente können ein Diagramm teilen oder je eines bekommen.** Steht **Anordnung** auf „je ein "
          "Diagramm“, bekommt jedes Instrument ein Panel, untereinander, mit einer eigenen Achse, die auf seinen "
          "eigenen Bereich skaliert ist und die Nulllinie weiterhin enthält; die x-Achse und die Daten sind gemeinsam "
          "und stehen einmal, unter dem untersten Panel. Die geteilte Ansicht fasst drei, bei mehr als drei "
          "Auswahlen werden also die ersten drei der Liste gezeichnet und der Rest in der Statuszeile genannt. "
          "Zwischen den beiden Anordnungen umzuschalten lädt nichts neu. So oder so endet das Bild mit einer Karte je "
          "Instrument: groß die **Veränderung über den Zeitraum** und darunter, wie viele Punkte — oder wie viel "
          "Geld — das waren, dieselbe Zahl, die das Etikett am Ende der Kurve zeigt.",
    "fr": "- **Plusieurs instruments peuvent partager un graphique ou avoir chacun le leur.** Avec **Disposition** sur "
          "« un graphique par instrument », chaque instrument occupe un panneau, empilés, avec son propre axe mis à "
          "l'échelle de sa propre amplitude, la ligne du zéro restant à l'intérieur ; l'axe des x et les dates sont "
          "communs et ne sont tracés qu'une fois, sous le panneau du bas. La vue éclatée en accepte trois : au-delà de "
          "trois sélections, les trois premières de la liste sont tracées et les autres sont nommées dans la barre "
          "d'état. Passer d'une disposition à l'autre ne recharge rien. Dans les deux cas, le bas du cadre porte une "
          "carte par instrument : en gros sa **variation sur la période**, et dessous de combien de points — ou de "
          "combien d'argent — il s'est déplacé, le même chiffre que celui affiché au bout de sa courbe.",
    "it": "- **Più strumenti possono condividere un grafico o averne uno ciascuno.** Con **Disposizione** su «un "
          "grafico ciascuno», ogni strumento occupa un pannello, impilati, con un asse proprio scalato sulla propria "
          "escursione e la linea dello zero ancora dentro; l'asse x e le date sono comuni e vengono disegnati una "
          "volta sola, sotto il pannello in basso. La vista divisa ne tiene tre: con più di tre selezionati si "
          "disegnano i primi tre dell'elenco e gli altri vengono indicati nella barra di stato. Passare da una "
          "disposizione all'altra non ricarica nulla. In entrambi i casi il fondo del fotogramma porta una scheda per "
          "strumento: in grande la sua **variazione nel periodo** e sotto di quanti punti — o di quanto denaro — si è "
          "mosso, la stessa cifra che mostra l'etichetta in fondo alla sua curva.",
    "es": "- **Varios instrumentos pueden compartir un gráfico o tener uno cada uno.** Con **Disposición** en «un "
          "gráfico por instrumento», cada instrumento ocupa un panel, apilados, con su propio eje escalado a su "
          "propio recorrido y la línea del cero aún dentro; el eje x y las fechas son comunes y se dibujan una sola "
          "vez, bajo el panel inferior. La vista dividida admite tres: con más de tres seleccionados se dibujan los "
          "tres primeros de la lista y el resto se indica en la barra de estado. Cambiar de una disposición a otra no "
          "recarga nada. En ambos casos el pie del cuadro lleva una tarjeta por instrumento: en grande su "
          "**variación en el periodo** y debajo cuántos puntos — o cuánto dinero — supuso, la misma cifra que muestra "
          "la etiqueta al final de su curva.",
    "pt-BR": "- **Vários instrumentos podem dividir um gráfico ou ter um cada um.** Com **Disposição** em «um gráfico "
             "cada», cada instrumento ocupa um painel, empilhados, com um eixo próprio escalado pela sua própria "
             "amplitude e a linha do zero ainda dentro; o eixo x e as datas são comuns e são desenhados uma vez só, "
             "sob o painel de baixo. A visão dividida comporta três: com mais de três selecionados, os três primeiros "
             "da lista são desenhados e os demais são indicados na barra de status. Trocar de disposição não "
             "recarrega nada. Nos dois casos, a base do quadro traz um cartão por instrumento: em letras grandes a "
             "sua **variação no período** e, abaixo, quantos pontos — ou quanto dinheiro — isso foi, o mesmo número "
             "que o rótulo no fim da curva mostra.",
    "pl": "- **Kilka instrumentów może dzielić jeden wykres albo mieć własny.** Przy **Układ** ustawionym na „wykres "
          "dla każdego” każdy instrument dostaje własny panel, jeden pod drugim, z osią skalowaną do własnego zakresu "
          "i linią zera w środku; oś x i daty są wspólne i rysowane raz, pod dolnym panelem. Widok dzielony mieści "
          "trzy, więc przy większej liczbie wybranych rysowane są trzy pierwsze z listy, a pozostałe są wymienione na "
          "pasku stanu. Przełączanie układów niczego nie pobiera ponownie. W obu układach na dole kadru jest jedna "
          "karta na instrument: dużymi cyframi jego **zmiana w okresie**, a pod nią, o ile punktów — albo o ile "
          "pieniędzy — się ruszył; ta sama liczba, którą pokazuje etykieta na końcu jego krzywej.",
    "cs": "- **Několik nástrojů může sdílet jeden graf, nebo mít každý svůj.** Při **Rozvržení** nastaveném na „graf "
          "pro každý” dostane každý nástroj vlastní panel, pod sebou, s osou škálovanou na vlastní rozsah a s nulovou "
          "linií uvnitř; osa x a data jsou společné a kreslí se jednou, pod spodním panelem. Dělené zobrazení zvládne "
          "tři, takže při více než třech vybraných se kreslí první tři v pořadí seznamu a zbytek se vypíše ve stavovém "
          "řádku. Přepnutí mezi oběma rozvrženími nic nenačítá znovu. V obou případech je dole v rámu jedna karta na "
          "nástroj: velkým písmem jeho **změna za období** a pod ní, o kolik bodů — nebo o kolik peněz — se pohnul; "
          "stejné číslo, jaké ukazuje popisek na konci jeho křivky.",
    "ru": "- **Несколько инструментов могут делить один график или получить по графику.** При параметре **Раскладка** "
          "«по графику на инструмент» каждый инструмент занимает свою панель, друг под другом, со своей осью, "
          "масштабированной по своему диапазону, и нулевая линия остаётся внутри; ось X и даты общие и рисуются "
          "один раз — под нижней панелью. Раскладка вмещает три, поэтому при выборе больше трёх рисуются первые три "
          "по списку, остальные перечисляются в строке состояния. Переключение раскладок ничего не перезагружает. "
          "В любом случае внизу кадра по карточке на инструмент: крупно его **изменение за период**, а под ним — на "
          "сколько пунктов (или на сколько денег) он сдвинулся; то же число, что и на метке в конце его кривой.",
    "tr": "- **Birçok enstrüman tek bir grafiği paylaşabilir ya da her biri kendi grafiğini alabilir.** **Yerleşim** "
          "«her biri için bir grafik» olduğunda her enstrüman alt alta bir panel alır; kendi aralığına göre "
          "ölçeklenmiş bir dikey ekseni olur ve sıfır çizgisi panelin içinde kalır. Yatay eksen ve tarihler ortaktır, "
          "tarihler yalnızca en alttaki panelin altına bir kez çizilir. Bölünmüş yerleşim üç panel alır: üçten fazla "
          "seçilirse listedeki ilk üç enstrüman çizilir, kalanlar durum çubuğunda belirtilir. İki yerleşim arasında "
          "geçmek hiçbir şeyi yeniden indirmez. Her iki durumda da karenin altında her enstrüman için bir kart olur: "
          "büyük yazıyla **aralıktaki değişimi**, altında kaç puan (ya da ne kadar para) hareket ettiği — eğrisinin "
          "ucundaki etiketin gösterdiği sayının aynısı.",
}


def insert(block, tag):
    """把这一条插进「比较」那条后面。锚找不到、或者这一条已经在，都抛。"""
    at = [i for i, text in enumerate(block) if ANCHOR[tag] in text]

    if len(at) != 1:
        raise AssertionError(
            f"{tag}: 以锚点收尾的 bullet 有 {len(at)} 条，应当是 1 条。"
            "锚是上一轮写进这一章的那句，找不到就说明它被改过或换了行 —— 不能猜。")

    after = at[0] + 1

    if any(NEW[tag][:40] in text for text in block):
        raise AssertionError(f"{tag}: 这一条已经在章里（幂等那一步没接住）")

    return block[:after] + [NEW[tag]] + block[after:]


def main():
    for tag in lt.LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)
        block = lines[starts[CHAPTER]:end]

        if any(NEW[tag][:40] in text for text in block):
            print(f"{tag:9} already there")
            continue

        lines[starts[CHAPTER]:end] = insert(block, tag)

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))
        print(f"{tag:9} written")


if __name__ == "__main__":
    main()
