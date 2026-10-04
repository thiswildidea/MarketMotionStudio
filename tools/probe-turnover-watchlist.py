# -*- coding: utf-8 -*-
r"""Can the market-turnover page be driven by a watchlist instead of a board?

The page today sums **whole-board turnover**, read off composite indices
(`sh000001` + `sz399106`, ...). Each index's daily amount is field [8] of the
general K-line endpoint, in 万元, divided by 10 000 to 亿元.

A watchlist would sum **one person's own stocks** the same way, so the question is
whether the same field means the same thing on a stock row. Three things can go
wrong and each is checked separately, because each fails differently:

1. **Does a stock row carry an amount at all, in the same unit?** If field [8] is
   absent or in a different unit, the sum is off by 10 000 and the chart is silently
   a hundred-million-fold wrong.
2. **Does `qfq` (the adjustment this endpoint is pinned to) break the close?** The
   return series is a ratio of consecutive closes. On a heavy payer the forward
   adjusted series puts historical closes *below zero*, and a ratio between two
   negative numbers is not a return. Measured on 贵州茅台 below.
3. **Do the dates line up?** The page keeps only days *every* fetched code has.
   Indices trade every session, so today that rule never bites. A stock that halts
   for a day would drop that day from the chart — and a missing day on this chart
   looks exactly like a quiet day, which is the failure this project keeps
   running into.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-turnover-watchlist.py
"""

import json
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

ENDPOINT = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

# Two heavy payers (the qfq trap), two ordinary large caps, and one that is
# plausibly thin. Plus the two composites the page uses today, as the control.
POOL = [
    ("sh600519", "贵州茅台"),
    ("sh601398", "工商银行"),
    ("sz000858", "五 粮 液"),
    ("sz000001", "平安银行"),
    ("sh688981", "中芯国际"),
    ("sh000001", "上证综指 (control)"),
    ("sz399106", "深证综指 (control)"),
]

DAYS = 90


def fetch(code, start, end, adj="qfq"):
    """Both series the endpoint can hand back, kept apart.

    The app prefers `qfqday` when it is non-empty and falls back to `day`. That
    preference is the whole question here: the two series are **not the same
    shape**, and if the adjusted one is the short one then a stock fetched by this
    method carries no amount at all — which is what "个股没有数据" means.
    """
    param = f"{code},day,{start},{end},{DAYS},{adj}"
    uri = f"{ENDPOINT}?param={urllib.parse.quote(param)}"

    with urllib.request.urlopen(uri, timeout=20) as response:
        root = json.load(response)

    if root.get("code") != 0:
        return None, f"envelope code {root.get('code')}"

    node = root.get("data", {}).get(code, {})

    return {"qfqday": node.get("qfqday") or [], "day": node.get("day") or []}, "ok"


def main():
    end = date.today()
    start = end - timedelta(days=DAYS)

    print(f"窗口 {start} .. {end}  ({DAYS} 天)\n")
    print("每个代码两种序列各一行：`qfqday`（应用优先取的）与 `day`（兜底）。")
    print("成交额在字段 [8]；行宽 < 9 就是这一行根本没有成交额。\n")
    print(f"{'代码':10s} {'名称':16s} {'序列':8s} {'行':>4s} {'字段':>5s} "
          f"{'末日':>12s} {'末日成交额(万元)':>17s} {'最低收盘':>10s}")
    print("-" * 96)

    series = {}
    detailed = {}

    for code, name in POOL:
        got, note = fetch(code, start, end)

        if got is None:
            print(f"{code:10s} {name:16s}  {note}")
            continue

        detailed[code] = got

        for kind in ("qfqday", "day"):
            rows = got[kind]

            if not rows:
                print(f"{code:10s} {name:16s} {kind:8s}   （空）")
                continue

            width = len(rows[0])
            bars = {}

            for row in rows:
                bars[row[0]] = (
                    float(row[2]),
                    float(row[8]) if len(row) > 8 else None,
                )

            days = sorted(bars)
            last_close, last_amount = bars[days[-1]]
            lowest = min(c for c, _ in bars.values())

            # 应用优先 qfqday、为空才落回 day，这里照做：一条序列记一次就够。
            if kind == "qfqday" or not series.get(code):
                if last_amount is not None:
                    series[code] = bars

            amount = "—" if last_amount is None else f"{last_amount:,.0f}"
            flag = "   × 收盘为负" if lowest <= 0 else ""

            print(f"{code:10s} {name:16s} {kind:8s} {len(rows):4d} {width:5d} "
                  f"{days[-1]:>12s} {amount:>17s} {lowest:10.2f}{flag}")

        print()

    # ---- 3. 日期是否对齐 ----
    # 两个 control 是合成指数，不是自选里的股票，必须按名字排除 —— 按代码后缀排除会把
    # 深证综指 sz399106 留在篮子里，于是「自选合计」其实是「自选 + 整个深市」。
    controls = {"sh000001", "sz399106"}
    stocks = [c for c, _ in POOL if c in series and c not in controls]
    print("\n日期对齐（只比个股，不含指数）:")

    all_days = set()
    for code in stocks:
        all_days |= set(series[code])

    per_code = {c: set(series[c]) for c in stocks}
    common = set.intersection(*per_code.values()) if per_code else set()

    print(f"  并集 {len(all_days)} 天，交集 {len(common)} 天，差 {len(all_days) - len(common)} 天")

    for code in stocks:
        missing = sorted(all_days - per_code[code])
        if missing:
            print(f"  {code} 缺 {len(missing)} 天: {missing[:6]}")

    # ---- 1. 单位与量级 ----
    print("\n自选合计 vs 全市场（末日，亿元）:")

    last = max(common) if common else None
    if last:
        basket = [c for c in stocks if c in series]
        total = sum(series[c][last][1] for c in basket) / 10_000
        market = sum(series[c][last][1] for c in ("sh000001", "sz399106")
                     if c in series) / 10_000
        print(f"  {len(basket)} 只自选合计 {total:12.2f} 亿元")
        print(f"  两市合计       {market:12.2f} 亿元")
        print(f"  自选占两市     {total / market * 100:11.3f}%")

    # ---- 2. qfq 是否把收盘价压到 0 以下 ----
    print("\nqfq 下的最低收盘价（负 = 涨跌幅口径不可用）:")

    for code, name in POOL:
        if code not in series:
            continue
        lowest = min(c for c, _ in series[code].values())
        mark = "  × 出现负值" if lowest <= 0 else ""
        print(f"  {code:10s} {name:18s} {lowest:12.2f}{mark}")


if __name__ == "__main__":
    main()
