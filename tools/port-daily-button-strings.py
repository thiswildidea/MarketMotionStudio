#!/usr/bin/env python3
"""Renames the sheet button to the block's own name, and drops the heading that named it.

The heading said 每日成交导入 and the button under it said 导入表格 — one block with two names and
only one of them doing anything. The button now carries the name, so the heading has nothing left
to say and is removed from the XAML; `PortfolioImportDaily.Text` goes with it, because an `x:Uid`
left in the resources for an element that no longer exists is a trap for the next person.

The values are rewritten rather than duplicated: a button is a verb, so the English is
"Import a day's fills" rather than the heading's noun phrase.

Idempotent: a file already carrying the new value is left alone. resw keeps its BOM and LF endings.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

BUTTON = {
    "zh-Hans": "每日成交导入",
    "zh-Hant": "每日成交匯入",
    "en-US": "Import a day's fills",
    "cs": "Importovat denní obchody",
    "de": "Tagesausführungen importieren",
    "es": "Importar operaciones del día",
    "fr": "Importer les opérations du jour",
    "it": "Importa le operazioni del giorno",
    "ja": "当日の約定を取り込む",
    "ko": "당일 거래 가져오기",
    "pl": "Importuj transakcje dnia",
    "pt-BR": "Importar operações do dia",
    "ru": "Импорт сделок за день",
    "tr": "Günün işlemlerini içe aktar",
}

BUTTON_KEY = "PortfolioImportSheet.Content"
HEADING_KEY = "PortfolioImportDaily.Text"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    changed = 0

    for lang, value in BUTTON.items():
        resw = STRINGS / lang / "Resources.resw"

        if not resw.exists():
            print(f"{lang}: MISSING FILE")
            continue

        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        before = text

        # The button's caption.
        text = re.sub(
            r'(<data name="%s"><value>).*?(</value></data>)' % re.escape(BUTTON_KEY),
            lambda m: m.group(1) + esc(value) + m.group(2),
            text,
            count=1,
        )

        # The heading that is no longer on any element.
        text = re.sub(
            r'^  <data name="%s"><value>.*?</value></data>\n' % re.escape(HEADING_KEY),
            "",
            text,
            flags=re.M,
        )

        if text == before:
            print(f"{lang}: already done")
            continue

        resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
        changed += 1
        print(f"{lang}: button -> {value!r}")

    print(f"changed {changed} files")


if __name__ == "__main__":
    main()
