#!/usr/bin/env python3
"""Compare the path the app took before with the one it takes now.

Two measures, both of which a split or a heavy dividend used to wreck:

  monthly   the gain matrix. It used to ask the general endpoint for `qfq`, which
            for a Hong Kong or US code answers with unadjusted months and for an
            A-share heavy payer answers with negative closes — and a close at or
            below zero is dropped, so the matrix silently lost those months and
            read the gap as one month's move.
  daily     the race and the calendar. They used to ask for `qfq` too, with the
            same two failures, plus the missing split adjustment on a US code.

"dropped" counts months whose close is not positive, which is what the loader
skips. A non-zero count on the old path is a matrix that quietly lost rows.

Run: python tools/verify-total-return.py
"""

from __future__ import annotations

import datetime
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HK = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

NEWEST = "2026-09-30"
OLDEST_DAILY = "2013-01-01"


def total_return(code: str) -> tuple[str, str]:
    """TencentKline.TotalReturn, mirrored."""
    if code.startswith("hk"):
        return HK, "hfq"
    if code.startswith("us"):
        return US, "qfq"
    return GENERAL, "hfq"


def fetch(endpoint: str, code: str, adjustment: str, period: str, start: str, end: str) -> dict:
    param = f"{code},{period},{start},{end},{640 if period == 'day' else 130},{adjustment}"
    uri = f"{endpoint}?{urllib.parse.urlencode({'param': param})}"
    try:
        request = urllib.request.Request(uri, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except Exception:
        return {}


def rows_of(payload: dict, code: str, keys: tuple[str, ...]) -> tuple[str, list]:
    node = (payload.get("data") or {}).get(code) or {}
    for key in keys:
        block = node.get(key)
        if isinstance(block, list) and block:
            return key, block
    return "none", []


def closes(rows: list) -> list[tuple[str, float]]:
    out = []
    for row in rows:
        try:
            out.append((row[0], float(row[2])))
        except (TypeError, ValueError, IndexError):
            continue
    return out


def monthly(code: str) -> dict:
    endpoint, adjustment = total_return(code)
    _, new_rows = rows_of(fetch(endpoint, code, adjustment, "month", "", ""), code,
                          (adjustment + "month", "month"))
    _, old_rows = rows_of(fetch(GENERAL, code, "qfq", "month", "", ""), code, ("qfqmonth", "month"))

    def summarise(rows: list) -> tuple[int, int, float, str]:
        points = closes(rows)
        kept = [p for p in points if p[1] > 0]
        worst, when = 0.0, ""
        for i in range(1, len(kept)):
            change = (kept[i][1] / kept[i - 1][1] - 1) if kept[i - 1][1] > 0 else 0.0
            if change < worst:
                worst, when = change, kept[i][0]
        return len(points), len(points) - len(kept), worst, when

    return {"code": code, "new": summarise(new_rows), "old": summarise(old_rows)}


def walk(endpoint: str, code: str, adjustment: str, pages: int = 24) -> tuple[str, list, bool]:
    points: dict[str, float] = {}
    block = "none"
    has_amount = False
    cursor = NEWEST

    for _ in range(pages):
        found, rows = rows_of(fetch(endpoint, code, adjustment, "day", OLDEST_DAILY, cursor),
                              code, (adjustment + "day", "day"))
        if not rows:
            break
        block = found
        for row in rows:
            try:
                points[row[0]] = float(row[2])
            except (TypeError, ValueError, IndexError):
                continue
            if len(row) > 8:
                try:
                    if float(row[8]) > 0:
                        has_amount = True
                except (TypeError, ValueError):
                    pass
        earliest = min(r[0] for r in rows if isinstance(r[0], str))
        if earliest <= OLDEST_DAILY:
            break
        nxt = (datetime.date.fromisoformat(earliest) - datetime.timedelta(days=1)).isoformat()
        if nxt >= cursor:
            break
        cursor = nxt

    return block, sorted(points.items()), has_amount


def daily(code: str) -> dict:
    endpoint, adjustment = total_return(code)
    block, points, has_amount = walk(endpoint, code, adjustment)
    _, plain_points, _ = walk(GENERAL, code, "qfq")

    def worst(pts: list) -> tuple[float, str]:
        w, when = 0.0, ""
        for i in range(1, len(pts)):
            before, after = pts[i - 1][1], pts[i][1]
            if before <= 0 or after <= 0:
                continue
            drop = (after - before) / before
            if drop < w:
                w, when = drop, pts[i][0]
        return w, when

    # What FillTurnoverAsync does: the general endpoint's amount, where the
    # adjusted series carries none.
    filled = has_amount
    if not has_amount:
        _, _, plain_amount = walk(GENERAL, code, "qfq", pages=1)
        filled = plain_amount

    return {"code": code, "block": block, "bars": len(points), "drop": worst(points),
            "plain_drop": worst(plain_points), "amount": has_amount, "filled": filled}


CODES = [
    ("sh600519", "贵州茅台 A股高分红"),
    ("sh601318", "中国平安 A股高分红"),
    ("sz000858", "五粮液 A股高分红"),
    ("sh000001", "上证指数 A股指数"),
    ("hk00700", "腾讯控股 港股2014一拆五"),
    ("hk02333", "长城汽车 港股"),
    ("hkHSI", "恒生指数 港股指数"),
    ("usAAPL.OQ", "苹果 美股一拆四/一拆七"),
    ("usMSTR.OQ", "MicroStrategy 美股一拆十"),
    ("usGE.N", "通用电气 美股八合一"),
    ("usXLK.AM", "科技SPDR 美股ETF"),
    ("usDJI", "道琼斯 美股指数"),
]


def main() -> None:
    with ThreadPoolExecutor(max_workers=6) as pool:
        months = list(pool.map(monthly, [c for c, _ in CODES]))
        days = list(pool.map(daily, [c for c, _ in CODES]))

    labels = dict(CODES)

    print("【月线 · 收益矩阵】旧 = 通用端点 qfq　新 = 按市场走复权端点")
    print(f"{'标的':<26} {'代码':<11} {'旧丢弃月':>8} {'新丢弃月':>8} {'旧最差月':>10} {'新最差月':>10}")
    print("-" * 78)
    for r in months:
        old_total, old_dropped, old_worst, old_when = r["old"]
        new_total, new_dropped, new_worst, new_when = r["new"]
        flag = "  ← 修复" if old_dropped or old_worst < -0.45 else ""
        print(f"{labels[r['code']]:<26} {r['code']:<11} {old_dropped:>8} {new_dropped:>8} "
              f"{old_worst*100:>9.2f}% {new_worst*100:>9.2f}%{flag}")

    print()
    print("【日线 · 竞速/日历】成交额是否在复权序列里，缺失则由通用端点补")
    print(f"{'标的':<26} {'代码':<11} {'块':<8} {'根数':>5} {'复权最大单日跌':>12} {'未复权':>10} {'成交额':>8}")
    print("-" * 88)
    for r in days:
        amount = "有" if r["amount"] else ("补齐" if r["filled"] else "缺")
        flag = "  ← 修复" if r["plain_drop"][0] < -0.45 and r["drop"][0] > -0.35 else ""
        print(f"{labels[r['code']]:<26} {r['code']:<11} {r['block']:<8} {r['bars']:>5} "
              f"{r['drop'][0]*100:>11.2f}% {r['plain_drop'][0]*100:>9.2f}% {amount:>8}{flag}")


if __name__ == "__main__":
    main()
