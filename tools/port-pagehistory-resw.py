#!/usr/bin/env python
"""Inject the page-history keys (back / forward) into all fourteen resource files.

Ported from AgolAdminKit, whose two title-bar buttons carry the same words. Their
values are copied, not re-translated: the four source keys are read per language
and written under this app's plainer key names, because MarketMotionStudio has never
used the ``[using:...]`` form — its buttons are named in code, the way the Settings
item's update button already is.

Idempotent: an earlier injection of the same four keys is removed first.
The byte order mark and the LF endings are preserved, and the key order is hashed
across the fourteen files so a partial run cannot pass unnoticed.
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = pathlib.Path(r"D:\software\AgolAdminKit\src\AgolAdminKit\Strings")
TARGET = ROOT / "src" / "MarketMotionStudio" / "Strings"

TAGS = "en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hans zh-Hant".split()

# Source key -> the key this app uses. The plain one names the button for screen
# readers, the Tip one is what hovering shows, shortcut included.
MAPPING = [
    ("NavHistoryBack.[using:Microsoft.UI.Xaml.Automation]AutomationProperties.Name", "NavHistoryBack"),
    ("NavHistoryBack.[using:Microsoft.UI.Xaml.Controls]ToolTipService.ToolTip", "NavHistoryBackTip"),
    ("NavHistoryForward.[using:Microsoft.UI.Xaml.Automation]AutomationProperties.Name", "NavHistoryForward"),
    ("NavHistoryForward.[using:Microsoft.UI.Xaml.Controls]ToolTipService.ToolTip", "NavHistoryForwardTip"),
]

KEY_LINE = re.compile(
    r'^[ \t]*<data name="(' + "|".join(re.escape(k) for k, _ in MAPPING) + r')"><value>.*?</value></data>[ \t]*\r?\n',
    re.M | re.S,
)


def read(path: pathlib.Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def write(path: pathlib.Path, text: str) -> None:
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))


def source_values(tag: str) -> dict[str, str]:
    text = read(SOURCE / tag / "Resources.resw")
    values = {}

    for source_key, target_key in MAPPING:
        match = re.search(
            r'<data name="' + re.escape(source_key) + r'"><value>(.*?)</value>',
            text,
            re.S,
        )

        if match is None:
            sys.exit(f"{tag}: missing source key {source_key}")

        values[target_key] = match.group(1)

    return values


def main() -> None:
    digests = {}

    for tag in TAGS:
        values = source_values(tag)
        path = TARGET / tag / "Resources.resw"
        text = read(path)
        text = KEY_LINE.sub("", text)

        block = "".join(
            f'  <data name="{key}"><value>{values[key]}</value></data>\n'
            for _, key in MAPPING
        )

        marker = "</root>"

        if marker not in text:
            sys.exit(f"{tag}: no </root> to insert before")

        text = text.replace(marker, block + marker, 1)
        write(path, text)

        keys = re.findall(r'<data name="([^"]+)"', text)
        digests[tag] = (len(keys), hashlib.md5("\n".join(keys).encode("utf-8")).hexdigest()[:12])
        print(f"{tag:8s} {len(keys):4d} keys  {digests[tag][1]}  {values['NavHistoryBack']} / {values['NavHistoryForward']}")

    distinct = set(digests.values())

    if len(distinct) != 1:
        sys.exit(f"key order differs across languages: {digests}")

    print(f"OK  14 files agree: {distinct.pop()}")


if __name__ == "__main__":
    main()
