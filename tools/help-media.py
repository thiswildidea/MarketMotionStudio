# -*- coding: utf-8 -*-
"""Build the pictures the help documents show.

The store screenshots are whole windows: a navigation rail, a title bar and a
status strip around the part that matters. Dropped into the manual at the
manual's own column width, the page itself would be a smudge. Cropped to the
content area they print at roughly one to one and the controls stay legible.

One set per language, taken from that language's own screenshots, so a
Japanese manual shows a Japanese window. The renderer picks the language
folder and falls back to the shared one when a language has no picture.

Sources: artifacts/store-screens/<lang>/NN-<page>.png (already 3x-scaled
window captures). Output: src/MarketMotionStudio/Assets/Help/media/<lang>/
"""

import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "artifacts", "store-screens")
DST = os.path.join(ROOT, "src", "MarketMotionStudio", "Assets", "Help", "media")

LANGS = [
    "zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de",
    "es", "fr", "it", "pl", "pt-BR", "cs", "ru", "tr",
]

# Screenshot file -> picture name used by the help documents.
PAGES = [
    ("02-sector-race.png", "sector-race"),
    ("03-gain-calendar.png", "gain-calendar"),
    ("04-monthly-matrix.png", "monthly-matrix"),
    ("05-dca-plan.png", "dca-plan"),
    ("06-position.png", "position"),
]

# The window capture, in its own pixels: title bar and navigation rail off the
# left, the status strip off the bottom, the window border off the right.
# Measured on the 1702x982 captures the screenshot script produces.
CROP = (400, 62, 1696, 946)

# Rendered at the manual's column width with room to spare; keeping more pixels
# than that only makes the package bigger, since XAML scales down anyway.
TARGET_WIDTH = 1400


def build_one(path_in, path_out):
    image = Image.open(path_in).convert("RGB")
    image = image.crop(CROP)

    if image.width > TARGET_WIDTH:
        height = round(image.height * TARGET_WIDTH / image.width)
        image = image.resize((TARGET_WIDTH, height), Image.LANCZOS)

    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    image.save(path_out, "PNG", optimize=True)
    return image.size, os.path.getsize(path_out)


def main():
    made = 0
    total = 0

    for lang in LANGS:
        for shot, name in PAGES:
            src = os.path.join(SRC, lang, shot)

            if not os.path.exists(src):
                print(f"  ! missing source {lang}/{shot}")
                continue

            size, weight = build_one(src, os.path.join(DST, lang, name + ".png"))
            made += 1
            total += weight

            if lang == "zh-Hans":
                print(f"  {name}: {size[0]}x{size[1]}, {weight // 1024} KB")

    print(f"{made} pictures, {total / 1048576:.1f} MB total")
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main())
