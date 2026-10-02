# -*- coding: utf-8 -*-
"""Probe candidates for page sixteen.

Fifteen pages are built. The last two form a pair: page fourteen says what the
eight domestic funds *earned*, page fifteen says what that cost on the way.
This round asks what the pair still does not answer, and it splits into two
kinds of candidate:

1. Computed from bars the app already fetches (volatility, correlation,
   dividend share, hold-window win rate). No new source, no new risk — the only
   question is whether the numbers move enough to be worth animating.
2. Needing a series the app has never asked for (style / size indices). Here the
   question is availability first: a page is an animation, and one number — or
   an empty window — is not data.

Every candidate is therefore judged on the same two things the last two rounds
used: does the series exist, and does it *change* over the window? A ranking
that never reorders is a static table wearing an animation.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators-4.py
"""

import json
import math
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def get(url, referer=None, encoding="utf-8", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "replace")


def tencent(code, period="month", adj="hfq", count=1000):
    """Monthly bars. adj="" gives the raw (unadjusted) series."""
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,{count},{adj}"
    )
    j = json.loads(get(url, referer="https://gu.qq.com/"))
    data = (j.get("data") or {}).get(code) or {}
    for key in (adj + period, period):
        rows = data.get(key)
        if isinstance(rows, dict):
            rows = next((v for v in rows.values() if isinstance(v, list) and v), None)
        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return rows
    return None


def monthly(code, adj="hfq"):
    """[(ym, close)] with the unfinished month dropped, as the app does.

    The app's IsSettledFor drops any bar dated on or after the first of this
    month; an external script that forgets this gets a twelfth month that is
    really two weeks, and every boundary number comes out slightly wrong.
    """
    rows = tencent(code, adj=adj)
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
        if ym >= cutoff:
            continue
        out.append((ym, close))
    return out


def window(series, months):
    """Trim to the last `months` settled months, aligned across the roster."""
    return series[-months:] if series else []


# ---------------------------------------------------------------------------
# the roster page fourteen and fifteen already share
# ---------------------------------------------------------------------------

ROSTER = {
    "沪深300ETF": "sh510300",
    "中证500ETF": "sh510500",
    "纳指ETF": "sh513100",
    "恒生ETF": "sz159920",
    "国债ETF": "sh511010",
    "黄金ETF": "sh518880",
    "豆粕ETF": "sz159985",
    "货币ETF": "sh511990",
}

YEARS = 10
MONTHS = YEARS * 12


def log_returns(closes):
    out = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0 and closes[i] > 0:
            out.append(math.log(closes[i] / closes[i - 1]))
        else:
            out.append(0.0)
    return out


def rolling_vol(closes, win=12):
    """Annualised rolling volatility of monthly log returns."""
    rets = log_returns(closes)
    if len(rets) < win:
        return []
    out = []
    for i in range(win - 1, len(rets)):
        chunk = rets[i - win + 1:i + 1]
        mean = sum(chunk) / win
        var = sum((x - mean) ** 2 for x in chunk) / (win - 1)
        out.append(math.sqrt(var * 12) * 100.0)
    return out


def rolling_corr(a, b, win=24):
    """Rolling Pearson correlation of monthly log returns."""
    ra, rb = log_returns(a), log_returns(b)
    n = min(len(ra), len(rb))
    if n < win:
        return []
    ra, rb = ra[-n:], rb[-n:]
    out = []
    for i in range(win - 1, n):
        x = ra[i - win + 1:i + 1]
        y = rb[i - win + 1:i + 1]
        mx, my = sum(x) / win, sum(y) / win
        sxy = sum((p - mx) * (q - my) for p, q in zip(x, y))
        sxx = sum((p - mx) ** 2 for p in x)
        syy = sum((q - my) ** 2 for q in y)
        out.append(sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else 0.0)
    return out


def hold_windows(closes, months=36):
    """Every buy-and-hold `months` window inside the series, as percent."""
    out = []
    for i in range(len(closes) - months):
        if closes[i] > 0:
            out.append((closes[i + months] / closes[i] - 1.0) * 100.0)
    return out


# ---------------------------------------------------------------------------
# 1. volatility — does the ranking actually reorder?
# ---------------------------------------------------------------------------

