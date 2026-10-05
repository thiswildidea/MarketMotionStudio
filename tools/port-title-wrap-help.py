# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「视频」那一章补一条：标题可以换行。

**为什么非说不可**：标题以前是一行、放不下就缩字号；现在是折行，而且折出第二行会把下面
整个画面往下挪一行、图表跟着变矮。这两件事都会让用户看到「画面和上次不一样了」——
不看说明，很容易以为是自己把边距调坏了。

**为什么不能按章节序号定位**：这一章不是某一页的说明，`listingtext.chapter_of` 够不着它
（它只认导航里的页面）。所以按**标题文本**认（每语言一条，`HEADING`），并且要求**恰好命中
一章** —— 标题被改写过就会当场炸，而不是静静地把这一条插进别的章里。这一章在 14 种语言里
都排在「持仓收益」之后、「视频存到哪里」之前，位置没写死，靠文本认。

**插在哪**：这一章末尾（最后一条 `- ` 之后）。原来三条讲时长、边距、安全区参考线，都对
仍然对；新的一条讲标题，独立成条更清楚，也免得动 14 份里已经定稿的句子。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符。

用法：python tools\port-title-wrap-help.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

# 「视频」这一章的标题文本，14 种语言。认出它、并且只认出一个。
HEADING = {
    "en-US": "## Video",
    "de": "## Video",
    "es": "## Vídeo",
    "fr": "## Vidéo",
    "it": "## Video",
    "pl": "## Film",
    "pt-BR": "## Vídeo",
    "cs": "## Video",
    "tr": "## Video",
    "ru": "## Видео",
    "ja": "## 動画",
    "ko": "## 영상",
    "zh-Hans": "## 视频",
    "zh-Hant": "## 影片",
}

