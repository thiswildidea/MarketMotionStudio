# -*- coding: utf-8 -*-
r"""Which field of a daily row is the turnover amount, on each series shape?

The market-turnover page reads field [8] and calls it 成交额 in 万元. That was
measured on `day` rows, which is what composite indices come back as. But the app
prefers `qfqday` when it is non-empty, and **stocks come back as `qfqday`, with a
different width** — ten fields where an index's `day` row has eleven.

So "add stocks to this page" is not free: if the shorter row is laid out
differently, field [8] of it is some other number, and the chart would be drawn
from it without anything failing.

That is not hypothetical. Measured on 贵州茅台, 2026-09-30:

*   daily `qfqday` field [8]  = 479,725  → ¥48.0 亿 if 万元
*   intraday cumulative to 15:00 = ¥38.9 亿, and volume × price agrees with that

One of the two is wrong. This script finds out which, by asking the row to
incriminate itself: **volume × price ≈ amount** must hold on the true amount
field, so whichever index satisfies it is the amount.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-turnover-fields.py
"""

import json
import urllib.parse
import urllib.request

KLINE = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
MINUTE = "https://web.ifzq.gtimg.cn/appstock/app/day/query"

# A stock that answers on qfqday, one that answers on day, and an index — the
# three shapes the page would have to read.
POOL = [
    ("sh600519", "贵州茅台 (qfqday)"),
    ("sh688981", "中芯国际 (day)"),
    ("sh000001", "上证综指 (day, control)"),
]

DAY = "2026-09-30"


def daily(code):
    param = f"{code},day,2026-09-25,2026-10-04,10,qfq"
    uri = f"{KLINE}?param={urllib.parse.quote(param)}"

    with urllib.request.urlopen(uri, timeout=20) as response:
        return json.load(response)["data"][code]


def intraday(code):
    uri = f"{MINUTE}?code={urllib.parse.quote(code)}"

    with urllib.request.urlopen(uri, timeout=20) as response:
        root = json.load(response)

    days = root["data"][code]["data"]

    for day in days:
        if day.get("date") == "20260930":
            return day["data"]

    return []


def number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def main():
    for code, name in POOL:
        node = daily(code)
        minutes = intraday(code)

        print(f"\n=== {code}  {name} ===")

        # 日内：15:00 那一行是收盘时刻的累计成交额（元）。端点会补到 15:30，所以
        # 不能直接取末行 —— 补出来的那半小时带着盘后固定价格交易，比日线多。
        if minutes:
            at_close = [m for m in minutes if m.split()[0] == "1500"]

            for label, row in (("15:00", at_close[-1] if at_close else None),
                               ("末行", minutes[-1])):
                if row is None:
                    continue

                parts = row.split()
                print(f"  日内 {label} {parts}  → {number(parts[3]) / 1e8:,.2f} 亿元")

        for kind in ("qfqday", "day"):
            rows = node.get(kind) or []

            if not rows:
                continue

            row = next((r for r in rows if r[0] == DAY), rows[-1])
            print(f"\n  {kind} 行宽 {len(row)}: {row}")

            # 量 × 价 ≈ 额：只有真正的成交额字段能满足它。
            close = number(row[2])
            volume = number(row[5])

            if close and volume:
                print(f"    [2] 收盘 {close:>12.2f}   [5] 成交量 {volume:>15,.0f}")

                for index in range(len(row)):
                    value = number(row[index])

                    if value is None or value <= 0:
                        continue

                    # 量以「手」计，价以元计：手 × 100 × 价 = 元。
                    for lots, unit in ((100, "手"), (1, "股")):
                        implied = volume * lots * close

                        if implied <= 0:
                            continue

                        ratio = implied / value

                        if 0.9 < ratio < 1.1:
                            print(f"    → [{index}] = {value:>18,.2f}  "
                                  f"{unit}×价/该值 = {ratio:.3f}   ★ 成交额")

            print(f"    [8] = {number(row[8]) if len(row) > 8 else None}")


if __name__ == "__main__":
    main()
