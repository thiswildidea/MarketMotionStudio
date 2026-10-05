# -*- coding: utf-8 -*-
r"""把「持仓收益」两种推进方式的 resw 键注入 14 份 Resources.resw。

这一页原来只有一种走法：把整段区间一口气铺满，曲线从左端长到右端。现在它跟 **K 线页**
一样多一个「推进方式」——整段铺满 / 窗口滚动——以及只在滚动时才有意义的窗口天数。

**为什么不复用 K 线页那四个键。** 表面上「推进方式」「窗口滚动」两页是同一样东西，但
`CandleWindowLabel` 的单位是**根**（`Window (candles)` /「窗口根数」），而这一页的窗口是
**交易日**；`CandleMotionGrow` 是「逐根铺满」，这一页没有「根」。共用会逼着 14 种语言
各自去猜单位。而且**一个 resw 键只有一个 port 脚本负责**——K 线那四个键归
`port-candle-resw.py`，这一页的要归这里。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-position-motion-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 下拉框的标题。K 线页那个是「推进方式」/ `Motion`，这一页是同一件事，所以照叫。
LABEL = [
    "Motion", "Ablauf", "Animación", "Animation", "Animazione", "Animacja",
    "Animação", "Animace", "Animasyon", "Анимация", "進行", "진행 방식",
    "推進方式", "推进方式",
]

# 第一种：整段区间一次铺满，曲线从左端长到右端。
#
# 不能照抄 K 线页的「逐根铺满」/`Grow across the range`：那一页的单位是根，这一页是日子
# 连成的一条线，「整段」才是它在说的事。
GROW = [
    "Grow across the span", "Über die ganze Spanne", "Crecer por todo el periodo",
    "Tracer tout l'intervalle", "Tutto l'intervallo", "Cały zakres naraz",
    "Todo o período", "Celé období", "Aralığın tamamı", "Весь диапазон",
    "全区間を描く", "전체 구간 그리기", "整段鋪滿", "整段铺满",
]

# 第二种：拿一个固定长度的窗口，从区间起点走到终点。
SCROLL = [
    "Scroll a window", "Fenster weiterbewegen", "Desplazar una ventana",
    "Fenêtre glissante", "Finestra scorrevole", "Przesuwne okno",
    "Janela deslizante", "Posuvné okno", "Kayan pencere", "Скользящее окно",
    "窓をスクロール", "창 이동", "視窗滾動", "窗口滚动",
]

# 窗口里装多少个**交易日**。K 线页那个是 `Window (candles)`；这里换成日。
WINDOW = [
    "Window (days)", "Fenster (Tage)", "Ventana (días)", "Fenêtre (jours)",
    "Finestra (giorni)", "Okno (dni)", "Janela (dias)", "Okno (dny)",
    "Pencere (gün)", "Окно (дней)", "表示日数", "창 크기(일)",
    "視窗天數", "窗口天数",
]

ROWS = [
    ("PositionMotionLabel.Header", LABEL),
    ("PositionMotionGrow", GROW),
    ("PositionMotionScroll", SCROLL),
    ("PositionWindowLabel.Header", WINDOW),
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
