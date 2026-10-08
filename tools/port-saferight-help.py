# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的三章各补一条：右边那条带可以让出来，也可以不让。

**为什么非说不可**：三页的图表右边空出一条、曲线不再铺满整幅宽，是这个开关**关着**的样子。
不看说明的人只看到「我的图变窄了」，看不到按钮栏 —— 那一部分只有手机上有。而开关本身又
是个复选框，一句话说不清开着会发生什么。

**为什么按章节号而不是按标题文本定位**：`listingtext.chapter_of` 从导航顺序算，导航顺序就是
章节顺序（手册 26 章与界面同序）。写 14 个语言的标题字符串就是 14 处会失配的地方，而
`port-endrail-help.py` 之所以按标题认，是因为「视频」那一章**不是任何一页的说明**，
`chapter_of` 够不着它。这三章都是页面章节，所以用序号。

**动效的名字不引用**：`*grow across the span*` 这类名字在 14 种语言里各不相同，抄错一处就是
一句指着不存在的控件的话。改成描述这个动效在做什么 —— 它本来就在同一章里被解释过。

**插在哪**：这一章**第一段连续的 `- ` 列表的末尾**。市值历程那一章插在「Span」那条之后，
定投/持仓插在「窗口在收尾展开」那条之后，都在设置那一带的末尾。

**重音字母照写。** 德语的 ä/ö/ü、法语的 é/è/ç、捷克语的 ř/ž/í、土耳其语的 ğ/ı/ş、俄语的
я/ё 都是这个字的一部分，不是装饰；为了「保险」写成 a/o/u/e/c/r/z/g/i/s 等于在应用里挂一句
拼错的外语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符。

幂等：先看这一章里有没有这一条，有就跳过。

用法：<venv python> tools/port-saferight-help.py      （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

# 三章：市值历程（没有推进方式，天然就是整段铺满）、定投计划、持仓收益（有两种推进方式）。
CAP = lt.chapter_of("NavCapHistory")
MOTION = [lt.chapter_of("NavDcaPlan"), lt.chapter_of("NavPosition")]

# 前半段三章共用：这条带是什么、为什么默认不让。
SHARED = {
    "en-US": "- **The band down the right-hand side can be given up, if you want the width.** It "
             "is off by default: the platform draws its avatar and its like and comment buttons "
             "down that side of a vertical video, and a figure underneath them is hidden on the "
             "phone even though it is perfectly readable here.",
    "de": "- **Der Streifen an der rechten Seite kann freigegeben werden, wenn du die Breite "
          "willst.** Voreingestellt ist er nicht: Die Plattform zeichnet ihr Profilbild sowie die "
          "Schaltflächen für „Gefällt mir“ und Kommentare an diese Seite eines Hochformatvideos, "
          "und eine Zahl darunter ist auf dem Telefon verdeckt, obwohl sie hier völlig lesbar ist.",
    "es": "- **La banda del lado derecho puede cederse, si quieres el ancho.** Viene desactivada: "
          "la plataforma dibuja su avatar y sus botones de «me gusta» y comentarios en ese lado de "
          "un vídeo vertical, y una cifra debajo queda oculta en el teléfono aunque aquí se lea "
          "perfectamente.",
    "fr": "- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est "
          "désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et "
          "commentaire sur ce côté d'une vidéo verticale, et un chiffre en dessous est masqué sur "
          "le téléphone alors qu'il est parfaitement lisible ici.",
    "it": "- **La fascia sul lato destro può essere ceduta, se vuoi la larghezza.** È disattivata "
          "per impostazione predefinita: la piattaforma disegna il proprio avatar e i pulsanti «mi "
          "piace» e commento su quel lato di un video verticale, e una cifra sotto di essi "
          "risulta nascosta sul telefono anche se qui è perfettamente leggibile.",
    "pl": "- **Pas po prawej stronie można oddać, jeśli zależy ci na szerokości.** Domyślnie jest "
          "wyłączony: platforma rysuje tam swój awatar oraz przyciski „lubię to” i komentarzy w "
          "pionowym wideo, a liczba pod nimi jest na telefonie zasłonięta, choć tutaj widać ją bez "
          "problemu.",
    "pt-BR": "- **A faixa do lado direito pode ser cedida, se você quiser a largura.** Ela vem "
             "desligada: a plataforma desenha seu avatar e os botões de curtir e comentar desse "
             "lado de um vídeo vertical, e um número sob eles fica escondido no celular, embora "
             "aqui esteja perfeitamente legível.",
    "cs": "- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je vypnutý: "
          "platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té straně "
          "svislého videa a číslo pod nimi je na telefonu skryté, přestože je tu zcela čitelné.",
    "tr": "- **Sağ kenardaki şerit, genişliği istersen bırakılabilir.** Varsayılan olarak kapalıdır: "
          "platform dikey videonun o kenarına avatarını, beğeni ve yorum düğmelerini çizer ve "
          "altındaki sayı, burada rahatça okunsa da telefonda gizli kalır.",
    "ru": "- **Полосу справа можно отдать, если нужна ширина.** По умолчанию она не отдаётся: "
          "платформа рисует свой аватар и кнопки «нравится» и комментариев у этого края "
          "вертикального видео, и число под ними на телефоне окажется скрыто, хотя здесь оно "
          "прекрасно читается.",
    "ja": "- **右側の帯は、幅が欲しければ譲ることができます。** 既定では譲りません。プラット"
          "フォームは縦長動画のその側に自分のアイコンと「いいね」「コメント」のボタンを描く"
          "ため、その下にある数値はここでははっきり読めてもスマートフォンでは隠れてしまいます。",
    "ko": "- **오른쪽 띠는 폭을 원한다면 내줄 수 있습니다.** 기본적으로는 내주지 않습니다. "
          "플랫폼이 세로 영상의 그쪽에 자기 아이콘과 좋아요·댓글 버튼을 그리기 때문에, 그 아래의 "
          "숫자는 여기서 또렷이 읽혀도 휴대폰에서는 가려집니다.",
    "zh-Hans": "- **右边那条带可以让出来，代价是画面变窄 —— 要不要由你定。** 默认是让的：平台会"
               "把头像、点赞和评论按钮画在竖屏视频的右侧，压在下面的数字在这里读得清清楚楚，"
               "到了手机上却被盖住。",
    "zh-Hant": "- **右邊那條帶可以讓出來，代價是畫面變窄 —— 要不要由你定。** 預設是讓的：平台"
               "會把頭像、按讚和留言按鈕畫在直式影片的右側，壓在下面的數字在這裡讀得清清楚楚，"
               "到了手機上卻被蓋住。",
}

