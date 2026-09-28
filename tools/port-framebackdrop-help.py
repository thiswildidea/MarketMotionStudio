# -*- coding: utf-8 -*-
"""给 14 份帮助手册插入「动画背景」一节。

**按章节序号定位，不按标题文本**：14 种语言的标题各不相同，锚在「数据」那一节
（第 12 个 `## `）之前插入，正好接在「背景图片」之后。幂等可重跑。
读 utf-8-sig、按原样写回（保 BOM 保行尾）。
"""
import os

ROOT = r"D:/software/MarketMotionStudio/src/MarketMotionStudio/Assets/Help"

# 每份：（标题，引言，4 条要点）
CHAPTERS = {
    "en-US": (
        "Animation background",
        "The Settings page can change what the animation is drawn on: the built-in gradient, two "
        "colours of your own, or a picture. It applies to the preview, the exported video and the "
        "cover image alike — all three are drawn by the same renderer, so there is no \"looks good "
        "in the preview, different in the file\".",
        [
            "Choosing colours gives you a top and a bottom stop, and the frame fades from one to "
            "the other. Dark suits these frames: every tone of text in them is light, and a light "
            "background makes the numbers hard to read.",
            "Choosing a picture works the same way as the window's: pick one from your computer, "
            "or use a wallpaper Windows already ships. One you pick is copied into the app's own "
            "folder.",
            "The picture fills the frame and the surplus is cropped, so its proportions are never "
            "stretched.",
            "The dimming slider sets how far the picture is pushed back towards the frame's own "
            "backdrop, from 20% to 95%.",
        ],
    ),
    "de": (
        "Animationshintergrund",
        "Auf der Einstellungsseite lässt sich ändern, worauf die Animation gezeichnet wird: der "
        "eingebaute Farbverlauf, zwei eigene Farben oder ein Bild. Es gilt für die Vorschau, das "
        "exportierte Video und das Titelbild gleichermaßen – alle drei zeichnet derselbe Renderer, "
        "es gibt also kein „in der Vorschau schön, in der Datei anders“.",
        [
            "Bei Farben geben Sie oben und unten je einen Farbton an; das Bild blendet dazwischen "
            "über. Dunkel passt: Jede Schriftfarbe darin ist hell, auf hellem Grund sind die Zahlen "
            "schwer zu lesen.",
            "Ein Bild wählen funktioniert wie beim Fensterhintergrund: eines vom Rechner oder ein "
            "mitgeliefertes Windows-Hintergrundbild. Ein eigenes wird in den App-Ordner kopiert.",
            "Das Bild füllt das Format und der Überstand wird beschnitten; die Proportionen werden "
            "nicht verzerrt.",
            "Der Regler für die Abdunklung bestimmt, wie weit das Bild zum eigenen Hintergrund der "
            "Seite zurückgenommen wird: 20 % bis 95 %.",
        ],
    ),
    "es": (
        "Fondo de la animación",
        "En la página de configuración puedes cambiar sobre qué se dibuja la animación: el "
        "degradado integrado, dos colores tuyos o una imagen. Se aplica por igual a la vista "
        "previa, al vídeo exportado y a la imagen de portada: los tres los dibuja el mismo motor, "
        "así que no hay un «se ve bien en la vista previa y distinto en el archivo».",
        [
            "Al elegir colores indicas un tono superior y otro inferior, y el fotograma pasa de uno "
            "a otro. Mejor oscuros: todos los tonos de texto son claros y un fondo claro dificulta "
            "leer las cifras.",
            "Elegir una imagen funciona igual que en el fondo de la ventana: una de tu equipo o un "
            "fondo que Windows ya incluye. La que elijas se copia a la carpeta de la aplicación.",
            "La imagen rellena el fotograma y lo que sobra se recorta, así que nunca se deforma.",
            "El control de atenuación decide cuánto se retira la imagen hacia el fondo propio de la "
            "página, del 20 % al 95 %.",
        ],
    ),
    "fr": (
        "Fond de l'animation",
        "La page Paramètres permet de changer ce sur quoi l'animation est dessinée : le dégradé "
        "intégré, deux couleurs de votre choix, ou une image. Cela vaut pour l'aperçu, pour la "
        "vidéo exportée et pour l'image de couverture : les trois sont dessinés par le même "
        "moteur, il n'y a donc pas de « joli dans l'aperçu, différent dans le fichier ».",
        [
            "Pour les couleurs, vous donnez un ton du haut et un ton du bas, et l'image passe de "
            "l'un à l'autre. Les tons sombres conviennent : chaque teinte de texte est claire et un "
            "fond clair rend les chiffres difficiles à lire.",
            "Choisir une image fonctionne comme pour le fond de la fenêtre : une image de votre "
            "ordinateur, ou un fond d'écran fourni par Windows. Celle que vous choisissez est "
            "copiée dans le dossier de l'application.",
            "L'image remplit le cadre et le surplus est rogné : ses proportions ne sont jamais "
            "étirées.",
            "Le curseur d'assombrissement règle à quel point l'image est ramenée vers le fond "
            "propre à la page, de 20 % à 95 %.",
        ],
    ),
    "it": (
        "Sfondo dell'animazione",
        "Nella pagina Impostazioni puoi cambiare ciò su cui viene disegnata l'animazione: il "
        "gradiente predefinito, due colori tuoi oppure un'immagine. Vale per l'anteprima, per il "
        "video esportato e per l'immagine di copertina: tutti e tre li disegna lo stesso renderer, "
        "quindi non esiste un «bello nell'anteprima, diverso nel file».",
        [
            "Con i colori indichi un tono in alto e uno in basso e il fotogramma passa dall'uno "
            "all'altro. Meglio scuri: ogni tono di testo è chiaro e uno sfondo chiaro rende i "
            "numeri difficili da leggere.",
            "Scegliere un'immagine funziona come per lo sfondo della finestra: una dal computer o "
            "uno sfondo già incluso in Windows. Quella scelta viene copiata nella cartella "
            "dell'app.",
            "L'immagine riempie il formato e l'eccedenza viene ritagliata: le proporzioni non "
            "vengono mai deformate.",
            "Il cursore di attenuazione decide quanto l'immagine viene riportata verso lo sfondo "
            "proprio della pagina, dal 20% al 95%.",
        ],
    ),
    "pl": (
        "Tło animacji",
        "Na stronie ustawień możesz zmienić to, na czym rysowana jest animacja: wbudowany "
        "gradient, dwa własne kolory albo obraz. Dotyczy to podglądu, eksportowanego wideo i "
        "obrazu okładki — wszystkie trzy rysuje ten sam renderer, więc nie ma „ładnie w podglądzie, "
        "inaczej w pliku”.",
        [
            "Przy kolorach podajesz ton górny i dolny, a klatka przechodzi między nimi. Lepiej "
            "ciemne: każdy odcień tekstu jest jasny, a jasne tło utrudnia odczyt liczb.",
            "Wybór obrazu działa tak samo jak dla tła okna: obraz z komputera albo tapeta "
            "dołączona do Windows. Wybrany jest kopiowany do folderu aplikacji.",
            "Obraz wypełnia klatkę, a nadmiar jest przycinany, więc proporcje nigdy się nie "
            "rozciągają.",
            "Suwak przyciemnienia decyduje, jak mocno obraz jest cofany do własnego tła strony: od "
            "20% do 95%.",
        ],
    ),
    "pt-BR": (
        "Fundo da animação",
        "Na página de configurações você pode mudar sobre o que a animação é desenhada: o "
        "gradiente padrão, duas cores suas ou uma imagem. Vale para a pré-visualização, o vídeo "
        "exportado e a imagem de capa: os três são desenhados pelo mesmo renderizador, então não "
        "existe \"bonito na pré-visualização e diferente no arquivo\".",
        [
            "Ao escolher cores, você indica um tom superior e um inferior, e o quadro passa de um "
            "para o outro. Prefira escuros: todos os tons de texto são claros, e um fundo claro "
            "dificulta a leitura dos números.",
            "Escolher uma imagem funciona como no fundo da janela: uma do computador ou um papel "
            "de parede que já vem com o Windows. A escolhida é copiada para a pasta do aplicativo.",
            "A imagem preenche o quadro e o excesso é cortado, então as proporções nunca são "
            "esticadas.",
            "O controle de escurecimento define o quanto a imagem volta para o fundo próprio da "
            "página, de 20% a 95%.",
        ],
    ),
    "cs": (
        "Pozadí animace",
        "Na stránce nastavení můžete změnit, na co se animace kreslí: vestavěný přechod, dvě "
        "vlastní barvy nebo obrázek. Platí to pro náhled, exportované video i titulní obrázek – "
        "všechny tři kreslí stejný renderer, takže neexistuje „v náhledu hezké, v souboru jinak“.",
        [
            "U barev zadáte horní a dolní odstín a snímek mezi nimi přechází. Tmavé jsou lepší: "
            "každý odstín textu je světlý a na světlém pozadí se čísla špatně čtou.",
            "Výběr obrázku funguje stejně jako u pozadí okna: obrázek z počítače nebo tapeta, "
            "kterou Windows už mají. Vybraný se zkopíruje do složky aplikace.",
            "Obrázek vyplní formát a přebytek se ořízne, takže se proporce nikdy neroztáhnou.",
            "Posuvník ztmavení určuje, jak silně se obrázek vrací k vlastnímu pozadí stránky: "
            "20 % až 95 %.",
        ],
    ),
    "tr": (
        "Animasyon arka planı",
        "Ayarlar sayfasında animasyonun neyin üzerine çizileceğini değiştirebilirsiniz: yerleşik "
        "geçiş, kendi seçtiğiniz iki renk veya bir resim. Önizleme, dışa aktarılan video ve kapak "
        "görseli için geçerlidir — üçünü de aynı oluşturucu çizer, yani \"önizlemede güzel, "
        "dosyada farklı\" diye bir şey yoktur.",
        [
            "Renk seçtiğinizde üst ve alt için birer ton verirsiniz ve kare ikisi arasında geçer. "
            "Koyu renkler daha uygundur: tüm metin tonları açıktır ve açık arka plan sayıları "
            "okumayı zorlaştırır.",
            "Resim seçmek pencere arka planındaki gibi işler: bilgisayarınızdan bir resim ya da "
            "Windows ile gelen bir duvar kağıdı. Seçtiğiniz resim uygulamanın klasörüne "
            "kopyalanır.",
            "Resim kareyi doldurur, artan kısım kırpılır; oranları asla bozulmaz.",
            "Karartma sürgüsü, resmin sayfanın kendi arka planına ne kadar geri çekileceğini "
            "belirler: %20 ile %95 arası.",
        ],
    ),
    "ru": (
        "Фон анимации",
        "На странице настроек можно изменить, на чём рисуется анимация: встроенный градиент, два "
        "ваших цвета или изображение. Это действует и на предпросмотр, и на экспортированное "
        "видео, и на обложку — все три рисует один и тот же отрисовщик, поэтому «в "
        "предпросмотре красиво, в файле иначе» не бывает.",
        [
            "Для цветов задаются верхний и нижний оттенок, и кадр переходит между ними. Лучше "
            "тёмные: все оттенки текста светлые, а на светлом фоне числа читаются плохо.",
            "Выбор изображения работает так же, как для фона окна: картинка с компьютера или "
            "обои, которые уже есть в Windows. Выбранная копируется в папку приложения.",
            "Изображение заполняет кадр, лишнее обрезается, поэтому пропорции никогда не "
            "растягиваются.",
            "Ползунок затемнения задаёт, насколько изображение возвращается к собственному фону "
            "страницы: от 20 % до 95 %.",
        ],
    ),
    "ja": (
        "アニメーションの背景",
        "設定ページで、アニメーションを何の上に描くかを変えられます。既定のグラデーション、"
        "自分で選んだ2色、または画像です。プレビュー・書き出した動画・カバー画像のすべてに"
        "同じものが使われます。三者は同じレンダラーが描くので、「プレビューでは良いのに"
        "ファイルでは違う」ということはありません。",
        [
            "色を選ぶときは上下2つの色を指定し、その間をフレームが移り変わります。暗い色が"
            "向いています。文字はすべて明るい色で、明るい背景では数字が読みにくくなるからです。",
            "画像の選択はウィンドウの背景と同じです。パソコンの画像か、Windows に最初から"
            "入っている壁紙を使えます。選んだ画像はアプリのフォルダーに複製されます。",
            "画像は画面いっぱいに広げ、はみ出した部分は切り取られるので、縦横比が崩れることは"
            "ありません。",
            "濃度スライダーは、画像をそのページ本来の背景にどれだけ戻すかを決めます"
            "（20%〜95%）。",
        ],
    ),
    "ko": (
        "애니메이션 배경",
        "설정 페이지에서 애니메이션을 무엇 위에 그릴지 바꿀 수 있습니다. 기본 그라데이션, 직접 "
        "고른 두 가지 색, 또는 사진입니다. 미리보기, 내보낸 영상, 커버 이미지에 모두 똑같이 "
        "적용됩니다. 세 가지 모두 같은 렌더러가 그리므로 \"미리보기에서는 좋은데 파일에서는 "
        "다른\" 경우는 없습니다.",
        [
            "색을 고를 때는 위와 아래 두 색을 정하고 그 사이를 프레임이 지나갑니다. 어두운 색이 "
            "어울립니다. 글자가 모두 밝은 색이라 밝은 배경에서는 숫자가 잘 읽히지 않습니다.",
            "사진 선택은 창 배경과 같습니다. 컴퓨터의 사진이나 Windows에 들어 있는 배경 그림을 "
            "쓸 수 있습니다. 고른 사진은 앱 폴더에 복사됩니다.",
            "사진은 화면을 채우고 넘치는 부분은 잘리므로 비율이 늘어나지 않습니다.",
            "농도 슬라이더는 사진을 원래 배경 쪽으로 얼마나 되돌릴지 정합니다(20%~95%).",
        ],
    ),
    "zh-Hans": (
        "动画背景",
        "设置页可以改动画画在什么上面：默认渐变、你选的两个颜色，或者一张图片。它同时作用于"
        "预览、导出的视频和封面图——三者由同一个渲染器绘制，所以不会出现「预览好看、文件里"
        "不一样」。",
        [
            "选颜色时要给上下两个色标，画面便在两者之间过渡。深色更合适：帧内所有文字都是"
            "浅色，浅色底会让数字难以辨认。",
            "选图片的方式和窗口背景一样：可以从电脑挑一张，也可以直接用 Windows 自带的壁纸。"
            "自己选的会复制一份保存。",
            "图片以「填满」的方式铺开，超出的部分裁掉，不会把比例拉变形。",
            "浓度滑条决定图片被压暗的程度，范围 20%–95%；越高越接近这一页原本的底色。",
        ],
    ),
    "zh-Hant": (
        "動畫背景",
        "設定頁面可以改動動畫畫在什麼上面：預設漸層、你選的兩個顏色，或是一張圖片。它同時"
        "作用於預覽、匯出的影片和封面圖——三者由同一個繪製器繪製，所以不會出現「預覽好看、"
        "檔案裡不一樣」的情況。",
        [
            "選顏色時要給上下兩個色階，畫面便在兩者之間過渡。深色更合適：畫格內所有文字都是"
            "淺色，淺色底會讓數字難以辨認。",
            "選圖片的方式和視窗背景一樣：可以從電腦挑一張，也可以直接用 Windows 內建的桌布。"
            "自己選的會複製一份保存。",
            "圖片以「填滿」的方式鋪開，超出的部分裁掉，不會把比例拉變形。",
            "濃度滑桿決定圖片被壓暗的程度，範圍 20%–95%；越高越接近這一頁原本的底色。",
        ],
    ),
}


