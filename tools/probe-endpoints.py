#!/usr/bin/env python3
"""For one code, list every (endpoint, adjustment) pair that answers with an
adjusted series — and walk the whole history, not just the last 640 bars.

Usage: python tools/probe-endpoints.py usPDD.OQ usGLD.AM hk01810 sh688981
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HK = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

OLDEST = "2013-01-01"


def fetch(endpoint: str, code: str, adjustment: str, start: str, end: str) -> dict:
    param = f"{code},day,{start},{end},640,{adjustment}"
    uri = f"{endpoint}?{urllib.parse.urlencode({'param': param})}"
    try:
        request = urllib.request.Request(uri, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:
        return {"__error__": str(exc)}


def blocks(payload: dict, code: str) -> dict:
    node = (payload.get("data") or {}).get(code) or {}
    return {k: len(v) for k, v in node.items() if isinstance(v, list)}


def walk(endpoint: str, code: str, adjustment: str, start: str, end: str, pages: int = 24):
    """Walk backwards the way HistoryWalk does, returning every bar from `start` on."""
    out = []
    cursor = end
    for _ in range(pages):
        payload = fetch(endpoint, code, adjustment, start, cursor)
        node = (payload.get("data") or {}).get(code) or {}
        which = adjustment + "day" if node.get(adjustment + "day") else "day"
        rows = node.get(which) or []
        if not rows:
            break
        for row in rows:
            try:
                out.append((row[0], float(row[2])))
            except (TypeError, ValueError, IndexError):
                continue
        earliest = min(r[0] for r in rows)
        if earliest <= start:
            break
        nxt = shift(earliest, -1)
        if nxt >= cursor:
            break
        cursor = nxt
    return sorted(set(out)), which


def shift(day: str, days: int) -> str:
    import datetime
    d = datetime.date.fromisoformat(day) + datetime.timedelta(days=days)
    return d.isoformat()


def worst(points):
    w, when = 0.0, ""
    for i in range(1, len(points)):
        a, b = points[i - 1][1], points[i][1]
        if a <= 0 or b <= 0:
            continue
        d = (b - a) / a
        if d < w:
            w, when = d, points[i][0]
    return w, when


def main() -> None:
    codes = sys.argv[1:] or ["usPDD.OQ"]
    end = "2026-09-30"

    for code in codes:
        print(f"\n=== {code} ===")
        endpoints = [GENERAL, US if code.startswith("us") else HK]
        if not code.startswith("us"):
            endpoints = [GENERAL, HK]

        for endpoint in dict.fromkeys(endpoints + [US, HK, GENERAL]):
            if endpoint == HK and not code.startswith("hk"):
                continue
            if endpoint == US and not code.startswith("us"):
                continue
            for adjustment in ("qfq", "hfq"):
                probe = fetch(endpoint, code, adjustment, "2024-01-01", end)
                if "__error__" in probe:
                    print(f"  {endpoint.rsplit('/',2)[-2]:<12} {adjustment:<4} 请求失败")
                    continue
                b = blocks(probe, code)
                print(f"  {endpoint.rsplit('/',2)[-2]:<12} {adjustment:<4} {b}")

        for endpoint, adjustment in ((US, "qfq"), (US, "hfq"), (HK, "hfq"), (GENERAL, "hfq"), (GENERAL, "qfq")):
            if endpoint == US and not code.startswith("us"):
                continue
            if endpoint == HK and not code.startswith("hk"):
                continue
            points, which = walk(endpoint, code, adjustment, OLDEST, end)
            if not points:
                continue
            w, when = worst(points)
            print(f"  全史 {endpoint.rsplit('/',2)[-2]:<12} {adjustment:<4} -> {which:<7} "
                  f"{len(points):>5} 根 {points[0][0]}..{points[-1][0]}  最大单日跌 {w*100:7.2f}% {when}")


if __name__ == "__main__":
    main()
