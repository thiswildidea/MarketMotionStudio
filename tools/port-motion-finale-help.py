# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的三个「推进方式」章节各补一条：滚动的窗口在收尾时展开成整段。

**为什么非说不可**：滚动回答的是「当时长什么样」，而动画停在的那一帧要回答「整段长什么样」。
现在收尾段会把窗口拉开成整段，于是「窗口滚动」这一项的意思变成「过程看窗口、结尾看整段」——
不看说明，用户会以为是自己把窗口调错了，或者以为动画被截断了。

**只加一条，不改原来那条**：原来那条讲的是两种走法看同一份数据、切换不重新取数，那些都还对；
这一条讲的是结尾，独立成条更清楚，也免得动 14 份里已经定稿的句子。

**定位两条腿，缺一条就炸**：

* 章节号用 `listingtext.chapter_of(key)`，**不写死** —— 章节顺序就是导航顺序，往导航中间插一页，
  后面每一章整体后移，写死的序号会把这一条安到别的页头上，14 份全错而每句都通顺。
* 章节内找**含「窗口」那一条**：三页里「推进方式」这一条是唯一提到窗口的。关键词按语言给
  （`WINDOW`），找不到或找到多条就 `assert` 失败 —— 静默插到错处比报错糟得多。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符。

用法：python tools\port-motion-finale-help.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

# 三页：K线走势、定投计划、持仓收益。
PAGES = ["NavCandle", "NavDcaPlan", "NavPosition"]

# 各语言里「窗口」那个词。用来在章节里认出「推进方式」那一条 —— 三页里只有它提到窗口。
WINDOW = {
    "en-US": ["window", "scroll"],
    "de": ["Fenster"],
    "es": ["ventana"],
    "fr": ["fenêtre"],
    "it": ["finestra"],
    "pl": ["okn"],
    "pt-BR": ["janela"],
    "cs": ["okn"],
    "tr": ["pencere"],
    "ru": ["окн"],
    # 日语这一条写的是「窓」而不是「ウィンドウ」—— 全篇另一处还用过「ウィンドウ」，两个
    # 词都列着，但在这一章里只有那一条会命中。
    "ja": ["窓", "ウィンドウ"],
    "ko": ["창"],
    "zh-Hans": ["窗口"],
    "zh-Hant": ["視窗", "窗口"],
}

OPENING = {
    "en-US": "- **A scrolling window opens out at the end.** As the closing stretch begins the "
             "window widens back towards the first day of the range, so the frame the animation "
             "stops on is the whole span rather than the last few dozen days of it.",

    "de": "- **Ein rollendes Fenster öffnet sich am Ende.** Mit Beginn des Schlussteils weitet "
          "sich das Fenster zurück bis zum ersten Tag des Zeitraums, also steht am Ende der "
          "Animation der ganze Zeitraum da und nicht nur seine letzten Dutzend Tage.",

    "es": "- **Una ventana deslizante se abre al final.** Al empezar el tramo de cierre la ventana "
          "se ensancha hacia atrás hasta el primer día del rango, así que el fotograma en el que "
          "se detiene la animación es el rango completo y no sus últimas decenas de días.",

    "fr": "- **Une fenêtre défilante s'ouvre à la fin.** Au début du segment de fermeture la "
          "fenêtre s'élargit vers l'arrière jusqu'au premier jour de la plage : l'image sur "
          "laquelle l'animation s'arrête est donc la plage entière et non ses dernières "
          "dizaines de jours.",

    "it": "- **Una finestra scorrevole si apre alla fine.** All'inizio del tratto di chiusura la "
          "finestra si allarga all'indietro fino al primo giorno dell'intervallo, quindi il "
          "fotogramma su cui l'animazione si ferma è l'intervallo intero e non le sue ultime "
          "decine di giorni.",

    "pl": "- **Przesuwne okno otwiera się na końcu.** Wraz z początkiem końcowego odcinka okno "
          "rozszerza się wstecz aż do pierwszego dnia zakresu, więc klatka, na której animacja "
          "się zatrzymuje, pokazuje cały zakres, a nie jego ostatnie kilkadziesiąt dni.",

    "pt-BR": "- **Uma janela rolante se abre no final.** No início do trecho de encerramento a "
             "janela se alarga para trás até o primeiro dia do intervalo, portanto o quadro em "
             "que a animação para é o intervalo inteiro, e não suas últimas dezenas de dias.",

    "cs": "- **Posuvné okno se na konci otevře.** Se začátkem závěrečného úseku se okno rozšíří "
          "zpět až k prvnímu dni rozsahu, takže snímek, na kterém animace skončí, je celý "
          "rozsah, nikoli jeho poslední několik desítek dnů.",

    "tr": "- **Kayan pencere sonda açılır.** Kapanış bölümü başlarken pencere geriye doğru, "
          "aralığın ilk gününe kadar genişler; böylece animasyonun durduğu kare son birkaç "
          "on günü değil, aralığın tamamını gösterir.",

    "ru": "- **Прокручиваемое окно в конце раскрывается.** С началом заключительного отрезка окно "
          "расширяется назад, к первому дню диапазона, поэтому кадр, на котором анимация "
          "останавливается, — это весь диапазон, а не его последние несколько десятков дней.",

    "ja": "- **スクロールするウィンドウは最後に開きます。** 終盤に入るとウィンドウは区間の初日まで"
          "後ろへ広がるので、アニメーションが止まるフレームは最後の数十日ではなく区間全体に"
          "なります。",

    "ko": "- **스크롤 창은 마지막에 펼쳐집니다.** 마무리 구간이 시작되면 창이 구간의 첫날까지 "
          "뒤로 넓어지므로, 애니메이션이 멈추는 프레임은 마지막 수십 일이 아니라 구간 "
          "전체입니다.",

    "zh-Hans": "- **窗口滚动的那个窗口会在收尾时展开成整段**：进入收尾段，窗口一路退回区间的第一天，"
               "所以动画停下的那一帧是整个区间，不是最后那几十天。",

    "zh-Hant": "- **視窗滾動的那個視窗會在收尾時展開成整段**：進入收尾段，視窗一路退回區間的第一天，"
               "所以動畫停下的那一幀是整個區間，不是最後那幾十天。",
}


def main():
    chapters = [lt.chapter_of(key) for key in PAGES]

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

        # 从后往前插，前面插进去的行不会挪动后面章节的位置。
        inserted = 0

        for chapter in sorted(chapters, reverse=True):
            assert chapter < len(starts), f"{tag}: {len(starts)} chapters, need {chapter + 1}"

            start = starts[chapter]
            end = starts[chapter + 1] if chapter + 1 < len(starts) else len(lines)

            block = lines[start:end]

            if any(line.strip() == OPENING[tag] for line in block):
                continue

            hits = [i for i, line in enumerate(block)
                    if line.startswith("- ") and any(w in line for w in WINDOW[tag])]

            assert len(hits) == 1, (
                f"{tag} chapter {chapter}: {len(hits)} entries mention the window, expected 1")

            at = hits[0] + 1
            block = block[:at] + [OPENING[tag]] + block[at:]

            lines[start:end] = block
            inserted += 1

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +{inserted}")


if __name__ == "__main__":
    main()
