#!/usr/bin/env python3
"""Probe every instrument this app can quote and report whether the series it
draws is actually adjusted — over the instrument's whole history, not just the
last 640 bars.

The chart endpoint answers at most 640 bars per request and ignores the start
date, so a single request reaches back about two and a half years and misses
every split that matters: Apple's four-for-one was in 2020 and Tencent's
one-for-five in 2014. This walks backwards the way Market/HistoryWalk.cs does —
ask for the window ending the day before the earliest bar already held, repeat —
so both columns below cover the same span.

For each code it asks the two paths side by side:

  total    the path the app takes (hkfqkline+hfq for Hong Kong,
           usfqkline+qfq for the US, newfqkline+hfq for A-shares)
  plain    the unadjusted rows off the general endpoint

and prints which series block came back and the worst one-day drop in each. A
split that has not been adjusted for shows up as a drop a holder never took —
Tencent 2014 -78.8%, Apple 2020 -74.2%, Nvidia 2024 -89.9% — so a code is only
really fixed when the worst drop on the total path is a plausible market move.

Run:  python tools/probe-adjustment.py [--market us|hk|a|all]
"""

from __future__ import annotations

import datetime
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
HK = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get"
US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"

OLDEST = "2013-01-01"
NEWEST = "2026-09-30"
PAGES = 26


def total_return(code: str) -> tuple[str, str]:
    if code.startswith("hk"):
        return HK, "hfq"
    if code.startswith("us"):
        return US, "qfq"
    return GENERAL, "hfq"


