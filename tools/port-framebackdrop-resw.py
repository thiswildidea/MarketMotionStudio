# -*- coding: utf-8 -*-
"""把「动画背景」的 resw 键写入 14 份 resw。

译文是本技能自带的（没有上游工程可抄，与 port-background-resw.py 不同）。
字节级插入：读 utf-8-sig、写回 BOM + LF，统一插在 </root> 前，各语言键序一致。
可重复运行（已存在则跳过），末尾做键序哈希校验。
"""
import hashlib
import os

DST = r"D:/software/MarketMotionStudio/src/MarketMotionStudio/Strings"

# 键名按此顺序写入，所有语言必须一致
KEYS = [
    "SettingsFrameBackdropLabel.Text",
    "SettingsFrameBackdropNote.Text",
    "SettingsFrameBackdropKind.Text",
    "SettingsFrameBackdropDefault",
    "SettingsFrameBackdropColour",
    "SettingsFrameBackdropPicture",
    "SettingsFrameBackdropTop.Text",
    "SettingsFrameBackdropBottom.Text",
    "SettingsFrameBackdropColourNote.Text",
]

TEXT = {
    "en-US": [
        "Animation background",
        "What every animation frame is drawn on. It reaches the exported video and the cover "
        "image as well as the preview — all three are drawn by the same renderer.",
        "Background",
        "Default",
        "Colour",
        "Picture",
        "Top",
        "Bottom",
        "Dark colours suit these frames: every tone of text in them is light. On a light "
        "background the numbers are hard to read in the video.",
    ],
    "de": [
        "Animationshintergrund",
        "Worauf jedes Animationsbild gezeichnet wird. Er gilt für das exportierte Video und das "
        "Titelbild ebenso wie für die Vorschau – alle drei zeichnet derselbe Renderer.",
        "Hintergrund",
        "Standard",
        "Farbe",
        "Bild",
        "Oben",
        "Unten",
        "Dunkle Farben passen zu diesen Bildern: Jede Schriftfarbe darin ist hell. Auf hellem "
        "Grund sind die Zahlen im Video schwer zu lesen.",
    ],
    "es": [
        "Fondo de la animación",
        "Aquello sobre lo que se dibuja cada fotograma. Afecta al vídeo exportado y a la imagen "
        "de portada además de a la vista previa: los tres los dibuja el mismo motor de dibujo.",
        "Fondo",
        "Predeterminado",
        "Color",
        "Imagen",
        "Arriba",
        "Abajo",
        "Los colores oscuros convienen a estos fotogramas: todos los tonos de texto son claros. "
        "Sobre un fondo claro, las cifras se leen mal en el vídeo.",
    ],
    "fr": [
        "Fond de l'animation",
        "Sur quoi chaque image de l'animation est dessinée. Il s'applique à la vidéo exportée et "
        "à l'image de couverture aussi bien qu'à l'aperçu : les trois sont dessinés par le même "
        "moteur de rendu.",
        "Fond",
        "Par défaut",
        "Couleur",
        "Image",
        "Haut",
        "Bas",
        "Les couleurs sombres conviennent à ces images : toutes leurs teintes de texte sont "
        "claires. Sur un fond clair, les chiffres sont difficiles à lire dans la vidéo.",
    ],
    "it": [
        "Sfondo dell'animazione",
        "Ciò su cui viene disegnato ogni fotogramma. Vale per il video esportato e per "
        "l'immagine di copertina oltre che per l'anteprima: tutti e tre li disegna lo stesso "
        "renderer.",
        "Sfondo",
        "Predefinito",
        "Colore",
        "Immagine",
        "Sopra",
        "Sotto",
        "I colori scuri si adattano a questi fotogrammi: ogni tono di testo è chiaro. Su uno "
        "sfondo chiaro i numeri si leggono male nel video.",
    ],
    "pl": [
        "Tło animacji",
        "To, na czym rysowana jest każda klatka animacji. Dotyczy eksportowanego wideo i obrazu "
        "okładki tak samo jak podglądu — wszystkie trzy rysuje ten sam renderer.",
        "Tło",
        "Domyślne",
        "Kolor",
        "Obraz",
        "Góra",
        "Dół",
        "Tym klatkom pasują ciemne kolory: wszystkie odcienie tekstu są jasne. Na jasnym tle "
        "liczby są w wideo trudne do odczytania.",
    ],
    "pt-BR": [
        "Fundo da animação",
        "Aquilo sobre o que cada quadro é desenhado. Vale para o vídeo exportado e para a imagem "
        "de capa, além da pré-visualização — os três são desenhados pelo mesmo renderizador.",
        "Fundo",
        "Padrão",
        "Cor",
        "Imagem",
        "Topo",
        "Base",
        "Cores escuras combinam com estes quadros: todos os tons de texto são claros. Sobre um "
        "fundo claro, os números ficam difíceis de ler no vídeo.",
    ],
    "cs": [
        "Pozadí animace",
        "To, na co se kreslí každý snímek animace. Platí pro exportované video a titulní obrázek "
        "stejně jako pro náhled – všechny tři kreslí stejný renderer.",
        "Pozadí",
        "Výchozí",
        "Barva",
        "Obrázek",
        "Nahoře",
        "Dole",
        "Těmto snímkům sluší tmavé barvy: všechny odstíny textu jsou světlé. Na světlém pozadí "
        "se čísla ve videu špatně čtou.",
    ],
    "tr": [
        "Animasyon arka planı",
        "Her animasyon karesinin üzerine çizildiği şey. Önizlemenin yanı sıra dışa aktarılan "
        "videoya ve kapak görseline de uygulanır — üçünü de aynı oluşturucu çizer.",
        "Arka plan",
        "Varsayılan",
        "Renk",
        "Resim",
        "Üst",
        "Alt",
        "Bu karelere koyu renkler yakışır: içlerindeki her metin tonu açıktır. Açık bir arka "
        "planda sayılar videoda zor okunur.",
    ],
    "ru": [
        "Фон анимации",
        "То, на чём рисуется каждый кадр анимации. Относится и к экспортированному видео, и к "
        "обложке, и к предпросмотру — все три рисует один и тот же отрисовщик.",
        "Фон",
        "По умолчанию",
        "Цвет",
        "Изображение",
        "Сверху",
        "Снизу",
        "Этим кадрам идут тёмные цвета: все оттенки текста в них светлые. На светлом фоне числа "
        "в видео читаются плохо.",
    ],
    "ja": [
        "アニメーションの背景",
        "アニメーションの各フレームが描かれる土台です。プレビューだけでなく、書き出した動画と"
        "カバー画像にも同じものが使われます。三者は同じレンダラーが描いているためです。",
        "背景",
        "既定",
        "色",
        "画像",
        "上部",
        "下部",
        "これらのフレームには暗い色が向いています。文字の色はすべて明るい色だからです。明るい"
        "背景では動画内の数字が読みにくくなります。",
    ],
    "ko": [
        "애니메이션 배경",
        "애니메이션의 모든 프레임이 그려지는 바탕입니다. 미리보기뿐 아니라 내보낸 영상과 커버 "
        "이미지에도 적용됩니다. 세 가지 모두 같은 렌더러가 그리기 때문입니다.",
        "배경",
        "기본값",
        "색",
        "사진",
        "위쪽",
        "아래쪽",
        "이 프레임에는 어두운 색이 어울립니다. 글자 색이 모두 밝은 색이기 때문입니다. 밝은 "
        "배경에서는 영상 속 숫자가 잘 읽히지 않습니다.",
    ],
    "zh-Hans": [
        "动画背景",
        "每一帧动画画在什么上面。它同时作用于预览、导出的视频和封面图——三者由同一个渲染器"
        "绘制。",
        "背景",
        "默认",
        "颜色",
        "图片",
        "顶部",
        "底部",
        "深色更适合这些画面：帧内所有文字都是浅色。浅色背景会让视频里的数字难以辨认。",
    ],
    "zh-Hant": [
        "動畫背景",
        "每一格動畫畫在什麼上面。它同時作用於預覽、匯出的影片和封面圖——三者由同一個繪製器"
        "繪製。",
        "背景",
        "預設",
        "顏色",
        "圖片",
        "頂部",
        "底部",
        "深色更適合這些畫面：畫格內所有文字都是淺色。淺色背景會讓影片裡的數字難以辨認。",
    ],
}


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    languages = sorted(os.listdir(DST))
    assert len(languages) == 14, languages
    assert set(languages) == set(TEXT), set(languages) ^ set(TEXT)

    for tag in languages:
        values = TEXT[tag]
        assert len(values) == len(KEYS), tag

        dst_path = os.path.join(DST, tag, "Resources.resw")

        with open(dst_path, "rb") as f:
            text = f.read().decode("utf-8-sig")

        already = [k for k in KEYS if 'name="%s"' % k in text]
        if already:
            print("%s: 已存在 %s，跳过" % (tag, already))
            continue

        lines = "".join(
            '  <data name="%s" xml:space="preserve"><value>%s</value></data>\n' % (k, escape(v))
            for k, v in zip(KEYS, values)
        )

        end = text.rindex("</root>")
        nl = text.rindex("\n", 0, end)
        text = text[: nl + 1] + lines + text[nl + 1 :]

        with open(dst_path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))

        print("%s: +%d 键" % (tag, len(KEYS)))

    import xml.etree.ElementTree as ET

    sigs = set()
    for tag in languages:
        root = ET.parse(os.path.join(DST, tag, "Resources.resw")).getroot()
        names = [e.get("name") for e in root.findall("data")]
        sigs.add(hashlib.md5("|".join(names).encode()).hexdigest())
    print("键序哈希一致:", len(sigs) == 1, sigs)


if __name__ == "__main__":
    main()
