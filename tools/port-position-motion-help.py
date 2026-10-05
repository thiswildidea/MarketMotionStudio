# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「持仓收益」那一章补上两种推进方式。

这一页跟 K 线页一样多了「整段铺满 / 窗口滚动」与只在滚动时有意义的窗口天数，而界面上
看不出两件事，所以它们要写进帮助：

* **为什么要有第二种。** 十二年铺满一屏时，一次三个月的回落只有两个像素 —— 窗口滚动
  是唯一能把长期日线看得清起落的走法。
* **切换不重新取数。** 两种走法看的是同一份数据，这是「显示方式」与「参数」的区别。

**章节序号不写死**：用 `listingtext.chapter_of("NavPosition")` 读导航顺序算出来（实测
18）。往导航中间插一页，后面每章 +1，写死序号会让说明挂到错章头上，14 语言全错而每句
都通顺 —— `port-custom-range-help.py` 里的 `PLAN = 8` / `HOLDING = 9` 就是那个年代
写死的，早就不对了。

**插入位置**：该章**最后一条**条目之后。追加到末尾是为幂等：位置只由「本章最后一条」
决定，不受前面插了几条的影响。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在
diff 里表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-position-motion-help.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

sys.path.insert(0, str(HERE))

import listingtext  # noqa: E402

CHAPTER = listingtext.chapter_of("NavPosition")

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]