# 后半段：市值历程没有推进方式，从第一帧起就是整段。
CAP_TAIL = {
    "en-US": " Turned on, the panels draw to the frame's own edge and the plot is as wide as the "
             "frame.",
    "de": " Eingeschaltet zeichnen die beiden Flächen bis zur eigenen Kante des Bildes, und der "
          "Graph ist so breit wie das Bild.",
    "es": " Activada, los paneles dibujan hasta el propio borde del encuadre y el gráfico es tan "
          "ancho como el encuadre.",
    "fr": " Activée, les panneaux tracent jusqu'au bord même de l'image et le graphique est aussi "
          "large que l'image.",
    "it": " Attivata, i pannelli disegnano fino al bordo stesso dell'inquadratura e il grafico è "
          "largo quanto l'inquadratura.",
    "pl": " Włączony: panele rysują do samej krawędzi kadru, a wykres jest tak szeroki jak kadr.",
    "pt-BR": " Ativada, os painéis desenham até a própria borda do quadro e o gráfico fica tão "
             "largo quanto o quadro.",
    "cs": " Zapnutý: panely kreslí až k vlastnímu okraji záběru a graf je široký jako záběr.",
    "tr": " Açıkken paneller karenin kendi kenarına kadar çizer ve grafik kare kadar geniş olur.",
    "ru": " Включённая — панели рисуют до собственного края кадра, и график становится шириной "
          "в кадр.",
    "ja": " 有効にすると、パネルは画面自身の端まで描き、グラフは画面と同じ幅になります。",
    "ko": " 켜면 패널이 화면 자체의 끝까지 그리며 그래프가 화면과 같은 너비가 됩니다.",
    "zh-Hans": " 打开后，两块面板一直画到画面自己的右缘，图就有多宽用多宽。",
    "zh-Hant": " 打開後，兩塊面板一直畫到畫面自己的右緣，圖就有多寬用多寬。",
}

