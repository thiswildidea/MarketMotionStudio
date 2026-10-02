# -*- coding: utf-8 -*-
"""Probe data sources for candidate pages fourteen and beyond.

Second pass. The first pass (probe-next-indicators.py) covered global indices
(they became page thirteen), domestic futures, global futures and VIX. This one
asks about the sources nobody has measured yet: ETFs, bond indices, dividend
indices, convertible bonds, sector sub-indices, and how far back single stocks
go in each market — the things a "compare my own basket" page would need.

Nothing here is asserted against the app; it only answers "does the source carry
this, how far back, and at what period". Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators-2.py
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


def tencent(code, period="month", count=1000):
    # newfqkline (the general endpoint) is the one that carries full history.
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,{count},"
    )
    try:
        j = json.loads(get(url, referer="https://gu.qq.com/"))
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"
    data = (j.get("data") or {}).get(code) or {}
    for key in (period, "qfq" + period, "hfq" + period, "day"):
        rows = data.get(key)
        if isinstance(rows, dict):
            # Shenzhen codes sometimes wrap the array one level deeper.
            rows = next((v for v in rows.values() if isinstance(v, list) and v), None)
        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return f"{len(rows):5d} {rows[0][0]} -> {rows[-1][0]}  [{key}]"
    return "EMPTY"


def group(title, codes, period="month"):
    print(f"\n== {title} ==")
    for code in codes:
        print(f"  {code:12s} {period:5s} {tencent(code, period)}")


def main():
    group("A股 宽基 / 风格 / 主题指数（月线）", [
        "sh000852",  # 中证1000
        "sh000922",  # 中证红利
        "sh000015",  # 上证红利
        "sh000688",  # 科创50
        "sh000998",  # 中证TMT
        "sh000934",  # 中证金融
        "sh000928",  # 中证能源
        "sh000913",  # 300医药
        "sh000827",  # 中证环保
        "sh000037",  # 上证医药
    ])

    group("A股 债券 / 转债指数（月线）", [
        "sh000012",  # 上证国债
        "sh000013",  # 上证企业债
        "sz399481",  # 深证企债
        "sh000832",  # 中证转债
        "sh000022",  # 上证债券
    ])

    group("场内 ETF（月线）", [
        "sh510300",  # 沪深300ETF
        "sh510500",  # 中证500ETF
        "sh510050",  # 上证50ETF
        "sh159915",  # 创业板ETF
        "sh512880",  # 证券ETF
        "sh518880",  # 黄金ETF
        "sh513100",  # 纳指ETF
        "sh513050",  # 中概互联ETF
        "sh511010",  # 国债ETF
        "sh511260",  # 十年国债ETF
        "sh588000",  # 科创50ETF
        "sh512690",  # 酒ETF
    ])

    group("个股（月线）— 「自选篮子对拼」要用的长度", [
        "sh600519",  # 贵州茅台
        "sh601318",  # 中国平安
        "sz000001",  # 平安银行
        "hk00700",   # 腾讯控股
        "hk09988",   # 阿里巴巴
        "usAAPL.OQ",
        "usMSFT.OQ",
    ])

    group("港股 / 美股 补充标的（月线）", [
        "hkHSCCI",   # 恒生红筹
        "usVIX",
        "usRUT",
        "usGSPC",
    ])

    print("\n== VIX 与波动率（日线，问的是能回溯多久） ==")
    for code in ["usVIX", "sh000001", "hkHSI", "usIXIC"]:
        print(f"  {code:12s} day   {tencent(code, 'day', 640)}")

    group("可转债个券（月线）", [
        "sh113050",
        "sz123070",
        "sh110059",
    ])


if __name__ == "__main__":
    main()
