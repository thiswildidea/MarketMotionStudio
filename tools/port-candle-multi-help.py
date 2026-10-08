# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「K 线走势」那一章补一条：这一页也可以选多个标的。

**为什么非说不可**：这一页原本是「一个标的」的页面，清单那一排名字现在成了开关。看不见这条
说明的人只会看到一件事 —— 打开第二个标的之后蜡烛图不见了，换成几条曲线。不给理由，那就是
一个把图画坏的开关。

**为什么按章节号定位**：`listingtext.chapter_of("NavCandle")` 从导航顺序算，导航顺序就是章节
顺序。写 14 个语言的标题字符串就是 14 处会失配的地方。

**不引用任何控件名字**：复选框、下拉框的名字在 14 种语言里各不相同，抄错一处就是一句指着不
存在的控件的说明。这条只说这个开关在做什么。

**插在哪**：这一章**第一段连续的 `- ` 列表的末尾**。这一章的列表是完整的一段，末尾就是
「Range」那条之后。

**重音字母照写。** 德语的 ä/ö/ü、法语的 é/è/ç、捷克语的 ř/ž/ů、土耳其语的 ğ/ı/ş、俄语的
я/ё 都是这个字的一部分，不是装饰；为了「保险」写成 a/o/u/e/c/r/z/g/i/s 等于在应用里挂一句
拼错的外语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM。

幂等：这一章里已经有这一条就跳过。

用法：<venv python> tools/port-candle-multi-help.py      （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP
CHAPTER = lt.chapter_of("NavCandle")

