#!/usr/bin/env python
"""Gives the candle page's empty-selection refusal a line of its own, in all fourteen
languages.

The page's instrument row became a switchboard: until the reader touches it the page
behaves exactly as it did — one instrument, named by the search or by a preset — and
afterwards what is fetched is whatever is switched on. Switching everything off is
therefore reachable for the first time, and it needs a sentence. The one other board
with the same row says "click a name to add it to the total", which is true there and
not here.

Idempotent: present already and the file is left alone. Files are written back as UTF-8
**with** a BOM and LF endings, which is what they are now; a resw without its BOM builds
and then reads as empty at run time.

Run:  <venv python> tools/port-candle-multi-resw.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRINGS = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")

WANTED = "CandlePickNone"

# Beside the other line this page reports a fetch with, which is where a reader who has
# just pressed 取数 and got nothing will look for the reason.
ANCHOR = '<data name="CandleFetched">'

VALUE = {
    "en-US": "No instrument is switched on. Click a name on your list to put it on the frame.",
    "de": "Kein Instrument ist eingeschaltet. Tippe einen Namen auf deiner Liste an, "
          "um es ins Bild zu nehmen.",
    "es": "Ningún instrumento está activado. Pulsa un nombre de tu lista para ponerlo "
          "en el gráfico.",
    "fr": "Aucun instrument n'est activé. Cliquez un nom de votre liste pour le mettre "
          "dans l'image.",
    "it": "Nessuno strumento è attivo. Tocca un nome nella tua lista per metterlo nel grafico.",
    "pl": "Żaden instrument nie jest włączony. Kliknij nazwę na swojej liście, aby "
          "umieścić ją na wykresie.",
    "pt-BR": "Nenhum instrumento está ativado. Toque um nome na sua lista para "
             "colocá-lo no gráfico.",
    "cs": "Žádný nástroj není zapnutý. Klikněte na název ve svém seznamu a vložte jej do grafu.",
    "tr": "Hiçbir enstrüman açık değil. Grafiğe eklemek için listenizdeki bir ada dokunun.",
    "ru": "Ни один инструмент не включён. Нажмите название в своём списке, "
          "чтобы добавить его в кадр.",
    "ja": "銘柄が選択されていません。リストの名前をクリックすると画面に追加されます。",
    "ko": "선택된 종목이 없습니다. 목록에서 이름을 눌러 화면에 추가하세요.",
    "zh-Hans": "没有选中任何标的。点清单里的一个名字把它放到画面上。",
    "zh-Hant": "沒有選中任何標的。點清單裡的一個名字把它放到畫面上。",
}


def main():
    tags = sorted(t for t in os.listdir(STRINGS)
                  if os.path.isdir(os.path.join(STRINGS, t)))

    if len(tags) != 14:
        print(f"expected 14 languages, found {len(tags)}")
        return 1

    if sorted(VALUE) != tags:
        print("the table and the folders disagree: %s" % (set(tags) ^ set(VALUE)))
        return 1

    written = 0
    problems = 0

    for tag in tags:
        path = os.path.join(STRINGS, tag, "Resources.resw")
        raw = open(path, "rb").read()

        if not raw.startswith(b"\xef\xbb\xbf"):
            print(f"{tag}: no BOM")
            problems += 1

        if raw.count(b"\r\n"):
            print(f"{tag}: CRLF line endings")
            problems += 1

        text = raw.decode("utf-8-sig")

        if WANTED in text:
            print(f"{tag:9} already there")
            continue

        if ANCHOR not in text:
            print(f"{tag}: the anchor {ANCHOR} is not in this file")
            problems += 1
            continue

        at = text.index(ANCHOR)
        end = text.index("</data>", at) + len("</data>")
        text = (text[:end]
                + f'\n  <data name="{WANTED}"><value>{VALUE[tag]}</value></data>'
                + text[end:])

        open(path, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
        written += 1
        print(f"{tag:9} written")

    print(f"\n{len(tags)} languages, {written} written, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