def fetch(endpoint: str, code: str, adjustment: str, start: str, end: str) -> dict:
    param = f"{code},day,{start},{end},640,{adjustment}"
    uri = f"{endpoint}?{urllib.parse.urlencode({'param': param})}"
    try:
        request = urllib.request.Request(uri, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except Exception:
        return {}


def shift(day: str, days: int) -> str:
    return (datetime.date.fromisoformat(day) + datetime.timedelta(days=days)).isoformat()


def walk(endpoint: str, code: str, adjustment: str) -> tuple[str, list]:
    """Every bar from OLDEST on, oldest first. Returns (block used, points)."""
    points: list[tuple[str, float]] = []
    seen: set[str] = set()
    block = "none"
    cursor = NEWEST

    for _ in range(PAGES):
        payload = fetch(endpoint, code, adjustment, OLDEST, cursor)
        node = (payload.get("data") or {}).get(code) or {}
        rows = node.get(adjustment + "day") or node.get("day") or []
        if not rows:
            break

        block = adjustment + "day" if node.get(adjustment + "day") else "day"

        for row in rows:
            try:
                day, close = row[0], float(row[2])
            except (TypeError, ValueError, IndexError):
                continue
            if day not in seen:
                seen.add(day)
                points.append((day, close))

        earliest = min(r[0] for r in rows if isinstance(r[0], str))
        if earliest <= OLDEST:
            break
        nxt = shift(earliest, -1)
        if nxt >= cursor:
            break
        cursor = nxt

    return block, sorted(points)


def worst(points: list) -> tuple[float, str]:
    w, when = 0.0, ""
    for i in range(1, len(points)):
        before, after = points[i - 1][1], points[i][1]
        if before <= 0 or after <= 0:
            continue
        drop = (after - before) / before
        if drop < w:
            w, when = drop, points[i][0]
    return w, when


def probe(code: str, label: str) -> dict:
    endpoint, adjustment = total_return(code)
    block, points = walk(endpoint, code, adjustment)
    plain_block, plain_points = walk(GENERAL, code, "qfq")

    drop, when = worst(points)
    plain_drop, plain_when = worst(plain_points)

    return {
        "code": code, "label": label, "endpoint": endpoint.rsplit("/", 2)[-2],
        "ask": adjustment, "got": block, "bars": len(points),
        "drop": drop, "when": when,
        "plain_got": plain_block, "plain_drop": plain_drop, "plain_when": plain_when,
    }


US_CODES = [
    ("usAAPL.OQ", "苹果 2020一拆四"),
    ("usTSLA.OQ", "特斯拉 2020一拆五/2022一拆三"),
    ("usNVDA.OQ", "英伟达 2024一拆十"),
    ("usAMZN.OQ", "亚马逊 2022一拆二十"),
    ("usGOOGL.OQ", "谷歌 2022一拆二十"),
    ("usSHOP.N", "Shopify 2022一拆十"),
    ("usWMT.N", "沃尔玛 2024一拆三"),
    ("usCMG.N", "墨式烧烤 2024一拆五十"),
    ("usAVGO.OQ", "博通 2024一拆十"),
    ("usPANW.OQ", "Palo Alto 2025一拆二"),
    ("usNFLX.OQ", "奈飞 2015一拆七"),
    ("usMSFT.OQ", "微软 分红"),
    ("usNKE.N", "耐克 分红"),
    ("usBABA.N", "阿里巴巴 ADR"),
    ("usPDD.OQ", "拼多多 ADR"),
    ("usJD.OQ", "京东 ADR"),
    ("usBRK.B.N", "伯克希尔B 从不拆"),
    ("usSPY.AM", "标普500ETF"),
    ("usQQQ.OQ", "纳指100ETF"),
    ("usDIA.AM", "道琼斯ETF"),
    ("usIWM.AM", "罗素2000ETF"),
    ("usGLD.AM", "黄金ETF"),
    ("usXLK.AM", "科技SPDR"),
    ("usXLF.AM", "金融SPDR"),
    ("usXLV.AM", "医疗SPDR"),
    ("usXLY.AM", "可选消费SPDR"),
    ("usXLP.AM", "必需消费SPDR"),
    ("usXLI.AM", "工业SPDR"),
    ("usXLE.AM", "能源SPDR"),
    ("usXLB.AM", "材料SPDR"),
    ("usXLU.AM", "公用事业SPDR"),
    ("usXLRE.AM", "房地产SPDR"),
    ("usDJI", "道琼斯指数"),
    ("usIXIC", "纳斯达克指数"),
    ("usINX", "标普500指数"),
]

HK_CODES = [
    ("hk00700", "腾讯控股 2014一拆五"),
    ("hk09988", "阿里巴巴-W"),
    ("hk00001", "长和"),
    ("hk00005", "汇丰控股"),
    ("hk00388", "港交所"),
    ("hk00939", "建设银行"),
    ("hk01299", "友邦保险"),
    ("hk01810", "小米集团"),
    ("hk02318", "中国平安"),
    ("hk03690", "美团"),
    ("hk02333", "长城汽车"),
    ("hk01177", "中国生物制药"),
    ("hk01088", "中国神华"),
    ("hkHSI", "恒生指数"),
    ("hkHSCEI", "国企指数"),
    ("hkHSTECH", "恒生科技"),
    ("hkHSCCI", "红筹指数"),
]

A_CODES = [
    ("sh600519", "贵州茅台 高分红"),
    ("sh601318", "中国平安 高分红"),
    ("sh600036", "招商银行 高分红"),
    ("sz000858", "五粮液 高分红"),
    ("sh600030", "中信证券"),
    ("sz002594", "比亚迪 多次转增"),
    ("sh601899", "紫金矿业 转增"),
    ("sh600887", "伊利股份 转增"),
    ("sh600000", "浦发银行"),
    ("sz000001", "平安银行"),
    ("sz300750", "宁德时代"),
    ("sh688981", "中芯国际"),
    ("sh518880", "黄金ETF"),
    ("sh510300", "沪深300ETF"),
    ("sz159915", "创业板ETF"),
    ("sh000001", "上证指数"),
    ("sz399001", "深证成指"),
]

GROUPS = {"us": US_CODES, "hk": HK_CODES, "a": A_CODES}


def main() -> None:
    market = sys.argv[1] if len(sys.argv) > 1 else "all"
    jobs = []
    if market in ("all", "us"):
        jobs += US_CODES
    if market in ("all", "hk"):
        jobs += HK_CODES
    if market in ("all", "a"):
        jobs += A_CODES

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda pair: probe(*pair), jobs))

    width = max(len(r["label"]) for r in results) + 2
    print(f"{'标的':<{width}} {'代码':<12} {'端点':<11} {'取到':<8} {'根数':>5} "
          f"{'应用路径最大单日跌':>16} {'未复权最大单日跌':>16}")
    print("-" * (width + 78))

    suspects = []

    for r in results:
        flag = ""
        if r["bars"] == 0:
            flag = "  ← 取不到数"
            suspects.append((r, flag))
        elif r["drop"] < -0.40 and r["plain_drop"] < r["drop"] - 0.05:
            flag = "  ← 疑似未复权的拆股"
            suspects.append((r, flag))
        elif r["drop"] < -0.45:
            flag = "  ← 跌幅过大，需人工确认"
            suspects.append((r, flag))

        print(f"{r['label']:<{width}} {r['code']:<12} {r['endpoint']:<11} {r['got']:<8} {r['bars']:>5} "
              f"{r['drop']*100:>13.2f}% {r['when']:>12} "
              f"{r['plain_drop']*100:>13.2f}% {r['plain_when']:>12}{flag}")

    print()
    if suspects:
        print(f"可疑 {len(suspects)} 只：")
        for r, flag in suspects:
            print(f"  {r['code']} {r['label']}  {flag.strip('← ')}｜取到 {r['got']}｜"
                  f"应用 {r['drop']*100:.2f}% ({r['when']})｜未复权 {r['plain_drop']*100:.2f}% ({r['plain_when']})")
    else:
        print("全部标的都拿到了序列，且没有疑似拆股的断崖。")


if __name__ == "__main__":
    main()
