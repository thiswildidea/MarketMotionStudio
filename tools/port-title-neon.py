# -*- coding: utf-8 -*-
"""Adds the Neon title-skin label to all fourteen resource files.

One key: PortfolioPnlTitleNeon.Content, the seventh headline treatment (青银) added
after 白墨. The skin itself lives in Render/TitleSkin.cs; this is only its menu label.
Idempotent, and it keeps each file's BOM and LF endings the way it found them.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEY = "PortfolioPnlTitleNeon.Content"

ROWS = {
    "zh-Hans": "青银",
    "zh-Hant": "青銀",
    "en-US": "Neon silver",
    "ja": "青銀",
    "ko": "청은",
    "de": "Neon-Silber",
    "fr": "Argent néon",
    "es": "Plata neón",
    "it": "Argento neon",
    "pt-BR": "Prata neon",
    "ru": "Неоновое серебро",
    "pl": "Neonowe srebro",
    "cs": "Neonové stříbro",
    "tr": "Neon gümüş",
}

ANCHOR = '  <data name="PortfolioPnlTitleInk.Content">'


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
