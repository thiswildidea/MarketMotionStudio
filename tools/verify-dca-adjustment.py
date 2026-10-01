# -*- coding: utf-8 -*-
"""验证定投 / 持仓两个页面取到的价格序列是否含分红与拆股。

两个页面共用的 `HistoryWalk` 要的是一条「任意两天之比 = 持有者真实总回报」的序列，
也就是复权价。源端只在 A 股上直接给得出（`newfqkline` + `hfq` → `hfqday`）；
港股有专门的 `hkfqkline` + `hfq`，美股只有 `usfqkline` + `qfq`（前复权，与后复权
只差一个全局常数因子，在「份额 = 金额 / 价」「市值 = 份额 × 价」里正好抵消）。
修复前三个市场统一走 `newfqkline` + `hfq`，港美股拿到的都是不复权的 `day`。

脚本把 `TencentKline.TotalReturn` 的选择规则和 `HistoryWalk.ClosesAsync` 的回溯照抄
一遍，两条路各跑一次，看三件事：

1. 序列里还有没有拆股指纹（单日涨跌超过 25%）——不复权的话腾讯 2014 一拆五是
   -78.83%、苹果 2020 一拆四是 -74.15%；
2. 定投出来的收益率差多少；
3. 回退到 `day` 的只有本来就没有除权的标的（指数、从未分派过的信托）。

用法：
    python tools/verify-dca-adjustment.py
"""
import json
import urllib.request
import urllib.parse
import datetime
import sys

UA = {"User-Agent": "MarketMotionStudio/0.1", "Referer": "https://gu.qq.com/"}
NEW = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HK = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

MOST_BARS = 640
MOST_REQUESTS = 20


def total_return(code):
    """TencentKline.TotalReturn 的规则。"""
    if code.startswith("hk"):
        return HK, "hfq"
    if code.startswith("us"):
        return US, "qfq"
    return NEW, "hfq"


def page(code, endpoint, adjustment, start, end):
    """一次请求，返回该窗口内的 {交易日: 收盘}，空窗口是合法答案。"""
    span = (end - start).days
    count = max(5, min(span, MOST_BARS))
    param = f"{code},day,{start:%Y-%m-%d},{end:%Y-%m-%d},{count},{adjustment}"
    uri = f"{endpoint}?param={urllib.parse.quote(param)}"
    req = urllib.request.Request(uri, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        doc = json.loads(r.read().decode("utf-8"))
    if doc.get("code") != 0:
        raise RuntimeError("envelope %s" % doc.get("code"))
    node = (doc.get("data") or {}).get(code)
    if not isinstance(node, dict):
        raise RuntimeError("no node")
    for key in (adjustment + "day", "day"):
        rows = node.get(key)
        if isinstance(rows, list) and rows:
            out = {}
            for row in rows:
                try:
                    day = datetime.date.fromisoformat(row[0])
                    close = float(row[2])
                except (ValueError, IndexError, TypeError):
                    continue
                if start <= day <= end and close > 0:
                    out[day] = close
            return out, key
    raise RuntimeError("no bars block")


def walk(code, endpoint, adjustment, start, end):
    """HistoryWalk.ClosesAsync 的回溯。"""
    closes = {}
    cursor = end
    earliest_seen = end
    blocks = set()

    for _ in range(MOST_REQUESTS):
        rows, key = page(code, endpoint, adjustment, start, cursor)
        blocks.add(key)
        closes.update(rows)
        if not rows:
            break
        earliest = min(rows)
        if earliest >= earliest_seen or earliest <= start:
            break
        earliest_seen = earliest
        cursor = earliest - datetime.timedelta(days=1)

    return dict(sorted(closes.items())), blocks


def worst_gap(closes):
    """序列里最大的单日跳空——拆股没处理的指纹。"""
    days = list(closes)
    worst = (0.0, None, 0.0, 0.0)
    for a, b in zip(days, days[1:]):
        change = closes[b] / closes[a] - 1
        if abs(change) > abs(worst[0]):
            worst = (change, b, closes[a], closes[b])
    return worst


def dca(closes, amount=10000.0):
    """DcaPlanner 的月度定投：每月首个交易日买入金额 / 收盘。"""
    shares = 0.0
    invested = 0.0
    last_month = None
    for day, close in closes.items():
        if close <= 0:
            continue
        if last_month != day.month:
            shares += amount / close
            invested += amount
            last_month = day.month
    value = shares * closes[list(closes)[-1]]
    return invested, value, (value / invested - 1) * 100 if invested else 0.0


YEARS = 13
END = datetime.date(2026, 10, 1)
START = END.replace(year=END.year - YEARS)

CASES = [
    ("sh510300", "沪深300ETF", "A股"),
    ("sh601318", "中国平安", "A股·高分红"),
    ("hk00700", "腾讯控股", "港股·2014一拆五"),
    ("hk00005", "汇丰控股", "港股·高分红"),
    ("hk02800", "盈富基金", "港股"),
    ("usAAPL.OQ", "苹果", "美股·2020一拆四"),
    ("usSPY.AM", "标普500ETF", "美股"),
    ("usTSLA.OQ", "特斯拉", "美股·2020拆5/2022拆3"),
]

FAILURES = []


def main():
    print(f"区间 {START} .. {END}（{YEARS} 年），月度定投 10000/期\n")
    print(f"{'标的':<14}{'市场':<16}{'修复前 块':<10}{'最大单日':>10}   "
          f"{'修复后 块':<10}{'最大单日':>10}   {'收益率 前':>9} {'收益率 后':>9}")
    print("-" * 108)

    for code, name, market in CASES:
        before, blocks_before = walk(code, NEW, "hfq", START, END)
        endpoint, adjustment = total_return(code)
        after, blocks_after = walk(code, endpoint, adjustment, START, END)

        if not before or not after:
            print(f"{name:<14}{market:<16} 数据不足 before={len(before)} after={len(after)}")
            FAILURES.append(name)
            continue

        gap_before = worst_gap(before)
        gap_after = worst_gap(after)
        _, _, ret_before = dca(before)
        invested, value, ret_after = dca(after)

        flag = ""
        if abs(gap_before[0]) > 0.25:
            flag += "  <<< 拆股指纹"
        if abs(gap_after[0]) > 0.25:
            flag += "  !!! 修复后仍有跳空"
            FAILURES.append(name + "(跳空未消除)")

        print(f"{name:<14}{market:<16}{'/'.join(blocks_before):<10}"
              f"{gap_before[0]*100:>9.2f}%   "
              f"{'/'.join(blocks_after):<10}{gap_after[0]*100:>9.2f}%   "
              f"{ret_before:>8.1f}% {ret_after:>8.1f}%{flag}")

    print()
    print("修复后回退到 day 的（应当只有指数 / 从不分派的信托）:")
    for code, name, market in CASES:
        endpoint, adjustment = total_return(code)
        _, blocks = walk(code, endpoint, adjustment, START, END)
        if blocks == {"day"}:
            print(f"  {name} ({code})")

    print()
    if FAILURES:
        print("FAIL:", ", ".join(FAILURES))
        sys.exit(2)
    print("全部通过：复权序列无拆股指纹")


if __name__ == "__main__":
    main()
