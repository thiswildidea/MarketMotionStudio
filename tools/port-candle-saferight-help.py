# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「K 线走势」那一章补一条：这一页也有「允许图形越过右侧安全线」。

**为什么非说不可**：这一页原本没有这个开关，现在有了，而且它管的是**两种画面**——蜡烛图的
右缘，和比较画面里曲线末端那颗标签。不说，读者只会在导出之后从手机上发现蜡烛最右边一截被
头像盖住，或者以为那个开关是给别的页面的。

**为什么按章节号定位**：`listingtext.chapter_of("NavCandle")` 从导航顺序算，导航顺序就是章节
顺序。写 14 个语言的标题字符串就是 14 处会失配的地方。

**不引用任何控件名字**：复选框的名字在 14 种语言里各不相同，抄错一处就是一句指着不存在的
控件的说明。这条只说这个开关在做什么。

**插在哪**：这一章**第一段连续的 `- ` 列表的末尾**。这一章的列表是完整的一段，末尾就是
「Range」那条之后（上一条是「选两个以上标的」那条）。

**和三页那条的关系**：前半句照抄 DcaPlan / Position 两章里那条（同一件事在同一个应用里
只有一种说法），后半句换成这一页的画面。三页说不出来的是蜡烛图那半边：那三页让路让的是
末端标签，这一页的蜡烛本身也是画在那条带里的墨。

**重音字母照写。** 德语的 ä/ö/ü、法语的 é/è/ç、捷克语的 ř/ž/ů、土耳其语的 ğ/ı/ş、俄语的
я/ё 都是这个字的一部分，不是装饰；为了「保险」写成 a/o/u/e/c/r/z/g/i/s 等于在应用里挂一句
拼错的外语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM。

幂等：这一章里已经有这一条就跳过。

用法：<venv python> tools/port-candle-saferight-help.py      （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP
CHAPTER = lt.chapter_of("NavCandle")

