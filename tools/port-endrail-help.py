# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「视频」那一章补一条：末端标注不会进入平台的按钮栏。

**为什么非说不可**：定投、持仓收益、市值历程三页的图表**右边会空出一条**，而且曲线不再
铺满整幅宽 —— 不看说明，很容易以为是自己把右边距调坏了。它其实是一直都在那里的东西：
竖屏视频右侧那条带子里是平台自己的头像、点赞和评论按钮，而画图的人看不到它。

这一条也顺手把「安全区参考线」那条从天真的说法里拉回来：参考线以前只是**画出来**给作者
看，右边那条从来没有被任何一页让过。

**为什么不能按章节序号定位**：这一章不是某一页的说明，`listingtext.chapter_of` 够不着它
（它只认导航里的页面）。所以按**标题文本**认（每语言一条，`HEADING`），并且要求**恰好命中
一章** —— 标题被改写过就会当场炸，而不是静静地把这一条插进别的章里。

**插在哪**：这一章**第一段连续的 `- ` 列表的末尾**（也就是「标题换行」那条之后、与下面
「免费/订阅」那条之间的空行之前）。不能照抄 `port-title-wrap-help.py` 的 `bullets[-1]`：
那个写法当时是对的，但那之后订阅那次又往章末补了一条 —— 现在 `bullets[-1]` 是订阅那条，
按它插会把版面的事插到收费那段后面去。不按语言写锚点，是因为这 14 份里那几条的句子各不
相同，写 14 个锚点就是 14 处会失配的地方。

**重音字母照写。** 德语的 ä/ö/ü、法语的 é/è/ç、捷克语的 ř/ž/í、土耳其语的 ğ/ı/ş、罗马尼亚
没有、俄语的 я/ё 都是这个字的一部分，不是装饰；为了「保险」写成 a/o/u/e/c/r/z/g/i/s 等于在
应用里挂一句拼错的外语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符。

幂等：先看这一章里有没有这一条，有就跳过。

