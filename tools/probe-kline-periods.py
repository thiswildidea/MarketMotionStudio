"""Probe which periods and adjustment blocks the Tencent kline endpoints return.

Answers three questions the candle page needs settled before any code is written:

  1. Does an endpoint serve `week` at all, or only `day` and `month`?
  2. What is the adjusted block called for each period — `hfqday`, `hfqweek`,
     `hfqmonth`? A period with no adjusted block means a split shows up as a cliff.
  3. Does a weekly/monthly row carry the full open/high/low/close, or only the
     close? The whole point of the page is the candle body.

Run:  <venv python> tools/probe-kline-periods.py
"""

import json
import urllib.request

ENDPOINTS = {
    "general": "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get",
    "hk": "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/hkfqkline/get",
    "us": "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get",
}

SAMPLES = [
    ("sh600519", "general"),   # A-share stock, heavy payer: qfq goes negative
    ("sh000001", "general"),   # A-share index
    ("sh510300", "general"),   # A-share ETF
    ("hk00700", "hk"),         # HK stock, one-for-five in 2014
    ("hkHSI", "hk"),           # HK index
    ("hk02800", "hk"),         # HK tracker fund
    ("usAAPL.OQ", "us"),       # US stock, four-for-one in 2020
    ("usDJI", "us"),           # US index
    ("usSPY.AM", "us"),        # US ETF
]

PERIODS = ["day", "week", "month"]
ADJUSTMENTS = ["hfq", "qfq"]


def fetch(endpoint, code, period, adjustment, count=8):
    param = f"{code},{period},,,{count},{adjustment}"
    url = f"{endpoint}?param={urllib.parse.quote(param)}"

    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def blocks(node):
    """The array-valued keys of one instrument's node, with their row lengths."""
    found = {}

    for key, value in node.items():
        if isinstance(value, list) and value and isinstance(value[0], list):
            found[key] = (len(value), len(value[0]))

    return found


def main():
    for code, endpoint_name in SAMPLES:
        endpoint = ENDPOINTS[endpoint_name]
        print(f"\n=== {code}  ({endpoint_name}) ===")

        for period in PERIODS:
            for adjustment in ADJUSTMENTS:
                try:
                    root = fetch(endpoint, code, period, adjustment)
                except Exception as ex:
                    print(f"  {period:5} {adjustment}: request failed ({ex})")
                    continue

                if root.get("code") != 0:
                    print(f"  {period:5} {adjustment}: envelope code {root.get('code')} {root.get('msg')!r}")
                    continue

                node = root.get("data", {}).get(code, {})
                seen = blocks(node)

                if not seen:
                    print(f"  {period:5} {adjustment}: no bar arrays at all")
                    continue

                wanted = f"{adjustment}{period}"
                plain = period

                label = (
                    f"{wanted}" if wanted in seen
                    else f"{plain} only" if plain in seen
                    else "? " + ",".join(sorted(seen))
                )

                chosen = wanted if wanted in seen else plain
                rows, fields = seen.get(chosen, (0, 0))

                sample = node.get(chosen, [[]])[0][:5] if rows else []

                print(
                    f"  {period:5} {adjustment}: {label:12} rows={rows:3} fields={fields:2} "
                    f"first={sample}")


if __name__ == "__main__":
    import urllib.parse

    main()
