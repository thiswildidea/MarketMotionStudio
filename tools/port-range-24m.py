#!/usr/bin/env python3
"""Inserts `StudioRange24M` into all fourteen resource files, after `StudioRange12M`.

The four pages that offer a span were all measured against the endpoints on 2026-10-02
(`tools/probe-range-limits.py`), and the day-line ones came out short in the same way:

  - The sector race and the volume page ask for one request each. That request carries 640 **bars**,
    which is about two and a half years of days — while the guard in both pages refused anything
    past 640 **days**, about one and three-quarter years. So the honest ceiling was neither: a
    two-year span fits with room to spare and was being turned away.
  - The candle page pages, and reaches fifteen years, while its longest daily entry was three.

Two years is the one step both need, and the two-year *label* does not exist: the files carry
last-month / three / six / twelve and then jump to three years, which is a different offer.
So this adds exactly one key — the key count goes 732 → 733, and every file gains the same one
line in the same place, which is what `verify-resw-uids.py` checks.

Idempotent: a file already carrying the key is left alone. BOM and LF are preserved.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

KEY = "StudioRange24M"

# Placed after `StudioRange12M` in every file, so the menus read in one order in every language.
ANCHOR = re.compile(r'( *<data name="StudioRange12M"><value>[^<]*</value></data>\n)')

LABELS = {
    "cs": "Poslední 2 roky",
    "de": "Letzte 2 Jahre",
    "en-US": "Last 2 years",
    "es": "Últimos 2 años",
    "fr": "2 dernières années",
    "it": "Ultimi 2 anni",
    "ja": "過去2年",
    "ko": "최근 2년",
    "pl": "Ostatnie 2 lata",
    "pt-BR": "Últimos 2 anos",
    "ru": "Последние 2 года",
    "tr": "Son 2 yıl",
    "zh-Hans": "近 2 年",
    "zh-Hant": "近 2 年",
}


def main():
    added = []
    skipped = []
    missing = []

    for folder in sorted(LABELS):
        path = STRINGS / folder / "Resources.resw"

        if not path.exists():
            missing.append(folder)
            continue

        text = path.read_text(encoding="utf-8-sig").lstrip("\ufeff")

        if f'<data name="{KEY}"' in text:
            skipped.append(folder)
            continue

        match = ANCHOR.search(text)

        if match is None:
            missing.append(folder)
            continue

        line = f'  <data name="{KEY}"><value>{LABELS[folder]}</value></data>\n'
        text = text[:match.end()] + line + text[match.end():]

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        added.append(folder)

    print(f"added   : {len(added)}  {' '.join(added)}")
    print(f"skipped : {len(skipped)}  {' '.join(skipped) or '-'}")
    print(f"problem : {len(missing)}  {' '.join(missing) or '-'}")

    counts = {}
    for folder in sorted(LABELS):
        path = STRINGS / folder / "Resources.resw"
        if path.exists():
            counts[folder] = len(re.findall(r'<data name="',
                                            path.read_text(encoding="utf-8-sig")))

    print(f"key counts: {sorted(set(counts.values()))}")


if __name__ == "__main__":
    main()
