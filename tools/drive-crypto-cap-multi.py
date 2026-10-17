#!/usr/bin/env python3
"""真机验证「加密货币市值历程」的**多标的**支持。

这一页原来只有一个币种下拉，画的是「上一条流通市值线、下一条价格线」。加了多标的后它
换成了三页共用的那一排开关，走的是**另一条分支**（`CapBoard.Comparing`）：整个画面留给
市值，每个币一条线，末端标名字。所以「一个币取到了数」证明不了新加的那一支是好的。

这一段跑三件事：

1. 只留 BTC 取一次 —— 单标的那一支照旧（状态行里要有「期末市值」这个数）。
2. 选 BTC + ETH 再取一次 —— 多标的那一支（状态行变成「几个币种 · 几个自然日」，
   而「期末市值」那个数**不该在**，它只有一条线才有）。
3. 市值刻度两档对画面的双向影响：什么都不动差多少、改刻度差多少、改回默认又差多少。
   那个下拉读的都是页面上已有的数，所以它坏了的话一行文字都不会变 —— 唯一的证据是画面。

最后把市场改回 A 股。复用 `verify-crypto.py` 里已经跑通的助手（它带 `__main__` 守卫，
按路径加载不会跑它的主流程）。
"""
import importlib.util
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import winui  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v = load("verify_crypto", os.path.join(HERE, "verify-crypto.py"))

ARTIFACTS = os.path.join(os.path.dirname(HERE), "artifacts")
SINGLE = os.path.join(ARTIFACTS, "crypto-caphistory.png")
MULTI = os.path.join(ARTIFACTS, "crypto-caphistory-multi.png")

FAILURES = []


def check(label, ok, detail=""):
    print("  %s %s%s" % ("PASS" if ok else "FAIL", label, (" -> " + detail) if detail else ""))

    if not ok:
        FAILURES.append(label)

    return ok


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
        v.reset_market()
        sys.exit(4)

    print("picked:", winui.combo_pick(win, combo, labels[3]))
    win = v.restart()
    time.sleep(2)

    try:
        if not v.open_page(win, "NavCryptoCapHistory", "CryptoCapRange"):
            print("OPEN_FAIL")
            sys.exit(5)

        # ---- 这一页现在用哪个选择器 --------------------------------------------------
        chips = v.chip_names(win)
        print("chips:", chips)

        # 「十二个都在」而不是「刚好十二个」：检索框能在线加币（`CryptoRegistry` 跨会话
        # 记着），加过的币下次开机就是一行里的开关。
        check("这一页用的是那一排币种开关（三页共用的选择器）", len(chips) >= 12, "%d 个" % len(chips))

        axis = winui.find(win, lambda c: c.AutomationId == "AxisCombo", limit=12)
        axis_labels = winui.combo_labels(win, axis) if axis is not None else []

        check("市值刻度有两档（实际数值 / 归一化）", len(axis_labels) == 2,
              "、".join(axis_labels) or "(没找到下拉)")

        # ---- 单标的：这一页一直的样子 ------------------------------------------------
        check("只留 BTC 一个币种", v.only_coin(win, "BTC"))

        text = v.fetch(win)
        print("  单标的:", text)
        check("单标的取数成功", bool(text) and not v.FAILED.search(text or ""))

        value = v.CAP_VALUE.search(text or "")
        check("单标的报出期末市值那个数", value is not None, value.group(1) if value else (text or ""))

        winui.shot(win, SINGLE)

        # ---- 多标的 ------------------------------------------------------------------
        check("选 BTC + ETH 两个币种", v.set_coins(win, ["BTC", "ETH"]))

        text = v.fetch(win)
        print("  多标的:", text)
        check("多标的取数成功", bool(text) and not v.FAILED.search(text or ""))

        pair = v.CAP_BOARD.search(text or "")
        check("状态行报出币种数与自然日数", pair is not None, text or "")

        if pair:
            check("报的是 2 个币种", int(pair.group(1)) == 2, pair.group(1))
            check("自然日在 80~4000 之间",
                  80 <= int(pair.group(2).replace(",", "")) <= 4000, pair.group(2))
            check("多标的那句里没有期末市值（那是单标的才有的数）",
                  v.CAP_VALUE.search(text or "") is None, text or "")

        winui.shot(win, MULTI)

        # ---- 市值刻度：改画面、再改回来 ------------------------------------------------
        shots = tempfile.mkdtemp(prefix="mm-cap-axis-")
        before, idle, changed, back = (os.path.join(shots, name)
                                       for name in ("a.png", "b.png", "c.png", "d.png"))

        if len(axis_labels) == 2:
            # 先拨一次**当前**那一档再开拍：UIA 的 Select 会把焦点挪走，标题框的光标一消失
            # 就是一万九千个与刻度无关的像素。拨当前档不触发 SelectionChanged，画面不动，
            # 焦点却稳了 —— 四张图站在同一块地基上。
            winui.combo_pick(win, axis, axis_labels[0])

        winui.shot(win, before)
        winui.shot(win, idle)

        still = v.differing(before, idle)

        if len(axis_labels) == 2:
            check("切到归一化刻度", winui.combo_pick(win, axis, axis_labels[1]) is not None)

        winui.shot(win, changed)

        moved = v.differing(idle, changed)

        if len(axis_labels) == 2:
            check("切回实际数值", winui.combo_pick(win, axis, axis_labels[0]) is not None)

        winui.shot(win, back)

        restored = v.differing(before, back)

        check("市值刻度真的改了画面（远多于静止时的噪声）",
              None not in (moved, still) and moved > 5000 and moved > 10 * max(still, 1),
              "改了 %s 像素，静止对照 %s" % (moved, still))

        check("改回默认刻度后画面回到原样",
              None not in (moved, restored) and restored < max(moved // 5, 1),
              "回来差 %s，改刻度差 %s" % (restored, moved))
    finally:
        # 跑完把市场改回 A 股，别留一台「市场是加密货币」的机器。
        v.reset_market()

    print("FAILURES:", FAILURES or "none")
    print("OUT:", SINGLE)
    print("OUT:", MULTI)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