LINE = {
    "en-US": "- **Two or more instruments turn the frame into a comparison.** The names on your "
             "list are switches: turn a second one on and the frame stops drawing candles, because "
             "two instruments' prices have no axis they can share, and draws what each of them did "
             "as a cumulative percentage instead — every curve named at its own leading end, with "
             "how far ahead or behind it is at the moment being shown. On the minute periods all of "
             "them are drawn on one trading day: the newest session every one of them has.",
    "de": "- **Zwei oder mehr Instrumente machen aus dem Bild einen Vergleich.** Die Namen auf "
          "deiner Liste sind Schalter: Schalte ein zweites ein und das Bild zeichnet keine Kerzen "
          "mehr — die Preise zweier Instrumente haben keine Achse, die sie teilen könnten —, "
          "sondern was jedes von ihnen getan hat, als aufgelaufenen Prozentwert. Jede Kurve ist an "
          "ihrem eigenen vorderen Ende beschriftet, mit dem Namen und damit, wie weit sie in dem "
          "gezeigten Moment vorn oder hinten liegt. Bei den Minuten-Perioden werden alle am selben "
          "Handelstag gezeichnet: an der jüngsten Sitzung, die jedes von ihnen hat.",
    "es": "- **Dos instrumentos o más convierten el marco en una comparación.** Los nombres de tu "
          "lista son interruptores: activa un segundo y el marco deja de dibujar velas — los precios "
          "de dos instrumentos no tienen ningún eje que puedan compartir — y dibuja en su lugar lo "
          "que cada uno hizo, como porcentaje acumulado. Cada curva va nombrada en su propio extremo "
          "delantero, con cuánto va por delante o por detrás en el momento mostrado. En los periodos "
          "de minutos todos se dibujan en un mismo día de negociación: la sesión más reciente que "
          "cada uno de ellos tiene.",
    "fr": "- **Deux instruments ou plus font de l'image une comparaison.** Les noms de votre liste "
          "sont des interrupteurs : activez-en un deuxième et l'image cesse de tracer des "
          "chandeliers — les prix de deux instruments n'ont aucun axe à partager — et trace à la "
          "place ce que chacun a fait, en pourcentage cumulé. Chaque courbe est nommée à sa propre "
          "extrémité avant, avec son avance ou son retard au moment affiché. Sur les périodes en "
          "minutes, tous sont tracés le même jour de bourse : la séance la plus récente que chacun "
          "possède.",
    "it": "- **Due o più strumenti trasformano l'inquadratura in un confronto.** I nomi nella tua "
          "lista sono interruttori: attivane un secondo e l'inquadratura smette di disegnare candele "
          "— i prezzi di due strumenti non hanno alcun asse da condividere — e disegna invece ciò che "
          "ciascuno ha fatto, come percentuale cumulata. Ogni curva è nominata alla propria estremità "
          "anteriore, con quanto è avanti o indietro nel momento mostrato. Nei periodi al minuto "
          "tutti sono disegnati nella stessa giornata di borsa: la seduta più recente che ciascuno "
          "ha.",
    "pl": "- **Dwa instrumenty lub więcej zamieniają kadr w porównanie.** Nazwy na twojej liście to "
          "przełączniki: włącz drugą, a kadr przestanie rysować świece — ceny dwóch instrumentów nie "
          "mają żadnej osi, którą mogłyby dzielić — i zamiast tego narysuje to, co każdy z nich "
          "zrobił, jako narastający procent. Każda krzywa jest opisana na własnym przednim końcu: "
          "nazwą oraz tym, o ile jest z przodu lub z tyłu w pokazywanym momencie. W okresach "
          "minutowych wszystkie są rysowane w tym samym dniu sesji: najnowszym, jaki każdy z nich ma.",
    "pt-BR": "- **Dois instrumentos ou mais transformam o quadro em uma comparação.** Os nomes na "
             "sua lista são chaves: ligue um segundo e o quadro para de desenhar candles — os preços "
             "de dois instrumentos não têm nenhum eixo que possam compartilhar — e desenha, em vez "
             "disso, o que cada um fez, como porcentagem acumulada. Cada curva é nomeada na própria "
             "extremidade dianteira, com o quanto está à frente ou atrás no momento mostrado. Nos "
             "períodos de minutos, todos são desenhados no mesmo dia de negociação: a sessão mais "
             "recente que cada um tem.",
    "cs": "- **Dva nebo více nástrojů udělají ze záběru srovnání.** Jména ve tvém seznamu jsou "
          "přepínače: zapni druhý a záběr přestane kreslit svíčky — ceny dvou nástrojů nemají žádnou "
          "osu, kterou by mohly sdílet — a místo toho nakreslí, co každý z nich udělal, jako "
          "kumulativní procento. Každá křivka je pojmenována na svém vlastním předním konci, s tím, "
          "jak je v zobrazovaném okamžiku napřed nebo pozadu. V minutových periodách jsou všechny "
          "nakresleny v jeden obchodní den: v nejnovější seanci, kterou každý z nich má.",
    "tr": "- **İki veya daha fazla enstrüman kareyi karşılaştırmaya çevirir.** Listenizdeki adlar "
          "anahtardır: ikincisini açın ve kare, mum çizmeyi bırakır — iki enstrümanın fiyatının "
          "paylaşabileceği ortak bir eksen yoktur — ve bunun yerine her birinin ne yaptığını birikimli "
          "yüzde olarak çizer. Her eğri, kendi ön ucunda adıyla ve gösterilen anda ne kadar önde ya da "
          "geride olduğuyla etiketlenir. Dakika periyotlarında hepsi tek bir işlem gününde çizilir: "
          "her birinin sahip olduğu en yeni seans.",
    "ru": "- **Два инструмента или больше превращают кадр в сравнение.** Имена в вашем списке — это "
          "переключатели: включите второй, и кадр перестанет рисовать свечи — у цен двух инструментов "
          "нет оси, которую они могли бы делить, — и вместо этого нарисует, что сделал каждый, в виде "
          "накопленного процента. Каждая кривая подписана у собственного переднего конца: название и "
          "то, насколько она впереди или позади в показываемый момент. На минутных периодах все они "
          "рисуются в один торговый день — в самую свежую сессию, которая есть у каждого.",
    "ja": "- **銘柄を二つ以上選ぶと、画面は比較になります。** リストの名前はスイッチです。二つ目"
          "をオンにすると、二つの銘柄の価格には共有できる軸がないため、画面はローソク足を描くのを"
          "やめ、それぞれが何をしたかを累積パーセントで描きます。各曲線は自分の先頭の端で、名前と、"
          "表示されている時点でどれだけ先行または遅れているかを示します。分足の期間では、すべてが"
          "一つの売買日に描かれます。それぞれが持つ最新のセッションです。",
    "ko": "- **종목을 두 개 이상 선택하면 화면이 비교로 바뀝니다.** 목록의 이름은 스위치입니다. 두 "
          "번째를 켜면 두 종목의 가격에는 함께 쓸 수 있는 축이 없으므로 화면은 캔들 그리기를 멈추고, "
          "대신 각각이 무엇을 했는지를 누적 백분율로 그립니다. 각 곡선은 자신의 선두 끝에서 이름과, "
          "표시되는 시점에 얼마나 앞서거나 뒤처지는지를 보여줍니다. 분 단위 기간에서는 모두가 하나의 "
          "거래일에 그려집니다. 각각이 가진 가장 최근 세션입니다.",
    "zh-Hans": "- **选两个以上标的，画面就变成比较。** 清单里的名字是开关：打开第二个，两个标的的"
               "价格没有能共用的轴，画面就不再画蜡烛，改画各自做了什么 —— 累计涨跌幅。每条曲线在自"
               "己的前端标着名字，以及画面上这一刻它领先或落后多少。分钟周期下所有的标的画在同一个"
               "交易日上：它们各自都有的最近一个完整交易日。",
    "zh-Hant": "- **選兩個以上標的，畫面就變成比較。** 清單裡的名字是開關：打開第二個，兩個標的的"
               "價格沒有能共用的軸，畫面就不再畫蠟燭，改畫各自做了什麼 —— 累計漲跌幅。每條曲線在自"
               "己的前端標著名字，以及畫面上這一刻它領先或落後多少。分鐘週期下所有的標的畫在同一個"
               "交易日上：它們各自都有的最近一個完整交易日。",
}


def insert(block, line):
    """Return `block` with `line` appended to its first contiguous bullet run."""
    runs = []
    run = []

    for i, text in enumerate(block):
        if text.startswith("- "):
            run.append(i)
        elif run:
            runs.append(run)
            run = []

    if run:
        runs.append(run)

    if not runs:
        raise AssertionError("this chapter has no bullet list")

    at = runs[0][-1] + 1

    return block[:at] + [line] + block[at:]


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

        if any(line.strip() == LINE[tag] for line in block):
            print(f"{tag:9} already there")
            continue

        lines[starts[CHAPTER]:end] = insert(block, LINE[tag])

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))
        print(f"{tag:9} written")


if __name__ == "__main__":
    main()
