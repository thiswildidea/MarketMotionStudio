# -*- coding: utf-8 -*-
"""Adds the Aurum title-skin label to all fourteen resource files.

One key: PortfolioPnlTitleAurum.Content, the fifth headline treatment (青金) added
after 火焰. The skin itself lives in Render/TitleSkin.cs; this is only its menu label.
Idempotent, and it keeps each file's BOM and LF endings the way it found them.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEY = "PortfolioPnlTitleAurum.Content"

ROWS = {
    "zh-Hans": "青金",
    "zh-Hant": "青金",
    "en-US": "Aurum",
    "ja": "オーラム",
    "ko": "오럼",
    "de": "Aurum",
    "fr": "Aurum",
    "es": "Aurum",
    "it": "Aurum",
    "pt-BR": "Aurum",
    "ru": "Аурум",
    "pl": "Aurum",
    "cs": "Aurum",
    "tr": "Aurum",
}

ANCHOR = '  <data name="PortfolioPnlTitleFire.Content">'


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
