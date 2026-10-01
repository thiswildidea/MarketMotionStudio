#!/usr/bin/env python
"""What each of the US venue guesses actually returns, period by period.

A US code written without an exchange suffix is quotable only after the suffix is
guessed, so the app asks `.OQ`, then `.N`, then `.AM`, then the bare code and takes
the first that answers with a real history. An index has no suffix at all, and the
day period on one of them came back from the app as "no day bars in that range"
while the week and the month on the same code drew fine — so which candidate answers
for which period is the whole question, and it is cheaper asked here than through
the page.

Run:  python tools/probe-us-candidates.py
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import date

US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

SUFFIXES = [".OQ", ".N", ".AM"]
COUNT = 640


def fetch(code, period, end):
    """The app's CandlesFromAsync, reduced to a count per block."""
    param = f"{code},{period},,{end:%Y-%m-%d},{COUNT},qfq"
    uri = f"{US}?{urllib.parse.urlencode({'param': param})}"

    with urllib.request.urlopen(uri, timeout=25) as response:
        root = json.load(response)

    if root.get("code") != 0:
        return f"envelope {root.get('code')}: {root.get('msg')}"

    node = (root.get("data") or {}).get(code)
    if node is None:
        return "no node"

    blocks = sorted(k for k in node if isinstance(node[k], list))

    if not blocks:
        return f"no array blocks at all (keys: {sorted(node)})"

    # The field count matters as much as the row count: a row the app cannot read
    # six fields out of is dropped one at a time, so a block of six hundred rows
    # arrives as an empty list and reads as an instrument with no history.
    described = []

    for key in blocks:
        rows = node[key]
        widths = sorted({len(r) for r in rows if isinstance(r, list)})
        first = rows[0][:5] if rows and isinstance(rows[0], list) else None
        described.append(f"{key}={len(rows)}x{widths} first={first}")

    return ", ".join(described)


def main():
    end = date.today()
    codes = ["usDJI", "usIXIC", "usAAPL", "usAAPL.OQ", "usSPY.AM"]

    for code in codes:
        tries = [code + s for s in SUFFIXES] + [code] if "." not in code[2:] else [code]

        for period in ("day", "week", "month"):
            for candidate in tries:
                print(f"  {candidate:14s} {period:6s} {fetch(candidate, period, end)}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