ENTRY = {
    "en-US": "- The title can be more than one line: press Enter in the title box to break it "
             "where you want. A title too wide for one line wraps onto a second, two lines at "
             "most; only when two still will not hold it does the size give way. A second line "
             "pushes everything below it down by one row, so the chart is that much shorter.",

    "de": "- Der Titel darf mehrzeilig sein: Mit der Eingabetaste im Titelfeld brechen Sie ihn "
          "dort, wo er brechen soll. Passt er nicht in eine Zeile, läuft er automatisch in eine "
          "zweite um – höchstens zwei Zeilen; erst wenn auch zwei nicht reichen, gibt die "
          "Schriftgröße nach. Eine zweite Zeile schiebt alles darunter um eine Zeile nach unten, "
          "das Diagramm wird entsprechend kürzer.",

    "es": "- El título puede ocupar varias líneas: pulsa Intro en el campo del título para "
          "partirlo donde quieras. Si no cabe en una línea, se ajusta solo a una segunda, dos como "
          "máximo; solo cuando dos tampoco bastan cede el tamaño de letra. Una segunda línea "
          "empuja hacia abajo una fila todo lo que hay debajo, así que el gráfico se acorta en esa "
          "medida.",

    "fr": "- Le titre peut tenir sur plusieurs lignes : appuyez sur Entrée dans le champ du titre "
          "pour le couper où vous voulez. S'il ne tient pas sur une ligne, il se replie sur une "
          "deuxième, deux au maximum ; ce n'est que si deux ne suffisent pas que la taille cède. "
          "Une deuxième ligne décale d'une ligne tout ce qui suit, et le graphique raccourcit "
          "d'autant.",

    "it": "- Il titolo può stare su più righe: premi Invio nel campo del titolo per spezzarlo dove "
          "vuoi. Se non entra in una riga va a capo da solo su una seconda, due al massimo; solo "
          "quando nemmeno due bastano cede la dimensione del carattere. Una seconda riga sposta di "
          "una riga tutto ciò che sta sotto, e il grafico si accorcia di conseguenza.",

    "pl": "- Tytuł może mieć więcej niż jedną linię: w polu tytułu naciśnij Enter, aby złamać go "
          "tam, gdzie chcesz. Jeśli nie mieści się w jednej linii, sam przechodzi do drugiej — "
          "najwyżej dwóch; dopiero gdy i dwie nie wystarczą, maleje stopień pisma. Druga linia "
          "przesuwa wszystko poniżej o jeden wiersz, więc wykres jest o tyle niższy.",

    "pt-BR": "- O título pode ter mais de uma linha: pressione Enter no campo do título para "
             "quebrá-lo onde quiser. Se não couber em uma linha, ele quebra sozinho em uma segunda, "
             "no máximo duas; só quando duas também não bastam é que o tamanho cede. Uma segunda "
             "linha empurra uma linha para baixo tudo o que vem depois, e o gráfico fica mais baixo "
             "na mesma medida.",

    "cs": "- Titulek může být na více řádcích: v poli titulku stiskněte Enter a zlomte ho tam, kde "
          "chcete. Když se nevejde na jeden řádek, zalomí se sám na druhý, nejvýše na dva; teprve "
          "když ani dva nestačí, ustoupí velikost písma. Druhý řádek posune vše pod ním o jeden "
          "řádek dolů, takže graf je o tolik nižší.",

    "tr": "- Başlık birden çok satır olabilir: başlık kutusunda Enter'a basarak istediğiniz yerden "
          "kırın. Tek satıra sığmazsa kendiliğinden ikinci satıra kayar, en fazla iki satır; iki "
          "satır da yetmezse yazı boyutu küçülür. İkinci satır altındaki her şeyi bir satır aşağı "
          "iter, grafik de o kadar kısalır.",

    "ru": "- Заголовок может занимать несколько строк: нажмите Enter в поле заголовка, чтобы "
          "разорвать его там, где нужно. Если он не помещается в одну строку, он сам переносится "
          "на вторую — не более двух; и только если и двух не хватает, уступает размер шрифта. "
          "Вторая строка сдвигает всё под ней на одну строку вниз, и график на столько же "
          "укорачивается.",

    "ja": "- タイトルは複数行にできます。タイトル欄で Enter を押せば、好きな位置で改行できます。"
          "1 行に収まらないときは画面幅に合わせて自動で 2 行目に折り返し、最大 2 行。2 行でも"
          "収まらないときだけ文字サイズが小さくなります。2 行目が出ると、その下の内容が 1 行分"
          "下がり、グラフはその分だけ低くなります。",

    "ko": "- 제목은 여러 줄이 될 수 있습니다. 제목 상자에서 Enter를 눌러 원하는 곳에서 줄을 "
          "바꾸세요. 한 줄에 들어가지 않으면 화면 너비에 맞춰 자동으로 두 번째 줄로 접히며 최대 "
          "두 줄까지입니다. 두 줄로도 부족할 때만 글자 크기가 줄어듭니다. 두 번째 줄이 생기면 "
          "아래 내용이 한 줄만큼 내려가고 그래프는 그만큼 낮아집니다.",

    "zh-Hans": "- 标题文字可以写多行：标题框里按回车就能手动断行。一行放不下时按画面宽度自动折成"
               "第二行，最多折两行；两行还放不下才按比例缩小字号。折出第二行时，下面的内容整体下移"
               "一行，图表相应变矮。",

    "zh-Hant": "- 標題文字可以寫多行：在標題框裡按 Enter 就能手動斷行。一行放不下時會按畫面寬度"
               "自動折成第二行，最多折兩行；兩行還放不下才按比例縮小字級。折出第二行時，下面的內容"
               "整體下移一行，圖表也跟著變矮。",
}


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

        heads = [i for i in starts if lines[i].strip() == HEADING[tag]]

        assert len(heads) == 1, (
            f"{tag}: {len(heads)} chapters headed {HEADING[tag]!r}, expected exactly one")

        chapter = starts.index(heads[0])
        end = starts[chapter + 1] if chapter + 1 < len(starts) else len(lines)

        start = heads[0]
        block = lines[start:end]

        if any(line.strip() == ENTRY[tag] for line in block):
            print(f"{tag:9} already there")
            continue

        bullets = [i for i, line in enumerate(block) if line.startswith("- ")]

        assert bullets, f"{tag}: the video chapter has no bullet list"

        at = bullets[-1] + 1
        lines[start:end] = block[:at] + [ENTRY[tag]] + block[at:]

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