LINE = {
    "en-US": "- **The band down the right-hand side can be given up, if you want the width.** It "
             "is off by default: the platform draws its avatar and its like and comment buttons "
             "down that side of a vertical video, and the candles and the ends of the curves drawn "
             "under them are hidden on the phone even though they are perfectly readable here. "
             "Turned on, both pictures this page draws run to the frame's own edge — the candles "
             "all the way to it, and a comparison's name and figure with them; a scrolling window "
             "still keeps clear while it is a window, and opens out into the full width along with "
             "the window.",
    "de": "- **Der Streifen an der rechten Seite kann freigegeben werden, wenn du die Breite "
          "willst.** Voreingestellt ist er nicht: Die Plattform zeichnet ihr Profilbild sowie die "
          "Schaltflächen für „Gefällt mir“ und Kommentare an diese Seite eines Hochformatvideos, "
          "und die Kerzen und Kurvenenden darunter sind auf dem Telefon verdeckt, obwohl sie hier "
          "völlig lesbar sind. Eingeschaltet laufen beide Bilder dieser Seite bis zur eigenen "
          "Kante des Bildes — die Kerzen ganz dorthin und Name und Zahl am Ende einer "
          "Vergleichskurve mit ihnen; ein wanderndes Fenster hält Abstand, solange es ein Fenster "
          "ist, und weitet sich zusammen mit dem Fenster auf die volle Breite.",
    "es": "- **La banda del lado derecho puede cederse, si quieres el ancho.** Viene desactivada: "
          "la plataforma dibuja su avatar y sus botones de «me gusta» y comentarios en ese lado de "
          "un vídeo vertical, y las velas y los extremos de las curvas dibujados debajo quedan "
          "ocultos en el teléfono aunque aquí se lean perfectamente. Activada, las dos imágenes "
          "que dibuja esta página llegan hasta el propio borde del encuadre: las velas hasta él, y "
          "el nombre y la cifra al final de una curva de comparación con ellas; una ventana "
          "deslizante sigue guardando distancia mientras es una ventana y se abre al ancho "
          "completo junto con la ventana.",
    "fr": "- **La bande du côté droit peut être cédée, si vous voulez la largeur.** Elle est "
          "désactivée par défaut : la plateforme dessine son avatar et ses boutons « j'aime » et "
          "commentaire sur ce côté d'une vidéo verticale, et les chandeliers et les extrémités des "
          "courbes tracés dessous sont masqués sur le téléphone alors qu'ils sont parfaitement "
          "lisibles ici. Activée, les deux images que trace cette page vont jusqu'au bord même de "
          "l'image : les chandeliers jusque-là, et le nom et le chiffre au bout d'une courbe de "
          "comparaison avec eux ; une fenêtre glissante continue de garder ses distances tant "
          "qu'elle est une fenêtre, et s'ouvre à la pleine largeur en même temps qu'elle.",
    "it": "- **La fascia sul lato destro può essere ceduta, se vuoi la larghezza.** È disattivata "
          "per impostazione predefinita: la piattaforma disegna il proprio avatar e i pulsanti «mi "
          "piace» e commento su quel lato di un video verticale, e le candele e le estremità delle "
          "curve disegnate sotto risultano nascoste sul telefono anche se qui sono perfettamente "
          "leggibili. Attivata, le due immagini che disegna questa pagina arrivano fino al bordo "
          "stesso dell'inquadratura: le candele fino a lì, e con esse il nome e la cifra in fondo "
          "a una curva di confronto; una finestra scorrevole continua a tenersi a distanza finché "
          "è una finestra, e si apre alla larghezza piena insieme alla finestra.",
    "pt-BR": "- **A faixa do lado direito pode ser cedida, se você quiser a largura.** Ela vem "
             "desligada: a plataforma desenha seu avatar e os botões de curtir e comentar desse "
             "lado de um vídeo vertical, e os candles e as pontas das curvas desenhados embaixo "
             "ficam escondidos no celular, embora aqui estejam perfeitamente legíveis. Ativada, os "
             "dois quadros que esta página desenha vão até a própria borda do quadro: os candles "
             "até ela, e o nome e o número no fim de uma curva de comparação junto com eles; uma "
             "janela rolante continua mantendo distância enquanto é uma janela e se abre para a "
             "largura total junto com a janela.",
    "pl": "- **Pas po prawej stronie można oddać, jeśli zależy ci na szerokości.** Domyślnie jest "
          "wyłączony: platforma rysuje tam swój awatar oraz przyciski „lubię to” i komentarzy w "
          "pionowym wideo, a świece i końce krzywych rysowane pod nimi są na telefonie zasłonięte, "
          "choć tutaj widać je bez problemu. Włączony: oba obrazy rysowane przez tę stronę sięgają "
          "własnej krawędzi kadru — świece aż do niej, a wraz z nimi nazwa i liczba na końcu "
          "krzywej porównania; przesuwne okno zachowuje odstęp, dopóki jest oknem, i wraz z oknem "
          "rozwiera się na pełną szerokość.",
    "cs": "- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je "
          "vypnutý: platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té "
          "straně svislého videa a svíčky a konce křivek nakreslené pod nimi jsou na telefonu "
          "skryté, přestože jsou tu zcela čitelné. Zapnutý: oba obrazy, které tato stránka kreslí, "
          "jdou až k vlastnímu okraji záběru — svíčky až k němu a s nimi jméno a číslo na konci "
          "srovnávací křivky; posuvné okno drží odstup, dokud je oknem, a spolu s oknem se rozevře "
          "na plnou šířku.",
    "tr": "- **Sağ kenardaki şerit, genişliği istersen bırakılabilir.** Varsayılan olarak "
          "kapalıdır: platform dikey videonun o kenarına avatarını, beğeni ve yorum düğmelerini "
          "çizer ve altına çizilen mumlar ile eğri uçları, burada rahatça okunsalar da telefonda "
          "gizli kalır. Açıkken bu sayfanın çizdiği iki görüntü de karenin kendi kenarına kadar "
          "gider — mumlar ta kendisine, karşılaştırma eğrisinin ucundaki ad ve sayı da onlarla "
          "birlikte; kayan pencere pencere olduğu sürece mesafeyi korur ve pencereyle birlikte tam "
          "genişliğe açılır.",
    "ru": "- **Полосу справа можно отдать, если нужна ширина.** По умолчанию она не отдаётся: "
          "платформа рисует свой аватар и кнопки «нравится» и комментариев у этого края "
          "вертикального видео, и свечи и концы кривых под ними на телефоне окажутся скрыты, "
          "хотя здесь они прекрасно читаются. Включённая — оба кадра, которые рисует эта "
          "страница, доходят до собственного края кадра: свечи до самого него, а вместе с ними "
          "название и число на конце кривой сравнения; скользящее окно по-прежнему держится на "
          "расстоянии, пока остаётся окном, и раскрывается на полную ширину вместе с окном.",
    "ja": "- **右側の帯は、幅が欲しければ譲ることができます。** 既定では譲りません。プラット"
          "フォームは縦長動画のその側に自分のアイコンと「いいね」「コメント」のボタンを描くため、"
          "その下に描かれるローソク足や曲線の末端は、ここでははっきり読めてもスマートフォンでは"
          "隠れてしまいます。 有効にすると、このページが描く二つの画面はどちらも画面自身の端まで"
          "描きます——ローソク足はそこまで、比較の曲線の末端の名前と数字も同様です。スクロール"
          "する窓は窓である間は距離を保ったまま、窓と一緒に全幅へ開きます。",
    "ko": "- **오른쪽 띠는 폭을 원한다면 내줄 수 있습니다.** 기본적으로는 내주지 않습니다. "
          "플랫폼이 세로 영상의 그쪽에 자기 아이콘과 좋아요·댓글 버튼을 그리기 때문에, 그 아래에 "
          "그려지는 캔들과 곡선의 끝은 여기서 또렷이 읽혀도 휴대폰에서는 가려집니다. 켜면 이 "
          "화면이 그리는 두 그림 모두 화면 자체의 끝까지 그립니다 — 캔들은 거기까지, 비교 곡선 "
          "끝의 이름과 숫자도 함께; 스크롤되는 창은 창인 동안에는 거리를 유지하다가 창과 함께 "
          "전체 너비로 열립니다.",
    "zh-Hans": "- **右边那条带可以让出来，代价是画面变窄 —— 要不要由你定。** 默认是让的：平台"
               "会把头像、点赞和评论按钮画在竖屏视频的右侧，画在那里的蜡烛和曲线末端在这里读得"
               "清清楚楚，到了手机上却被盖住。 打开后，这一页的两种画面都放宽到画面右缘 —— "
               "蜡烛图一直画到那里，比较画面里曲线末端的名字与数字也一样；窗口滚动时照旧让位，"
               "收尾展开时随窗口一起放开到全宽。",
    "zh-Hant": "- **右邊那條帶可以讓出來，代價是畫面變窄 —— 要不要由你定。** 預設是讓的：平台"
               "會把頭像、按讚和留言按鈕畫在直式影片的右側，畫在那裡的蠟燭和曲線末端在這裡讀得"
               "清清楚楚，到了手機上卻被蓋住。 打開後，這一頁的兩種畫面都放寬到畫面右緣 —— "
               "蠟燭圖一直畫到那裡，比較畫面裡曲線末端的名字與數字也一樣；視窗滾動時照舊讓位，"
               "收尾展開時隨視窗一起放開到全寬。",
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
