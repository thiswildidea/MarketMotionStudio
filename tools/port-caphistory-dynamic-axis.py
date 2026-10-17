"""One-shot: add the CapHistoryDynamicAxis checkbox label to every language resw.

Preserves the resw convention (UTF-8 BOM, LF) used across the project. Idempotent:
skips any file that already contains the key. Labels mirror port-position-dynamic-axis.py,
since the feature is the same "dynamic vertical axis" idea applied to the cap-history page.
"""
import os

BASE = r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings"

LABELS = {
    "en-US": "Dynamic vertical axis",
    "de": "Dynamische Y-Achse",
    "es": "Eje vertical dinámico",
    "fr": "Axe vertical dynamique",
    "it": "Asse verticale dinamico",
    "pl": "Dynamiczna oś pionowa",
    "pt-BR": "Eixo vertical dinâmico",
    "cs": "Dynamická svislá osa",
    "tr": "Dinamik dikey eksen",
    "ru": "Динамическая вертикальная ось",
    "ja": "縦軸を動的に調整",
    "ko": "세로축 동적 조정",
    "zh-Hant": "動態縱軸",
    "zh-Hans": "动态纵轴",
}

KEY = "CapHistoryDynamicAxis.Content"

for lang, label in LABELS.items():
    path = os.path.join(BASE, lang, "Resources.resw")
    if not os.path.exists(path):
        print(f"skip (missing): {path}")
        continue
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    if KEY in text:
        print(f"skip (present): {lang}")
        continue
    entry = f'  <data name="{KEY}"><value>{label}</value></data>'
    if "</root>" in text:
        text = text.replace("</root>", entry + "\n</root>", 1)
    else:
        text = text + "\n" + entry + "\n"
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(text)
    print(f"added: {lang} = {label}")