用法：python tools\port-endrail-help.py      （跑第二遍应当是 14 个 already there）
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
    "en-US": "- **The name and the figure at a line's end stop short of the platform's own "
             "interface.** A phone app draws its avatar and its like and comment buttons down the "
             "right-hand side of a vertical video, so the plotting area ends before the frame's "
             "right edge and the live point of a curve — with the name and the figure riding it — "
             "comes to rest to the left of that band. The chart is narrower than the frame, and "
             "that is why.",

    "de": "- **Name und Zahl am Ende einer Linie halten Abstand von der Oberfläche der "
          "Plattform.** Eine Telefon-App zeichnet ihr Profilbild sowie die Schaltflächen für "
          "„Gefällt mir“ und Kommentare an die rechte Seite eines Hochformatvideos; deshalb endet "
          "die Zeichenfläche vor dem rechten Bildrand, und der aktuelle Punkt einer Kurve – samt "
          "Name und Zahl – kommt links von diesem Streifen zur Ruhe. Das Diagramm ist schmaler "
          "als das Bild, und das ist der Grund.",

    "es": "- **El nombre y la cifra al final de una línea se detienen antes de la interfaz de la "
          "plataforma.** Una aplicación de móvil dibuja su avatar y sus botones de «me gusta» y "
          "comentarios en el lado derecho de un vídeo vertical, así que el área de dibujo termina "
          "antes del borde derecho del encuadre y el punto actual de una curva —con el nombre y la "
          "cifra que lo acompañan— queda a la izquierda de esa banda. El gráfico es más estrecho "
          "que el encuadre, y por eso.",

    "fr": "- **Le nom et le chiffre au bout d'une courbe s'arrêtent avant l'interface de la "
          "plateforme.** Une application mobile place son avatar et ses boutons « j'aime » et "
          "commentaire sur le bord droit d'une vidéo verticale ; la zone de tracé s'arrête donc "
          "avant le bord droit de l'image, et le point courant d'une courbe — avec le nom et le "
          "chiffre qui l'accompagnent — se pose à gauche de cette bande. Le graphique est plus "
          "étroit que l'image, et c'est pourquoi.",

    "it": "- **Il nome e il valore in fondo a una linea si fermano prima dell'interfaccia della "
          "piattaforma.** Un'app per telefono disegna il proprio avatar e i pulsanti «mi piace» e "
          "commento sul lato destro di un video verticale, quindi l'area di disegno finisce prima "
          "del bordo destro dell'inquadratura e il punto corrente di una curva — con il nome e il "
          "valore che lo accompagnano — si ferma a sinistra di quella fascia. Il grafico è più "
          "stretto dell'inquadratura, ed è per questo.",

    "pl": "- **Nazwa i liczba na końcu linii zatrzymują się przed interfejsem platformy.** "
          "Aplikacja na telefon rysuje swój awatar oraz przyciski „lubię to” i komentarzy po "
          "prawej stronie pionowego wideo, więc obszar rysowania kończy się przed prawym brzegiem "
          "kadru, a bieżący punkt krzywej — wraz z nazwą i liczbą — zatrzymuje się na lewo od tego "
          "pasa. Wykres jest węższy od kadru i dlatego.",

    "pt-BR": "- **O nome e o número no fim de uma linha param antes da interface da plataforma.** "
             "Um aplicativo de celular desenha o próprio avatar e os botões de curtir e comentar na "
             "lateral direita de um vídeo vertical, então a área de desenho termina antes da borda "
             "direita do quadro e o ponto atual de uma curva — com o nome e o número que o "
             "acompanham — fica à esquerda dessa faixa. O gráfico é mais estreito que o quadro, e é "
             "por isso.",

    "cs": "- **Název a číslo na konci křivky se zastaví před rozhraním platformy.** Aplikace v "
          "telefonu kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů po pravé straně "
          "svislého videa, takže kreslicí plocha končí před pravým okrajem záběru a aktuální bod "
          "křivky — spolu s názvem a číslem — se zastaví vlevo od toho pásu. Graf je užší než "
          "záběr, a proto.",

    "tr": "- **Bir çizginin ucundaki ad ve sayı, platformun kendi arayüzünün önünde durur.** Bir "
          "telefon uygulaması avatarını, beğeni ve yorum düğmelerini dikey videonun sağ kenarına "
          "çizer; bu yüzden çizim alanı karenin sağ kenarından önce biter ve bir eğrinin güncel "
          "noktası — yanındaki ad ve sayıyla birlikte — o şeridin solunda durur. Grafik kareden "
          "dardır ve nedeni budur.",

    "ru": "- **Название и число в конце линии останавливаются перед интерфейсом самой "
          "платформы.** Приложение на телефоне рисует свой аватар и кнопки «нравится» и "
          "комментариев у правого края вертикального видео, поэтому область построения "
          "заканчивается раньше правого края кадра, а текущая точка кривой — вместе с названием и "
          "числом — остаётся левее этой полосы. График уже кадра, и вот почему.",

    "ja": "- **線の末端に付く名前と数値は、プラットフォーム自身の UI の手前で止まります。** "
          "スマートフォンのアプリは縦長動画の右側に、自分のアイコンと「いいね」「コメント」の"
          "ボタンを描きます。そのため描画領域は画面の右端より手前で終わり、曲線の現在の点は"
          "名前と数値ごとその帯の左側に収まります。グラフが画面より狭いのはそのためです。",

    "ko": "- **선 끝에 붙는 이름과 숫자는 플랫폼 자체 인터페이스 앞에서 멈춥니다.** 휴대폰 앱은 "
          "세로 영상의 오른쪽에 자기 아이콘과 좋아요·댓글 버튼을 그립니다. 그래서 그리기 영역은 "
          "화면 오른쪽 끝보다 앞에서 끝나고, 곡선의 현재 점은 이름과 숫자와 함께 그 띠의 왼쪽에 "
          "자리합니다. 그래프가 화면보다 좁은 것은 그 때문입니다.",

    "zh-Hans": "- **曲线末端那个名字和数字不会进入平台自己的界面**：手机应用会把头像、点赞和评论"
               "按钮画在竖屏视频的右侧，所以绘图区在画面右缘之前就结束，曲线的实时点连同它的名字"
               "与数字都落在那一条带的左边。图表比画面窄，原因就是这个。",

    "zh-Hant": "- **曲線末端那個名字和數字不會進入平台自己的介面**：手機應用程式會把頭像、按讚和"
               "留言按鈕畫在直式影片的右側，所以繪圖區在畫面右緣之前就結束，曲線的即時點連同它的"
               "名字與數字都落在那條帶的左邊。圖表比畫面窄，原因就是這個。",
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

        # 第一段连续的 `- ` 列表：插在它末尾。空行把它与后面「免费/订阅」那条隔开，所以
        # `runs[0]` 就是版面那几条，插进去不会插到收费那段后面。
        runs = []
        run = []

        for i, line in enumerate(block):
            if line.startswith("- "):
                run.append(i)
            elif run:
                runs.append(run)
                run = []

        if run:
            runs.append(run)

        assert runs, f"{tag}: the video chapter has no bullet list"

        at = runs[0][-1] + 1
        lines[start:end] = block[:at] + [ENTRY[tag]] + block[at:]

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
