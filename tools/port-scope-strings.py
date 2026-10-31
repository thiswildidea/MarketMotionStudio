"""Adds the book-scope captions to all fourteen resource files.

Three keys: the picker's own header (`PortfolioPnlScope.Header`) and its two items. The items are
`ComboBoxItem`s, so they carry `.Content` — the same trap the fee boxes fell into, where a plain
key leaves the control with a border and no words in it.

Idempotent: an existing key is left alone, and the file's BOM and LF endings are preserved by
editing the decoded text and writing it back the way it was read.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

ROWS = {
    "zh-Hans": ("持仓范围", "A股", "A股+港股通"),
    "zh-Hant": ("持倉範圍", "A股", "A股+港股通"),
    "en-US": ("Book", "A-shares", "A-shares + Stock Connect"),
    "ja": ("保有範囲", "A株", "A株＋港股通"),
    "ko": ("보유 범위", "A주", "A주+홍콩주식통"),
    "de": ("Bestand", "A-Aktien", "A-Aktien + Stock Connect"),
    "fr": ("Portefeuille", "Actions A", "Actions A + Stock Connect"),
    "es": ("Cartera", "Acciones A", "Acciones A + Stock Connect"),
    "it": ("Portafoglio", "Azioni A", "Azioni A + Stock Connect"),
    "pt-BR": ("Carteira", "Ações A", "Ações A + Stock Connect"),
    "ru": ("Портфель", "А-акции", "А-акции + Stock Connect"),
    "pl": ("Portfel", "Akcje A", "Akcje A + Stock Connect"),
    "cs": ("Portfolio", "Akcie A", "Akcie A + Stock Connect"),
    "tr": ("Portföy", "A hisseleri", "A hisseleri + Stock Connect"),
}

ANCHOR = '  <data name="PortfolioPnlFeeKongMinimum.Header">'


def esc(text: str) -> str:
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

    header, ashare, kong = ROWS[lang]
    wanted = [
        f'  <data name="PortfolioPnlScope.Header"><value>{esc(header)}</value></data>',
        f'  <data name="PortfolioScopeAShare.Content"><value>{esc(ashare)}</value></data>',
        f'  <data name="PortfolioScopeWithKong.Content"><value>{esc(kong)}</value></data>',
    ]

    missing = [line for line in wanted if line.split('"')[1] not in text]

    if not missing:
        print(f"{lang}: already present")
        continue

    at = text.index(ANCHOR)
    end = text.index("\n", at) + 1
    text = text[:end] + "\n".join(missing) + "\n" + text[end:]

    resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
    changed += 1
    print(f"{lang}: added {len(missing)}")

print("files changed:", changed)
