#!/usr/bin/env python3
"""真机验证**在线加进来的币真能取到 K 线**（**日档**，不是分钟档）：
切到加密市场 -> 打开加密 K 线 -> 周期切到「日K」-> 每次只留一只（默认 AAVE、TANGYUAN）
-> 取数 -> 读状态行。跑完把市场改回 A 股。

复用 `verify-crypto.py` 的助手（`reset_market` / `open_settings` / `labels_of` /
`restart` / `open_page` / `toggle_state` / `fetch` / `DONE` / `FAILED`）。
"""
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import uiautomation as auto  # noqa: E402
import winui  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v = load("verify_crypto", os.path.join(HERE, "verify-crypto.py"))

OUT = os.path.join(os.path.dirname(HERE), "artifacts", "crypto-extra-fetch.png")
CODES = [c.strip() for c in os.environ.get("MM_CODES", "AAVE,TANGYUAN").split(",") if c.strip()]


def chips(win):
    return winui.find_all(
        win, lambda c: c.AutomationId and c.AutomationId.startswith("Coin"), limit=14)


def set_only(win, code):
    """把币种开关摆成「只有这一只」，摆完读回。"""
    states = {}

    for _ in range(3):
        states = {}

        for chip in chips(win):
            chip_code = chip.AutomationId[len("Coin"):]
            state = v.toggle_state(chip)
            states[chip_code] = state

            if state is None:
                continue

            if (state == 1) != (chip_code == code):
                try:
                    chip.GetPattern(auto.PatternId.TogglePattern).Toggle()
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(0.8)

        if states.get(code) == 1 and all(s != 1 for k, s in states.items() if k != code):
            return states

        time.sleep(1.0)

    return states


def main():
    win = v.reset_market()
    assert win is not None, "窗口未找到"

    if not v.open_settings(win):
        print("SETTINGS_FAIL")
        sys.exit(3)

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)
    labels = v.labels_of(win, seconds=200)
    print("market labels:", labels)

    if len(labels) < 4:
        print("NO_CRYPTO_MARKET")
        sys.exit(4)

    winui.combo_pick(win, combo, labels[3])
    win = v.restart()
    time.sleep(2)

    if not v.open_page(win, "NavCryptoCandle", "CoinBTC"):
        print("OPEN_CANDLE_FAIL")
        sys.exit(5)

    # 周期切到日档：分钟档只有交叉源对某些币才有，日线才有全历史。
    period = winui.find(win, lambda c: c.AutomationId == "CryptoPeriodCombo", limit=14)

    if period is not None:
        print("period ->", winui.combo_pick(win, period, "日K"))
        time.sleep(2)

    on_frame = {c.AutomationId[len("Coin"):] for c in chips(win)}
    print("on frame:", sorted(on_frame))

    results = {}

    for code in CODES:
        if code not in on_frame:
            print("[%s] 不在开关里（没注册）—— 跳过" % code)
            results[code] = None
            continue

        print("[%s] only ->" % code, set_only(win, code))
        text = v.fetch(win, seconds=300)
        ok = bool(text) and bool(v.DONE.search(text)) and not v.FAILED.search(text)
        results[code] = ok
        print("[%s] status:" % code, text)
        print("[%s] FETCH_OK:" % code, ok)
        time.sleep(1)

    winui.capture(win, OUT, tries=6)
    print("OUT:", OUT)
    print("SUMMARY:", results)

    v.reset_market()

    sys.exit(0 if all(r for r in results.values()) else 8)


if __name__ == "__main__":
    main()
