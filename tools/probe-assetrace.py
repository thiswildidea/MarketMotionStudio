# -*- coding: utf-8 -*-
"""Probe the ETF shortlist for page fourteen (asset-class race).

Page thirteen races indices. Page fourteen races the things you can actually
hold: an ETF for each asset class. The question this script answers is the one
that decides the roster — how far back does each ETF go, because an ETF that
starts in 2019 cannot fill a twenty-year span, and the page has to say so rather
than pretend.

Nothing here is asserted against the app. Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-assetrace.py
"""

import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def get(url, referer=None, encoding="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(encoding, "replace")


def rows_of(code, period="month", adj=""):
    """One series, as the app would ask for it. `adj` is "" (raw) or "hfq" or "qfq"."""
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,1000,{adj}"
    )
    j = json.loads(get(url, referer="https://gu.qq.com/"))
    data = (j.get("data") or {}).get(code) or {}
    # Order matters: the adjusted series is what the app wants, the raw one is the fallback.
    keys = [adj + period if adj else period, period] if adj else [period]
    for key in keys:
        rows = data.get(key)
        if isinstance(rows, dict):
            rows = next((v for v in rows.values() if isinstance(v, list) and v), None)
        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return key, rows
    return None, None


def month(code):
    try:
        key, rows = rows_of(code)
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"
    if not rows:
        return "EMPTY"
    return f"{len(rows):4d} months  {rows[0][0]} -> {rows[-1][0]}  [{key}]"


def main():
    print("== 每一格的候选（月线，看的是起点） ==")
    # 159xxx and 161xxx are Shenzhen codes; the first pass wrote them as sh* and got nothing.
    groups = {
        "境内股票": ["sh510300", "sh510050", "sh510500", "sz159915", "sh588000"],
        "境外股票": ["sh513100", "sz159941", "sh513500", "sz159920", "sh513660",
                     "sh513050", "sh513180"],
        "债券": ["sh511010", "sh511260", "sh511020", "sz159972", "sh511220"],
        "黄金 / 贵金属": ["sh518880", "sz159934", "sz161226", "sh512400"],
        "商品": ["sz159985", "sz159980", "sz159981", "sh512400"],
        "现金 / 货币": ["sh511990", "sh511880", "sh511900", "sz159001"],
        "指数代理（起点更长，用来判断要不要退回去）": [
            "sh000300", "sh000016", "sh000012", "sh000832", "sh000015",
        ],
    }
    for title, codes in groups.items():
        print(f"\n  -- {title}")
        for code in codes:
            print(f"     {code:10s} {month(code)}")

    print("\n== 复权口径：这些 ETF 有分红，债券和现金的收益几乎全在分红里 ==")
    print("   raw 是不复权的收盘，hfq 是后复权。两者差多少 = 分红占了多少。")
    for code in ["sh510300", "sh511010", "sh511990", "sh511880", "sh518880", "sh513100"]:
        line = [f"{code:10s}"]
        for adj in ("", "hfq"):
            try:
                key, rows = rows_of(code, "month", adj)
            except Exception as exc:  # noqa: BLE001
                line.append(f"{adj or 'raw'}: ERR {exc}")
                continue
            if not rows:
                line.append(f"{adj or 'raw'}: EMPTY")
                continue
            first = float(rows[0][2])
            last = float(rows[-1][2])
            line.append(
                f"{adj or 'raw'}: {len(rows):3d}月 {rows[0][0]} {first:.3f} -> "
                f"{rows[-1][0]} {last:.3f}  ({(last / first - 1) * 100:+.1f}%)")
        print("   " + "   ".join(line))

    # The one number on the board nobody can sanity-check by eye: the Nasdaq ETF's
    # backward-adjusted series says +578% over ten years. An ETF with a share split in
    # its history is exactly the case where an adjustment can be wrong in a way that
    # looks plausible, so it is checked against the index it tracks, converted at the
    # rate that was actually quoted.
    print("\n== 对账：纳指ETF 的复权序列 vs 纳斯达克100 指数 × 汇率 ==")
    try:
        _, ndx = rows_of("usNDX", "month", "")
        _, fx = rows_of("whUSDCNY", "month", "")
        _, etf = rows_of("sh513100", "month", "hfq")
        if ndx and fx and etf:
            def ym(rows):
                out = {}
                for r in rows:
                    out[r[0][:7]] = float(r[2])
                return out
            n, f, e = ym(ndx), ym(fx), ym(etf)
            months = sorted(set(n) & set(f) & set(e))
            window = months[-120:]
            a, b = window[0], window[-1]
            index_gain = n[b] / n[a] - 1
            fx_gain = f[b] / f[a] - 1
            combined = (1 + index_gain) * (1 + fx_gain) - 1
            print(f"   窗口 {a} -> {b}")
            print(f"   纳斯达克100（点位，不含股息）  {n[a]:.0f} -> {n[b]:.0f}  {index_gain * 100:+.1f}%")
            print(f"   美元兑人民币                   {f[a]:.3f} -> {f[b]:.3f}  {fx_gain * 100:+.1f}%")
            print(f"   两者相乘（人民币计价）                      {combined * 100:+.1f}%")
            print(f"   纳指ETF 后复权                 {e[a]:.3f} -> {e[b]:.3f}  {(e[b] / e[a] - 1) * 100:+.1f}%")
    except Exception as exc:  # noqa: BLE001
        print(f"   对账失败：{exc}")

    print("\n== 预演：近十年（120 个月）这一页会给每个资产什么数字 ==")
    # Dry run of the page's own arithmetic, hfq monthly, each row measured from
    # its own first month inside the window — the rule page thirteen established.
    roster = {
        "沪深300ETF": "sh510300",
        "中证500ETF": "sh510500",
        "纳指ETF": "sh513100",
        "恒生ETF": "sz159920",
        "国债ETF": "sh511010",
        "黄金ETF": "sh518880",
        "豆粕ETF": "sz159985",
        "银华日利": "sh511880",
    }
    series = {}
    for name, code in roster.items():
        try:
            _, rows = rows_of(code, "month", "hfq")
        except Exception:  # noqa: BLE001
            print(f"   {name:12s} {code:10s} ERR")
            continue
        if not rows:
            print(f"   {name:12s} {code:10s} EMPTY")
            continue
        # Month keyed by year-month, last bar in a month wins; the month that has
        # not finished yet is not a month (the app's IsSettledFor rule).
        by_month = {}
        for r in rows:
            ym = r[0][:7]
            by_month[ym] = float(r[2])
        series[name] = by_month
    months = sorted({m for s in series.values() for m in s})
    if months:
        window = months[-120:]
        print(f"   窗口 {window[0]} -> {window[-1]}（{len(window)} 个月）")
        for name, by_month in series.items():
            inside = [m for m in window if m in by_month]
            if not inside:
                print(f"   {name:12s} 窗口内没有数据")
                continue
            base = by_month[inside[0]]
            last = by_month[inside[-1]]
            print(f"   {name:12s} 起 {inside[0]}  {base:8.3f} -> {last:8.3f}  "
                  f"{(last / base - 1) * 100:+8.2f}%   ({len(inside)} 个月)")


if __name__ == "__main__":
    main()
