# -*- coding: utf-8 -*-
"""Probe candidates for page fifteen and beyond.

Fourteen pages are built and every one of them races a *return* or a *level*.
This round asks what has not been covered at all: risk, and the sources the app
has never touched (rates, valuation, flows). Two questions per candidate:

1. Can the app get a *series*? A page is an animation — one number is not data.
2. If it needs a new source, does that source actually answer a request?

The risk candidates (drawdown, volatility) need no new source: they are computed
from bars the app already fetches. Those are dry-run here so the page can be
judged on the numbers it would show, not on the idea.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators-3.py
"""

import json
import math
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def get(url, referer=None, encoding="utf-8", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "replace")


def tencent(code, period="month", adj="hfq", count=1000):
    """Monthly bars as page fourteen asks for them (adjusted)."""
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


def closes(code):
    rows = tencent(code)
    if not rows:
        return []
    out = []
    for r in rows:
        try:
            out.append((r[0], float(r[2])))
        except (ValueError, IndexError):
            pass
    return out


# ---------------------------------------------------------------------------
# 1. Risk, computed from bars the app already has
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


def drawdown(series):
    """Worst peak-to-trough, and how many months it took to get back.

    The pair is the whole point of the page: a -45% that healed in 14 months and
    a -20% that took eight years are not the same fact, and only one of the two
    numbers says which is which.
    """
    if not series:
        return None

    # Two passes, and the order is the whole point: the trough has to be final
    # before "how long to climb back" means anything. Measured in one pass, a
    # shallow dip early on sets the clock and the real fall is never timed.
    peak = series[0][1]
    worst = 0.0
    worst_at = 0
    worst_from = series[0][1]   # the high the worst drawdown fell from

    for i, (_, close) in enumerate(series):
        if close > peak:
            peak = close
        drop = (close / peak - 1.0) * 100.0
        if drop < worst:
            worst = drop
            worst_at = i
            worst_from = peak

    healed = None

    for i in range(worst_at + 1, len(series)):
        if series[i][1] >= worst_from:
            healed = i - worst_at
            break

    return worst, worst_at, healed, series[worst_at][0]


def underwater(series):
    """How far below the high each month sits — the curve itself, not the worst point."""
    out = []
    peak = series[0][1]
    for _, close in series:
        if close > peak:
            peak = close
        out.append((close / peak - 1.0) * 100.0)
    return out


def volatility(series, window=12):
    """Annualised rolling volatility of monthly returns."""
    rets = []
    for i in range(1, len(series)):
        if series[i - 1][1] > 0:
            rets.append(math.log(series[i][1] / series[i - 1][1]))
    if len(rets) < window:
        return None
    out = []
    for i in range(window - 1, len(rets)):
        chunk = rets[i - window + 1:i + 1]
        mean = sum(chunk) / window
        var = sum((x - mean) ** 2 for x in chunk) / (window - 1)
        out.append(math.sqrt(var * 12) * 100.0)
    return out


def risk_section():
    print("\n== 风险：用现成的 K 线算（回撤 / 波动率） ==")
    print("   %-12s %8s %8s %6s %8s %14s" % ("标的", "最深", "修复(月)", "波动率", "波动区间", "最深发生在"))
    for name, code in ROSTER.items():
        s = closes(code)
        if not s:
            print(f"   {name:12s} EMPTY")
            continue
        worst, at, healed, when = drawdown(s)
        vol = volatility(s)
        vol_now = vol[-1] if vol else float("nan")
        lo = min(vol) if vol else float("nan")
        hi = max(vol) if vol else float("nan")
        heal = f"{healed}" if healed is not None else "至今未修复"
        print("   %-12s %7.2f%% %8s %7.1f%% %5.1f–%.1f %14s"
              % (name, worst, heal, vol_now, lo, hi, when))

    print("\n   -- 水下曲线（近十年末尾与最深处的对照，看画面有没有东西可画）")
    for name in ("沪深300ETF", "纳指ETF", "黄金ETF"):
        s = closes(ROSTER[name])
        u = underwater(s)[-120:] if len(s) >= 120 else underwater(s)
        if not u:
            continue
        print(f"      {name}: 末值 {u[-1]:6.2f}%  最深 {min(u):6.2f}%  "
              f"0 轴占比 {100.0 * sum(1 for x in u if x > -0.01) / len(u):.0f}%")


# ---------------------------------------------------------------------------
# 2. Sources the app has never touched
# ---------------------------------------------------------------------------

def tencent_us():
    print("\n== 腾讯 us 源：VIX 家族与利率代理 ==")
    for code in ("usVIX", "usVIX9D", "usVIX3M", "usVIX6M", "usVXN", "usVXD",
                 "usTLT.OQ", "usIEF.OQ", "usSHY.OQ", "usUUP.OQ"):
        rows = tencent(code, adj="")
        print(f"   {code:10s} " + (f"{len(rows):4d} months  {rows[0][0]} -> {rows[-1][0]}"
                                   if rows else "EMPTY"))


def eastmoney():
    print("\n== 东财：国债收益率 / 北向资金 / 估值（项目曾在此被封，小量试探） ==")
    tries = [
        ("中国十年国债收益率 K 线",
         "https://push2his.eastmoney.com/api/qt/stock/kline/get"
         "?secid=100.CN10Y&fields1=f1,f2,f3&fields2=f51,f52,f53&klt=101&fqt=0&beg=0&end=20500101"),
        ("美国十年国债收益率 K 线",
         "https://push2his.eastmoney.com/api/qt/stock/kline/get"
         "?secid=100.US10Y&fields1=f1,f2,f3&fields2=f51,f52,f53&klt=101&fqt=0&beg=0&end=20500101"),
        ("北向资金历史",
         "https://datacenter-web.eastmoney.com/api/data/v1/get"
         "?reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&pageSize=5&pageNumber=1&sortColumns=TRADE_DATE&sortTypes=-1"),
        ("指数估值历史",
         "https://datacenter-web.eastmoney.com/api/data/v1/get"
         "?reportName=RPT_VALUEINDEX_HIS&columns=ALL&pageSize=5&pageNumber=1&filter=(INDEX_CODE=%22000300%22)"),
    ]
    for title, url in tries:
        try:
            raw = get(url, referer="https://data.eastmoney.com/", timeout=12)
            head = raw[:160].replace("\n", " ")
            print(f"   {title:20s} {head}")
        except Exception as exc:  # noqa: BLE001
            print(f"   {title:20s} ERR {exc}")


def chinabond():
    print("\n== 中债：国债收益率曲线 ==")
    url = ("https://yield.chinabond.com.cn/web/cbtv/queryGjqxInfo"
           "?workTime=2026-10-01&locale=zh_CN")
    try:
        raw = get(url, timeout=15)
        print("   " + raw[:200].replace("\n", " "))
    except Exception as exc:  # noqa: BLE001
        print(f"   ERR {exc}")


def sina_macro():
    print("\n== 新浪 / 其他：宏观序列 ==")
    tries = [
        ("新浪 国债期货", "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_=/"
         "InnerFuturesNewService.getDailyKLine?symbol=T0"),
    ]
    for title, url in tries:
        try:
            raw = get(url, referer="https://finance.sina.com.cn/", timeout=15,
                      encoding="gbk")
            print(f"   {title:16s} {raw[:160].replace(chr(10), ' ')}")
        except Exception as exc:  # noqa: BLE001
            print(f"   {title:16s} ERR {exc}")


def main():
    risk_section()
    tencent_us()
    eastmoney()
    chinabond()
    sina_macro()


if __name__ == "__main__":
    main()