def vol_section(series):
    print("\n== 候选 A：波动率竞速（纯计算，滚动 12 个月年化波动率）==")
    print("   %-12s %8s %8s %8s %8s %8s" % ("标的", "最新", "最低", "最高", "首帧", "末帧名次"))
    vols = {}
    for name, s in series.items():
        v = rolling_vol([c for _, c in s])
        if not v:
            print(f"   {name:12s} EMPTY")
            continue
        vols[name] = v[-MONTHS + 12 - 1:] if len(v) > MONTHS else v
        v = vols[name]
        first = sum(v[:12]) / 12.0
        last = sum(v[-12:]) / 12.0
        print("   %-12s %7.1f%% %7.1f%% %7.1f%% %7.1f%%" % (name, v[-1], min(v), max(v), first))

    if len(vols) >= 2:
        # The whole question for a race page: does the order change? A ranking
        # that never reorders is a static table wearing an animation.
        names = list(vols)
        n = min(len(vols[k]) for k in names)
        early = sorted(names, key=lambda k: sum(vols[k][:6]) / 6.0)
        late = sorted(names, key=lambda k: sum(vols[k][-6:]) / 6.0)
        moves = sum(1 for i, k in enumerate(early) if early[i] != late[i])
        print(f"\n   窗口 {n} 个月；十年间名次发生变化的档位：{moves}/{len(names)}")
        print(f"   最早 6 个月均值排序：{' < '.join(early)}")
        print(f"   最近 6 个月均值排序：{' < '.join(late)}")
    return vols


# ---------------------------------------------------------------------------
# 2. correlation — is there anything to say about diversification?
# ---------------------------------------------------------------------------

def corr_section(series):
    print("\n== 候选 B：相关性 / 分散化（滚动 24 个月相关系数）==")
    names = list(series)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = [c for _, c in series[names[i]]]
            b = [c for _, c in series[names[j]]]
            r = rolling_corr(a, b)
            if not r:
                continue
            pairs.append((names[i], names[j], r))

    if not pairs:
        print("   EMPTY")
        return

    pairs.sort(key=lambda p: sum(p[2][-6:]) / 6.0)
    print("   %-28s %8s %8s %8s" % ("组合", "最新", "十年最低", "十年最高"))
    for a, b, r in pairs:
        print("   %-28s %7.2f %8.2f %8.2f" % (f"{a} × {b}", r[-1], min(r), max(r)))

    print(f"\n   共 {len(pairs)} 对。最互补：{pairs[0][0]} × {pairs[0][1]}（{pairs[0][2][-1]:+.2f}）")
    print(f"   最同步：{pairs[-1][0]} × {pairs[-1][1]}（{pairs[-1][2][-1]:+.2f}）")
    spread = [max(r) - min(r) for _, _, r in pairs]
    print(f"   十年内相关性摆幅最大：{max(spread):.2f}（摆幅小 → 画出来是一条平线）")


# ---------------------------------------------------------------------------
# 3. dividend share — how much of the return was price, how much was payout
# ---------------------------------------------------------------------------

def dividend_section():
    print("\n== 候选 C：分红贡献（后复权收益 − 不复权收益）==")
    print("   %-12s %10s %10s %10s %8s" % ("标的", "后复权", "不复权", "差额", "分红占比"))
    for name, code in ROSTER.items():
        adj = window(monthly(code, "hfq"), MONTHS)
        raw = window(monthly(code, ""), MONTHS)
        if len(adj) < 24 or len(raw) < 24:
            print(f"   {name:12s} EMPTY ({len(adj)}/{len(raw)})")
            continue
        # Align on the month label: the two series can start on different months.
        raw_map = dict(raw)
        a0, a1 = None, None
        for ym, c in adj:
            if ym in raw_map:
                a0, a1 = adj[0][1], adj[-1][1]
                break
        if a0 is None:
            print(f"   {name:12s} NO OVERLAP")
            continue
        common = [ym for ym, _ in adj if ym in raw_map]
        r0 = raw_map[common[0]]
        r1 = raw_map[common[-1]]
        ga = (a1 / a0 - 1.0) * 100.0
        gr = (r1 / r0 - 1.0) * 100.0
        share = (ga - gr) / abs(ga) * 100.0 if abs(ga) > 0.5 else float("nan")
        print("   %-12s %9.2f%% %9.2f%% %9.2f%% %7.0f%%" % (name, ga, gr, ga - gr, share))
    print("\n   注：差额 = 分红再投资 + 份额拆分。拆过份额的标的（纳指ETF）差额含拆分，不是纯分红。")


