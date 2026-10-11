# -*- coding: utf-8 -*-
"""Put a picture at the head of each manual chapter that has one.

**The chapter is looked up from the navigation, never written down here.** This
file used to hold `CHAPTERS = {4: ..., 5: ...}` — plain 1-based heading counts —
and by today those six numbers point at the wrong chapters: the manual has grown
past them, the page that a picture belongs to has moved, and nothing about the
script says so. `listingtext.chapter_of(key)` reads the order out of
`MainWindow.xaml`, so a chapter inserted anywhere moves every number below it.
(The old numbers would have put the sector-race picture in "Candles".)

The headings are translated, so matching on their text would need one table of
fourteen titles; the chapter *order* is the rule the manuals are held to, and it
is the same in all of them.

Idempotent: a chapter that already carries its own picture is left alone, so this
can be run again after adding a language. A chapter is asked "is *my* picture
here", not "is any picture here" — the difference matters the moment one is
inserted into the wrong chapter, which is a mistake this file can make.

One caption per language rather than one per chapter. The heading two lines
above already names the page; what the caption adds is what the reader is
looking at, and that is the same sentence every time.

The pictures themselves are cropped from the Store screenshots by
`help-media.py`; the crypto six are captured by `store-screenshots.py --crypto`,
since that market replaces the stock pages in the navigation rather than
joining them.

Run: python tools\\port-help-images.py
"""

import os
import pathlib
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

LANGS = listingtext.LANGS

# Navigation key -> picture file the chapter opens with.
PICTURES = [
    ("NavSectorRace", "sector-race.png"),
    ("NavMatrix", "monthly-matrix.png"),
    ("NavGainCalendar", "gain-calendar.png"),
    ("NavDcaPlan", "dca-plan.png"),
    ("NavPosition", "position.png"),
    # 加密六页：它们只在市场切成「加密货币」时在导航里，图片也是单独那趟拍的。
    ("NavCryptoCandle", "crypto-candle.png"),
    ("NavCryptoDca", "crypto-dca.png"),
    ("NavCryptoPosition", "crypto-position.png"),
    ("NavCryptoCalendar", "crypto-calendar.png"),
    ("NavCryptoCapHistory", "crypto-caphistory.png"),
    ("NavCryptoMarketCap", "crypto-marketcap.png"),
]

CAPTIONS = {
    "zh-Hans": "这一页的全貌：左侧预览、下方播放进度条、右侧参数面板。",
    "zh-Hant": "這一頁的全貌：左側預覽、下方播放進度條、右側參數面板。",
    "en-US": "The page in full: preview on the left, scrubber below, settings on the right.",
    "ja": "このページの全景：左がプレビュー、下が再生スライダー、右が設定パネルです。",
    "ko": "이 페이지의 전체 모습: 왼쪽 미리보기, 아래 재생 슬라이더, 오른쪽 설정 패널.",
    "de": "Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.",
    "es": "La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.",
    "fr": "La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.",
    "it": "La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.",
    "pl": "Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.",
    "pt-BR": "A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.",
    "cs": "Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.",
    "ru": "Страница целиком: предпросмотр слева, полоса воспроизведения снизу, настройки справа.",
    "tr": "Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.",
}


def add_pictures(text, lang, joiner):
    """插好之后返回 (新文本, 图的总数, [(章节键, 那一章现在点的图)])。"""
    lines = text.split(joiner)
    caption = CAPTIONS[lang]
    wrong = []

    # 从后往前插：从前往后插会让后面每一章的行号整体后移。
    for key, picture in reversed(PICTURES):
        index = listingtext.chapter_of(key)

        if index < 0:
            raise SystemExit(f"  ! 导航里没有 {key}")

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if index >= len(heads):
            raise SystemExit(f"  ! {lang} 只有 {len(heads)} 章，第 {index} 章不在")

        start = heads[index]
        end = heads[index + 1] if index + 1 < len(heads) else len(lines)
        wanted = f"![{caption}](media/{picture})"
        here = [line for line in lines[start:end] if line.startswith("![")]

        if here:
            # 已经有一张 —— 是这一张才算对。**不修**：插错图是个该有人看的问题，顺手再补
            # 一张只会让这一章带两张图，而两张都在那一章的正文里，读的人分不清哪张是准的。
            if wanted not in here:
                wrong.append((key, here[0]))

            continue

        # 标题、空行、图、空行、正文 —— 与已有的五张同一个摆法。
        lines[start + 1:start + 1] = ["", wanted]

    return joiner.join(lines), sum(1 for line in lines if line.startswith("![")), wrong


def main():
    failures = []

    for lang in LANGS:
        path = HELP / f"help-{lang}.md"

        if not path.exists():
            failures.append(f"{lang}: no document")
            continue

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig").lstrip("\ufeff")
        joiner = "\r\n" if "\r\n" in text else "\n"

        updated, pictures, wrong = add_pictures(text, lang, joiner)

        if pictures != len(PICTURES):
            failures.append(f"{lang}: {pictures} pictures, expected {len(PICTURES)}")

        for key, said in wrong:
            failures.append(f"{lang}: {key} 那一章点的是 {said!r}")

        if updated != text:
            # 写回字节：read_text/write_text 会把行尾归一化，那会让整份文件变成一处巨大的
            # 改动（本机 core.autocrlf，而手册是 LF）。
            path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + updated.encode("utf-8"))
            changed = "+"
        else:
            changed = "="

        print(f"  {changed} {lang}: {pictures} pictures, {len(updated.split(joiner))} lines")

    if failures:
        print("\n".join("  ! " + item for item in failures))
        return 1

    print("all fourteen documents carry the same %d pictures" % len(PICTURES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
