# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「动画背景」那一章补上「水印长什么样」这一条。

水印那张卡片原来只有开关与一句话；这一轮加了**字体**（系统里装的全部字体，每一项用该字体
渲染自己）、**颜色**（取色器）和**浓度**（不透明度，10% 起、最高 40%）。

**必须说清的三件事**，没有一件是从画面上能看出来的：

* **字体下拉里每一项都是用那款字体写的它自己。** 不写，用户以为那只是一个名字列表，挑一款要等
  导出才看得到 —— 而导出的画面在别的页上。
* **浓度才是「看不看得见」的那一个数。** 默认 10% 时白、琥珀、蓝出来都是同一层极淡的痕，
  光改颜色等于改了个看不见的东西。
* **最高 40%，而且拉满仍然画在数据之下。** 不说上界，用户会以为拉满就是盖住画面 —— 那正是这个
  设置存在的反面。

**插在那一章倒数第二条之后、最后一条之前**：最后一条是「默认那句话不跟着界面语言变」那句收尾
（归 `port-watermark-help.py`），它留在末尾；这一条讲的是水印本身，紧挨着讲水印的那一条。

**这一条必须后于 `port-watermark-help.py` 跑。** 那个脚本是把两条插在「当时最后一个条目之后」，
所以它先在时，最后一条就是它放进去的收尾句；顺序反过来，这一条会落在那条之后，读起来是收尾句
后面又接一句。两个脚本都幂等，跑错顺序不会插重，只会排错位置。

按**章节序号**定位（0-based 22 = 第 23 章「动画背景」），不按标题找：14 种语言的标题各不相同。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里
表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-watermark-look-help.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

# 0-based：「动画背景」是第 23 章。
CHAPTER = 22

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]