# ---------------------------------------------------------------------------
# 4. hold-window win rate
# ---------------------------------------------------------------------------

def hold_section(series):
    print("\n== 候选 D：持有胜率（任意时点买入、持有 36 个月）==")
    print("   %-12s %8s %10s %10s %8s" % ("标的", "窗口数", "正收益占比", "中位收益", "最差"))
    for name, s in series.items():
        closes = [c for _, c in s]
        w = hold_windows(closes[-MONTHS:], 36)
        if len(w) < 12:
            print(f"   {name:12s} EMPTY ({len(w)})")
            continue
        w_sorted = sorted(w)
        win = sum(1 for x in w if x > 0) / len(w) * 100.0
        print("   %-12s %8d %9.0f%% %9.2f%% %7.2f%%"
              % (name, len(w), win, w_sorted[len(w_sorted) // 2], w_sorted[0]))


# ---------------------------------------------------------------------------
# 5. style / size indices — the one candidate that needs a new series
# ---------------------------------------------------------------------------

STYLE = [
    ("沪深300", "sh000300"),
    ("沪深300价值", "sh000919"),
    ("沪深300成长", "sh000918"),
    ("中证红利", "sh000922"),
    ("上证50", "sh000016"),
    ("中证500", "sh000905"),
    ("中证1000", "sh000852"),
    ("创业板指", "sz399006"),
    ("科创50", "sh000688"),
    ("国证2000", "sz399303"),
    ("巨潮大盘", "sz399314"),
    ("巨潮小盘", "sz399316"),
]


def style_section():
    print("\n== 候选 E：风格轮动比价（需要新序列，先看给不给）==")
    print("   %-14s %8s %14s %10s" % ("指数", "月数", "起点", "近十年涨幅"))
    got = {}
    for name, code in STYLE:
        s = monthly(code, "")
        if not s:
            print(f"   {name:14s} EMPTY")
            continue
        got[name] = s
        cut = window(s, MONTHS + 1)
        if len(cut) < 25:
            print(f"   {name:14s} {len(s):8d} {s[0][0]:>14s} 仅 {len(cut)} 月")
            continue
        gain = (cut[-1][1] / cut[0][1] - 1.0) * 100.0
        print(f"   {name:14s} {len(s):8d} {s[0][0]:>14s} {gain:9.2f}%")

    # The page would race value against growth. If the ratio is a straight line
    # there is no rotation to show, only a drift.
    if "沪深300价值" in got and "沪深300成长" in got:
        v = dict(got["沪深300价值"])
        g = dict(got["沪深300成长"])
        common = sorted(set(v) & set(g))[-(MONTHS + 1):]
        if len(common) >= 25:
            ratio = [v[m] / g[m] for m in common]
            print(f"\n   价值/成长 比值（{common[0]} → {common[-1]}，{len(common)} 月）：")
            print(f"     最低 {min(ratio):.3f} · 最高 {max(ratio):.3f} · 最新 {ratio[-1]:.3f}")
            flips = sum(
                1 for i in range(1, len(ratio))
                if (ratio[i] - ratio[i - 1]) * (ratio[i - 1] - ratio[i - 2]) < 0
            ) if len(ratio) > 2 else 0
            print(f"     方向反转次数 {flips}（0 次 = 一条直线，没有轮动可画）")


def main():
    series = {}
    print("== 取数：八档 ETF 后复权月线（第十四页同一批）==")
    for name, code in ROSTER.items():
        s = window(monthly(code, "hfq"), MONTHS)
        series[name] = s
        print(f"   {name:12s} {len(s):4d} 月  {s[0][0] if s else '-'} → {s[-1][0] if s else '-'}")

    vol_section(series)
    corr_section(series)
    dividend_section()
    hold_section(series)
    style_section()


if __name__ == "__main__":
    main()
