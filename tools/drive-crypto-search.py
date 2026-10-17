#!/usr/bin/env python3
"""真机验证「加密 K 线」检索框的**在线检索**：切到加密市场 -> 打开加密 K 线 ->
在检索框里敲一个不在固定 12 币里的名字 -> 看下面有没有出现可点的候选 -> 点一个 ->
看它有没有变成一个开关（并被选中）。最后把市场改回 A 股。

复用 `verify-crypto.py` 里已经跑通的助手（`reset_market` / `open_settings` /
`labels_of` / `restart` / `open_page` / `chip_names`），它带 `__main__` 守卫，
所以按路径加载不会跑它的主流程。
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

OUT = os.path.join(os.path.dirname(HERE), "artifacts", "crypto-search.png")
QUERY = os.environ.get("MM_QUERY", "aave")
PICK = os.environ.get("MM_PICK", "1") != "0"


def suggestions(win):
    found = winui.find_all(
        win, lambda c: c.AutomationId and c.AutomationId.startswith("Sugg"), limit=18)

    return [c for c in found if c.Name]


def main():
    # 市场是持久化的：开场先摆回 A 股再重启，不假设上一趟收得干净。
    win = v.reset_market()
    assert win is not None, "窗口未找到"

    # ---- 切到加密货币市场 --------------------------------------------------------
    if not v.open_settings(win):
        print("SETTINGS_FAIL")
        sys.exit(3)

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo", limit=14)
    labels = v.labels_of(win, seconds=200)
    print("market labels:", labels)

    if len(labels) < 4:
        print("NO_CRYPTO_MARKET（本机取不到币价，加密市场那格没出现）")
        sys.exit(4)

    print("picked:", winui.combo_pick(win, combo, labels[3]))
    win = v.restart()
    time.sleep(2)

    if not v.open_page(win, "NavCryptoCandle", "CoinBTC"):
        print("OPEN_CANDLE_FAIL")
        sys.exit(5)

    before = v.chip_names(win)
    print("chips before: %d ->" % len(before), before)

    box = winui.find(win, lambda c: c.AutomationId == "CryptoSearch", limit=14)

    if box is None:
        print("NO_SEARCH_BOX")
        sys.exit(6)

    # 敲进检索框。走 ValuePattern，和 verify-crypto 一样。
    box.GetPattern(auto.PatternId.ValuePattern).SetValue(QUERY)
    print("typed:", QUERY)

    # 防抖 260ms + 一次跨境往返：给足时间，并且分几次看，免得早看一眼就判死。
    found = []

    for _ in range(8):
        time.sleep(2.5)
        found = suggestions(win)

        if found:
            break

    print("suggestions: %d" % len(found))

    for row in found:
        print("   ", row.AutomationId, "|", row.Name)

    # 先抓一张：不管有没有候选，这一眼都是证据（有候选=在线检索通了）。
    winui.capture(win, OUT, tries=6)
    print("OUT:", OUT)

    if not found:
        print("NO_SUGGESTIONS（在线检索没答；固定 12 币的收窄仍照常）")
        v.reset_market()
        sys.exit(7)

    if not PICK:
        # 只看候选，不点 —— 用来验「上次加的币跨会话还在」（这一眼 chips before 就是证据），
        # 同时不再往机器的清单里添东西。
        print("MM_PICK=0：不点，只验候选")
        v.reset_market()
        sys.exit(0)

    # ---- 点第一个候选，看它变成一个开关 ------------------------------------------
    first = found[0]
    code = first.AutomationId[len("Sugg"):]
    print("choosing:", code)

    try:
        first.GetInvokePattern().Invoke()
    except Exception:  # noqa: BLE001
        try:
            win.SetActive()
        except Exception:  # noqa: BLE001
            pass
        first.Click()

    time.sleep(3)

    after = v.chip_names(win)
    added = [c for c in after if c not in before]
    print("chips after: %d ->" % len(after), after)
    print("ADDED:", added)
    print("CHIP_PRESENT:", ("Coin" + code) in [c for c in after] or code in added)

    winui.capture(win, OUT, tries=6)
    print("OUT_FINAL:", OUT)

    # 跑完把市场改回 A 股，别留一台「市场是加密货币」的机器。
    v.reset_market()
    print("DONE")


if __name__ == "__main__":
    main()