def main():
    files = sorted(f for f in os.listdir(ROOT) if f.startswith("help-") and f.endswith(".md"))
    assert len(files) == 14, files

    for name in files:
        tag = name[len("help-"):-len(".md")]
        assert tag in CHAPTERS, tag
        title, intro, bullets = CHAPTERS[tag]

        path = os.path.join(ROOT, name)
        with open(path, "rb") as f:
            text = f.read().decode("utf-8-sig")

        if ("## " + title + "\n") in text:
            print("%s: 已有该节，跳过" % tag)
            continue

        # 第 12 个 `## ` 标题（「数据…」那一节）之前插入，正好接在「背景图片」之后
        marks = [i for i in range(len(text)) if text.startswith("## ", i)]
        assert len(marks) >= 12, (tag, len(marks))
        at = marks[11]
        # 退回行首
        at = text.rindex("\n", 0, at) + 1

        lines = ["## " + title, "", intro]
        for b in bullets:
            lines += ["", "- " + b]
        block = "\n".join(lines) + "\n\n"

        text = text[:at] + block + text[at:]

        with open(path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))

        print("%s: +1 节（第 12 节前）" % tag)

    # 章节数一致性校验
    counts = {}
    for name in files:
        tag = name[len("help-"):-len(".md")]
        with open(os.path.join(ROOT, name), "rb") as f:
            body = f.read().decode("utf-8-sig")
        counts[tag] = sum(1 for i in range(len(body)) if body.startswith("## ", i))
    print("章节数:", counts)
    print("一致:", len(set(counts.values())) == 1)


if __name__ == "__main__":
    main()
