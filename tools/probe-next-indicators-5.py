# -*- coding: utf-8 -*-
r"""Probe candidates for page seventeen and beyond.

Sixteen pages are built. Four earlier passes (probe-next-indicators.py … -4.py)
measured global indices, futures, VIX, ETFs, bond indices, sector sub-indices,
risk measures and style indices; pages thirteen to sixteen came out of them. This
fifth pass asks what those passes never put to the endpoint: **the instrument
classes the app has never asked for** — bonds and convertible bonds, commodities
and futures, non-US global indices, REITs — plus one thing that needs no new
source at all, whether a *single* instrument has enough history to animate on its
own (annual bars for one symbol, rather than a roster).

Two questions per candidate, the same two every round has used:

1. Does the endpoint return a **series**? A page is an animation and one number is
   not data. An empty window is an answer, not an error.
2. Does it **change** over the window? A line that never moves is a table.

Codes are guesses by class, and most of them are expected to come back empty —
that is the point of measuring rather than assuming.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators-5.py
"""

import json
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

YEARS = 10
MONTHS = YEARS * 12


def get(url, referer=None, encoding="utf-8", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    if referer:
        req.add_header("Referer", referer)

    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "replace")


def tencent(code, period="month", adj="", count=1000):
    """newfqkline is the endpoint that carries full history."""
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,{count},{adj}"
    )

    try:
        j = json.loads(get(url, referer="https://gu.qq.com/"))
    except Exception:  # noqa: BLE001 - a refused class is the answer, not a crash
        return None

    data = (j.get("data") or {}).get(code) or {}

    for key in (adj + period, period):
        rows = data.get(key)

        if isinstance(rows, dict):
            rows = next((v for v in rows.values()
                         if isinstance(v, list) and v), None)

        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return rows

    return None


def monthly(code):
    """[(ym, close)] with the unfinished month dropped, as the app does."""
    rows = tencent(code)

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


# ---------------------------------------------------------------------------
# the classes the app has never asked for
# ---------------------------------------------------------------------------

CLASSES = [
    ("债券 / 固收", [
        ("上证国债", "sh000012"),
        ("上证企债", "sh000013"),
        ("上证公司债", "sh000022"),
        ("中证全债", "sh000023"),
        ("中证转债", "sh000832"),
        ("国债ETF", "sh511010"),
    ]),
    ("可转债个券", [
        ("南银转债", "sh113050"),
        ("兴业转债", "sh113052"),
        ("浦发转债", "sh110059"),
    ]),
    ("商品 / 期货", [
        ("沪金主力", "nf_AU0"),
        ("螺纹主力", "nf_RB0"),
        ("原油主力", "nf_SC0"),
        ("沪铜主力", "nf_CU0"),
        ("COMEX黄金", "hf_GC"),
        ("纽约原油", "hf_CL"),
    ]),
    ("境外指数（非美股）", [
        ("日经225", "jpNI225"),
        ("德国DAX", "deDAX"),
        ("英国富时100", "ukUKX"),
        ("法国CAC40", "frCAC"),
        ("韩国KOSPI", "krKS11"),
        ("印度SENSEX", "inSENSEX"),
        ("越南VN30", "vnVN30"),
        ("恒生科技", "hkHSTECH"),
        ("国企指数", "hkHSCEI"),
    ]),
    ("美股指数与 ETF", [
        ("纳斯达克100", "usNDX"),
        ("纳斯达克综指", "usIXIC"),
        ("道琼斯", "usDJI"),
        ("罗素2000", "usRUT"),
        ("REIT 指数", "usVNQ"),
        ("恐慌指数", "usVIX"),
    ]),
]


def probe_classes():
    print("== 候选：应用从没问过的标的类别（月线，看给不给、多久、动不动）==")
    print("   %-14s %-8s %6s %12s %12s" % ("名称", "代码", "月数", "起点", "近十年涨幅"))

    for label, roster in CLASSES:
        print("\n   -- %s --" % label)

        for name, code in roster:
            s = monthly(code)

            if not s:
                print("   %-14s %-8s %6s" % (name, code, "空"))
                continue

            cut = s[-(MONTHS + 1):]
            gain = ""

            if len(cut) >= 25:
                gain = "%11.2f%%" % ((cut[-1][1] / cut[0][1] - 1.0) * 100.0)
            elif cut:
                gain = "仅 %d 月" % len(cut)

            print("   %-14s %-8s %6d %12s %12s" % (
                name, code, len(s), s[0][0], gain))


# ---------------------------------------------------------------------------
# one instrument, many years: is a single-symbol page worth animating?
# ---------------------------------------------------------------------------

def yearly(code):
    rows = tencent(code, period="year")

    if not rows:
        return []

    out = []

    for r in rows:
        try:
            out.append((r[0][:4], float(r[2])))
        except (ValueError, IndexError, TypeError):
            continue

    return out


def single_section():
    """单标的年线：一只自己的历史能不能撑起一页（而不是一篮子）。"""
    print("\n== 候选：单标的年线（一只标的自己够不够画一页）==")
    print("   %-12s %-10s %6s %10s %12s" % ("名称", "代码", "年数", "起点", "涨跌交替"))

    for name, code in [("上证指数", "sh000001"), ("沪深300", "sh000300"),
                       ("恒生指数", "hkHSI"), ("标普500", "usINX"),
                       ("纳斯达克", "usIXIC"), ("黄金ETF", "sh518880")]:
        s = yearly(code)

        if not s:
            print("   %-12s %-10s %6s" % (name, code, "空"))
            continue

        flips = sum(1 for i in range(2, len(s))
                    if (s[i][1] - s[i - 1][1]) * (s[i - 1][1] - s[i - 2][1]) < 0)

        print("   %-12s %-10s %6d %10s %11d 次" % (
            name, code, len(s), s[0][0] if s else "-", flips))


def main():
    probe_classes()
    single_section()


if __name__ == "__main__":
    main()
