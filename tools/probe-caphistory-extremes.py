# -*- coding: utf-8 -*-
r"""五粮液十年市值曲线的最低点与最高点，到底是多少？

`Assets/Help/help-*.md` 与 `Render/CapHistoryRenderer.cs` 的注释里各写了一个「最低值」，
两个数不一样（1,256 亿 / 1,001 亿），而最高点两处都说 13,097 亿。两个数不可能同时对。
这一段文案要说的是「最低点离底边只有几个像素」，说的是那个比例，所以两个都得同时对。

所以这里把同一个算式照搬一遍、连清洗规则一起复刻，去量那一对数出来是多少：
流通股本 = 成交量 ÷（换手率 / 100），取二十日居中中位数，市值 = 当日股价 × 股本。
差 1–2pp 是边界规则不同，差 10+ 才是算法分叉。这里只问三个数，不需要还原整个 md。

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-caphistory-extremes.py
"""
import json
import statistics
import urllib.parse
import urllib.request

KLINE = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

CODE = "sz000858"
NAME = "五粮液"

# 与前一轮口径一致：about a decade.
START = "2016-01-01"
END = "2026-10-07"

MEDIAN_SPAN = 20


def fetch(start, end):
    param = f"{CODE},day,{start},{end},640,"
    uri = f"{KLINE}?param={urllib.parse.quote(param)}"

    with urllib.request.urlopen(uri, timeout=25) as response:
        root = json.load(response)

    node = root["data"][CODE]

    for block in ("qfqday", "day"):
        rows = node.get(block) or []

        if rows:
            return block, rows

    return None, []


def walk():
    """倒着走，直到端点不再给出更早的行 —— 与 CapHistory.WalkAsync 同一个循环。"""
    rows = {}
    cursor = END
    earliest_seen = END
    block = None

    for _ in range(20):
        if cursor < START:
            break

        kind, bars = fetch(START, cursor)

        if not bars:
            break

        block = kind

        for bar in bars:
            if bar[0] < START:
                continue

            rows[bar[0]] = bar

        earliest = bars[0][0]

        if earliest >= earliest_seen or earliest <= START:
            break

        earliest_seen = earliest
        cursor = earliest

    return block, [rows[k] for k in sorted(rows)]


def number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def main():
    block, rows = walk()

    print(f"{CODE} {NAME}: {len(rows)} 行，块 = {block}")
    print(f"首行 {rows[0][0]}  末行 {rows[-1][0]}  行宽 {len(rows[-1])}")

    usable = []

    for row in rows:
        close = number(row[2])
        volume = number(row[5])
        rate = number(row[7]) if len(row) > 7 else None
        amount = number(row[8]) if len(row) > 8 else None

        if not (close and volume and rate and amount) or rate <= 0 or volume <= 0:
            continue

        usable.append((row[0], close, volume, rate, amount))

    print(f"可用行 {len(usable)} / {len(rows)}")

    # 手还是股：成交量 × 100 × 价 ≈ 成交额（万元）。比值靠近 1 → 这一列是手；靠近 100
    # → 它已经是股。两地相差一百倍，不需要调阈值 —— 照 C# 里 CountsShares 的写法：> 10
    # 就是当成股本来数的那一类。
    ratios = sorted(
        (v * 100.0 * c / 10_000.0) / a for (_, c, v, _, a) in usable if a > 0)

    median_ratio = statistics.median(ratios)
    per = 1.0 if median_ratio > 10 else 100.0

    print(f"成交量 × 100 × 价 ÷ 成交额 的中位数 = {median_ratio:.3f}  "
          f"→ 以{'股' if per == 1.0 else '手'}计")

    counts = [v * per / (r / 100.0) / 1e8 for (_, _, v, r, _) in usable]
    prices = [c for (_, c, _, _, _) in usable]

    caps = []

    half = MEDIAN_SPAN // 2

    for i, (day, close, _, _, _) in enumerate(usable):
        lo = max(0, i - half)
        hi = min(len(counts) - 1, lo + MEDIAN_SPAN - 1)
        window = sorted(counts[lo:hi + 1])

        settled = window[len(window) // 2] if len(window) % 2 else \
            (window[len(window) // 2 - 1] + window[len(window) // 2]) / 2.0

        caps.append((day, close * settled, settled))

    lo = min(caps, key=lambda c: c[1])
    hi = max(caps, key=lambda c: c[1])

    print()
    print(f"最低 {lo[1]:,.0f} 亿元   日期 {lo[0]}   股价 {prices[caps.index(lo)]:.2f}   股本 {lo[2]:.2f} 亿股")
    print(f"最高 {hi[1]:,.0f} 亿元   日期 {hi[0]}   股价 {prices[caps.index(hi)]:.2f}   股本 {hi[2]:.2f} 亿股")
    print(f"期末 {caps[-1][1]:,.0f} 亿元   日期 {caps[-1][0]}   股本 {caps[-1][2]:.2f} 亿股")
    print()
    print(f"最低 / 最高 = {lo[1] / hi[1]:.4f}  → 占面板高度的 {lo[1] / hi[1] * 100:.1f}%")


if __name__ == "__main__":
    main()
