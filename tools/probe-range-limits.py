#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What each endpoint actually answers, so the range menus can stop guessing.

Four pages offer a span and four different paths serve them:

  - **K线** — `CandleLoader`, which pages: six requests of at most 640, so the reach is a real
    6 × 640 whatever the endpoint's own ceiling is.
  - **成交量换手率** — `StockSeries.LoadDailyAsync` → `StockBarsAsync`, **one** request, and the
    count it sends is `Clamp(calendar days, 5, 640)`. Two things follow, and both are measured
    here rather than reasoned about: what a span past 640 days actually returns, and how many
    days the intraday endpoint offers at all.
  - **行业板块竞速** — `SectorSeries`, one `StockBarsAsync` per entrant, same ceiling.
  - **市值榜** — `MarketCapSeries` asks for 180 months in one request. A month is a bar, so 180
    months is 15 years of them; the question is whether the endpoint agrees.

The measurement that matters most is the first one. If the source honours `start`, a span past
640 days loses its *tail*; if it ignores `start` and answers with the most recent `count` bars, the
same span loses its *head* — and the page draws a shorter chart that looks entirely correct, which
is how the fifth page's own bug hid for as long as it did.

Usage: python tools/probe-range-limits.py
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta

UA = {"User-Agent": "Mozilla/5.0"}

GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HONGKONG = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
UNITED = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"
MINUTE = "https://web.ifzq.gtimg.cn/appstock/app/day/query"


def endpoint_and_adj(code):
    """Same routing as TencentKline.TotalReturn."""
    if code.startswith("hk"):
        return HONGKONG, "hfq"
    if code.startswith("us"):
        return UNITED, "qfq"
    return GENERAL, "hfq"


def ask(code, period, start, end, count):
    """One request, exactly as FetchFromAsync builds it."""
    endpoint, adj = endpoint_and_adj(code)
    suffix = {"day": "day", "week": "week", "month": "month"}[period]

    parameter = f"{code},{suffix},{start},{end},{count},{adj}"
    url = f"{endpoint}?param={urllib.parse.quote(parameter, safe=',-:.')}"

    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) \
        .read().decode("utf-8", "ignore")

    node = json.loads(raw).get("data", {}).get(code, {})

    for key in (f"{adj}{suffix}", suffix, f"qfq{suffix}", f"hfq{suffix}"):
        value = node.get(key)
        if isinstance(value, list) and value:
            return value, key

    return [], "-"


def section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


today = date.today()

# ---------------------------------------------------------------------------------------------
section("1) 日线单次：跨度超过 640 天时，丢的是头还是尾？")
# ---------------------------------------------------------------------------------------------

for code in ["sh600519", "hk00700", "usAAPL.OQ"]:
    for label, days in [("365 天（1 年）", 365), ("640 天（上限）", 640), ("1825 天（5 年）", 1825)]:
        start = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        count = max(5, min(days, 640))

        try:
            rows, key = ask(code, "day", start, end, count)
        except Exception as ex:  # noqa: BLE001
            print(f"{code:12s} {label:14s} ERROR {ex}")
            continue

        if not rows:
            print(f"{code:12s} {label:14s} EMPTY  key={key}")
            continue

        first, last = rows[0][0], rows[-1][0]
        head_lost = first > start
        print(f"{code:12s} {label:14s} count={count:4d}  要 {start} → 给 {first} .. {last}"
              f"  ({len(rows)} 根)  key={key}  头部缺={head_lost}")

# ---------------------------------------------------------------------------------------------
section("2) 日线分页：K线的 6 次 × 640 实际能走多久")
# ---------------------------------------------------------------------------------------------

for code in ["sh600519", "hk00700", "usAAPL.OQ"]:
    cursor = today
    seen = {}
    earliest = today.strftime("%Y-%m-%d")

    for request in range(6):
        start = (cursor - timedelta(days=640)).strftime("%Y-%m-%d")
        end = cursor.strftime("%Y-%m-%d")

        try:
            rows, _ = ask(code, "day", start, end, 640)
        except Exception as ex:  # noqa: BLE001
            print(f"{code:12s} 第 {request + 1} 次 ERROR {ex}")
            break

        if not rows:
            print(f"{code:12s} 第 {request + 1} 次 EMPTY，停在 {earliest}")
            break

        for row in rows:
            seen[row[0]] = row[2]

        new_earliest = min(seen)

        if new_earliest >= earliest:
            print(f"{code:12s} 第 {request + 1} 次没有任何新的，停在 {earliest}（共 {len(seen)} 根）")
            break

        earliest = new_earliest
        cursor = date.fromisoformat(earliest) - timedelta(days=1)

    print(f"{code:12s} 六次共 {len(seen)} 根，最早 {min(seen) if seen else '-'}")

# ---------------------------------------------------------------------------------------------
section("3) 周线 / 月线：一次请求实际给多少根")
# ---------------------------------------------------------------------------------------------

for period, wanted in [("week", 640), ("month", 430)]:
    for code in ["sh600519", "hk00700", "usAAPL.OQ", "sh000001", "hkHSI", "usINX"]:
        start = "1990-01-01"
        end = today.strftime("%Y-%m-%d")

        try:
            rows, key = ask(code, period, start, end, wanted)
        except Exception as ex:  # noqa: BLE001
            print(f"{period:6s} {code:12s} ERROR {ex}")
            continue

        span = f"{rows[0][0]} .. {rows[-1][0]}" if rows else "-"
        print(f"{period:6s} {code:12s} 要 {wanted} → 给 {len(rows):4d} 根  {span}  key={key}")

# ---------------------------------------------------------------------------------------------
section("4) 日内分时：day/query 到底给几个交易日")
# ---------------------------------------------------------------------------------------------

for code in ["sh600519", "hk00700", "usAAPL"]:
    url = f"{MINUTE}?code={urllib.parse.quote(code)}"

    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) \
            .read().decode("utf-8", "ignore")
        root = json.loads(raw)
    except Exception as ex:  # noqa: BLE001
        print(f"{code:12s} ERROR {ex}")
        continue

    holder = root.get("data")

    # The US answer is a list where the others are objects, which is the shape that makes
    # "no intraday mode on that market" a fact about the payload rather than a decision.
    if not isinstance(holder, dict):
        print(f"{code:12s} data 是 {type(holder).__name__}，不是对象 —— 美股没有日内分时")
        continue

    node = holder.get(code, {})
    days = node.get("data") if isinstance(node, dict) else None

    if not isinstance(days, list) or not days:
        print(f"{code:12s} EMPTY（状态 {root.get('code')}）")
        continue

    listed = []
    for day in days:
        points = len(day.get("data", [])) if isinstance(day, dict) else 0
        listed.append(f"{day.get('date')}({points} 点)")

    print(f"{code:12s} {len(days)} 个交易日: {'  '.join(listed)}")

# ---------------------------------------------------------------------------------------------
section("5) 市值榜：180 个月够不够页面给的每个区间")
# ---------------------------------------------------------------------------------------------

for code in ["sh600519", "hk00700", "usAAPL.OQ"]:
    for months in (120, 180):
        start = (today - timedelta(days=int(months * 30.44))).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        try:
            rows, _ = ask(code, "month", start, end, 180)
        except Exception as ex:  # noqa: BLE001
            print(f"{code:12s} {months} 个月 ERROR {ex}")
            continue

        span = f"{rows[0][0]} .. {rows[-1][0]}" if rows else "-"
        print(f"{code:12s} 要 {months:3d} 个月 → 给 {len(rows):3d} 根  {span}")

print()
print("done")
