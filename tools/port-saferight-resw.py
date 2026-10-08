#!/usr/bin/env python
"""Gives the three end-label pages' "may the picture cross the safe line" checkbox a
label key of its own, in all fourteen languages.

One key for three pages, not one per page. The checkbox is the same question on all
three — whether the picture may run into the band the host covers with its button
rail — and a key per page would be three translations of one sentence, which is how
the same setting ends up described three different ways.

`x:Uid` on a CheckBox asks for `<name>.Content`, and a bare key cannot share a stem
with one of those (MakePri reads the dot as a qualifier and refuses the pair,
PRI278) — hence a stem of its own, `SafeRightCross`, used by nothing else.

Idempotent: present already and the file is left alone. Files are written back as
UTF-8 **with** a BOM and LF endings, which is what they are now; a resw without its
BOM builds and then reads as empty at run time.

Run:  <venv python> tools/port-saferight-resw.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRINGS = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")

WANTED = "SafeRightCross.Content"

# Next to the other frame-wide look settings, which is where a reader who has just
# been told about the title row will go looking for it.
ANCHOR = '<data name="StudioHideTitleNote.Text">'

VALUE = {
    "en-US": "Let the chart cross the right safe line",
    "de": "Die Grafik die rechte Sicherheitslinie überschreiten lassen",
    "es": "Permitir que el gráfico cruce la línea de seguridad derecha",
    "fr": "Laisser le graphique dépasser la ligne de sécurité à droite",
    "it": "Consentire al grafico di superare la linea di sicurezza a destra",
    "pl": "Pozwól wykresowi przekroczyć prawą linię bezpieczeństwa",
    "pt-BR": "Permitir que o gráfico cruze a linha de segurança à direita",
    "cs": "Nechat graf překročit pravou bezpečnou linii",
    "tr": "Grafiğin sağ güvenli çizgiyi aşmasına izin ver",
    "ru": "Позволить графику заходить за правую безопасную линию",
    "ja": "右側のセーフラインを越えて描画する",
    "ko": "오른쪽 안전선을 넘어 그리기",
    "zh-Hans": "允许图形越过右侧安全线",
    "zh-Hant": "允許圖形越過右側安全線",
}


def main():
    tags = sorted(t for t in os.listdir(STRINGS)
                  if os.path.isdir(os.path.join(STRINGS, t)))

    if len(tags) != 14:
        print(f"expected 14 languages, found {len(tags)}")
        return 1

    if sorted(VALUE) != tags:
        print("the table and the folders disagree: %s" %
              (set(tags) ^ set(VALUE)))
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
        before = text

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

        if text != before:
            open(path, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
            written += 1
            print(f"{tag:9} written")

    print(f"\n{len(tags)} languages, {written} written, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
