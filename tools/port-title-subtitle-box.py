# -*- coding: utf-8 -*-
"""Adds the subtitle box label to all fourteen resource files.

One key: StudioSubtitleText.Text, the label over the subtitle text box in the shared
video panel. Idempotent, and it keeps each file's BOM and LF endings the way it found them.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEY = "StudioSubtitleText.Text"

ROWS = {
    "zh-Hans": "副标题",
    "zh-Hant": "副標題",
    "en-US": "Subtitle",
    "ja": "サブタイトル",
    "ko": "부제목",
    "de": "Untertitel",
    "fr": "Sous-titre",
    "es": "Subtítulo",
    "it": "Sottotitolo",
    "pt-BR": "Subtítulo",
    "ru": "Подзаголовок",
    "pl": "Podtytuł",
    "cs": "Podtitul",
    "tr": "Alt başlık",
}

ANCHOR = '  <data name="StudioTitleText.Header">'


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


changed = 0

for resw in sorted(ROOT.glob("*/Resources.resw")):
    lang = resw.parent.name

    if lang not in ROWS:
        print(f"{lang}: no row")
        continue

    raw = resw.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    wanted = f'  <data name="{KEY}"><value>{esc(ROWS[lang])}</value></data>'

    if KEY in text:
        print(f"{lang}: already present")
        continue

    at = text.index(ANCHOR)
    end = text.index("\n", at) + 1
    text = text[:end] + wanted + "\n" + text[end:]

    resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
    changed += 1
    print(f"{lang}: added")


print(f"\n{changed} file(s) changed")
