# -*- coding: utf-8 -*-
r"""把「水印长什么样」这三个设置的 resw 键注入 14 份 Resources.resw。

水印那张卡片原来只有开关与一句话；这一轮加了**字体**（系统里装的全部字体）、**颜色**（取色器）
和**浓度**（不透明度百分比）。四个键，都是新加的这三个控件自己的。

**为什么不进 `port-watermark-resw.py`。** 一个 resw 键只有一个 port 脚本负责：那个脚本每次运行会
按基础名删掉自己那六个键再重写，把新键并进去，等于两个脚本抢同一批键，改一个的值会被另一个
按自己的那张表改回来。新键归这里，旧键仍归那里。

**三个标签都极短**（字体 / 颜色 / 浓度），因为它们上面一行是卡片标题、下面一条是反馈预览条 ——
在这张卡片上，标签多说一个字都是把预览条往下挤。浓度还多一句说明，因为「浓度」这个词本身没说
清它的上界：拉到最高水印仍然画在数据之下，不说这句话，用户会以为拉满就是盖上画面。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-watermark-look-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 字体 -----------------------------------------------------------------------
#
# 一个词，不是「Font family」：下拉里每一项都是用该字体渲染的自己，标签只要说这是哪一栏。

FONT = [
    "Font", "Schriftart", "Fuente", "Police", "Carattere", "Czcionka", "Fonte",
    "Písmo", "Yazı tipi", "Шрифт", "フォント", "글꼴", "字型", "字体",
]

# ---- 颜色 -----------------------------------------------------------------------

COLOUR = [
    "Colour", "Farbe", "Color", "Couleur", "Colore", "Kolor", "Cor", "Barva",
    "Renk", "Цвет", "色", "색상", "顏色", "颜色",
]

# ---- 浓度 -----------------------------------------------------------------------

STRENGTH = [
    "Strength", "Stärke", "Intensidad", "Intensité", "Intensità", "Intensywność",
    "Intensidade", "Síla", "Yoğunluk", "Насыщенность", "濃さ", "진하기", "濃度",
    "浓度",
]

# ---- 浓度的说明 -----------------------------------------------------------------
#
# 三件事：它管的是「用多少所选颜色」、越高越明显、以及**上界仍然画在数据之下**。第三件不说，
# 用户会以为拉满就是盖住画面，而那恰恰是这个设置存在的反面。

STRENGTH_NOTE = [
    "How much of the chosen colour is used. Higher is more visible; even at its "
    "strongest the mark is drawn under the data.",

    "Wie viel von der gewählten Farbe verwendet wird. Höher ist deutlicher; selbst "
    "am stärksten wird das Zeichen unter den Daten gezeichnet.",

    "Cuánto del color elegido se usa. Cuanto más alto, más visible; incluso en su "
    "punto máximo la marca se dibuja debajo de los datos.",

    "Quelle part de la couleur choisie est utilisée. Plus haut, plus visible ; même "
    "au maximum, la marque est dessinée sous les données.",

    "Quanto del colore scelto viene usato. Più alto, più visibile; anche al massimo "
    "il segno è disegnato sotto i dati.",

    "Ile wybranej barwy zostanie użyte. Wyżej — wyraźniej; nawet przy najwyższym "
    "ustawieniu znak jest rysowany pod danymi.",

    "Quanto da cor escolhida é usado. Mais alto, mais visível; mesmo no máximo a "
    "marca é desenhada abaixo dos dados.",

    "Kolik zvolené barvy se použije. Vyšší je viditelnější; i na maximum je značka "
    "kreslena pod daty.",

    "Seçilen rengin ne kadarının kullanılacağı. Yükseldikçe daha görünür olur; en "
    "yüksek değerde bile işaret verilerin altına çizilir.",

    "Сколько выбранного цвета используется. Выше — заметнее; даже на максимуме знак "
    "рисуется под данными.",

    "選んだ色をどれだけ使うか。高いほどはっきり見えます。最大でも透かしはデータの下に描かれ"
    "ます。",

    "선택한 색을 얼마나 쓸지. 높을수록 더 잘 보입니다. 가장 높여도 워터마크는 데이터 아래에 "
    "그려집니다.",

    "用多少所選的顏色。越高越明顯；即使拉到最高，浮水印仍然畫在數據之下。",

    "用多少所选的颜色。越高越明显；即使拉到最高，水印仍然画在数据之下。",
]

ROWS = [
    ("SettingsWatermarkFont.Header", FONT),
    ("SettingsWatermarkColour.Text", COLOUR),
    ("SettingsWatermarkStrength.Text", STRENGTH),
    ("SettingsWatermarkStrengthNote.Text", STRENGTH_NOTE),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
