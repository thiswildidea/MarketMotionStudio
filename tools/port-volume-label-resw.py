#!/usr/bin/env python
"""Gives the candle page's volume checkbox a label key of its own.

Two ways a key is asked for, and they need different names:

    Strings.Get("StockPanelVolume")   ->  an entry named exactly that
    x:Uid="Foo" on a CheckBox         ->  an entry named "Foo.Content"

The volume checkbox was written with `x:Uid="StockPanelVolume"`, borrowing the name
the frame labels its volume panel with. That key exists as a bare name, so nothing
complained — the checkbox simply rendered with no text beside it, which next to one
that *did* have its text reads as a styling fault.

Adding the missing `StockPanelVolume.Content` is the obvious repair and it does not
build: MakePri reads the dot as a qualifier separator, so `StockPanelVolume` would
be defined both as a resource and as the scope of `StockPanelVolume.Content`, and
resource creation fails with PRI278. A bare key and a `<key>.<Suffix>` key cannot
share a stem — which is presumably why the frame label and the checkbox label were
never the same name in the first place, and why the collision went unnoticed until
something asked for both.

So the checkbox gets its own stem, next to the average line's `CandleShowAverages`
and carrying the same word the frame's panel label does.

Run:  python tools/port-volume-label-resw.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRINGS = os.path.join(ROOT, "src", "MarketMotionStudio", "Strings")

SOURCE = "StockPanelVolume"
WANTED = "CandleShowVolume.Content"
ANCHOR = '<data name="CandleShowAverages.Content"><value>'
STALE = re.compile(r'\n\s*<data name="StockPanelVolume\.Content"><value>[^<]*</value></data>')


def main():
    tags = sorted(t for t in os.listdir(STRINGS)
                  if os.path.isdir(os.path.join(STRINGS, t)))

    if not tags:
        print("no resource folders found")
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

        # A first attempt at this fix added the colliding key; take it back out.
        text = STALE.sub("", text)

        if f'<data name="{WANTED}">' not in text:
            value = dict(re.findall(r'<data name="([^"]+)"><value>([^<]*)</value>', text)).get(SOURCE)

            if value is None:
                print(f"{tag}: no {SOURCE} to copy the word from")
                problems += 1
                continue

            at = text.index(ANCHOR)
            end = text.index("</data>", at) + len("</data>")
            text = text[:end] + f'\n  <data name="{WANTED}"><value>{value}</value></data>' + text[end:]

        if text != before:
            open(path, "wb").write(b"\xef\xbb\xbf" + text.encode("utf-8"))
            written += 1

    print(f"{len(tags)} languages, {written} written, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
