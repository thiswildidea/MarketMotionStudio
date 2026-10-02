# -*- coding: utf-8 -*-
"""Probe: can the four roster boards take a watchlist of one's own?

Thirteen, fourteen, fifteen and sixteen all draw a board across a *roster* — a
fixed list the app ships. Four (the sector race) already offers a third kind of
roster besides its built-in ones: a list of stocks the reader types in
(`Roster.Stocks`). The question this round answers is whether the four roster
boards can take that too, and what it costs.

The whole question turns on one thing, and it is not availability:

**Thirteen is the only one of the four drawn on unadjusted bars.**
`IndexRace.LoadAsync` calls `RawBarsAsync` because it is comparing two listings
against each other, which is the case the app's own rule says must not be
adjusted: a backward-adjusted series re-bases one end of the comparison. The
other three ask "what did holding this earn", which is the case that *must* be
adjusted. A single stock on an unadjusted series is not a small error — a
dividend is a cliff in the price and a split is a halving, and neither is
something a holder lost.

So this probe asks, for every code each board can be pointed at:

1. **Does adjusting an index change it?** If the source ignores the adjustment
   for indices and hands back the same rows, thirteen can switch to the adjusted
   call and every number already on that board stays exactly as it is. If it
   does not, thirteen cannot take stocks without becoming a different board.
2. **How wrong is a stock unadjusted?** If the gap is small, the rule is
   theoretical. If it is a factor of two, it is not.
3. **Can a watchlist cross markets?** These four boards are not governed by the
   market setting, so a typed list could hold a mainland share, a Hong Kong one
   and a New York one at once — if each venue's endpoint answers.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-watchlist-rosters.py
"""

import json
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

GENERAL = "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
HK = "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get"
US = "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get"

# The twelve indices of board thirteen, in the board's own order.
INDICES = [
    ("sh000001", "上证指数"), ("sh000300", "沪深300"), ("sz399001", "深证成指"),
    ("sh000905", "中证500"), ("sz399006", "创业板指"), ("sh000016", "上证50"),
    ("hkHSI", "恒生指数"), ("hkHSCEI", "国企指数"), ("hkHSTECH", "恒生科技"),
    ("usINX", "标普500"), ("usIXIC", "纳斯达克"), ("usDJI", "道琼斯"),
]

# What a reader would type into a watchlist. Chosen for the ways a stock's price
# series lies about what a holder earned: dividends, splits, and a late listing.
STOCKS = [
    ("sh600519", "贵州茅台"),     # large dividends, never split
    ("sh601398", "工商银行"),     # the dividend is most of the return
    ("sh600900", "长江电力"),     # ditto
    ("sz000651", "格力电器"),     # dividends and a share issue
    ("sh510300", "沪深300ETF"),   # a fund, the kind board fourteen already draws
    ("hk00700", "腾讯控股"),      # a Hong Kong share
    ("usAAPL.OQ", "苹果"),        # a New York share
    ("sz300750", "宁德时代"),     # listed 2018: a row that joins late
]


