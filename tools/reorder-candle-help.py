"""Moves the candle chapter up to sit right after the market-turnover chapter.

The manual reads in the order the navigation rail lists the pages, and the rail now
puts the candle page second. The chapter was written when it was seventh, so it sits
tenth in the file — after every other page chapter and before "Video".

Positioned by heading index rather than by matching a translated title, the same way
`port-candle-help.py` inserts it: the titles are exactly what differs between the
fourteen files. The chapter's own first line is taken from that script so this one can
tell whether the move has already happened — running it twice must change nothing.

Run:  <venv python> tools/reorder-candle-help.py
"""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# Where the chapter belongs: after `## 市场成交额` (index 2), before `## 成交量换手率`.
TARGET = 3

# Where it sits today: after `## 持仓收益` (index 8), before `## 视频` (index 10).
SOURCE = 9


def chapters(tag):
    """The candle chapter's own lines, from the script that authored them."""
    path = HERE / "port-candle-help.py"

    spec = importlib.util.spec_from_file_location("port_candle_help", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.SECTIONS[tag]


def main() -> int:
    written = 0
    skipped = 0

    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")

        crlf = "\r\n" in text
        joiner = "\r\n" if crlf else "\n"
        lines = text.split(joiner)

        headings = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(headings) < 11:
            print(f"{tag}: only {len(headings)} headings, expected at least 11")
            return 1

        wanted = chapters(tag).strip("\n").split("\n")[0].strip()

        if lines[headings[TARGET]].strip() == wanted:
            skipped += 1
            print(f"{tag:9} already there")
            continue

        at = next((i for i, h in enumerate(headings) if lines[h].strip() == wanted), None)

        if at is None:
            print(f"{tag}: the candle chapter is not in this file")
            return 1

        if at != SOURCE:
            print(f"{tag}: the candle chapter sits at heading {at}, not {SOURCE}")
            return 1

        block = lines[headings[at]:headings[at + 1]]
        rest = lines[:headings[at]] + lines[headings[at + 1]:]
        moved = rest[:headings[TARGET]] + block + rest[headings[TARGET]:]

        path.write_bytes(b"\xef\xbb\xbf" + joiner.join(moved).encode("utf-8"))

        written += 1
        print(f"{tag:9} moved")

    print(f"\n14 languages, {written} written, {skipped} already in place")

    return 0


if __name__ == "__main__":
    sys.exit(main())
