#!/usr/bin/env python3
"""How much of the US market does the adjusted endpoint actually serve?

The app lets a user type any ticker, so the five ETFs on the one-key list prove
nothing about coverage. This asks usfqkline for a spread of listings — mega
caps, ADRs, small caps on each venue, share classes with a dot — and reports
which come back with a forward-adjusted series and which fall through to raw.

Run: python tools/probe-us-coverage.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

US = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/usfqkline/get"
GENERAL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

TICKERS = [
    "usAAPL.OQ", "usMSFT.OQ", "usNVDA.OQ", "usGOOG.OQ", "usMETA.OQ",
    "usTSLA.OQ", "usJPM.N", "usV.N", "usJNJ.N", "usXOM.N",
    "usBRK.A.N", "usBRK.B.N", "usBF.B.N", "usRDS.A.N",
    "usBABA.N", "usJD.OQ", "usNIO.N", "usLI.OQ", "usXPEV.N",
    "usTCEHY.OQ", "usNTES.OQ", "usBIDU.OQ", "usYMM.N",
    "usPLTR.OQ", "usCOIN.OQ", "usRBLX.N", "usSNOW.N", "usDDOG.OQ",
    "usCRWV.OQ", "usARM.OQ", "usSMCI.OQ", "usMRVL.OQ",
    "usF.N", "usGM.N", "usRIVN.OQ", "usLCID.OQ",
    "usKO.N", "usPEP.OQ", "usMCD.N", "usSBUX.OQ", "usDIS.N",
    "usAMD.OQ", "usINTC.OQ", "usMU.OQ", "usQCOM.OQ", "usTXN.OQ",
    "usUNH.N", "usLLY.N", "usNVO.N", "usAZN.OQ",
    "usGS.N", "usMS.N", "usC.N", "usWFC.N", "usBAC.N",
    "usAAPL", "usMSFT", "usNVDA",  # bare, to show the suffix problem
]


def ask(code: str, adjustment: str = "qfq") -> tuple[str, int]:
    param = f"{code},day,2020-01-01,2026-09-30,640,{adjustment}"
    uri = f"{US}?{urllib.parse.urlencode({'param': param})}"
    try:
        request = urllib.request.Request(uri, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as r:
            payload = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return "error", 0

    node = (payload.get("data") or {}).get(code) or {}
    if not node:
        return "empty", 0
    for key in ("qfqday", "hfqday", "day"):
        block = node.get(key)
        if isinstance(block, list) and block:
            return key, len(block)
    return "empty", 0


def main() -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(ask, TICKERS))

    adjusted = sum(1 for block, _ in results if block.endswith("day") and block != "day")
    print(f"{'代码':<12} {'取到':<8} {'根数':>5}")
    print("-" * 28)
    for code, (block, n) in zip(TICKERS, results):
        print(f"{code:<12} {block:<8} {n:>5}")

    print()
    print(f"共 {len(TICKERS)} 只，取到复权序列 {adjusted} 只，"
          f"回落未复权 {sum(1 for b, _ in results if b == 'day')} 只，"
          f"取不到 {sum(1 for b, _ in results if b in ('empty', 'error'))} 只。")


if __name__ == "__main__":
    main()