LOOK = {
    "en-US": "- **How the mark looks is yours too.** The font is any font installed on this "
             "machine — each entry in the list is drawn in the font it names —, the colour is "
             "whatever the picker gives, and the strength is how much of that colour is used: "
             "10% by default, up to 40%, and even at its strongest it is drawn under the data. "
             "All three reach the preview, the exported video and the cover image alike.",

    "de": "- **Wie das Zeichen aussieht, ist ebenfalls Ihres.** Die Schriftart ist jede auf "
          "diesem Rechner installierte — jeder Eintrag in der Liste ist in der Schrift gesetzt, "
          "die er nennt —, die Farbe jede, die der Wähler hergibt, und die Stärke ist, wie viel "
          "von dieser Farbe verwendet wird: standardmäßig 10%, bis zu 40%, und selbst am "
          "stärksten wird es unter den Daten gezeichnet. Alle drei gelten für Vorschau, "
          "exportiertes Video und Titelbild gleichermaßen.",

    "es": "- **El aspecto de la marca también es tuyo.** La fuente es cualquier fuente instalada "
          "en este equipo —cada entrada de la lista está escrita en la fuente que nombra—, el "
          "color es el que dé el selector, y la intensidad es cuánto de ese color se usa: 10% por "
          "defecto, hasta 40%, e incluso en su punto máximo se dibuja debajo de los datos. Las "
          "tres afectan igual a la vista previa, al vídeo exportado y a la imagen de portada.",

    "fr": "- **L'aspect de la marque vous appartient aussi.** La police est n'importe quelle "
          "police installée sur cette machine — chaque entrée de la liste est écrite dans la "
          "police qu'elle nomme —, la couleur est celle que donne le sélecteur, et l'intensité "
          "est la part de cette couleur utilisée : 10% par défaut, jusqu'à 40%, et même au "
          "maximum elle est dessinée sous les données. Ces trois réglages valent pour l'aperçu, "
          "la vidéo exportée et l'image de couverture.",

    "it": "- **Anche l'aspetto del segno è vostro.** Il carattere è qualsiasi carattere "
          "installato su questa macchina — ogni voce dell'elenco è scritta nel carattere che "
          "nomina —, il colore è quello che dà il selettore, e l'intensità è quanto di quel "
          "colore viene usato: 10% per impostazione predefinita, fino al 40%, e anche al massimo "
          "è disegnato sotto i dati. Tutte e tre valgono per anteprima, video esportato e "
          "immagine di copertina.",

    "pl": "- **Wygląd znaku też jest twój.** Font to dowolny font zainstalowany na tym komputerze "
          "— każda pozycja na liście jest napisana fontem, który wymienia —, kolor to ten, który "
          "da próbnik, a moc to, ile tego koloru zostanie użyte: domyślnie 10%, najwyżej 40%, i "
          "nawet przy najwyższym znak jest rysowany pod danymi. Wszystkie trzy dotyczą podglądu, "
          "eksportowanego wideo i okładki tak samo.",

    "pt-BR": "- **A aparência da marca também é sua.** A fonte é qualquer fonte instalada nesta "
             "máquina — cada item da lista é escrito na fonte que nomeia —, a cor é a que o "
             "seletor der, e a intensidade é quanto dessa cor é usado: 10% por padrão, até 40%, e "
             "mesmo no máximo ela é desenhada abaixo dos dados. As três valem para a "
             "pré-visualização, o vídeo exportado e a imagem de capa igualmente.",

    "cs": "- **Jak značka vypadá, je také vaše.** Písmo je jakékoli písmo nainstalované v tomto "
          "počítači — každá položka seznamu je napsána písmem, které uvádí —, barva je ta, kterou "
          "dá výběrník, a síla je, kolik z té barvy se použije: ve výchozím stavu 10%, nejvíce "
          "40%, a i na maximum je značka kreslena pod daty. Všechny tři platí pro náhled, "
          "exportované video i titulní obrázek stejně.",

    "tr": "- **İşaretin nasıl göründüğü de sizin.** Yazı tipi bu makinede yüklü herhangi bir yazı "
          "tipidir — listedeki her girdi, adını verdiği yazı tipiyle yazılır —, renk seçicinin "
          "verdiği renktir ve yoğunluk, o rengin ne kadarının kullanıldığıdır: varsayılan %10, en "
          "fazla %40 ve en yüksek değerde bile verilerin altına çizilir. Üçü de önizleme, dışa "
          "aktarılan video ve kapak görseli için aynı şekilde geçerlidir.",

    "ru": "- **Как знак выглядит, тоже ваше.** Шрифт — любой шрифт, установленный на этом "
          "компьютере: каждая строка списка набрана тем шрифтом, который она называет; цвет — "
          "любой, который даст палитра, а насыщенность — сколько этого цвета используется: по "
          "умолчанию 10%, максимум 40%, и даже на максимуме знак рисуется под данными. Все три "
          "относятся к предпросмотру, экспортированному видео и обложке одинаково.",

    "ja": "- **透かしの見た目も自分のものです。** フォントはこのマシンにインストールされている"
          "任意のフォント（リストのそれぞれの項目は、その項目が示すフォント自身で書かれています）、"
          "色はカラーピッカーで選んだもの、濃さはその色をどれだけ使うか——既定 10%、最大 40% で、"
          "最大でもデータの下に描かれます。三つともプレビュー、書き出した動画、カバー画像に同じ"
          "ように反映されます。",

    "ko": "- **워터마크의 모양도 직접 정할 수 있습니다.** 글꼴은 이 컴퓨터에 설치된 어떤 글꼴이든 "
          "고를 수 있습니다(목록의 각 항목은 그 항목이 가리키는 글꼴로 직접 쓰여 있습니다). 색은 색 "
          "선택기에서 고른 색, 진하기는 그 색을 얼마나 쓸지입니다. 기본값 10%, 최대 40%이며, 가장 "
          "높여도 데이터 아래에 그려집니다. 세 가지 모두 미리보기, 내보낸 영상, 커버 이미지에 "
          "똑같이 적용됩니다.",

    "zh-Hans": "- **水印的样子也是自己的：字体**可以选这台机器装的任何一款（下拉里每一项都是用那"
               "款字体写的它自己），**颜色**用取色器任选，**浓度**是不透明度，默认 10%、最高 "
               "40%——拉到最高它仍然画在数据之下。三项都同时作用于预览、导出的视频与封面图。",

    "zh-Hant": "- **浮水印的樣子也是自己的：字型**可以選這台機器裝的任何一款（下拉裡每一項都是用"
               "那款字型寫的它自己），**顏色**用取色器任選，**濃度**是不透明度，預設 10%、最高 "
               "40%——拉到最高它仍然畫在數據之下。三項都同時作用於預覽、匯出的影片與封面圖。",
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

        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        assert len(starts) > CHAPTER, f"{tag}: {len(starts)} chapters, need {CHAPTER + 1}"

        start = starts[CHAPTER]
        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)

        chapter = lines[start:end]

        # Idempotent: this entry is there already, so this chapter has been done.
        if any(line.strip() == LOOK[tag] for line in chapter):
            print(f"{tag:9} already there")
            continue

        bullets = [i for i, line in enumerate(chapter) if line.startswith("- ")]

        assert len(bullets) >= 2, f"{tag}: too few bullets in the backdrop chapter"

        # Before the last entry, which is the watermark chapter's closing line. This
        # one is about the mark itself, so it belongs next to the entry that is.
        last = bullets[-1]

        chapter = chapter[:last] + ["", LOOK[tag]] + chapter[last:]

        lines[start:end] = chapter

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1 bullet")


if __name__ == "__main__":
    main()
