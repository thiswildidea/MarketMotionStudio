#!/usr/bin/env python3
"""Adds `PortfolioImportDay.Text` to all fourteen resource files.

The date picker used to carry its caption as its own `Header`, which laid the label on one line
and the three fields on the next. To put them on one line the caption becomes a `TextBlock`
beside the picker — and a `TextBlock` reads `<uid>.Text`, while the picker read `<uid>.Header`.

Both keys stay: `Header` is simply unused now, and deleting it would mean this script rewrites
history for no gain. Two suffixed keys under one name are fine — what the resource index refuses
is a name that is *both* a resource and a scope (PRI278), and there is no unsuffixed
`PortfolioImportDay` here.

Idempotent: a file already carrying `PortfolioImportDay.Text` is left alone. resw keeps its BOM
and LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

# The caption already exists as `.Header` in every language; this is the same text under the key
# a TextBlock looks for.
#
# **`.Header` has to go, and that is not tidiness.** `x:Uid` applies *every* sub-key of its uid as
# a property of the element: `PortfolioImportDay.Header` becomes `TextBlock.Header`, a property a
# TextBlock does not have, and the dialog then throws `XamlParseException: Unable to resolve
# property 'Header'` the moment it is constructed — from `InitializeComponent`, so the dialog never
# appears and the whole import button looks dead.
LEGACY = ("PortfolioImportDay.Header",)
TEXT = {
    "zh-Hans": "交易日期",
    "zh-Hant": "交易日期",
    "en-US": "Trading day",
    "cs": "Obchodní den",
    "de": "Handelstag",
    "es": "Día de negociación",
    "fr": "Jour de bourse",
    "it": "Giorno di contrattazione",
    "ja": "取引日",
    "ko": "거래일",
    "pl": "Dzień transakcyjny",
    "pt-BR": "Dia de negociação",
    "ru": "Торговый день",
    "tr": "İşlem günü",
}

KEY = "PortfolioImportDay.Text"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    changed = 0

    for lang, value in TEXT.items():
        resw = STRINGS / lang / "Resources.resw"

        if not resw.exists():
            print(f"{lang}: MISSING FILE")
            continue

        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        dropped = False

        for legacy in LEGACY:
            pattern = r'^  <data name="%s"><value>.*?</value></data>\n' % re.escape(legacy)

            if re.search(pattern, text, flags=re.M):
                text = re.sub(pattern, "", text, flags=re.M)
                dropped = True

        if f'name="{KEY}"' in text and not dropped:
            print(f"{lang}: already present")
            continue

        trimmed = text.rstrip()
        assert trimmed.endswith("</root>"), lang
        body = trimmed[: -len("</root>")].rstrip("\n")
        body += f'\n  <data name="{KEY}"><value>{esc(value)}</value></data>\n'

        resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + (body + "</root>\n").encode("utf-8"))
        changed += 1
        print(f"{lang}: added")

    print(f"changed {changed} files")


if __name__ == "__main__":
    main()
