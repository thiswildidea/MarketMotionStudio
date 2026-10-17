"""Probe the four candidate crypto pages' data before any code is written.

Run:  python tools/probe-crypto-four.py
Delete after the readings are recorded in NOTES.md.
"""
import json
import ssl
import sys
import urllib.request

UA = {"User-Agent": "MarketMotionStudio-probe/1.0"}
CTX = ssl.create_default_context()


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read().decode("utf-8", "replace")


def show(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------- 1. CoinGecko ranking
show("1. CoinGecko coins/markets — 字段与涨跌幅榜")
try:
    url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
           "&order=market_cap_desc&per_page=250&page=1&sparkline=false"
           "&price_change_percentage=24h,7d,30d")
    st, body = get(url)
    print("status", st, "bytes", len(body))
    rows = json.loads(body)
    print("rows:", len(rows))
    if rows:
        print("row[0] keys:", sorted(rows[0].keys()))
        print("sample:", {k: rows[0].get(k) for k in
                          ("id", "symbol", "name", "current_price", "market_cap",
                           "price_change_percentage_24h",
                           "price_change_percentage_24h_in_currency",
                           "price_change_percentage_7d_in_currency",
                           "price_change_percentage_30d_in_currency")})
    # top gainers / losers among the top 250 by cap
    live = [r for r in rows if r.get("price_change_percentage_24h_in_currency") is not None]
    live.sort(key=lambda r: r["price_change_percentage_24h_in_currency"], reverse=True)
    print("\n--- top 10 gainers (24h, of top 250) ---")
    for r in live[:10]:
        print(f"  {r['symbol']:8} {r['name'][:22]:22} "
              f"{r['price_change_percentage_24h_in_currency']:+7.2f}%  cap={r['market_cap']:.3e}")
    print("--- top 10 losers (24h, of top 250) ---")
    for r in live[-10:][::-1]:
        print(f"  {r['symbol']:8} {r['name'][:22]:22} "
              f"{r['price_change_percentage_24h_in_currency']:+7.2f}%  cap={r['market_cap']:.3e}")
except Exception as e:
    print("FAILED:", type(e).__name__, e)

# ---------------------------------------------------------------- 2. CoinGecko global
show("2. CoinGecko /global — 市值占比")
try:
    st, body = get("https://api.coingecko.com/api/v3/global")
    print("status", st, "bytes", len(body))
    g = json.loads(body)["data"]
    print("keys:", sorted(g.keys()))
    print("market_cap_percentage:", g.get("market_cap_percentage"))
    print("total_market_cap usd:", g.get("total_market_cap", {}).get("usd"))
except Exception as e:
    print("FAILED:", type(e).__name__, e)

# ---------------------------------------------------------------- 3. CoinMetrics batch caps
show("3. CoinMetrics asset-metrics — 批量市值（占比可算）")
try:
    url = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
           "?assets=btc,eth,sol,bnb,xrp&metrics=CapMrktEstUSD&frequency=1d"
           "&start_time=2024-01-01&end_time=2024-01-05&page_size=100")
    st, body = get(url)
    print("status", st, "bytes", len(body))
    j = json.loads(body)
    data = j.get("data", [])
    print("rows:", len(data), "next:", j.get("next_page_token"))
    for row in data[:8]:
        print(" ", row)
except Exception as e:
    print("FAILED:", type(e).__name__, e)

# ---------------------------------------------------------------- 4. Yahoo annual folding
show("4. Yahoo chart — 年度折叠（日线 -> 年末收盘）")
try:
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
           "?range=10y&interval=1d")
    st, body = get(url)
    print("status", st, "bytes", len(body))
    j = json.loads(body)
    res = j["chart"]["result"][0]
    stamps = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    print("bars:", len(stamps))
    import datetime as dt
    # last close of each calendar year
    last = {}
    for t, c in zip(stamps, closes):
        if c is None:
            continue
        d = dt.datetime.utcfromtimestamp(t).date()
        last[d.year] = (d, c)
    for y in sorted(last):
        d, c = last[y]
        print(f"  {y}: {d}  {c:,.2f}")
except Exception as e:
    print("FAILED:", type(e).__name__, e)

print("\ndone.")
