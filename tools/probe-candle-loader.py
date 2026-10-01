#!/usr/bin/env python
"""Replays CandleLoader.LoadAsync against the live source and prints what it gets.

The point is to see, for one (code, period, span) at a time, how many candles the
walk actually ends up holding — and therefore whether the "< 3 candles" guard in
LoadAsync fires. The app's own loop is re-implemented here rather than read out of
a log because what matters is the count at each pass, which is the one thing the
status bar does not say.

Run:  python tools/probe-candle-loader.py
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HK = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

MOST_BARS = 640
MOST_REQUESTS = 6


def total_return(code):
    if code.startswith("hk"):
        return HK, "hfq"
    if code.startswith("us"):
        return US, "qfq"
    return GENERAL, "hfq"


def settled(day, period, today):
    """The app's IsSettledFor: a week's or a month's bar is not finished until it is over."""
    if period == "week":
        # Monday as the week's first day, so a week's bar is settled once Monday has come.
        back = today.weekday()
        return day < today - timedelta(days=back)
    if period == "month":
        return day < date(today.year, today.month, 1)
    return day < today


def fetch(code, period, start, end, count):
    endpoint, adjustment = total_return(code)
    wanted = max(5, min(count, MOST_BARS))
    param = f"{code},{period},{start:%Y-%m-%d},{end:%Y-%m-%d},{wanted},{adjustment}"
    uri = f"{endpoint}?{urllib.parse.urlencode({'param': param})}"

    with urllib.request.urlopen(uri, timeout=20) as response:
        root = json.load(response)

    if root.get("code") != 0:
        raise RuntimeError(f"envelope {root.get('code')}: {root.get('msg')}")

    node = root.get("data", {}).get(code)
    if not node:
        raise RuntimeError("no node for this code")

    block = node.get(adjustment + period) or node.get(period) or []
    if not block:
        raise RuntimeError(f"no {adjustment + period} and no {period}")

    today = date.today()
    rows = []

    for bar in block:
        if len(bar) < 6:
            continue
        try:
            day = date.fromisoformat(bar[0])
            values = [float(bar[i]) for i in range(1, 5)]
        except (ValueError, TypeError):
            continue
        if day < start or day > end or not settled(day, period, today):
            continue
        if min(values) <= 0:
            continue
        rows.append((day, values))

    return rows, (adjustment + period if node.get(adjustment + period) else period)


def wanted_for(period, months):
    if period == "week":
        return round(months * (52.0 / 12))
    if period == "month":
        return months
    return round(months * (252.0 / 12))


def load(code, period, months):
    """LoadAsync, pass for pass. Returns (held count, [per-pass counts])."""
    today = date.today()
    start = today.replace(year=today.year - 40) if months <= 0 else add_months(today, -months)
    wanted = 0 if months <= 0 else wanted_for(period, months)
    per_request = max(5, min(wanted + 8 if wanted > 0 else MOST_BARS, MOST_BARS))

    held = {}
    cursor = today
    earliest_seen = today
    passes = []
    block_used = None

    for _ in range(MOST_REQUESTS):
        passes.append(len(held))

        if wanted > 0 and len(held) >= wanted:
            break

        try:
            page, block_used = fetch(code, period, start, cursor, per_request)
        except Exception as exc:  # noqa: BLE001 - the walk's own answer for a dead end
            passes.append(f"error: {exc}")
            break

        if not page:
            passes.append("empty")
            break

        for day, values in page:
            held[day] = values

        earliest = min(held)
        if earliest >= earliest_seen or earliest <= start:
            passes.append(f"stop at {earliest}")
            break

        earliest_seen = earliest
        cursor = earliest - timedelta(days=1)

    ordered = sorted(held)
    if wanted > 0 and len(ordered) > wanted:
        ordered = ordered[len(ordered) - wanted:]

    return len(ordered), passes, block_used, ordered[:1], ordered[-1:]


def add_months(day, months):
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def main():
    today = date.today()
    print(f"today {today}\n")

    cases = []

    for code in ("sh000001", "sh600519"):
        for period in ("day", "week", "month"):
            for months in (3, 12, 36, 120, 0):
                cases.append((code, period, months))

    for code in ("hkHSI", "hk00700", "usDJI", "usAAPL.OQ"):
        for period in ("day", "week", "month"):
            for months in (36, 120, 0):
                cases.append((code, period, months))

    failures = 0

    for code, period, months in cases:
        try:
            count, passes, block, first, last = load(code, period, months)
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {code:12s} {period:5s} {months:4d}  raised {exc}")
            failures += 1
            continue

        flag = "  <-- TOO FEW" if count < 3 else ""
        span = f"{first[0] if first else '-'}..{last[0] if last else '-'}"
        print(f"  {code:12s} {period:5s} {months:4d}  {count:5d} bars  "
              f"[{block}]  passes={passes}  {span}{flag}")

        if count < 3:
            failures += 1

    print(f"\n{len(cases)} cases, {failures} with fewer than three candles")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