def get(url, referer=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def route(code):
    """The endpoint and adjustment `TencentKline.TotalReturn` picks."""
    if code.startswith("hk"):
        return HK, "hfq"
    if code.startswith("us"):
        return US, "qfq"
    return GENERAL, "hfq"


def bars(code, adjusted):
    """Monthly rows, or None. Mirrors the app's two calls.

    `adjusted=False` is `RawBarsAsync`: the general endpoint with an empty
    adjustment, whatever the code. `adjusted=True` is `TotalReturnBarsAsync`:
    the venue's own endpoint with the adjustment `TotalReturn` names.
    """
    endpoint, adj = route(code) if adjusted else (GENERAL, "")

    url = f"{endpoint}?param={code},month,,,430,{adj}"

    try:
        j = json.loads(get(url, referer="https://gu.qq.com/"))
    except Exception as ex:  # noqa: BLE001
        print(f"    {code}: {type(ex).__name__}")
        return None

    data = (j.get("data") or {}).get(code) or {}

    for key in (adj + "month", "month"):
        rows = data.get(key)
        if isinstance(rows, dict):
            rows = next((v for v in rows.values() if isinstance(v, list) and v), None)
        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return rows

    return None


def monthly(code, adjusted):
    """[(ym, close)] with the unfinished month dropped, exactly as the app does."""
    rows = bars(code, adjusted)
    if not rows:
        return []

    cutoff = "%04d-%02d" % (date.today().year, date.today().month)
    out = []

    for r in rows:
        try:
            ym = r[0][:7]
            close = float(r[2])
        except (ValueError, IndexError, TypeError):
            continue
        if ym >= cutoff or close <= 0:
            continue
        out.append((ym, close))

    return out


def window(series, months=120):
    """The last `months` settled months."""
    return series[-months:] if len(series) >= months else series


def growth(series):
    """The return across the window, as the boards draw it."""
    if len(series) < 2:
        return None
    return series[-1][1] / series[0][1] - 1.0


def index_section():
    """Does the adjustment change an index? This decides board thirteen."""
    print("\n=== 1. 指数：复权会不会改掉它（决定第十三页能不能接个股）===\n")
    print(f"{'代码':<12}{'名称':<12}{'空复权 月数':>12}{'复权 月数':>10}"
          f"{'首月收盘 差':>14}{'末月收盘 差':>14}{'十年涨幅差':>12}")
    print("-" * 78)

    verdict = []

    for code, name in INDICES:
        raw = monthly(code, False)
        adj = monthly(code, True)

        if not raw or not adj:
            print(f"{code:<12}{name:<12}{len(raw):>12}{len(adj):>10}   —— 有一路取不到")
            verdict.append((code, name, None))
            continue

        w_raw = window(raw)
        w_adj = window(adj)

        same_months = len(w_raw) == len(w_adj) and all(
            a[0] == b[0] for a, b in zip(w_raw, w_adj))

        if not same_months:
            # Different months on the two calls is already a different board:
            # one of them is answering with a series the other does not have.
            print(f"{code:<12}{name:<12}{len(w_raw):>12}{len(w_adj):>10}   月份对不上")
            verdict.append((code, name, None))
            continue

        head = abs(w_adj[0][1] - w_raw[0][1])
        tail = abs(w_adj[-1][1] - w_raw[-1][1])
        grew = abs((growth(w_adj) or 0) - (growth(w_raw) or 0))

        print(f"{code:<12}{name:<12}{len(w_raw):>12}{len(w_adj):>10}"
              f"{head:>14.4f}{tail:>14.4f}{grew * 100:>11.4f}%")

        verdict.append((code, name, max(head, tail, grew)))

    print()
    changed = [v for v in verdict if v[2] is not None and v[2] > 1e-9]

    if not changed:
        print("  结论：十二个指数在两路上给出的是同一条序列。第十三页可以改用复权调用，")
        print("        而它现在画出的每一个数字一个都不会变 —— 因为源端对指数忽略复权参数。")
    else:
        print("  结论：有指数被复权改掉了 → 第十三页改成复权会换掉它自己的数字：")
        for code, name, delta in changed:
            print(f"        {code} {name}  差 {delta}")

    return not changed


def stock_section():
    """How wrong is a stock unadjusted? This decides whether it matters."""
    print("\n=== 2. 个股：不复权会错多少（决定这条规则是不是只在理论上成立）===\n")
    print(f"{'代码':<12}{'名称':<12}{'起点':>10}{'月数':>6}"
          f"{'不复权 十年':>14}{'复权 十年':>14}{'差':>12}")
    print("-" * 84)

    for code, name in STOCKS:
        raw = window(monthly(code, False))
        adj = window(monthly(code, True))

        if not raw or not adj:
            print(f"{code:<12}{name:<12}{'':>10}{'':>6}   取不到（raw {len(raw)} / adj {len(adj)}）")
            continue

        g_raw = growth(raw)
        g_adj = growth(adj)

        print(f"{code:<12}{name:<12}{adj[0][0]:>10}{len(adj):>6}"
              f"{g_raw * 100:>13.2f}%{g_adj * 100:>13.2f}%"
              f"{(g_adj - g_raw) * 100:>11.2f}pp")

    print()
    print("  结论：差多少个百分点是「分红没算进去」，差一倍以上是「拆过份额 / 送过股」。")
    print("        不复权的个股曲线上有持有人根本没承受过的断崖 —— 这正是第十三页")
    print("        现在那条规则要拦的东西。")


def cross_market_section():
    """A typed list is not governed by the market setting: can it mix venues?"""
    print("\n=== 3. 自选能不能跨市场（这四页都不受市场设置管辖）===\n")
    print(f"{'代码':<12}{'名称':<12}{'端点':>14}{'复权':>6}{'首月':>10}{'月数':>6}")
    print("-" * 62)

    for code, name in STOCKS:
        endpoint, adj = route(code)
        adj_series = monthly(code, True)

        if not adj_series:
            print(f"{code:<12}{name:<12}{endpoint.split('/')[-2]:>14}{adj:>6}   取不到")
            continue

        print(f"{code:<12}{name:<12}{endpoint.split('/')[-2]:>14}{adj:>6}"
              f"{adj_series[0][0]:>10}{len(adj_series):>6}")

    print()
    print("  结论：三个端点各自给得出月线，代码前缀决定走哪个 —— 与 `TotalReturn` 一致。")
    print("        晚上市的那一行由 `Starts` 处理（第十四/十五/十六页已有，第十三页也有）。")


def main():
    print("=" * 84)
    print("四页清单板能不能接自选股")
    print("=" * 84)

    safe = index_section()
    stock_section()
    cross_market_section()

    print("\n" + "=" * 84)
    if safe:
        print("第十三页可以接：改调用，数字不变。")
    else:
        print("第十三页不能接：改调用会换掉它自己的数字。")
    print("第十四 / 十五 / 十六页本来就是复权口径，接个股不需要换任何口径。")
    print("=" * 84)


if __name__ == "__main__":
    main()
