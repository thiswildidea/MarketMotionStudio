# -*- coding: utf-8 -*-
"""Probe data sources for candidate pages thirteen and beyond.

Nothing here is asserted against the app; it only answers "does the source carry
this, how far back, and at what period". Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators.py
"""

import json
import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def get(url, referer=None, encoding="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(encoding, "replace")


def tencent(code, period="month", count=1000):
    # newfqkline (the general endpoint) is the one that carries full history;
    # plain fqkline gives usINX ten months and usDJI one.
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,{count},"
    )
    try:
        raw = get(url, referer="https://gu.qq.com/")
        j = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"
    data = (j.get("data") or {}).get(code) or {}
    for key in (period, "qfq" + period, "hfq" + period, "day", "month"):
        rows = data.get(key)
        if rows:
            return f"{len(rows)} bars from {rows[0][0]} to {rows[-1][0]} (key={key})"
    return "EMPTY"


def sina_futures(symbol):
    # jsonp.php needs the callback-variable segment, or the service name is "invalid".
    url = (
        "https://stock2.finance.sina.com.cn/futures/api/jsonp.php"
        "/var%20_=/InnerFuturesNewService.getDailyKLine?symbol=" + symbol
    )
    try:
        raw = get(url, referer="https://finance.sina.com.cn/")
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"
    m = re.search(r"\((\[.*\])\)", raw, re.S)
    if not m:
        return "EMPTY or no array"
    try:
        rows = json.loads(m.group(1))
    except Exception as exc:  # noqa: BLE001
        return f"ERR parse {exc}"
    if not rows:
        return "EMPTY"
    return f"{len(rows)} bars from {rows[0]['d']} to {rows[-1]['d']}"


def main():
    print("== tencent monthly: indices ==")
    for code in [
        "sh000001", "sz399001", "sz399006", "sh000300", "sh000905", "sh000016",
        "hkHSI", "hkHSCEI", "hkHSTECH",
        "usINX", "usDJI", "usIXIC", "usNDX", "usVIX",
    ]:
        print(f"  {code:10s} month  {tencent(code, 'month')}")
    print("  usVIX      day    " + tencent("usVIX", "day", 640))

    print("\n== sina domestic futures (daily) ==")
    for sym in ["AU0", "AG0", "CU0", "SC0", "RB0", "IF0", "T0", "M0", "C0"]:
        print(f"  {sym:5s} {sina_futures(sym)}")

    print("\n== sina global futures (daily) ==")
    for sym in ["XAU", "XAG", "CL", "OIL", "HG"]:
        url = (
            "https://stock2.finance.sina.com.cn/futures/api/jsonp.php"
            "/var%20_=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=" + sym
        )
        try:
            raw = get(url, referer="https://finance.sina.com.cn/")
        except Exception as exc:  # noqa: BLE001
            print(f"  {sym:5s} ERR {exc}")
            continue
        m = re.search(r"\((\[.*\])\)", raw, re.S)
        if not m:
            print(f"  {sym:5s} EMPTY")
            continue
        rows = json.loads(m.group(1))
        if not rows:
            print(f"  {sym:5s} EMPTY")
            continue
        key = "date" if "date" in rows[0] else "d"
        print(f"  {sym:5s} {len(rows)} bars from {rows[0][key]} to {rows[-1][key]}")


if __name__ == "__main__":
    main()
