#!/usr/bin/env python3
"""真机验证「加密货币月度收益」页（年 × 月涨跌格子）。

这一页是股票收益矩阵的加密读法：渲染器、装配、复利全是共用的，**新的只有取数**——
没有月K接口，月份从日线折叠。所以判据的重心是三件新事：

1. 页面真的在加密导航里，且取到数（状态行说「N 个格子」）；
2. 年数下拉**不重新取数**就能重画格子（改 10 年 → 5 年画面要变，改回来要还原 ——
   它是「读已有的月」，坏了的话一行文字都不会变，唯一的证据是画面）；
3. 格子真的红绿都有（涨红跌绿是这个页面的全部意义，一张全红或全绿的图说明取数
   或折叠错了；全灰说明颜色映射没画）。

跑完把市场改回 A 股。复用 `verify-crypto.py` 里已经跑通的助手（带 `__main__` 守卫，
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
MATRIX_SHOT = os.path.join(ARTIFACTS, "crypto-matrix.png")
MATRIX_ETH_SHOT = os.path.join(ARTIFACTS, "crypto-matrix-eth.png")

# 状态行的「说完了」：MatrixFetched 那句里有「N 个格子」。认形状不认总数 —— 总数随
# 币种上市时间漂，格子数在 100~130 之间（十年 ≈ 120 个月，去掉头尾两个月）。
DONE = "个格子"
CELLS = r"(\d[\d,]*)\s*个格子"

FAILURES = []


def check(label, ok, detail=""):
    print("  %s %s%s" % ("PASS" if ok else "FAIL", label, (" -> " + detail) if detail else ""))

    if not ok:
        FAILURES.append(label)

    return ok


def grid_colours(path):
    """画面里红格与绿格各占多少像素（千分比）。

    涨红跌绿是这个页面的全部意义：红占位而绿缺席（或反过来）说明取数折进来的
    月份全朝一边倒 —— 对一个十年的币这是取数坏了，不是行情。
    """
    from PIL import Image

    im = Image.open(path).convert("RGB")
    data = im.getdata()
    total = len(data)
    red = green = 0

    for r, g, b in data:
        if r > 100 and r > g * 1.6 and r > b * 1.6:
            red += 1
        elif g > 100 and g > r * 1.6 and g > b * 1.6:
            green += 1

    return red * 1000.0 / total, green * 1000.0 / total


def main():
    # 市场是持久化的：开场先摆回 A 股再重启，不假设上一趟收得干净。
    win = v.reset_market()
    assert win is not None, "窗口未找到"

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
        if not v.open_page(win, "NavCryptoMatrix", "CryptoMatrixYears"):
            print("OPEN_FAIL")
            sys.exit(5)

        # ---- 页面骨架 ----------------------------------------------------------------
        chips = v.chip_names(win)
        print("chips:", chips)
        check("这一页用的是那一排币种开关", len(chips) >= 12, "%d 个" % len(chips))

        years = winui.find(win, lambda c: c.AutomationId == "CryptoMatrixYears", limit=12)
        year_labels = winui.combo_labels(win, years) if years is not None else []

        # 十档、没有「全部」：日线源端十年封顶，最长的诚实答案就是最后一档。
        check("年数有十档", len(year_labels) == 10, "、".join(year_labels) or "(没找到下拉)")
        check("默认停在最长那档（十年）", year_labels and year_labels[-1] == "10",
              year_labels[-1] if year_labels else "")

        check("只留 BTC 一个币种", v.only_coin(win, "BTC"))

        # ---- 取数 --------------------------------------------------------------------
        text = v.fetch(win, seconds=240, done=DONE)
        print("  取数:", text)
        check("取数成功", bool(text) and DONE in (text or "") and not v.FAILED.search(text or ""),
              text or "")

        cells = __import__("re").search(CELLS, text or "")
        check("格子数在 100~130 之间（十年去掉头尾）",
              cells is not None and 100 <= int(cells.group(1).replace(",", "")) <= 130,
              cells.group(1) if cells else (text or ""))

        winui.shot(win, MATRIX_SHOT)

        red, green = grid_colours(MATRIX_SHOT)
        print("  红格 %.1f‰ / 绿格 %.1f‰" % (red, green))
        check("红格绿格都在画面上（涨红跌绿）", red > 2 and green > 2,
              "红 %.1f‰，绿 %.1f‰" % (red, green))

        # ---- 年数：不取数的重画 --------------------------------------------------------
        shots = tempfile.mkdtemp(prefix="mm-matrix-years-")
        before, idle, changed, back = (os.path.join(shots, name)
                                       for name in ("a.png", "b.png", "c.png", "d.png"))

        if year_labels:
            # 先拨一次**当前**那一档再开拍：UIA 的 Select 会把焦点挪走，标题框光标的
            # 像素会混进来。拨当前档不触发 SelectionChanged，画面不动，焦点却稳了。
            winui.combo_pick(win, years, year_labels[-1])

        winui.shot(win, before)
        winui.shot(win, idle)

        still = v.differing(before, idle)

        if year_labels:
            check("切到五年", winui.combo_pick(win, years, "5") is not None)

        time.sleep(1.0)
        winui.shot(win, changed)

        moved = v.differing(idle, changed)

        if year_labels:
            check("切回十年", winui.combo_pick(win, years, "10") is not None)

        time.sleep(1.0)
        winui.shot(win, back)

        restored = v.differing(before, back)

        check("改年数真的重画了格子（远多于静止时的噪声）",
              None not in (moved, still) and moved > 5000 and moved > 10 * max(still, 1),
              "改了 %s 像素，静止对照 %s" % (moved, still))

        check("改回十年后画面回到原样",
              None not in (moved, restored) and restored < max(moved // 5, 1),
              "回来差 %s，改年数差 %s" % (restored, moved))

        # ---- 换一个币 ------------------------------------------------------------------
        check("只留 ETH", v.set_coins(win, ["ETH"]))

        text = v.fetch(win, seconds=240, done=DONE)
        print("  ETH:", text)
        check("ETH 取数成功", bool(text) and DONE in (text or "") and not v.FAILED.search(text or ""),
              text or "")
        check("状态行报的是 ETH 的格子", "以太坊" in (text or "") or "Ethereum" in (text or ""),
              text or "")

        winui.shot(win, MATRIX_ETH_SHOT)
    finally:
        # 跑完把市场改回 A 股，别留一台「市场是加密货币」的机器。
        v.reset_market()

    print("FAILURES:", FAILURES or "none")
    print("OUT:", MATRIX_SHOT)
    print("OUT:", MATRIX_ETH_SHOT)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