# 后半段：另两页有两种推进方式 —— 铺满全程不让，滚动途中照旧让、展开时一起放开。
MOTION_TAIL = {
    "en-US": " Turned on, a frame filling the whole span draws to the frame's own edge from its "
             "first frame on; a scrolling window still keeps clear while it is a window, and opens "
             "out into the full width along with the window — so the frame the video stops on is "
             "the whole span, edge to edge.",
    "de": " Eingeschaltet zeichnet ein Bild, das die ganze Spanne füllt, von seiner ersten Aufnahme "
          "an bis zur eigenen Kante des Bildes; ein wanderndes Fenster hält Abstand, solange es "
          "ein Fenster ist, und weitet sich zusammen mit dem Fenster auf die volle Breite — das "
          "Bild, auf dem das Video anhält, ist also die ganze Spanne von Rand zu Rand.",
    "es": " Activada, un encuadre que llena toda la serie dibuja hasta el propio borde del encuadre "
          "desde su primera imagen; una ventana deslizante sigue guardando distancia mientras es "
          "una ventana y se abre al ancho completo junto con la ventana — así que la imagen en la "
          "que se detiene el vídeo es la serie completa, de borde a borde.",
    "fr": " Activée, une image qui remplit toute la période trace jusqu'au bord même de l'image "
          "dès sa première image ; une fenêtre glissante continue de garder ses distances tant "
          "qu'elle est une fenêtre, et s'ouvre à la pleine largeur en même temps qu'elle — l'image "
          "sur laquelle la vidéo s'arrête est donc toute la période, d'un bord à l'autre.",
    "it": " Attivata, un'inquadratura che riempie tutto l'intervallo disegna fino al bordo stesso "
          "dell'inquadratura fin dal primo fotogramma; una finestra scorrevole continua a tenersi "
          "a distanza finché è una finestra, e si apre alla larghezza piena insieme alla finestra — "
          "così l'inquadratura su cui il video si ferma è tutto l'intervallo, da bordo a bordo.",
    "pl": " Włączony: kadr wypełniający cały zakres rysuje do własnej krawędzi kadru od pierwszej "
          "klatki; przesuwne okno zachowuje odstęp, dopóki jest oknem, i wraz z oknem rozwiera się "
          "na pełną szerokość — więc klatka, na której zatrzymuje się film, to cały zakres od "
          "krawędzi do krawędzi.",
    "pt-BR": " Ativada, um quadro que preenche todo o intervalo desenha até a própria borda do "
             "quadro desde o primeiro quadro; uma janela rolante continua mantendo distância "
             "enquanto é uma janela e se abre para a largura total junto com a janela — então o "
             "quadro em que o vídeo para é o intervalo inteiro, de borda a borda.",
    "cs": " Zapnutý: záběr, který vyplňuje celý rozsah, kreslí od první snímku až k vlastnímu "
          "okraji záběru; posuvné okno drží odstup, dokud je oknem, a spolu s oknem se rozevře na "
          "plnou šířku — snímek, na kterém video skončí, je tedy celý rozsah od okraje k okraji.",
    "tr": " Açıkken tüm aralığı dolduran bir kare, ilk karesinden itibaren karenin kendi kenarına "
          "kadar çizer; kayan pencere pencere olduğu sürece mesafeyi korur ve pencereyle birlikte "
          "tam genişliğe açılır — yani videonun durduğu kare, kenardan kenara tüm aralıktır.",
    "ru": " Включённая — кадр, заполняющий весь период, рисует до собственного края кадра с первого "
          "же кадра; скользящее окно по-прежнему держится на расстоянии, пока остаётся окном, и "
          "раскрывается на полную ширину вместе с окном — так что кадр, на котором видео "
          "останавливается, это весь период от края до края.",
    "ja": " 有効にすると、全区間を埋める画面は最初のフレームから画面自身の端まで描き、スクロール"
          "する窓は窓である間は距離を保ったまま、窓と一緒に全幅へ開きます。つまり動画が止まる"
          "フレームは端から端までの全区間になります。",
    "ko": " 켜면 전체 구간을 채우는 화면이 첫 프레임부터 화면 자체의 끝까지 그리고, 스크롤되는 "
          "창은 창인 동안에는 거리를 유지하다가 창과 함께 전체 너비로 열립니다. 즉 영상이 멈추는 "
          "프레임이 끝에서 끝까지의 전체 구간이 됩니다.",
    "zh-Hans": " 打开后，整段铺满的那一版从第一帧起就一直画到画面右缘；窗口滚动则滚动途中照旧让"
               "位，收尾展开时随窗口一起放开到全宽 —— 于是视频停住的那一帧是端到端的整段。",
    "zh-Hant": " 打開後，整段鋪滿的那一版從第一幀起就一直畫到畫面右緣；視窗滾動則滾動途中照舊讓"
               "位，收尾展開時隨視窗一起放開到全寬 —— 於是影片停住的那一幀是端到端的整段。",
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

        wanted = {CAP: SHARED[tag] + CAP_TAIL[tag]}
        wanted.update({n: SHARED[tag] + MOTION_TAIL[tag] for n in MOTION})

        added = 0

        for number, entry in sorted(wanted.items(), reverse=True):
            end = starts[number + 1] if number + 1 < len(starts) else len(lines)
            block = lines[starts[number]:end]

            if any(line.strip() == entry for line in block):
                continue

            lines[starts[number]:end] = insert(block, entry)
            added += 1

        if not added:
            print(f"{tag:9} already there")
            continue

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +{added}")


if __name__ == "__main__":
    main()