NOTE = {
    "en-US": "- **Two motions.** *Grow across the span* lays the whole range down at once, so the "
             "curve's shape on screen is its shape in time. *Scroll a window* holds a window of a "
             "fixed number of trading days and walks it from the start of the range to its end — "
             "the only way a long daily series keeps its wobbles readable, since spread over "
             "twelve years a three-month fall is two pixels. The window only counts while "
             "scrolling, and both motions read **the same marks**: switching re-fetches nothing.",

    "de": "- **Zwei Ablaufarten.** *Über die ganze Spanne* legt den gesamten Zeitraum auf einmal "
          "hin, die Kurve zeigt also ihre echte Form über die Zeit. *Fenster weiterbewegen* hält "
          "ein Fenster aus einer festen Zahl von Handelstagen und schiebt es vom Anfang bis zum "
          "Ende des Zeitraums — nur so bleiben die Ausschläge einer langen Tagesreihe lesbar: über "
          "zwölf Jahre verteilt sind drei Monate Rückgang zwei Pixel. Das Fenster zählt nur beim "
          "Weiterbewegen, und beide Arten lesen **dieselben Kurse** — Umschalten lädt nichts neu.",

    "es": "- **Dos modos de avance.** *Crecer por todo el periodo* despliega todo el intervalo de "
          "una vez, así que la forma de la curva en pantalla es su forma en el tiempo. *Desplazar "
          "una ventana* mantiene una ventana de un número fijo de días de cotización y la recorre "
          "desde el inicio hasta el fin del intervalo: es la única forma de que una serie diaria "
          "larga conserve legibles sus oscilaciones, porque repartida en doce años una caída de "
          "tres meses son dos píxeles. La ventana solo cuenta al desplazar, y ambos modos leen "
          "**los mismos datos**: cambiar no vuelve a descargar.",

    "fr": "- **Deux animations.** *Tracer tout l'intervalle* déploie toute la période d'un coup : "
          "la forme de la courbe à l'écran est sa forme dans le temps. *Fenêtre glissante* garde "
          "une fenêtre d'un nombre fixe de jours de cotation et la fait avancer du début à la fin "
          "de la période — c'est le seul moyen de garder lisibles les oscillations d'une longue "
          "série quotidienne : étalée sur douze ans, une baisse de trois mois fait deux pixels. La "
          "fenêtre ne compte qu'en défilement, et les deux animations lisent **les mêmes "
          "données** : en changer ne recharge rien.",

    "it": "- **Due animazioni.** *Tutto l'intervallo* dispiega l'intero periodo in una volta, "
          "quindi la forma della curva sullo schermo è la sua forma nel tempo. *Finestra "
          "scorrevole* mantiene una finestra di un numero fisso di giorni di contrattazione e la "
          "fa avanzare dall'inizio alla fine del periodo: è l'unico modo perché una lunga serie "
          "giornaliera resti leggibile nei suoi movimenti, perché distribuita su dodici anni una "
          "discesa di tre mesi sono due pixel. La finestra conta solo nello scorrimento, ed "
          "entrambe le animazioni leggono **gli stessi dati**: cambiare non ricarica nulla.",

    "pl": "- **Dwa tryby animacji.** *Cały zakres naraz* rozkłada cały okres za jednym razem, więc "
          "kształt krzywej na ekranie to jej kształt w czasie. *Przesuwne okno* utrzymuje okno o "
          "stałej liczbie dni sesyjnych i przesuwa je od początku do końca okresu — tylko tak "
          "długa seria dzienna zachowuje czytelne wahania: rozłożona na dwanaście lat, "
          "trzymiesięczny spadek to dwa piksele. Okno liczy się tylko przy przewijaniu, a oba "
          "tryby czytają **te same dane** — przełączenie nic nie pobiera ponownie.",

    "pt-BR": "- **Dois modos de avanço.** *Todo o período* dispõe o intervalo inteiro de uma vez, "
             "então a forma da curva na tela é a sua forma no tempo. *Janela deslizante* mantém "
             "uma janela de um número fixo de dias de negociação e a percorre do início ao fim do "
             "intervalo — é a única forma de uma longa série diária manter as oscilações "
             "legíveis, porque espalhada por doze anos uma queda de três meses são dois pixels. A "
             "janela só conta ao deslizar, e os dois modos leem **os mesmos dados**: trocar não "
             "baixa nada de novo.",

    "cs": "- **Dva způsoby animace.** *Celé období* rozloží celý rozsah najednou, takže tvar "
          "křivky na obrazovce je její tvar v čase. *Posuvné okno* drží okno s pevným počtem "
          "obchodních dnů a posouvá je od začátku do konce rozsahu — jen tak zůstanou výkyvy "
          "dlouhé denní řady čitelné, protože rozložená na dvanáct let jsou tři měsíce poklesu "
          "dva pixely. Okno má význam jen při posouvání a oba způsoby čtou **stejné kurzy** — "
          "přepnutí nic nenačítá.",

    "tr": "- **İki ilerleme biçimi.** *Aralığın tamamı* tüm dönemi bir anda serer; eğrinin "
          "ekrandaki biçimi, zamandaki biçimidir. *Kayan pencere* sabit sayıda işlem gününden "
          "oluşan bir pencereyi aralığın başından sonuna kadar yürütür — uzun bir günlük serinin "
          "dalgalanmalarını okunur tutmanın tek yolu budur, çünkü on iki yıla yayılmış üç aylık "
          "bir düşüş iki pikseldir. Pencere yalnızca kaydırırken anlam taşır ve iki biçim de "
          "**aynı fiyatları** okur — geçiş yeniden veri çekmez.",

    "ru": "- **Два способа продвижения.** «Весь диапазон» раскладывает весь период сразу, поэтому "
          "форма кривой на экране — это её форма во времени. «Скользящее окно» держит окно из "
          "фиксированного числа торговых дней и ведёт его от начала периода к концу — только так "
          "у длинного дневного ряда колебания остаются читаемыми: растянутые на двенадцать лет, "
          "три месяца падения — это два пикселя. Окно имеет смысл только при прокрутке, и оба "
          "способа читают **одни и те же цены** — переключение ничего не загружает заново.",

    "ja": "- **2 つの進行方式。**「全区間を描く」は期間全体を一度に敷き詰めるので、画面の曲線の形が"
          "そのまま時間の中での形になります。「窓をスクロール」は一定の営業日数の窓を期間の先頭から"
          "末尾まで動かします——長い日次系列の揺れを読める形で保つにはこれしかありません。12 年に"
          "広げると、3 か月の下落は 2 ピクセルです。窓はスクロール時だけ意味を持ち、どちらも"
          "**同じデータ**を読むので、切り替えても再取得はしません。",

    "ko": "- **두 가지 진행 방식.** *전체 구간 그리기*는 기간 전체를 한 번에 펼치므로 화면의 곡선 "
          "모양이 곧 시간 속의 모양입니다. *창 이동*은 고정된 거래일 수의 창을 기간 처음부터 끝까지 "
          "밀어 갑니다 — 긴 일별 계열의 흔들림을 읽을 수 있게 유지하는 유일한 방법입니다. 12년에 "
          "펼치면 3개월 하락은 2픽셀입니다. 창은 이동할 때만 의미가 있고, 두 방식 모두 **같은 "
          "데이터**를 읽으므로 전환해도 다시 받지 않습니다.",

    "zh-Hans": "- **两种推进方式**：「整段铺满」把整段区间一次铺开，曲线的形状就是它在时间里的形状；"
               "「窗口滚动」拿一个固定天数的窗口，从区间起点走到终点——日线的长期走势只有这样才能看"
               "得出起伏，十二年铺满一屏，一次三个月的回落只有两个像素。窗口只在滚动时有效；两种"
               "走法看的是**同一份数据**，切换不会重新取数。",

    "zh-Hant": "- **兩種推進方式**：「整段鋪滿」把整段區間一次鋪開，曲線的形狀就是它在時間裡的形狀；"
               "「視窗滾動」拿一個固定天數的視窗，從區間起點走到終點——日線的長期走勢只有這樣才能"
               "看得出起伏，十二年鋪滿一屏，一次三個月的回落只有兩個像素。視窗只在滾動時有效；"
               "兩種走法看的是**同一份資料**，切換不會重新取數。",
}


def main():
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")

        # Chapters open on a "## " line, and their position among those is the navigation order.
        # Spliced as lines rather than rebuilt from a split on the heading: putting a split back
        # together has to reproduce the newline the split ate, and getting that wrong rewrites
        # every heading in fourteen files.
        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        assert len(starts) > CHAPTER, f"{tag}: {len(starts)} chapters, need {CHAPTER + 1}"

        start = starts[CHAPTER]
        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)

        chapter = lines[start:end]

        # Idempotent: the entry is there already, so this chapter has been done.
        if any(line.strip() == NOTE[tag] for line in chapter):
            print(f"{tag:9} already there")
            continue

        bullets = [i for i, line in enumerate(chapter) if line.startswith("- ")]

        assert bullets, f"{tag}: no bullet in the holding chapter"

        at = bullets[-1] + 1
        lines[start:end] = chapter[:at] + [NOTE[tag]] + chapter[at:]

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1 bullet")


if __name__ == "__main__":
    main()
