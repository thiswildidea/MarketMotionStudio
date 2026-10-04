#!/usr/bin/env python
"""Probe: can the K-line page draw one named trading day?

The question is whether the source gives minute candles at all, for how many days
back, and with which fields — because a "pick a day" control that promises dates
the source has already dropped cannot be satisfied.

Endpoint: https://ifzq.gtimg.cn/appstock/app/kline/mkline?param={code},{period},,{count}
Note the host: `web.ifzq.gtimg.cn` answers 301 and `web.ifzqgtimg.com` does not
resolve; only the bare `ifzq.gtimg.cn` returns a body.
"""

import json
import sys
import urllib.parse
import urllib.request

HOST = "https://ifzq.gtimg.cn/appstock/app/kline/mkline"


def get(url):
    request = urllib.request.Request(
        url, headers={"Referer": "https://gu.qq.com/", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def fetch(code, period="m5", count=320, param=None):
    query = param or f"{code},{period},,{count}"
    return get(f"{HOST}?param={urllib.parse.quote(query)}")


def describe(code, period="m5", count=320, param=None):
    print(f"--- {code} {param or f'{period},,{count}'}")
    try:
        payload = fetch(code, period, count, param)
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not handle
        print("   ERR", error)
        return

    data = payload.get("data")
    if isinstance(data, list):
        print("   `data` is a list:", json.dumps(data[:1], ensure_ascii=False)[:200])
        return

    node = (data or {}).get(code)
    if node is None:
        print("   no node; top-level keys:", list((data or {}).keys()),
              "code field:", payload.get("code"), payload.get("msg"))
        return
    if isinstance(node, list):
        print("   node is a list:", json.dumps(node[:1], ensure_ascii=False)[:200])
        return

    print("   node keys:", list(node.keys()))
    key = param.split(",")[1] if param else period
    rows = node.get(key)
    if not rows:
        print("   no", key)
        return

    print("   rows", len(rows), "first", rows[0], "last", rows[-1])
    days = sorted({row[0][:8] for row in rows})
    print("   days", len(days), days[:2], "…", days[-2:])


CODES = ["sh600519", "sh000001", "sz300750", "sh688981", "hk00700", "usAAPL.OQ"]

if __name__ == "__main__":
    for name in CODES:
        describe(name)

    print()
    print("=== how far does the count go? ===")
    for count in (320, 480, 640, 700, 800, 1000, 1280, 2000):
        describe("sh600519", count=count)

    print()
    print("=== does it take a date window? ===")
    for query in ("sh600519,m5,2026-09-25,2026-09-30,320",
                  "sh600519,m5,20260925,20260930,320",
                  "sh600519,m5,20260930,,320",
                  "sh600519,m5,,,320"):
        describe("sh600519", param=query)

    print()
    print("=== the other periods: how many rows is one day? ===")
    for period in ("m1", "m5", "m15", "m30", "m60"):
        describe("sh600519", period=period, count=640)

    print()
    print("=== Hong Kong and New York ===")
    for query in ("hk00700,m5,,320", "hk00700,m5", "hkHSI,m5,,320",
                  "usAAPL.OQ,m5,,320", "usAAPL,m5,,320", "us.IXIC,m5,,320"):
        describe(query.split(",")[0], param=query)

    sys.exit(0)
