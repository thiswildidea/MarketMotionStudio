# -*- coding: utf-8 -*-
"""Adds the Fire title-skin label to all fourteen resource files.

One key: PortfolioPnlTitleFire.Content, the fourth headline treatment (火焰) added
after 常规/镀金/金宋. The skin itself lives in Render/TitleSkin.cs; this is only its
menu label. Idempotent, and it keeps each file's BOM and LF endings the way it found them.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEY = "PortfolioPnlTitleFire.Content"

ROWS = {
    "zh-Hans": "火焰",
    "zh-Hant": "火焰",
    "en-US": "Flame",
    "ja": "フレイム",
    "ko": "플레임",
    "de": "Flamme",
    "fr": "Flamme",
    "es": "Llama",
    "it": "Fiamma",
    "pt-BR": "Chama",
    "ru": "Пламя",
    "pl": "Płomień",
    "cs": "Plamen",
    "tr": "Alev",
}

ANCHOR = '  <data name="PortfolioPnlTitleEngraved.Content">'


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
